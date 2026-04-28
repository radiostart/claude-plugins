#!/usr/bin/env bash
# pilot-update — Claude Code 의 /plugin 커맨드가 막힌 환경 (IDE 내장, 관리형 세션 등)
# 에서 pilot 플러그인 캐시를 원격 최신으로 강제 동기화한다.
#
# 전제: /plugin marketplace add radiostart/claude-plugins 이 이미 완료되어
#       ~/.claude/plugins/marketplaces/claude-plugins/ 가 git clone 되어 있어야 함.
#
# 설치 (1회, .zshrc 또는 .bashrc 에 추가):
#   alias pilot-update='bash ~/.claude/plugins/marketplaces/claude-plugins/pilot/tools/pilot-update.sh'
#
# 사용:
#   pilot-update           # 최신 main 으로 fast-forward
#   pilot-update --check   # 업데이트 있는지만 확인 (pull 안 함)

set -euo pipefail

CACHE_DIR="$HOME/.claude/plugins/marketplaces/claude-plugins"
PLUGIN_JSON="$CACHE_DIR/pilot/.claude-plugin/plugin.json"

bold() { printf '\033[1m%s\033[0m' "$1"; }
green() { printf '\033[32m%s\033[0m' "$1"; }
yellow() { printf '\033[33m%s\033[0m' "$1"; }
red() { printf '\033[31m%s\033[0m' "$1"; }

if [[ ! -d "$CACHE_DIR/.git" ]]; then
  echo "$(red '✗') 캐시 디렉토리 없음: $CACHE_DIR"
  echo "   먼저 터미널에서 'claude' 실행 후:"
  echo "     /plugin marketplace add radiostart/claude-plugins"
  echo "     /plugin install pilot@claude-plugins"
  exit 1
fi

current_version() {
  [[ -f "$PLUGIN_JSON" ]] || { echo "unknown"; return; }
  python3 -c "import json; print(json.load(open('$PLUGIN_JSON'))['version'])" 2>/dev/null || echo "unknown"
}

BEFORE_VERSION=$(current_version)
BEFORE_SHA=$(git -C "$CACHE_DIR" rev-parse --short HEAD)

echo "$(bold 'pilot-update')  $CACHE_DIR"
echo "  현재: v$BEFORE_VERSION ($BEFORE_SHA)"

# 원격 조회
git -C "$CACHE_DIR" fetch --quiet origin main

REMOTE_SHA=$(git -C "$CACHE_DIR" rev-parse --short origin/main)

if [[ "$BEFORE_SHA" == "$REMOTE_SHA" ]]; then
  echo "$(green '✓') 이미 최신 (origin/main = $REMOTE_SHA)"
  exit 0
fi

BEHIND_COUNT=$(git -C "$CACHE_DIR" rev-list --count HEAD..origin/main)
echo "  원격: $REMOTE_SHA ($(yellow "$BEHIND_COUNT 커밋 뒤처짐"))"

if [[ "${1:-}" == "--check" ]]; then
  echo
  echo "$(yellow '!') 업데이트 있음. 적용하려면 --check 없이 재실행."
  exit 0
fi

# pull 수행 (fast-forward only — 로컬 변경 덮어쓰지 않음)
echo
echo "▶ git pull --ff-only"
if ! git -C "$CACHE_DIR" pull --ff-only --quiet origin main; then
  echo "$(red '✗') fast-forward 불가 (캐시에 로컬 변경 존재). 수동 확인 필요:"
  echo "   cd $CACHE_DIR && git status"
  exit 1
fi

AFTER_VERSION=$(current_version)
AFTER_SHA=$(git -C "$CACHE_DIR" rev-parse --short HEAD)

echo "$(green '✓') 업데이트 완료: v$BEFORE_VERSION → v$AFTER_VERSION  ($BEFORE_SHA → $AFTER_SHA)"
echo
echo "$(yellow '!') 열려있는 Claude Code 세션은 구버전을 로드한 상태입니다."
echo "   새 내용 반영하려면 세션 재시작 또는 새 창을 여세요."
