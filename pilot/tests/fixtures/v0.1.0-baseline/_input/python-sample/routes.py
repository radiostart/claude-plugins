"""HTTP 라우트 정의."""

from models.user import User
from models.order import Order, OrderStatus
from services.auth import AuthService
from services.checkout import CheckoutService

auth_svc = AuthService()
checkout_svc = CheckoutService()


def register_routes(app):
    """FastAPI app 에 라우트를 등록한다."""

    @app.get("/users/{user_id}")
    def get_user(user_id: int):
        """사용자 조회."""
        return auth_svc.get_user(user_id)

    @app.post("/users/login")
    def login(username: str, password: str):
        """로그인 — 토큰 반환."""
        return auth_svc.login(username, password)

    @app.post("/orders")
    def create_order(user_id: int):
        """주문 생성."""
        return checkout_svc.create_order(user_id)

    @app.get("/orders/{order_id}")
    def get_order(order_id: int):
        """주문 조회."""
        return checkout_svc.get_order(order_id)

    @app.post("/orders/{order_id}/pay")
    def pay_order(order_id: int):
        """결제 처리 — PENDING → PAID."""
        return checkout_svc.pay(order_id)

    @app.post("/orders/{order_id}/cancel")
    def cancel_order(order_id: int):
        """주문 취소 — PENDING/PAID → CANCELLED."""
        return checkout_svc.cancel(order_id)
