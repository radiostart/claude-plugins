# #07 analyze SKILL.md scope/{domain}.md 생성 절차 명시

> source: v0.2.1 hotfix discovery (NS #5 cycle, 2026-04-29) — hotfix 후보 #3

## 요구사항

- **조건**: NS #5 cycle 시뮬레이션에서 `pilot/skills/analyze/SKILL.md` 의 5-2 단계가 "scope 파일 있으면 읽고 없으면 skip" 만 정의함을 발견. 그러나 회귀 픽스처 expected (`pilot/tests/fixtures/v0.1.0-baseline/analyze/expected/scope/python-sample.md`) 는 scope 가 생성된 상태를 가정. analyze 가 어느 단계에서 어떤 입력으로 scope 파일을 새로 만드는지 SKILL.md 본문 trace 불가.
- **트리거**: `/pilot:analyze {도메인}` 호출 + `workspace/context/scope/{domain}.md` 부재 + MANIFEST 진입파일에 표 헤더 (`## Routes`·`## Models`·`## Services` 또는 config 의 `scope 헤더` 컬럼 값) 존재.
- **기대결과**: analyze 가 부재 시 scope 파일을 새로 **생성**. 표 본문은 MANIFEST 진입파일 (`workspace/context/{domain}/index.md` 등) 또는 learn 산출 (`inventory.md`) 에서 추출. 헤더 = config 의 `scope 헤더` 컬럼.

## 비즈니스 규칙

- **scope 파일 생성 트리거**:
  - `workspace/context/scope/{domain}.md` 부재 (또는 빈 파일)
  - MANIFEST 진입파일 (`workspace/context/{domain}/index.md`) 또는 learn 의 `inventory.md` 에 config 의 `scope 헤더` 값과 일치하는 H2 헤더 존재
  - 위 둘 만족 시 analyze 가 scope 파일을 자동 생성
- **scope 파일 본문 구성**:
  - H2 헤더 = config 의 `scope 헤더` 컬럼 값 그대로 (예: `## Routes`·`## Models`·`## Services`)
  - 표 헤더 = config 의 `표 헤더` 컬럼 값 (예: `엔드포인트, Method, 목적`)
  - 표 본문 = learn `inventory.md` 의 역할 분류 표에서 해당 카테고리 추출. 예: `## Routes` → 역할 = `routes` 행들. `## Models` → 역할 = `models` 행들.
  - 각 행에 `(file:line)` 인용 포함 (learn 산출의 file:line 그대로 복사).
- **본문 추출 우선순위**:
  - 1순위: `inventory.md` 역할 분류 표 (learn 산출)
  - 2순위: `index.md` 본문의 표 (사용자 수동 정의 가능성)
  - 3순위: 본문 추출 실패 → 표 헤더만 있는 빈 표 + INFO 1 줄 (`scope/{domain}.md 표 본문 추출 실패 — 사용자 수동 채움 권장`)
- **5-2 단계와 정합**: 본 절차 = 5-1 또는 5-2 진입 직전 단계로 분리. 5-2 의 "scope/{domain}.md 의 표를 추출해 project.md 에 기입" 룰은 그대로 유지 — 본 단계가 scope 파일을 만들면 5-2 가 정상 동작.
- **A2 runtime fallback 정합**: scope 파일 생성 실패 (본문 추출 실패) → 빈 표 + INFO + 5-2 진행 (abort 안 함). 사용자 수동 채움 후 다음 analyze 호출 시 5-2 가 정상 추출.
- **idempotency**: 두 번째 analyze 호출 시 scope 파일이 이미 존재 → 새로 만들지 않음. 기존 파일 그대로 사용 (사용자 수동 추가·교정 보존).
- **사용자 수동 보존**: 사용자가 직접 작성한 scope/{domain}.md 행 (자동 생성 행 외) 도 그대로 보존. 자동 갱신은 별도 옵션 (`/pilot:analyze --regen-scope` v2 외).

## 예외 케이스

- **MANIFEST 진입파일 부재**: scope 파일 생성 안 함 + INFO 1 줄 (`MANIFEST 진입파일 없음 — scope 파일 생성 skip`). 5-2 도 skip.
- **config 의 `## scope 카테고리` 빈 표**: features/02 의 default 매핑 (Routes/Models/Services → Endpoints/Models/Services) 사용. scope 파일 헤더도 default 따라 작성.
- **learn 산출 `inventory.md` 부재**: 1순위 추출 실패. 2순위 (`index.md`) 또는 3순위 (빈 표 + INFO) 적용.
- **scope 헤더 컬럼 값이 `## ` prefix 미준수**: features/04 의 doctor 검증이 사전 차단 (ERROR). 본 단계 진입 자체가 안 됨 — A2 fallback 으로 default 적용.
- **여러 도메인 동시 analyze** (`/pilot:analyze --multi-domain`): v2 외. 본 v0.3.0 은 단일 도메인만.

## 관련 파일 범위

- **변경**: `pilot/skills/analyze/SKILL.md`
  - 5-2 직전에 신규 단계 5-1.5 또는 5-1 본문 보강: "scope/{domain}.md 부재 + MANIFEST 표 헤더 존재 → 자동 생성 절차" 1 단락 추가.
  - 본문 추출 우선순위 (inventory.md → index.md → 빈 표 fallback) 명시.
  - idempotency 룰 명시 (기존 파일 보존).
- **단위 테스트 (선택, 본 v0.3.0 에는 미포함)**: scope 자동 생성 함수가 추가되면 테스트 신설. 단 본 v0.3.0 은 SKILL.md 본문 보강만 — LLM 절차 따르기로 검증.
- **회귀 픽스처**: `pilot/tests/fixtures/v0.1.0-baseline/analyze/expected/scope/python-sample.md` 가 본 단계의 expected 산출. 본 v0.3.0 변경 후 cycle 재실행 시 동일 파일 byte-clean 산출 검증.
- **사용자 영향**: 0 ~ 미미. v0.2.x 에서도 LLM 이 사실상 scope 파일을 만들고 있었음 (NS #5 cycle 검증 결과). 본 변경은 그 거동의 명문화.
