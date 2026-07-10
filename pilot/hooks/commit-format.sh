#!/usr/bin/env bash
# commit-format.sh
# git commit -m 실행 시 커밋 메시지 형식을 검증한다. (규칙 SSOT: skills/context/shared/commit.md)
# 한계: heredoc / -F 파일 방식 메시지는 추출 불가라 검증 없이 통과하고,
# stderr 경고는 advisory (항상 exit 0) — 이 훅은 commit.md 준수를 돕는 보조 장치다.

set -euo pipefail

# stdin JSON에서 command 추출
COMMAND=$(cat /dev/stdin | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

# git commit 명령이 아니면 통과
[[ "$COMMAND" != *"git commit"* ]] && exit 0
# --amend 는 검증 제외
[[ "$COMMAND" == *"--amend"* ]] && exit 0

# 커밋 메시지 추출 (-m "..." 또는 -m '...' 방식)
# macOS/BSD grep 은 -oP (PCRE) 비지원 → sed -E 로 호환 추출.
MSG=$(echo "$COMMAND" | sed -nE 's/.*-m "([^"]*)".*/\1/p' | head -1)
if [[ -z "$MSG" ]]; then
  MSG=$(echo "$COMMAND" | sed -nE "s/.*-m '([^']*)'.*/\1/p" | head -1)
fi

# 메시지를 추출할 수 없으면 통과 (heredoc 방식 등)
[[ -z "$MSG" ]] && exit 0

# 첫 번째 줄(제목)만 검사
TITLE=$(echo "$MSG" | head -1)
TITLE_LEN=${#TITLE}

# VALID_SCOPES 결정 순서:
# 1. workspace/context/config.md 의 `## 설정` 표에 `commit_scopes` 행
# 2. 부재 시 기본값 fallback — shared/commit.md 의 scope 표 4종 + 작성 원칙의 `wip` (commit.md 가 SSOT)
#    ({기능명} 자유 scope 는 목록 검증 불가 — advisory 경고로만 노출됨)
DEFAULT_SCOPES="feat,fix,refactor,skills,wip"
VALID_SCOPES_CSV="$DEFAULT_SCOPES"

CONFIG_FILE="workspace/context/config.md"
if [[ -f "$CONFIG_FILE" ]]; then
  # `## 설정` 섹션에서 `| commit_scopes | <value> |` 추출.
  # awk 로 섹션 범위 한정, sed 로 값 컬럼만 추출. 백틱·공백 제거.
  FROM_CONFIG=$(awk '
    /^## 설정/ {in_sec=1; next}
    in_sec && /^## / {exit}
    in_sec && /^\| commit_scopes /
  ' "$CONFIG_FILE" | sed -nE 's/^\| commit_scopes[[:space:]]*\|[[:space:]]*`?([^`|]+)`?[[:space:]]*\|.*$/\1/p' | head -1 | tr -d '[:space:]')
  if [[ -n "$FROM_CONFIG" ]]; then
    VALID_SCOPES_CSV="$FROM_CONFIG"
  fi
fi

# CSV → pipe-separated (bash regex 에서 사용)
VALID_SCOPES=$(echo "$VALID_SCOPES_CSV" | tr ',' '|')

# 형식 검증
# 허용 형식 1: {scope}: {설명}
# 허용 형식 2: [{티켓번호}] {설명}
# 허용 형식 3: 한국어 설명만 (scope 없음)

ERRORS=()

# 50자 초과 경고 (차단하지 않고 additionalContext로 전달)
if [[ $TITLE_LEN -gt 50 ]]; then
  ERRORS+=("제목이 ${TITLE_LEN}자입니다. 50자 이내를 권장합니다.")
fi

# scope: 형식인데 허용 목록 밖의 scope 사용
# (VALID_SCOPES_CSV 가 비어있으면 이 검증 자체 skip — config.md 팀 설정 미기입 케이스)
if [[ -n "$VALID_SCOPES_CSV" && "$TITLE" =~ ^([a-z]+): ]]; then
  SCOPE="${BASH_REMATCH[1]}"
  if ! echo "$SCOPE" | grep -qE "^($VALID_SCOPES)$"; then
    ERRORS+=("알 수 없는 scope: '$SCOPE'. 허용 목록: ${VALID_SCOPES_CSV}")
  fi
fi

# 에러가 없으면 통과
[[ ${#ERRORS[@]} -eq 0 ]] && exit 0

# 경고/오류를 additionalContext로 출력 (exit 0으로 차단하지 않고 피드백만)
echo "⚠️  커밋 메시지 검토 (commit.md 기준):" >&2
for err in "${ERRORS[@]}"; do
  echo "   - $err" >&2
done
echo "" >&2
echo "권장 형식:" >&2
echo "  feat: 신규 기능 설명" >&2
echo "  fix: 버그 수정 설명" >&2
echo "  [TICKET-123] 티켓 기반 설명" >&2
echo "  order: 기능명 기반 설명" >&2

# 50자 초과는 경고만 (exit 0), 차단하지 않음
exit 0
