---
name: auto
description: >-
  이미 생성된 단일 feature 를 planner→critic→generator→evaluator 로
  자동 순차 진행하는 감독형 자율 모드. hard-stop 신호(plan-validate 실패·
  critic blocking·재시도 소진·신호 파싱 실패)에 걸리면 즉시 사람에게 제어를
  반환한다. 모든 자동 결정은 features/NN-{slug}.auto.md 에 기록한다. feature
  생성·명세 작업은 `/pilot:create-feature`·`/pilot:analyze` 가 담당한다.
---

# /pilot:auto

이미 명세가 존재하는 **단일 feature** 를 자동 순차 진행한다. 기본 흐름은
사용자가 각 에이전트를 명시 호출하는 것이고, 이 스킬은 그 마찰을 줄이는
**opt-in 예외 모드**다. 위험 신호에 걸리면 자동 진행을 멈추고 사람에게 넘긴다.

대상: $ARGUMENTS (feature 번호 — 예: `03` 또는 `3`)

**사용 예:**

```
/pilot:auto 03
/pilot:auto 3
```

---

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P1** 수행.

- P1: `{PROJECT}` 획득. 실패 시 [messages.md](../context/shared/messages.md) 의
  `workspace_missing` / `no_active_project` 출력 후 종료.

`$ARGUMENTS` 가 비어있으면 **"feature 번호를 입력하세요. 예: `/pilot:auto 03`"**
안내 후 종료.

`{NN}` = 입력 번호를 2자리 zero-pad (예: `3` → `03`).
`{FEAT}` = `workspace/projects/{PROJECT}/features/{NN}-*.md` (`.plan.md`·`.plan.critic.md`·`.auto.md` 제외).
`{FEAT}` 가 없으면 **"feature {NN} 없음. `/pilot:create-feature` 로 먼저 생성하세요."**
출력 후 종료 (hard-stop: feature 부재).

`{AUTO_LOG}` = `workspace/projects/{PROJECT}/features/{NN}-{slug}.auto.md`.

---

## 재개 확인

`{AUTO_LOG}` 이 이미 존재하면, 이전 실행이 중단됐거나 완료된 것이다.
파일 마지막 `## Run` 섹션의 마지막 줄(stop 사유 또는 ✅ DONE)을 읽고
사용자에게 **1회 확인**한다:

```
이 feature 는 이전에 auto-pilot 이 실행됐습니다.
마지막 상태: {마지막 줄}

어떻게 할까요?
  1. 여기서 재개 (마지막 멈춘 phase 다음부터)
  2. 처음부터 다시 (planner 부터)
  3. 취소
```

사용자 응답 전까지 진행하지 않는다. 이미 ✅ DONE 인 경우에도 동일하게
"이미 완료됨, 다시 할까요?" 로 확인한다. `{AUTO_LOG}` 이 없으면 처음부터
(planner) 시작하고 새 `## Run` 섹션을 연다.

---

## 자동 진행 절차

각 단계 후 반드시 `auto_pilot.py` 로 다음 액션을 결정한다. **스킬이 직접
신호를 해석하지 않는다** — CLI 가 반환한 `kind` 에 따라서만 분기한다.

### 1. planner

`@pilot-planner` 를 호출해 `{NN}-{slug}.plan.md` 를 작성하게 한다.
완료되면 plan 을 검증한다 (mode 는 `.agent-state.yml` 의 tdd/characterize 로 결정 —
tdd:true→`tdd`, mode:characterize→`characterize`, 그 외→`standard`):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/plan-validate.py \
  workspace/projects/{PROJECT}/features/{NN}-{slug}.plan.md --mode {MODE}
echo "exit=$?"
```

exit 0 이면 `--plan-valid true`, 아니면 `false`:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/auto_pilot.py --phase planner --plan-valid {true|false}
```

- `kind=proceed` → 2번으로
- `kind=stop` (reason=plan-validate) → **STOP**. 로그에 기록 후 사람에게 보고.

### 2. critic

`@pilot-planner-critic` 를 호출해 `{NN}-{slug}.plan.critic.md` 를 작성하게 한다.
완료되면:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/auto_pilot.py --phase critic \
  --critic-file workspace/projects/{PROJECT}/features/{NN}-{slug}.plan.critic.md
