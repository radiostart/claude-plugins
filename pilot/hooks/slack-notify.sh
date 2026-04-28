#!/usr/bin/env bash
# slack-notify.sh
# Claude Code harness 의 훅 어댑터. 지원 이벤트:
#   - PermissionRequest — 권한 다이얼로그 표시 순간 (도구 실행 전). 사용자 대기 경로.
#   - Notification      — 알림 (permission_prompt / idle_prompt / auth_success / elicitation_dialog).
#
# 두 이벤트 모두 `slack-notify.py --from-hook` 으로 stdin 을 그대로 릴레이한다
# (파싱은 .py 가 담당 — 단일 SSOT). 어댑터 책임:
#   - workspace 경로 결정 (PROJECT_DIR/workspace)
#   - Slack POST 를 **백그라운드 실행** → 훅 지연이 사용자 승인 흐름을 막지 않음
#   - `PILOT_SLACK_DEBUG=1` 일 때만 호출 이력을 /tmp/pilot-slack-hook.log 에 기록
#   - 어떤 실패 경로에서도 exit 0 — harness 파이프라인을 차단하지 않는다.

set -uo pipefail

PILOT_SLACK_LOG="/tmp/pilot-slack-hook.log"
_pilot_log() {
  [[ -n "${PILOT_SLACK_DEBUG:-}" ]] || return 0
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" >> "$PILOT_SLACK_LOG" 2>/dev/null || true
}

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-}"
if [[ -z "$PLUGIN_ROOT" ]]; then
  PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

NOTIFIER="$PLUGIN_ROOT/tools/slack-notify.py"
if [[ ! -f "$NOTIFIER" ]]; then
  _pilot_log "SKIP notifier missing: $NOTIFIER"
  exit 0
fi

WORKSPACE="$PROJECT_DIR/workspace"
# linked worktree 인 경우 main worktree 의 workspace 로 fallback.
# (Claude Code 가 .claude/worktrees/<name>/ 에서 작업할 때 workspace 가 메인 루트에만 있는 경우)
if [[ ! -d "$WORKSPACE" ]]; then
  MAIN_WT="$(git -C "$PROJECT_DIR" worktree list --porcelain 2>/dev/null \
              | sed -n 's/^worktree //p' | head -n 1)"
  if [[ -n "$MAIN_WT" && -d "$MAIN_WT/workspace" ]]; then
    WORKSPACE="$MAIN_WT/workspace"
  fi
fi
if [[ ! -d "$WORKSPACE" ]]; then
  _pilot_log "SKIP no workspace: $WORKSPACE"
  exit 0
fi

# stdin 을 한 번 읽어 보존 — 백그라운드 프로세스에 그대로 파이프.
STDIN_JSON=$(cat)

_pilot_log "RELAY project_dir=$PROJECT_DIR plugin_root=$PLUGIN_ROOT bytes=${#STDIN_JSON}"

if [[ -n "${PILOT_SLACK_DEBUG:-}" ]]; then
  REDIRECT_TARGET="$PILOT_SLACK_LOG"
else
  REDIRECT_TARGET="/dev/null"
fi

# Slack POST 를 백그라운드로 분리 — 사용자 승인 다이얼로그가 POST 대기로 지연되지 않게.
(
  printf '%s' "$STDIN_JSON" | python3 "$NOTIFIER" \
    --from-hook \
    --workspace "$WORKSPACE" \
    >>"$REDIRECT_TARGET" 2>&1 \
    || _pilot_log "RELAY_FAIL"
) &
disown 2>/dev/null || true

exit 0
