# Planner — python-sample-demo

구현 대상 기능을 분석하고, Generator가 실행 가능한 단계별 계획을 수립한다.

> **⚠️ 이 파일은 `@planner` subagent 정의가 아닙니다.** 실제 subagent 는 플러그인의 [`${CLAUDE_PLUGIN_ROOT}/agents/planner.md`](${CLAUDE_PLUGIN_ROOT}/agents/planner.md) 에 등록돼 있고, wrapper 가 Read 로 **이 파일을 컨텍스트 문서로** 불러들입니다. 이 파일 편집은 다음 `@planner` 호출에 반영됩니다 (단 `<!-- [analyze-managed] -->` 섹션은 다음 `--regen-agents` 시 덮어쓰임).
>
> 스캐폴딩·analyze-managed·TDD 상세: [agents-scaffold-notes.md](${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/projects/agents-scaffold-notes.md) 참조.

<!-- [analyze-managed] -->
## 기능별 사전 확인 사항

### #01 주문 생성 기능

- `Order` 모델 생성 시 `user_id` 유효성은 `AuthService.get_user` 에 위임 (checkout.py:9)
- 주문 항목이 1 개 이상이어야 한다 (sample-spec.md 비즈니스 규칙)
- 재고 부족 시 주문 생성 불가 (sample-spec.md 비즈니스 규칙)

### #02 결제 처리 기능

- `order.status == PENDING` 이 아니면 `ValueError` (checkout.py:17) — 선제 확인 필요
- 상태 전환: PENDING → PAID 만 허용 (sample-spec.md 상태 전환표)
- 이미 PAID·CANCELLED 주문에 결제 시도 시 오류 처리 필요
