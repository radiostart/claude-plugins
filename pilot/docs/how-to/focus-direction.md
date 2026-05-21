# Focus 로 방향 조정

!!! info "한 줄 요약"
    메인 대화에서 내린 결정 (예: "소프트 딜리트는 빼자", "Goal 5 먼저") 을 다음 subagent 호출 (`@pilot-planner`·`@pilot-planner-critic`·`@pilot-generator`·`@pilot-evaluator`) 에 명시 전달. 메인 대화의 의도가 subagent 에는 보이지 않는 구조적 단절을 `.focus.md` 파일 매개로 해소한다.

## 전제

- 활성 프로젝트가 있다.
- 다음 호출에서 반영할 *비교적 짧은* 사용자 지시가 있다 (긴 요구사항이면 `features/NN-*.md` 또는 `project.md` 가 SSOT 로 더 적합).

## 절차

### 1. 지시 기록

```bash
/pilot:focus 소프트 딜리트는 빼자. 물리 삭제로 가자.
```

다음을 수행:

- 기존 `.focus.md` 가 있으면 `.focus.history/{timestamp}.md` 로 아카이브.
- 새 지시를 `workspace/projects/{PROJECT}/.focus.md` 에 저장.

### 2. 다음 subagent 호출

```
@pilot-planner
```

(또는 `@pilot-planner-critic` · `@pilot-generator` · `@pilot-evaluator` 어느 것이든)

각 wrapper 의 `orchestrate-load.py` 가 `.focus.md` 를 자동 Read 해서 호출 컨텍스트의 *hints* 로 주입한다. **본 호출에 한해** 지시에 반영. 파일은 그대로 — 한 focus 가 여러 phase 에 걸쳐 유효.

### 3. 반영 완료 후 제거

planner → critic → generator → evaluator 사이클이 끝나고 focus 가 더 이상 필요 없다면:

```bash
/pilot:focus --clear
```

`.focus.md` 가 `.focus.history/` 로 아카이브되고 활성 focus 가 해제된다.

또는 새 focus 로 *덮어쓰기* 도 가능 (위 step 1 을 다시 실행).

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:focus`](../reference/skills/focus.md)
- :material-tools: How-to: critic 결과를 검토하고 다음 planner 에 "C1·C3 만 반영" 같이 지시할 때 자주 함께 쓴다 — [Critic 활용](critic-review.md).
- :material-lightbulb-on: Explanation: focus 가 해결하는 *메인 대화 단절* 문제는 [에이전트 시스템 — 페르소나 분리](../explanation/index.md) 에서.
