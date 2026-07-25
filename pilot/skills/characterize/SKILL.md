---
name: characterize
description: >-
  Characterization test 모드로 전환/복귀한다. 기존 레거시 코드의 현재 동작을
  테스트로 포착하기 위한 모드. 구현 변경 없음 (`{source_root}` 수정 금지). 리팩터는 별도 사이클.
---

# /pilot:characterize

레거시 코드의 **현재 동작을 포착**하는 characterization 테스트를 추가하는 모드로 전환한다. 구현 변경 없이 테스트만 추가해 이후 리팩터를 안전하게 진행할 발판을 만든다. **본 스킬은 상태 전환 명령일 뿐 — 절차 정본은 [`characterize.md`](../context/modes/characterize.md)**.

대상: $ARGUMENTS (`off` / 없음 = on)

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P1** 수행. 실패 시 [messages.md](../context/shared/messages.md) 의 `workspace_missing`/`no_active_project` 출력 후 종료.

## 동작

`$ARGUMENTS` 가 (빈 문자열) 또는 `on` 이면 `.agent-state.yml` 에 `mode: characterize` 설정, `off` 면 `mode` 를 `null`(또는 키 제거)로 설정.

1. `.agent-state.yml` Read. 없거나 `schema` 가 `v1.1` 미만이면 에러 후 종료: "프로젝트 상태 파일 누락 또는 구버전. `/pilot:doctor --fix` 실행 후 재시도."
2. 모드 전환 (on: `mode: characterize` 라인 추가/교체 · off: `mode:` 제거 또는 `null`).
3. 결과 안내: `characterize 모드 {ON|OFF}` + `mode`/`tdd` 현재 값 + 적용될 절차(characterize.md|rgr.md|표준) + 정본 경로.

## 주의

- `tdd: true` 와 동시 설정 시 우선순위는 [`characterize.md`](../context/modes/characterize.md):10 이 정본 (characterize 우선).
- `{source_root}` 잠금은 `scope-guard.sh` 훅(Edit/Write 시점 차단) + Evaluator `git diff` 재검증의 이중 강제. 리팩터가 필요하면 먼저 `/pilot:characterize off` 로 복귀.
