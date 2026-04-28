---
name: characterize
description: >-
  Characterization test 모드로 전환/복귀한다. 기존 레거시 코드의 현재 동작을
  spec 으로 포착하기 위한 모드. 구현 변경 없음 (`{source_root}` 잠금). 리팩터는 별도 사이클.
---

# /pilot:characterize

레거시 코드의 **현재 동작을 포착** 하는 characterization spec 을 추가하는 모드로 전환한다. 구현 변경 없이 spec 만 추가하여, 이후 리팩터를 안전하게 진행할 발판을 만든다.

상세 절차: [`characterize.md`](../context/modes/characterize.md).

대상: $ARGUMENTS  (`off` / `없음` — mode 복귀)

---

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P1** 수행.

- P1: `{PROJECT}` 획득. 실패 시 [messages.md](../context/shared/messages.md) 의 `workspace_missing` / `no_active_project` 출력 후 종료.

## 동작

`$ARGUMENTS` 를 분기:

| `$ARGUMENTS` | 동작 |
| --- | --- |
| (빈 문자열) 또는 `on` | `.agent-state.yml` 에 `mode: characterize` 설정 |
| `off` | `.agent-state.yml` 의 `mode` 를 `null` (또는 키 제거) 로 설정 |

### 절차

1. `workspace/projects/{PROJECT}/.agent-state.yml` 을 Read.
2. 파일이 없거나 `schema` 가 `v1.1` 미만이면 에러 출력 후 종료: **"프로젝트 상태 파일 누락 또는 구버전. `/pilot:doctor --fix` 실행 후 재시도."**
3. 모드 전환:
   - **on**: `mode: characterize` 라인을 추가 (기존에 `mode:` 키가 있으면 값 교체)
   - **off**: `mode:` 라인을 제거하거나 `mode: null` 로 설정
4. 결과 확인 후 사용자에게 안내:

   ```
   characterize 모드 {ON|OFF}.

   - mode: {characterize | null}
   - tdd: {true | false}

   이후 @planner / @generator / @evaluator 호출 시 {characterize.md | rgr.md | 표준} 절차가 적용됩니다.
   상세: {CLAUDE_PLUGIN_ROOT}/skills/context/modes/characterize.md
   ```

## 주의

- `tdd: true` 와 `mode: characterize` 가 **동시 설정** 된 경우 characterize 가 우선 적용된다 (Red 계약 대신 Characterization Contract).
- Characterization 사이클 중 `{source_root}` 수정은 Evaluator 가 반려한다. 리팩터가 필요하면 먼저 `/pilot:characterize off` 로 복귀.
- 정본 절차는 [`characterize.md`](../context/modes/characterize.md). 본 스킬은 **상태 전환 명령** 일 뿐 절차 정의가 아니다.
