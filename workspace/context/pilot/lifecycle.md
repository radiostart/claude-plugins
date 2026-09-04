# pilot — Lifecycle skills

워크스페이스 셋업·세션 활성·정합성 검사·즉석 지시 기록을 다룬다. 5 개 스킬: `pilot-init` `project` `issue` `pilot-doctor` `focus`.

---

## `/pilot:pilot-init`

워크스페이스 구조를 일괄 생성한다 (`pilot/skills/pilot-init/SKILL.md:11`).

- **인자**: `--no-wizard` (선택 — wizard skip, `pilot/skills/pilot-init/SKILL.md:35·51`).
- **사전 확인**: P 절차 없음. workspace 경로 = CWD 기준 `./workspace/`, 폴더 없으면 `mkdir -p workspace/context` (`pilot/skills/pilot-init/SKILL.md:15`).
- **1. 스켈레톤 생성** (`pilot/skills/pilot-init/SKILL.md:19-31`) — 템플릿 3 개를 **대상 존재 시 skip(exists) / 없으면 생성(created)** 원칙으로 적용 (idempotent):

  | 템플릿 | 대상 경로 |
  | --- | --- |
  | `templates/STATE.md.template` | `workspace/STATE.md` |
  | `templates/MANIFEST.md.template` | `workspace/context/MANIFEST.md` |
  | `templates/config.md.template` | `workspace/context/config.md` |

  - 템플릿 위치: `${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/setup/templates/` (`pilot/skills/pilot-init/SKILL.md:21`).
  - `MANIFEST.md.template` 의 `## 외부 도메인 reference` 는 placeholder 주석만 — 실제 작성은 `/pilot:learn` 이 cross-domain reference 를 처음 발견할 때 (`pilot/skills/pilot-init/SKILL.md:29`).
  - **`rules/`·`scope/`·`enums/` 카테고리 폴더는 만들지 않는다** — 사용자가 MANIFEST 를 채우며 구조를 결정 (`pilot/skills/pilot-init/SKILL.md:31`).
- **2. wizard 적용** — `config.md` 가 `created` 인 경우만, `--no-wizard` 시 skip. 어느 단계가 실패해도 abort 금지 (A2) (`pilot/skills/pilot-init/SKILL.md:33-41`):
  1. **언어 감지 — Glob 직접 판단** (`:39`): 저장소 루트에서 확장자별 Glob (`**/*.rb`·`**/*.py`·`**/*.ts`+`**/*.tsx` 합산·`**/*.go`·`**/*.java`). `.git/`·`node_modules/`·`__pycache__/`·`vendor/`·`dist/`·`build/`·`.next/`·`target/`·`.` 로 시작하는 폴더 제외. 매치 상위 3 언어 (동률이면 나열 순) 를 `## learn 언어 패턴` 두 표에 주입 (기존 행 dedupe 병합). 감지 0 건 → 헤더만 + INFO.
  2. **scope 후보 감지 — Glob 직접 판단** (`:40`): 루트 직속 폴더 (depth 1) 와 그 하위 (depth 2) 를 나열하고 영문 소문자 폴더명만 매핑 — `controllers`·`routes` → Endpoints / `models`·`entities` → Models / `services`·`workers`·`jobs` → Services. 같은 H3 중복은 1 행 dedupe. 후보 0 건 → default 3 행 (Routes·Models·Services) + INFO.
  3. **Ignore baseline 주입** (`:41`): 10 패턴 (`.git/`·`node_modules/`·`__pycache__/`·`vendor/`·`dist/`·`build/`·`.next/`·`target/`·`*.pyc`·`*.lock`) 을 `## Ignore` 표에 dedupe 병합.
  - 표 헤더는 **고정 스키마** — 문자열 원문 그대로 보존하고 저장 직후 재확인 (`pilot/skills/pilot-init/SKILL.md:37`).
- **부수 효과 없음** — STATE 갱신·도메인 로드 안 함.

---

## `/pilot:project`

새 프로젝트 시작 또는 기존 프로젝트 재개 (`pilot/skills/project/SKILL.md:11`).

