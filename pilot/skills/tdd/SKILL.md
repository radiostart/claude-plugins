---
name: tdd
description: >-
  TDD 모드를 사후 활성화·비활성화·정합성 보정·상태 보고한다.
  `/pilot:tdd on` — 활성화, `/pilot:tdd off` — 비활성화,
  `/pilot:tdd --fix` — 3-way 정합성 보정, `/pilot:tdd` (인자 없음) — 상태 보고.
  신규 프로젝트를 TDD로 시작할 때는 `/pilot:project --tdd`를 사용한다.
---

**이미 구현된 코드가 있는 프로젝트**에 TDD 모드를 사후 적용하거나 비활성화한다.

> 신규 프로젝트를 TDD로 시작할 때는 `/pilot:project {PROJECT} --tdd` 를 사용한다.
> `mode: characterize` 와 동시 설정 시 우선순위는 [`characterize.md`](../context/modes/characterize.md):10 이 정본 (characterize 우선).

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P1** 수행 (`{PROJECT}` 획득). 실패 시 [messages.md](../context/shared/messages.md) 의 `workspace_missing`/`no_active_project` 출력 후 종료.

절차 SSOT 는 전 서브커맨드 공통으로 [tdd-activation.md](../context/modes/tdd-activation.md) — 아래는 진입 분기만 기술한다.

## /pilot:tdd on — 활성화

`.agent-state.yml` 의 `tdd:` 가 이미 `true` 면 `[INFO] TDD 모드 이미 활성화 상태` 후 종료(idempotent). 아니면 [tdd-activation.md](../context/modes/tdd-activation.md) **§1-1b**(백업 마커 주입) → **§1~6**(활성화 본체, 각 단계 idempotent) 위임. 완료 후 갱신 파일(`.agent-state.yml`·`project.md`·`prompts/*`) 요약 출력.

## /pilot:tdd off — 비활성화

`tdd:` 가 이미 `false` 면 `[INFO] TDD 모드 이미 비활성화 상태` 후 종료(idempotent). 아니면 [tdd-activation.md](../context/modes/tdd-activation.md) `## 비활성화 절차` **off-1~off-7** 전체 위임(마커 부재 시 template fallback INFO 함께 출력). 완료 후 복원 결과 요약 출력.

## /pilot:tdd --fix — 정합성 보정

`.agent-state.yml` 의 `tdd:` 값을 **진실로 간주**(Q4 — state.yml 진실). 아래 3-way 를 검증한다:

- state.yml `tdd:` 값
- project.md `## 에이전트 호출 흐름` 의 TDD 분기 여부 ([tdd-activation.md](../context/modes/tdd-activation.md) §1-2 Detect literal)
- prompts/{planner,generator,evaluator}.md 의 TDD 섹션 존재 여부 (동일 문서 §2·§3·§4 각 Detect literal)

state 값이 `true` 면 on 절차, `false` 면 off 절차를 재실행한다(이미 일치하면 idempotent no-op). 완료 후 "보정 전 INCONSISTENT: {내용}" → "보정 후 CONSISTENT: state=… · project.md=… · prompts=…" 출력.

## /pilot:tdd (인자 없음) — 상태 보고

`.agent-state.yml` 의 `tdd:` 값 + project.md·prompts 3파일의 TDD 섹션 존재 여부([tdd-activation.md](../context/modes/tdd-activation.md) §1-2·§2·§3·§4 각 Detect literal 기준)를 확인한다. 출력:

```
TDD 모드 상태: {ON|OFF|INCONSISTENT}

- .agent-state.yml tdd:      {true|false|missing}
- project.md TDD 제한사항:    {present|absent}
- prompts TDD 섹션:           {3/3|N/3 (...)}

{모두 일치: ✓ 정합성 OK / 불일치: ⚠ INCONSISTENT — `/pilot:tdd --fix` 로 동기화하세요}
```
