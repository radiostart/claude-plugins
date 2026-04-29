# python-sample-demo

> **Orchestrator** — 프로젝트 전체 흐름을 조율한다.
> 구체적 구현 지식은 `prompts/` 의 에이전트 컨텍스트 파일을 참조한다.
>
> **이 파일은 스캐폴딩 템플릿이다.** `/pilot:project` 가 신규 프로젝트 생성 시 그대로 복사한다.
> `{프로젝트명}` 토큰만 실제 프로젝트명으로 치환하고, 본문의 `{…}` 플레이스홀더는 사용자 또는 `/pilot:analyze` 가 채운다.

## 개요

{프로젝트 목적과 배경을 1~2문장으로}

## 제한사항

- {구현 제약 사항 — 예: 특정 DB 단일 조회, 외부 API 호출 금지, 상태값 전환 규칙 등}

## 목표

- [ ] 주문 생성 기능 -> [상세](features/01-order-create.md)
- [ ] 결제 처리 기능 -> [상세](features/02-payment-process.md)

> `/pilot:analyze` 실행 시 features/ 파일과 동기화되어 이 목록이 자동 갱신된다.

## 에이전트 호출 흐름

**순서를 반드시 준수한다. 이전 단계 완료 전 다음 단계로 진행하지 않는다.**

### 1. Planner — 구현 계획 수립

- **진입 조건:** 새 기능 구현 시작 시 항상 실행
- **로드:** `prompts/planner.md`
- **완료 기준:** 구현 단계별 계획이 명시적으로 확정됨 → Generator 진행

### 2. Generator — 코드 구현

- **진입 조건:** Planner 계획 확정 후
- **로드:** `prompts/generator.md` + [`coding.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/coding.md)
- **완료 기준:** 구현 완료 후 [`evals/coding.json`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/evals/coding.json) 해당 케이스 체크 통과 → Evaluator 진행

### 3. Evaluator — 검토

- **진입 조건:** Generator eval 체크 통과 후
- **로드:** `prompts/evaluator.md`
- **완료 기준:** 체크리스트 전 항목 확인 → 목표의 해당 항목 `[x]` 처리

> **TDD 모드** 활성화 시 (`/pilot:project {PROJECT} --tdd` 또는 `/pilot:tdd`) 이 섹션이 Red-Green-Refactor 흐름으로 자동 교체된다. 상세: [tdd-activation.md](${CLAUDE_PLUGIN_ROOT}/skills/context/modes/tdd-activation.md).

## 관련 파일

> H3 + 표는 `/pilot:project` 가 신규 폴더 생성 시 1 회 가공한다 (`workspace/context/config.md` 의 `## scope 카테고리` 의 `project.md 대상 H3` 컬럼 따라 H3 + 빈 표 생성). 표 본문은 `/pilot:analyze` 5-2 또는 `/pilot:create-feature` 가 매번 갱신한다. 사용자 수동 추가 H3 는 양쪽 모두 보존, 삭제는 복구하지 않는다.

### Endpoints

| 엔드포인트 | Method | 목적 |
| ---------- | ------ | ---- |
| `/orders` | POST | 주문 생성 |
| `/orders/{order_id}` | GET | 주문 조회 |
| `/orders/{order_id}/pay` | POST | 결제 처리 — PENDING → PAID |
| `/orders/{order_id}/cancel` | POST | 주문 취소 — PENDING/PAID → CANCELLED |
| `/users/{user_id}` | GET | 사용자 조회 |
| `/users/login` | POST | 로그인 — 토큰 반환 |

### Models

| Class | DB | 목적 |
| ----- | -- | ---- |
| `Order` | orders | 주문 엔티티 — id·user_id·items·status |
| `OrderItem` | order_items | 주문 항목 — product_id·quantity·unit_price |
| `OrderStatus` | — | 주문 상태 enum: PENDING·PAID·SHIPPED·CANCELLED |
| `User` | users | 사용자 엔티티 — id·username·email·role |
| `UserProfile` | user_profiles | 사용자 프로필 1:1 |

### Services

| Class | 파일 | 목적 |
| ----- | ---- | ---- |
| `CheckoutService` | `services/checkout.py` | 주문 생성·결제·취소 처리 |
| `AuthService` | `services/auth.py` | 사용자 인증·토큰 검증·조회 |

## 에이전트 간 전달사항