- **인자**: `{PROJECT}` 필수 · `--tdd` · `{CONFL_URL}` (URL 또는 순수 숫자 page_id) (`pilot/skills/project/SKILL.md:15`).
- **사전 확인**: P-1, P0 (`pilot/skills/project/SKILL.md:19-21`).
- **진행 안내 규칙**: 중간 단계마다 "다음 작업" 을 흘리지 않고 모든 단계를 마친 뒤 결과 출력에서 한 번만 안내 (`pilot/skills/project/SKILL.md:25`).
- **수행 절차 10 단계** (`pilot/skills/project/SKILL.md:27-87`):
  1. **인자 파싱** (`:29`) — 비어있음·예약어 (`example`·`workspace`·`STATE`·`context`) 면 안내 후 종료.
  2. **프로젝트 폴더 생성/로드** (`:31-41`) — 없으면 `context/lifecycle/projects/example/` 4 종 (`project.md` + `prompts/{planner,generator,evaluator}.md`) 을 **그대로 복사** 후 H1 의 `{프로젝트명}` 토큰만 파일당 1 회 치환. **본문 재작성·요약·환각·도메인 예시 삽입 금지**, GUIDE.md 본문 복사 금지. H1 토큰 부재 시 치환 skip + INFO (A2).
     - **`## 관련 파일` H3 동적 채움** (`:37`) — 복사 직후 1 회만. `config.md` `## scope 카테고리` 의 `project.md 대상 H3` 컬럼마다 `### {대상 H3}` + 빈 표 추가. SSOT 분리: H3 헤더 = 본 단계 1 회 생성 (재실행 시 보존) / 표 본문 = analyze 5-2·create-feature 가 매번 갱신 / 사용자 수동 H3 = 양쪽 보존.
     - **`.agent-state.yml` 초기화** (`:39`) — `schema: v1.2` · `analyzed: false` · `tdd: false` · `domain: null` · `plugin_version`(획득 실패 시 라인 생략). `domain` 자동 추론 금지.
     - **있으면** (`:41`) — `project.md`·`prompts/` 로드. `.agent-state.yml` 부재·`schema: v1` 이면 `/pilot:pilot-doctor --fix` 안내. **drift 체크** (v1.1+·`analyzed_at` 존재 시): `docs_last_fetched_at > analyzed_at` → 재분석 질의 / `features 개수 > last_analyzed_features+1` → `--regen-agents` 권장 / `scope mtime > analyzed_at` → `--regen-agents` 권장. 모두 안내만, 자동 실행 없음.
  3. **STATE.md 갱신 (P2)** (`:43-45`) — `| project | {PROJECT} | 진행중 |` 1 행 교체.
  4. **도메인 컨텍스트 로드 (P3)** (`:47-49`).
  5. **TDD 모드 적용** (`:51-53`) — `--tdd` 시 `context/modes/tdd-activation.md` 절차.
  6. **기획서 저장** (`:55-63`) — `{CONFL_URL}` 시 `tools/confluence.py fetch` 를 이 턴에 직접 실행 (`/pilot:confl` nested 호출 금지 — 컨텍스트 이중 적재·경로 어긋남 위험). 실패 시 7·8 건너뛰고 9 단계로.
  7. **기능 분석** (`:65-67`) — 6 단계 성공 시만. 전체 분석 / 키워드 필터 (실제 H2 예시 2~4 개 제시) / 건너뛰기 질의 후 analyze 1~5 단계.
  8. **prompts/ 갱신·자가 검증** (`:69-71`) — 7 단계에서 분석 수행 시만. analyze 6~7 단계.
  9. **무결성 검증** (`:73-79`) — `tools/doctor.py workspace` 자동 실행. 출력 규칙은 pilot-doctor § 임베디드 호출 규칙 참조.
  10. **결과 출력** (`:81-87`) — features/ 유무로 분기. 있음 → `/pilot:autopilot {NN}` 또는 `@pilot-planner` 병기 / 없음 → project.md 보강 → confl+analyze 또는 create-feature 순서 안내. 신규 프로젝트에만 Slack 활성화 안내 1 줄.

---

## `/pilot:issue`

운영 이슈 처리 모드 (`pilot/skills/issue/SKILL.md:11`). issue 는 **기존 누적 컨텍스트 기반 단건 처리** — projects/ 산출물 (project.md·features/·prompts/) 은 미참조지만 `workspace/context/` 도메인 지식·과거 `issues/` 이력·메모리는 진단의 기반이다 (`pilot/skills/issue/SKILL.md:13-15`).

