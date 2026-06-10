#!/usr/bin/env bash
# scope-guard.sh
# 1) workspace/context/config.md 의 `## Ignore` 섹션에 해당하는 파일 수정을 차단한다.
# 2) 활성 프로젝트가 characterize 모드면 {source_root} 하위 수정을 사전 차단한다
#    (evaluator 의 git diff 사후 게이트를 Edit/Write 시점으로 조기화 — 원복 사이클 방지).

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

# --- characterize 모드 source_root 잠금 ------------------------------------
# STATE.md 진행중 프로젝트의 .agent-state.yml 이 mode: characterize 면,
# source_root (project.md 제한사항 override > config.md 언어·도구 기본값) 하위
# 수정을 차단한다. 테스트 계층 (test_path_convention 의 고정 prefix) 은 허용.
STATE_MD="$PROJECT_DIR/workspace/STATE.md"
if [[ -f "$STATE_MD" ]]; then
  ACTIVE_PROJECT=$(awk -F'|' '$0 ~ /진행중/ { gsub(/^[ \t]+|[ \t]+$/, "", $3); if ($3 != "") { print $3; exit } }' "$STATE_MD")
  STATE_YML="$PROJECT_DIR/workspace/projects/$ACTIVE_PROJECT/.agent-state.yml"
  if [[ -n "$ACTIVE_PROJECT" && -f "$STATE_YML" ]] \
    && grep -qE '^mode:[[:space:]]*"?characterize"?[[:space:]]*$' "$STATE_YML"; then

    # config.md `## 언어·도구 기본값` 표 또는 project.md `## 제한사항` 의 key 값 추출
    lang_key() {
      local key="$1" project_md="$PROJECT_DIR/workspace/projects/$ACTIVE_PROJECT/project.md" val=""
      if [[ -f "$project_md" ]]; then
        val=$(sed -nE "s/^[ \t]*-[ \t]*\*{0,2}${key}\*{0,2}[ \t]*:[ \t]*\`?([^\`]+)\`?[ \t]*$/\1/p" "$project_md" | head -1)
      fi
      if [[ -z "$val" ]]; then
        val=$(sed -nE "s/^\|[ \t]*\`?${key}\`?[ \t]*\|[ \t]*\`?([^\`|]+)\`?[ \t]*\|.*$/\1/p" "$CONFIG_FILE" | head -1)
      fi
      # 미기입 placeholder (공백·예시 구분자 포함) 는 미설정으로 간주
      val="${val%"${val##*[![:space:]]}"}"   # trailing 공백 제거
      if [[ "$val" == *" "* || "$val" == *"·"* ]]; then val=""; fi
      printf '%s' "$val"
    }

    SOURCE_ROOT=$(lang_key "source_root")
    if [[ -n "$SOURCE_ROOT" ]]; then
      SOURCE_ROOT="${SOURCE_ROOT#./}"
      SOURCE_ROOT="${SOURCE_ROOT%/}/"
      # test_path_convention 의 glob 이전 고정 prefix (예: spec/**/... → spec/)
      TEST_CONV=$(lang_key "test_path_convention")
      TEST_PREFIX="${TEST_CONV%%\**}"
      if [[ "$REL_PATH" == "$SOURCE_ROOT"* ]]; then
        if [[ -z "$TEST_PREFIX" || "$REL_PATH" != "$TEST_PREFIX"* ]]; then
          echo "❌ characterize 모드 — source_root 수정 차단: $REL_PATH" >&2
          echo "   현재 동작 포착 사이클에서는 {source_root}($SOURCE_ROOT) 를 수정할 수 없습니다." >&2
          echo "   테스트 계층(픽스처·헬퍼 포함)만 추가하세요. 구현 변경은 characterize 종료 후 별도 사이클." >&2
          exit 2
        fi
      fi
    fi
  fi
fi

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
