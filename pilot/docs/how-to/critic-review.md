# Critic 활용 — Plan adversarial 검증

!!! info "한 줄 요약"
    `@pilot-planner-critic`을 활용하여 planner가 수립한 `plan.md`를 비판적 관점에서 검증하고, `.plan.critic.md`에 결과를 기록한 뒤, planner를 재호출하여 합의 표를 작성하는 1.5-pass review flow입니다.

## 전제 조건

- planner가 최소 1회 실행되어 `features/NN-{slug}.plan.md` 파일이 이미 작성되어 있어야 합니다.
- 변경 영향 범위가 크거나 확인해야 할 전제 조건이 많은 feature 작업에 권장됩니다. 단순한(trivial) 수정 작업 시에는 사용자의 판단에 따라 critic 단계를 생략할 수 있습니다.

## 작업 절차

### 1. critic 호출

```
@pilot-planner-critic
```

planner와 동일한 context(`orchestrate-load.py`로 로드됨)를 공유하며, 상반된 관점에서 동작합니다. planner가 *설계*를 담당한다면, critic은 *반론 및 잠재적 결함 발굴*을 수행합니다. `premise`, `scope`, `edge-case`, `alternative`, `risk` 등 5가지 카테고리로 피드백을 구성하여 다음 파일에 결과를 기록합니다:

```
features/NN-{slug}.plan.critic.md
```

각 피드백에는 중요도(`severity`: `blocking`, `suggestion`, `nit`), plan 내 인용구, 그리고 개선 제안이 포함됩니다.

!!! tip "critic의 책임 경계"
    critic은 *plan이나 code를 직접 수정하지 않습니다*. 지적된 결함은 planner가 다시 호출될 때 반영되어 수정됩니다. 이러한 역할 분리를 통해 사용자가 중재자(의장) 역할을 주도적으로 수행할 수 있게 됩니다.

### 2. critic 결과 검토 후 결정

critic은 실행 후 다음 3가지 항목 위주로 보고합니다:

- 작성한 파일 경로
- `blocking`, `suggestion`, `nit` 등 피드백의 유형별 개수
- 다음 추천 단계 (`blocking >= 1`인 경우 planner 재호출 권장, `blocking`이 없는 경우 generator 호출 가능)

사용자는 `.plan.critic.md` 파일을 열어 피드백 목록을 직접 검토합니다. 필요한 경우 `/pilot:focus "C1, C3 피드백만 반영하고 C2는 무시"` 형태로 후속 지시사항을 명시하여 planner 재호출 시 반영되도록 주입합니다.

### 3. planner 재호출 (수정 라운드)

```
@pilot-planner
```

planner가 `.plan.critic.md` 파일의 존재를 감지하면 다음과 같이 처리합니다:

- 제기된 피드백 항목들을 모두 검토하여 `plan.md` 내용을 보강합니다.
- `.plan.critic.md` 파일 내 `## 합의` 표의 각 피드백 ID(`C#`) 항목에 `accepted | rejected | deferred` 상태와 간략한 조치 내역(메모)을 기록합니다 (이 합의 표를 작성하지 않거나 빈 상태로 두면 generator 단계 실행이 허용되지 않습니다).

### 4. 반복 (필요 시)

피드백이 수렴되지 않는 경우, 다음과 같이 critic → planner cycle을 다시 반복해 진행할 수 있습니다:

```
@pilot-planner-critic   # 수정된 plan.md를 바탕으로 새로운 피드백 수집 (기존 .plan.critic.md 파일이 오버라이트됩니다)
```

!!! warning "라운드가 3 회를 넘기면"
    동일한 유형의 피드백이 계속 반복된다면 plan의 구조적 결함이 아니라 *기획 명세 자체가 모호함*을 뜻합니다. critic cycle을 반복하기보다 `features/NN-{slug}.md` 파일의 사양을 명확히 보완하십시오.

### 5. generator 단계로 진행

피드백 합의 표 작성이 완료되고 해결되지 않은 blocking 이슈가 없다면:

```
@pilot-generator
```

## 다음 단계

- :material-book-open-variant: Reference: [`@pilot-planner-critic`](../reference/agents/pilot-planner-critic.md) · [Identity SSOT](../reference/identity.md)
- :material-lightbulb-on: Explanation: [에이전트 흐름 — planner ↔ critic 의 책임 분리](../explanation/index.md)
- :material-tools: How-to: critic 피드백에 대해 사용자의 명확한 반영 가이드를 전달하려면 [Focus로 방향 조정](focus-direction.md) 스킬을 함께 활용하십시오.
