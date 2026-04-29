"""
python-sample — fixture entry point.

FIXTURE NOTE: 이 파일은 실행 불가 토이 코드입니다.
              /pilot:learn 회귀 테스트 입력용으로만 사용합니다.
"""

try:
    from fastapi import FastAPI
except ImportError:
    FastAPI = None  # 의존성 없이 import 가능하도록 guard

from routes import register_routes

app = FastAPI() if FastAPI else None


def create_app():
    """앱 팩토리 — routes 등록 후 반환."""
    if app is not None:
        register_routes(app)
    return app


if __name__ == "__main__":
    create_app()
