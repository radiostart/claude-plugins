# pilot — Modes skills

활성 프로젝트의 실행 모드를 다룬다. 3 개 스킬: `tdd` `characterize` `autopilot`. tdd·characterize 는 `.agent-state.yml` 의 모드 플래그를 토글하고 `project.md`·`prompts/*` 의 거동을 바꾸며, autopilot 은 단일 feature 를 자동 순차 진행하는 opt-in 예외 모드다.

> 두 모드 동시 활성 시 — `tdd: true` + `mode: characterize` 면 **characterize 가 우선** (Red 계약 대신 Characterization Contract). 정본은 `pilot/skills/context/modes/characterize.md:10` 이며 `pilot/skills/characterize/SKILL.md:28`·`pilot/skills/tdd/SKILL.md:13`·`pilot/skills/context/lifecycle/plan-schema.md:18` 이 모두 이 줄을 가리킨다.

**모드 → plan 스키마 매핑** (`pilot/skills/context/lifecycle/plan-schema.md:10-16`):

| `mode` | `tdd` | 적용 스키마 |
| --- | --- | --- |
| `characterize` | (무시) | **characterize** |
| 미설정 | `true` | **tdd** |
| 미설정 | `false` 또는 미설정 | **standard** |

---

## `/pilot:tdd`

TDD 모드를 사후 활성화·비활성화·정합성 보정·상태 보고한다. 4 분기: `on` / `off` / `--fix` / 인자 없음 (`pilot/skills/tdd/SKILL.md:4-7`). 대상은 **이미 구현된 코드가 있는 프로젝트** (`pilot/skills/tdd/SKILL.md:10`).

> 신규 프로젝트를 TDD 로 시작할 때는 `/pilot:project {PROJECT} --tdd` 를 사용한다 (`pilot/skills/tdd/SKILL.md:12`).

- **사전 확인**: P1 — `{PROJECT}` 획득 (`pilot/skills/tdd/SKILL.md:15-17`).
- **절차 SSOT**: 전 서브커맨드 공통으로 `pilot/skills/context/modes/tdd-activation.md` — SKILL.md 는 **진입 분기만** 기술한다 (`pilot/skills/tdd/SKILL.md:19`).
- **`on` — 활성화** (`pilot/skills/tdd/SKILL.md:21-23`): state `tdd:` 가 이미 `true` 면 `[INFO] TDD 모드 이미 활성화 상태` 후 종료 (idempotent). 아니면 tdd-activation **§1-1b** (백업 마커 주입) → **§1~6** (활성화 본체, 각 단계 idempotent) 위임. 완료 후 갱신 파일 요약 출력.
- **`off` — 비활성화** (`pilot/skills/tdd/SKILL.md:25-27`): state `tdd:` 가 이미 `false` 면 idempotent 종료. 아니면 tdd-activation `## 비활성화 절차` **off-1~off-7** 전체 위임 (마커 부재 시 template fallback INFO 동반).
- **`--fix` — 3-way 정합성 보정** (`pilot/skills/tdd/SKILL.md:29-37`): `.agent-state.yml` 의 `tdd:` 값을 **진실로 간주**하고 아래 3 축을 검증한다 — state.yml 값 / `project.md` `## 에이전트 호출 흐름` 의 TDD 분기 / `prompts/{planner,generator,evaluator}.md` 의 TDD 섹션. state 가 `true` 면 on 절차, `false` 면 off 절차를 재실행 (일치하면 idempotent no-op). 출력은 "보정 전 INCONSISTENT: …" → "보정 후 CONSISTENT: …".
- **인자 없음 — 상태 보고** (`pilot/skills/tdd/SKILL.md:39-51`): `ON|OFF|INCONSISTENT` + state `tdd:` (`true|false|missing`) + `project.md TDD 제한사항` (`present|absent`) + `prompts TDD 섹션` (`N/3`). 불일치 시 `--fix` 안내.
- **Detect literal** (idempotency 판별 기준, `pilot/skills/context/modes/tdd-activation.md`): 제한사항 `- **TDD 모드**:` (`:21`) · 호출 흐름 `### 1. Planner — Red 계약 작성` (`:51`) · planner `## TDD — Red 계약` (`:88`) · generator `> **TDD 모드**: Red 작성` (`:104`) · evaluator `## TDD 테스트 실행` (`:117`) · state `tdd: true` (`:218`). 해당 literal 이 이미 있으면 그 단계를 생략한다 (`:6`).
- **수정 대상 파일**: `.agent-state.yml` · `project.md` · `prompts/{planner,generator,evaluator}.md`.
- **참조**: `pilot/skills/context/modes/tdd-activation.md` (활성화·비활성화 SSOT) · `pilot/skills/context/modes/rgr.md` (Red-Green-Refactor 정책 — Planner Red Contract `:44`, Generator Red+Green+Refactor `:78`, Evaluator 실행·검증 `:138`, Mock 안티패턴 `:153`).

---

## `/pilot:characterize`

