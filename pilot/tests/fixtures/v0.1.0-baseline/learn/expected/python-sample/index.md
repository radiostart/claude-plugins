# python-sample — 도메인 요약

> **진입 파일**: `_input/python-sample/main.py`
> **추적 깊이**: 2
> **발견 파일**: 7 개 (routes 1 · services 2 · models 2 · helpers 1 · 기타 1)
> **생성**: `/pilot:learn` v0.2.0

Python FastAPI 기반 주문·사용자 도메인. `main.py` 에서 `register_routes` 를 호출해 6 개 HTTP 엔드포인트를 등록한다. 사용자 인증 (`AuthService`)·주문 결제 (`CheckoutService`) 두 서비스가 핵심 비즈니스 로직을 담당한다.

## 파일 목록

| 파일 | 역할 | 라인 |
| ---- | ---- | ---- |
| `main.py` | 진입점 — FastAPI app 팩토리 | ~20 |
| `routes.py` | HTTP 라우트 6 개 등록 | ~40 |
| `models/user.py` | User·UserProfile dataclass | ~20 |
| `models/order.py` | Order·OrderItem·OrderStatus (Enum) | ~35 |
| `services/auth.py` | AuthService — 인증·조회 | ~20 |
| `services/checkout.py` | CheckoutService — 주문·결제·취소 | ~30 |
| `helpers.py` | to_dict·paginate·format_price | ~25 |

## 상세 파일

- [inventory.md](inventory.md) — Phase 2 의존성 + 역할 분류
