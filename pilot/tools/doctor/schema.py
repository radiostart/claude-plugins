"""플러그인 구조 스키마 검사 (--schema 모드).

PLUGIN_SCHEMA_NOTES.md 의 규칙과 동기화. plugin.json / hooks.json /
SKILL frontmatter / agent frontmatter / version↔git tag 일치 검증.

청중: 플러그인 메인테이너 / pre-push hook / CI.
"""

import json
import re
import subprocess
from pathlib import Path

from doctor._common import BOLD, RESET, Result, summarize


# ---------------------------------------------------------------------------
# Schema 상수 — PLUGIN_SCHEMA_NOTES.md 와 동기화
# ---------------------------------------------------------------------------

PLUGIN_JSON_RECOMMENDED_KEYS = ("name", "version", "description", "author")
PLUGIN_JSON_FORBIDDEN_KEYS = ("hooks", "agents", "skills", "commands")
HOOK_MATCHERS_ALLOWED = (
    "PreToolUse",
    "PostToolUse",
    "UserPromptSubmit",
    "Stop",
    "SubagentStop",
    "PreCompact",
    "SessionStart",
    "SessionEnd",
    "Notification",
    "PermissionRequest",
)
SKILL_DESCRIPTION_MAX_BYTES = 1024
AGENT_REQUIRED_FRONTMATTER = ("name", "description", "tools")
SKILL_REQUIRED_FRONTMATTER = ("name", "description")
TAG_PREFIX = "pilot-v"


# ---------------------------------------------------------------------------
# Frontmatter / git 헬퍼
# ---------------------------------------------------------------------------

def _extract_frontmatter(md_path: Path) -> dict | None:
    """`.md` 파일 상단 `---` 블록을 파싱해 flat dict 반환. pyyaml 불필요.

    지원: `key: value` 1줄, `key: >-` 시작 multiline (후속 인덴트 라인 결합).
    nested 구조는 무시 (플러그인 frontmatter 는 flat 만 사용).
    """
    if not md_path.is_file():
        return None
    try:
        text = md_path.read_text(encoding="utf-8")
    except Exception:
        return None
    m = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.S)
    if not m:
        return None
    block = m.group(1)
    data: dict = {}
    current_key: str | None = None
    multiline_parts: list[str] = []
    multiline_mode = False

    def _flush_multiline():
        nonlocal multiline_mode, multiline_parts, current_key
        if current_key is not None and multiline_mode:
            joined = " ".join(s.strip() for s in multiline_parts if s.strip())
            data[current_key] = joined
        multiline_mode = False
        multiline_parts = []

    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            if multiline_mode and raw.startswith((" ", "\t")):
                continue
            continue
        if multiline_mode and raw.startswith((" ", "\t")):
            multiline_parts.append(raw)
            continue
        _flush_multiline()
        if ":" not in raw:
            continue
        k, v = raw.split(":", 1)
        k = k.strip()
        v = v.strip()
        current_key = k
        if v in (">", ">-", "|", "|-"):
            multiline_mode = True
            multiline_parts = []
        else:
            if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
                v = v[1:-1]
            data[k] = v
    _flush_multiline()
    return data


def _latest_git_tag(repo: Path) -> str | None:
    """최신 `pilot-v*` 태그를 SemVer 정렬로 반환. 없으면 None."""
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "tag", "--list", f"{TAG_PREFIX}*", "--sort=-v:refname"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode != 0:
            return None
        for line in out.stdout.splitlines():
            line = line.strip()
            if line.startswith(TAG_PREFIX):
                return line
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 개별 검사
# ---------------------------------------------------------------------------

