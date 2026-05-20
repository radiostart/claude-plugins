# #14 Onboarding 시나리오 가이드 (5분 완주 문서)

> source: design-pilot-review-2026-05-20.md (Tier 1 — 도입 장벽 해소)

## 요구사항

- **조건**: 현재 [`pilot/README.md`](../../../../pilot/README.md) 은 47KB reference 성격. 신규 사용자가 "init → learn → project → planner → generator → evaluator" 순서를 직선으로 따라갈 가이드 부재. 어떤 명령부터 시작해야 할지, 각 명령의 산출물이 무엇인지, 실패 시 어디를 봐야 할지 한 화면에 정리된 문서가 없음.
- **트리거**: 신규 사용자가 플러그인 설치 직후 첫 cycle 진입 시. README 의 상단 링크를 통해 가이드로 진입.
- **기대결과**: 신규 사용자가 가이드만으로 5분 안에 첫 plan 산출 (`features/NN-{slug}.plan.md`) 까지 도달. 각 단계는 더미 저장소 (#00 의 `_input/python-sample/`) 기준 기대 출력 1~3 줄 예시 포함.

## 비즈니스 규칙

- **가이드 구조 (5 step + troubleshooting)**:
  1. **사전 준비** — 플러그인 설치 확인, 작업 폴더 지정, gstack 같은 외부 의존성 (CLAUDE.md `gstack (REQUIRED)` 룰) 안내.
  2. **`/pilot:init`** — 워크스페이스 스켈레톤 생성 + wizard (#13) 적용. 기대 출력 블록 첨부.
  3. **`/pilot:learn <진입파일>`** — 도메인 추출. 산출물 `workspace/context/{domain}/index.md` `inventory.md` 예시 첨부.
  4. **`/pilot:project <이름>`** — 프로젝트 폴더 생성 + 컨텍스트 적재. 산출물 트리 첨부.
  5. **planner 호출** — `@pilot-planner` 로 첫 feature 의 plan 작성. 기대 산출 `features/NN-{slug}.plan.md` 형태.
  6. **다음 행보** — generator/evaluator 호출 시점, TDD 모드 전환 (#15), doctor 점검 (#16) 으로의 링크.
- **더미 저장소 재사용**:
  - 가이드의 모든 예시는 `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/` (features/00 에서 생성된 5~10 파일 토이 코드베이스) 기준. 사용자가 자체 저장소 없이도 즉시 따라할 수 있도록.
  - 가이드 첫 단락에 "이 가이드는 더미 저장소 `_input/python-sample/` 를 따라 진행한다" 명시.
- **기대 출력 블록**: 각 단계마다 실제 명령 결과를 코드 블록 (` ``` `) 으로 첨부. 출력 차이가 크면 "환경에 따라 달라질 수 있음" 주석 1줄.
- **troubleshooting 섹션**: 신규 사용자가 자주 만나는 실패 케이스 5건 (config.md fallback 동작 모드, wizard skip 조건, learn 의 H2 매칭 실패, planner 진입 직전 STATE.md 누락, generator 의 orchestrate-load 누락) 와 해결 명령 1~2줄씩.
- **링크 정책**: pilot/ 내부 파일은 상대 경로 (`../skills/init/SKILL.md`), 외부 (workspace/projects/...) 는 절대 경로 사용 금지 — 사용자 환경마다 다름.
- **README 상단 진입점**: `pilot/README.md` 의 첫 H2 (`## 빠른 시작` 또는 동등 위치) 에 "처음 사용하시나요? → [pilot/docs/getting-started.md](docs/getting-started.md)" 한 줄 링크 추가. README 본문은 그대로 유지.
- **분량**: 가이드 본문 + 출력 블록 포함 ~300줄. 1 페이지 (스크롤 3회) 안에 완주 가능한 분량.

## 예외 케이스

- **더미 저장소 (`_input/python-sample/`) 가 아직 미완성**: features/00 가 done 상태이지만 실측 검증 미완료. 가이드 작성은 features/00 의 픽스처 캡처 완료 후 진행. 본 feature 의 의존성으로 명시.
- **신규 사용자가 한국어/영어 외 환경**: 본 가이드는 한국어 (build-plugin 의 공통 문서 언어). 영어 번역은 v2 외.
- **gstack 미설치 환경**: 사전 준비 단계에서 명시적으로 점검 명령 (`test -d ~/.claude/skills/gstack/bin && echo OK`) 제시. 실패 시 가이드 진행 중단 + CLAUDE.md 의 설치 안내 인용.
- **`/pilot:init` wizard 가 0건 감지 (빈 폴더)**: 가이드 더미 저장소는 보장된 입력이므로 미발생. 사용자 자체 저장소로 시도할 경우 troubleshooting 5번 케이스로 우회.
- **가이드 자체가 stale 되는 경우**: doctor 의 file:line drift 감지 (`/pilot:doctor`) 영역 외. 명령 출력 캡처가 실제와 어긋나면 사용자 피드백으로 별도 hotfix.

## 관련 파일 범위

- **신설**: `pilot/docs/getting-started.md` (~300줄)
- **변경**: `pilot/README.md`
  - 상단 (가능하면 첫 H2 직후) 에 "처음 사용하시나요?" 한 줄 링크.
  - 본문은 그대로 유지 (reference 성격 보존).
- **의존성**: features/00 (회귀 픽스처) 의 `_input/python-sample/` 트리 캡처 완료. 가이드 본문 작성은 본 의존성 충족 후 진행.
- **테스트**: 본 가이드는 문서이므로 자동 테스트 없음. 검증은 features/05 의 dogfooding 일환으로 신규 사용자 1인이 가이드만 보고 완주 가능한지 1회 실측.
- **사용자 영향**: 기존 사용자 0. 신규 사용자 진입 비용 대폭 감소.
