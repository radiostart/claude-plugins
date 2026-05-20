#!/usr/bin/env python3
"""
pilot orchestrate-load — wrapper agents 용 컨텍스트 로드 의사결정.

래퍼 (@pilot-planner / @pilot-generator / @pilot-evaluator) 가 프로젝트 workspace 를 조사해서
어떤 파일을 Read 해야 하는지 결정하는 로직을 여기로 이관.

입력:
    --phase {planner|generator|evaluator}
    --workspace PATH          (default: ./workspace)
    --project NAME            (optional — 미지정 시 STATE.md 진행중)

출력 (stdout, JSON):
    {
      "phase": "planner",
      "project": "MyProject",
      "domain": "<domain-name>" | null,
      "analyzed": bool,
      "tdd": bool,
      "focus": string | null,
      "files_to_read": [...],   # 순서대로
      "hints": [...],           # 자유 형식 힌트 (래퍼 프롬프트에 포함)
      "error": string | null
    }

Exit:
    0 — 성공
    1 — 치명 오류 (error 필드 참조)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

SCHEMA_VERSION = "v1.2"
SUPPORTED_SCHEMAS = ["v1.1", "v1.2"]  # v1.1 도 읽기 허용 (하위호환). v1 은 doctor --fix 로 강제 업그레이드
PLUGIN_ROOT_ENV = "CLAUDE_PLUGIN_ROOT"


def read_plugin_version() -> str | None:
    """`$CLAUDE_PLUGIN_ROOT/.claude-plugin/plugin.json` 의 version. 못 읽으면 None."""
    root = os.environ.get(PLUGIN_ROOT_ENV)
    if not root:
        return None
    pj = Path(root) / ".claude-plugin" / "plugin.json"
    if not pj.is_file():
        return None
    try:
        data = json.loads(pj.read_text(encoding="utf-8"))
        v = data.get("version")
        return v if isinstance(v, str) else None
    except Exception:
        return None


def parse_semver(v: str | None) -> tuple[int, int, int] | None:
    """`0.1.75` → `(0, 1, 75)`. 실패 시 None."""
    if not v or not isinstance(v, str):
        return None
    try:
        parts = v.strip().split(".")
        nums = [int(p) for p in parts[:3]]
        while len(nums) < 3:
            nums.append(0)
        return (nums[0], nums[1], nums[2])
    except Exception:
        return None


def compare_plugin_version(state_ver: str | None, current_ver: str | None) -> tuple[str, str] | None:
    """
    state 의 plugin_version 과 현재 실행 플러그인 버전 비교.
    Returns (level, message) | None. level ∈ {"INFO", "WARN"}.
    patch 차이는 silent.
    """
    if current_ver is None:
        return None  # 플러그인 루트 모름 → skip (테스트 환경 등)
    if state_ver is None:
        return (
            "INFO",
            f"plugin_version 미기록 (legacy state). 현재 플러그인 {current_ver} — "
            "다음 `/pilot:project` / `/pilot:analyze` 실행 시 자동 기록.",
        )
    sv = parse_semver(state_ver)
    cv = parse_semver(current_ver)
    if sv is None or cv is None:
        return None
    if sv[:2] == cv[:2]:
        return None  # patch 차이는 무시
    if sv < cv:
        return (
            "WARN",
            f"플러그인이 {state_ver} → {current_ver} 로 업그레이드됨. "
            "wrapper 계약 변경 가능성 — `/pilot:analyze --regen-agents` 권장.",
        )
    return (
        "WARN",
        f"state.plugin_version ({state_ver}) 이 현재 플러그인 ({current_ver}) 보다 높음. "
        "플러그인 업데이트 또는 state 확인 필요.",
    )


def parse_state_md_active(state_md: Path) -> list[str]:
    """STATE.md 에서 진행중 행들의 이름 목록 반환."""
    if not state_md.is_file():
        return []
    active = []
    for line in state_md.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("|") and "진행중" in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 3 and cells[2] == "진행중":
                active.append(cells[1])
    return active


def parse_state_yml(yml: Path) -> dict | None:
    """Flat YAML parser for state file. Returns dict or None."""
    if not yml.is_file():
        return None
    data = {}
    try:
        for line in yml.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()
            # strip surrounding quotes
            if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
                v = v[1:-1]
            if v in ("true", "True"):
                data[k] = True
            elif v in ("false", "False"):
                data[k] = False
            elif v in ("null", "~", ""):
                data[k] = None
            elif v.isdigit():
                data[k] = int(v)
            else:
                data[k] = v
    except Exception:
        return None
    return data


LANG_KEYS = (
    "language",
    "test_command",
    "test_command_fail_fast",
    "coverage_command",
    "lint_command",
    "test_path_convention",
    "source_root",
    "test_framework_hints",
    "conventions_doc",
    "conventions_evals",
)


def parse_lang_tools(config_md: Path) -> dict[str, str]:
    """
    config.md 의 `## 언어·도구 기본값` 섹션에서 표 행을 파싱.
    | `key` | `value` | 설명 | 형식만 지원. 반환 키는 LANG_KEYS 에 제한.

    호출 대상: `workspace/context/config.md`
    """
    if not config_md.is_file():
        return {}
    try:
        text = config_md.read_text(encoding="utf-8")
    except Exception:
        return {}
    m = re.search(
        r"##\s*언어[·\s]*도구[\s]*기본값([\s\S]*?)(?:\n##\s|\Z)", text
    )
    if not m:
        return {}
    section = m.group(1)
    result: dict[str, str] = {}
    for line in section.splitlines():
        row = re.match(
            r"^\|\s*`?([a-z_]+)`?\s*\|\s*`?([^`|]+?)`?\s*\|", line
        )
        if row:
            key = row.group(1).strip()
            value = row.group(2).strip()
            if key in LANG_KEYS and value and value != "값":
                result[key] = value
    return result


def parse_lang_override(project_md: Path) -> dict[str, str]:
    """
    project.md 제한사항 섹션에서 `- key: value` 형식 override 파싱.
    (backtick 래핑 선택) 반환 키는 LANG_KEYS 에 제한.
    """
    if not project_md.is_file():
        return {}
    try:
        text = project_md.read_text(encoding="utf-8")
    except Exception:
        return {}
    m = re.search(r"##\s*제한사항([\s\S]*?)(?:\n##\s|\Z)", text)
    if not m:
        return {}
    section = m.group(1)
    result: dict[str, str] = {}
    for line in section.splitlines():
        row = re.match(
            r"^\s*-\s*\*?\*?([a-z_]+)\*?\*?\s*:\s*`?([^`\n]+?)`?\s*$", line
        )
        if row:
            key = row.group(1).strip()
            value = row.group(2).strip()
            if key in LANG_KEYS:
                result[key] = value
    return result


def determine_domain(project_md: Path) -> str | None:
    """
    project.md 의 제한사항 등에서 `domain: xxx` 패턴 추출.
    MANIFEST 기반 키워드 매칭은 여기서 안 함 (LLM/사용자 판단이 더 정확).
    판단 불가 시 None 반환 — wrapper 가 사용자에게 확인 요청.
    """
    if not project_md.is_file():
        return None
    try:
        text = project_md.read_text(encoding="utf-8")
    except Exception:
        return None
    m = re.search(r"^\s*-?\s*\*?\*?domain\*?\*?\s*:\s*(\S+)", text, re.MULTILINE)
    if m:
        return m.group(1).strip("`*")
    return None


def parse_manifest_domain_files(manifest_md: Path, domain: str) -> list[str]:
    """
    MANIFEST.md `## 도메인 분류` 표에서 해당 domain 의 진입 파일 경로 추출.

    형식: `| {도메인} | <백틱>진입 파일<백틱> | {설명} |` (3 컬럼, 진입 파일 컬럼은
    backtick·공백 허용). MANIFEST 가 자유 형식이라 best-effort — 매칭 실패 시
    빈 리스트 반환 (호출자가 graceful degrade).

    반환: workspace/context/ 기준 상대 경로 리스트 (예: `["orders.md"]`,
    `["payments/index.md"]`). 절대경로·workspace/context/ 접두는 제거.
    """
    if not manifest_md.is_file() or not domain:
        return []
    try:
        text = manifest_md.read_text(encoding="utf-8")
    except Exception:
        return []
    # `## 도메인 분류` 섹션 추출 (한국어 헤딩만 인식 — 영문은 향후 확장)
    m = re.search(r"##\s*도메인\s*분류([\s\S]*?)(?:\n##\s|\Z)", text)
    if not m:
        return []
    section = m.group(1)
    # 표 행에서 도메인 일치하는 행 찾기
    for line in section.splitlines():
        row = re.match(
            r"^\|\s*`?([^`|\s]+)`?\s*\|\s*`?([^`|]+?)`?\s*\|", line
        )
        if not row:
            continue
        row_domain = row.group(1).strip()
        if row_domain != domain:
            continue
        entry = row.group(2).strip().strip("`").strip()
        if not entry or entry.lower() in ("진입 파일", "entry"):
            continue
        # workspace/context/ 접두 제거 (작성자 실수 보정)
        entry = entry.lstrip("/")
        if entry.startswith("workspace/context/"):
            entry = entry[len("workspace/context/"):]
        elif entry.startswith("context/"):
            entry = entry[len("context/"):]
        return [entry]
    return []


def read_focus(focus_md: Path) -> str | None:
    """.focus.md 의 본문 (첫 # 헤더 제외) 반환. 없으면 None."""
    if not focus_md.is_file():
        return None
    try:
        text = focus_md.read_text(encoding="utf-8").strip()
    except Exception:
        return None
    if not text:
        return None
    lines = text.splitlines()
    if lines and lines[0].lstrip().startswith("#"):
        body = "\n".join(lines[1:]).strip()
        return body or None
    return text


def plugin_root() -> str:
    """$CLAUDE_PLUGIN_ROOT env. 없으면 리터럴 placeholder 로 남김."""
    return os.environ.get(PLUGIN_ROOT_ENV, "${CLAUDE_PLUGIN_ROOT}")


def build_load_plan(
    workspace: Path,
    project: str,
    domain: str | None,
    analyzed: bool,
    tdd: bool,
    phase: str,
    mode: str | None = None,
) -> tuple[list[str], list[str], dict[str, str]]:
    """
    Returns (files_to_read, hints, config).

    files_to_read 는 Claude Code 의 Read 툴이 처리 가능한 경로 문자열:
    - workspace-상대 경로 (e.g. "workspace/context/MANIFEST.md")
    - `${CLAUDE_PLUGIN_ROOT}/...` 플러그인 내 파일 (rgr.md, coding.md)
    존재하지 않는 파일은 목록에 포함하지 않는다.

    config 는 언어·도구 기본값 병합 결과:
      `workspace/context/config.md` → `project.md` 제한사항 (프로젝트 override).
    지원 키는 `LANG_KEYS` 참조.
    `conventions_doc` / `conventions_evals` 는 workspace-상대 경로이며
    generator phase 에서 존재 시 자동으로 `files_to_read` 에 추가된다.
    """
    files: list[str] = []
    hints: list[str] = []
    config: dict[str, str] = {}

    def add_if_exists(abs_path: Path, rel_path: str) -> bool:
        if abs_path.is_file():
            files.append(rel_path)
            return True
        return False

    # 0) SSOT — 모든 wrapper 가 톤·instinct·판정 축을 강제 로드.
    #    페르소나는 identity.yml 의 personas.{phase} 가 자기 역할에 해당.
    for ssot in ("identity.yml", "instincts.yaml", "guardrails.md"):
        files.append(f"{plugin_root()}/skills/context/shared/{ssot}")
    hints.append(
        f"페르소나: identity.yml `personas.{phase}` 적용 (voice·phrasing·forbid 준수)"
    )

    # 1) context — 도메인 지식(MANIFEST.md) + 런타임 설정(config.md)
    manifest_abs = workspace / "context" / "MANIFEST.md"
    add_if_exists(manifest_abs, "workspace/context/MANIFEST.md")
    config_abs = workspace / "context" / "config.md"
    if config_abs.is_file():
        config.update(parse_lang_tools(config_abs))

    # 2) project.md (always if exists)
    project_md_abs = workspace / "projects" / project / "project.md"
    project_md_exists = add_if_exists(
        project_md_abs, f"workspace/projects/{project}/project.md"
    )
    if not project_md_exists:
        hints.append("project.md 없음 — 에이전트 가이드만으로 작업")

    # 3) prompts/{phase}.md (if exists)
    prompt_abs = workspace / "projects" / project / "prompts" / f"{phase}.md"
    prompt_exists = add_if_exists(
        prompt_abs,
        f"workspace/projects/{project}/prompts/{phase}.md",
    )
    if not prompt_exists:
        hints.append(
            f"prompts/{phase}.md 없음 — project.md 만으로 작업"
        )

    # 4) MANIFEST 의 도메인 진입 파일 자동 로드
    #    MANIFEST 의 `## 도메인 분류` 표에서 해당 domain 의 entry 파일 경로 추출.
    #    플러그인은 MANIFEST 만 알면 된다 — workspace/context/ 하위의 폴더 구조·
    #    파일명 컨벤션은 워크스페이스가 자유롭게 결정한다 (플러그인은 강제하지 않음).
    if domain:
        entries = parse_manifest_domain_files(manifest_abs, domain)
        if entries:
            for rel in entries:
                entry_abs = workspace / "context" / rel
                if add_if_exists(entry_abs, f"workspace/context/{rel}"):
                    hints.append(f"MANIFEST 도메인 진입 파일 로드: context/{rel}")
        else:
            hints.append(
                f"도메인 '{domain}' 의 진입 파일이 MANIFEST 에 등록되지 않음 — "
                "`/pilot:learn {진입점}` 으로 부트스트랩하거나 MANIFEST 의 `## 도메인 분류` 표에 행 추가"
            )
    else:
        hints.append("도메인 판정 실패 — 도메인 컨텍스트 로드 skip. 사용자 확인 필요.")

    # 6) generator 만 coding.md (플러그인 언어중립판) + workspace conventions_doc/evals (언어별)
    if phase == "generator":
        files.append(f"{plugin_root()}/skills/context/shared/coding.md")
        for key in ("conventions_doc", "conventions_evals"):
            rel = config.get(key)
            if not rel:
                continue
            rel = rel.lstrip("/")
            # MANIFEST 값은 workspace-상대 경로. "workspace/" 접두사가 있으면 제거.
            if rel.startswith("workspace/"):
                rel = rel[len("workspace/"):]
            abs_path = workspace / rel
            load_path = f"workspace/{rel}"
            if abs_path.is_file():
                files.append(load_path)
            else:
                hints.append(
                    f"{key}={rel} 로 선언됐으나 파일 없음 — workspace 에 생성 필요"
                )

    # 7) 모드 분기 — characterize 우선, 없으면 tdd, 둘 다 아니면 표준
    if mode == "characterize":
        files.append(f"{plugin_root()}/skills/context/modes/characterize.md")
        hints.append(
            "mode: characterize — characterize.md 절차 준수 ({source_root} 수정 금지, 테스트만 추가)"
        )
        if tdd:
            hints.append(
                "tdd: true 이지만 mode: characterize 가 우선 — Red 계약 대신 Characterization Contract 사용"
            )
    elif tdd:
        files.append(f"{plugin_root()}/skills/context/modes/rgr.md")
        hints.append("TDD 모드 — rgr.md 절차 준수 필수")
    else:
        hints.append("비 TDD 프로젝트")

    # 8) project.md 제한사항의 언어·도구 override 적용 (base 위에 덮어쓰기)
    project_md_abs = workspace / "projects" / project / "project.md"
    config.update(parse_lang_override(project_md_abs))
    if config:
        summary = " · ".join(f"{k}={v}" for k, v in config.items())
        hints.append(f"언어·도구: {summary}")
    else:
        hints.append(
            "언어·도구 기본값 미정의 — `workspace/context/config.md` 의 "
            "`## 언어·도구 기본값` 섹션 또는 project.md 제한사항에 키 등록 권장"
        )

    return files, hints, config


def main() -> int:
    parser = argparse.ArgumentParser(
        description="pilot orchestrate-load — LOAD phase 의사결정"
    )
    parser.add_argument(
        "--phase", required=True, choices=["planner", "generator", "evaluator"]
    )
    parser.add_argument("--workspace", default="workspace", help="workspace/ 경로")
    parser.add_argument(
        "--project", default=None, help="프로젝트명 (생략 시 STATE.md 진행중)"
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    result: dict = {
        "phase": args.phase,
        "project": None,
        "domain": None,
        "analyzed": None,
        "tdd": None,
        "mode": None,
        "focus": None,
        "config": {},
        "files_to_read": [],
        "hints": [],
        "error": None,
    }

    if not workspace.is_dir():
        result["error"] = (
            f"workspace not found: {workspace}. `/pilot:init` 실행 필요."
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    # P1: 활성 프로젝트
    active = parse_state_md_active(workspace / "STATE.md")
    project = args.project
    if not project:
        if len(active) == 1:
            project = active[0]
        elif len(active) == 0:
            result["error"] = (
                "활성 프로젝트 없음. `/pilot:project {이름}` 으로 활성화."
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1
        else:
            result["error"] = (
                f"STATE.md 에 진행중 {len(active)} 개 ({', '.join(active)}). "
                "1 개만 허용. STATE.md 수정 후 재시도 또는 --project 로 명시."
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1
    result["project"] = project

    # state.yml
    state_yml = workspace / "projects" / project / ".agent-state.yml"
    state = parse_state_yml(state_yml)
    if not state:
        result["error"] = (
            f".agent-state.yml 누락. `/pilot:project {project}` 재실행 또는 직접 작성."
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    schema = state.get("schema")
    if schema not in SUPPORTED_SCHEMAS:
        result["error"] = (
            f".agent-state.yml schema={schema!r} 가 이 플러그인에서 지원되지 않음 "
            f"(지원 버전: {', '.join(SUPPORTED_SCHEMAS)}). "
            "플러그인 업그레이드 또는 마이그레이션 필요."
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    result["analyzed"] = bool(state.get("analyzed"))
    result["tdd"] = bool(state.get("tdd"))

    # plugin_version drift 체크 (optional 필드 — 없어도 INFO 힌트만)
    pv_check = compare_plugin_version(
        state.get("plugin_version"), read_plugin_version()
    )
    if pv_check:
        level, msg = pv_check
        result["hints"].append(f"[{level}] {msg}")

    # mode: null | "characterize" (optional, v1.1+)
    state_mode = state.get("mode")
    if isinstance(state_mode, str) and state_mode:
        result["mode"] = state_mode

    # Domain — state 의 domain 필드 우선, null 이면 project.md 에서 추출
    project_md = workspace / "projects" / project / "project.md"
    state_domain = state.get("domain")
    if isinstance(state_domain, str) and state_domain:
        result["domain"] = state_domain
    else:
        result["domain"] = determine_domain(project_md)

    # Focus
    focus_md = workspace / "projects" / project / ".focus.md"
    result["focus"] = read_focus(focus_md)
    if result["focus"]:
        result["hints"].append(
            ".focus.md 존재 — 사용자 최근 지시. 후속 작업에 반드시 반영."
        )

    # Files + phase-specific hints + language/tools config
    files, phase_hints, config = build_load_plan(
        workspace=workspace,
        project=project,
        domain=result["domain"],
        analyzed=result["analyzed"],
        tdd=result["tdd"],
        phase=args.phase,
        mode=result["mode"],
    )
    result["files_to_read"] = files
    result["hints"].extend(phase_hints)
    result["config"] = config

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