레거시 코드의 **현재 동작을 포착**하는 characterization 테스트 모드로 전환한다. 구현 변경 없이 테스트만 추가해 이후 리팩터의 발판을 만든다 (`pilot/skills/characterize/SKILL.md:10`). **본 스킬은 상태 전환 명령일 뿐 — 절차 정본은 `pilot/skills/context/modes/characterize.md`.**

- **인자** (`pilot/skills/characterize/SKILL.md:12·20`): 빈 문자열 또는 `on` → ON, `off` → OFF.
- **사전 확인**: P1 (`pilot/skills/characterize/SKILL.md:14-16`).
- **동작** (`pilot/skills/characterize/SKILL.md:18-24`):
  1. `.agent-state.yml` Read. 없거나 `schema` 가 `v1.1` 미만이면 에러 후 종료 — "프로젝트 상태 파일 누락 또는 구버전. `/pilot:pilot-doctor --fix` 실행 후 재시도."
  2. 모드 전환 — on: `mode: characterize` 라인 추가/교체 · off: `mode:` 제거 또는 `null`.
  3. 결과 안내 — `characterize 모드 {ON|OFF}` + `mode`/`tdd` 현재 값 + 적용될 절차 (`characterize.md`|`rgr.md`|표준) + 정본 경로.
- **주의** (`pilot/skills/characterize/SKILL.md:26-29`):
  - `tdd: true` 와 동시 설정 시 characterize 우선.
  - **`{source_root}` 잠금은 이중 강제** — `scope-guard.sh` 훅이 Edit/Write 시점에 차단하고 (`pilot/hooks/scope-guard.sh:28-33·59-63` — STATE.md 진행중 행 → `.agent-state.yml` 의 `mode: characterize` 확인 후 `exit 2`), Evaluator 가 `git diff` 로 재검증한다. 리팩터가 필요하면 먼저 `/pilot:characterize off`.
- **모드 정책 요지** (`pilot/skills/context/modes/characterize.md`):
  - **전제** (`:9-12`): `mode: characterize` 활성 프로젝트에서만 적용 · **구현 변경 없음** (리팩터는 테스트가 녹색인 상태에서 별도 사이클) · Planner → Generator → Evaluator 흐름 유지.
  - **역할 분담** (`:16-20`): Planner = 포착 대상 분할 + Characterization Contract 작성 (테스트 코드 X) / Generator = 현재 동작 실행·기록 (테스트 계층 + `.plan.md` 만, **`{source_root}` 절대 금지**) / Evaluator = `{source_root}` 미수정 검증 + 테스트 pass + 3 축 일치.
  - **3 축** (`:36-38`): **입력** (호출 인자·request body·CLI args) · **현재 출력** (반환값·response body·stdout·exit code — **추정하지 않고 Generator 가 실제 실행해서 기록**) · **관찰된 사이드 이펙트** (탐지 불가한 것은 "탐지 불가 가능성" 으로 명시, 숨기지 말 것).
  - 판정 축 `capture_lockdown` (`pilot/skills/context/shared/guardrails.md:17-19`): `git diff --stat {source_root}` 가 비어 있어야 pass — 1 줄이라도 있으면 fail (Generator 원복·재작업). 다른 모드에서는 skip.

---

## `/pilot:autopilot`

이미 명세가 존재하는 **단일 feature** 를 planner→critic→generator→evaluator 로 자동 순차 진행하는 감독형 자율 모드 (`pilot/skills/autopilot/SKILL.md:17`). 기본 흐름은 사용자가 각 에이전트를 명시 호출하는 것이고, 이 스킬은 그 마찰을 줄이는 **opt-in 예외 모드**다 (`pilot/skills/context/shared/guardrails.md:47` § A16).

> **자발 발동 금지** — "계속·이어서 진행해줘" 류 발화만으로는 발동하지 않는다. 필요해 보이면 대상 feature 를 제시하고 확인 1 회 (`pilot/skills/autopilot/SKILL.md:4-7`).
> **wrapper 호출은 동기 실행** — 직전 단계 산출물을 수신·판독하기 전에 다음 단계를 기동하지 않는다. 하니스가 background 를 기본 제공해도 사용하지 않는다 (`pilot/skills/autopilot/SKILL.md:19`). 메인 루프에서 직접 호출하며 subagent 가 subagent 를 띄우지 않는다.

