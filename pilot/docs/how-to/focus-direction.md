# Focus 기능으로 방향 조정

!!! info "한 줄 요약"
    메인 대화에서 내린 지시나 의사결정 사항(예: "소프트 딜리트는 제외합시다", "Goal 5 먼저 구현")을 다음 subagent 호출(`@pilot-planner`, `@pilot-planner-critic`, `@pilot-generator`, `@pilot-evaluator`) 시에 명시적으로 전달합니다. 메인 대화와 subagent 간의 맥락 단절을 `.focus.md` 파일을 매개로 해소하는 기능입니다.

## 전제 조건

- 활성화된 project 또는 issue가 존재해야 합니다. (focus는 issue 모드에서도 계속 동작하는 예외 스킬입니다)
- 다음 에이전트 실행에 반영해야 할 *비교적 짧고 구체적인* 사용자의 추가 지시가 존재해야 합니다. (지시가 너무 방대하거나 영구적인 요구사항인 경우, `features/NN-*.md` 나 `project.md` 에 기록하여 SSOT로 관리하는 것이 더 적절합니다)

## 작업 절차

### 1. 지시사항 기록

```bash
/pilot:focus 소프트 딜리트는 빼자. 물리 삭제로 가자.
```

이 명령을 실행하면 다음 작업이 수행됩니다:

- 기존에 존재하던 `.focus.md` 파일은 `.focus.history/{timestamp}.md` 경로로 아카이브됩니다.
- 새로운 지시 내용이 `STATE.md` 진행중 행의 mode에 따라 분기 기록됩니다 — project 활성이면 `workspace/projects/{PROJECT}/.focus.md`, issue 활성이면 `workspace/issues/{이슈명}/.focus.md`. (orchestrate-load 가 같은 `work_mode` 기준으로 읽으므로 두 경로는 반드시 일치해야 합니다)
- 단, 이슈명 없는 bare issue 행(`| issue | - |`)은 기록처가 없어 거부됩니다 — `/pilot:issue {이슈명}` 으로 재진입해야 합니다.

### 2. 다음 subagent 호출

```
@pilot-planner
```

(또는 `@pilot-planner-critic`, `@pilot-generator`, `@pilot-evaluator` 중 필요한 에이전트 호출)

호출 시 각 에이전트 wrapper의 `orchestrate-load.py` 가 `.focus.md` 파일의 존재를 감지하고, 해당 내용을 분석하여 호출 컨텍스트의 *hints* 정보로 주입합니다. **해당 호출 실행에 한하여** 해당 지시사항이 반영됩니다. 파일 자체는 삭제되지 않고 유지되므로, 여러 phase에 걸쳐 유효하게 작동할 수 있습니다.

### 3. 반영 완료 후 해제

planner → critic → generator → evaluator cycle이 모두 완료되어 등록한 지시사항이 더 이상 필요치 않다면 focus 설정을 초기화합니다:

```bash
/pilot:focus --clear
```

`.focus.md` 파일이 `.focus.history/` 경로로 아카이브되고 활성화 상태였던 focus 가 해제됩니다.

(동일하게 신규 focus 내용을 작성하여 실행하면 기존 focus 내용을 *덮어쓰기* 할 수 있습니다)

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:focus`](../reference/skills/focus.md)
- :material-tools: How-to: critic 피드백 검토 후 다음 planner 재호출 시 "C1, C3 피드백만 반영하라"와 같이 지시할 때 유용하게 조합하여 활용할 수 있습니다 — [Critic 활용](critic-review.md) 가이드 참고.
- :material-lightbulb-on: Explanation: focus를 통해 해결하고자 하는 메인 대화 단절 이슈의 상세 배경은 [에이전트 시스템 — 역할 분리](../explanation/index.md)에서 다룹니다.
