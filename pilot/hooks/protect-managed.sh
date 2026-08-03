#!/usr/bin/env bash
# protect-managed.sh
# 기존 프로젝트 파일 보호 — 동일 프로젝트명으로 재호출 시 누적 작업물 손실 차단.
#
# 단일 규칙:
#   workspace/projects/{PROJECT}/ 하위 *기존 파일* 에 대한
#   Write 와 destructive Bash 명령은 차단. Edit·신규 파일·외부 경로는 통과.
#
# issues/ 규칙:
#   workspace/issues/{이슈명}/ 하위 *기존 파일* 도 동일 보호 —
#   issue.md 의 사용자 작성 현상·누적 기록이 재진입 Write 로 소실되는 것을
#   차단한다. Edit (원인·조치 기입)·신규 파일 (사이클 파생 산출물)·`.focus.*`
#   는 통과. issues/ 상위 폴더 destructive 도 projects/ 와 대칭으로 차단.
#
# 예외 (통과):
#   - Edit 도구 (splice 방식 — 안전)
#   - 신규 파일 생성 (대상 경로에 파일 없음)
#   - .prompts.bak/ · .bak.* 경로 (백업물)
#   - features/*.eval[.rN].md · issues/*/issue.eval[.rN].md (evaluator REPORT — 재생성 산출물)
#   - 프로젝트 폴더 외부 경로
#
# 명시 우회: PILOT_PROTECT_BYPASS=1 환경변수 (의도적 destructive 시).

set -euo pipefail

INPUT=$(cat /dev/stdin)
TOOL=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")

