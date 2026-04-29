# #00 회귀 골든 픽스처 — 0b 단계 (`_input/` + `expected/` 캡처)

> source: features/00-regression-fixture.md · 직전 plan 협상 (옵션 C — plan 만 저장, generator 호출은 별도 세션)
> mode: standard (tdd: false)
> planner_at: 2026-04-29

## 사전 결정 사항 (직전 turn 협상 결과)

본 plan 은 사용자가 다음 결정을 확정한 뒤 작성한다 — generator 가 추가 질의 없이 그대로 실행 가능.

- **옵션 C**: plan 만 저장. 본 turn 에서 generator 자동 진행 금지. 사용자가 다른 세션에서 `@generator` 호출 시점 결정.
- **Open Q #2 (Stage 1 정의 재해석)**: Stage 1 = "v0.2.0 + config-post-accepted (마이그레이션 후 default 주입된 상태)". v0.1.0 ↔ v0.2.0 byte-diff 0 의 원래 약속은 D10 default 폐지로 의미가 달라졌으므로 **현재 v0.2.0 의 마이그레이션 accepted 상태를 baseline 으로 캡처**한다. v1.0 기준선이 아닌 v0.2.0 기준선.
- **Open Q #3 (diff.sh 단순화)**: timestamp/UUID 정규화 placeholder 도입 보류. `diff.sh` 는 `--actual {dir}` 인자를 받아 `_input/` 으로 세 스킬 (`/pilot:learn` `/pilot:project` `/pilot:analyze`) 를 재실행한 결과 디렉터리와 `expected/` 를 단순 `diff -ru` 로 비교. timestamp 류 정규화는 v1.1 milestone.
- **Open Q #4 (analyze 토이 docs)**: `_input/python-sample/docs/sample-spec.md` 1 개 추가 — `/pilot:analyze` 가 docs/ 트리를 발견하고 scope 표에 반영하는 흐름 회귀.
- **Open Q #5 (`__init__.py` 무시)**: `_input/python-sample/services/__init__.py` 같은 빈 파이썬 패키지 마커는 `Ignore` 패턴 (`*/__init__.py`) 으로 일괄 제외 — config 표 의존성 노이즈 제거.
- **에이전트 간 전달사항 14 건 전부 이월**: project.md `## 에이전트 간 전달사항` 의 미처리 항목 전부 owning future feature 의 planner 가 처리. 본 0b plan 범위 외. 본 turn 은 체크리스트 갱신도 하지 않는다 (이월 결정 자체가 사용자 명시).

## 범위 — 0b 만

- **포함**: `_input/python-sample/` 더미 코드베이스, `learn/expected/`·`project/expected/`·`analyze/expected/` 캡처, `diff.sh` 본 구현, `README.md` 재생성 절차.
- **제외**: `config/` 5 fixture (이미 0a 에서 완료). Stage 2 (config override 거동) — v1.1 milestone. timestamp 정규화 — v1.1.

## 변경 파일

### 신설 — `_input/python-sample/` (더미 입력 코드베이스, 의존성 0)

- [x] `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/` — 진입 폴더
- [x] `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/main.py` — entry point (1 도메인 단일 import, 5~10 줄)
- [x] `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/models/user.py` — 단순 dataclass 모델
- [x] `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/models/order.py` — 단순 dataclass 모델
- [x] `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/services/auth.py` — User import 의존
- [x] `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/services/checkout.py` — Order + auth 의존
- [x] `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/services/__init__.py` — 빈 패키지 마커 (Ignore 처리됨)
- [x] `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/docs/sample-spec.md` — analyze 가 발견할 토이 spec 1 개 (1~2 H2)
- [x] `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/.gitignore` — `__pycache__/` 등 표준 exclude

> **의존성 0 원칙**: 외부 라이브러리 import 금지. dataclass · typing 만 사용. `pip install` 없이 import 가능.

### 신설 — `learn/expected/` 캡처 (v0.2.0 마이그레이션 accepted 상태)

- [x] `pilot/tests/fixtures/v0.1.0-baseline/learn/expected/MANIFEST.md` — `/pilot:learn _input/python-sample/main.py` 산출 MANIFEST (도메인 분류 표 1 행)
- [x] `pilot/tests/fixtures/v0.1.0-baseline/learn/expected/python-sample/index.md` — 도메인 진입 파일
- [x] `pilot/tests/fixtures/v0.1.0-baseline/learn/expected/python-sample/inventory.md` — Phase 2 결과 (의존성 추적 + 역할 분류 표)
- [x] `pilot/tests/fixtures/v0.1.0-baseline/learn/expected/config.md` — 마이그레이션 accepted 후 v0.1.0 default 행 주입된 상태

