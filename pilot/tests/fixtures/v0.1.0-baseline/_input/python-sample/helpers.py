"""유틸리티 헬퍼 함수 모음."""

from typing import Any, Dict, Optional


def to_dict(obj: Any) -> Dict:
    """dataclass 인스턴스를 dict 로 변환 (중첩 지원)."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_dict(v) for k, v in obj.__dict__.items()}
    if hasattr(obj, "value"):  # Enum
        return obj.value
    return obj


def paginate(items: list, page: int = 1, per_page: int = 20) -> Dict:
    """리스트를 페이지 단위로 슬라이싱."""
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "items": items[start:end],
        "page": page,
        "per_page": per_page,
        "total": len(items),
    }


def format_price(amount: float, currency: str = "KRW") -> str:
    """금액 포맷팅. 예: 12300 → '12,300 KRW'."""
    return f"{amount:,.0f} {currency}"
