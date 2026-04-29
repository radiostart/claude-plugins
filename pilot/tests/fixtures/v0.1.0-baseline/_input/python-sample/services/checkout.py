"""결제·주문 처리 서비스."""

from models.order import Order, OrderItem, OrderStatus
from services.auth import AuthService

auth_svc = AuthService()


class CheckoutService:
    """주문 생성·결제·취소 담당."""

    def create_order(self, user_id: int) -> Order:
        """빈 주문 생성. user_id 유효성은 auth_svc 에 위임."""
        user = auth_svc.get_user(user_id)
        if user is None:
            raise ValueError(f"user {user_id} not found")
        # fixture — 실제 DB 저장 없음
        return Order(id=1, user_id=user_id)

    def get_order(self, order_id: int) -> Order:
        """주문 조회. 미존재 시 None 반환."""
        # fixture — 실제 DB 접근 없음
        return Order(id=order_id, user_id=0)

    def pay(self, order_id: int) -> Order:
        """결제 처리 — PENDING → PAID. 이미 PAID/CANCELLED 면 ValueError."""
        order = self.get_order(order_id)
        if order.status != OrderStatus.PENDING:
            raise ValueError(f"order {order_id} is not PENDING (status={order.status})")
        order.status = OrderStatus.PAID
        return order

    def cancel(self, order_id: int) -> Order:
        """주문 취소 — PENDING 또는 PAID → CANCELLED. SHIPPED 는 취소 불가."""
        order = self.get_order(order_id)
        if order.status == OrderStatus.SHIPPED:
            raise ValueError(f"order {order_id} is already SHIPPED — cannot cancel")
        if order.status == OrderStatus.CANCELLED:
            raise ValueError(f"order {order_id} is already CANCELLED")
        order.status = OrderStatus.CANCELLED
        return order
