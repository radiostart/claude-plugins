# TDD 활성화 절차 (SSOT)

이 문서는 `/pilot:project --tdd` 와 `/pilot:tdd` 양쪽에서 참조되는 공통 절차다.
대상 프로젝트는 호출자가 결정한다. 이 문서에서는 `{PROJECT}` 로 표기한다.

모든 단계는 **idempotent** 하다. "이미 존재함" 판별 기준은 각 단계의 **Detect literal** 로 명시한다. 해당 literal 이 파일에 이미 있으면 그 단계를 생략한다.

대상 파일:

- `workspace/projects/{PROJECT}/project.md`
- `workspace/projects/{PROJECT}/agents/planner.md`
- `workspace/projects/{PROJECT}/agents/generator.md`
- `workspace/projects/{PROJECT}/agents/evaluator.md`

---

## 1. `project.md` 수정

### 1-1. `## 제한사항` 에 TDD 문구 추가 (중복 방지)

**Detect literal:** `- **TDD 모드**:` (제한사항 섹션 내 문자열 포함 여부로 판단)

이미 있으면 생략한다. 없으면 아래 항목을 추가한다:

```markdown
- **TDD 모드**: 테스트 없이 프로덕션 코드를 작성하지 않는다. Planner 는 Red 계약 (스텝 분할 + 테스트 경로·검증 행동·기대 실패 유형) 만 남기고, Generator 가 **Red 작성·실패 확인 → Green → Refactor** 를 한 컨텍스트에서 순환한다. Evaluator 는 `.plan.md` 의 Red 증거 교차 검증 + **변경 관련 테스트만** 실행한다.
```

### 1-2. `## 에이전트 호출 흐름` 을 TDD 버전으로 교체

**Detect literal:** `### 1. Planner — Red 계약 작성` (`## 에이전트 호출 흐름` 섹션 내 포함 여부로 판단)

이미 있으면 생략한다. 없으면 기존 `## 에이전트 호출 흐름` 섹션을 아래 구조로 교체한다.

```markdown
## 에이전트 호출 흐름

**순서를 반드시 준수한다. 이전 단계 완료 전 다음 단계로 진행하지 않는다.**

### 1. Planner — Red 계약 작성 (테스트 코드 X)

- **진입 조건:** 새 기능 구현 시작 시 항상 실행
- **로드:** `agents/planner.md` + [`rgr.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/modes/rgr.md)
- **산출물:** `.plan.md` 에 스텝별 3 축 기록 — (a) 테스트 대상 경로 · (b) 검증할 행동 · (c) 기대 실패 유형
- **완료 기준:** 스텝 목록과 Red 계약 3 축 확정 → Generator 진행
- **금지:** 테스트 코드 작성 — Generator 담당

### 2. Generator — Red + Green + Refactor 순환

- **진입 조건:** Planner 의 Red 계약 확정 후
- **로드:** `agents/generator.md` + [`coding.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/coding.md) + [`rgr.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/modes/rgr.md) + workspace `conventions_doc` (`orchestrate-load` 자동 주입)
- **동작:** 스텝마다 Red → Green → Refactor 를 한 컨텍스트에서 순환. 각 스텝의 `.plan.md` 에 `[Red] 실패 유형·메시지` / `[Green] 통과 시각` / `[Refactor] 수정 내역` 을 Edit 로 기록.
- **완료 기준:** 모든 스텝 [Red]+[Green] 증거 기록 + 직전 `{test_command}` 전체 PASS + `{source_root}` 1 개 이상 수정 → Evaluator 진행

### 3. Evaluator — Red 증거 교차 검증 + 변경 관련 테스트 실행

- **진입 조건:** Generator 완료 후
- **로드:** `agents/evaluator.md`
- **동작:** `{test_command} {변경 관련 경로}` 실행 + `.plan.md` 스텝별 [Red]+[Green] 증거 교차 검증. 증거 누락·"인프라 오류" 기록 스텝 발견 시 Generator 에 반려.
- **완료 기준:** 변경 관련 테스트 통과 + Red 증거 교차 검증 통과 + 요구사항 체크리스트 확인 → 목표의 해당 항목 완료 처리 + VERIFICATION REPORT `status: READY` 출력
- **금지:** 인자 없는 `{test_command}` (전체 스위트) 실행 금지 — 반드시 변경된 테스트 경로를 나열
```

---

## 2. `agents/planner.md` — TDD Red 계약 단계 추가

**Detect literal:** `## TDD — Red 계약`

