# #13 부트스트랩 마법사 (`/pilot:init` 확장)

> source: design-pilot-review-2026-05-20.md (Tier 1 — 도입 장벽 해소)

## 요구사항

- **조건**: 현재 [`/pilot:init`](../../../../pilot/skills/init/SKILL.md) 은 빈 스켈레톤만 생성. `config.md` 가 채워지지 않으면 후속 `/pilot:learn` `/pilot:analyze` 가 fallback default 만 동작 → 도메인 추출 정확도 저하 + 신규 사용자가 첫 명령부터 막힘.
- **트리거**: `/pilot:init` 실행 시. 기존 `workspace/` 가 이미 있고 `config.md` 가 비어있지 않은 경우는 wizard 단계 skip (idempotent).
- **기대결과**: `/pilot:init` 한 번으로 `config.md` 의 ① 주 언어 패턴 표 ② `## scope 카테고리` 표 ③ `## Ignore` 패턴이 **저장소 실측에 근거해** 채워진 상태. 사용자 추가 입력 없이 `/pilot:learn` 이 fallback 분기 없이 1차 추출 성공.

## 비즈니스 규칙

- **wizard 활성 조건**:
  - `/pilot:init` 가 `config.md` 를 `created` (신규 생성) 한 경우만 wizard 진입.
  - `exists` (기존 파일 보존) 인 경우는 wizard skip — 사용자 수동 편집 보존.
  - `--no-wizard` 플래그로 강제 skip 가능 (v0.1.0 동작 동등).
- **언어 감지 (config 의 `## learn 언어 패턴` 표 자동 채움)**:
  - CWD 기준 `find . -type f` 로 확장자 빈도 집계 (`.git`·`node_modules` 등 sane default exclude 적용 후).
  - 상위 3개 확장자 → features/01 의 5개 default 언어 (`ruby`·`python`·`typescript`·`go`·`java`) 와 매핑. 비매핑 확장자는 INFO 로 알리고 skip.
  - 매핑된 언어의 default 행만 표에 주입. 빈도 0 인 언어 행은 추가하지 않음.
  - 매핑 결과 0건 → default 표 5행 전체 주입 (현재 fallback 거동과 동일).
- **scope 카테고리 후보 제안 (config 의 `## scope 카테고리` 표 자동 채움)**:
  - 상위 디렉터리 (depth ≤ 2) 의 폴더명 빈도 집계.
  - 빈도 ≥ 1 (= 존재) 이고 영문 소문자 폴더명 → scope 후보. 사용자 확인 없이 default 매핑 (`controllers`/`routes` → `Endpoints`, `models`/`entities` → `Models`, `services`/`workers`/`jobs` → `Services`) 으로 1차 채움.
  - 매핑 안 되는 후보는 INFO 출력 + 표에는 미반영 (사용자가 수동 추가).
  - 후보 0건 → features/02 의 default 매핑 그대로 주입.
- **Ignore 패턴 sane default**:
  - 모든 init 시 `Ignore` 표에 baseline 패턴 강제 주입: `.git/`, `node_modules/`, `__pycache__/`, `vendor/`, `dist/`, `build/`, `.next/`, `target/`, `*.pyc`, `*.lock`.
  - 기존 행이 있으면 dedupe 병합 (사용자 수동 추가 보존).
- **`/pilot:init` 출력 변경**: wizard 적용 결과를 결과 출력 블록에 한 줄씩 보고 — "언어 N개 자동 감지·주입", "scope 후보 M개 매핑", "Ignore baseline P개 추가".
- **재실행 안전성**: 두 번째 `/pilot:init` 호출 시 `config.md exists` → wizard skip. 강제 재실행은 별도 명령 (`/pilot:init --rewizard` v2 외).

## 예외 케이스

- **저장소가 거대 (>100k 파일)**: `find` 가 느림. `--max-files 50000` 으로 잘라서 샘플링. INFO 로 "샘플링 적용 (50000 파일)" 보고.
- **CWD 가 모노레포 루트 (서브폴더에 여러 언어 혼재)**: 빈도 기반이므로 상위 3개 확장자만 → 다른 서브트리는 사용자 수동 추가 안내 (INFO).
- **`.gitignore` 미존재**: 감지 시 sane default exclude 만 적용 (위 baseline 와 동일 목록). WARN 없음.
- **wizard 단계 1개 실패 (감지 0건 등)**: 해당 단계만 default 표 주입 + INFO 1줄. 다른 단계는 계속 진행. abort 금지 (A2 fallback 정책 일관).
- **사용자가 wizard 중간에 명령 중단 (Ctrl-C)**: `/pilot:init` 자체가 1회 실행이라 중간 상태 없음. config.md 가 부분 작성된 상태로 남으면 다음 `/pilot:init` 가 `exists` 분기 → wizard skip. 사용자가 직접 편집하거나 `--rewizard` v2.

## 관련 파일 범위

- **변경**: `pilot/skills/init/SKILL.md`
  - "동작" 섹션 1.5 단계 신설: "wizard 적용 — `config.md created` 인 경우만, 언어·scope·Ignore 자동 채움".
  - 출력 포맷에 wizard 결과 요약 줄 추가.
- **신설**: `pilot/tools/init_detect.py`
  - `detect_languages(cwd, max_files=50000) -> list[str]` (상위 3개 매핑된 언어)
  - `detect_scope_candidates(cwd) -> dict[str, str]` (폴더명 → scope 카테고리)
  - `IGNORE_BASELINE: list[str]` 상수
  - Python 표준 라이브러리만 사용 (의존성 0).
- **변경**: `pilot/skills/context/lifecycle/setup/templates/config.md.template`
  - wizard 가 채울 표의 헤더는 그대로 유지. 본문 행만 wizard 가 동적 주입.
- **테스트 픽스처**: `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/` 를 wizard 입력으로 재활용. wizard 산출 `config.md` 가 features/01·02 의 expected default 와 동등한지 회귀 검증 (features/00 의 diff.sh 흐름에 케이스 추가).
- **사용자 영향**: 기존 사용자는 영향 없음 (`config.md exists` 분기). 신규 사용자는 1단계 onboarding 비용 → 0.
