"""런타임 실패 패턴 진단 (--diagnose 모드).

기존 정합성 검사와 독립. 4-phase 루프:
  1. capture   — .plan.md / .focus.md / 최근 git 상태
  2. diagnose  — 패턴 매칭 (loop · red-miss · repeat-not-ready · scope-violation)
  3. reduce    — 패턴별 권장 액션 확정
  4. report    — DIAGNOSIS 블록 출력

패턴 정의 변경 시 PLUGIN_SCHEMA_NOTES.md 와 무관. 본 파일에서만 관리.
"""

import re
import subprocess
import sys
from pathlib import Path

from doctor._common import BOLD, RED, RESET, YELLOW
from doctor.integrity import determine_active_project


DIAGNOSE_PATTERNS = ("loop", "red-miss", "repeat-not-ready", "scope-violation", "none")


def _read_project_files(workspace: Path, project: str) -> dict:
    """진단 입력을 모은다. 없는 파일은 조용히 None."""
    proj_dir = workspace / "projects" / project
    out = {
        "project_dir": proj_dir,
        "plan_md": None,
        "focus_md": None,
        "project_md": None,
        "state_yml": None,
    }
    for key, name in (("plan_md", ".plan.md"), ("focus_md", ".focus.md"),
                      ("project_md", "project.md"), ("state_yml", ".agent-state.yml")):
        p = proj_dir / name
        if p.is_file():
            try:
                out[key] = p.read_text(encoding="utf-8")
            except Exception:
                pass
    return out


def _pattern_red_miss(captured: dict) -> tuple[bool, str]:
    """tdd:true 프로젝트에서 .plan.md 스텝에 [Red] 누락 여부."""
    state = captured.get("state_yml") or ""
    if "tdd: true" not in state:
        return False, ""
    plan = captured.get("plan_md") or ""
    if not plan:
        return False, ""
    step_headers = re.findall(r"^(?:#{2,4})\s*(?:스텝|Step)\s*\d+", plan, re.MULTILINE)
    red_marks = plan.count("[Red]")
    green_marks = plan.count("[Green]")
    if step_headers and red_marks < len(step_headers):
        missing = len(step_headers) - red_marks
        return True, f"{len(step_headers)} 스텝 중 [Red] {red_marks} · [Green] {green_marks} — {missing} 스텝 누락"
    return False, ""


def _pattern_repeat_not_ready(captured: dict) -> tuple[bool, str]:
    """동일 feature 에 대해 NOT_READY / 반려 이력이 2회 이상."""
    plan = captured.get("plan_md") or ""
    project = captured.get("project_md") or ""
    combined = plan + "\n" + project
    not_ready = len(re.findall(r"status:\s*NOT_READY", combined))
    rejections = len(re.findall(r"반려|재수행 요청|재작성 요청", combined))
    total = not_ready + rejections
    if total >= 2:
        return True, f"NOT_READY {not_ready} · 반려 {rejections} (합계 {total})"
    return False, ""


def _pattern_loop(captured: dict) -> tuple[bool, str]:
    """.plan.md 에서 동일 작업 설명이 3회+ 반복되면 루프 의심."""
    plan = captured.get("plan_md") or ""
    if not plan:
        return False, ""
    counts: dict[str, int] = {}
    for line in plan.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(">") or s.startswith("-") and len(s) < 20:
            continue
        if 20 <= len(s) <= 120:
            counts[s] = counts.get(s, 0) + 1
    repeats = [(line, n) for line, n in counts.items() if n >= 3]
    if repeats:
        top = max(repeats, key=lambda x: x[1])
        return True, f"`{top[0][:60]}...` {top[1]}회 반복"
    return False, ""