파일 **말미에** 아래 섹션을 추가한다. literal 이 이미 있으면 생략한다.

```markdown
---

## TDD — Red 계약

이 프로젝트는 TDD 모드다. Planner 는 Red 계약만 남긴다 — **테스트 코드는 작성하지 않는다**. 스텝별 3 축 (테스트 경로 · 검증할 행동 · 기대 실패 유형) 을 `.plan.md` 에 기록한다. 상세: [`rgr.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/modes/rgr.md) 의 `Planner — Red Contract` 절 (래퍼가 자동 로드).
```

---

## 3. `agents/generator.md` — TDD 모드 안내 추가

**Detect literal:** `> **TDD 모드**: Red 작성`

파일 **최상단(첫 줄 앞)** 에 아래 안내를 추가한다. literal 이 이미 있으면 생략한다.

```markdown
> **TDD 모드**: Red 작성·실패 확인 → Green (최소 구현) → Refactor 를 한 컨텍스트에서 순환한다.
> Planner 가 남긴 `.plan.md` 의 Red 계약을 따라 spec 을 직접 작성·실행한다. 각 스텝의 `[Red][Green][Refactor]` 증거를 `.plan.md` 에 Edit 로 기록 (텍스트 보고만 금지). 상세 절차는 [`rgr.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/modes/rgr.md) 의 `Generator — Red + Green + Refactor` 절을 따른다 (래퍼가 자동 로드).
```

---

## 4. `agents/evaluator.md` — TDD 테스트 실행 섹션 추가

**Detect literal:** `## TDD 테스트 실행`

파일 **최상단(첫 줄 앞)** 에 아래 섹션을 추가한다. literal 이 이미 있으면 생략한다.

```markdown
## TDD 테스트 실행

이 프로젝트는 TDD 모드다. (1) 변경 관련 테스트 실행 + (2) `.plan.md` 스텝별 `[Red]+[Green]` 증거 교차 검증. 증거 누락·"인프라 오류" 기록 스텝 발견 시 Generator 에 반려. 상세 절차는 [`rgr.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/modes/rgr.md) 의 `Evaluator — 실행 및 검증` 절을 따른다. 실행 대상 테스트 경로는 이번 feature 의 `plan.md` 에서 확인한다 (인자 없는 전체 스위트 실행 금지). 실제 명령 문자열은 `workspace/context/config.md` 의 `{test_command}` 값.

---
```

---

## 5. `.agent-state.yml` — `tdd: true` 갱신

**Detect literal:** `tdd: true`

`workspace/projects/{PROJECT}/.agent-state.yml` 을 Read 후:

- `schema` 가 지원 버전(`v1.1`, `v1.2`) 이 아니거나 파일 없음 → 에러 출력: **"프로젝트 상태 파일 누락 또는 구버전. `/pilot:doctor --fix` 실행 후 재시도하세요."**
- `tdd: true` 이미 있으면 생략.
- 없으면 `tdd: false` 를 `tdd: true` 로 Edit.

이 단계를 통과해야 wrapper (`@planner`·`@generator`·`@evaluator`) 가 TDD 분기로 동작한다. 스키마 상세: [state-schema.md](../lifecycle/state-schema.md).

---

## 6. 무결성 검증 (자동)

TDD 활성화 완료 후 아래를 실행한다:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace
```

- ERROR / WARN 있으면 **원문 그대로** 출력.
- 모두 PASS 면 `doctor: all checks passed`.

---

## 완료 후 요약 출력

호출자는 아래 항목을 요약해 사용자에게 안내한다.

- 수정된 파일: `project.md`, `agents/planner.md`, `agents/generator.md`, `agents/evaluator.md`, `.agent-state.yml`
- 참조 문서: `skills/context/modes/rgr.md`, `skills/context/lifecycle/state-schema.md`
