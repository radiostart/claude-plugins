#!/usr/bin/env bash
# pilot 로컬 릴리스 스크립트. `gh` CLI 로 태그·릴리스 생성.
#
# 사용:
#   pilot/tools/release.sh             # plugin.json 의 현재 버전으로 릴리스
#   pilot/tools/release.sh 0.2.3       # 버전 명시 (plugin.json 과 일치해야 함)
#
# 전제:
#   - 현재 브랜치가 main 이고 origin/main 과 동기화돼 있다
#   - working tree 가 clean
#   - `gh auth status` 통과
#   - plugin.json 의 version 이 릴리스하려는 값과 일치 (커밋 완료 상태)
#   - pilot/mkdocs.yml 의 extra.version 이 같은 버전으로 갱신·커밋됨
#   - (권장) pilot/docs/index.md 의 highlights 블록을 새 버전으로 갱신

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLUGIN_JSON="$REPO_ROOT/pilot/.claude-plugin/plugin.json"

if [[ ! -f "$PLUGIN_JSON" ]]; then
  echo "::error:: plugin.json 을 찾을 수 없습니다: $PLUGIN_JSON" >&2
  exit 1
fi

PLUGIN_VERSION="$(python3 -c "import json; print(json.load(open('$PLUGIN_JSON'))['version'])")"
ARG_VERSION="${1:-$PLUGIN_VERSION}"

if [[ "$ARG_VERSION" != "$PLUGIN_VERSION" ]]; then
  echo "::error:: 인자 버전($ARG_VERSION) 과 plugin.json 버전($PLUGIN_VERSION) 불일치." >&2
  echo "          plugin.json 을 먼저 수정·커밋한 뒤 다시 실행하세요." >&2
  exit 1
fi

TAG="pilot-v$PLUGIN_VERSION"

# --- 사전 검증 ---
cd "$REPO_ROOT"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$CURRENT_BRANCH" != "main" ]]; then
  echo "::error:: main 브랜치에서만 릴리스 가능. 현재: $CURRENT_BRANCH" >&2
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "::error:: working tree 가 clean 하지 않습니다. 커밋 또는 stash 후 재실행." >&2
  exit 1
fi

git fetch origin main --quiet
LOCAL_HEAD="$(git rev-parse HEAD)"
REMOTE_HEAD="$(git rev-parse origin/main)"
if [[ "$LOCAL_HEAD" != "$REMOTE_HEAD" ]]; then
  echo "::error:: 로컬 main 과 origin/main 이 다릅니다. pull/push 후 재실행." >&2
  exit 1
fi

if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "::error:: 태그 $TAG 가 이미 존재합니다." >&2
  exit 1
fi

# 파생 버전 표기 검증 — 매뉴얼 사이트가 plugin.json 과 어긋난 채 릴리스되지 않도록.
MKDOCS_VERSION="$(grep -E '^[[:space:]]+version:[[:space:]]*"' pilot/mkdocs.yml 2>/dev/null | head -1 | sed -E 's/.*"([^"]+)".*/\1/' || true)"
if [[ "$MKDOCS_VERSION" != "$PLUGIN_VERSION" ]]; then
  echo "::error:: pilot/mkdocs.yml 의 extra.version (\"$MKDOCS_VERSION\") 이 plugin.json (\"$PLUGIN_VERSION\") 과 다릅니다." >&2
  echo "          pilot/mkdocs.yml 의 version 을 \"$PLUGIN_VERSION\" 으로 수정·커밋한 뒤 다시 실행하세요." >&2
  exit 1
fi

if ! grep -q "v${PLUGIN_VERSION} highlights" pilot/docs/index.md; then
  echo "::warning:: pilot/docs/index.md 에 'v${PLUGIN_VERSION} highlights' 블록이 없습니다." >&2
  echo "            새 기능이 있으면 랜딩 페이지의 highlights 를 새 버전으로 갱신하세요 (patch 릴리스면 무시 가능)." >&2
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "::error:: gh CLI 가 필요합니다. https://cli.github.com" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "::error:: gh 인증 필요: gh auth login" >&2
  exit 1
fi

# --- 실행 ---
echo "▶ 태그 생성: $TAG ($LOCAL_HEAD)"
git tag "$TAG"

echo "▶ 태그 푸시"
git push origin "$TAG"

echo "▶ GitHub Release 생성 (자동 release notes)"
gh release create "$TAG" \
  --title "pilot v$PLUGIN_VERSION" \
  --generate-notes

echo "✅ 릴리스 완료: $(gh release view "$TAG" --json url --jq .url)"
