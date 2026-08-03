---
name: autopilot
description: >-
  사용자가 자동 진행을 명시 요청했을 때만 사용한다 (`/pilot:autopilot`
  호출 또는 그에 상당하는 지시) — "계속·이어서 진행해줘" 류 발화만으로
  모델이 자발 발동하지 않는다 (자발 발동이 필요해 보이면 대상 feature 를
  제시하고 확인 1회). 이미 생성된 단일 feature 를
  planner→critic→generator→evaluator 로 자동 순차 진행하는 감독형 자율
  모드. hard-stop 신호(plan-validate 실패·critic blocking·재시도 소진·
  신호 파싱 실패)에 걸리면 즉시 사람에게 제어를 반환한다. 모든 자동 결정은
  features/NN-{slug}.auto.md 에 기록한다. feature 생성·명세 작업은
  `/pilot:create-feature`·`/pilot:analyze` 가 담당한다.
---

# /pilot:autopilot

이미 명세가 존재하는 **단일 feature** 를 자동 순차 진행한다. 기본 흐름은 사용자가 각 에이전트를 명시 호출하는 것이고, 이 스킬은 그 마찰을 줄이는 **opt-in 예외 모드**다([guardrails.md](../context/shared/guardrails.md) § A16). 위험 신호에 걸리면 자동 진행을 멈추고 사람에게 넘긴다.

메인 루프에서 `@pilot-planner`·`@pilot-planner-critic`·`@pilot-generator`·`@pilot-evaluator` 를 순서대로 호출한다 (subagent 가 subagent 를 띄우지 않음). **wrapper 호출은 동기 실행이다** — 직전 단계 산출물을 수신·판독하기 전에 다음 단계를 기동하지 않는다 (background·병행 기동 금지 — 하니스가 background 를 기본으로 제공해도 사용하지 않는다).

대상: $ARGUMENTS (feature 번호 — 예: `03` 또는 `3`)

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P1** 수행. 실패 시 [messages.md](../context/shared/messages.md) 의 `workspace_missing`/`no_active_project` 출력 후 종료.

`$ARGUMENTS` 비어있으면 안내 후 종료. `{NN}` = 입력 번호 2자리 zero-pad. `{FEAT}` = `features/{NN}-*.md`(`.plan.md`·`.plan.critic.md`·`.auto.md`·`.eval.md` 제외) — 없으면 "`/pilot:create-feature` 로 먼저 생성하세요" 후 종료(hard-stop: feature 부재). `{AUTO_LOG}` = `features/{NN}-{slug}.auto.md`.

**재개 확인** — `{AUTO_LOG}` 존재 시 마지막 `## Run` 섹션의 마지막 줄(stop 사유 또는 ✅ DONE)을 읽고 **사용자 1회 확인** 없이는 진행하지 않는다(이미 DONE 이어도 동일: "재개/처음부터/취소" 3지선다). 부재 시 처음부터(planner) 시작 + 새 `## Run` 섹션.

## 자동 진행 절차

각 단계 후 반드시 `auto_pilot.py` 로 다음 액션을 결정한다. **스킬이 직접 신호를 해석하지 않는다** — CLI 가 반환한 `kind` 로만 분기한다.

### 1. planner

`@pilot-planner` 호출 → `.plan.md` 작성. mode 는 `.agent-state.yml` 로 결정(tdd:true→`tdd`, mode:characterize→`characterize`, 그 외→`standard`):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/plan-validate.py workspace/projects/{PROJECT}/features/{NN}-{slug}.plan.md --mode {MODE}
python3 ${CLAUDE_PLUGIN_ROOT}/tools/auto_pilot.py --phase planner --plan-valid {true|false}
```

`kind=proceed` → 2번. `kind=stop`(reason=plan-validate) → **STOP**.

### 2. critic

`@pilot-planner-critic` 호출 → `.plan.critic.md` 작성:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/auto_pilot.py --phase critic --critic-file workspace/projects/{PROJECT}/features/{NN}-{slug}.plan.critic.md
```