- **인자**: `$ARGUMENTS` (이슈 서술, 비어 있어도 진입 가능).
- **사전 확인**: P-1, P0 — P0 는 이슈명·키워드로 유사 이슈 이력 반영 (`pilot/skills/issue/SKILL.md:21-26`).
- **사이클 계약**: 코드 수정이 필요하면 `@pilot-planner → @pilot-planner-critic → @pilot-generator → @pilot-evaluator` 를 그대로 사용한다 — orchestrate-load 가 STATE.md 의 `issue` 행을 인식해 issues/ 기반으로 로드하는 **`work_mode` 계약** (`pilot/skills/issue/SKILL.md:17`). 조사·회신만으로 끝나면 사이클 없이 직접 처리.
- **수행 절차 6 단계** (`pilot/skills/issue/SKILL.md:28-55`):
  1. **bare 진입** (`:30`) — `$ARGUMENTS` 비어있으면 "폴더·기록이 남지 않고 사이클도 비지원" 1 줄 고지 후 GUIDE.md 로드, **2·3 단계를 건너뛰어** (검색·slug 불가) 4 단계부터 진행. 5 단계는 질의 없이 MANIFEST 까지만, 6 단계 안내에서 사이클 항목 제외.
  2. **유사 이슈 검색** (`:31-40`) — 폴더명과 제목을 **함께** 훑는다 (`ls workspace/issues/` + `grep -H "^# " workspace/issues/*/issue.md`). 폴더명은 영문 slug 라 한글 키워드는 H1 제목이 받는다. 발견 시 `{slug} — {제목}` 목록으로 "재개할까요, 새 이슈로 진행할까요?" 질의. H1 없는 기존 이슈는 폴더명으로만 매칭 — 소급 기입하지 않는다.
  3. **이슈 slug 결정 + 폴더 생성/로드** (`:41-45`) — 폴더명은 원문이 아니라 원문에서 도출한 **영문 kebab slug** (`[a-z0-9-]` 만, 40 자 이내). 팀 용어는 임의 번역하지 말고 `workspace/context/` 도메인 문서의 코드 표기를 우선 채택 (폴더명으로 소스를 grep 하려는 목적). 축이 둘 이상 섞이거나 매핑이 모호하면 후보 2~3 개 제시 후 확정, 명확하면 결정한 slug 를 1 줄 고지.
     - **없으면**: GUIDE.md 로드 → `issues/{slug}/issue.md` 생성. H1 = 원문 1 줄 요약 (개행·`|` 제거), `## 현상` = 원문 전문, `도메인:` 라인 포함 (값은 5 단계에서 확정).
     - **있으면**: `issue.md` 만 Read (GUIDE.md 미로드), slug 재도출 안 함. 파생 산출물 (`issue.plan*.md`·`issue.eval*.md`) 이 있으면 진행 상태 요약.
  4. **STATE.md 갱신 (P2)** (`:46`) — `| issue | {slug} | 진행중 |` 1 행 교체. 기록 값은 3 단계가 확정한 **slug** (원문·제목 아님). bare 면 `| issue | - | 진행중 |`.
  5. **도메인 확정 + 컨텍스트 로드 (P3)** (`:47-49`) — 도메인 소스는 `.agent-state.yml` 이 아니라 **issue.md 의 `도메인:` 라인** (`pilot/skills/context/shared/preamble.md:64`). 라인 부재 시 **1 회 질의** 후 issue.md 상단에 `도메인: {값}` 을 Edit 기입. 판단이 어려우면 미정으로 MANIFEST 까지만 (wrapper 진입 시 재질의). bare 는 질의 없이 MANIFEST 까지만.
  6. **결과 출력 — 산출물 상태 분기** (`:50-55`, 명시적 if/elif/else 로 한 번에 하나만 안내):
     1. `issue.eval*.md` 최신 REPORT 가 READY → "조치 완료 — `## 재발 방지` 기록 여부 확인" 안내.
     2. elif `issue.plan*.md` 존재 → "챌린지 전이면 `@pilot-planner-critic`, plan 승인 후면 `@pilot-generator`" (승인 흔적이 산출물에 없어 재개 시 사용자 재확인).
     3. else → **코드 수정형** ("`@pilot-planner` 호출 — plan 은 `issues/{이슈명}/issue.plan.md`") / **조사·경미형** ("GUIDE 진단 절차로 직접 처리 후 `## 원인`·`## 조치` 기록") 로 분기.
- **이슈 폴더 구조** (`pilot/skills/context/lifecycle/issues/GUIDE.md:42-50`): `issue.md` (필수) + `issue.plan[.r{N}].md` · `issue.plan.critic[.r{N}].md` · `issue.eval[.r{N}].md`. `.r{N}` 은 **항상 마지막 `.md` 직전**, 재작업 시 기존 최대값 +1.
- **영문 slug 강제 사유** (`GUIDE.md:71`): `issues/` 는 장기 누적 자산이고 셸에서 경로를 직접 다루는 빈도가 높다. 한글 자유 문자열은 표기가 흔들려 같은 이슈에 폴더가 둘 생기고, 그러면 유사 이슈 검색이 과거 이력을 놓친다 (macOS NFD 정규화 노출면도 넓다).

