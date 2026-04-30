"""외부 도메인 (secondary_domain) 의 인증 서비스 스텁.

이 파일은 cross-domain detect 회귀 픽스처용으로,
`python-sample` 도메인이 `secondary_domain.AuthService` 를 참조하는
cross-domain import 시나리오를 검증하기 위해 사용한다.
"""


class AuthService:
    """외부 도메인 인증 서비스 — 스텁."""

    def verify_token(self, token: str) -> bool:
        """토큰 유효성 검사 (스텁 — 항상 True)."""
        return bool(token)

    def get_user_id(self, token: str) -> int | None:
        """토큰에서 user_id 추출 (스텁)."""
        if not token:
            return None
        return 1
