"""Order 도메인 모델."""

from dataclasses import dataclass, field
from typing import List
from enum import Enum


class OrderStatus(Enum):
    """주문 상태값."""

    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


@dataclass
class OrderItem:
    """주문 항목."""

    product_id: int
    product_name: str
    quantity: int
    unit_price: float

    @property
    def subtotal(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class Order:
    """주문 엔티티."""

    id: int
    user_id: int
    items: List[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PENDING

    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.items)