---

## `/pilot:pilot-doctor`

워크스페이스·프로젝트 정합성 검사. 페르소나 **diagnostician** — "증상 → 근거 → 처방" (`pilot/skills/pilot-doctor/SKILL.md:13-16`). 검사 범위·판정 기준·출력 형식·처방은 스크립트가 출력에 전부 포함하며 **로직 SSOT 는 `pilot/tools/doctor.py`** (`pilot/skills/pilot-doctor/SKILL.md:18`).

- **기본 동작** (`pilot/skills/pilot-doctor/SKILL.md:22-30`) — 인자로 프로젝트명 전달 시 `--project {PROJECT}` 덧붙임:

  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace
  ```

  exit `0` — ERROR 없음 (PASS / WARN 만) · `1` — ERROR 1 건 이상.
- **argparse 실제 표면** (`pilot/tools/doctor.py:43-60`): 위치 인자 `workspace` (기본값 `"workspace"`) + `--project` · `--fix` · `--schema`. **그 외 플래그는 없다.**
- **플래그** (`pilot/skills/pilot-doctor/SKILL.md:32-36`):
  - `--fix` — auto-fixable 항목 자동 수정 (`.gitignore` secret 패턴 주입 · STATE.md 이력 정리 · schema 업그레이드 등).
  - `--diagnose` — **스크립트 플래그가 아니라 SKILL 지시문 모드**다. 정합성 검사와 독립적으로 런타임 실패 패턴을 진단하며, 절차는 SKILL.md § 진단 모드 가 직접 기술한다 (모델이 더 잘 판단하는 휴리스틱 패턴 매칭 — `pilot/skills/pilot-doctor/SKILL.md:18`). `pilot/tools/doctor.py:11-13` 도 "진단 모드(과거 `--diagnose`)는 스크립트 없이 SKILL.md 지시문이 수행" 을 명시한다.
  - `--schema` — 플러그인 구조 전용 (workspace 무관, `workspace` 인자 없이 실행). `.github/workflows/validate.yml` 가 CI 로 실행. 스키마 규칙은 `pilot/.claude-plugin/PLUGIN_SCHEMA_NOTES.md`.
- **임베디드 호출 시 출력 규칙 (정본)** (`pilot/skills/pilot-doctor/SKILL.md:38-40`) — 다른 스킬이 자체 흐름 마지막에 `doctor.py workspace` 를 실행할 때 (`project`·`create-feature`·`analyze` 6-5·`tdd-activation` §6) 공통 적용: ERROR·WARN 있으면 **원문 그대로 출력** (요약하면 어떤 파일·필드가 문제인지 확인 불가) · 모두 PASS 면 `doctor: all checks passed` 한 줄 · **비차단** (호출부 절차를 중단시키지 않음). 호출부는 재서술 없이 이 절 참조만 남긴다.
- **진단 모드 절차** (`pilot/skills/pilot-doctor/SKILL.md:42-66`) — 대상 프로젝트 = `--project` 또는 STATE.md 진행중 (없으면 안내 후 종료):
  1. **캡처** — `projects/{project}/` 의 `.plan.md`·`.focus.md`·`project.md`·`.agent-state.yml` Read (없으면 조용히 skip).
  2. **패턴 판정** — 4 패턴 모두 확인. 동시 감지 시 우선순위 `red-miss` > `repeat-not-ready` > `scope-violation` > `loop` 로 1 건 채택 + "(+N 다른 패턴 동시 감지)" 부기, confidence `medium`. 정확히 1 건이면 `high`, 0 건이면 `none`.

     | 패턴 | 판정 기준 | recommended_action |
     | --- | --- | --- |
     | `loop` | `.plan.md` 에서 동일 서술 줄 (20~120 자, 헤더·인용·짧은 리스트 제외) 3 회 이상 반복 | feature 재분할 — planner 재호출 또는 스텝 축소 |
     | `red-miss` | `tdd: true` **이고** `.plan.md` 스텝 헤더 수 대비 `[Red]` 마킹 부족 | generator 재호출 시 `[Red]`/`[Green]` 증거 기록 강제 |
     | `repeat-not-ready` | `.plan.md`+`project.md` 에서 `status: NOT_READY`·"반려"·"재수행 요청"·"재작성 요청" 합계 2 회 이상 | planner 재진입 — spec 또는 scope 재정의 |
     | `scope-violation` | `.focus.md` scope 패턴과 `git diff --name-only` (CWD = 서비스 레포) 대조해 scope 밖 파일 존재 | 편집 되돌리기 또는 `.focus.md` scope 확장 후 재진입 |

  3. **출력** — `## DIAGNOSIS` 블록 5 필드 고정: `project` · `pattern` · `evidence` · `recommended_action` · `confidence`.
  - **호출 시점** (`:35`): evaluator `NOT_READY` 2 회 / 동일 도구 반복 의심 / 완료 선언인데 체크리스트·REPORT 가 비었을 때.