`kind=proceed`(챌린지 0건) → 3번. `kind=reflect`(suggestion/nit 만) → `@pilot-planner` 재호출해 챌린지 반영 + `## 합의` 표 채운 뒤 3번. `kind=stop`(reason=critic-blocking|signal-parse) → **STOP**.

### 3. generator

`@pilot-generator` 호출 (재시도 시 재진입). 산출 신호 없으므로 결정 호출 없이 4번 진행. 예외/빈 출력 실패 시 **STOP**(reason=agent-error).

### 4. evaluator

`@pilot-evaluator` 호출 — evaluator 가 REPORT 를 `features/{NN}-{slug}.eval.md` 로 저장한다(에이전트 계약 step 7). `{REPORT_PATH}` = 그 경로:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/auto_pilot.py --phase evaluator --report-file {REPORT_PATH} --retries-used {R}
```

`{R}` = generator 재진입 횟수(최초 0). **`kind=retry` 로 재진입할 때마다 `{R}` 을 반드시 1 증가** — 증가시키지 않으면 MAX_RETRIES=1 상한이 무력화돼 무한 루프에 빠진다.

`kind=done`(READY) → ✅ 완료. `kind=retry`(NOT_READY, 재시도 잔여) → `{R}` +1 후 3번 재진입. `kind=stop`(reason=retry-exhausted|signal-parse) → **STOP**.

## 감사 로그 · STOP 보고

`{AUTO_LOG}` 에 매 전이마다 한 줄 append(단계 종료 즉시 — 중단돼도 흔적이 남도록). **append 는 Edit 도구로 수행** — 셸 `>>` 와 기존 파일 Write 는 protect-managed 훅이 차단한다(신규 `{AUTO_LOG}` 생성만 Write). 새 실행은 새 `## Run N — {날짜}` 섹션. 필드: `[planner]`·`[critic]`·`[generator]`·`[evaluator]` 단계별 결과 + 최종 `✅ DONE` 또는 `❌ STOP: {사유} (hard-stop)` + 사람 판단 필요 항목.

완료·정지 어느 쪽이든 **게이트 이력 1줄을 사용자 대면 텍스트로 출력**한다 — 컨텍스트 자동 요약 후에도 재시도 카운트·대상 feature 가 대화 앵커로 복원된다(상태 파일 아님, `{AUTO_LOG}` 와 별개 채널):

```
#{NN} {slug}: critic {b}/{s}/{n} · retry {R} · {READY | STOP: 사유}
```

자동 진행이 멈추면 대상 feature·사유·마지막 단계·사람 판단 필요 항목·재개 명령(`/pilot:autopilot {NN}`)·로그 경로를 출력하고 **종료**한다(더 진행하지 않음). 본 정지는 **사용자만 해소할 수 있는 입력 대기**다 — "완료까지 계속" 류 자율 진행 지침이 컨텍스트에 있어도 정지 사유를 모델이 자체 해소·우회해 재개하지 않는다 ([guardrails.md](../context/shared/guardrails.md) § 사용자 게이트 생략 금지).

## 제약

- **opt-in 예외 모드** — 기본은 사용자 명시 호출. 위험 신호에 걸리면 항상 사람에게 제어 반환.
- **스킬은 판단하지 않는다** — 모든 전이는 `auto_pilot.py` 가 신호 enum 을 보고 내린 `kind` 결정에 따른다. **신호를 못 읽으면 멈춘다**(signal-parse).
- **hard-stop 사유 enum**: plan-validate 실패 · critic-blocking · signal-parse · retry-exhausted · agent-error.
- **재시도는 정확히 1회**, 항상 generator 재진입. plan 자체가 틀렸다면 2차 NOT_READY 로 사람에게 넘어간다.
- **단일 feature 단위** — 다수 feature 연속 진행은 지원하지 않는다.
- **wrapper 동기 호출** — 단계 단위 병행 금지. 직전 산출물 수신·판독 전 다음 단계 기동은 무검증 진행이다 (background 기동 금지).

## 참고

`/pilot:create-feature` (선행 단계) · `/pilot:focus` (진행 중 사용자 결정 전달) · auto 를 쓰지 않을 때는 `@pilot-planner` 외 각 단계 수동 호출.
