#!/usr/bin/env bash
# domain-pointer.sh
# PostToolUse(Edit|Write): 경로 트리거 규칙(.claude/rules/pilot-{domain}.md)의 보완 훅 (#30 C1 보완, plan r2 C1).
# 조건부 규칙은 매칭 파일을 Read 할 때만 하네스가 로드한다 — Write·Edit 만으로는 발화하지 않는 틈을
# 같은 규칙 파일의 `paths:` 를 대조해 같은 포인터 본문으로 메운다 (세션·도메인당 1회, ≤2 도메인, 지식 본문 없음).
# 판정 로직은 tools/doctor/rules_pointer.py (learn·doctor 와 공유). 훅은 무음 실패 — 작업을 막지 않는다.
set -uo pipefail
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
exec python3 "$PLUGIN_ROOT/tools/rules-pointer.py" --hook --workspace "$PROJECT_DIR/workspace"