[[ "${PILOT_PROTECT_BYPASS:-}" == "1" ]] && exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# 인자: $1 = 경로 (절대/상대), $2 = 도구명
# 반환: 0 = 통과, 2 = 차단
check_path() {
  local file_path="$1"
  local tool="$2"
  # `./` 접두 정규화 — 접두가 남으면 아래 regex 판정을 통째로 벗어난다.
  while [[ "$file_path" == ./* ]]; do file_path="${file_path#./}"; done
  local rel_path="${file_path#$PROJECT_DIR/}"

  # 백업 경로는 통과
  [[ "$rel_path" == *".prompts.bak/"* ]] && return 0
  [[ "$rel_path" == *".bak."* ]] && return 0
  # focus 수명주기 경로는 통과 (focus 스킬의 아카이브 mv/삭제/재작성 흐름)
  [[ "$rel_path" == */.focus.md ]] && return 0
  [[ "$rel_path" == *".focus.history/"* ]] && return 0

  # evaluator REPORT 산출물은 통과 — 재평가마다 전체 재생성 (agents/pilot-evaluator step 7,
  # 이슈 규약 issues/GUIDE.md). 이력은 git 이 보존. 접미 고정 매치 — `.evaluate.md` 류 서브스트링 오매치 방지.
  [[ "$rel_path" == */features/*.eval.md || "$rel_path" == */features/*.eval.r[0-9]*.md ]] && return 0
  [[ "$rel_path" == */issues/*/issue.eval.md || "$rel_path" == */issues/*/issue.eval.r[0-9]*.md ]] && return 0

  # projects/ 상위 폴더 자체 — destructive 대상이면 차단 (모든 프로젝트 소실 경로)
  if [[ "$rel_path" =~ ^(workspace/projects)/?$ ]]; then
    local abs_parent
    if [[ "$file_path" = /* ]]; then abs_parent="$file_path"; else abs_parent="$PROJECT_DIR/${BASH_REMATCH[1]}"; fi
    [[ ! -e "$abs_parent" ]] && return 0
    cat >&2 <<EOF
❌ $tool 차단: $rel_path
   projects/ 상위 폴더 삭제·이동 금지 — 모든 프로젝트의 누적 작업물이 소실됩니다.
   우회: PILOT_PROTECT_BYPASS=1 환경변수와 함께 재실행 (백업 권장)
EOF
    return 2
  fi

  # issues/ 상위 폴더 자체 — destructive 대상이면 차단 (모든 이슈 기록 소실 경로)
  if [[ "$rel_path" =~ ^(workspace/issues)/?$ ]]; then
    local abs_iparent
    if [[ "$file_path" = /* ]]; then abs_iparent="$file_path"; else abs_iparent="$PROJECT_DIR/${BASH_REMATCH[1]}"; fi
    [[ ! -e "$abs_iparent" ]] && return 0
    cat >&2 <<EOF
❌ $tool 차단: $rel_path
   issues/ 상위 폴더 삭제·이동 금지 — 모든 이슈의 누적 기록이 소실됩니다.
   우회: PILOT_PROTECT_BYPASS=1 환경변수와 함께 재실행 (백업 권장)
EOF
    return 2
  fi

  # workspace/issues/{이슈명} 자기 자신 또는 하위 검사
  # projects 기본 규칙과 동일: 신규 통과, 기존 파일·폴더 Write/destructive 차단.
  # Edit 분기 코드는 불필요 — 이 훅은 Write·Bash 만 처리하므로 Edit 통과는 구조적 보장.
  # (백업·focus 예외는 위 공통 예외가 이미 처리.)
  if [[ "$rel_path" =~ ^(workspace/issues/[^/]+)(/|$) ]]; then
    local abs_issue
    if [[ "$file_path" = /* ]]; then abs_issue="$file_path"; else abs_issue="$PROJECT_DIR/$rel_path"; fi
    [[ ! -e "$abs_issue" ]] && return 0
    cat >&2 <<EOF
❌ $tool 차단: $rel_path
   기존 이슈 파일·폴더 덮어쓰기·삭제·이동 금지 (issue.md 의 사용자 작성 현상·기록 손실 위험).
   대안:
     - 부분 갱신 (원인·조치·재발 방지 기입) → Edit 도구
     - 의도적 reset → PILOT_PROTECT_BYPASS=1 환경변수와 함께 재실행 (백업 권장)
EOF
    return 2
  fi

  # workspace/projects/*/ 하위 + 프로젝트 폴더 자체(trailing slash 없는 rm -rf 등) 검사
  [[ ! "$rel_path" =~ ^workspace/projects/[^/]+(/|$) ]] && return 0

  # 절대 경로 정규화
  local abs_path
  if [[ "$file_path" = /* ]]; then
    abs_path="$file_path"
  else
    abs_path="$PROJECT_DIR/$rel_path"
  fi

  # 파일·폴더 모두 없으면 신규 생성 — 허용
  [[ ! -e "$abs_path" ]] && return 0

  cat >&2 <<EOF
❌ $tool 차단: $rel_path
   기존 프로젝트 파일 덮어쓰기·삭제 금지 (누적 작업물 손실 위험).
   대안:
     - 부분 갱신 → Edit 도구
     - 의도적 reset → PILOT_PROTECT_BYPASS=1 환경변수와 함께 재실행 (백업 권장)
EOF
  return 2
}

# Write 도구
if [[ "$TOOL" == "Write" ]]; then
  FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")
  [[ -z "$FILE_PATH" ]] && exit 0
  check_path "$FILE_PATH" "Write" || exit $?
  exit 0
fi

# Bash 도구 — destructive 명령의 write/delete target 추출
if [[ "$TOOL" == "Bash" ]]; then
  CMD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")
  [[ -z "$CMD" ]] && exit 0

  TARGETS=$(CMD_FOR_PARSE="$CMD" python3 - <<'PY'
import os, re, shlex

cmd = os.environ.get("CMD_FOR_PARSE", "")
try:
    tokens = shlex.split(cmd, posix=True)
except ValueError:
    # 따옴표 unbalanced — 보수적으로 모든 workspace 토큰 검사
    for t in re.findall(r"[\w./\-]*workspace/[\w./\-]+", cmd):
        print(t)
    raise SystemExit(0)

WS_RE = re.compile(r"workspace/[\w./\-]+")
def is_ws(tok):
    return bool(WS_RE.search(tok))

targets = []

# 1차: 리다이렉트 `>` / `>>` (명령 어디서나 등장)
for i, tok in enumerate(tokens):
    if tok in (">", ">>"):
        if i + 1 < len(tokens) and is_ws(tokens[i+1]):
            targets.append(tokens[i+1])
    else:
        m = re.match(r"^>{1,2}(.+)$", tok)
        if m and is_ws(m.group(1)):
            targets.append(m.group(1))

# 2차: 명령별 target 추론
i = 0
n = len(tokens)
while i < n:
    tok = tokens[i]
    if tok == "tee":
        j = i + 1
        while j < n and tokens[j].startswith("-"):
            j += 1
        if j < n and is_ws(tokens[j]):
            targets.append(tokens[j])
        i = j + 1; continue
    if tok in ("cp", "install"):
        # source read, target write — 마지막 non-flag 만
        rest = [t for t in tokens[i+1:] if not t.startswith("-")]
        if rest and is_ws(rest[-1]):
            targets.append(rest[-1])
        break
    if tok == "mv":
        # source 삭제 + target write — 양쪽 모두 destructive
        rest = [t for t in tokens[i+1:] if not t.startswith("-")]
        for r in rest:
            if is_ws(r):
                targets.append(r)
        break
    if tok == "sed":
        has_i = any(t == "-i" or t.startswith("-i") for t in tokens[i+1:])
        if has_i:
            rest = [t for t in tokens[i+1:] if not t.startswith("-")]
            if len(rest) >= 2 and is_ws(rest[-1]):
                targets.append(rest[-1])
        break
    if tok == "truncate":
        rest = [t for t in tokens[i+1:] if not t.startswith("-")]
        if rest and is_ws(rest[-1]):
            targets.append(rest[-1])
        break
    if tok == "rm":
        rest = [t for t in tokens[i+1:] if not t.startswith("-")]
        for r in rest:
            if is_ws(r):
                targets.append(r)
        break
    i += 1

# python -c "...open(path, 'w'/'a'/...)..." 패턴
open_re = re.compile(r"open\s*\(\s*[\x22\x27]([^\x22\x27]+)[\x22\x27]\s*,\s*[\x22\x27](w|a|wb|ab|w\+|a\+|x)[\x22\x27]")
for m in open_re.finditer(cmd):
    if is_ws(m.group(1)):
        targets.append(m.group(1))

seen = set()
for t in targets:
    t = t.strip(chr(34) + chr(39) + chr(96))
    if t and t not in seen:
        seen.add(t)
        print(t)
PY
)

  [[ -z "$TARGETS" ]] && exit 0

  rc=0
  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    check_path "$path" "Bash" || rc=$?
  done <<< "$TARGETS"

  exit $rc
fi

exit 0
