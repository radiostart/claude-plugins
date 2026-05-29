# `/pilot:auto` — 감독형 자율 오케스트레이터 설계

- 작성일: 2026-05-29
- 상태: 설계 승인됨 (구현 전)
- 대상: pilot 플러그인 (`/Users/jay-p/Projects/claude-plugins/pilot/`)

## 1. 배경 & 문제

현재 pilot 의 feature 진행은 사용자가 `@pilot-planner → @pilot-planner-critic → @pilot-generator → @pilot-evaluator` 를 **수동으로** 순차 호출한다. 이는 의도된 설계다 — README 와 `docs/explanation/agent-flow.md` 에 "각 에이전트는 사용자가 명시 호출한다 — 자동 파이프라인이 아니라 phase 사이 개입 가능한 흐름"이라고 명시돼 있다.

문제: 저위험·소규모 feature 에서 4회 수동 호출은 반복 마찰이다. 이 마찰만 줄이되 pilot 의 "개입 가능" 철학은 버리지 않는, **감독형 자율(supervised autonomy)** 모드를 추가한다.

## 2. 목표 & 비목표

**목표**
- feature 명세가 이미 존재하는 상태에서 planner→evaluator 를 자동 순차 진행
- 위험 신호(hard-stop)에 걸리면 즉시 사람에게 제어 반환
- 모든 자동 결정을 감사 가능하게 로그로 남김
- 기존 4개 에이전트 내부는 **변경하지 않음**

**비목표**
- 완전 자동(사람 개입 0) — 명시적으로 제외
- 다수 feature / 프로젝트 전체 연속 진행 — 이번 범위 밖 (단일 feature 단위)
- evaluator NOT_READY 무한 재시도 — 정확히 1회로 제한
- `/pilot:doctor` 의 `NN.auto.md` 정합성 점검 — 추후 과제

## 3. 핵심 설계 결정 요약

| 항목 | 결정 |
|---|---|
| 자율성 수준 | 감독형 자율 (hard-stop 시 사람에게 반환) |
| 실행 범위 | 단일 feature (이미 생성된 feature 대상) |
| 진입점 | 새 스킬 `/pilot:auto NN` |
| critic 처리 | 항상 실행. suggestion/nit → planner auto-reflect, blocking → hard-stop |
| 재시도 | NOT_READY 시 generator 재진입 1회, 그 후에도 NOT_READY 면 STOP |
| 재시도 대상 | 항상 generator (planner 아님) |
| Hard-stop | ① 재시도 소진(NOT_READY 지속) ② critic blocking ③ plan-validate 실패 |
| 감사 로그 | `features/NN-{slug}.auto.md` (feature 단위 SSOT) |
| 재개 | 멈춘 뒤 재호출 시 1회 확인 후 이어감 |
| 신호 파싱 실패 | 항상 STOP (추측 금지) |

## 4. 아키텍처

### 4.1 오케스트레이션 모델

`/pilot:auto` 는 **얇은 오케스트레이터**다. pilot 의 "플러그인은 메커니즘만, 도메인 판단은 에이전트가" 원칙을 지킨다.

- 스킬 자체는 **상태 기계 전이 규칙**만 보유. 도메인 판단을 하지 않는다.
- 기존 4개 에이전트를 그대로 순차 호출한다. 에이전트 내부는 미변경.
- 각 에이전트가 산출하는 **머신리더블 신호**만 읽어 다음 전이를 결정한다:
  - `plan-validate.py` exit code
  - `.plan.critic.md` 의 챌린지 severity 목록
  - evaluator VERIFICATION REPORT 의 `status` (READY | NOT_READY)

**경계 원칙:** 오케스트레이터는 "이 챌린지가 타당한가", "요구사항 충족했나" 같은 판단을 절대 하지 않는다. 그 판단은 각 에이전트의 책임이고, 오케스트레이터는 그들이 내놓은 신호만 보고 전이한다.

### 4.2 흐름도

```
/pilot:auto NN
   │
   ├─[진입 검증] feature NN 존재? ──NO──► ❌ STOP "feature NN 없음"
   │                              YES
   │              NN.auto.md 존재? ──YES──► 재개 확인 (1회): 재개/처음부터/취소
   │
   ├─[1] @pilot-planner ───────────► NN.plan.md
   │        └─ plan-validate.py ──FAIL──► ❌ STOP (hard-stop ③)
   │                              PASS
   ├─[2] @pilot-planner-critic ───► NN.plan.critic.md
   │        ├─ blocking 있음? ──YES──► ❌ STOP (hard-stop ②)
   │        └─ suggestion/nit ──► @pilot-planner 재호출로 auto-reflect → 합의표
   │
   ├─[3] @pilot-generator ────────► code diff
   │
   ├─[4] @pilot-evaluator ────────► VERIFICATION REPORT
   │        ├─ READY ──────────────► ✅ DONE
   │        └─ NOT_READY ──► [retry 1/1] @pilot-generator 재진입
   │                            └─ @pilot-evaluator ──► 또 NOT_READY ──► ❌ STOP (hard-stop ①)
   │                                                    READY ──► ✅ DONE
   │
   └─ 모든 전이 → NN.auto.md 에 로그
```

