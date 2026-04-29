#!/usr/bin/env bash
# diff.sh — v0.1.0-baseline 회귀 비교 도구
#
# 사용법:
#   bash diff.sh --stage 1   # Stage 1: config 비움 검증
#   bash diff.sh --stage 2   # Stage 2: config 채움 검증
#
# exit 0 = 회귀 없음
# exit 1 = diff 발견
# exit 2 = _input/ 미존재 (0b 미완료 — 실행 불가)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="$SCRIPT_DIR/_input"

STAGE=""

# ---------------------------------------------------------------------------
# 인자 처리
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --stage)
            STAGE="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 --stage {1|2}" >&2
            exit 2
            ;;
    esac
done

if [[ -z "$STAGE" ]]; then
    echo "[ERROR] --stage 인자 필수 (1 또는 2)" >&2
    echo "Usage: $0 --stage {1|2}" >&2
    exit 2
fi

if [[ "$STAGE" != "1" && "$STAGE" != "2" ]]; then
    echo "[ERROR] --stage 값은 1 또는 2 여야 합니다 (받은 값: $STAGE)" >&2
    exit 2
fi

# ---------------------------------------------------------------------------
# _input/ 존재 확인 (0b 완료 여부 게이트)
# ---------------------------------------------------------------------------
if [[ ! -d "$INPUT_DIR" ]]; then
    echo "[ERROR] _input/ 디렉터리가 없습니다." >&2
    echo "        Open Q #1 (입력 언어 결정) 이후 0b PR 에서 추가됩니다." >&2
    echo "        현재는 config/ 인공 fixture + diff.sh 골격만 포함 (0a 범위)." >&2
    exit 2
fi

# ---------------------------------------------------------------------------
# Stage 에 따른 expected 디렉터리 결정
# ---------------------------------------------------------------------------
if [[ "$STAGE" == "1" ]]; then
    EXPECTED_DIRS=("learn/expected" "project/expected" "analyze/expected")
    echo "[diff.sh] Stage 1: config 비움 — v0.1.0 = v1 출력 동일 검증"
else
    EXPECTED_DIRS=("learn/expected" "project/expected" "analyze/expected")
    echo "[diff.sh] Stage 2: config 채움 — v1 override 거동 검증"
fi

# ---------------------------------------------------------------------------
# timestamp placeholder 정규화 함수
# (analyzed_at 등 timestamp 를 {ANALYZED_AT} 으로 치환해 diff 노이즈 제거)
# ---------------------------------------------------------------------------
normalize() {
    local file="$1"
    # ISO 8601 timestamp (2026-04-29T12:34:56Z 형태) → {ANALYZED_AT}
    sed 's/[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}T[0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}Z\?/{ANALYZED_AT}/g' "$file"
}

# ---------------------------------------------------------------------------
# diff 실행
# ---------------------------------------------------------------------------
DIFF_FOUND=0

for expected_rel in "${EXPECTED_DIRS[@]}"; do
    expected_dir="$SCRIPT_DIR/$expected_rel"
    if [[ ! -d "$expected_dir" ]]; then
        echo "[SKIP] $expected_rel 없음 (0b 미완료)"
        continue
    fi

    # 현재 빌드 결과와 expected 를 비교
    # 실제 빌드 실행은 각 스킬을 _input/ 으로 호출하는 방식으로 구현 (0b 에서 확정)
    echo "[INFO] $expected_rel vs 현재 출력 비교..."

    # 임시 출력 디렉터리 (0b 에서 실제 빌드 결과 경로로 교체)
    TMP_OUT=$(mktemp -d)
    trap 'rm -rf "$TMP_OUT"' EXIT

    # placeholder: 0b 에서 실제 스킬 호출로 교체
    # 예: python3 "$(dirname "$SCRIPT_DIR")/../../skills/learn/run.py" --input "$INPUT_DIR" --out "$TMP_OUT/learn"

    while IFS= read -r -d '' expected_file; do
        rel_path="${expected_file#$expected_dir/}"
        actual_file="$TMP_OUT/$rel_path"

        if [[ ! -f "$actual_file" ]]; then
            echo "[DIFF] 누락: $rel_path"
            DIFF_FOUND=1
            continue
        fi

        # timestamp 정규화 후 diff
        expected_norm=$(normalize "$expected_file")
        actual_norm=$(normalize "$actual_file")

        if ! diff -u <(echo "$expected_norm") <(echo "$actual_norm") > /dev/null 2>&1; then
            echo "[DIFF] 변경: $rel_path"
            diff -u <(echo "$expected_norm") <(echo "$actual_norm") || true
            DIFF_FOUND=1
        fi
    done < <(find "$expected_dir" -type f -print0)
done

# ---------------------------------------------------------------------------
# 결과
# ---------------------------------------------------------------------------
if [[ "$DIFF_FOUND" -eq 0 ]]; then
    echo "[OK] 회귀 없음 — Stage $STAGE 검증 통과"
    exit 0
else
    echo "[FAIL] diff 발견 — Stage $STAGE 회귀 감지"
    exit 1
fi