def _pattern_scope_violation(captured: dict, service_repo: Path) -> tuple[bool, str]:
    """git diff --name-only 가 .focus.md scope 밖 경로를 포함하는지.

    service_repo: 서비스 레포 루트 (= workspace 의 부모, CWD). 플러그인 루트 아님 —
    scope-guard.sh 와 동일한 기준으로 사용자의 실제 작업 레포 변경을 본다.
    """
    focus = captured.get("focus_md") or ""
    if not focus:
        return False, ""
    scope_paths = re.findall(r"[\w./\-*]+\.(?:rb|py|ts|tsx|js|jsx|go|rs|md)", focus)
    scope_paths += re.findall(r"(?:app|lib|src|spec|test|tests)/[\w./\-*]+", focus)
    if not scope_paths:
        return False, ""
    try:
        out = subprocess.run(
            ["git", "-C", str(service_repo), "diff", "--name-only"],
            capture_output=True, text=True, timeout=5,
        )
        changed = [l for l in out.stdout.splitlines() if l.strip()]
    except Exception:
        return False, ""
    if not changed:
        return False, ""
    violations = []
    for f in changed:
        if not any(s in f or f.startswith(s.rstrip("*")) for s in scope_paths):
            violations.append(f)
    if violations:
        sample = ", ".join(violations[:3])
        more = f" (+{len(violations)-3})" if len(violations) > 3 else ""
        return True, f"{len(violations)} 파일 scope 외: {sample}{more}"
    return False, ""


def _recommend_action(pattern: str) -> str:
    return {
        "loop":             "feature 재분할 제안 — planner 재호출 또는 스텝 크기 축소",
        "red-miss":         "generator 재호출 시 `.plan.md` 에 [Red]/[Green] 증거 기록 강제",
        "repeat-not-ready": "planner 재진입 — feature spec 또는 scope 재정의 필요",
        "scope-violation":  "현 편집을 되돌리거나 `.focus.md` scope 확장 후 재진입",
        "none":             "없음 — 정상 진행",
    }.get(pattern, "unknown")


def run_diagnose(workspace: Path, project: str | None) -> int:
    """`--diagnose` 모드 진입점. 런타임 실패 패턴 진단."""
    print(f"{BOLD}pilot doctor [--diagnose]{RESET}  workspace: {workspace}\n")

    project = project or determine_active_project(workspace)
    if not project:
        print(f"{YELLOW}활성 프로젝트 없음{RESET} — `--project` 로 지정 필요")
        return 1

    captured = _read_project_files(workspace, project)
    # 서비스 레포 = workspace 의 부모 (= CWD, scope-guard.sh 와 동일 기준).
    # 플러그인 루트가 아님에 주의 — 플러그인은 지식, diff 대상은 사용자 작업 레포.
    service_repo = workspace.parent

    checks = [
        ("loop",             _pattern_loop(captured)),
        ("red-miss",         _pattern_red_miss(captured)),
        ("repeat-not-ready", _pattern_repeat_not_ready(captured)),
        ("scope-violation", _pattern_scope_violation(captured, service_repo)),
    ]

    hits = [(p, ev) for p, (matched, ev) in checks if matched]

    if not hits:
        pattern, evidence, confidence = "none", "정상 — 감지된 패턴 없음", "high"
    elif len(hits) == 1:
        pattern, evidence = hits[0]
        confidence = "high"
    else:
        # 우선순위: red-miss > repeat-not-ready > scope-violation > loop
        priority = {"red-miss": 0, "repeat-not-ready": 1, "scope-violation": 2, "loop": 3}
        hits.sort(key=lambda x: priority.get(x[0], 99))
        pattern, evidence = hits[0]
        evidence += f" (+{len(hits)-1} 다른 패턴 동시 감지)"
        confidence = "medium"

    print(f"## DIAGNOSIS")
    print(f"- project: {project}")
    print(f"- pattern: {pattern}")
    print(f"- evidence: {evidence}")
    print(f"- recommended_action: {_recommend_action(pattern)}")
    print(f"- confidence: {confidence}")

    return 0 if pattern == "none" else 1