## 5. 컴포넌트

### 5.1 전이 결정 로직 (순수 함수)

실제 에이전트 호출과 분리된 순수 함수로 구현한다. pilot 의 기존 Python 도구 패턴(`tools/*.py`)을 따른다.

입력 신호 → 출력 액션 매핑:

| 입력 신호 | 출력 액션 |
|---|---|
| plan-validate exit != 0 | `stop` (reason: plan-validate) |
| critic severity 에 `blocking` 포함 | `stop` (reason: critic-blocking) |
| critic severity 가 suggestion/nit 뿐 | `reflect` (→ planner 재호출) |
| critic severity 파싱 불가 | `stop` (reason: signal-parse, blocking 으로 간주) |
| evaluator status == READY | `done` |
| evaluator status == NOT_READY, 재시도 잔여 | `retry` (→ generator) |
| evaluator status == NOT_READY, 재시도 소진 | `stop` (reason: retry-exhausted) |
| evaluator status 파싱 불가 | `stop` (reason: signal-parse) |
| 에이전트 호출 예외/빈 출력 | `stop` (reason: agent-error) |

출력 액션 집합: `proceed | reflect | retry | done | stop`

### 5.2 감사 로그 — `features/NN-{slug}.auto.md`

feature 단위 SSOT. `.agent-state.yml`(프로젝트 단위)과 섞지 않는다 — 레이어 분리 원칙.

구조 예시:

```markdown
# Auto-pilot Log: 03-user-deletion

## Run 1 — 2026-05-29
- [planner]  plan.md 작성 → plan-validate PASS
- [critic]   챌린지 3건 (suggestion 2, nit 1) → planner auto-reflect, 합의표 작성
- [generator] diff 생성 (4 files)
- [evaluator] NOT_READY (requirements: fail — soft-delete 누락)
- [retry 1/1] generator 재진입 → evaluator NOT_READY 지속
- ❌ STOP: 재시도 소진 (hard-stop ①)
  → 사람 판단 필요: requirements gate
```

각 phase 결과, 자동 결정과 근거, 재시도 횟수, 최종 stop 사유를 타임라인으로 기록한다.

### 5.3 상태 추적 & 재개

- 진행 상태의 SSOT 는 `NN.auto.md` 의 타임라인. `.agent-state.yml` 에 새 필드를 추가하지 않는다.
- `/pilot:auto NN` 재호출 시:
  - `NN.auto.md` 없음 → 처음부터 (planner)
  - 있음 → 마지막 phase 와 stop 사유를 읽고, 사람에게 **1회 확인**: ① 여기서 재개 ② 처음부터 ③ 취소
- 재개가 완전 자동이 아닌 이유: hard-stop 은 사람 판단이 필요했다는 뜻이고, 사람이 실제로 고쳤는지 오케스트레이터는 알 수 없다.

## 6. 에러 처리 & 경계 케이스

핵심 원칙: **"신호를 못 읽으면 멈춘다."** 머신리더블 신호 파싱 실패 시 추측 없이 항상 사람에게 넘긴다.

| 상황 | 처리 |
|---|---|
| feature 명세 없음 / 번호 오류 | 시작 전 검증 실패 → 즉시 STOP |
| 에이전트 호출 실패(예외/빈 출력) | 재시도 안 함 → STOP, "agent error" 기록 |
| `.plan.critic.md` severity 파싱 불가 | STOP (blocking 으로 간주) |
| evaluator REPORT status 파싱 불가 | STOP (NOT_READY 로 간주 안 함, 즉시 사람에게) |
| `.focus.md` 존재 | 그대로 둠. 에이전트가 기존대로 읽음. auto 가 지우거나 무시 안 함 |
| 이미 READY 인 feature 에 재실행 | 재개 확인에서 감지 → "이미 완료됨, 다시 할까요?" |

## 7. 테스트 & 검증

**전이 로직 단위 테스트** (실제 에이전트 호출 없이):
- plan-validate FAIL → stop
- critic blocking → stop / suggestion·nit 만 → reflect
- evaluator READY → done / NOT_READY → retry → NOT_READY → stop
- 신호 파싱 실패 → stop
- 재개 시 1회 확인

전이 결정을 순수 함수로 분리해 신호 입력 → 액션 출력만 검증한다.

**문서 정합성:**
- README / `docs/explanation/agent-flow.md` 에 "수동이 기본, auto 는 opt-in 예외 모드" 명시
- 기존 "명시 호출" 원칙과 충돌하지 않도록 auto 가 예외임을 문서화

## 8. 추후 과제 (이번 범위 밖)

- 다수 feature / 프로젝트 전체 연속 진행 (`--all`)
- `/pilot:doctor` 의 `NN.auto.md` 정합성 점검 (중단 방치 감지)
- 위험도 기반 게이팅 (저위험만 자동 허용)
- Slack 알림 연동 (기존 `slack-notify.py` 재사용)
