# pilot — Lifecycle skills

워크스페이스 셋업·세션 활성·정합성 검사·즉석 지시 기록을 다룬다. 5 개 스킬: `init` `project` `issue` `doctor` `focus`.

---

## `/pilot:init`

워크스페이스 스켈레톤 생성 (`pilot/skills/init/SKILL.md:9`).

- **인자**: `--no-wizard` (선택 — wizard skip).
- **사전 확인**: 없음 (workspace 가 없는 상태에서 실행되므로 P1 미적용 — `pilot/skills/init/SKILL.md:15-18`)
- **1. 스켈레톤 생성** (`pilot/skills/init/SKILL.md:24-44`):
  - CWD 기준 `./workspace/context/` 폴더 생성 (필요 시).
  - 템플릿 3 개 → 대상 경로로 Write (대상 존재 시 skip=`exists`, 없으면 `created` — idempotent):
    - `templates/STATE.md.template` → `workspace/STATE.md`
    - `templates/MANIFEST.md.template` → `workspace/context/MANIFEST.md` (외부 도메인 reference placeholder 주석 포함)
    - `templates/config.md.template` → `workspace/context/config.md`
  - 템플릿 위치: `${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/setup/templates/` (`pilot/skills/init/SKILL.md:34`)
  - **`rules/`·`scope/`·`enums/` 카테고리 폴더는 만들지 않는다** — MANIFEST 가 가리키는 대로 사용자가 만든다 (`pilot/skills/init/SKILL.md:44`).
- **2. wizard 적용** — `config.md` 가 `created` 인 경우만, `--no-wizard` 시 skip (`pilot/skills/init/SKILL.md:48-78`):
  1. **언어 감지** — `tools/init_detect.py` `detect_languages()` → `## learn 언어 패턴` 두 표에 default 패턴 주입 (기존 행 dedupe 병합, 감지 0건 → 헤더만 + INFO).
  2. **scope 후보 감지** — `detect_scope_candidates()` → `## scope 카테고리` 3 컬럼 표 주입 (후보 0건 → default 3 행 Routes·Models·Services).
  3. **Ignore baseline** — `IGNORE_BASELINE` 10 패턴 주입.
  - 어느 단계가 실패해도 abort 금지 (A2 fallback). 표 헤더는 doctor strict 검증 대상 고정 스키마 (`pilot/skills/init/SKILL.md:56-61`).
- **부수 효과 없음** — STATE 갱신·도메인 로드 안 함.

---

## `/pilot:project`

새 프로젝트 시작 또는 기존 프로젝트 재개 (`pilot/skills/project/SKILL.md:11`).

- **인자**: `{PROJECT}` 필수, `--tdd` 플래그, `{CONFL_URL}` (URL 또는 순수 숫자 page_id).
- **사전 확인**: P-1, P0 (`pilot/skills/project/SKILL.md:31-38`).
- **수행 절차** (`pilot/skills/project/SKILL.md:40-158` — 10 단계):
  1. **인자 파싱** (`:44-57`) — `--tdd` → TDD 플래그 / `http(s)://`·순수 숫자 → `{CONFL_URL}` / 그 외 → `{PROJECT}`. 비어있음 → `project_name_required`, 예약어 (`example`·`workspace`·`STATE`·`context`) → `project_name_reserved` 후 종료.
  2. **프로젝트 폴더 생성/로드** (`:59-105`) — 없으면 `example/` 4 종 (`project.md`, `prompts/{planner,generator,evaluator}.md`) **그대로 복사** (본문 재작성·요약·환각 금지) + `{프로젝트명}` 토큰 치환 (치환 범위·H1 정규식·sanitize 는 본문 blockquote 명문화). `.agent-state.yml` 초기화 (`schema: v1.2`, `analyzed: false`, `tdd: false`, `domain: null`). 존재 시 → 로드 + state schema 검사 + drift 체크.
  3. **STATE.md 갱신 (P2)** (`:107-109`) — `| project | {PROJECT} | 진행중 |` **1 행으로 교체** (이력은 git log).
  4. **도메인 컨텍스트 로드 (P3)** (`:111-113`).
  5. **TDD 모드 적용** (`:115-117`) — `--tdd` 시 `tdd-activation.md` 절차.
  6. **기획서 저장** (`:119-128`) — `{CONFL_URL}` 시 `tools/confluence.py fetch` 직접 호출 (`/pilot:confl` nested 호출 금지).
  7. **기능 분석** (`:130-138`) — 6단계 성공 시만. 사용자 분석 범위 질의 (전체·키워드·건너뛰기) → `analyze` 1~5 단계.
  8. **prompts/ 갱신·자가 검증** (`:140-142`) — 7단계에서 분석 수행 시만 (`analyze` 6~7 단계).
  9. **무결성 검증** (`:144-153`) — `tools/doctor.py workspace` 자동 실행.
  10. **결과 출력** (`:155-`) — 모든 단계 마친 후 한 번만. features/ 유무로 분기.

