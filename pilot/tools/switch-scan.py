#!/usr/bin/env python3
"""pilot switch-scan — workspace 의 projects/·issues/ 에서 최근 작업 목록을 파생.

`/pilot:switch` 스킬이 Bash 1회로 호출하는 읽기 전용 조회 도구.
목록은 호출 시점에 폴더에서 파생한다 — 저장 상태를 만들지 않는다 (stateless,
이력의 SSOT 는 폴더 자체 — preamble P2 원칙). STATE.md 는 활성 마커 표시
용도로만 읽으며, 어떤 파일도 쓰지 않는다. 표준 라이브러리만 사용한다
(다른 tools/*.py 와 동일한 컨트랙트).

Usage:
    python3 switch-scan.py WORKSPACE_PATH           # markdown 표 (최근순 상위 10건)
    python3 switch-scan.py WORKSPACE_PATH --all     # cap 없이 전체
    python3 switch-scan.py WORKSPACE_PATH --json    # 전체 목록 JSON (테스트·기계 소비용)

출력 컬럼:
    mode(project|issue) · 이름(STATE 활성 행 일치 시 ◀ 활성) ·
    상태(analyzed·tdd·chr 부기 — `.agent-state.yml` 파생) ·
    진행(project 목표 [x]/전체 · issue 조치완/미완) ·
    최근(YYYY-MM-DD) · 요약

파생 규칙 (전부 관대 fallback — 폴더 상태 검증은 pilot-doctor 소관):
    - 상태: `.agent-state.yml` 의 analyzed(→`분석완`)·tdd(→`tdd`)·
      mode: characterize(→`chr`)·phase: qa(→`qa`) 를 `·` 로 연결. 전부 부재 → `-`.
    - 진행: project = project.md `## 목표` 체크박스 계수. 파일·섹션·체크박스
      부재 또는 항목 전부 placeholder (`{` 시작) → `-`.
      issue = issue.md `## 조치` 섹션 기반 3값 — 실내용 있음 `조치완` /
      템플릿 placeholder·빈 내용뿐 `미완` / 섹션 부재 (비템플릿 legacy) `-`
      (조치 기입이 완료 신호라는 issues/GUIDE 계약의 프록시).
    - cap 초과 시 `외 N건` 문구에 밀린 `미완` 이슈 수를 병기 (침묵 절단 금지).
    - 요약: project = 개요 첫 줄 → (placeholder 면) 목표 첫 비-placeholder
      항목 → 폴더명. issue = issue.md H1 → 폴더명.
    - 최근: 폴더 내 파일 최대 mtime (깊이 2, `*.bak`·`.prompts.bak/` 제외).
      동률은 이름 오름차순.

Exit:
    0 — 성공 (degraded WARN 포함 — corrupt STATE·활성 폴더 부재는 WARN 후 계속)
    1 — workspace 부재
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

# tools/ 를 sys.path 에 추가 — `doctor` 패키지의 STATE 파서를 재사용하기 위해
# (doctor.py 와 동일 메커니즘. 파서 복제 금지 — 파싱 규약 SSOT 유지).
_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from doctor._common import parse_state_md_all_rows  # noqa: E402

CAP = 10
SUMMARY_MAX = 40
ACTIVE_MARK = "◀ 활성"

# issue.md `## 조치` 의 템플릿 placeholder (issues/GUIDE.md § issue.md 템플릿과
# 정확 일치 계약 — 테스트가 GUIDE 본문 포함 여부로 drift 를 감지한다).
# 접두/접미 패턴이 아닌 정확 일치라 정당한 한 줄 italic 조치를 오인하지 않는다.
ACTION_PLACEHOLDER = "_(수정 완료 후 자동 기입)_"

_GOAL_RE = re.compile(r"^- \[( |x)\] (.+)$")
_GOAL_LINK_SUFFIX_RE = re.compile(r"\s*->\s*\[[^\]]*\]\([^)]*\)\s*$")
_STATE_KEY_RE = re.compile(r"^(analyzed|tdd|mode|phase):\s*(.+?)\s*$")


def _is_placeholder(text: str) -> bool:
    """스캐폴딩 템플릿의 미기입 표식 (`{…}`) 여부."""
    return text.lstrip().startswith("{")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def latest_mtime(root: Path) -> float:
    """폴더 내 최대 mtime (깊이 2). 백업 산출물 (`*.bak`·`.prompts.bak/`) 제외.

    폴더 자체 mtime 은 직계 자식 변경만 반영하므로 파일 단위로 본다.
    """

    def _skip(p: Path) -> bool:
        return p.name.endswith(".bak") or p.name == ".prompts.bak"

    best = root.stat().st_mtime
    try:
        children = list(root.iterdir())
    except OSError:
        return best
    for child in children:
        if _skip(child):
            continue
        try:
            best = max(best, child.stat().st_mtime)
        except OSError:
            continue
        if child.is_dir():
            try:
                grandchildren = list(child.iterdir())
            except OSError:
                continue
            for g in grandchildren:
                if _skip(g):
                    continue
                try:
                    best = max(best, g.stat().st_mtime)
                except OSError:
                    continue
    return best


def parse_agent_state(path: Path) -> "dict[str, str]":
    """`.agent-state.yml` 의 analyzed·tdd·mode 만 라인 파싱 (frontmatter 펜스 무시)."""
    out: "dict[str, str]" = {}
    for line in _read_text(path).splitlines():
        m = _STATE_KEY_RE.match(line.strip())
        if m:
            out[m.group(1)] = m.group(2).strip("\"'")
    return out


def parse_project_md(path: Path) -> "tuple[str, list[tuple[bool, str]]]":
    """project.md 에서 (개요 첫 줄, 목표 체크박스 목록) 을 뽑는다."""
    overview = ""
    goals: "list[tuple[bool, str]]" = []
    section = ""
    for line in _read_text(path).splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if section == "개요":
            stripped = line.strip()
            if stripped and not overview and not stripped.startswith(">"):
                overview = stripped
        elif section == "목표":
            m = _GOAL_RE.match(line)
            if m:
                text = _GOAL_LINK_SUFFIX_RE.sub("", m.group(2)).strip()
                goals.append((m.group(1) == "x", text))
    return overview, goals


def _truncate(text: str) -> str:
    text = " ".join(text.split())
    if len(text) > SUMMARY_MAX:
        return text[: SUMMARY_MAX - 1] + "…"
    return text


def _state_column(state: "dict[str, str]") -> str:
    """`.agent-state.yml` 파생 상태 표기 — `분석완`·`tdd`·`chr`·`qa` 를 `·` 연결."""
    parts: "list[str]" = []
    if state.get("analyzed") == "true":
        parts.append("분석완")
    if state.get("tdd") == "true":
        parts.append("tdd")
    if state.get("mode") == "characterize":
        parts.append("chr")
    if state.get("phase") == "qa":
        parts.append("qa")
    return "·".join(parts) if parts else "-"


def scan_project(folder: Path) -> "dict[str, object]":
    overview, goals = parse_project_md(folder / "project.md")
    state = parse_agent_state(folder / ".agent-state.yml")

    real_goals = [g for g in goals if not _is_placeholder(g[1])]
    if goals and real_goals:
        progress = "{}/{}".format(sum(1 for done, _ in goals if done), len(goals))
    else:
        progress = "-"

    summary = ""
    if overview and not _is_placeholder(overview):
        summary = overview
    elif real_goals:
        summary = real_goals[0][1]
    if not summary:
        summary = folder.name

    return {
        "mode": "project",
        "name": folder.name,
        "state": _state_column(state),
        "progress": progress,
        "summary": _truncate(summary),
    }


def _issue_action_progress(text: str) -> str:
    """issue.md `## 조치` 섹션 기반 진행 판정 — `조치완` / `미완` / `-`.

    실내용 줄 = 비공백이며 템플릿 placeholder (정확 일치) 도 `{` placeholder 도
    아닌 줄. 섹션 부재 (비템플릿 legacy) 는 판정 불가 `-`. 펜스 코드블록은
    인식하지 않는다 (parse_project_md 와 동일 한계 — 의도적 상속, 테스트로 고정).
    """
    section = ""
    seen = False
    filled = False
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            seen = seen or section == "조치"
            continue
        if section != "조치":
            continue
        stripped = line.strip()
        if stripped and stripped != ACTION_PLACEHOLDER and not _is_placeholder(stripped):
            filled = True
    if not seen:
        return "-"
    return "조치완" if filled else "미완"


def scan_issue(folder: Path) -> "dict[str, object]":
    text = _read_text(folder / "issue.md")
    summary = ""
    for line in text.splitlines():
        if line.startswith("# "):
            summary = line[2:].strip()
            break
    if not summary or _is_placeholder(summary):
        summary = folder.name
    return {
        "mode": "issue",
        "name": folder.name,
        "state": "-",
        "progress": _issue_action_progress(text),
        "summary": _truncate(summary),
    }


def collect_items(workspace: Path) -> "list[dict[str, object]]":
    items: "list[dict[str, object]]" = []
    for sub, scan in (("projects", scan_project), ("issues", scan_issue)):
        base = workspace / sub
        if not base.is_dir():
            continue  # issues/ 없는 워크스페이스도 정상
        for folder in sorted(base.iterdir()):
            if not folder.is_dir():
                continue
            item = scan(folder)
            mtime = latest_mtime(folder)
            item["mtime"] = mtime
            item["date"] = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
            items.append(item)
    items.sort(key=lambda it: (-float(it["mtime"]), str(it["name"])))
    return items


def read_active(workspace: Path) -> "tuple[list[tuple[str, str]], list[str]]":
    """STATE.md 의 진행중 (mode, name) 쌍 + degraded WARN 목록.

    STATE.md 부재는 정상 (마커 없이 목록만). corrupt (진행중 ≥2행) 는
    WARN 후 계속 — 본 도구는 복구 진입점이라 fail-fast 하지 않는다.
    """
    warnings: "list[str]" = []
    rows = parse_state_md_all_rows(workspace / "STATE.md")
    active = [(m, n) for (m, n, status) in rows if status == "진행중"]
    if len(active) > 1:
        warnings.append(
            "WARN: STATE.md 에 진행중 행이 {}개입니다 — `/pilot:pilot-doctor` 로 진단하세요.".format(
                len(active)
            )
        )
    for mode, name in active:
        sub = "projects" if mode == "project" else "issues"
        if mode in ("project", "issue") and name != "-" and not (workspace / sub / name).is_dir():
            warnings.append(
                "WARN: STATE.md 활성 {} '{}' 의 폴더가 {}/ 에 없습니다 — `/pilot:pilot-doctor` 로 진단하세요.".format(
                    mode, name, sub
                )
            )
    return active, warnings


def _md_cell(text: str) -> str:
    return text.replace("|", "\\|")


def render_markdown(
    items: "list[dict[str, object]]",
    active: "list[tuple[str, str]]",
    warnings: "list[str]",
    show_all: bool,
) -> str:
    lines: "list[str]" = []
    lines.extend(warnings)
    if warnings:
        lines.append("")

    if not items:
        lines.append(
            "작업 폴더가 없습니다 — 새로 시작하려면 `/pilot:project {이름}` 또는 `/pilot:issue {이슈명}`."
        )
        return "\n".join(lines)

    shown = items if show_all else items[:CAP]
    active_set = set(active)
    lines.append("| mode | 이름 | 상태 | 진행 | 최근 | 요약 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for it in shown:
        name = str(it["name"])
        if (str(it["mode"]), name) in active_set:
            name = "{} {}".format(name, ACTIVE_MARK)
        lines.append(
            "| {} | {} | {} | {} | {} | {} |".format(
                it["mode"],
                _md_cell(name),
                _md_cell(str(it["state"])),
                it["progress"],
                it["date"],
                _md_cell(str(it["summary"])),
            )
        )
    rest = len(items) - len(shown)
    if rest > 0:
        hidden_unresolved = sum(
            1
            for it in items[len(shown) :]
            if it["mode"] == "issue" and it["progress"] == "미완"
        )
        note = " (미완 이슈 {}건 포함)".format(hidden_unresolved) if hidden_unresolved else ""
        lines.append("")
        lines.append("외 {}건{} — `--all` 로 전체 표시".format(rest, note))
    return "\n".join(lines)


def main(argv: "list[str]") -> int:
    parser = argparse.ArgumentParser(
        prog="switch-scan.py", description="workspace 최근 작업 목록 파생 (읽기 전용)"
    )
    parser.add_argument("workspace", help="workspace 디렉토리 경로")
    parser.add_argument("--all", action="store_true", help="상위 {}건 cap 해제".format(CAP))
    parser.add_argument("--json", action="store_true", help="전체 목록 JSON 출력")
    args = parser.parse_args(argv)

    workspace = Path(args.workspace)
    if not workspace.is_dir():
        print("workspace/ 가 없습니다. 먼저 `/pilot:pilot-init` 으로 초기화하세요.")
        return 1

    items = collect_items(workspace)
    active, warnings = read_active(workspace)

    if args.json:
        active_set = set(active)
        payload = {
            "warnings": warnings,
            "count": len(items),
            "items": [
                {
                    "mode": it["mode"],
                    "name": it["name"],
                    "active": (str(it["mode"]), str(it["name"])) in active_set,
                    "state": it["state"],
                    "progress": it["progress"],
                    "date": it["date"],
                    "summary": it["summary"],
                }
                for it in items
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(render_markdown(items, active, warnings, args.all))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
