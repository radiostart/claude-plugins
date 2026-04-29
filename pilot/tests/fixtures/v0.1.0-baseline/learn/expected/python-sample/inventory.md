# python-sample — Inventory

> Phase 2 결과. config.md `## learn 언어 패턴` 의 Python 행 사용.
> 생성: `/pilot:learn _input/python-sample/main.py` (v0.2.0, migration accepted)

## 의존성 추적

추적 패턴: `from {module} import {X}` · `import {module}` (config.md Python 행)

| 파일 | 의존 파일 | 추출 패턴 |
| ---- | --------- | --------- |
| `main.py` | `routes.py` | `from routes import register_routes` (main.py:7) |
| `routes.py` | `models/user.py` | `from models.user import User` (routes.py:4) |
| `routes.py` | `models/order.py` | `from models.order import Order, OrderStatus` (routes.py:5) |
| `routes.py` | `services/auth.py` | `from services.auth import AuthService` (routes.py:6) |
| `routes.py` | `services/checkout.py` | `from services.checkout import CheckoutService` (routes.py:7) |
| `services/checkout.py` | `models/order.py` | `from models.order import Order, OrderItem, OrderStatus` (checkout.py:4) |
| `services/checkout.py` | `services/auth.py` | `from services.auth import AuthService` (checkout.py:5) |
| `services/auth.py` | `models/user.py` | `from models.user import User` (auth.py:4) |

## 역할 분류

분류 패턴: config.md `## learn 언어 패턴` › `### 역할 분류` 표 (Python 패턴)

| 파일 | 역할 | 근거 패턴 |
| ---- | ---- | --------- |
| `routes.py` | routes | 함수에 `@app.get`·`@app.post` decorator 포함 |
| `services/auth.py` | services | `app/services/**` 패턴·`AuthService` 클래스명 |
| `services/checkout.py` | services | `app/services/**` 패턴·`CheckoutService` 클래스명 |
| `models/user.py` | models | `app/models/**` 패턴·dataclass |
| `models/order.py` | models | `app/models/**` 패턴·dataclass·Enum |
| `helpers.py` | helpers | `util/lib` 폴더 패턴·`helpers` 파일명 |
| `main.py` | other | 진입점 — routes·services·models 어느 것도 아님 |

## 필터 제외 목록

| 파일 | 제외 사유 |
| ---- | --------- |
| `services/__init__.py` | `.gitignore` 의 `*/__init__.py` 패턴 매칭 |
| `docs/sample-spec.md` | `.md` 파일 — 코드 의존성 추적 대상 아님 |

## 상태 enum

`models/order.py:OrderStatus` (order.py:11)

| 값 | 의미 |
| -- | ---- |
| `PENDING` | 주문 생성 직후 |
| `PAID` | 결제 완료 |
| `SHIPPED` | 배송 중 |
| `CANCELLED` | 취소됨 |

## 주요 비즈니스 규칙

- 결제: `order.status == PENDING` 이 아니면 `ValueError` (checkout.py:17)
- 취소: `status == SHIPPED` 면 취소 불가 `ValueError` (checkout.py:24)
- 취소: `status == CANCELLED` 면 중복 취소 불가 `ValueError` (checkout.py:26)
