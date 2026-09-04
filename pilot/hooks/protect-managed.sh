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
# qa 규칙:
#   workspace/projects/{PROJECT}/features/**/*.md 는 phase=qa 동안
#   읽기 전용 (회귀영향 차단 — 신규 생성·Edit 포함 전부 차단).
#   qa/ 폴더는 phase 와 무관하게 쓰기 허용 (명시 — 향후 실수 방지).
#   fail-closed: phase 값이 development/qa 외이거나 state 를 읽을 수 없으면
#   features/ 쓰기를 차단한다 (오타가 조용히 통과해 qa 게이트가 풀리는 것 방지).
#
# 예외 (통과):
#   - Edit 도구 (splice 방식 — 안전) — phase=qa features/ 트리는 예외 아님
#   - 신규 파일 생성 (대상 경로에 파일 없음) — phase=qa features/ 트리는 예외 아님
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

# 인자: $1 = workspace/projects/{PROJECT}/ prefix (rel)
# stdout: 해당 project 의 phase 값 (yaml `phase:` 라인). 없거나 읽기 실패면 빈 문자열.
read_project_phase() {
  local proj_prefix="$1"
  local state_file="$PROJECT_DIR/${proj_prefix}.agent-state.yml"
  [[ ! -f "$state_file" ]] && return 0
  # 단순 awk — yq/python 의존성 없이 phase 라인 1 개만 추출.
  # 주석·들여쓰기·따옴표 허용. 첫 매칭만 사용.
  awk '
    /^[[:space:]]*phase[[:space:]]*:/ {
      sub(/^[[:space:]]*phase[[:space:]]*:[[:space:]]*/, "")
      sub(/[[:space:]]*#.*$/, "")
      sub(/[[:space:]]+$/, "")
      gsub(/^["\x27]|["\x27]$/, "")
      print
      exit
    }
  ' "$state_file" 2>/dev/null
}

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
  # projects 기본 규칙과 동일: Edit·신규 통과, 기존 파일·폴더 Write/destructive 차단.
  # (백업·focus 예외는 위 공통 예외가 이미 처리. qa/·features/ 규칙은 projects 전용.)
  if [[ "$rel_path" =~ ^(workspace/issues/[^/]+)(/|$) ]]; then
    [[ "$tool" == "Edit" ]] && return 0
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
  [[ ! "$rel_path" =~ ^(workspace/projects/[^/]+)(/|$) ]] && return 0
  local proj_prefix="${BASH_REMATCH[1]}/"
  local sub_path="${rel_path#$proj_prefix}"
  # 프로젝트 폴더 자체 (trailing slash 유무 불문) → sub_path 빈 값으로 정규화
  if [[ "$rel_path" == "${BASH_REMATCH[1]}" || "$rel_path" == "${BASH_REMATCH[1]}/" ]]; then
    sub_path=""
  fi

  # qa/ 폴더는 명시 허용 (phase 와 무관하게 항상 쓰기 가능 — 향후 실수 방지).
  [[ "$sub_path" == qa/* ]] && return 0

  # ── phase=qa features/ Write·Edit 차단 ────────────────────────────────────
  # features/**/*.md 는 QA phase 동안 회귀영향 차단을 위해 읽기 전용.
  # 신규 생성·기존 수정·중첩 폴더 모두 차단 (Edit 도 예외 아님).
  # fail-closed: phase 값 비정상·state 읽기 불가 시에도 차단 —
  # 오타(qaa 등)가 == "qa" 불일치로 조용히 통과하면 qa 게이트가 풀린다.
  if [[ "$sub_path" == features/*.md ]]; then
    local state_file="$PROJECT_DIR/${proj_prefix}.agent-state.yml"
    if [[ -f "$state_file" && ! -r "$state_file" ]]; then
      cat >&2 <<EOF
❌ [PROTECTED] $tool 차단: $rel_path
   .agent-state.yml 읽기 불가 — phase 판정 불가로 features/ 쓰기를 차단합니다 (fail-closed).
   파일 권한을 확인하세요: ${proj_prefix}.agent-state.yml
   우회: PILOT_PROTECT_BYPASS=1 환경변수와 함께 재실행
EOF
      return 2
    fi
    local phase
    phase=$(read_project_phase "$proj_prefix")
    if [[ "$phase" == "qa" ]]; then
      # project 이름 추출 (안내 메시지용)
      local project_name
      project_name=$(echo "$proj_prefix" | awk -F/ '{print $3}')
      cat >&2 <<EOF
❌ [PROTECTED] $tool 차단: $rel_path
   features/**/*.md (features/ 트리) 는 phase=qa 동안 읽기 전용입니다 (회귀영향 차단).
   수정이 필요하면:
     /pilot:project ${project_name} --qa off  (development 복귀)
   우회: PILOT_PROTECT_BYPASS=1 환경변수와 함께 재실행
EOF
      return 2
    elif [[ -n "$phase" && "$phase" != "development" ]]; then
      cat >&2 <<EOF
❌ [PROTECTED] $tool 차단: $rel_path
   .agent-state.yml 의 phase='$phase' 가 유효하지 않습니다 (허용: development, qa).
   판정 불가 시 features/ 쓰기를 차단합니다 (fail-closed).
   phase 행을 수정하거나 'python3 \${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace --fix' 로 재생성하세요.
   우회: PILOT_PROTECT_BYPASS=1 환경변수와 함께 재실행
EOF
      return 2
    fi
    # phase == development 또는 부재 → 기존 규칙으로 fall-through
  fi

  # Edit 도구는 기본 splice 안전 — phase=qa features/ 외엔 통과.
  [[ "$tool" == "Edit" ]] && return 0

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

# Edit 도구 — 기본 통과 (splice 안전). phase=qa features/ 잠금만 check_path 가 차단.
if [[ "$TOOL" == "Edit" ]]; then
  FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")
  [[ -z "$FILE_PATH" ]] && exit 0
  check_path "$FILE_PATH" "Edit" || exit $?
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
