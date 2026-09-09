#!/usr/bin/env bash
# rules-trace.sh
# InstructionsLoaded 훅 — 경로 조건부 규칙(.claude/rules/*.md)이 언제·어느 에이전트에서·어떤 사유로 로드됐는지
# 1줄씩 남긴다 (#30 G4/G6 증거 — plan r2 critic C8). 플러그인 hooks.json 에는 등록하지 않는다: 계측이 필요한
# 사람이 .claude/settings.local.json 에 opt-in 등록한다 (#30 § 실측 기록의 스니펫). 로그 위치:
#   ${PILOT_RULES_TRACE_LOG:-${TMPDIR:-/tmp}/pilot-rules-trace.log}
# 입력(stdin JSON): session_id · load_reason(session_start|nested_traversal|path_glob_match|include|compact) ·
#   file_path · file_content · cwd · (서브에이전트) agent_id · agent_type. file_content 는 기록하지 않는다.
set -uo pipefail
LOG="${PILOT_RULES_TRACE_LOG:-${TMPDIR:-/tmp}/pilot-rules-trace.log}"
python3 - "$LOG" <<'PY' 2>/dev/null || true
import json, sys, time
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)  # 잘못된 입력 — 파일도 만들지 않는다
row = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "session": d.get("session_id", ""),
    "agent": d.get("agent_type") or "main",
    "reason": d.get("load_reason", ""),
    "file": d.get("file_path", ""),
    "cwd": d.get("cwd", ""),
}
with open(sys.argv[1], "a", encoding="utf-8") as fh:
    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
PY
exit 0