```

- `kind=proceed` (챌린지 0건) → 3번으로
- `kind=reflect` (suggestion/nit 만) → `@pilot-planner` 를 재호출해 챌린지를
  반영하고 `.plan.critic.md` 의 `## 합의` 표를 채우게 한 뒤 3번으로.
- `kind=stop` (reason=critic-blocking) → **STOP**. blocking 챌린지는 사람 판단.
- `kind=stop` (reason=signal-parse) → **STOP**. critic 파일 형식 이상.

### 3. generator

`@pilot-generator` 를 호출해 구현하게 한다. (재시도 시에도 이 단계로 재진입.)
generator 는 산출 신호가 없으므로 결정 호출 없이 4번으로 진행한다.
generator 호출이 예외/빈 출력으로 실패하면 **STOP** (reason=agent-error) 후
로그 기록.

### 4. evaluator

`@pilot-evaluator` 를 호출해 검증하게 한다. evaluator 의 VERIFICATION REPORT
출력을 파일로 저장한다 (`{NN}-{slug}.report.md` 임시 저장 또는 evaluator 가
남긴 산출물 경로). 그 파일로:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/auto_pilot.py --phase evaluator \
  --report-file {REPORT_PATH} --retries-used {R}
```

`{R}` = 지금까지 generator 재진입 횟수 (최초 0).

- `kind=done` (READY) → ✅ 완료. 로그에 기록 후 사람에게 보고.
- `kind=retry` (NOT_READY, 재시도 잔여) → `{R}` 을 1 증가시키고 3번(generator)
  으로 재진입.
- `kind=stop` (reason=retry-exhausted) → **STOP**. 재시도 소진, 사람 판단.
- `kind=stop` (reason=signal-parse) → **STOP**. REPORT 형식 이상.

---

## 감사 로그 (`{AUTO_LOG}`)

매 전이마다 `{AUTO_LOG}` 에 타임라인 한 줄을 append 한다. 새 실행은 새
`## Run N — {날짜}` 섹션으로 시작한다. 형식:

```markdown
# Auto-pilot Log: {NN}-{slug}

## Run 1 — {YYYY-MM-DD}
- [planner]  plan.md 작성 → plan-validate {PASS|FAIL}
- [critic]   챌린지 {N}건 (blocking a · suggestion b · nit c) → {proceed|reflect}
- [generator] diff 생성
- [evaluator] {READY|NOT_READY} ({실패 gate 요약})
- [retry 1/1] generator 재진입 → evaluator {결과}
- {✅ DONE | ❌ STOP: {사유} (hard-stop)}
  → {사람 판단 필요 항목 — stop 인 경우}
```

각 줄은 해당 단계가 끝나는 즉시 기록한다 (중단돼도 진행 흔적이 남도록).

---

## STOP 시 사람에게 보고

자동 진행이 멈추면 메인 대화에 다음을 출력하고 **종료**한다 (더 진행하지 않음):

```
auto-pilot 중단: {NN}-{slug}
사유: {stop 사유}
마지막 단계: {phase}
사람 판단 필요: {항목}

수정 후 `/pilot:auto {NN}` 으로 재개할 수 있습니다.
로그: features/{NN}-{slug}.auto.md
```

---

## 제약

- **opt-in 예외 모드.** pilot 의 기본은 사용자가 각 에이전트를 명시 호출하는
  것이다. 이 스킬은 저위험·소규모 feature 의 마찰을 줄이기 위한 것이며,
  위험 신호에 걸리면 항상 사람에게 제어를 반환한다.
- **스킬은 판단하지 않는다.** 모든 전이는 `auto_pilot.py` 가 신호 enum 을 보고
  내린 결정(`kind`)에 따른다. 도메인 판단은 각 에이전트의 책임이다.
- **신호를 못 읽으면 멈춘다.** critic/evaluator 산출물 파싱 실패는 추측 없이
  hard-stop(signal-parse) 한다.
- **재시도는 정확히 1회**, 항상 generator 재진입. plan 자체가 틀렸다면 2차
  NOT_READY 로 사람에게 넘어간다.
- **단일 feature 단위.** 다수 feature 연속 진행은 지원하지 않는다.

---

## 참고

- `/pilot:create-feature` — 단일 feature 명세 생성 (이 스킬의 선행 단계)
- `/pilot:focus` — 진행 중 사용자 결정을 에이전트에 전달
- `@pilot-planner` 외 — 수동으로 각 단계 호출 (auto 를 쓰지 않을 때)
