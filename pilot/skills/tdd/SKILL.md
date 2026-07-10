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
> `mode: characterize` 와 동시 설정 시 **characterize 가 우선** 적용된다 — 우선순위 규칙: [characterize/SKILL.md](../characterize/SKILL.md) 참조.

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P1** 수행. (`{PROJECT}` 획득)
실패 시 [messages.md](../context/shared/messages.md) 의 `workspace_missing` / `no_active_project` 출력 후 종료.

---

## /pilot:tdd on — 활성화

1. `workspace/projects/{PROJECT}/.agent-state.yml` 의 `tdd:` 값을 읽는다.
   - 이미 `tdd: true` → `[INFO] TDD 모드 이미 활성화 상태 (state.yml tdd: true)` 보고 후 종료 (idempotent).
2. [tdd-activation.md](../context/modes/tdd-activation.md) §1-1b (백업 마커 주입) 수행.
3. [tdd-activation.md](../context/modes/tdd-activation.md) §1~6 (활성화 본체) 위임 — 각 단계 idempotent.
4. 완료 후 사용자 출력:
   ```
   ✓ TDD 모드 활성화
     - .agent-state.yml: tdd: true
     - project.md `## 에이전트 호출 흐름`: TDD 분기로 교체 (백업 마커 주입 완료)
     - prompts/{planner,generator,evaluator}.md: TDD 분기 활성
   ```

---

## /pilot:tdd off — 비활성화

1. `workspace/projects/{PROJECT}/.agent-state.yml` 의 `tdd:` 값을 읽는다.
   - 이미 `tdd: false` → `[INFO] TDD 모드 이미 비활성화 상태 (state.yml tdd: false)` 보고 후 종료 (idempotent).
2. [tdd-activation.md](../context/modes/tdd-activation.md) 의 `## 비활성화 절차 (/pilot:tdd off)` 위임 — off-1~off-7 전체 수행.
3. 완료 후 사용자 출력:
   ```
   ✓ TDD 모드 비활성화
     - .agent-state.yml: tdd: false
     - project.md `## 에이전트 호출 흐름`: 표준 흐름 복원 (백업 마커에서)
     - prompts/{planner,generator,evaluator}.md: 표준 분기 복원
   ```
   - 마커 부재 시 (template fallback) INFO 1줄 함께 출력 (off-2 참조).

---

## /pilot:tdd --fix — 정합성 보정

1. `workspace/projects/{PROJECT}/.agent-state.yml` 의 `tdd:` 값을 진실로 간주 (Q4 — state.yml 진실).
2. 아래 3-way 검증을 수행한다:
   - state.yml `tdd:` 값
   - project.md `## 에이전트 호출 흐름` TDD 분기 여부 (`### 1. Planner — Red 계약 작성` 포함 여부)
   - prompts/{planner,generator,evaluator}.md 의 TDD 섹션 존재 여부 (각 Detect literal 확인)
3. state 값이 `true` 이면 `/pilot:tdd on` 절차 재실행 (idempotent — 이미 일치하면 no-op).
   state 값이 `false` 이면 `/pilot:tdd off` 절차 재실행.
4. 완료 후 사용자 출력:
   ```
   ✓ TDD 정합성 보정 (state.yml 진실 기준)
     - 보정 전 INCONSISTENT: {검출된 불일치 내용}
     - 보정 후 CONSISTENT: state={true|false} · project.md={TDD|표준} · prompts={TDD|표준}
   ```

---

## /pilot:tdd (인자 없음) — 상태 보고

1. `workspace/projects/{PROJECT}/.agent-state.yml` 의 `tdd:` 값을 읽는다.
2. project.md `## 에이전트 호출 흐름` 내 TDD Detect literal (`### 1. Planner — Red 계약 작성`) 존재 여부를 확인한다.
3. prompts/{planner,generator,evaluator}.md 의 TDD 섹션 각각의 Detect literal 존재 여부를 확인한다.
   - planner: `## TDD — Red 계약`
   - generator: `> **TDD 모드**: Red 작성`
   - evaluator: `## TDD 테스트 실행`
4. 사용자 출력:
   ```
   TDD 모드 상태: {ON|OFF|INCONSISTENT}

   - .agent-state.yml tdd:      {true|false|missing}
   - project.md TDD 제한사항:    {present|absent}
   - prompts TDD 섹션:           {3/3|N/3 (...)}

   {모두 일치 시: ✓ 정합성 OK
    불일치 시: ⚠ INCONSISTENT — `/pilot:tdd --fix` 로 동기화하세요}
   ```
   - 셋이 모두 일치하면 `✓ 정합성 OK`.
   - 하나라도 불일치하면 `⚠ INCONSISTENT — `/pilot:tdd --fix` 로 동기화하세요` 출력.
