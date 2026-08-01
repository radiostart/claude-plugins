# 코드 리뷰

!!! info "한 줄 요약"
    PR(Pull Request)을 생성하기 전에 작성한 코드(`git diff`)를 `@pilot-code-review` 가 품질 관점에서 검토하고, 발견된 결함마다 적절한 수정 경로(routing)를 제시합니다. 언어별 상세 리뷰 규칙(rule)은 워크스페이스 내에서 직접 관리할 수 있습니다.

## `@pilot-code-review` 란

planner → critic → generator → evaluator cycle과 **별개로 동작하는 독립적인 agent** 입니다. `orchestrate-load.py` 를 사용하지 않고, 호출 시점에 전달받은 변경 범위만을 직접 검토합니다.

- **검토 대상**: `git diff` (uncommitted 변경사항 우선 적용, 없으면 현재 branch의 commit 내역 검토)
- **검토 기준**: 플러그인 baseline 루브릭(rubric) + 언어별 규칙 문서 (`context/review/{lang}.md`)
- **출력**: `CODE REVIEW REPORT` — 각 결함의 severity(중요도), `file:line`, 개선 제안, 후속 수정 routing 제시 (코드를 직접 수정하지는 않습니다)

타 검토 단계와의 차이점:

| 검토 방식 | 검토 대상 | 실행 시점 |
|---|---|---|
| `@pilot-planner-critic` | 작성된 설계 *계획* (`plan.md`) | generator 실행 전 |
| **`@pilot-code-review`** | 작성된 *코드* (`git diff`) | PR 올리기 전 |
| `@pilot-evaluator` | 요구사항 및 게이트 충족 여부 *판정* | cycle의 마지막 검증 단계 |
| 내장 `/code-review` | 범용 정확성 검토 (로컬 diff 또는 GitHub PR) | 팀 규칙·routing이 필요 없는 리뷰 |

## 전제 조건

- 리뷰를 진행할 변경 내용이 존재해야 합니다 (uncommitted 변경사항 또는 현재 branch의 commit).

## 작업 절차

### 1. 리뷰 실행

```
/pilot:pilot-review
```

`@pilot-code-review` 를 호출합니다. 검토 대상 범위는 다음과 같이 지정할 수 있습니다:

- **인자 없음**: 전체 변경사항 검토 (uncommitted + 현재 branch의 commit)
- **특정 경로 지정** (예: `/pilot:pilot-review app/services/`): 해당 디렉터리 내의 변경사항만 검토
- **Commit 범위 지정** (예: `/pilot:pilot-review HEAD~3..HEAD`): 해당 범위 내의 변경사항 검토

실행이 완료되면 `CODE REVIEW REPORT`가 출력되며, 각 결함 항목에 `blocking`, `suggestion`, `nit` 중 하나의 severity와 함께 `file:line`, 개선안, 재진입 routing(`feature`, `planner`, `generator`, `trivial`, `new-feature`, `dismiss`)이 제공됩니다.

### 2. 언어별 리뷰 규칙(rule) 설정 (최초 1회)

`workspace/context/review/{lang}.md` 파일이 존재하는 언어는 *해당 규칙 + baseline*이 적용되며, 파일이 없는 언어는 *baseline*만 적용됩니다. 규칙을 새로 커스텀하려면 다음 명령을 실행합니다:

```
/pilot:code-review-init python
```

초기 생성 시 다음 3가지 전략 중 하나를 선택할 수 있습니다:

- **예시 복사**: 플러그인에서 제공하는 내장 템플릿을 가져옵니다. 프레임워크 선택 단계를 거쳐 필요하지 않은 섹션을 정리합니다.
- **빈 템플릿**: 뼈대만 갖춘 빈 문서로 시작합니다. `관용구/패턴`, `자주 발생하는 결함` 등의 섹션을 직접 작성합니다.
- **AI draft**: 코드베이스를 자동으로 분석하여 컨벤션 및 안티패턴을 추출한 초안을 생성합니다. *추측 기반이므로 최종 검토 및 수정이 필수적입니다.*

생성된 `workspace/context/review/{lang}.md` 파일을 열어 팀의 컨벤션과 일치하도록 세부 내용을 수정합니다.

!!! tip "lint 자동 연동"
    `review/{lang}.md` 파일 상단에 `lint: {명령어}` 형식을 지정하면, 리뷰 시 해당 언어로 변경된 파일에 대해 lint 도구를 자동 실행하여 그 검출 결과를 findings 보고서에 통합해 보여줍니다. `lint:` 설정이 없으면 이 단계는 생략됩니다.

### 3. 결함 수정

routing 및 수정 규모 분류는 `CODE REVIEW REPORT` 에 통합되어 있습니다. report 하단의 `routing` 요약 블록이 trivial 일괄 commit(직접 편집 후 `/pilot:commit`) · one-shot 묶음(`@pilot-generator` 1회 실행) · full-cycle 후보(`@pilot-planner` 부터 정식 cycle 진입) · `new-feature`(`/pilot:create-feature` 로 신규 작업 생성) · `dismiss`(판단 사유 기록 혹은 `review/{lang}.md` 파일 보강) 후보를 직접 안내하므로, 사용자는 원하는 경로를 선택해 진행하면 됩니다 (자동으로 수정이 이루어지지는 않습니다).

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:pilot-review`](../reference/skills/pilot-review.md) · [`/pilot:code-review-init`](../reference/skills/code-review-init.md)
- :material-lightbulb-on: Explanation: [에이전트 흐름](../explanation/agent-flow.md) — critic 과 code-review 의 역할 및 검토 범위 경계.
- :material-shield-alert: How-to: [Critic 활용](critic-review.md) — *계획(Plan)* 수립 단계에서의 adversarial 검토 방법.
