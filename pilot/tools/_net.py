"""HTTPS 호출용 공용 헬퍼.

stdlib `urllib` 로 HTTPS 를 호출하는 툴(jira·confluence·slack-notify)이
인터프리터 빌드에 따라 CA 번들을 못 찾아 인증서 검증에 실패하는 문제를
공통으로 해소한다 (특히 python.org macOS 프레임워크 빌드).
"""

from __future__ import annotations

import os
import ssl


def ssl_context() -> ssl.SSLContext:
    """HTTPS 검증용 SSL 컨텍스트를 우선순위에 따라 생성한다.

    우선순위:
      1. `SSL_CERT_FILE` / `SSL_CERT_DIR` 환경변수가 있으면 stdlib 기본 컨텍스트.
         (커스텀 CA·프록시 환경을 존중 — 사용자가 명시 지정.)
      2. 없으면 `certifi` 번들을 사용. `import certifi` 는 실행 중인 인터프리터의
         certifi 를 가리키므로 빌드별 CA 미발견 문제를 제거한다.
      3. certifi 도 없으면 stdlib 기본 (현행 동작 보존 — regression 없음).

    이 헬퍼 덕분에 매 호출마다 `SSL_CERT_FILE=...` 을 인라인으로 줄 필요가 없다.
    """
    if os.environ.get("SSL_CERT_FILE") or os.environ.get("SSL_CERT_DIR"):
        return ssl.create_default_context()
    try:
        import certifi  # soft dependency — 없으면 stdlib 기본으로 fallback

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def http_timeout(env_key: str, default: float) -> float:
    """환경변수 우선 HTTP 타임아웃(초).

    프록시·느린 네트워크에서 기본값이 짧을 때 사용자가 env 로
    오버라이드한다 (예: ATLASSIAN_HTTP_TIMEOUT, SLACK_HTTP_TIMEOUT).
    비수치·0 이하 값은 default 로 폴백 — 잘못된 설정으로 호출이
    무한 대기하거나 즉시 실패하지 않게.
    """
    raw = os.environ.get(env_key)
    if not raw:
        return default
    try:
        val = float(raw)
    except ValueError:
        return default
    return val if val > 0 else default
