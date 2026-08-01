#!/usr/bin/env bash
# commit-format.sh
# git commit -m 실행 시 커밋 메시지 형식을 검증한다. (규칙 SSOT: skills/context/shared/commit.md)
# 한계: -F 파일 방식 메시지는 추출 불가라 검증 없이 통과하고,
# stderr 경고는 advisory (항상 exit 0) — 이 훅은 commit.md 준수를 돕는 보조 장치다.

set -euo pipefail

# stdin JSON에서 command 추출
COMMAND=$(cat /dev/stdin | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

# git commit 명령이 아니면 통과.
# 명령 위치 앵커링 — 행 시작 또는 체인 토큰(; & | () 뒤의 `git commit` 만 커밋으로
# 판정한다. substring 매칭은 `echo 'git commit -m ...' >> doc.md` 같은 비커밋
# 명령까지 검증 대상에 걸었다.
if ! printf '%s\n' "$COMMAND" | grep -Eq '(^|[;&|(])[[:space:]]*git[[:space:]]+commit'; then
  exit 0
fi
# --amend 는 검증 제외
[[ "$COMMAND" == *"--amend"* ]] && exit 0

# 커밋 메시지 추출
# 1) -m "..." 또는 -m '...' 방식 — *첫 번째* -m 이 제목이다.
#    (sed greedy 패턴은 다중 -m 에서 마지막 -m(본문)을 제목으로 오추출)
MSG=$(COMMAND_FOR_PARSE="$COMMAND" python3 - <<'PY' 2>/dev/null || echo ""
import os, re
cmd = os.environ.get("COMMAND_FOR_PARSE", "")
cands = []
# 개행 제외 — 닫는 따옴표가 같은 행에 있어야 매칭 (HEREDOC `-m "$(cat <<'EOF'` 는
# 여기서 매칭되지 않고 아래 HEREDOC 분기로 넘어간다)
for pat in (r'-m[ \t]+"([^"\n]*)"', r"-m[ \t]+'([^'\n]*)'"):
    m = re.search(pat, cmd)
    if m:
        cands.append((m.start(), m.group(1)))
if cands:
    print(min(cands)[1])
PY
)

# 2) HEREDOC 방식: git commit -m "$(cat <<'EOF'\n...\nEOF\n)"
#    Claude Code 가 커밋 시 사용하는 형식 — 첫 번째 내용 줄을 제목으로 추출
if [[ -z "$MSG" && ("$COMMAND" == *"<<'EOF'"* || "$COMMAND" == *'<<"EOF"'*) ]]; then
  MSG=$(printf '%s\n' "$COMMAND" \
    | awk "/<<['\"]EOF['\"]/{flag=1; next} flag && /^[[:space:]]*EOF[[:space:]]*$/{exit} flag{print}" \
    | sed 's/^[[:space:]]*//' \
    | grep -v '^$' \
    | head -1)
fi

# 메시지를 추출할 수 없으면 통과 (비표준 커밋 방식)
[[ -z "$MSG" ]] && exit 0

# 첫 번째 줄(제목)만 검사
TITLE=$(printf '%s\n' "$MSG" | head -1)
# 길이는 UTF-8 문자 수 기준 — bash ${#} 는 locale 이 C 면 바이트 수를 세서
# 한국어 제목이 3배로 과대 측정된다.
TITLE_LEN=$(printf '%s' "$TITLE" | python3 -c "import sys; print(len(sys.stdin.buffer.read().decode('utf-8', 'replace')))" 2>/dev/null || echo "${#TITLE}")

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

# scope: 형식인데 허용 목록 밖의 scope 사용 — `feat(api):` 서브 scope 표기도 파싱
# (VALID_SCOPES_CSV 가 비어있으면 이 검증 자체 skip — config.md 팀 설정 미기입 케이스)
# 주의: [[ =~ ]] 안에 괄호가 포함된 regex는 구문 오류 유발 → 변수로 분리
SCOPE_REGEX='^([a-z]+)(\([^)]+\))?:[[:space:]]'
if [[ -n "$VALID_SCOPES_CSV" && "$TITLE" =~ $SCOPE_REGEX ]]; then
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
