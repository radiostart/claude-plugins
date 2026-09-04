# pilot — Modes skills

활성 프로젝트의 실행 모드를 다룬다. 3 개 스킬: `tdd` `characterize` `autopilot`. tdd·characterize 는 `.agent-state.yml` 의 모드 플래그를 토글하고 prompts/* 의 거동을 바꾸며, autopilot 은 단일 feature 를 자동 순차 진행하는 opt-in 예외 모드다.

> 두 모드 동시 활성 시 — `tdd: true` + `mode: characterize` 면 **characterize 가 우선** (Red 계약 대신 Characterization Contract) (`pilot/skills/characterize/SKILL.md:54`, `pilot/skills/tdd/SKILL.md:13`).

---

## `/pilot:tdd`

TDD 모드를 사후 활성화·비활성화·정합성 보정·상태 보고한다. 4 분기: `on` / `off` / `--fix` / 인자 없음 (`pilot/skills/tdd/SKILL.md:3-7`).

> 신규 프로젝트를 TDD 로 시작할 때는 `/pilot:project {PROJECT} --tdd` 사용 (`pilot/skills/tdd/SKILL.md:12`).

- **사전 확인**: P1 — `{PROJECT}` 획득 (`pilot/skills/tdd/SKILL.md:15-18`).
- **`on` — 활성화** (`pilot/skills/tdd/SKILL.md:22-34`): state `tdd: true` 면 idempotent 종료. 아니면 `tdd-activation.md` §1-1b (백업 마커 주입) → §1~6 위임. 각 단계 idempotent.
- **`off` — 비활성화** (`pilot/skills/tdd/SKILL.md:38-50`): state `tdd: false` 면 idempotent 종료. 아니면 `tdd-activation.md` `## 비활성화 절차` off-1~off-7 위임 (백업 마커에서 표준 흐름 복원, 마커 부재 시 template fallback + INFO).
- **`--fix` — 3-way 정합성 보정** (`pilot/skills/tdd/SKILL.md:54-68`): state `tdd:` 값을 진실로 간주. state ↔ project.md TDD 분기 (`### 1. Planner — Red 계약 작성` literal) ↔ prompts 3종 TDD 섹션 literal 을 검증하고, state 값 기준으로 on/off 절차 재실행 (idempotent).
- **인자 없음 — 상태 보고** (`pilot/skills/tdd/SKILL.md:72-92`): 위 3-way 각각의 상태를 `ON|OFF|INCONSISTENT` 로 출력. 불일치 시 `--fix` 안내. Detect literal — planner: `## TDD — Red 계약` / generator: `> **TDD 모드**: Red 작성` / evaluator: `## TDD 테스트 실행`.
- **수정 대상 파일**: `.agent-state.yml`, `project.md`, `prompts/{planner,generator,evaluator}.md`.
- **참조 문서**: `pilot/skills/context/modes/tdd-activation.md` (활성화·비활성화 절차 SSOT) · `rgr.md` (Red-Green-Refactor).

---

## `/pilot:characterize`

레거시 코드의 현재 동작을 spec 으로 포착하는 characterization 모드 전환 (`pilot/skills/characterize/SKILL.md:10`).

- **인자** (`pilot/skills/characterize/SKILL.md:14`): `(빈 문자열)` 또는 `on` → ON, `off` → OFF.
- **사전 확인**: P1 — `{PROJECT}` 획득 (`pilot/skills/characterize/SKILL.md:18-22`).
- **동작** (`pilot/skills/characterize/SKILL.md:34-49`):
  1. `workspace/projects/{PROJECT}/.agent-state.yml` Read.
  2. 파일 없거나 schema < `v1.1` → "프로젝트 상태 파일 누락 또는 구버전. `/pilot:doctor --fix` 실행 후 재시도" 출력 후 종료.
  3. 모드 전환 — **on**: `mode: characterize` 라인 추가 (기존 `mode:` 키 있으면 값 교체) / **off**: `mode:` 라인 제거 또는 `mode: null`.
  4. 결과 안내 — `mode: {characterize|null}`, `tdd: {true|false}` 표시 + 참조 `${CLAUDE_PLUGIN_ROOT}/skills/context/modes/characterize.md`.
- **주의** (`pilot/skills/characterize/SKILL.md:52-56`):
  - `tdd: true` + `mode: characterize` 동시 → characterize 우선.
  - **Characterization 사이클 중 `{source_root}` 수정은 `scope-guard.sh` 훅이 Edit/Write 시점에 차단**하고, Evaluator 가 `git diff` 로 재검증. 리팩터하려면 먼저 `/pilot:characterize off` 로 복귀.
  - 정본 절차는 `pilot/skills/context/modes/characterize.md`. 본 스킬은 **상태 전환 명령** 일 뿐 절차 정의가 아님.

---

## `/pilot:autopilot`

이미 명세가 존재하는 **단일 feature** 를 planner→critic→generator→evaluator 로 자동 순차 진행하는 감독형 자율 모드 (`pilot/skills/autopilot/SKILL.md:13-15`). 기본 흐름은 사용자가 각 에이전트를 명시 호출하는 것이고, 이 스킬은 그 마찰을 줄이는 **opt-in 예외 모드**다.

- **인자**: feature 번호 (예: `03` 또는 `3`) — 2자리 zero-pad. feature 부재 시 hard-stop (`pilot/skills/autopilot/SKILL.md:17·38-41`).
- **사전 확인**: P1 (`pilot/skills/autopilot/SKILL.md:28-33`).
- **재개 확인** (`pilot/skills/autopilot/SKILL.md:47-65`): `{NN}-{slug}.auto.md` 감사 로그가 이미 있으면 마지막 상태를 보여주고 재개/처음부터/취소 1회 질의. 응답 전 진행 금지.
- **자동 진행 절차** (`pilot/skills/autopilot/SKILL.md:69-137`): 각 단계 후 `auto_pilot.py` 가 반환한 `kind` 로만 분기 (**스킬이 직접 신호를 해석하지 않는다**):
  1. planner → `plan-validate.py` 결과로 `--plan-valid` 판정. 실패 → STOP.
  2. critic → 챌린지 0건 proceed / suggestion·nit 만 reflect (planner 재호출 + 합의 표) / **blocking → STOP** (사람 판단).
  3. generator → 신호 없음, 실패 시 STOP (agent-error).
  4. evaluator → READY done / NOT_READY 재시도 (`{R}` 반드시 +1, MAX_RETRIES=1) / 소진·파싱 실패 STOP.
- **감사 로그** (`pilot/skills/autopilot/SKILL.md:141-159`): 매 전이마다 `{AUTO_LOG}` 에 타임라인 1줄 append. 새 실행은 `## Run N — {날짜}` 섹션.
- **제약** (`pilot/skills/autopilot/SKILL.md:179-190`): opt-in 예외 모드 · 신호 파싱 실패는 추측 없이 hard-stop · 재시도 정확히 1회 (generator 재진입) · 단일 feature 단위 (다수 연속 진행 미지원). feature 생성·명세는 `/pilot:create-feature`·`/pilot:analyze` 담당.