> **D10 영향**: `learn/expected/config.md` 의 `## learn 언어 패턴` 두 표는 빈 헤더가 아니라 v0.1.0 default 5 언어 행이 마이그레이션 결과 주입된 상태로 캡처 (Open Q #2 결정).

### 신설 — `project/expected/` 캡처

- [x] `pilot/tests/fixtures/v0.1.0-baseline/project/expected/projects/python-sample/project.md` — `/pilot:project python-sample` 산출. `## 관련 파일` 의 H3 (Models · Services) 가 #03 에 의해 동적 생성된 상태. (Endpoints H3 는 docs 만 있고 라우트 패턴 없으므로 부재).
- [x] `pilot/tests/fixtures/v0.1.0-baseline/project/expected/projects/python-sample/prompts/planner.md` — analyze-managed 영역 비어있음 (analyze 미실행 상태)
- [x] `pilot/tests/fixtures/v0.1.0-baseline/project/expected/projects/python-sample/prompts/generator.md`
- [x] `pilot/tests/fixtures/v0.1.0-baseline/project/expected/projects/python-sample/prompts/evaluator.md`

### 신설 — `analyze/expected/` 캡처

- [x] `pilot/tests/fixtures/v0.1.0-baseline/analyze/expected/projects/python-sample/project.md` — analyze 5-2 적용 후. `## 관련 파일` Models · Services H3 표가 scope 카테고리 lookup 결과로 채워짐.
- [x] `pilot/tests/fixtures/v0.1.0-baseline/analyze/expected/scope/python-sample.md` — scope 분류 산출
- [x] `pilot/tests/fixtures/v0.1.0-baseline/analyze/expected/projects/python-sample/.agent-state.yml` — `analyzed: true`, `last_analyzed_features: 0`, `plugin_version: 0.2.0` (timestamp 는 placeholder 가 아니라 캡처 시점 그대로 — Open Q #3 결정)

### 신설 — `diff.sh` 본 구현 + `README.md`

- [x] `pilot/tests/fixtures/v0.1.0-baseline/diff.sh` — 단순 `--actual {dir}` 인자 비교 도구 (Open Q #3)
- [x] `pilot/tests/fixtures/v0.1.0-baseline/README.md` — 재생성 절차 1 페이지 (Open Q #2 의 v0.2.0 baseline 정의 명시)

### 갱신 — workspace/context 또는 .gitignore (Ignore 패턴)

- [x] `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/.gitignore` 에 `*/__init__.py` 1 줄 추가 — diff.sh 가 fixture 재실행 시 빈 패키지 마커가 expected 와 비교되지 않도록. (또는 diff.sh 안에서 `--exclude=__init__.py` 플래그 명시. 본 plan 은 .gitignore 방식 채택 — git 추적도 동시에 배제하여 깔끔.)

> **Ignore 정책 위치 결정**: `_input/python-sample/.gitignore` 에 명시. `workspace/context/config.md` 의 Ignore 섹션은 도메인별 산출 학습용이라 fixture 입력에는 부적합.

## 구현 순서

1. **`_input/python-sample/` 더미 코드베이스 작성** — 의존성 0 원칙 준수. main → services → models 단방향 import 그래프. `docs/sample-spec.md` 도 함께 추가. `__init__.py` 는 빈 파일.
2. **`.gitignore` 작성** — `__pycache__/`, `*/__init__.py` 등 fixture 입력에서 무시할 패턴.
3. **v0.2.0 환경에서 `/pilot:learn _input/python-sample/main.py` 수동 실행** — 산출물을 `learn/expected/` 로 복사. 마이그레이션 prompt 발화 시 `accepted` 선택 → config.md 에 default 주입된 상태 캡처.
4. **`/pilot:project python-sample` 수동 실행** — 산출물을 `project/expected/` 로 복사. `## 관련 파일` H3 동적 생성 거동 검증.
5. **`/pilot:analyze` 수동 실행** — 산출물을 `analyze/expected/` 로 복사. scope 카테고리 lookup 거동 검증.
6. **`diff.sh` 작성** — `--actual {dir}` 인자 받아 `expected/` 와 `diff -ru`. exit 0 = 회귀 없음, exit 1 = diff. timestamp 정규화는 v1.1.
7. **`README.md` 작성** — 재생성 절차 1 페이지: `(a)` v0.2.0 환경에서 빈 workspace 준비 `(b)` `_input/` 으로 세 스킬 cycle `(c)` 산출물을 `expected/` 로 복사 `(d)` 커밋. **Stage 1 정의 = v0.2.0 + config-post-accepted** 를 README 에 명시 (Open Q #2 결정).
8. **수동 회귀 1 회 실행** — `bash diff.sh --actual /tmp/regen` 으로 즉시 재실행한 결과가 captured 와 diff 0 인지 확인. 차이 발생 시 캡처 재현성 보장 위해 절차 보정.

## 주의사항

- **현재 plugin 환경 = v0.1.0** — `pilot/.claude-plugin/plugin.json` 이 0.1.0. 본 0b 작업은 **v0.2.0 환경에서 수행해야** 마이그레이션 prompt 가 발화하고 D10 의 자동 주입 동작이 캡처 가능. 0b 시작 전 version bump 선결 필요. (전달사항 #91 의 (a) 항목 = version bump 가 0b 의 사전 조건 — 단 본 plan 은 14 건 이월 결정에 따라 version bump 자체를 본 feature 작업으로 포함하지 **않는다.** 0b generator 진입 시 version bump 가 선행되어 있어야 함을 README·protocol 차원에서 사용자/다음 planner 가 별도 처리).
- **timestamp 정규화 보류** — `.agent-state.yml` 의 `analyzed_at` 같은 timestamp 는 캡처 시점 그대로 두고 `diff.sh` 는 단순 비교. v1.1 milestone 에서 placeholder 정규화 도입 시 expected 도 일괄 갱신 (Open Q #3).
- **`__init__.py` 노이즈 제거** — `.gitignore` 의 `*/__init__.py` 가 fixture 입력에서 빈 파일을 배제. learn 의 의존성 추적이 dunder 마커를 잘못 분석하지 않도록.
- **Stage 2 보류** — config override 거동 (사용자가 자기 패턴 정의했을 때) 캡처는 v1.1 milestone. 본 0b 는 Stage 1 (마이그레이션 accepted 후 default 주입) 만.
- **OS-specific path 구분자**: macOS (`/`) 기준. Windows 호환은 v1 외.
- **#03 SSOT 분리 검증 부산물**: `project/expected/` 캡처와 `analyze/expected/` 캡처의 `## 관련 파일` H3 비교 시, project 단계에서 H3 헤더 (Models · Services) 만 있고 빈 표, analyze 단계에서 표 본문이 채워진 형태가 정상. 차이 발생 시 #03 의 SSOT 분리 (H3 헤더 = project 1 회 생성 / 표 본문 = analyze 매번 갱신) 가 깨진 것.
- **에이전트 간 전달사항 14 건 = 본 0b 범위 외** — 사용자 결정으로 전부 이월. owning feature 별 후속 planner 가 처리.

## 교차 의존

- **#01·#02·#03·#04·#05 (모두 `[x]` 완료)**: 본 0b 는 다섯 feature 의 산출물을 회귀 검증한다. v0.2.0 환경에서 캡처한 expected 가 향후 동일 입력으로 재현되어야 byte-diff 0. 다섯 feature 의 어느 하나가 거동 변경 시 본 fixture 의 expected 도 함께 갱신 필요.
- **plugin.json version bump (0.1.0 → 0.2.0)**: 본 0b 의 사전 조건. 14 건 이월 결정에 따라 version bump 자체는 별도 feature/PR 로 분리. 0b generator 진입 시 v0.2.0 환경이 보장되어야 함.

## focus 반영 사항

`.focus.md` 의 D10 결정 (default 표 폐지 + 자동 마이그레이션) 은 본 0b 의 baseline 정의에 직접 영향:

- `learn/expected/config.md` 는 **빈 표 + INFO** 가 아닌 **마이그레이션 accepted 후 default 주입된 상태** 로 캡처 (Open Q #2 의 Stage 1 재해석과 일치).
- `learn/expected/.agent-state.yml` 은 `migration_v0_2_0: accepted`, `plugin_version: 0.2.0` 포함.
- doctor 가 빈 표 INFO 와 채워진 표 PASS 를 모두 정상 처리하는 거동은 0a 의 `config/pass-empty` 와 `config/pass-valid` fixture 가 이미 검증. 0b 는 마이그레이션 accepted 분기만 캡처.

D10 의 8~10 곳 변경은 #01·#04·#05 generator 가 이미 적용 완료 (project.md `## 목표` 의 [x] 체크 상태). 본 0b 는 그 결과를 회귀 픽스처로 고정.