---

## `/pilot:issue`

운영 이슈 처리 모드 (`pilot/skills/issue/SKILL.md:11`).

- **인자**: `$ARGUMENTS` (이슈명, 비어 있어도 OK).
- **사전 확인**: P-1, P0 (`pilot/skills/issue/SKILL.md:17-20`).
- **수행 절차** (`pilot/skills/issue/SKILL.md:22-31`):
  1. 인자 비어있으면 이슈명 없이 진입.
  2. `workspace/issues/{이슈명}/` 존재 확인.
     - 없으면 `${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/issues/GUIDE.md` 로드 → 새 폴더 생성.
     - 있으면 `issue.md` 만 로드 (GUIDE.md 는 로드하지 않음).
  3. **STATE.md 갱신 (P2)** — `| issue | {이슈명} | 진행중 |` 1 행으로 교체. 이슈명 없으면 `| issue | - | 진행중 |`.
  4. P3 도메인 컨텍스트 로드.
  5. 이슈 컨텍스트 요약·다음 작업 안내.

---

## `/pilot:doctor`

워크스페이스·프로젝트 정합성 검사. **검사 범위·판정 기준·출력 형식·처방의 로직 SSOT 는 `pilot/tools/doctor.py`** (진단 모드는 `tools/doctor/diagnose.py`) — SKILL.md 는 호출 계약만 정의 (`pilot/skills/doctor/SKILL.md:22-23`). 페르소나: diagnostician (증상 → 근거 → 처방).

- **인자**: 생략 시 STATE.md 의 `진행중` 프로젝트, 프로젝트명 전달 시 `--project {PROJECT}` 부가 (`pilot/skills/doctor/SKILL.md:24·33`).
- **기본 동작** (`pilot/skills/doctor/SKILL.md:27-38`):
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace [--project {PROJECT}]
  ```
  - exit `0` — ERROR 없음 (PASS / WARN 만)
  - exit `1` — ERROR 1 건 이상
- **플래그** (`pilot/skills/doctor/SKILL.md:44-46`):
  - `--fix` — auto-fixable 항목 자동 수정 + v0.1.0→v0.2.0 마이그레이션 질의 (상세: `references/migration.md`).
  - `--diagnose` — 런타임 실패 패턴 진단 (`loop`·`red-miss`·`repeat-not-ready`·`scope-violation`·`none`). exit `0` (none) · `1` (감지). 호출 시점: evaluator NOT_READY 2회 / 동일 도구 반복 의심 / 완료 선언인데 체크리스트·REPORT 비어있을 때.
  - `--schema` — 플러그인 구조 전용 (workspace 무관). CI 자동 실행 (`.github/workflows/validate.yml`).
- **제약** (`pilot/skills/doctor/SKILL.md:59-63`): 순수 stdlib · 비파괴 (읽기만, `--fix` 제외) · 실패 시 fix 제안만 출력하고 자동 적용 안 함.

---

## `/pilot:focus`

대화 중 결정·방향 조정을 다음 래퍼 호출에 전달 (`pilot/skills/focus/SKILL.md:12`).

- **인자**: 지시문 또는 `--clear`.
- **사전 확인**: P1 — `{PROJECT}` 획득 (`pilot/skills/focus/SKILL.md:28-30`).
- **경로** (`pilot/skills/focus/SKILL.md:46-48`):
  - 현재 focus: `workspace/projects/{PROJECT}/.focus.md`
  - 아카이브: `workspace/projects/{PROJECT}/.focus.history/{YYYY-MM-DDTHH-MM-SS}.md`
- **기록 모드** (`pilot/skills/focus/SKILL.md:51-70`):
  1. 기존 `.focus.md` 존재 시 → `.focus.history/{기존 timestamp}.md` 로 이동.
  2. 새 `.focus.md` 작성: `# Focus — {timestamp}\n\n{지시문}`.
- **제거 모드 (`--clear`)** (`pilot/skills/focus/SKILL.md:72-77`):
  - `.focus.md` 없으면 "활성 focus 가 없습니다" 출력 후 종료.
  - 있으면 `.focus.history/{timestamp}.md` 로 이동 후 삭제.
- **래퍼 동작** (`pilot/skills/focus/SKILL.md:85-89`):
  - `@pilot-planner`·`@pilot-generator`·`@pilot-evaluator` 가 컨텍스트 로드 시 `.focus.md` Read 하여 본 호출에 반영.
  - 래퍼는 **파일을 수정·삭제·아카이브하지 않는다** — 한 focus 가 여러 phase 에 걸쳐 유효.
- **제약** (`pilot/skills/focus/SKILL.md:93-97`): 활성 focus 최대 1 개·focus 는 사양이 아니라 지시·`.focus.md` 와 `.focus.history/` 는 gitignore 대상.
