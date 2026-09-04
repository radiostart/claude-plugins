#!/usr/bin/env bash
# scope-guard.sh
# 1) workspace/context/config.md 의 `## Ignore` 섹션에 해당하는 파일 수정을 차단한다.
# 2) 활성 프로젝트가 characterize 모드면 {source_root} 하위 수정을 사전 차단한다
#    (evaluator 의 git diff 사후 게이트를 Edit/Write 시점으로 조기화 — 원복 사이클 방지).

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
PROJECT_DIR="${PROJECT_DIR%/}"

# stdin JSON 의 tool_input.file_path 를 프로젝트 루트 기준 상대 경로로 변환한다.
# Ignore 패턴은 프로젝트 상대 규약이므로, 프로젝트 밖 경로 (스크래치패드·타 레포) 는
# 판정 대상이 아니라 보고 빈 문자열을 돌려 통과시킨다. 문자열 접두어 비교만 하면
# 심볼릭 링크 (`/tmp` ↔ `/private/tmp`) 나 `./`·`..` 표기 차이로 접두어가 어긋나
# 프로젝트 *안* 파일까지 통과하므로 (가드 무음 해제), lexical·realpath 양쪽을 본다.
REL_PATH=$(cat /dev/stdin | python3 -c '
import json, os, sys

proj = sys.argv[1]
try:
    d = json.load(sys.stdin)
except Exception:
    print(""); raise SystemExit(0)

fp = (d.get("tool_input") or {}).get("file_path") or ""
if not fp:
    print(""); raise SystemExit(0)

# 상대 경로 입력은 프로젝트 루트 기준으로 해석한다 (훅의 CWD 규약).
if not os.path.isabs(fp):
    fp = os.path.join(proj, fp)

# 둘 중 하나라도 프로젝트 안이면 프로젝트 파일로 취급 — 판정을 끄는 쪽으로 기울지 않는다
# (프로젝트 안에서 밖을 가리키는 심링크가 검사 대상에서 빠지는 것을 막는다).
for f, p in ((os.path.normpath(fp), os.path.normpath(proj)),
             (os.path.realpath(fp), os.path.realpath(proj))):
    if f == p or f.startswith(p.rstrip(os.sep) + os.sep):
        print(os.path.relpath(f, p)); raise SystemExit(0)

print("")
' "$PROJECT_DIR" 2>/dev/null || echo "")

# 경로가 없거나 프로젝트 밖이면 통과
[[ -z "$REL_PATH" ]] && exit 0

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

# config.md 의 `## Ignore` 섹션에서 첫 번째 컬럼(`pattern`)을 원형 그대로 추출한다.
# 정규화는 아래 매칭 루프가 담당한다 (패턴 종류를 구분해야 하므로 여기서 뭉개지 않는다).
IGNORE_PATTERNS=()
while IFS= read -r pattern; do
  [[ -z "$pattern" ]] && continue
  IGNORE_PATTERNS+=("$pattern")
done < <(
  awk '/^## Ignore/{flag=1; next} /^## /{flag=0} flag && /^\| `/' "$CONFIG_FILE" \
    | sed -E 's/^\|[[:space:]]*`([^`]+)`.*/\1/'
)

# Ignore 섹션이 비어있으면 통과
[[ ${#IGNORE_PATTERNS[@]} -eq 0 ]] && exit 0

# 패턴 해석은 gitignore 규약을 따른다 (config.md 가 "Glob 패턴" 이라 선언한 것의 표준 해석).
#   - `**/` 접두어, 또는 `/` 가 없는 패턴 (`*.http`·`poetry.lock`) → 임의 깊이에서 매칭
#   - 그 외 경로 패턴 (`tmp/**`·`app/models/gen_*`)             → 프로젝트 루트 기준 앵커
#   - `/**`·`/` 접미어 → 그 디렉터리 자신과 하위 전체
# glob 매칭이라 `*.http` 가 `api.httpie.md`·`response.http.json` 을 잡던 substring 오차단도
# 함께 사라진다 (패턴이 문자열 어딘가가 아니라 경로 전체와 대응해야 한다).
for pattern in "${IGNORE_PATTERNS[@]}"; do
  p="$pattern"

  anydepth=false
  if [[ "$p" == '**/'* ]]; then
    anydepth=true
    p="${p#'**/'}"
  fi

  # 앵커 여부는 접미어를 벗기기 *전* 형태로 판정한다 — gitignore 는 경로 중간의 `/` 만
  # 앵커 신호로 보고 후행 `/` 는 세지 않는다 (`tmp/**` 는 앵커, `log/` 는 임의 깊이).
  [[ "${p%/}" != */* ]] && anydepth=true

  subtree=false
  if [[ "$p" == */'**' ]]; then
    p="${p%'/**'}"
    subtree=true
  elif [[ "$p" == */ ]]; then
    p="${p%/}"
    subtree=true
  fi

  [[ -z "$p" ]] && continue

  pats=("$p")
  [[ "$subtree" == true ]] && pats+=("$p/*")

  matched=false
  for pat in "${pats[@]}"; do
    if [[ "$REL_PATH" == $pat ]]; then
      matched=true
      break
    fi
    if [[ "$anydepth" == true && "$REL_PATH" == */$pat ]]; then
      matched=true
      break
    fi
  done

  if [[ "$matched" == true ]]; then
    echo "❌ Scope 외 파일 수정 차단: $REL_PATH" >&2
    echo "   config.md Ignore 패턴에 해당합니다: $pattern" >&2
    echo "   이 파일을 수정해야 한다면 사용자에게 확인을 받으세요." >&2
    exit 2
  fi
done

exit 0