- **Onboarding Health (모델 점검)** (`pilot/skills/pilot-doctor/SKILL.md:68-74`) — `doctor.py` 출력 자체에는 온보딩 섹션이 없다 (구조 정합성 검사로 축소). **스킬 경유 호출에서만** 모델이 직접 점검하며 임베디드 호출에서는 발화하지 않는다 (의도된 다운그레이드).
  - 발동 조건: MANIFEST `## 도메인 분류` 표 행 0 건 **또는** STATE.md 등록 프로젝트 0 건.
  - 점검 5 항목: config.md 3 섹션 채움 · `context/scope/` 의 `*.md` 존재 · STATE.md 프로젝트 ≥1 · MANIFEST 표 행 ≥1 · 활성 프로젝트 `features/` 의 `*.md` ≥1.
  - 처방 3 종: `/pilot:learn {진입파일}` · `/pilot:project {이름}` · `/pilot:create-feature`.
- **제약** (`pilot/skills/pilot-doctor/SKILL.md:76-80`): 순수 stdlib · **비파괴** (읽기만, `--fix` 제외) · 실패 시 fix 제안만 출력하고 자동 적용 안 함.

---

## `/pilot:focus`

대화 중 결정·방향 조정을 다음 래퍼 호출에 전달 (`pilot/skills/focus/SKILL.md:17`). 페르소나 **note-taker** — "결정만 받아 적는다. 해석·확장 금지" (`pilot/skills/focus/SKILL.md:12-15`).

- **인자**: 지시문 또는 `--clear`. 둘 다 없는 빈 인자면 안내 후 종료 (`pilot/skills/focus/SKILL.md:23`).
- **사전 확인**: P1 (`pilot/skills/focus/SKILL.md:21-26`). 활성 행이 `| issue | {이슈명} |` 이어도 **종료하지 않고** 이슈를 대상으로 진행 (P1 issue 종료 규칙 예외). 단 `| issue | - |` (bare) 는 기록처가 없어 "bare issue 모드에는 focus 를 기록할 수 없습니다" 출력 후 종료.
- **경로 계약** (`pilot/skills/focus/SKILL.md:28-35`) — **orchestrate-load 가 같은 기준 (`work_mode`) 으로 읽으므로 반드시 일치**시켜야 한다 (project 활성인데 issues/ 에 쓰면 래퍼가 지시를 못 본다):
  - project 활성: `workspace/projects/{PROJECT}/.focus.md` · 아카이브 `.../.focus.history/{ISO timestamp}.md`
  - issue 활성: `workspace/issues/{이슈명}/.focus.md` · 아카이브 `.../.focus.history/{ISO timestamp}.md`
- **기록 모드** (`pilot/skills/focus/SKILL.md:39-49`): 기존 `.focus.md` 있으면 `.focus.history/{기존 기록시각}.md` 로 **이동** (파일 timestamp 헤더 기준, 없으면 mtime) — 활성 focus 는 항상 최대 1 개. 새 파일 형식은 `# Focus — {YYYY-MM-DDTHH:MM:SS}` + 지시문 본문.
- **제거 모드 (`--clear`)** (`pilot/skills/focus/SKILL.md:51-53`): 없으면 "활성 focus 가 없습니다" 후 종료, 있으면 history 로 이동 후 삭제.
- **래퍼와의 상호작용** (`pilot/skills/focus/SKILL.md:55-57`): 4 에이전트가 컨텍스트 로드 단계에서 `.focus.md` 를 Read 하고 **본 호출에 한해** 반영. **래퍼는 Read 만** — 수정·삭제·아카이브하지 않으므로 한 focus 가 여러 phase 에 걸쳐 유효하다. 해제는 사용자의 `--clear` 또는 새 focus 덮어쓰기.
- **제약** (`pilot/skills/focus/SKILL.md:59-63`): 활성 focus 최대 1 개 (여러 지시는 하나로 묶어 작성) · focus 는 **지시**이지 **사양**이 아니다 (긴 내용은 feature 명세 수정이 적합) · `.focus.md`·`.focus.history/` 는 gitignore 대상.
