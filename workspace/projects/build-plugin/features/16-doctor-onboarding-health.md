# #16 Doctor — onboarding-health 점검 (신규 사용자 관점 진단)

> source: design-pilot-review-2026-05-20.md (Tier 3 — 신뢰도 보강)

## 요구사항

- **조건**: 현재 [`/pilot:doctor`](../../../../pilot/skills/doctor/SKILL.md) 는 구조 무결성 (STATE.md·MANIFEST.md·config.md 존재, `.agent-state.yml` 스키마, analyzed/tdd 플래그 정합) 만 검사. **사용자가 실제로 plan-generate-evaluate cycle 을 돌릴 수 있는 상태인지** 는 점검하지 않음. config.md 가 빈 표만 있어도 PASS, scope/ 폴더가 비어있어도 PASS, 첫 project 가 미등록이어도 PASS — 신규 사용자가 "왜 안 되지" 라고 느끼는 갭이 진단되지 않음.
- **트리거**: `/pilot:doctor` 또는 `/pilot:doctor {프로젝트}` 호출 시. 자동 활성. 별도 플래그 없이 기존 점검에 onboarding-health 룰이 추가됨.
- **기대결과**: 신규 사용자 관점 3~5개 체크 항목이 WARN 수준으로 보고됨 (PASS/ERROR 와 별도 색상·prefix). 어떤 명령으로 해소하는지 처방까지 1줄 동반.

## 비즈니스 규칙

- **점검 항목 (WARN 수준, 차단 안 함)**:
  - **OH-1 · config.md 핵심 섹션 채워짐**:
    - `## learn 언어 패턴` 표 본문 행 수 ≥ 1
    - `## scope 카테고리` 표 본문 행 수 ≥ 1
    - `## Ignore` 표 본문 행 수 ≥ 1
    - 셋 중 하나라도 0 → WARN + 처방: `/pilot:init --rewizard` (v2) 또는 수동 편집 안내.
  - **OH-2 · scope/ 디렉터리 채워짐**:
    - `workspace/context/scope/` 존재 + 하위 `.md` 파일 ≥ 1
    - 0 → WARN + 처방: `/pilot:learn <진입파일>` 호출 안내 (analyze 가 scope 파일 생성 — features/07).
  - **OH-3 · 첫 project 등록**:
    - `workspace/STATE.md` 의 `진행중` 또는 `대기` 프로젝트 ≥ 1
    - 0 → WARN + 처방: `/pilot:project {이름}` 호출 안내.
  - **OH-4 · MANIFEST 진입파일 존재**:
    - `workspace/context/MANIFEST.md` 의 도메인 분류 표 본문 행 수 ≥ 1
    - 0 → WARN + 처방: `/pilot:learn` 호출 안내.
  - **OH-5 · features/ 진입 가능 상태** (프로젝트 인자 지정 시):
    - `workspace/projects/{프로젝트}/features/` 존재 + `*.md` 1건 이상
    - 0 → WARN + 처방: planner 호출 안내 (`@pilot-planner` 또는 `/pilot:create-feature`).
- **출력 형식**:
  ```
  ── Onboarding Health ─────────────────
  OH-1  config 핵심 섹션:        {PASS|WARN}
  OH-2  scope/ 채움:              {PASS|WARN}
  OH-3  첫 project 등록:          {PASS|WARN}
  OH-4  MANIFEST 진입파일:        {PASS|WARN}
  OH-5  features/ 진입 가능:      {PASS|WARN|N/A}   ← 프로젝트 인자 시만

  {WARN 항목이 있으면 처방 1~2 줄씩 추가 출력}
  ```
- **WARN 수준 정책**: ERROR 와 분리. exit code 영향 없음 (구조 정합성 ERROR 만 exit 1). WARN 은 stdout 색상 차별 (노란색) 만.
- **`--fix` 미지원**: onboarding-health 는 사용자의 실제 작업 의도가 필요. `--fix` 로 자동 채울 수 없음. 처방 명령만 안내.
- **idempotency**: 동일 점검 반복 호출 시 결과 동일. 부수효과 없음.
- **기존 doctor 출력과 통합**: 기존 "구조 정합성" 섹션 아래에 "Onboarding Health" 섹션을 H4 또는 구분선으로 추가. 기존 출력 보존.

## 예외 케이스

- **workspace 자체 부재**: doctor 의 사전 검사가 사전 차단 (현재 동작 유지). onboarding-health 진입 안 함.
- **`--project` 인자 미지정**: OH-1~4 만 검사. OH-5 는 `N/A` 표시 + INFO 1줄 ("프로젝트 지정 시 features/ 진입 가능성 검사").
- **WARN 5건 모두 발생 (신규 사용자 첫 호출)**: 출력 길이 ~20줄 + 처방 5건. 압도 방지 위해 출력 상단에 "신규 워크스페이스 감지 — getting-started.md 권장" 1 줄 안내 (features/14 가이드 링크).
- **사용자가 의도적으로 빈 워크스페이스 유지 (CI 환경 등)**: WARN 무시 가능 (exit 0). `--no-onboarding-health` 플래그로 OH 섹션 자체 skip 가능 (v2 옵션).
- **config.md 표 헤더 자체가 깨짐**: features/04 의 doctor 구조 검증이 ERROR 로 사전 차단. OH-1 진입 안 함.

## 관련 파일 범위

- **변경**: `pilot/skills/doctor/SKILL.md`
  - "동작" 섹션에 onboarding-health 1 단락 추가.
- **변경**: `pilot/tools/doctor.py`
  - `check_onboarding_health(workspace_path, project=None) -> list[CheckResult]` 함수 신설.
  - 각 OH-N 룰을 개별 함수로 분리 (`_check_oh1_config_sections` 등).
  - 출력 포맷터에 WARN 색상 (yellow) + 처방 라인 지원.
- **회귀 픽스처**: features/00 의 분기 케이스 추가 — `doctor-onboarding/expected/` (PASS-only / WARN-mixed 두 케이스).
- **연계 features**:
  - features/14 (getting-started.md) — OH 5건 모두 WARN 시 상단 안내 링크.
  - features/13 (`init` wizard) — OH-1 의 WARN 처방으로 `--rewizard` 안내.
  - features/15 (tdd toggle) — tdd 3-way 일치 룰 (features/15 가 자체 추가) 와는 별도 섹션. 본 feature 와 충돌 없음.
- **사용자 영향**: 기존 사용자는 OH 가 PASS 면 출력 변화 미미. WARN 발생 시 처방 안내가 도움. 신규 사용자는 "어디서 막혔는지" 명시적 진단.