- **인자**: feature 번호 (예: `03` 또는 `3`) — 2 자리 zero-pad (`pilot/skills/autopilot/SKILL.md:21·27`).
- **사전 확인**: P1 + 인자 검증 (`pilot/skills/autopilot/SKILL.md:23-27`). `{FEAT}` = `features/{NN}-*.md` (`.plan.md`·`.plan.critic.md`·`.auto.md` 제외) — 부재 시 hard-stop. `{AUTO_LOG}` = `features/{NN}-{slug}.auto.md`.
- **재개 확인** (`pilot/skills/autopilot/SKILL.md:29`): `{AUTO_LOG}` 존재 시 마지막 `## Run` 섹션 끝줄을 읽고 **사용자 1 회 확인 없이는 진행하지 않는다** (이미 DONE 이어도 "재개/처음부터/취소" 3 지선다). 부재 시 planner 부터 시작 + 새 `## Run` 섹션.
- **자동 진행 절차** (`pilot/skills/autopilot/SKILL.md:31-70`) — 각 단계 후 반드시 `auto_pilot.py` 로 다음 액션을 결정한다. **스킬이 직접 신호를 해석하지 않고** CLI 가 반환한 `kind` 로만 분기한다:
  1. **planner** (`:35-44`) — `@pilot-planner` → `.plan.md`. mode 는 `.agent-state.yml` 로 결정 (tdd:true→`tdd`, mode:characterize→`characterize`, 그 외→`standard`). `plan-validate.py --mode {MODE}` → `auto_pilot.py --phase planner --plan-valid {true|false}`. `kind=stop`(plan-validate) → **STOP**.
  2. **critic** (`:46-54`) — `@pilot-planner-critic` → `.plan.critic.md` → `auto_pilot.py --phase critic --critic-file ...`. `proceed`(챌린지 0 건) → 3 / `reflect`(suggestion·nit 만) → planner 재호출로 챌린지 반영 + `## 합의` 표 채운 뒤 3 / `stop`(critic-blocking\|signal-parse) → **STOP**.
  3. **generator** (`:56-58`) — 산출 신호가 없으므로 결정 호출 없이 4 로. 예외·빈 출력 실패 시 **STOP**(agent-error).
  4. **evaluator** (`:60-70`) — REPORT 를 파일로 저장 후 `auto_pilot.py --phase evaluator --report-file {PATH} --retries-used {R}`. **`kind=retry` 로 재진입할 때마다 `{R}` 을 반드시 1 증가** — 증가시키지 않으면 `MAX_RETRIES=1` 상한이 무력화돼 무한 루프에 빠진다 (`pilot/tools/auto_pilot.py:29`). `done`(READY) → 완료 / `retry`(NOT_READY, 잔여) → 3 재진입 / `stop`(retry-exhausted\|signal-parse) → **STOP**.
- **plan 분량 가드 (WARN, 비차단)** (`pilot/skills/context/lifecycle/plan-schema.md:98-107`) — plan 은 Generator·Critic·Evaluator 가 매 라운드 전문을 Read 하는 인계 문서라, 분량 초과는 후속 에이전트의 컨텍스트 윈도우를 선소모한다. `plan-validate.py` 가 **본문 30,000 자 초과** (≈ 토큰 10~15k — 한 라운드 인계 문서 상한) 와 **최장 라인 1,500 자 초과** (Read 툴 라인 절단 2,000 자의 안전 마진) 를 stderr `[WARN]` 으로 보고하되 **exit code 는 불변**이다 (`pilot/tools/plan-validate.py:39-46·401`). WARN 시 planner 는 회차 이력 잔재 (`N차 갱신`·`N회차 개정` 헤더, 해소 주석, 기각된 대안의 장문 사유) 를 제거하고 **최신 확정 상태만** 남긴다 — disposition 의 기록처는 critic 합의 표 (현 회차) 이고 회차 간 이력은 git 이다.
- **전이 결정 로직** (`pilot/tools/auto_pilot.py:231-258`): 스크립트는 "판단하지 않는다 — 신호의 enum 값만 보고 전이한다" (`:2-18`). action kind 는 `proceed | reflect | retry | done | stop` (`:15·34`), 유효 severity 는 `{blocking, suggestion, nit}` (`:46`), evaluator 는 `READY`/`NOT_READY` 만 인정 (`:214-228`). 항상 exit 0 (`:306-307`).
- **감사 로그 · STOP 보고** (`pilot/skills/autopilot/SKILL.md:72-82`): `{AUTO_LOG}` 에 매 전이마다 **단계 종료 즉시** 1 줄 append (중단돼도 흔적이 남도록). 새 실행은 새 `## Run N — {날짜}` 섹션. 완료·정지 어느 쪽이든 게이트 이력 1 줄 (`#{NN} {slug}: critic {b}/{s}/{n} · retry {R} · {READY | STOP: 사유}`) 을 **사용자 대면 텍스트로** 출력해 컨텍스트 자동 요약 후에도 대화 앵커로 복원되게 한다 (상태 파일 아님, `{AUTO_LOG}` 와 별개 채널).
- **정지 후 재개 금지** (`pilot/skills/autopilot/SKILL.md:82`): 본 정지는 **사용자만 해소할 수 있는 입력 대기**다 — "완료까지 계속" 류 자율 진행 지침이 컨텍스트에 있어도 정지 사유를 모델이 자체 해소·우회해 재개하지 않는다 (`pilot/skills/context/shared/guardrails.md:51` § 사용자 게이트 생략 금지).
- **제약** (`pilot/skills/autopilot/SKILL.md:84-91`): opt-in 예외 모드 · **신호를 못 읽으면 멈춘다**(signal-parse) · hard-stop enum = `plan-validate 실패`·`critic-blocking`·`signal-parse`·`retry-exhausted`·`agent-error` · **재시도는 정확히 1 회** (항상 generator 재진입, plan 자체가 틀렸다면 2 차 NOT_READY 로 사람에게 넘어감) · **단일 feature 단위** (다수 연속 진행 미지원) · wrapper 동기 호출 (background 기동 금지).
