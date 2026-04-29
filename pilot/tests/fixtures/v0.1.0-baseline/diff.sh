#!/usr/bin/env bash
# diff.sh — v0.1.0-baseline 회귀 비교 도구
#
# 사용법:
#   bash diff.sh --actual {dir}
#
#   {dir} = 세 스킬을 _input/ 으로 재실행한 결과 디렉터리.
#           디렉터리 안에 learn/·project/·analyze/ 서브 트리가 있어야 한다.
#
# exit 0 = 회귀 없음 (actual == expected byte-for-byte)
# exit 1 = diff 발견
# exit 2 = 인자 오류 또는 _input/ 미존재 (0b 미완료 — 실행 불가)
#
# 주의:
# - timestamp 정규화 없음 — .agent-state.yml 의 analyzed_at 등 timestamp 는
#   캡처 시점 그대로. 재실행 시 timestamp 가 달라 diff 1 로 처리됨.
#   v1.1 milestone 에서 placeholder 정규화 도입 예정.
# - Stage 2 (config override 거동) 는 v1.1 milestone.
# - Open Q #3 결정: diff -ru 단순 비교. 정규화 없음.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="$SCRIPT_DIR/_input"

ACTUAL_DIR=""

# ---------------------------------------------------------------------------
# 인자 처리
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --actual)
            ACTUAL_DIR="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 --actual {dir}" >&2
            exit 2
            ;;
    esac
done

if [[ -z "$ACTUAL_DIR" ]]; then
    echo "[ERROR] --actual {dir} 인자 필수" >&2
    echo "Usage: $0 --actual {dir}" >&2
    exit 2
fi

# ---------------------------------------------------------------------------
# _input/ 존재 확인 (0b 완료 여부 게이트)
# ---------------------------------------------------------------------------
if [[ ! -d "$INPUT_DIR" ]]; then
    echo "[ERROR] _input/ 디렉터리가 없습니다." >&2
    echo "        0b PR 이 완료되어야 diff.sh 를 실행할 수 있습니다." >&2
    exit 2
fi

# ---------------------------------------------------------------------------
# --actual 디렉터리 존재 확인
# ---------------------------------------------------------------------------
if [[ ! -d "$ACTUAL_DIR" ]]; then
    echo "[ERROR] --actual 디렉터리가 없습니다: $ACTUAL_DIR" >&2
    exit 2
fi

# ---------------------------------------------------------------------------
# expected 서브 트리 목록
# ---------------------------------------------------------------------------
EXPECTED_SUBDIRS=("learn/expected" "project/expected" "analyze/expected")

# ---------------------------------------------------------------------------
# diff 실행
# ---------------------------------------------------------------------------
DIFF_FOUND=0

for expected_rel in "${EXPECTED_SUBDIRS[@]}"; do
    expected_dir="$SCRIPT_DIR/$expected_rel"
    actual_subdir="$ACTUAL_DIR/$expected_rel"

    if [[ ! -d "$expected_dir" ]]; then
        echo "[SKIP] expected/$expected_rel 없음 (캡처 미완료)"
        continue
    fi

    if [[ ! -d "$actual_subdir" ]]; then
        echo "[DIFF] actual/$expected_rel 없음 — 재실행 결과 디렉터리에 해당 서브 트리가 없습니다"
        DIFF_FOUND=1
        continue
    fi

    echo "[INFO] diff: $expected_rel"

    # diff -ru: 재귀 비교, unified format
    if ! diff -ru "$expected_dir" "$actual_subdir" > /dev/null 2>&1; then
        echo "[DIFF] 변경 감지: $expected_rel"
        diff -ru "$expected_dir" "$actual_subdir" || true
        DIFF_FOUND=1
    else
        echo "[OK]   일치: $expected_rel"
    fi
done

# ---------------------------------------------------------------------------
# 결과
# ---------------------------------------------------------------------------
if [[ "$DIFF_FOUND" -eq 0 ]]; then
    echo ""
    echo "[OK] 회귀 없음 — 모든 expected 와 actual 일치"
    exit 0
else
    echo ""
    echo "[FAIL] diff 발견 — 회귀 감지"
    exit 1
fi
