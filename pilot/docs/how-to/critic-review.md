# Critic 활용 — Plan adversarial 검증

!!! info "한 줄 요약"
    `@pilot-planner-critic` 으로 planner 가 만든 `plan.md` 를 반론 시각에서 챌린지 → `.plan.critic.md` 에 결과 기록 → planner 재호출이 합의 표를 채우는 1.5-pass 흐름.

## 전제

- planner 가 한 번 실행되어 `features/NN-{slug}.plan.md` 가 이미 작성돼 있다.
- 변경 영향이 크거나 가정이 많은 feature — trivial 변경에는 critic 을 건너뛰는 게 옳다 (사용자 판단).

## 절차

### 1. critic 호출

```
@pilot-planner-critic
```

planner 와 같은 컨텍스트 (orchestrate-load) 위에서 정반대 관점으로 동작한다 — planner 가 *설계* 라면 critic 은 *반론·결함 찾기*. 5 카테고리 — `premise` · `scope` · `edge-case` · `alternative` · `risk` — 로 챌린지를 만들고:

```
features/NN-{slug}.plan.critic.md
```

에 기록한다. 각 챌린지에 `severity` (`blocking` · `suggestion` · `nit`) 와 plan 인용·제안이 붙는다.

!!! tip "critic 의 책임 경계"
    critic 은 *plan/코드를 직접 수정하지 않는다*. 결함은 planner 가 재호출되어 수정한다. 이 분리가 사용자가 *중간에 의장 역할* 을 하게 만드는 핵심.

### 2. critic 결과 검토 후 결정

critic 출력은 3 가지만 보고한다:

- 작성한 파일 경로
- blocking · suggestion · nit 개수
- 다음 권장 (`blocking ≥ 1` 이면 planner 재호출 권장, 0 이면 generator 진행 가능)

사용자가 `.plan.critic.md` 를 열어 챌린지를 검토하고 — 또는 `/pilot:focus "C1·C3 만 반영, C2 무시"` 로 다음 호출에 명시 지시.

### 3. planner 재호출 (수정 라운드)

```
@pilot-planner
```

planner 가 `.plan.critic.md` 가 이미 존재함을 감지하면:

- 챌린지 항목을 모두 검토하고 plan.md 수정.
- `.plan.critic.md` 의 `## 합의` 표를 각 `C#` 별로 `accepted | rejected | deferred` + 짧은 메모로 채운다 (강제 — 빈 표 그대로 두면 generator 단계로 넘어가지 않는다).

### 4. 반복 (필요 시)

수렴이 안 되면 critic → planner 라운드를 다시 돈다:

```
@pilot-planner-critic   # 새 plan.md 에 대한 새 챌린지 — .plan.critic.md 덮어쓰기
```

!!! warning "라운드가 3 회를 넘기면"
    같은 카테고리의 챌린지가 반복된다면 plan 이 아니라 *원본 feature.md 가 모호하다* 는 신호. critic 라운드를 더 도는 대신 `features/NN-{slug}.md` 를 손보세요.

### 5. generator 로 진행

합의 표가 채워지고 blocking 이 없으면:

```
@pilot-generator
```

## 다음 단계

- :material-book-open-variant: Reference: [`@pilot-planner-critic`](../reference/agents/pilot-planner-critic.md) · [Identity SSOT](../reference/identity.md)
- :material-lightbulb-on: Explanation: [에이전트 흐름 — planner ↔ critic 의 책임 분리](../explanation/index.md)
- :material-tools: How-to: critic 챌린지에 사용자 의도가 따로 있으면 [Focus 로 방향 조정](focus-direction.md) 와 같이 쓰면 됩니다.
