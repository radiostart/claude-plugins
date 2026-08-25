"""Shared credential helpers for Atlassian tools (confluence.py / jira.py).

공용 책임:
  - resolve_credential  : 도구별 env 키 우선, 부재 시 ATLASSIAN_* fallback.
  - load_dotenv         : .env 파일 파싱 — partition("=")·따옴표 strip·# skip.
                          credential 로드 시 INFO 메시지를 stderr 에 출력 (메시지 포맷은 호출자 제공).

doctor 패키지에 의존하지 않는다 — credential 처리는 doctor-independent.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable


def resolve_credential(tool_key: str, atlassian_key: str) -> str:
    """도구별 키 우선, 부재(또는 공백만) 시 통합 Atlassian 키 fallback.

    두 키 모두 비어있으면 빈 문자열을 반환 — 누락 판정은 호출자가 수행.
    """
    val = os.environ.get(tool_key, "").strip()
    if val:
        return val
    return os.environ.get(atlassian_key, "").strip()


def load_dotenv(
    candidates: list[Path],
    credential_prefixes: tuple[str, ...],
    info_message_fn: Callable[[Path, str], str],
) -> None:
    """candidates 경로 목록에서 KEY=VALUE 를 읽어 os.environ 에 주입한다.

    Args:
        candidates: 시도할 .env 경로 목록 (존재하는 첫 번째부터 파싱).
        credential_prefixes: INFO 알림 대상 키 prefix 튜플.
            예: ("CONFLUENCE_", "ATLASSIAN_") 또는 ("JIRA_", "ATLASSIAN_").
        info_message_fn: credential 키 로드 시 stderr 에 출력할 메시지를 반환하는 함수.
            signature: (src: Path, keys: str) -> str

    정책:
      - 이미 os.environ 에 존재하는 키는 덮어쓰지 않는다 (export 우선).
      - 값의 양쪽 따옴표(단/쌍)는 strip 한다.
      - 빈 라인·#로 시작하는 주석·= 없는 라인은 무시한다.
      - OSError(파일 읽기 실패)는 조용히 skip.
    """
    loaded_credentials: list[tuple[str, Path]] = []
    for path in candidates:
        if not path.exists():
            continue
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
                    if any(key.startswith(pfx) for pfx in credential_prefixes):
                        loaded_credentials.append((key, path))
        except OSError:
            continue

    if loaded_credentials:
        keys = ", ".join(k for k, _ in loaded_credentials)
        src = loaded_credentials[0][1]
        print(info_message_fn(src, keys), file=sys.stderr)
