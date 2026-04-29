# #00 회귀 골든 픽스처 (v0.1.0 baseline 캡처)

> source: design-pilot-generic-2026-04-29.md (Next Steps 0번)

## 요구사항

- **조건**: `pilot/tests/fixtures/v0.1.0-baseline/` 디렉터리 신설. 작은 입력 코드베이스 1 개 (Ruby 또는 Python, 5~10 파일) + v0.1.0 의 `/pilot:learn` `/pilot:project` `/pilot:analyze` 산출물 캡처.
- **트리거**: 수동 (1 회 캡처). v1 적용 후 회귀 검증 시점 (Next Steps 5번) 에 `diff.sh` 로 재실행.
- **기대결과**: config 비어있을 때 v1 출력이 v0.1.0 캡처와 byte-for-byte 또는 의미 동등하게 일치 (#01 #02 #04 의 backward-compat 0 brittle 1 차 검증). #03 의 H3 동적 생성은 거동이 바뀌므로 별도 baseline.

## 비즈니스 규칙

- **fixture 디렉터리 구조**:
  ```
  pilot/tests/fixtures/v0.1.0-baseline/
  ├── README.md                  # 목적·재생성 절차 1 페이지
  ├── _input/                    # 더미 코드베이스 (read-only, 수정 금지)
  ├── learn/expected/            # /pilot:learn 산출물 (workspace/context/{domain}/ 트리)
  ├── project/expected/          # /pilot:project 신규 폴더 직후 (하드코드 H3 포함)
  ├── analyze/expected/          # /pilot:analyze 5-2 적용 후
  ├── config/                    # #04 doctor 검증 케이스 (PASS·ERROR 픽스처)
  │   ├── pass-empty/            # 신규 섹션 부재 → INFO
  │   ├── pass-valid/            # 신규 섹션 정상 정의 → PASS
  │   ├── error-column-mismatch/ # 컬럼 수 불일치
  │   ├── error-bad-header-char/ # 슬래시·콜론·#·| 포함
  │   └── error-no-prefix/       # scope 헤더 `## ` 누락
  └── diff.sh                    # 회귀 비교 도구 (shell 또는 python)
  ```
- **두 단계 baseline (A3 결정)**:
  - **Stage 1 (config 비움)**: v0.1.0 = v1 동일 출력 (#01 #02 #04 검증). #03 도 default H3 생성 시 v0.1.0 의 example/project.md 와 동일 결과 (Models/Endpoints/Services).
  - **Stage 2 (config 채움)**: v1 의 override 거동 캡처. 사용자 행 우선·#03 동적 H3 채움 검증.
- **언어 선정 (T3 결정)**: v1 = **1 언어 fixture** (Python 또는 Ruby — Open Q #1 의 dogfooding 대상과 일치 권장). A1 의 wide-form 유지 결정으로 lookup 코드는 5 언어 default 표 전체를 한 번에 검증 가능 → 1 언어 fixture 만으로 다른 4 언어 default 회귀도 wide-form 표 자체의 무결성으로 간접 보장. 5 언어 fixture 는 v1.1 milestone.
- **diff.sh 동작**: fixture `_input/` 으로 현재 트리 빌드 → `expected/` 와 `diff -ru` 비교. exit 0 = 회귀 없음, exit 1 = diff 발견. `tdd: false` 라 자동 실행은 안 함, 수동 호출만.
- **재생성 절차** (README.md): v0.1.0 (또는 다음 baseline 지점) 에서 `_input/` 으로 cycle 1 회 → `expected/` 갱신 → 커밋.

## 예외 케이스

- **`_input/` 의존성 (gem·npm)**: 의존성 0 인 plain 스크립트로 작성. 외부 패키지 install 없이 fixture 가 self-contained.
- **timestamp 포함 산출물** (analyzed_at 등): expected 캡처 시 timestamp 는 placeholder (`{ANALYZED_AT}`) 로 정규화. diff 시 placeholder 무시.
- **OS-specific path 구분자**: macOS (`/`) 기준. Windows 호환은 v1 외 (Open Q #1 의 dogfooding 환경 결정 시 재검토).
- **#03 거동 변화 후 stage 1 baseline 유효성**: #03 의 default H3 (Models/Endpoints/Services) 가 v0.1.0 example/project.md 의 하드코드 H3 와 정확히 동일해야 함 — diff 0 보장. 다른 결과 시 #03 구현 잘못.

## 관련 파일 범위

- 신설: `pilot/tests/fixtures/v0.1.0-baseline/` (전체 트리)
- 참조: `pilot/skills/learn/SKILL.md` (Phase 2 default 표) · `pilot/skills/analyze/SKILL.md` (5-2 default) · `pilot/skills/project/SKILL.md` (H3 생성) · `pilot/skills/context/lifecycle/projects/example/project.md` (templating 입력)
- 다음 단계: 1~4 (각 feature) 완료 후 5번 회귀 검증에서 `diff.sh` 재실행.
