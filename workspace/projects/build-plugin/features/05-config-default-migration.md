# #05 v0.1.0 → v0.2.0 자동 마이그레이션 (M1)

> source: design-pilot-generic-2026-04-29.md (D10 결정, M1 마이그레이션)

## 요구사항

- **조건**: 사용자가 pilot v0.1.0 사용 중 v0.2.0 으로 업그레이드. v0.2.0 의 D10 결정으로 SKILL.md default 표 폐지 → 사용자 `workspace/context/config.md` 가 비어있으면 거동 변경 (폴더 인접성 fallback). backward-compat 0 brittle 약속을 마이그레이션으로 보장.
- **트리거**: `/pilot:doctor --fix` 호출. doctor 가 v0.1.0→v0.2.0 업그레이드 감지 + config 신규 섹션 부재 시 사용자 config 에 v0.1.0 default 표 자동 주입 제안.
- **기대결과**: 사용자가 명시 거부 안 하면 자동 주입 → v0.1.0 거동 그대로. 사용자가 거부하면 빈 config 유지 → 폴더 인접성 fallback.

## 비즈니스 규칙

- **업그레이드 감지**: `workspace/projects/{PROJECT}/.agent-state.yml` 의 `plugin_version` 이 `0.1.x` 또는 부재 + 현재 plugin v0.2.0 + `workspace/context/config.md` 의 `## learn 언어 패턴` `## scope 카테고리` 모두 부재.
- **자동 주입 대상**: `workspace/context/config.md` 에 v0.1.0 default 5 언어 의존성 추적 표 + 역할 분류 long-form 6 행 + scope 카테고리 3 행 (Routes/Models/Services). 본문은 README example block 과 동일 형식.
- **opt-out 메커니즘**:
  - `/pilot:doctor --fix` 가 자동 주입 직전 사용자 확인:
    ```
    [UPGRADE] pilot 0.1.0 → 0.2.0 — default 표가 SKILL.md 에서 폐지됐습니다.
    backward-compat 을 위해 v0.1.0 default 표를 workspace/context/config.md 에 자동 주입할까요?
    
    a) 주입 (권장) — v0.1.0 거동 그대로 유지
    b) 거부 — config 빈 채로 폴더 인접성 fallback 으로 전환 (사용자 자유 정의)
    c) 미루기 — 다음 doctor --fix 호출 시 다시 묻기
    ```
  - 사용자 응답을 `.agent-state.yml` 의 `migration_v0_2_0` 필드에 기록 (`accepted` / `declined` / null). null 이면 다음 호출 시 다시 묻기.
- **`plugin_version` 갱신**: 자동 주입 또는 거부 결정 후 `.agent-state.yml.plugin_version` 을 `0.2.0` 으로 갱신.
- **여러 프로젝트가 같은 workspace 공유**: `workspace/context/config.md` 는 1 개라 1 회 주입으로 모든 프로젝트 적용. 단 `.agent-state.yml.migration_v0_2_0` 는 프로젝트별 기록.

## 예외 케이스

- **사용자가 이미 config 에 부분 정의** (예: 일부 언어만): 자동 주입 안 함 + INFO 1 줄 (`config 의 신규 섹션이 부분 정의됨 — 마이그레이션 skip, 사용자 직접 갱신 권장`). README 의 example block 참조 안내.
- **신규 사용자 (v0.1.0 미경험)**: `plugin_version` 이 처음부터 `0.2.0` 으로 기록 → 마이그레이션 skip. config 비어있으면 폴더 인접성 fallback 정상 동작.
- **사용자가 거부 후 config 가 빈 채로 사용**: 폴더 인접성 fallback 동작 + INFO 1 줄 (`config 의 ## learn 언어 패턴 가 비어있음 — 폴더 인접성 fallback 동작 중. 정확한 분류는 README 의 example 참조하여 config 정의 권장`).
- **다음 release (v0.3.0+)**: 본 마이그레이션 로직 유지. 단 v0.3.0 시점에 v0.1.0 사용자가 거의 없으면 deprecation warning 추가 후 v0.4.0 에서 제거.

## 관련 파일 범위

- **변경**: `pilot/tools/doctor/integrity.py` 의 `run_auto_fixes` 단계에 신규 마이그레이션 함수 추가 (`migrate_v0_1_to_v0_2`).
- **변경**: `pilot/skills/doctor/SKILL.md` 본문에 `--fix` 옵션의 마이그레이션 동작 명시.
- **신규**: `pilot/tests/tools/test_doctor_migration.py` — `test_doctor_slack.py` 패턴 답습. 케이스:
  - PASS: v0.1.0 감지 + opt-in → config 에 default 5 언어 표 주입
  - PASS: v0.1.0 감지 + opt-out → config 빈 채로 + `.agent-state.yml.migration_v0_2_0: declined`
  - PASS: 신규 사용자 (`plugin_version: 0.2.0` 부터) → 마이그레이션 skip
  - PASS: 부분 정의 사용자 → skip + INFO
- **참조**: README example block (#01 결과의 README 갱신과 짝).
- **회귀 픽스처**: `pilot/tests/fixtures/v0.1.0-baseline/migration/` 신규 디렉터리 — pre-migration config (`config-pre.md`) + post-migration config (`config-post-accepted.md`, `config-post-declined.md`) 캡처.
