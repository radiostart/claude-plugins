# #04 doctor config 정합성 검증

> source: design-pilot-generic-2026-04-29.md

## 요구사항

- **조건**: `pilot/tools/doctor/integrity.py` 에 신규 검사 함수 추가. config.md 의 신규 섹션 (`## learn 언어 패턴`, `## scope 카테고리`) 의 스키마·헤더 화이트리스트 검증.
- **트리거**: `python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace` 또는 `/pilot:doctor` 호출. workspace 단계 검사 항목으로 추가.
- **기대결과**: 신규 섹션이 존재하면 스키마 검증 (컬럼 수·헤더 화이트리스트). 부재하면 INFO 1 줄 (WARN 아님 — backward-compat). 위반 시 ERROR + 수정 안내.

## 비즈니스 규칙

- **컬럼 수 강제**:
  - `## learn 언어 패턴` 의 첫 표 (의존성 추적): 정확히 2 컬럼 (`언어`, `의존성 추출 패턴`). 헤더 정확 일치. 행 수 0 허용 (D10 default 폐지로 빈 표 정상).
  - `## learn 언어 패턴` 의 두번째 표 (역할 분류) **long-form (D9 + D10)**: 정확히 2 컬럼 (`역할`, `식별 패턴`). 헤더 정확 일치. 행 수 0 허용.
  - `## scope 카테고리`: 정확히 3 컬럼 (`scope 헤더`, `project.md 대상 H3`, `표 헤더`). 헤더 정확 일치. 행 수 0 허용.
- **`project.md 대상 H3` 헤더 화이트리스트**:
  - 허용 문자: 영숫자, 공백, 하이픈
  - 차단 문자: 슬래시 (`/`), 콜론 (`:`), 해시 (`#`), 파이프 (`|`), 기타 마크다운 메타 문자
  - 위반 시 ERROR
- **`scope 헤더` 컬럼 prefix 강제**: 값이 `## ` 로 시작하지 않으면 ERROR.
- **부재 처리**: 신규 섹션 부재 시 INFO 1 줄 (예: `[INFO] config.md 의 ## learn 언어 패턴 섹션 미정의 — SKILL.md default 사용`). WARN 아님 (backward-compat 0 brittle).
- **결과 출력**: 기존 doctor 출력 형식과 일관 (`[PASS]`, `[INFO]`, `[WARN]`, `[ERROR]` prefix + 1 줄 설명 + 필요 시 fix 안내).
- **runtime 동작 (A2 결정)**: `/pilot:learn` `/pilot:analyze` `/pilot:project` `/pilot:create-feature` 가 잘못된 config 행을 만나도 **abort 하지 않는다**. 해당 행만 무시하고 SKILL.md default 로 fallback + stderr 에 경고 1 줄 (`[WARN] config.md {섹션}:{행번호} 무시 — {사유}, default 사용`). doctor 가 별도 실행될 때만 ERROR 로 보고. 워크플로 중단을 사용자가 명시 fix 후 결정. (rationale: 1행 오류로 전체 워크플로 중단 vs default fallback 안전성 — 후자.)

## 예외 케이스

- **config.md 자체 부재**: 기존 `[WARN] context/config.md` 가 그대로 발동 (변경 없음).
- **신규 섹션 모두 부재**: 각각에 대해 INFO 1 줄. 정상 default 사용 안내.
- **컬럼 수 불일치**: ERROR. 예: `[ERROR] config.md ## scope 카테고리: 표 컬럼 수 2개 (3개 필요) — 기대 헤더: scope 헤더, project.md 대상 H3, 표 헤더`.
- **부적절 헤더 문자**: ERROR. 예: `[ERROR] config.md ## scope 카테고리:3행: project.md 대상 H3 값 "Models/Repos" 에 차단 문자 슬래시 포함 — 영숫자·공백·하이픈만 허용`.
- **scope 헤더 prefix 위반**: ERROR. 예: `[ERROR] config.md ## scope 카테고리:2행: scope 헤더 값 "Routes" — "## " prefix 필요`.

## 관련 파일 범위

- 변경: `pilot/tools/doctor/integrity.py` (신규 검증 함수)
- **단위 테스트 (신규)**: `pilot/tests/tools/test_doctor_integrity.py` — 기존 `test_doctor_slack.py` 패턴 답습 (`unittest` + `importlib.util` 로 doctor 모듈 로드). 케이스:
  - **PASS** — `## learn 언어 패턴` 표 1·2 정상, `## scope 카테고리` 정상, 신규 섹션 부재 → INFO
  - **ERROR** — 컬럼 수 불일치 (각 섹션별 1 케이스), 헤더 화이트리스트 위반 (슬래시·콜론·#·|), scope `## ` prefix 누락
  - 기존 `pilot/tests/fixtures/v0.1.0-baseline/config/{pass-empty,pass-valid,error-*}` fixture 재사용 (#00 의 산출물)
- 회귀 픽스처: `pilot/tests/fixtures/v0.1.0-baseline/config/`
