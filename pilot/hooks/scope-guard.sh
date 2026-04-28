#!/usr/bin/env bash
# scope-guard.sh
# workspace/context/config.md 의 `## Ignore` 섹션에 해당하는 파일 수정을 차단한다.

set -euo pipefail

# tool_input.file_path를 stdin JSON에서 추출
FILE_PATH=$(cat /dev/stdin | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

# 경로가 없으면 통과
[[ -z "$FILE_PATH" ]] && exit 0

# 프로젝트 루트 기준 상대 경로로 변환
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
REL_PATH="${FILE_PATH#$PROJECT_DIR/}"

CONFIG_FILE="$PROJECT_DIR/workspace/context/config.md"

# config.md 가 없으면 안전하게 통과
[[ ! -f "$CONFIG_FILE" ]] && exit 0

# config.md 의 `## Ignore` 섹션에서 첫 번째 컬럼(`pattern`)을 추출해 substring 매칭용으로 정규화
# - `/**` 접미사는 `/`로 축소해 상위 경로 오매칭을 막는다 (예: "public" → "publication" 오매칭 방지)
# - `**/` 접두사와 끝의 `*`는 제거한다
IGNORE_PATTERNS=()
while IFS= read -r pattern; do
  [[ -z "$pattern" ]] && continue
  IGNORE_PATTERNS+=("$pattern")
done < <(
  awk '/^## Ignore/{flag=1; next} /^## /{flag=0} flag && /^\| `/' "$CONFIG_FILE" \
    | sed -E 's/^\|[[:space:]]*`([^`]+)`.*/\1/' \
    | sed -E 's|/\*\*$|/|; s|^\*\*/||; s|\*||g'
)

# Ignore 섹션이 비어있으면 통과
[[ ${#IGNORE_PATTERNS[@]} -eq 0 ]] && exit 0

for pattern in "${IGNORE_PATTERNS[@]}"; do
  if [[ "$REL_PATH" == *"$pattern"* ]]; then
    echo "❌ Scope 외 파일 수정 차단: $REL_PATH" >&2
    echo "   config.md Ignore 패턴에 해당합니다: $pattern" >&2
    echo "   이 파일을 수정해야 한다면 사용자에게 확인을 받으세요." >&2
    exit 2
  fi
done

exit 0
