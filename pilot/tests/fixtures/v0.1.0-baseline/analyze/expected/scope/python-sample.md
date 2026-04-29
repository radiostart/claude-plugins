# python-sample — scope

> 생성: `/pilot:analyze` on `docs/sample-spec.md` (v0.2.0)
> 도메인: python-sample
> 진입 파일: `workspace/context/python-sample/index.md`

## Routes

| 엔드포인트 | Method | 목적 |
| ---------- | ------ | ---- |
| `/orders` | POST | 주문 생성 (routes.py:20) |
| `/orders/{order_id}` | GET | 주문 조회 (routes.py:25) |
| `/orders/{order_id}/pay` | POST | 결제 처리 — PENDING → PAID (routes.py:30) |
| `/orders/{order_id}/cancel` | POST | 주문 취소 — PENDING/PAID → CANCELLED (routes.py:35) |
| `/users/{user_id}` | GET | 사용자 조회 (routes.py:10) |
| `/users/login` | POST | 로그인 — 토큰 반환 (routes.py:15) |

## Models

| Class | DB | 목적 |
| ----- | -- | ---- |
| `Order` | orders | 주문 엔티티 — id·user_id·items·status (models/order.py:27) |
| `OrderItem` | order_items | 주문 항목 — product_id·quantity·unit_price (models/order.py:18) |
| `OrderStatus` | — | 주문 상태 enum: PENDING·PAID·SHIPPED·CANCELLED (models/order.py:11) |
| `User` | users | 사용자 엔티티 — id·username·email·role (models/user.py:9) |
| `UserProfile` | user_profiles | 사용자 프로필 1:1 (models/user.py:20) |

## Services

| Class | 파일 | 목적 |
| ----- | ---- | ---- |
| `CheckoutService` | `services/checkout.py` | 주문 생성·결제·취소 처리 |
| `AuthService` | `services/auth.py` | 사용자 인증·토큰 검증·조회 |
