#!/usr/bin/env python3
"""
pilot init_detect — `/pilot:init` wizard 자동 감지 도구.

저장소 CWD 를 스캔하여 주 언어·scope 카테고리·Ignore baseline 을
자동으로 추정한다. Python 표준 라이브러리만 사용 (외부 의존성 0).

Usage (CLI):
    python3 pilot/tools/init_detect.py [CWD] [--max-files N]

Usage (import):
    from pilot.tools.init_detect import detect_languages, detect_scope_candidates, IGNORE_BASELINE
"""

import argparse
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Tuple

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

# Ignore 강제 주입 baseline (spec #13 line 28)
IGNORE_BASELINE: list = [
    ".git/",
    "node_modules/",
    "__pycache__/",
    "vendor/",
    "dist/",
    "build/",
    ".next/",
    "target/",
    "*.pyc",
    "*.lock",
]

# 확장자 → 언어 매핑 (features/01 의 5 default 언어 + java)
LANG_EXT_MAP: dict = {
    ".rb": "ruby",
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".java": "java",
}

# 폴더명 → scope 카테고리 매핑 (features/02 의 default 매핑)
SCOPE_FOLDER_MAP: dict = {
    "controllers": "Endpoints",
    "routes": "Endpoints",
    "models": "Models",
    "entities": "Models",
    "services": "Services",
    "workers": "Services",
    "jobs": "Services",
}

# Ignore baseline 에 포함된 패턴을 walk 시 제외할 폴더명 목록
_IGNORE_DIR_NAMES: set = {
    ".git",
    "node_modules",
    "__pycache__",
    "vendor",
    "dist",
    "build",
    ".next",
    "target",
}


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _should_ignore_dir(dir_name: str) -> bool:
    """폴더명이 IGNORE_BASELINE 에 포함된 항목이면 True."""
    return dir_name in _IGNORE_DIR_NAMES or dir_name.startswith(".")


# ---------------------------------------------------------------------------
# 공개 함수
# ---------------------------------------------------------------------------

def detect_languages(
    cwd: Path,
    max_files: int = 50000,
) -> Tuple[list, list]:
    """저장소 확장자 빈도를 집계해 주 언어 목록을 반환한다.

    Args:
        cwd: 스캔 대상 루트 디렉터리.
        max_files: 샘플링 상한. 초과 시 상위 N개만 집계하고 INFO 메시지 추가.

    Returns:
        (languages, info_messages) 튜플.
        - languages: LANG_EXT_MAP 에 매핑된 상위 3개 언어 목록 (중복 제거).
          매핑 결과 0건 → 빈 리스트 반환 (spec line 21: default fallback 은 호출자 책임).
        - info_messages: 비매핑 확장자 및 샘플링 알림 문자열 목록.
    """
    ext_counter: Counter = Counter()
    info_messages: list = []
    file_count = 0
    sampled = False

    for root, dirs, files in os.walk(cwd):
        # Ignore 디렉터리 제외 (in-place 수정으로 walk 차단)
        dirs[:] = [d for d in dirs if not _should_ignore_dir(d)]

        for fname in files:
            if file_count >= max_files:
                sampled = True
                break
            ext = Path(fname).suffix.lower()
            if ext:
                ext_counter[ext] += 1
            file_count += 1

        if sampled:
            break

    if sampled:
        info_messages.append(
            f"INFO: 파일 수가 {max_files}개를 초과하여 샘플링 적용 ({max_files}파일)"
        )

    # 상위 3 확장자 → 언어 매핑
    top_exts = [ext for ext, _ in ext_counter.most_common()]
    seen_langs: list = []
    unmapped_exts: list = []

    for ext in top_exts:
        if len(seen_langs) >= 3:
            break
        if ext in LANG_EXT_MAP:
            lang = LANG_EXT_MAP[ext]
            if lang not in seen_langs:
                seen_langs.append(lang)
        else:
            unmapped_exts.append(ext)

    if unmapped_exts:
        info_messages.append(
            f"INFO: 매핑되지 않은 확장자 (결과에서 제외): {', '.join(unmapped_exts)}"
        )

    return seen_langs, info_messages


