#!/usr/bin/env bash
# coding-rules.sh
# PostToolUse(Edit|Write): 소스 파일 수정 후 workspace 코딩 규칙 준수 검증을 리마인드한다.
# 코딩 규칙(conventions_doc 또는 context/rules/*.md)이 workspace 에 없으면 no-op.
# PostToolUse 이므로 차단하지 않는다 — additionalContext 로 리마인드만 주입한다.

set -euo pipefail

# tool_input.file_path 추출
INPUT=$(cat /dev/stdin)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")
[[ -z "$FILE_PATH" ]] && exit 0

# 세션당 1회 발화 — 같은 안내가 Edit 마다 대화 컨텍스트에 누적되는 것을 방지.
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null || echo "")
MARKER=""
if [[ -n "$SESSION_ID" ]]; then
  MARKER="${TMPDIR:-/tmp}/pilot-coding-rules.$(printf '%s' "$SESSION_ID" | tr -cd '[:alnum:]-_')"
  [[ -f "$MARKER" ]] && exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# 프로젝트 디렉토리 밖의 파일은 대상 아님 → skip (REL_PATH 미스트립 오발화 방지)
[[ "$FILE_PATH" != "$PROJECT_DIR"/* ]] && exit 0
REL_PATH="${FILE_PATH#$PROJECT_DIR/}"

# workspace/ 내부 (pilot 컨텍스트·상태 문서) 는 프로젝트 소스가 아님 → skip
[[ "$REL_PATH" == workspace/* ]] && exit 0

CONTEXT_DIR="$PROJECT_DIR/workspace/context"
CONFIG_FILE="$CONTEXT_DIR/config.md"
RULES_DIR="$CONTEXT_DIR/rules"

# source_root 가 선언돼 있으면 그 안의 파일만 대상 (문서·스크립트 등 소스 밖 수정에 오발화 방지).
# 실재하는 디렉토리일 때만 적용 — 템플릿 placeholder 값은 -d 검사에서 걸러진다 (fail-open).
if [[ -f "$CONFIG_FILE" ]]; then
  SOURCE_ROOT=$(sed -nE 's/^\|[ \t]*`?source_root`?[ \t]*\|[ \t]*`?([^`|]+)`?[ \t]*\|.*$/\1/p' "$CONFIG_FILE" | head -1 | tr -d '[:space:]')
  if [[ -n "$SOURCE_ROOT" && -d "$PROJECT_DIR/${SOURCE_ROOT%/}" ]]; then
    ROOT_TRIMMED="${SOURCE_ROOT%/}"
    case "$REL_PATH" in
      "$ROOT_TRIMMED"/*) ;;
      *) exit 0 ;;
    esac
  fi
fi

# --- 코딩 규칙 존재 여부 탐지 (규칙 없으면 hook 은 동작하지 않는다) ---
RULE_SOURCES=()

# (a) context/rules/*.md — 도메인 규칙
if [[ -d "$RULES_DIR" ]] && compgen -G "$RULES_DIR/*.md" > /dev/null 2>&1; then
  RULE_SOURCES+=("workspace/context/rules/ (도메인 규칙)")
fi

# (b) config.md `## 언어·도구 기본값` 의 conventions_doc — 언어·프레임워크 관행 문서
if [[ -f "$CONFIG_FILE" ]]; then
  CONV_RAW=$(awk '
    /^## 언어·도구 기본값/ {f=1; next}
    f && /^## / {exit}
    f && /^\| `conventions_doc`/
  ' "$CONFIG_FILE" | sed -nE 's/^\| `conventions_doc`[[:space:]]*\|([^|]*)\|.*$/\1/p' | head -1)
  CONV=$(echo "$CONV_RAW" | sed -E 's/예://; s/`//g' | tr -d '[:space:]')
  if [[ -n "$CONV" ]]; then
    for cand in "$CONTEXT_DIR/${CONV#context/}" "$PROJECT_DIR/workspace/$CONV" "$PROJECT_DIR/$CONV"; do
      if [[ -f "$cand" ]]; then
        RULE_SOURCES+=("$CONV (conventions_doc)")
        break
      fi
    done
  fi
fi

# 코딩 규칙이 하나도 없으면 동작하지 않는다 (no-op)
[[ ${#RULE_SOURCES[@]} -eq 0 ]] && exit 0

# --- 리마인드 컨텍스트 주입 (PostToolUse, 비차단) ---
SRC_LIST=$(printf '%s; ' "${RULE_SOURCES[@]}")
MSG="소스 파일 '${REL_PATH}' 이 수정되었습니다. pilot 워크스페이스에 코딩 규칙이 정의돼 있습니다 — 변경분이 다음 규칙을 준수하는지 검증하고, 미충족 항목은 수정 후 재확인하세요: ${SRC_LIST%; }. 언어 중립 원칙: ${CLAUDE_PLUGIN_ROOT:-\$CLAUDE_PLUGIN_ROOT}/skills/context/shared/coding.md (이 안내는 세션당 1회만 표시됩니다.)"

python3 -c "import json,sys; print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext': sys.argv[1]}}))" "$MSG"

[[ -n "$MARKER" ]] && { touch "$MARKER" 2>/dev/null || true; }

exit 0
