"""doctor 공통 유틸 — 모든 서브모듈이 의존.

ANSI 색상, Result 클래스, state.yml/STATE.md 파서, summarize/run_auto_fixes,
_git_repo_root 등.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "v1.2"
SUPPORTED_SCHEMAS = ["v1", "v1.1", "v1.2"]
PLUGIN_ROOT_ENV = "CLAUDE_PLUGIN_ROOT"

# ANSI color codes
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"
BOLD = "\033[1m"


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

class Result:
    PASS = "PASS"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"

    def __init__(self, level: str, label: str, message: str, hint: str = "", fix=None):
        self.level = level
        self.label = label
        self.message = message
        self.hint = hint
        # fix: optional callable that performs auto-fix and returns (success: bool, message: str)
        # 오직 whitelist 안전 대상만 전달해야 한다. 확실하지 않으면 None.
        self.fix = fix

    def render(self) -> str:
        color = {"PASS": GREEN, "INFO": RESET, "WARN": YELLOW, "ERROR": RED}.get(self.level, RESET)
        line = f"  [{color}{self.level}{RESET}] {self.label}: {self.message}"
        if self.hint:
            line += f"\n         → {self.hint}"
        if self.fix is not None:
            line += f"\n         (auto-fixable — `doctor --fix` 로 자동 수정 가능)"
        return line


# ---------------------------------------------------------------------------
# 플러그인 / semver 헬퍼
# ---------------------------------------------------------------------------

def read_current_plugin_version() -> str | None:
    """현재 실행중인 플러그인 version (plugin.json). 못 찾으면 None."""
    root = os.environ.get(PLUGIN_ROOT_ENV)
    candidates = []
    if root:
        candidates.append(Path(root) / ".claude-plugin" / "plugin.json")
    here = Path(__file__).resolve().parent.parent.parent  # tools/doctor/_common.py → 플러그인 루트
    candidates.append(here / ".claude-plugin" / "plugin.json")
    candidates.append(here.parent / ".claude-plugin" / "plugin.json")
    for c in candidates:
        if c.is_file():
            try:
                v = json.loads(c.read_text(encoding="utf-8")).get("version")
                if isinstance(v, str):
                    return v
            except Exception:
                continue
    return None


def _parse_semver(v: str | None) -> tuple[int, int, int] | None:
    if not isinstance(v, str):
        return None
    try:
        parts = v.strip().split(".")
        nums = [int(p) for p in parts[:3]]
        while len(nums) < 3:
            nums.append(0)
        return (nums[0], nums[1], nums[2])
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Workspace / STATE 파서
# ---------------------------------------------------------------------------

def parse_state_md(state_md: Path) -> tuple[int, list[str]]:
    """Return (진행중 count, list of active project names)."""
    if not state_md.is_file():
        return 0, []
    active = []
    try:
        for line in state_md.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("|") and "진행중" in line:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) >= 3 and cells[2] == "진행중":
                    active.append(cells[1])
    except Exception:
        pass
    return len(active), active


def parse_state_md_all_rows(state_md: Path) -> list[tuple[str, str, str]]:
    """모든 데이터 행 `(mode, name, status)` 반환. 헤더/구분선 제외."""
    rows: list[tuple[str, str, str]] = []
    if not state_md.is_file():
        return rows
    try:
        for line in state_md.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s.startswith("|"):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) < 3:
                continue
            first = cells[0]
            if first in ("모드", "mode") or set(first) <= set("-: "):
                continue
            rows.append((cells[0], cells[1], cells[2]))
    except Exception:
        pass
    return rows


def parse_state_yml(yml: Path) -> dict | None:
    """Minimal YAML parser for flat {key: value} state files."""
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


def parse_dotenv_file(path: Path) -> dict[str, str]:
    """workspace/.env 파일을 파싱해 key-value dict 반환.

    confluence.py `_load_dotenv` 와 동일한 파싱 규칙 (strip + 따옴표 제거).
    """
    if not path.is_file():
        return {}
    result = {}
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                result[key] = value
    except Exception:
        pass
    return result


# ---------------------------------------------------------------------------
# Project file 헬퍼
# ---------------------------------------------------------------------------

def count_real_features(features_dir: Path) -> int:
    if not features_dir.is_dir():
        return 0
    return sum(
        1
        for p in features_dir.iterdir()
        if p.is_file() and p.suffix == ".md" and not p.name.endswith(".plan.md")
    )


def project_has_tdd_literal(project_md: Path) -> bool:
    """`## 제한사항` 섹션 내 `- **TDD 모드**:` bullet 존재 여부.

    tdd-activation.md:21 의 Detect literal 계약 ("제한사항 섹션 내 문자열") 을 준수.
    template 의 blockquote 안내문 (`> **TDD 모드** 활성화 시 …`) 은 의도적으로 제외.
    """
    if not project_md.is_file():
        return False
    try:
        text = project_md.read_text(encoding="utf-8")
    except Exception:
        return False
    section_match = re.search(
        r"^##\s+제한사항\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S
    )
    if not section_match:
        return False
    return bool(re.search(r"^- \*\*TDD 모드\*\*:", section_match.group(1), re.M))


def detect_duplicate_h2_sections(md: Path) -> list[str]:
    """H2 헤딩 중 2회 이상 등장 — regen-gone-wrong 신호.

    코드블록 안의 `## ...` 은 pseudo-heading 이므로 제외.
    """
    if not md.is_file():
        return []
    try:
        text = md.read_text(encoding="utf-8")
    except Exception:
        return []

    headers: list[str] = []
    in_code_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        m = re.match(r"^##\s+([^#].*)$", line)
        if m:
            headers.append(m.group(1).strip())

    seen: dict[str, int] = {}
    for h in headers:
        seen[h] = seen.get(h, 0) + 1
    return [h for h, count in seen.items() if count >= 2]


# ---------------------------------------------------------------------------
# git 헬퍼
# ---------------------------------------------------------------------------

def _git_repo_root(start: Path) -> Path | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except Exception:
        return None
    return None


# ---------------------------------------------------------------------------
# 출력 / fix 실행 유틸
# ---------------------------------------------------------------------------

def run_auto_fixes(results: list[Result]) -> None:
    """--fix 모드: 각 Result 의 fix 를 실행. WARN/ERROR 만 대상."""
    fixable = [r for r in results if r.fix is not None and r.level in (Result.WARN, Result.ERROR)]
    if not fixable:
        print(f"\n{BOLD}[--fix]{RESET} 자동 수정 대상 없음.")
        return

    print(f"\n{BOLD}[--fix]{RESET} 자동 수정 대상 {len(fixable)} 건 처리:")
    success = fail = 0
    for r in fixable:
        ok, msg = r.fix()
        if ok:
            print(f"  [{GREEN}FIXED{RESET}] {r.label}: {msg}")
            success += 1
        else:
            print(f"  [{RED}FAIL{RESET}]  {r.label}: {msg}")
            fail += 1
    print(f"\n{BOLD}[--fix 결과]{RESET} {GREEN}{success} fixed{RESET} · {RED}{fail} failed{RESET}")
    print("재실행으로 검증 권장: `python3 doctor.py workspace`")


def summarize(results: list[Result]) -> int:
    passes = sum(1 for r in results if r.level == Result.PASS)
    warns = sum(1 for r in results if r.level == Result.WARN)
    errors = sum(1 for r in results if r.level == Result.ERROR)

    print(
        f"\n{BOLD}요약:{RESET} "
        f"{GREEN}{passes} PASS{RESET} · "
        f"{YELLOW}{warns} WARN{RESET} · "
        f"{RED}{errors} ERROR{RESET}"
    )

    return 1 if errors > 0 else 0
