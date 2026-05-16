#!/usr/bin/env bash
# coding-rules.sh
# PostToolUse(Edit|Write): 소스 파일 수정 후 workspace 코딩 규칙 준수 검증을 리마인드한다.
# 코딩 규칙(conventions_doc 또는 context/rules/*.md)이 workspace 에 없으면 no-op.
# PostToolUse 이므로 차단하지 않는다 — additionalContext 로 리마인드만 주입한다.

set -euo pipefail

# tool_input.file_path 추출
FILE_PATH=$(cat /dev/stdin | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")
[[ -z "$FILE_PATH" ]] && exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
REL_PATH="${FILE_PATH#$PROJECT_DIR/}"

# workspace/ 내부 (pilot 컨텍스트·상태 문서) 는 프로젝트 소스가 아님 → skip
[[ "$REL_PATH" == workspace/* ]] && exit 0

CONTEXT_DIR="$PROJECT_DIR/workspace/context"
CONFIG_FILE="$CONTEXT_DIR/config.md"
RULES_DIR="$CONTEXT_DIR/rules"

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
MSG="소스 파일 '${REL_PATH}' 이 수정되었습니다. pilot 워크스페이스에 코딩 규칙이 정의돼 있습니다 — 변경분이 다음 규칙을 준수하는지 검증하고, 미충족 항목은 수정 후 재확인하세요: ${SRC_LIST%; }"

python3 -c "import json,sys; print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext': sys.argv[1]}}))" "$MSG"

exit 0
