# pilot — Lifecycle skills

워크스페이스 셋업·세션 활성·정합성 검사·즉석 지시 기록을 다룬다. 5 개 스킬: `init` `project` `issue` `doctor` `focus`.

---

## `/pilot:init`

워크스페이스 스켈레톤 생성 (`pilot/skills/init/SKILL.md:9`).

- **인자**: 없음
- **사전 확인**: 없음 (workspace 가 없는 상태에서 실행되므로 P1 미적용 — `pilot/skills/init/SKILL.md:15-18`)
- **핵심 동작** (`pilot/skills/init/SKILL.md:24-42`):
  - CWD 기준 `./workspace/context/` 폴더 생성 (필요 시).
  - 템플릿 3 개 → 대상 경로로 Write (대상 존재 시 skip, 없으면 created — idempotent):
    - `templates/STATE.md.template` → `workspace/STATE.md`
    - `templates/MANIFEST.md.template` → `workspace/context/MANIFEST.md`
    - `templates/config.md.template` → `workspace/context/config.md`
  - 템플릿 위치: `${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/setup/templates/` (`pilot/skills/init/SKILL.md:34`)
- **부수 효과 없음** — STATE 갱신·도메인 로드 안 함.
- **`rules/`·`scope/`·`enums/` 카테고리 폴더는 만들지 않는다** — MANIFEST 가 가리키는 대로 사용자가 만든다 (`pilot/skills/init/SKILL.md:42`).

---

## `/pilot:project`

새 프로젝트 시작 또는 기존 프로젝트 재개 (`pilot/skills/project/SKILL.md:11`).

- **인자** (`pilot/skills/project/SKILL.md:13-27`): `{PROJECT}` 필수, `--tdd` 플래그, `{CONFL_URL}` (URL 또는 순수 숫자 page_id).
- **사전 확인**: P-1, P0 (`pilot/skills/project/SKILL.md:33-36`).
- **인자 파싱** (`pilot/skills/project/SKILL.md:46-58`):
  - `--tdd` → TDD 플래그
  - `http://`·`https://` 또는 순수 숫자 → `{CONFL_URL}`
  - 그 외 → `{PROJECT}`
  - `{PROJECT}` 비어있음 → `messages.md:project_name_required` 후 종료
  - 예약어 (`example`, `workspace`, `STATE`, `context`) → `project_name_reserved` 후 종료
- **수행 절차** (`pilot/skills/project/SKILL.md:60-138`):
  1. `workspace/projects/{PROJECT}/` 폴더가 없으면 `skills/context/lifecycle/projects/example/` 4 종 (`project.md`, `prompts/{planner,generator,evaluator}.md`) 을 **그대로 복사** (본문 재작성·요약·환각 금지) + `{프로젝트명}` 토큰 치환 (`pilot/skills/project/SKILL.md:63-67`).
  2. `.agent-state.yml` 초기화 — `schema: v1.2`, `analyzed: false`, `tdd: false`, `domain: null`, `plugin_version` (옵션) (`pilot/skills/project/SKILL.md:68-80`).
  3. 폴더 존재 시 → `project.md`+`prompts/` 로드 + state schema 검사 + drift 체크 (docs_last_fetched_at vs analyzed_at 등) (`pilot/skills/project/SKILL.md:81-86`).
  4. **STATE.md 갱신 (P2)** — `| project | {PROJECT} | 진행중 |` **1 행으로 교체**. 기존 다른 이름 행은 모두 삭제 (이력은 git log) (`pilot/skills/project/SKILL.md:88-90`).
  5. P3 도메인 컨텍스트 로드 (`pilot/skills/project/SKILL.md:92-94`).
  6. `--tdd` 면 `tdd-activation.md` 절차 (`pilot/skills/project/SKILL.md:96-98`).
  7. `{CONFL_URL}` 있으면 `python3 ${CLAUDE_PLUGIN_ROOT}/tools/confluence.py fetch "{CONFL_URL}"` 직접 호출 — `/pilot:confl` nested 호출 금지 (`pilot/skills/project/SKILL.md:100-109`).
  8. 사용자 분석 범위 질의 (전체·키워드·건너뛰기) → `analyze` 의 1~5 단계 실행 (`pilot/skills/project/SKILL.md:111-119`).
  9. project.md `## 목표` + prompts/ 갱신 (`analyze` 의 6~7 단계) (`pilot/skills/project/SKILL.md:121-123`).
  10. `python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace` 실행 (`pilot/skills/project/SKILL.md:126-131`).
- **결과 안내** — 모든 단계 마친 후 한 번만 출력. features/ 유무로 분기 (`pilot/skills/project/SKILL.md:140-151`).

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

워크스페이스·프로젝트 정합성 검사 (`pilot/skills/doctor/SKILL.md:13`).

- **인자**: 생략 시 STATE.md 의 `진행중` 프로젝트, 인자 있으면 `--project` 플래그.
- **기본 동작** (`pilot/skills/doctor/SKILL.md:21-37`):
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace [--project {PROJECT}]
  ```
  - exit `0` — ERROR 없음 (PASS / WARN 만)
  - exit `1` — ERROR 1 건 이상
- **검사 범위** (`pilot/skills/doctor/SKILL.md:42-56`):
  - Workspace: `workspace/`·`STATE.md` (`진행중` 1 개 정확히)·`MANIFEST.md`·`config.md`
  - Project: `.agent-state.yml` schema v1.2, `analyzed` ↔ `features/*.md`, `tdd` ↔ `project.md` 의 `**TDD 모드**`, `pr_base_branch` ↔ `git ls-remote origin <X>`
- **`--diagnose` 모드** — 런타임 실패 패턴 진단 (4-phase capture→diagnose→reduce→report) (`pilot/skills/doctor/SKILL.md:93-130`).
  - 패턴: `loop`·`red-miss`·`repeat-not-ready`·`scope-violation`·`none`
  - 우선순위: `red-miss > repeat-not-ready > scope-violation > loop` (복수 감지 시 confidence: medium)
  - 호출 시점: NOT_READY 2회 누적·동일 도구 반복·체크리스트 비어있음 등
- **`--schema` 모드** — 플러그인 구조 전용. workspace 무관. CI 자동 실행 (`.github/workflows/validate.yml`) (`pilot/skills/doctor/SKILL.md:133-148`).
- **제약** (`pilot/skills/doctor/SKILL.md:152-156`): 순수 stdlib · 비파괴 (읽기만) · 자동 fix 없음.

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
  - `@planner`·`@generator`·`@evaluator` 가 컨텍스트 로드 시 `.focus.md` Read 하여 본 호출에 반영.
  - 래퍼는 **파일을 수정·삭제·아카이브하지 않는다** — 한 focus 가 여러 phase 에 걸쳐 유효.
- **제약** (`pilot/skills/focus/SKILL.md:93-97`): 활성 focus 최대 1 개·focus 는 사양이 아니라 지시·`.focus.md` 와 `.focus.history/` 는 gitignore 대상.
