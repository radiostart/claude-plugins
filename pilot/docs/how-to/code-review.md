# 코드 리뷰 (PR 전)

!!! info "한 줄 요약"
    PR 올리기 전에 작성한 코드(git diff)를 `@pilot-code-review` 가 품질 관점에서 검토하고, 결함마다 *어디서부터 고칠지* 라우팅을 제시한다. 언어별 리뷰 룰은 워크스페이스에 직접 둔다.

## `@pilot-code-review` 란

planner → critic → generator → evaluator 사이클과 **별개의 독립 에이전트** 다. orchestrate-load 를 쓰지 않고, 호출자가 준 변경 범위를 그대로 검토한다.

- **본다:** git diff (uncommitted 우선, 없으면 현재 브랜치 커밋).
- **검토 기준:** 플러그인 baseline 루브릭 + 언어별 룰 (`context/review/{lang}.md`).
- **출력:** `CODE REVIEW REPORT` — 결함별 severity·`file:line`·개선안·재진입 라우팅. **코드는 수정하지 않는다.**

다른 검토와의 구분:

| 검토 | 대상 | 시점 |
|---|---|---|
| `@pilot-planner-critic` | 작성된 *계획* (`plan.md`) | generator 전 |
| **`@pilot-code-review`** | 작성된 *코드* (`git diff`) | PR 올리기 전 |
| `@pilot-evaluator` | 요구사항·게이트 *판정* | 사이클의 일부 |
| 공식 `/code-review` | GitHub PR | PR 생성 *후* |

## 전제

- 리뷰할 변경분이 있다 (uncommitted 또는 현재 브랜치 커밋).

## 절차

### 1. 리뷰 실행

```
/pilot:review
```

`@pilot-code-review` 를 호출한다. 대상 범위:

- 인자 없음 → 변경분 전체 (uncommitted + 현재 브랜치 커밋)
- 경로 (예: `/pilot:review app/services/`) → 그 경로만
- 커밋 범위 (예: `/pilot:review HEAD~3..HEAD`) → 그 범위

`CODE REVIEW REPORT` 가 출력된다 — 결함마다 `blocking`·`suggestion`·`nit` severity, `file:line`, 개선안, 재진입 라우팅(`feature`·`planner`·`generator`·`local`).

### 2. 언어별 리뷰 룰 설정 (한 번)

`workspace/context/review/{lang}.md` 가 있는 언어는 *그 룰 + baseline*, 없는 언어는 *baseline 만* 적용된다. 팀 룰을 추가하려면:

```
/pilot:code-review-init python
```

3 가지 시작 전략 중 택 1:

- **예시 복사** — 플러그인 사전 작성 예시를 가져온다. 사용 프레임워크를 묻고 해당 섹션만 남긴다.
- **빈 템플릿** — 형식만 있는 골격. `관용구·패턴`·`자주 나오는 결함` 섹션을 직접 채운다.
- **AI draft** — 코드베이스를 훑어 컨벤션·안티패턴을 추출해 초안 생성. *추측 기반이라 검토·편집 필수.*

생성 후 `workspace/context/review/{lang}.md` 를 열어 팀 컨벤션에 맞게 편집한다.

!!! tip "lint 자동 실행"
    `review/{lang}.md` 상단에 `lint: {명령}` 줄을 두면, 리뷰 시 그 언어 변경 파일에 lint 를 한 번 실행해 결과를 findings 에 반영한다. `lint:` 줄이 없으면 실행하지 않는다.

### 3. finding 처리 경로 받기

```
/pilot:fix-review
```

`CODE REVIEW REPORT` 의 finding 을 5 경로로 분류해 추천한다 (추천만 — 자동 실행 안 함):

| 경로 | 언제 | 다음 |
|---|---|---|
| `trivial` | 단일 파일·기계적 수정 | 직접 Edit → `/pilot:commit` |
| `one-shot` | 단일 함수·로직 변경 | `@pilot-generator` 1 회 |
| `full-cycle` | 다중 파일·시그니처 변경 | `@pilot-planner` 정식 사이클 |
| `new-feature` | 분리돼야 할 별도 기능 | `/pilot:create-feature` |
| `dismiss` | 의도된 결정·룰 보강 | 사유 기록 / `review/{lang}.md` 보강 |

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:review`](../reference/skills/review.md) · [`/pilot:code-review-init`](../reference/skills/code-review-init.md) · [`/pilot:fix-review`](../reference/skills/fix-review.md)
- :material-lightbulb-on: Explanation: [에이전트 흐름](../explanation/agent-flow.md) — critic 과 code-review 의 책임 경계.
- :material-shield-alert: How-to: [Critic 활용](critic-review.md) — *계획* 단계의 adversarial 검토.
