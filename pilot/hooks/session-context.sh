#!/usr/bin/env bash
# session-context.sh
# SessionStart 훅 — 소비 레포에 pilot 워크스페이스가 있을 때만
# 메인 세션 컨텍스트에 도메인 컨텍스트 "포인터"를 주입한다.
#
# 갭: workspace/context/MANIFEST.md 의 적용 트리거는 스킬·서브에이전트에만
#   걸려 있어, 스킬을 부르지 않고 메인 세션이 직접 도메인 코드를 분석·디버깅할 때는
#   아무도 MANIFEST·STATE 를 읽지 않는다. 이 훅이 그 갭을 닫는다.
#
# 하드 게이트: workspace/context/MANIFEST.md 가 없으면 아무것도 출력하지 않는다.
#   exit 0 + 빈 stdout → SessionStart 훅은 컨텍스트를 추가하지 않는다(완전 무음).
#   pilot 미사용 레포에 흔적을 남기지 않기 위한 분기이며, 지시가 아니라 실제 게이트다.
#
# 포인터만 주입한다: 도메인 분류·로딩 규칙 등 실제 라우팅은 레포별 MANIFEST.md 가
#   SSOT 이며 이 훅에 복제하지 않는다.

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
MANIFEST_FILE="$PROJECT_DIR/workspace/context/MANIFEST.md"

# ── 하드 게이트 ───────────────────────────────────────────────
# workspace/context/MANIFEST.md 가 없으면 pilot 미사용 레포 — 완전 무음.
[[ ! -f "$MANIFEST_FILE" ]] && exit 0

# ── 포인터 본문 ───────────────────────────────────────────────
POINTER=$(cat <<'EOF'
[pilot 도메인 컨텍스트]
이 레포는 pilot 워크스페이스(workspace/)의 도메인 컨텍스트를 사용한다.
비즈니스 도메인 코드를 분석·디버깅·수정하기 전에:
1. workspace/context/MANIFEST.md 의 로딩 규칙에 따라 해당 도메인의 scope/·rules/(·필요 시 enums/) 를 적재한다.
2. workspace/STATE.md 로 진행 중인 project/issue 를 확인하고, 작업이 그 항목과
   관련되면 해당 컨텍스트(projects/{이름}/project.md 또는 issues/{이름}/issue.md)도 함께 검토한다.
읽기 전용 단순 질의나 도메인과 무관한 UI/인프라 작업에는 적용하지 않는다.
EOF
)

# ── SessionStart additionalContext 로 안전하게 직렬화해 출력 ──
# 본문이 여러 줄·한국어·특수문자를 포함하므로 json.dumps 로 이스케이프.
POINTER="$POINTER" python3 -c '
import os, json
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": os.environ["POINTER"],
    }
}, ensure_ascii=False))
'
