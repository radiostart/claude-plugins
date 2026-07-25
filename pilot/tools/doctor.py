#!/usr/bin/env python3
"""
pilot doctor — workspace / project 정합성 검사.

본 파일은 thin dispatcher. 실제 검사 로직은 `tools/doctor/` 패키지에 있다.

  - default 모드     → doctor.integrity.run_integrity_check
  - --fix            → 위에 포함 (run_integrity_check 인자)
  - --schema         → doctor.schema.run_schema_check
  - --diagnose       → doctor.diagnose.run_diagnose

Usage:
    python3 doctor.py [WORKSPACE_PATH] [--project PROJECT] [--fix]
    python3 doctor.py --schema
    python3 doctor.py [WORKSPACE_PATH] --diagnose [--project PROJECT]

패키지 함수를 직접 테스트하려면 `doctor.integrity`·`doctor._common` 을
sys.path 경유로 직접 import 한다 (본 파일은 더 이상 wildcard-style
backward-compat re-export 를 제공하지 않는다 — `tests/tools/test_doctor_conventions.py`
참조).
"""

import argparse
import sys
from pathlib import Path

# tools/ 를 sys.path 에 추가 — `doctor` 패키지를 import 하기 위해.
# 본 파일이 script 로 실행될 때 (python3 doctor.py) 와 importlib 로 로드될 때
# 모두 이 라인이 실행되어 패키지 경로가 보장된다.
_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from doctor._common import RED, RESET  # noqa: E402
from doctor.integrity import run_integrity_check  # noqa: E402
from doctor.schema import run_schema_check  # noqa: E402
from doctor.diagnose import (  # noqa: E402, F401
    DIAGNOSE_PATTERNS,
    _pattern_loop,
    _pattern_red_miss,
    _pattern_repeat_not_ready,
    _pattern_scope_violation,
    _read_project_files,
    _recommend_action,
    run_diagnose,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="pilot doctor")
    parser.add_argument(
        "workspace", nargs="?", default="workspace", help="workspace/ 경로"
    )
    parser.add_argument(
        "--project",
        default=None,
        help="대상 프로젝트 (생략 시 STATE.md 진행중 사용)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="auto-fixable 로 표시된 WARN/ERROR 에 대해 자동 수정 수행.",
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="플러그인 구조 스키마 검사만 수행 (workspace 인자 무시).",
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="런타임 실패 패턴 진단 — loop/red-miss/repeat-not-ready/scope-violation 검사.",
    )
    args = parser.parse_args()

    if args.schema:
        # 이 스크립트의 부모 디렉터리 = 플러그인 루트 (tools/ 상위)
        plugin_root = Path(__file__).resolve().parent.parent
        return run_schema_check(plugin_root)

    if args.diagnose:
        workspace = Path(args.workspace).resolve()
        if not workspace.is_dir():
            print(f"{RED}error{RESET}: workspace not found: {workspace}", file=sys.stderr)
            return 1
        return run_diagnose(workspace, args.project)

    workspace = Path(args.workspace).resolve()
    if not workspace.is_dir():
        print(f"{RED}error{RESET}: workspace not found: {workspace}", file=sys.stderr)
        return 1

    return run_integrity_check(workspace, args.project, args.fix)


if __name__ == "__main__":
    sys.exit(main())