def detect_scope_candidates(cwd: Path) -> Tuple[dict, list]:
    """depth ≤ 2 폴더명을 집계해 scope 후보를 반환한다.

    Args:
        cwd: 스캔 대상 루트 디렉터리.

    Returns:
        (scope_map, info_messages) 튜플.
        - scope_map: {폴더명: scope 카테고리} — SCOPE_FOLDER_MAP 에 매핑된 항목만.
          빈도 ≥ 1 (= 존재 시) 이고 영문 소문자 폴더명 조건 (Q1 결정).
        - info_messages: 매핑 안 되는 폴더명 안내 문자열 목록.
    """
    folder_counter: Counter = Counter()

    # depth ≤ 2 탐색 (cwd 직속 하위 + 그 하위)
    try:
        depth0_entries = list(cwd.iterdir())
    except PermissionError:
        return {}, ["INFO: CWD 읽기 권한 없음"]

    for entry in depth0_entries:
        if not entry.is_dir():
            continue
        if _should_ignore_dir(entry.name):
            continue
        # depth 1
        folder_counter[entry.name] += 1
        # depth 2
        try:
            for sub in entry.iterdir():
                if sub.is_dir() and not _should_ignore_dir(sub.name):
                    folder_counter[sub.name] += 1
        except PermissionError:
            pass

    scope_map: dict = {}
    unmapped_folders: list = []
    info_messages: list = []

    for folder_name, count in folder_counter.items():
        # 영문 소문자 확인
        if not folder_name.islower() or not folder_name.isascii():
            continue
        # 빈도 ≥ 1 (Q1: 존재 시 매핑)
        if count < 1:
            continue
        if folder_name in SCOPE_FOLDER_MAP:
            scope_map[folder_name] = SCOPE_FOLDER_MAP[folder_name]
        else:
            unmapped_folders.append(folder_name)

    if unmapped_folders:
        info_messages.append(
            f"INFO: 매핑되지 않은 폴더 (scope 표에 미반영, 수동 추가 가능): "
            f"{', '.join(sorted(unmapped_folders))}"
        )

    return scope_map, info_messages


def print_detection_summary(
    languages: list,
    info_lang: list,
    scope_map: dict,
    info_scope: list,
) -> None:
    """CLI 실행 시 감지 결과를 stdout 에 출력한다."""
    print("=== init_detect 결과 ===")
    print()
    print(f"언어 감지: {len(languages)}개")
    if languages:
        for lang in languages:
            print(f"  - {lang}")
    else:
        print("  (없음 — default 5행 주입 권장)")
    for msg in info_lang:
        print(f"  {msg}")

    print()
    print(f"scope 후보: {len(scope_map)}개")
    if scope_map:
        for folder, cat in scope_map.items():
            print(f"  - {folder} -> {cat}")
    else:
        print("  (없음 — features/02 default 매핑 주입 권장)")
    for msg in info_scope:
        print(f"  {msg}")

    print()
    print(f"Ignore baseline: {len(IGNORE_BASELINE)}개")
    for pattern in IGNORE_BASELINE:
        print(f"  - {pattern}")


# ---------------------------------------------------------------------------
# CLI 진입점
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="pilot init wizard — 저장소 언어·scope 자동 감지"
    )
    parser.add_argument(
        "cwd",
        nargs="?",
        default=".",
        help="스캔 대상 디렉터리 (기본값: 현재 디렉터리)",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=50000,
        dest="max_files",
        help="파일 수 상한 (기본값: 50000)",
    )
    args = parser.parse_args()

    cwd = Path(args.cwd).resolve()
    if not cwd.is_dir():
        print(f"[ERROR] 디렉터리가 없습니다: {cwd}", file=sys.stderr)
        sys.exit(1)

    langs, info_lang = detect_languages(cwd, max_files=args.max_files)
    scope_map, info_scope = detect_scope_candidates(cwd)

    print_detection_summary(langs, info_lang, scope_map, info_scope)
