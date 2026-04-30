"""외부 도메인 (secondary_domain) 의 사용자 모델 스텁."""

from dataclasses import dataclass


@dataclass
class ExternalUser:
    """외부 도메인 사용자 — 스텁."""

    id: int
    email: str
    is_active: bool = True
