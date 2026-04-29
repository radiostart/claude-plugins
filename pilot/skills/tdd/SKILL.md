---
name: tdd
description: >-
  이미 구현된 코드가 있는 기존 프로젝트에 TDD(Red-Green-Refactor) 모드를
  사후 적용한다. project.md의 제한사항·에이전트 호출 흐름과 prompts/
  (planner/generator/evaluator) 파일을 TDD 버전으로 갱신한다. 신규
  프로젝트를 TDD로 시작할 때는 `/pilot:project --tdd`를 사용한다.
---

**이미 구현된 코드가 있는 프로젝트**에 TDD 모드를 사후 적용한다.

> 신규 프로젝트를 TDD로 시작할 때는 `/pilot:project {PROJECT} --tdd` 를 사용한다.
> 이 커맨드는 기존 코드베이스에 TDD 체계를 도입하거나, 이미 일부 구현된 프로젝트에 TDD를 적용할 때 사용한다.

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P1** 수행. (`{PROJECT}` 획득)
실패 시 [messages.md](../context/shared/messages.md) 의 `workspace_missing` / `no_active_project` 출력 후 종료.

## 수행 절차

1. `workspace/projects/{PROJECT}/project.md` 의 `## 제한사항` 에 TDD 모드 문구 ([tdd-activation.md](../context/modes/tdd-activation.md) §1-1 literal) 존재 여부를 확인한다.
   - **이미 있으면**: [messages.md](../context/shared/messages.md) 의 `tdd_already_active` 출력 후 2단계에서 누락된 항목만 보완한다.
   - **없으면**: 2단계를 수행한다.
2. [tdd-activation.md](../context/modes/tdd-activation.md) 절차에 따라 `project.md`, `prompts/planner.md`, `prompts/generator.md`, `prompts/evaluator.md` 를 갱신한다. 각 단계는 idempotent 하므로 이미 적용된 항목은 자동으로 건너뛴다.
3. 적용 결과를 요약 출력한다:
   - 수정된 파일: `project.md`, `prompts/planner.md`, `prompts/generator.md`, `prompts/evaluator.md`
   - 참조 문서: `skills/rgr.md`
   - 다음 작업 안내: **"TDD 모드 활성화 완료. `@planner` 를 호출해 기능을 스텝 단위로 분할하고 실패 테스트를 작성하세요."**