def _check_plugin_json(plugin_json: Path) -> list[Result]:
    results: list[Result] = []
    if not plugin_json.is_file():
        results.append(
            Result(
                Result.ERROR,
                ".claude-plugin/plugin.json",
                "없음",
                "플러그인 루트에 plugin.json 생성 필요",
            )
        )
        return results
    try:
        data = json.loads(plugin_json.read_text(encoding="utf-8"))
    except Exception as e:
        results.append(
            Result(
                Result.ERROR,
                ".claude-plugin/plugin.json",
                f"JSON 파싱 실패: {e}",
                "문법 오류 수정",
            )
        )
        return results

    missing = [k for k in PLUGIN_JSON_RECOMMENDED_KEYS if k not in data]
    if missing:
        results.append(
            Result(
                Result.ERROR,
                "plugin.json 필수 키",
                f"누락: {', '.join(missing)}",
                f"권장 필드: {', '.join(PLUGIN_JSON_RECOMMENDED_KEYS)}",
            )
        )
    else:
        results.append(
            Result(
                Result.PASS,
                "plugin.json 필수 키",
                f"{', '.join(PLUGIN_JSON_RECOMMENDED_KEYS)} 모두 존재",
            )
        )

    forbidden = [k for k in PLUGIN_JSON_FORBIDDEN_KEYS if k in data]
    if forbidden:
        results.append(
            Result(
                Result.ERROR,
                "plugin.json 금지 키",
                f"발견: {', '.join(forbidden)}",
                "PLUGIN_SCHEMA_NOTES.md 참조 — hooks/hooks.json 또는 파일 기반 자동 인식으로 이관",
            )
        )
    else:
        results.append(
            Result(Result.PASS, "plugin.json 금지 키", "없음 (clean)")
        )
    return results


def _check_hooks_json(hooks_json: Path) -> list[Result]:
    results: list[Result] = []
    if not hooks_json.is_file():
        results.append(
            Result(
                Result.WARN,
                "hooks/hooks.json",
                "없음 (훅 미사용 프로젝트면 정상)",
                "",
            )
        )
        return results
    try:
        data = json.loads(hooks_json.read_text(encoding="utf-8"))
    except Exception as e:
        results.append(
            Result(
                Result.ERROR,
                "hooks/hooks.json",
                f"JSON 파싱 실패: {e}",
                "문법 오류 수정",
            )
        )
        return results

    if "hooks" not in data or not isinstance(data["hooks"], dict):
        results.append(
            Result(
                Result.ERROR,
                "hooks/hooks.json",
                "최상위 `hooks` 객체 없음",
                "`{ \"hooks\": { \"PreToolUse\": [...] } }` 형태로 작성",
            )
        )
        return results

    bad = [m for m in data["hooks"].keys() if m not in HOOK_MATCHERS_ALLOWED]
    if bad:
        results.append(
            Result(
                Result.ERROR,
                "hooks/hooks.json matcher",
                f"허용되지 않은 값: {', '.join(bad)}",
                f"허용 목록: {', '.join(HOOK_MATCHERS_ALLOWED)}",
            )
        )
    else:
        used = sorted(data["hooks"].keys())
        results.append(
            Result(
                Result.PASS,
                "hooks/hooks.json matcher",
                f"허용 목록 내: {', '.join(used) if used else '(empty)'}",
            )
        )
    return results


def _check_skills_frontmatter(skills_dir: Path) -> list[Result]:
    results: list[Result] = []
    if not skills_dir.is_dir():
        return results
    skill_files = sorted(skills_dir.glob("*/SKILL.md"))
    if not skill_files:
        results.append(
            Result(Result.WARN, "skills/*/SKILL.md", "파일 없음", "")
        )
        return results
    errors: list[str] = []
    for sk in skill_files:
        fm = _extract_frontmatter(sk)
        rel = sk.relative_to(skills_dir.parent)
        if fm is None:
            errors.append(f"{rel}: frontmatter 블록 없음")
            continue
        missing = [k for k in SKILL_REQUIRED_FRONTMATTER if k not in fm]
        if missing:
            errors.append(f"{rel}: 누락 {', '.join(missing)}")
            continue
        desc = fm.get("description", "")
        byte_len = len(desc.encode("utf-8"))
        if byte_len > SKILL_DESCRIPTION_MAX_BYTES:
            errors.append(
                f"{rel}: description {byte_len} bytes > {SKILL_DESCRIPTION_MAX_BYTES} 제한"
            )
    if errors:
        for e in errors:
            results.append(
                Result(
                    Result.ERROR,
                    "skills/*/SKILL.md frontmatter",
                    e,
                    "PLUGIN_SCHEMA_NOTES.md 참조",
                )
            )
    else:
        results.append(
            Result(
                Result.PASS,
                "skills/*/SKILL.md frontmatter",
                f"{len(skill_files)} 파일 모두 유효",
            )
        )
    return results


