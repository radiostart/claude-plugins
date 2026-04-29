"""인증 서비스."""

from models.user import User


class AuthService:
    """사용자 인증·조회 담당."""

    def get_user(self, user_id: int) -> User:
        """ID 로 사용자 조회. 미존재 시 None 반환."""
        # fixture — 실제 DB 접근 없음
        return User(id=user_id, username="fixture_user", email="fixture@example.com")

    def login(self, username: str, password: str) -> dict:
        """로그인. 성공 시 {"token": str} 반환, 실패 시 {"error": str} 반환."""
        if not username or not password:
            return {"error": "username and password required"}
        # fixture — 실제 인증 없음
        return {"token": f"token_{username}"}

    def validate_token(self, token: str) -> bool:
        """토큰 유효성 검증."""
        return token.startswith("token_")
