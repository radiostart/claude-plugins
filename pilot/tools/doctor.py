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

backward compat:
    test/외부 코드가 `importlib.util.spec_from_file_location` 으로 본 파일을
    로드해도 기존 함수명 (`check_gitignore_required_patterns`, `_git_repo_root` 등)
    이 그대로 노출되도록 4 모듈을 wildcard re-export 한다.
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

# Backward-compat re-exports — test/외부 코드가 import 할 수 있는 모든 공개 심볼.
# wildcard 가 아닌 명시 import 를 사용하면 누락 시 즉시 ImportError 로 발견 가능.
from doctor._common import (  # noqa: E402, F401
    BOLD,
    GREEN,
    PLUGIN_ROOT_ENV,
    Result,
    SCHEMA_VERSION,
    SUPPORTED_SCHEMAS,
    YELLOW,
    _git_repo_root,
    _parse_semver,
    count_real_features,
    detect_duplicate_h2_sections,
    parse_dotenv_file,
    parse_state_md,
    parse_state_md_all_rows,
    parse_state_yml,
    project_has_tdd_literal,
    read_current_plugin_version,
    run_auto_fixes,
    summarize,
)
from doctor.integrity import (  # noqa: E402, F401
    REQUIRED_GITIGNORE_PATTERNS,
    _fix_migrate_state_to_current,
    _fix_remove_legacy_planning_section,
    _fix_state_md_prune_history,
    _inject_v010_defaults_into_config,
    _is_learn_section_empty,
    _has_partial_learn_definition,
    _parse_md_tables_in_section,
    _parse_md_tables_in_h3_section,
    check_auto_memory_presence,
    check_credential_drift,
    check_domain_transaction_contracts,
    check_features_open_questions,
    check_gitignore_required_patterns,
    check_project,
    check_slack_env_not_tracked,
    check_workspace,
    check_workspace_config_sections,
    check_workspace_external_domain_section,
    determine_active_project,
    migrate_v0_1_to_v0_2,
    run_integrity_check,
)
from doctor.schema import (  # noqa: E402, F401
    AGENT_REQUIRED_FRONTMATTER,
    HOOK_MATCHERS_ALLOWED,
    PLUGIN_JSON_FORBIDDEN_KEYS,
    PLUGIN_JSON_RECOMMENDED_KEYS,
    SKILL_DESCRIPTION_MAX_BYTES,
    SKILL_REQUIRED_FRONTMATTER,
    TAG_PREFIX,
    _check_agents_frontmatter,
    _check_hooks_json,
    _check_plugin_json,
    _check_skills_frontmatter,
    _check_version_tag,
    _extract_frontmatter,
    _latest_git_tag,
    run_schema_check,
)
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