def _check_agents_frontmatter(agents_dir: Path) -> list[Result]:
    results: list[Result] = []
    if not agents_dir.is_dir():
        return results
    agent_files = sorted(agents_dir.glob("*.md"))
    if not agent_files:
        results.append(
            Result(Result.WARN, "agents/*.md", "파일 없음", "")
        )
        return results
    errors: list[str] = []
    for ag in agent_files:
        fm = _extract_frontmatter(ag)
        rel = ag.relative_to(agents_dir.parent)
        if fm is None:
            errors.append(f"{rel}: frontmatter 블록 없음")
            continue
        missing = [k for k in AGENT_REQUIRED_FRONTMATTER if k not in fm]
        if missing:
            errors.append(f"{rel}: 누락 {', '.join(missing)}")
    if errors:
        for e in errors:
            results.append(
                Result(
                    Result.ERROR,
                    "agents/*.md frontmatter",
                    e,
                    "PLUGIN_SCHEMA_NOTES.md 참조",
                )
            )
    else:
        results.append(
            Result(
                Result.PASS,
                "agents/*.md frontmatter",
                f"{len(agent_files)} 파일 모두 유효",
            )
        )
    return results


def _check_version_tag(plugin_root: Path) -> list[Result]:
    plugin_json = plugin_root / ".claude-plugin" / "plugin.json"
    if not plugin_json.is_file():
        return []
    try:
        data = json.loads(plugin_json.read_text(encoding="utf-8"))
    except Exception:
        return []
    version = data.get("version")
    if not version:
        return []
    tag = _latest_git_tag(plugin_root)
    expected = f"{TAG_PREFIX}{version}"
    if tag is None:
        return [
            Result(
                Result.WARN,
                "version vs git tag",
                f"plugin.json version={version} 이지만 `{TAG_PREFIX}*` 태그 없음",
                f"릴리즈 시 `git tag {expected}` 생성 권장",
            )
        ]
    if tag != expected:
        return [
            Result(
                Result.WARN,
                "version vs git tag",
                f"plugin.json={expected} ≠ 최신 태그={tag}",
                "CHANGELOG 업데이트 + 태그 동기화 권장",
            )
        ]
    return [
        Result(Result.PASS, "version vs git tag", f"{expected} 일치")
    ]


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------

def run_schema_check(plugin_root: Path) -> int:
    """`--schema` 모드 진입점. 플러그인 구조 전용 검사."""
    print(f"{BOLD}pilot doctor [--schema]{RESET}  plugin_root: {plugin_root}\n")
    all_results: list[Result] = []

    print(f"{BOLD}plugin.json:{RESET}")
    r1 = _check_plugin_json(plugin_root / ".claude-plugin" / "plugin.json")
    for r in r1:
        print(r.render())
    all_results.extend(r1)

    print(f"\n{BOLD}hooks/hooks.json:{RESET}")
    r2 = _check_hooks_json(plugin_root / "hooks" / "hooks.json")
    for r in r2:
        print(r.render())
    all_results.extend(r2)

    print(f"\n{BOLD}skills/*/SKILL.md:{RESET}")
    r3 = _check_skills_frontmatter(plugin_root / "skills")
    for r in r3:
        print(r.render())
    all_results.extend(r3)

    print(f"\n{BOLD}agents/*.md:{RESET}")
    r4 = _check_agents_frontmatter(plugin_root / "agents")
    for r in r4:
        print(r.render())
    all_results.extend(r4)

    print(f"\n{BOLD}version / git tag:{RESET}")
    r5 = _check_version_tag(plugin_root)
    if r5:
        for r in r5:
            print(r.render())
        all_results.extend(r5)
    else:
        print("  (skip — version 또는 plugin.json 없음)")

    return summarize(all_results)
