"""User 도메인 모델."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    """사용자 엔티티."""

    id: int
    username: str
    email: str
    is_active: bool = True
    role: str = "customer"  # customer | admin


@dataclass
class UserProfile:
    """사용자 프로필 (User 1:1)."""

    user_id: int
    display_name: Optional[str] = None
    bio: Optional[str] = None
