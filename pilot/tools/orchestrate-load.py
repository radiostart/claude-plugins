#!/usr/bin/env python3
"""
pilot orchestrate-load — wrapper agents 용 컨텍스트 로드 의사결정.

래퍼 (@pilot-planner / @pilot-planner-critic / @pilot-generator / @pilot-evaluator) 가 프로젝트
workspace 를 조사해서 어떤 파일을 Read 해야 하는지 결정하는 로직을 여기로 이관.

입력:
    --phase {planner|planner-critic|generator|evaluator}
    --workspace PATH          (default: ./workspace)
    --project NAME            (optional — 미지정 시 STATE.md 진행중.
                               명시 시 STATE 우회 project 모드 강제)

출력 (stdout, JSON):
    {
      "phase": "planner",
      "project": "MyProject",              # issue 모드에서는 이슈명
      "work_mode": "project" | "issue",    # STATE.md mode 열 (issue 외 → project 폴백)
      "project_phase": "development" | "qa",  # issue 모드는 "development" 고정
      "domain": "<domain-name>" | null,
      "analyzed": bool,                    # 보고용 — 로드 분기에 쓰이지 않는다
      "tdd": bool,
      "mode": string | null,
      "focus": string | null,
      "config": {...},          # 언어·도구 병합 결과 (LANG_KEYS)
      "instructions": [...],    # 결과 처리 공통 지시 — wrapper 는 이 지시를 따른다 (SSOT)
      "files_to_read": [...],   # 순서대로
      "hints": [...],           # 자유 형식 힌트 (래퍼 프롬프트에 포함)
      "error": string | null
    }

`instructions` 는 wrapper 4종에 공통이던 JSON 처리 지시의 정본이다 — wrapper .md 에
전문을 복제하지 않는다 (drift 방지). phase 별 focus 반영 지시만 값이 다르다.

issue 모드 (STATE.md `| issue | {이슈명} | 진행중 |`):
    상태 파일 없이 `issues/{이슈명}/issue.md` 가 단건 명세다 (stateless).
    analyzed=false, tdd=false, mode=null 고정 (`.agent-state.yml` 안 읽음).
    domain 은 issue.md 의 `도메인:`/`domain:` 라인에서 파싱.
    project.md·prompts/* 는 로드하지 않는다. 계약 상세: docs/how-to/issue-cycle.md.

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

# tools/ 를 sys.path 에 추가 — `doctor._common` 의 parse_state_yml·_parse_semver·
# parse_state_md_all_rows 를 재사용하기 위해 (dedup, #20 스텝 6-②, 근거:
# repo 루트 docs/audits/2026-07-24-audit-4-python.md § A). doctor.py 와 동일한 sys.path 패턴.
# 두 모듈 다 플러그인 tools/ 안에 함께 배포되므로 doctor 패키지 부재는 곧
# doctor.py 자체도 못 쓰는 상태 — 같은 실패 모드를 공유한다 (dedup 이 새 결합
# 리스크를 추가하지 않음).
_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from doctor._common import (  # noqa: E402
    parse_state_md_all_rows,
    parse_state_yml,
    _parse_semver as parse_semver,
)

SCHEMA_VERSION = "v1.2"
SUPPORTED_SCHEMAS = ["v1.1", "v1.2", "v1.3"]  # v1.1/v1.2 도 읽기 허용 (하위호환). v1 은 doctor --fix 로 강제 업그레이드

VALID_PROJECT_PHASES = ("development", "qa")


def resolve_project_phase(state: dict) -> "tuple[str | None, str | None]":
    """state 의 phase 필드를 검증·정규화. (phase, error) 반환.

    부재·null → ("development", None) — v1.2 이하 호환 기본값.
    유효 값 → (값, None). 그 외 → (None, 에러) — fail-closed:
    오타·corrupt 를 development 로 조용히 폴백하면 qa 게이트
    (최소 변경·회귀영향) 가 풀린다.
    """
    raw = state.get("phase")
    if raw is None:
        return "development", None
    if raw in VALID_PROJECT_PHASES:
        return raw, None
    return None, (
        f".agent-state.yml 의 phase={raw!r} 가 유효하지 않음 "
        f"(허용: {', '.join(VALID_PROJECT_PHASES)}). "
        "phase 행을 수정하거나 `doctor --fix` 로 재생성 필요."
    )
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


def parse_state_md_active(state_md: Path) -> list[tuple[str, str]]:
    """STATE.md 에서 진행중 행들의 (mode, 이름) 목록 반환.

    mode 열 값: `project` | `issue`. legacy 표 (`| 순번 | 이름 | 상태 |`) 는
    첫 칸이 순번 숫자 — 소비부가 `issue` 외 값을 project 로 폴백해 하위호환.
    행 파싱 SSOT 는 doctor/_common.parse_state_md_all_rows.
    """
    return [
        (mode, name)
        for mode, name, status in parse_state_md_all_rows(state_md)
        if status == "진행중"
    ]


LANG_KEYS = (
    "language",
    "test_command",
    "test_command_fail_fast",
    "coverage_command",
    "lint_command",
    "regression_command",
    "test_path_convention",
    "source_root",
    "test_framework_hints",
    "conventions_doc",
    "conventions_evals",
)


def parse_lang_tools(config_md: Path) -> dict[str, str] | None:
    """
    config.md 의 `## 언어·도구 기본값` 섹션에서 표 행을 파싱.
    | `key` | `value` | 설명 | 형식만 지원. 반환 키는 LANG_KEYS 에 제한.

    호출 대상: `workspace/context/config.md`

    반환값:
    - `dict` — 정상 파싱 (섹션·키 없으면 빈 dict).
    - `None` — 파일 부재 또는 읽기 예외 (호출부가 "손상" 으로 판단해 경고).
    """
    if not config_md.is_file():
        return None
    try:
        text = config_md.read_text(encoding="utf-8")
    except Exception:
        return None
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


def determine_domain(spec_md: Path) -> str | None:
    """
    project.md 제한사항 또는 issue.md 상단에서 `domain: xxx` / `도메인: xxx`
    패턴 추출. MANIFEST 기반 키워드 매칭은 여기서 안 함 (LLM/사용자 판단이
    더 정확). 판단 불가 시 None 반환 — wrapper 가 사용자에게 확인 요청.
    """
    if not spec_md.is_file():
        return None
    try:
        text = spec_md.read_text(encoding="utf-8")
    except Exception:
        return None
    m = re.search(
        r"^\s*-?\s*\*?\*?(?:domain|도메인)\*?\*?\s*:\s*(\S+)", text, re.MULTILINE
    )
    if m:
        return m.group(1).strip("`*")
    return None


def _strip_fenced_code_blocks(text: str) -> str:
    """마크다운 펜스 코드블록(``` ... ```)에 속한 줄을 제거한 텍스트를 반환.

    가이드·예시 코드블록 안의 `## 도메인 분류` 같은 리터럴이 실제 섹션
    헤더로 오인되는 것을 방지 (learn SKILL.md:80 의 "코드블록·prose 인용
    무시" 계약 완전 구현, #20 스텝 6-①·critic C4).
    """
    out: list[str] = []
    in_fence = False
    for line in text.splitlines(keepends=True):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        out.append(line)
    return "".join(out)


_DOMAIN_SECTION_HEADER_RE = re.compile(r"^##\s+도메인\s*분류\s*$", re.M)
_NEXT_H2_RE = re.compile(r"^##\s", re.M)


def parse_manifest_domain_files(manifest_md: Path, domain: str) -> list[str]:
    """
    MANIFEST.md `## 도메인 분류` 표에서 해당 domain 의 진입 파일 경로 추출.

    형식: `| {도메인} | <백틱>진입 파일<백틱> | {설명} |` (3 컬럼, 진입 파일 컬럼은
    backtick·공백 허용). MANIFEST 가 자유 형식이라 best-effort — 매칭 실패 시
    빈 리스트 반환 (호출자가 graceful degrade).

    섹션 헤더는 **단독 라인** `## 도메인 분류` 만 인식한다(anchored, re.M) —
    blockquote·본문 prose 안의 동일 문자열(예: 안내 문구가 이 리터럴을
    인용하는 경우)이 먼저 매칭돼 실제 표를 건너뛰는 오탐을 방지한다
    (#20 스텝 6-①, D1 승인 — 실버그 재현: prose 선매칭 시 표 파싱 누락).
    suffix 붙은 변형(`## 도메인 분류 (수동 관리)` 등)은 의도적으로 미매칭
    — 자동 로드 계약은 정확한 H2 리터럴을 요구한다(learn SKILL.md:80).

    도메인이 일치하는 **모든 행**을 표 순서대로 반환한다 (중복 제거).
    한 도메인이 여러 진입 파일을 등록할 수 있다 (예: 개요 + 상태 전이표).

    반환: workspace/context/ 기준 상대 경로 리스트 (예: `["orders.md"]`,
    `["payments/index.md"]`). 절대경로·workspace/context/ 접두는 제거.
    """
    if not manifest_md.is_file() or not domain:
        return []
    try:
        text = manifest_md.read_text(encoding="utf-8")
    except Exception:
        return []
    text = _strip_fenced_code_blocks(text)
    header_m = _DOMAIN_SECTION_HEADER_RE.search(text)
    if not header_m:
        return []
    rest = text[header_m.end():]
    next_h2 = _NEXT_H2_RE.search(rest)
    section = rest[: next_h2.start()] if next_h2 else rest
    # 표 행에서 도메인 일치하는 행 모두 수집
    entries: list[str] = []
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
        if entry not in entries:
            entries.append(entry)
    return entries


def parse_manifest_external_refs(manifest_md: Path) -> list[tuple[str, str]]:
    """MANIFEST `## 외부 도메인 reference` 표에서 (추정 도메인, 클래스 목록 문자열) 추출.

    헤더 서픽스 (예: "(learn 미완료)") 허용. learn 이 학습 완료 도메인 행을 제거하므로
    반환 목록 = 아직 학습되지 않은 외부 의존. 매칭 실패 시 빈 리스트 (graceful).
    """
    if not manifest_md.is_file():
        return []
    try:
        text = manifest_md.read_text(encoding="utf-8")
    except Exception:
        return []
    m = re.search(
        r"^##\s*외부\s*도메인\s*reference[^\n]*\n([\s\S]*?)(?:\n##\s|\Z)", text, re.M
    )
    if not m:
        return []
    refs: list[tuple[str, str]] = []
    for line in m.group(1).splitlines():
        row = re.match(r"^\|\s*`?([^`|\s]+)`?\s*\|\s*([^|]+?)\s*\|", line)
        if not row:
            continue
        dom = row.group(1).strip()
        classes = row.group(2).strip()
        # 헤더 행("추정 도메인" → 공백 전 "추정")·구분선 행 제외
        if dom == "추정" or set(dom) <= {"-", ":"}:
            continue
        refs.append((dom, classes))
    return refs


# 경계 계약 문서 로드 상한 — 초과분은 hint 로 안내 (토큰 경제)
MAX_BOUNDARY_DOCS = 6


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
        if body:
            return body
        # heading 만 있는 파일 — heading 텍스트 자체를 지시로 간주.
        # (본문이 비었다고 사용자 지시를 통째로 버리지 않는다.)
        heading = lines[0].lstrip().lstrip("#").strip()
        return heading or None
    return text


def plugin_root() -> str:
    """$CLAUDE_PLUGIN_ROOT env. 없으면 리터럴 placeholder 로 남김."""
    return os.environ.get(PLUGIN_ROOT_ENV, "${CLAUDE_PLUGIN_ROOT}")


def has_path_traversal(name: str) -> bool:
    """식별자(project/domain)에 경로 구분자나 `..` 가 있으면 True.

    이 값들은 workspace 하위 경로에 그대로 보간되므로, traversal 문자가
    있으면 workspace 밖 파일이 `files_to_read` 에 섞일 수 있다.
    """
    return "/" in name or "\\" in name or ".." in name


def build_load_plan(
    workspace: Path,
    project: str,
    domain: str | None,
    tdd: bool,
    phase: str,
    mode: str | None = None,
    work_mode: str = "project",
) -> tuple[list[str], list[str], dict[str, str]]:
    """
    Returns (files_to_read, hints, config).

    files_to_read 는 Claude Code 의 Read 툴이 처리 가능한 경로 문자열:
    - workspace-상대 경로 (e.g. "workspace/context/MANIFEST.md")
    - `${CLAUDE_PLUGIN_ROOT}/...` 플러그인 내 파일 (rgr.md, coding.md)
    존재하지 않는 파일은 목록에 포함하지 않는다.

    config 는 언어·도구 기본값 병합 결과:
      `workspace/context/config.md` → 작업 명세 (project.md / issue.md) 제한사항
    (프로젝트 override). 지원 키는 `LANG_KEYS` 참조.
    `conventions_doc` / `conventions_evals` 는 workspace-상대 경로이며
    generator·evaluator phase 에서 존재 시 자동으로 `files_to_read` 에 추가된다.
    """
    files: list[str] = []
    hints: list[str] = []
    config: dict[str, str] = {}

    def add_if_exists(abs_path: Path, rel_path: str) -> bool:
        if abs_path.is_file():
            files.append(rel_path)
            return True
        return False

    # 0) SSOT — 모든 wrapper 가 톤·판정 축 + 공통 계약을 강제 로드.
    #    페르소나는 identity.yml 의 personas.{phase} 가 자기 역할에 해당.
    #    wrapper-protocol.md 는 4 phase(agents/pilot-*.md) 공통 계약(경로 규칙·
    #    반환 JSON 처리·domain null 예외·부분 로드·탐색 제약·drift 대응) SSOT —
    #    각 agent .md 상단의 "Read 지시 1줄"과 이중화(#19 전달사항, D2 승인).
    #    CLAUDE_PLUGIN_ROOT 가 해석 가능하면 존재 확인 후 로드 — 파일 부재 시
    #    존재하지 않는 파일 Read 지시 대신 WARN 힌트로 우아하게 생략한다.
    resolved_root = os.environ.get(PLUGIN_ROOT_ENV)
    for ssot in ("identity.yml", "guardrails.md", "wrapper-protocol.md"):
        if resolved_root and not (
            Path(resolved_root) / "skills" / "context" / "shared" / ssot
        ).is_file():
            hints.append(f"[WARN] SSOT 파일 없음 — 로드 생략: shared/{ssot}")
            continue
        files.append(f"{plugin_root()}/skills/context/shared/{ssot}")
    hints.append(
        f"페르소나: identity.yml `personas.{phase}` 적용 (archetype·forbid 준수)"
    )

    # 1) context — 도메인 지식(MANIFEST.md) + 런타임 설정(config.md)
    manifest_abs = workspace / "context" / "MANIFEST.md"
    add_if_exists(manifest_abs, "workspace/context/MANIFEST.md")
    config_abs = workspace / "context" / "config.md"
    if config_abs.is_file():
        parsed = parse_lang_tools(config_abs)
        if parsed is None:
            hints.append(
                "[WARN] workspace/context/config.md 읽기 실패 — 언어·도구 기본값 누락"
            )
        else:
            config.update(parsed)

    # 2) 작업 명세 — project: project.md (없어도 진행) / issue: issue.md
    #    (issue.md 존재는 main 의 issue 분기가 이미 확인 — 부재면 여기 도달 전 에러)
    if work_mode == "issue":
        spec_md_abs = workspace / "issues" / project / "issue.md"
        add_if_exists(spec_md_abs, f"workspace/issues/{project}/issue.md")
    else:
        spec_md_abs = workspace / "projects" / project / "project.md"
        project_md_exists = add_if_exists(
            spec_md_abs, f"workspace/projects/{project}/project.md"
        )
        if not project_md_exists:
            hints.append("project.md 없음 — 에이전트 가이드만으로 작업")

    # 3) prompts/{phase}.md (if exists) — issue 모드는 프로젝트별 prompts/ 트윈이
    #    없으므로 전체 skip (부재 힌트도 미출력 — project 전제 힌트 억제).
    #    planner-critic 는 critic 전용 가이드(prompts/planner-critic.md) 가 있으면 우선,
    #    없으면 planner 와 동일한 prompts/planner.md 로 fallback — 같은 계획 기준 위에서 챌린지.
    if work_mode != "issue":
        prompt_phase = phase
        prompt_abs = workspace / "projects" / project / "prompts" / f"{phase}.md"
        if phase == "planner-critic" and not prompt_abs.is_file():
            prompt_phase = "planner"
            prompt_abs = workspace / "projects" / project / "prompts" / "planner.md"
        prompt_exists = add_if_exists(
            prompt_abs,
            f"workspace/projects/{project}/prompts/{prompt_phase}.md",
        )
        if not prompt_exists:
            hints.append(
                f"prompts/{prompt_phase}.md 없음 — project.md 만으로 작업"
            )
        elif phase == "planner-critic" and prompt_phase == "planner":
            hints.append(
                "prompts/planner-critic.md 없음 — prompts/planner.md 로 대체 (같은 계획 기준 위에서 챌린지)"
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
                "`/pilot:learn {진입점}` 으로 부트스트랩하거나 MANIFEST 의 `## 도메인 분류` 표에 행 추가 "
                "(H2 헤더가 단독 라인 `## 도메인 분류` 형태인지 확인 — suffix·코드블록 안 문자열은 인식되지 않음)"
            )
    else:
        hints.append("도메인 판정 실패 — 도메인 컨텍스트 로드 skip. 사용자 확인 필요.")

    # 5) cross-domain — 경계 계약 문서(boundaries/) 로드 + 외부 도메인 reference 힌트
    #    정방향({domain}--B: 내가 호출하는 표면) 과 역방향(B--{domain}: 남이 나를
    #    호출하는 표면 — 영향 분석용) 모두 로드한다. 문서는 호출 표면만 담아 작게 유지.
    if domain:
        bdir = workspace / "context" / "boundaries"
        matched: list[Path] = []
        if bdir.is_dir():
            matched = sorted(
                p
                for p in bdir.glob("*.md")
                if p.name.startswith(f"{domain}--") or p.stem.endswith(f"--{domain}")
            )
            for p in matched[:MAX_BOUNDARY_DOCS]:
                files.append(f"workspace/context/boundaries/{p.name}")
                hints.append(f"경계 계약 로드: boundaries/{p.name}")
            if len(matched) > MAX_BOUNDARY_DOCS:
                hints.append(
                    f"경계 계약 {len(matched)}건 중 {MAX_BOUNDARY_DOCS}건만 로드 — "
                    "나머지는 필요 시 수동 Read"
                )
        covered = {p.name for p in matched}
        ext_refs = parse_manifest_external_refs(manifest_abs)
        shown = 0
        for ext_domain, classes in ext_refs:
            if ext_domain == domain:
                continue
            if f"{domain}--{ext_domain}.md" in covered:
                continue  # 경계 계약 문서가 이미 커버
            if shown >= 3:
                hints.append(
                    f"외부 도메인 reference 총 {len(ext_refs)}건 — "
                    "MANIFEST `## 외부 도메인 reference` 표 참조"
                )
                break
            hints.append(
                f"미학습 외부 도메인 의존: {ext_domain} ({classes}) — "
                f"경계만 필요하면 `/pilot:learn --boundary {ext_domain} --from {domain}`, "
                "전체 학습은 표의 추천 명령 참조"
            )
            shown += 1

    # 6) generator 만 coding.md (플러그인 언어중립판).
    #    conventions_doc/evals (언어별) 는 generator (자기 검사) 와
    #    evaluator (독립 검증) 가 같은 파일을 본다 — 생성자 자기 인증 방지.
    if phase == "generator":
        files.append(f"{plugin_root()}/skills/context/shared/coding.md")
    if phase in ("generator", "evaluator"):
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

    # 8) 작업 명세 (project.md / issue.md) 제한사항의 언어·도구 override 적용
    #    spec_md_abs 는 위 2) 에서 이미 구성됨 — 재사용 (issue.md 는 통상
    #    제한사항 섹션이 없어 빈 dict, graceful).
    config.update(parse_lang_override(spec_md_abs))
    if config:
        summary = " · ".join(f"{k}={v}" for k, v in config.items())
        hints.append(f"언어·도구: {summary}")
    else:
        hints.append(
            "언어·도구 기본값 미정의 — `workspace/context/config.md` 의 "
            "`## 언어·도구 기본값` 섹션 또는 project.md 제한사항에 키 등록 권장"
        )

    return files, hints, config


# phase 별 focus 반영 지시 — wrapper .md 에 복제하지 않는 공통 지시(instructions)의 일부.
PHASE_FOCUS_DIRECTIVE = {
    "planner": (
        "focus 값이 있으면 사용자 최근 지시로 간주하고 계획에 반드시 반영 — "
        "계획 본문에 'focus 반영 사항' 으로 명시"
    ),
    "planner-critic": "focus 값이 있으면 챌린지 작성 시 반드시 반영 (사용자 최근 지시)",
    "generator": "focus 값이 있으면 구현에 반드시 반영하고 반영 결과를 사용자에게 간단 보고",
    "evaluator": "focus 값이 있으면 검토 관점에 반영 (관련 체크 항목 추가·비중 상향)",
}


def build_instructions(phase: str) -> list[str]:
    """wrapper 가 결과 JSON 을 처리하는 공통 지시. 모든 분기(에러 포함)에서 동일하게 출력."""
    return [
        "error 필드가 있으면 원문을 사용자에게 출력하고 종료",
        "files_to_read 를 순서대로 Read 한다 (존재 확인된 파일들)",
        PHASE_FOCUS_DIRECTIVE[phase],
        "hints 내용을 본 세션 컨텍스트로 주입",
        "tdd / mode / domain / project_phase / work_mode 값을 이후 분기에 사용 (analyzed 는 보고용 — 로드 분기에 쓰이지 않는다)",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="pilot orchestrate-load — LOAD phase 의사결정"
    )
    parser.add_argument(
        "--phase",
        required=True,
        choices=["planner", "planner-critic", "generator", "evaluator"],
    )
    parser.add_argument("--workspace", default="workspace", help="workspace/ 경로")
    parser.add_argument(
        "--project",
        default=None,
        help="프로젝트명 (생략 시 STATE.md 진행중. 명시 시 STATE 우회 project 모드 강제)",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    result: dict = {
        "phase": args.phase,
        "project": None,
        "work_mode": "project",
        "project_phase": None,
        "domain": None,
        "analyzed": None,
        "tdd": None,
        "mode": None,
        "focus": None,
        "config": {},
        "instructions": build_instructions(args.phase),
        "files_to_read": [],
        "hints": [],
        "error": None,
    }

    if not workspace.is_dir():
        result["error"] = (
            f"workspace not found: {workspace}. `/pilot:pilot-init` 실행 필요."
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    # P1: 활성 작업 단위 (project / issue) — STATE.md mode 열 판정.
    #     `--project` 명시 시 활성 조회 자체를 건너뛰어 project 모드 강제
    #     (corrupt-state 탈출구 — 아래 multi-active 에러의 안내와 동일 의미 유지).
    project = args.project
    work_mode = "project"
    if not project:
        active = parse_state_md_active(workspace / "STATE.md")
        if len(active) == 1:
            active_mode, project = active[0]
            # `issue` 외 값 (project·legacy 순번 숫자) 은 project 로 폴백.
            if active_mode == "issue":
                work_mode = "issue"
        elif len(active) == 0:
            result["error"] = (
                "활성 project/issue 없음. `/pilot:project {이름}` 또는 "
                "`/pilot:issue {이슈명}` 으로 활성화."
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1
        else:
            names = ", ".join(name for _, name in active)
            result["error"] = (
                f"STATE.md 에 진행중 {len(active)} 개 ({names}). "
                "1 개만 허용. STATE.md 수정 후 재시도 또는 --project 로 명시."
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1
    if work_mode == "issue" and project == "-":
        result["error"] = (
            "이슈명 없는 issue 모드 (STATE.md `| issue | - |`) 는 사이클 비지원. "
            "`/pilot:issue {이슈명}` 으로 이슈를 생성한 뒤 재시도."
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    if has_path_traversal(project):
        result["error"] = (
            f"프로젝트명에 허용되지 않는 문자(`/` `\\` `..`): {project!r}"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    result["project"] = project
    result["work_mode"] = work_mode

    if work_mode == "issue":
        # issue 모드 — 상태 파일 없음 (stateless). issues/{이슈명}/issue.md 가
        # 단건 명세다. 부재 시 issue 맥락 에러 (mode 미판정 시절에는 projects/
        # 경로의 .agent-state.yml 부재로 오도성 처방이 나갔다).
        issue_md = workspace / "issues" / project / "issue.md"
        if not issue_md.is_file():
            result["error"] = (
                f"workspace/issues/{project}/issue.md 없음 — "
                f"`/pilot:issue {project}` 로 이슈 폴더를 생성한 뒤 재시도."
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1
        # stateless 고정 — `.agent-state.yml` 안 읽음 (mode 는 초기값 None 유지).
        # project_phase 는 development 고정 (wrapper 의 qa 블록 비활성 보장) —
        # issue 는 phase 개념 밖의 단발 작업이다.
        result["analyzed"] = False
        result["tdd"] = False
        result["project_phase"] = "development"
        result["hints"].append(
            "[work_mode] issue — 이슈 수정 모드: 최소 변경·롤백 가능. "
            "issue.md 가 단건 명세 (planner=원인, generator=조치 기입)"
        )
        result["domain"] = determine_domain(issue_md)
    else:
        # state.yml — 누락 / 읽기 실패 / 빈 파일을 각각 구분해 안내한다.
        state_yml = workspace / "projects" / project / ".agent-state.yml"
        state = parse_state_yml(state_yml)
        if not state:
            if not state_yml.is_file():
                result["error"] = (
                    f".agent-state.yml 누락. `/pilot:project {project}` 재실행 또는 직접 작성."
                )
            elif state is None:
                result["error"] = (
                    f".agent-state.yml 읽기 실패 (인코딩·권한 등 확인 필요): {state_yml}"
                )
            else:
                result["error"] = (
                    f".agent-state.yml 가 비어 있거나 유효한 `key: value` 가 없음: "
                    f"{state_yml}. 내용을 확인하거나 `/pilot:project {project}` 로 재생성."
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
            if state_mode != "characterize":
                result["hints"].append(
                    f"[WARN] state.mode={state_mode!r} 는 인식되지 않는 모드 — "
                    "표준 모드로 처리됨. 유효 값: 'characterize' 또는 미설정."
                )

        # project phase (v1.3+, 부재=development) — fail-closed: 비정상 값이면 에러 중단
        project_phase, phase_err = resolve_project_phase(state)
        if phase_err:
            result["error"] = phase_err
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1
        result["project_phase"] = project_phase
        if project_phase == "qa":
            result["hints"].append(
                "[phase] qa — 결함 수정 모드: 최소 변경·회귀영향 후보 필수·features/ 읽기 전용"
            )

        # Domain — state 의 domain 필드 우선, null 이면 project.md 에서 추출
        project_md = workspace / "projects" / project / "project.md"
        state_domain = state.get("domain")
        if isinstance(state_domain, str) and state_domain:
            result["domain"] = state_domain
        else:
            result["domain"] = determine_domain(project_md)

    # domain 은 scope/rules 경로에 보간되므로 traversal 문자가 있으면 무시한다.
    if result["domain"] and has_path_traversal(result["domain"]):
        result["hints"].append(
            f"[WARN] domain={result['domain']!r} 에 허용되지 않는 문자 — 무시됨. "
            "도메인 미판정으로 처리."
        )
        result["domain"] = None

    # Focus — 활성 작업 폴더 (projects/ 또는 issues/) 의 .focus.md
    focus_base = "issues" if work_mode == "issue" else "projects"
    focus_md = workspace / focus_base / project / ".focus.md"
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
        tdd=result["tdd"],
        phase=args.phase,
        mode=result["mode"],
        work_mode=work_mode,
    )
    result["files_to_read"] = files
    result["hints"].extend(phase_hints)
    result["config"] = config

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
