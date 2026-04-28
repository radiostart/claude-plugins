# pilot

개발 워크플로우 플러그인 — 기획서 분석부터 코드 구현·리뷰까지 에이전트 기반으로 자동화. 정확한 버전·구성은 [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) 과 `skills/`·`agents/`·`tools/`·`hooks/` 디렉토리 참조.

플러그인은 **메커니즘** (에이전트 래퍼, 스킬, 훅, 오케스트레이션 스크립트) 만 제공한다. 도메인 지식 (비즈니스 규칙·파일 경로·상태값) 은 소비 프로젝트의 `workspace/context/` 에서 사용자가 직접 관리한다.

- **핵심 계약:** 프로젝트별 `.agent-state.yml` (machine-readable 상태) + `workspace/context/MANIFEST.md` (도메인 SSOT) + `workspace/context/config.md` (런타임 설정 SSOT)

## 목차

1. [설치 및 초기 세팅](#설치-및-초기-세팅)
2. [Quick Start](#quick-start)
3. [핵심 개념](#핵심-개념)
4. [스킬 커맨드 (13종)](#스킬-커맨드-13종)
5. [에이전트 (3종)](#에이전트-3종)
6. [전형적 워크플로우](#전형적-워크플로우)
7. [도메인 컨텍스트](#도메인-컨텍스트)
8. [Hooks & Tools](#hooks--tools)
9. [운영 — drift 감지 및 대응](#운영--drift-감지-및-대응)
10. [주의사항](#주의사항)
11. [릴리스 및 업데이트](#릴리스-및-업데이트)

---

## 설치 및 초기 세팅

### 1. 플러그인 등록

Claude Code 의 marketplace 기반 플러그인 시스템을 사용한다. 이 플러그인은 [`radiostart/claude-plugins`](https://github.com/radiostart/claude-plugins) 레포의 `pilot/` 폴더로 배포되며, 레포 루트 `.claude-plugin/marketplace.json` 에 등록돼 있다.

```
/plugin marketplace add radiostart/claude-plugins
/plugin install pilot@claude-plugins
```

- `marketplace add` — GitHub 레포를 marketplace 로 등록. 레포 루트의 `.claude-plugin/marketplace.json` 을 읽어 플러그인 목록 확인. 로컬 개발 중이라면 경로(`/path/to/claude-plugins`) 도 허용.
- `plugin install` — `{플러그인명}@{마켓플레이스명}` 형태. 마켓플레이스 이름은 `claude-plugins` (레포의 `marketplace.json` 에 정의).

설치 후 Claude Code 재시작 (또는 `/plugin reload`) 시 에이전트·스킬·훅이 자동 등록. 업데이트 반영은 `/plugin marketplace update claude-plugins` → `/plugin update pilot@claude-plugins`.

**확인:** 설치 성공 시 slash 커맨드 자동완성에 `/pilot:project`·`/pilot:init` 등이 노출되고, `@planner`·`@generator`·`@evaluator` subagent 호출 가능.

#### `/plugin` 이 막힌 환경에서의 수동 업데이트 — `pilot-update`

IDE 내장 세션·관리형 환경 등에서 `/plugin` 커맨드가 `isn't available in this environment.` 로 차단될 때, 캐시(`~/.claude/plugins/marketplaces/claude-plugins/`) 를 직접 fast-forward 하는 헬퍼 스크립트를 제공.

**설치 (1회, `~/.zshrc` 또는 `~/.bashrc` 에 추가):**

```bash
alias pilot-update='bash ~/.claude/plugins/marketplaces/claude-plugins/pilot/tools/pilot-update.sh'
```

**사용:**

```bash
pilot-update           # 원격 main 으로 fast-forward + 버전 비교
pilot-update --check   # pull 하지 않고 업데이트 유무만 확인
```

실행 후 열려있는 Claude Code 세션은 구버전 프롬프트를 이미 로드한 상태 — 새 내용 반영하려면 **세션 재시작** 필요.

### 2. 워크스페이스 부트스트랩

**권장 — `/pilot:init`** 한 줄이면 전체 구조 생성.

```
/pilot:init
```

생성물:

```
workspace/
├── STATE.md                      # 진행중 프로젝트 추적 (빈 테이블)
└── context/
    ├── MANIFEST.md               # 도메인 지식 — 자유롭게 채움
    └── config.md                 # 런타임 설정 (Ignore · 언어·도구 · commit_scopes)
```

카테고리 하위 폴더 (`scope/`·`rules/`·`enums/`) 는 **생성하지 않음**. MANIFEST.md 를 채우면서 실제 도메인 파일을 추가할 때 만든다. (`scope/{domain}.md`·`rules/{domain}.md` 경로는 플러그인 컨트랙트.)

**수동 대체:** `mkdir -p workspace/context` 후 각 파일 직접 작성. 템플릿은 `skills/context/lifecycle/setup/templates/` 참고.

### 3. MANIFEST.md 채우기 (선택)

비워둬도 `/pilot:project` 는 동작한다. 도메인을 명시하면 에이전트가 자동으로 적절한 `scope`·`rules` 를 로드한다. 자유 형식이지만 도메인 분류 표가 가장 흔히 쓰이는 패턴:

```markdown
## 도메인 분류 (예시 — 자유 형식)

| 도메인 | scope | rules | 설명 |
| ------ | ----- | ----- | ---- |
| retail | `scope/retail.md` | `rules/retail.md` | 소매 주문·환불·송장 |
```

도메인 파일을 추가한 뒤 `/pilot:doctor` 로 정합성 확인.

### 4. 환경변수 (Confluence 사용 시)

`/pilot:confl` 을 쓰려면 토큰 필요:

```bash
# 프로젝트 루트 또는 workspace/ 에 .env
cat > .env <<'EOF'
CONFLUENCE_EMAIL=user@example.com
CONFLUENCE_TOKEN=your-api-token
EOF
echo ".env" >> .gitignore
```

shell profile `export` 도 가능. 둘 다 있으면 env var 우선. 토큰 발급: https://id.atlassian.com/manage-profile/security/api-tokens

> **credential drift 주의** — `.env` 와 export 값이 다르면 `/pilot:doctor` 가 WARN 출력. interactive/non-interactive shell 간 토큰 불일치로 401 이 조용히 나는 패턴을 차단한다. Batch 13 신설.

### 5. Python 의존성 (Confluence 사용 시)

```bash
pip install requests beautifulsoup4
```

---

## Quick Start

실제 소요 시간은 상황에 따라 다르다:

- **신규 즉시 시작:** `init` → `project` 한 줄로 **수 분 내** (모든 파일 비워두고 시작 가능 — fallback 동작).
- **첫 도메인 지식 채우기:** 코드 작업 중 필요해지는 순간 점진적, 첫 scope/rules 1 쌍 작성 **10~30 분**.
- **MANIFEST 이미 정리됨:** 신규 프로젝트 시작부터 첫 feature 구현까지 **10~20 분**.
- **기존 프로젝트 재개:** 한 커맨드 (`/pilot:project {이름}`) 로 즉시.

### 최소 커맨드 시퀀스

```
# 1. (1회) 워크스페이스 부트스트랩
/pilot:init

# 2. (선택) MANIFEST.md 편집 — 아래 "MANIFEST 최소 채우기" 참고

# 3. 프로젝트 시작
/pilot:project MyFeature

# 4. (선택) 기획서 가져와서 분석 / docs 없이 단건 추가
/pilot:confl https://wiki.example.com/pages/12345
/pilot:analyze
# 또는 docs 없이 프롬프트로 단건 추가:
# /pilot:create-feature "지연 주문 목록 UI"

# 5. 3-phase 구현 — 각 에이전트를 명시 호출
@planner        # features/NN-*.md → features/NN-*.plan.md 계획 수립
@generator      # plan 기반 구현 (TDD 면 Red→Green→Refactor)
@evaluator      # 요구사항 충족·spec·VERIFICATION REPORT

# 6. (선택) 중간에 방향 조정
/pilot:focus 소프트 딜리트는 빼줘

# 7. 커밋
/pilot:commit
```

### MANIFEST 최소 채우기

신규에서 2단계 (MANIFEST 편집) 는 **사실상 0 작업** — 모든 파일이 fallback 으로 동작한다:

| 파일 | 미작성 시 |
| --- | --- |
| `context/MANIFEST.md` | 비워둬도 OK (자유 작성, 강제 X) |
| `context/config.md` | 미존재면 파서가 해당 검증만 skip 하고 통과. toolchain 키 fallback 으로 Ruby 만 동작 |
| `context/scope/{domain}.md` · `rules/{domain}.md` | `_(추가 예정)_` 또는 미존재여도 OK |

도메인 등록을 시작하려면 `MANIFEST.md` 에 자유 형식으로 분류만 적으면 된다:

```markdown
## 도메인 분류 (예시 — 자유 형식)

| 도메인 | scope | rules | 설명 |
| ------ | ----- | ----- | ---- |
| retail | `scope/retail.md` | `rules/retail.md` | 소매 주문 |
```

> **`## 카테고리` 표는 적지 않아도 된다** — 플러그인이 `scope/{domain}.md` · `rules/{domain}.md` 경로를 자동으로 인식 (컨트랙트).
>
> **`## Ignore` · `## 언어·도구 기본값` · `## 설정` 은 `config.md` 에 둔다.** MANIFEST 에 적으면 파서가 인식하지 않는다.

이후 `context/scope/retail.md` · `context/rules/retail.md` 를 작성. 첫 도메인 파일 1 쌍을 `_(추가 예정)_` 로 두고 시작해도 `/pilot:project` 는 동작한다 — 실제 코드 작업 전까지 채우면 충분.

`/pilot:analyze` 가 docs/ → features/\*.md 벌크 생성. 구현은 사용자가 `@planner → @generator → @evaluator` 를 명시 호출. 각 phase 에서 중단·수정 가능한 투명한 흐름. ad-hoc 지시는 `/pilot:focus` 로 `.focus.md` 작성.

---

## 핵심 개념

### 스킬 vs 에이전트

| 종류 | 호출 | 역할 |
|---|---|---|
| **스킬** | `/pilot:{이름}` | 환경 세팅·데이터 준비 (상태 파일 작성, 기획서 저장, 분석 등) |
| **에이전트** | `@{이름}` | 실제 개발 작업 (계획·구현·검토) — **별도 인스턴스** 로 실행 |

일반 흐름: **스킬로 환경 준비 → 에이전트로 작업 수행**.

### `agents/` 폴더 2 가지 (혼동 주의)

플러그인과 프로젝트 양쪽에 `agents/planner.md` · `generator.md` · `evaluator.md` 가 존재한다. **이름은 같지만 성격이 다르다**:

| 위치 | 정체 | `@planner` 호출 시 | 편집 효과 |
|---|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/agents/{phase}.md` | **Claude Code subagent 정의** (frontmatter `name:`, `tools:`) | ✅ 실제 실행되는 wrapper | 플러그인 업데이트로만 변경 |
| `workspace/projects/{PROJECT}/agents/{phase}.md` | **프로젝트 컨텍스트 문서** (마크다운) | wrapper 가 Read 로 내용만 참고 | 다음 `@{phase}` 호출에 반영 |

즉 프로젝트 쪽 파일은 Claude Code subagent 레지스트리에 등록되지 않는다. wrapper 가 진입 시 `tools/orchestrate-load.py` 결과에 따라 Read 로 불러들이는 **입력 자료**. wrapper 의 절차·tool 권한·model 은 플러그인 쪽에서만 선언된다.

**따라서:**

- 프로젝트 `agents/*.md` 편집은 다음 `@{phase}` 호출에 반영되지만, `<!-- [analyze-managed] -->` 섹션은 다음 `--regen-agents` 에서 덮어쓰인다 → 커스텀은 주석 없는 섹션에.
- wrapper 의 **동작 자체** (단계 순서, tool 허용 범위, model) 를 바꾸려면 플러그인 수정 필요.
- 상세: [`skills/context/lifecycle/projects/agents-scaffold-notes.md`](skills/context/lifecycle/projects/agents-scaffold-notes.md).

### state 파일 2 가지

- `workspace/STATE.md` — 워크스페이스 레벨. **현재 활성 1행만** 유지 (헤더 + 진행중 프로젝트 한 줄). `/pilot:project` / `/pilot:issue` 진입 시 테이블 본문을 해당 1행으로 교체 — `보류`·`완료` 같은 이력 행을 누적하지 않는다 (이력은 `git log workspace/STATE.md` 로). `doctor` 가 이력 행 잔존 시 WARN + `--fix` 로 자동 정리.
- `workspace/projects/{PROJECT}/.agent-state.yml` — 프로젝트 레벨 (현재 schema **v1.2**). `{schema, analyzed, tdd, domain}` + optional `{mode, analyzed_at, last_analyzed_features, docs_last_fetched_at, plugin_version, pr_base_branch}`. 래퍼가 pre/post-analyze 분기에 사용. `plugin_version` 이 현재 플러그인과 minor 이상 차이 나면 wrapper 진입 시 `--regen-agents` 권장 WARN. `pr_base_branch` 는 `/pilot:pr` 가 사용자 명시 입력 시 기록 (PR 자동 타겟).

state.yml 은 **machine-readable 계약**. 스트링 detection 으로 인한 drift 위험을 구조적으로 차단. 상세: `skills/context/lifecycle/state-schema.md`.

### workspace 구조

```
workspace/
├── STATE.md                                # 진행중 프로젝트 (한 줄)
├── context/                                # 지식·설정 (수동 유지)
│   ├── MANIFEST.md                         # 도메인 지식 — 자유롭게 정의
│   ├── config.md                           # 런타임 설정 (Ignore · 언어·도구 기본값 · commit_scopes; 파서 대상)
│   ├── scope/{domain}.md                   # 도메인별 scope (플러그인 컨트랙트)
│   ├── rules/{domain}.md                   # 도메인별 규칙 (플러그인 컨트랙트)
│   ├── pr.md                               # (선택) PR 컨벤션 — 플러그인 default 대체
│   ├── coding.md                           # (선택) 코딩 컨벤션 — `conventions_doc` 키가 가리키는 경로
│   └── {카테고리}/...                       # 예: enums/, testing/, evals/ 등 자유
├── projects/{PROJECT}/                     # /pilot:project 가 생성
│   ├── project.md                          # 오케스트레이터
│   ├── .agent-state.yml                    # machine-readable 상태
│   ├── agents/
│   │   ├── planner.md                      # 프로젝트 고유 사전 확인
│   │   ├── generator.md                    # 기술 레퍼런스
│   │   └── evaluator.md                    # 체크리스트
│   ├── docs/{page_id}_{slug}.md            # /pilot:confl 가 저장
│   ├── features/{NN}-{slug}.md             # /pilot:analyze 가 생성
│   ├── features/{NN}-{slug}.plan.md        # @planner 가 자동 생성
│   ├── .focus.md                           # /pilot:focus 사용자 지시
│   ├── .focus.history/                     # 아카이브
│   └── .agents.bak/                        # regen 백업
└── issues/{이슈명}/
    └── issue.md
```

**경계:**

- `context/` 는 사용자가 손으로 유지하는 **지식·설정 저장소**
- `projects/`·`issues/` 는 스킬이 만들고 갱신하는 **작업 상태**

**Override 순서:** 언어·도구 기본값은 `workspace/context/config.md` → `project.md` 제한사항 순으로 적용된다. project.md 에 같은 키가 있으면 그 값이 최종.

**산문 컨벤션 fallback:** `pr.md`·`coding.md` 같은 컨벤션 산문은 `workspace/context/{이름}.md` 에 두면 플러그인 내장 default (`${CLAUDE_PLUGIN_ROOT}/skills/context/shared/{이름}.md`) 를 **완전 대체**.

### pre/post-analyze 게이트

래퍼 에이전트는 `.agent-state.yml` 의 `analyzed` 필드로 분기:

| 값 | 동작 |
|---|---|
| `true` (post-analyze) | `agents/*.md` 가 analyze 주입 압축본. 도메인 scope 원본 재로드 생략 |
| `false` (pre-analyze) | MANIFEST 가 선언한 도메인 scope 파일을 fallback 로드 |

**`analyzed` 필드를 수동 편집하지 말 것.** `/pilot:analyze` 가 유일한 정식 writer.

### `<!-- [analyze-managed] -->` 주석

agent 파일 안에서 analyze 가 주입·덮어쓸 섹션을 마크. 해당 주석이 붙은 섹션은 **수동 편집 금지** (다음 regen 시 사라짐). 커스텀 내용은 주석 없는 별도 섹션에 작성.

---

## 스킬 커맨드 (13종)

> **도메인 컨텍스트 로드는 보조 자료**로 분류됨. `/pilot:project`·`/pilot:issue` 가 진입 시 [`shared/preamble.md`](skills/context/shared/preamble.md) 의 P3 단계에서 자동 수행. 자료 인덱스는 [`skills/context/INDEX.md`](skills/context/INDEX.md) 참조.

### 부트스트랩·활성화

#### `/pilot:init`

워크스페이스 초기화. STATE.md + MANIFEST.md + config.md 스켈레톤. idempotent.

#### `/pilot:project {PROJECT} [URL] [--tdd]`

프로젝트 활성화. 처음이면 폴더·`.agent-state.yml` 생성. URL 주면 Confluence fetch + analyze 자동 수행. `--tdd` 로 TDD 모드 적용.

#### `/pilot:issue [이슈명]`

운영 이슈 처리 모드. 이슈명 생략 시 즉시 모드.

### 기획서·분석

#### `/pilot:confl {URL | keyword | all}`

Confluence 페이지를 `docs/` 에 저장하거나 저장된 내용 검색.

```
/pilot:confl https://wiki.example.com/pages/12345    # 저장
/pilot:confl 배송상태                                  # 검색
/pilot:confl 배송상태 > project.md 요구사항 정리       # 검색 + 작업
/pilot:confl all                                       # 전체 출력
```

#### `/pilot:analyze [keyword | filename | --regen-agents] [--force]`

`docs/` → `features/` 기능별 명세. project.md 목표 + agents/*.md 자동 갱신.

- **`--regen-agents`**: docs 변화 없어도 agents/*.md 만 재작성 (drift 대응). **자동 백업** 수행 (`.agents.bak/{timestamp}/`) 후 post-check 중복 섹션 감지.
- **`--force`**: 기존 features 덮어쓰기. **prompt-origin features 감지 시 사용자 승인 대기** (데이터 손실 방지).

#### `/pilot:create-feature "{지시문}"`

docs 없이 프롬프트로 단일 기능 명세 추가. `features/NN-{slug}.md` 를 prompt-origin 템플릿으로 작성하고 **`/pilot:analyze` 와 동일한 절차로 `project.md` (목표·관련 파일) 와 `agents/*.md` 를 자동 동기화**. 기존 features 의 `[analyze-managed]` 섹션 내용은 보존된다. 도메인 미지정 시 한 번 질의 후 `.agent-state.yml` 에 기록. 구현은 `@planner` 부터 사용자가 명시 호출.

### 작업 지원

#### `/pilot:focus "{지시}"` / `/pilot:focus --clear`

사용자 지시를 `.focus.md` 에 기록 → 다음 `@planner`·`@generator`·`@evaluator` 호출 시 자동 반영. **메인 대화의 의도가 서브에이전트에 안 전달되는** 문제 해소. `--clear` 로 명시 삭제.

#### `/pilot:tdd`

이미 구현된 프로젝트에 TDD 체계 도입. project.md + agents/*.md + `.agent-state.yml` 갱신. idempotent. 신규 프로젝트는 `/pilot:project ... --tdd` 사용.

#### `/pilot:characterize [on|off]`

**레거시 코드 특화 모드.** 기존 구현의 **현재 동작을 spec 으로 포착** 하는 characterization test 사이클로 전환/복귀. `.agent-state.yml` 의 `mode: characterize` 플래그를 토글한다. `app/` 수정 잠금 — spec 만 추가하고 리팩터는 별도 사이클에서. `tdd: true` 와 동시 설정 시 characterize 가 우선 (Red 계약 → Characterization Contract). 상세 절차: `skills/context/modes/characterize.md`.

### 운영·안전망

#### `/pilot:doctor [--project PROJECT]`

workspace·project 정합성 검사. 각 skill 말미 자동 실행. 수동 실행도 가능.

검사 항목:

- workspace/ · STATE.md · context/MANIFEST.md · context/config.md 존재
- `.agent-state.yml` schema 호환성
- `analyzed` ↔ `features/*.md` 정합
- `tdd` ↔ `project.md` 의 TDD 모드 문구 정합
- `pr_base_branch` (있을 경우) ↔ `git ls-remote origin <X>` 존재 (stale 시 WARN)
- features 증가 drift (regen 권장 신호)
- scope/*.md mtime drift
- `## 플래닝 프로세스` 잔존 감지 (구식 template 잔재)
- duplicate H2 section (regen-gone-wrong 감지)
- `.env` ↔ env var credential drift

**doctor 는 3 모드 + 자동 수정 플래그 (`tools/doctor.py` 진입점):**

| 모드 | 호출 | 언제 쓰나 | 대상 |
|---|---|---|---|
| default | `doctor.py workspace [--project X]` | 매 skill 완료 후 자동. 수동 진단 시. | workspace 구조 · `.agent-state.yml` · managed 섹션 |
| `--fix` | `doctor.py workspace --fix` | default 에서 `auto-fixable` 표시된 WARN/ERROR 일괄 수정. | whitelist 대상 (state schema 업그레이드 · 구식 template 잔재 등) |
| `--schema` | `doctor.py --schema` | 플러그인 구조 회귀 검증. 푸시 전 로컬에서 실행. | `.claude-plugin/plugin.json` · `hooks/hooks.json` · SKILL frontmatter · 버전↔태그 |
| `--diagnose` | `doctor.py workspace --diagnose` | evaluator NOT_READY 2 회 연속, 에이전트 루프·Red 증거 누락 의심 시. | `.plan.md`·`project.md`·`.focus.md` 4 패턴 매칭 |

`--diagnose` 감지 패턴: `loop` (동일 작업 반복) · `red-miss` (`tdd:true` 인데 Red 증거 누락) · `repeat-not-ready` (같은 feature 2 회+ 반려) · `scope-violation` (`.focus.md` scope 외 편집). exit 0 = 정상, exit 1 = 패턴 감지. 상세: [`skills/doctor/SKILL.md`](skills/doctor/SKILL.md).

### 마무리

#### `/pilot:commit`

변경 파일 확인 + 커밋 메시지 규칙 적용 (scope: description, 한글, 50자 권장). 허용 scope 목록은 `workspace/context/config.md` `## 설정` 의 `commit_scopes` 행에서 로드 (부재 시 `feat,fix,refactor,skills,chore,docs,test,wip` fallback).

#### `/pilot:pr [--draft] [--base <branch>] [--no-slack] [--title "..."]`

현재 브랜치를 GitHub PR 로 올린다. base branch 결정 우선순위:

1. `.agent-state.yml` 의 `pr_base_branch` (이전에 명시 입력 → 저장됨)
2. `workspace/context/config.md` 의 `pr_default_base` (default, 미선언 시 하드 fallback `develop`)

**자동 타겟팅 흐름:**

- state 에 값 있음 → "타겟: <X> (저장됨). Enter=유지 / 입력=변경" 한 줄 confirm. Enter 면 그대로 사용 (state 변경 없음), 새 입력은 state 갱신.
- state 에 값 없음 → "타겟 브랜치? (Enter=<default>)" 질의. Enter (default 채택) 면 **state 미저장**, 명시 입력은 state 에 `pr_base_branch` 신규 기록.

PR 생성 직전 `git ls-remote --exit-code origin <base>` 로 stale 검증, 없으면 재질의 (최대 3회). uncommitted 변경 있으면 `/pilot:commit` 안내 후 종료. 본문은 `skills/context/shared/pr.md` (또는 워크스페이스 override `workspace/context/pr.md`) 의 컨벤션을 따라 자동 작성. `.slack.env` 활성 시 PR URL 알림.

### 알림 (선택)

#### `/pilot:slack [test | status | disable]`

프로젝트별 Slack Incoming Webhook 으로 작업 완료·승인 요청을 자동 알림. **설정한 프로젝트만** 활성화 (미설정 프로젝트는 완전 no-op).

**서브커맨드:**

| 인자 | 동작 |
| --- | --- |
| (없음) | 현재 활성 프로젝트에 `.slack.env` 생성 + 대화식으로 채널·이벤트 설정 |
| `test` | 현재 설정으로 테스트 메시지 1건 발송 |
| `status` | `.slack.env` 존재·필드·gitignore 보호·tracked 여부 요약 |
| `disable` | 비활성화 방법 안내 (`.slack.env` 삭제) |

**설정 SSOT:** `workspace/projects/{PROJECT}/.slack.env`

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_CHANNEL=#my-channel            # 표시용 라벨
SLACK_EVENTS=complete,approval        # 생략 시 둘 다
```

**발송 이벤트:**

| 이벤트 | 트리거 | 메시지 예 |
| --- | --- | --- |
| `complete` | `@evaluator` 가 `status: READY` | `✅ [Proj] #NN 작업 완료 (evaluator READY)` |
| `approval` | 권한 다이얼로그 (PermissionRequest 훅) | `⏸ [Proj] 승인 필요: [Bash] ...` (코드블록) |
| `approval` | `@planner` 가 계획 확정 후 사용자 확인 대기 | `⏸ [Proj] 승인 필요: 계획 확인 필요: #NN ...` |

**Secret 보호 (강제):**

- `.slack.env` 는 **절대 커밋 금지**. `/pilot:doctor` 가 리포 루트 `.gitignore` 에 `.slack.env` 패턴을 **자동 주입** (사용자 확인 없이).
- 파일이 git tracked 상태로 발견되면 doctor 가 `[CRITICAL]` + exit 2 로 차단. `slack-notify.py` 도 POST 전 `git ls-files` 로 이중 확인.
- webhook URL 은 메시지 본문에 출력되지 않음. `status` 출력도 "설정됨 / 비어있음" 만 표시.

**디버그 로그** (opt-in): `export DP_SLACK_DEBUG=1` 후 Claude Code 재시작하면 `/tmp/pilot-slack-hook.log` 에 훅 호출 이력 기록.

---

## 에이전트 (3종)

`@에이전트명` 으로 호출. 별도 인스턴스로 실행되며 `tools/orchestrate-load.py` 를 통해 컨텍스트를 자동 로드.

| 에이전트 | 호출 | 역할 |
|---|---|---|
| **Planner** | `@planner` | 요구사항 분석 + 영향 범위 + 계획 수립 + plan.md 저장 |
| **Generator** | `@generator` | 계획대로 구현 + 제출 전 sanity check (언어 중립 `skills/context/shared/evals/coding.json` + 팀 `conventions_evals`) |
| **Evaluator** | `@evaluator` | 완성도 심사 + 체크리스트 평가 + 전달사항 기록 |

### 호출 순서

```
@planner → 계획 확정 → @generator → 구현 완료 → @evaluator → 검토 통과
```

순서 엄수. 이전 단계 완료 전 다음 단계 금지. 각 에이전트는 사용자가 **명시 호출** (`@planner` → `@generator` → `@evaluator`). 이전 단계 완료 후 다음 에이전트 명시 호출. 자동 파이프라인 없음 — phase 간 사용자 개입 가능.

### TDD 모드 확장

`.agent-state.yml` 의 `tdd: true` 가 설정되면 각 에이전트의 책임이 확장됨:

| 에이전트 | 기본 | TDD 모드 추가 |
|---|---|---|
| Planner | 구현 계획 | + 스텝 분할 + 실패 테스트 (Red) |
| Generator | 코드 구현 | + 실패 테스트 통과시키는 최소 구현 (Green) |
| Evaluator | 체크리스트 | + **변경 관련 테스트만** `{test_command} {paths}` 실행 |

Evaluator 가 **변경 관련 테스트만** 실행하는 게 핵심. 인자 없는 전체 스위트 실행 금지. `{test_command}` 는 `workspace/context/config.md` `## 언어·도구 기본값` 에서 해석 (예: Ruby `bundle exec rspec`, Kotlin `./gradlew test --tests`).

### Characterize 모드 확장

`.agent-state.yml` 의 `mode: characterize` 가 설정되면 **레거시 동작 포착** 사이클이 활성화된다. `/pilot:characterize [on|off]` 로 토글.

| 에이전트 | 기본/TDD | Characterize 모드 |
|---|---|---|
| Planner | Red 계약 (바뀌어야 할 동작) | **Characterization Contract** (현재 동작의 관찰된 입출력) |
| Generator | 구현 수정 | **`app/` 잠금** — spec 만 추가, 구현 변경 금지 |
| Evaluator | 변경 관련 테스트 실행 | 구현 수정 감지 시 반려. spec 이 현재 동작을 정확히 포착하는지 검증 |

핵심 차이:

- **목적**: "이 코드가 지금 뭘 하고 있는지" 를 테스트로 고정 → 이후 리팩터의 안전망
- **`tdd: true` 와 공존 시**: characterize 가 우선 (Red 가 아닌 현재 동작이 계약)
- **복귀**: 리팩터가 필요해지면 `/pilot:characterize off` 로 잠금 해제 후 표준/TDD 사이클 진행

정본 절차: `skills/context/modes/characterize.md`.

### 래퍼의 컨텍스트 로드 (내부)

각 래퍼는 첫 단계로 아래 명령을 실행해 JSON 으로 load plan 을 받음:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/orchestrate-load.py --phase {planner|generator|evaluator} --workspace workspace
```

스크립트가 state.yml·도메인·focus.md·files_to_read 를 한 번에 결정 → 래퍼는 리스트 순서대로 Read 만 수행. prose 기반 drift 위험 구조적 차단. 상세: `tools/orchestrate-load.py`.

**generator phase 자동 로드 확장:** `workspace/context/config.md` `## 언어·도구 기본값` 에 `conventions_doc` (언어·프레임워크 관행 산문) · `conventions_evals` (코드 검증 케이스 JSON) 경로가 선언돼 있으면 generator 의 `files_to_read` 에 자동 추가. 플러그인은 언어 중립 원칙(`skills/context/shared/coding.md` · `skills/context/shared/evals/coding.json`) 만 제공하고, 언어·프레임워크 고유 규칙/케이스는 워크스페이스가 공급하는 구조.

#### orchestrate-load 에러 시나리오 (래퍼 진입 실패 복구)

에러 발생 시 래퍼는 `error` 필드 원문을 출력하고 즉시 종료. 각 케이스별 복구:

| 에러 메시지 | 원인 | 복구 |
|---|---|---|
| `workspace not found: {path}` | CWD 에 `workspace/` 없음 | 올바른 디렉터리에서 호출 또는 `/pilot:init` |
| `활성 프로젝트 없음` | STATE.md 에 `진행중` 행 없음 | `/pilot:project {이름}` 로 활성화 |
| `STATE.md 에 진행중 N 개 (...)` | 진행중 프로젝트 2 개 이상 | STATE.md 편집하여 1 개로 줄이거나 `--project {이름}` 명시 |
| `.agent-state.yml 누락` | 프로젝트 state 파일 없음 | `/pilot:project {이름}` 재실행 또는 직접 작성 |
| `.agent-state.yml schema=... 지원되지 않음` | 스키마 버전 불일치 (현재 지원: v1.1 / v1.2) | `/pilot:doctor --fix` 로 v1.2 까지 업그레이드 또는 플러그인 업그레이드 |

에러 원문에 복구 명령이 이미 포함되어 있음. 래퍼 중단 시 원문을 그대로 읽으면 다음 행동 명확. 소스: [`tools/orchestrate-load.py`](tools/orchestrate-load.py).

---

## 전형적 워크플로우

### A. 신규 기획서로 기능 구현

```
/pilot:project MyFeature https://wiki.example.com/pages/12345 --tdd
  # → 프로젝트 생성 + Confluence fetch + analyze 실행 + TDD 모드

@planner       # features/01-{slug}.md → plan 수립 → 사용자 확인
@generator     # plan 기반 구현 (TDD 면 Red→Green→Refactor)
@evaluator     # VERIFICATION REPORT + project.md 목표 체크

/pilot:commit
```

### B. 중간에 방향 조정

```
@planner 로 계획 받음 → 사용자가 "소프트 딜리트 빼자" 결정

/pilot:focus "소프트 딜리트는 archived_at 타임스탬프로 대체"
  # .focus.md 기록

@planner              # 지시 반영된 새 계획
@generator
@evaluator
```

### C. Trivial 변경 (우회 정식 경로)

오타·주석·상수 같은 변경은 **3-phase 파이프라인을 강제하지 않는다**. criteria 모두 만족 시 메인 대화에서 직접 처리:

- 변경 파일 1~2 개
- 로직 변경 아님
- 기존 테스트 영향 없음
- `/pilot:doctor` ERROR 없음

규칙 위반 아닌 **정식 선택지**. 큰 변경만 pipeline 을 탄다.

### D. Drift 대응 — 오래된 프로젝트 재개

```
/pilot:project OldFeature    # 활성화
/pilot:doctor                # 실행 — drift WARN 확인

# WARN: features 증가 / scope mtime / duplicate section
/pilot:analyze --regen-agents
  # 자동 백업 (.agents.bak/{ts}/) + agents/*.md 재생성 + post-check

# post-check 에 duplicate 발견되면 백업과 비교해 수동 머지
```

### E. 새 워크스페이스 도입

```
# 다른 저장소에 워크스페이스 셋업
/pilot:init
# → MANIFEST.md 편집으로 도메인 정의
# → 도메인별 scope/rules 작성
/pilot:project {첫 프로젝트}
```

저장소마다 workspace 1 개. 같은 플러그인이 여러 저장소에서 독립적으로 동작.

---

## 도메인 컨텍스트

### SSOT 는 MANIFEST.md

`workspace/context/MANIFEST.md` 가 도메인 지식의 진입점. 도메인 분류·판단 기준·공통 모델/서비스 등은 **자유롭게 구조를 정의**한다 (플러그인은 파싱하지 않음). 단, `scope/{domain}.md` · `rules/{domain}.md` 경로는 플러그인 컨트랙트로 강제. 런타임 설정 (Ignore · 언어·도구 · commit_scopes) 은 같은 폴더의 `config.md` 에서 분리 관리.

에이전트·스킬은 **탐색·코드 수정 전 반드시 MANIFEST.md 먼저 로드**. 거기에 선언된 카테고리·로딩 시점을 따름.

### 작성 방법 (카테고리 설계)

**기본 카테고리 (`scope`, `rules`) 는 플러그인 컨트랙트로 강제** — 별도 선언 없이 `scope/{domain}.md` · `rules/{domain}.md` 경로면 자동 로드. **추가 카테고리** (예: `enums`, `policies`) 를 만들 때만 MANIFEST 에 명시한다.

**1 단계 (선택) — 추가 카테고리 선언.** 기본 외 카테고리를 쓰려면 `(이름, 로딩 시점, 경로 패턴, 역할)` 4 요소로 기술:

```markdown
## 카테고리 (선택 — 기본 외 추가 시만)

| 카테고리 | 로딩 시점       | 경로 패턴           | 역할                       |
| -------- | --------------- | ------------------- | -------------------------- |
| enums    | 상태값 참조 시  | `enums/{domain}/{Model}.md` + `enums/INDEX.md` | 상태·유형 정의 |
| policies | 정책 참조 시   | `policies/{domain}.md` | 정책 문서 |
```

다른 팀이면 `domain/`, `contracts/` 등 자유 명명 가능. 각 카테고리가 **언제** 로드되는지가 중요하다 (이 메타데이터로 에이전트가 로딩 시점 판단).

**2 단계 — 도메인 분류 테이블.** MANIFEST 에서 도메인별로 어떤 카테고리 파일이 있는지 매핑:

```markdown
## 도메인 분류

| 도메인 | scope            | rules            | 설명                 |
| ------ | ---------------- | ---------------- | -------------------- |
| retail | `scope/retail.md`| `rules/retail.md`| 소매 주문·환불·송장   |
```

**3 단계 — 실제 파일 배치.** MANIFEST 에서 선언한 경로 패턴대로 파일을 생성. 예: scope 카테고리 경로가 `scope/{domain}.md` 면 `workspace/context/scope/retail.md` 에 작성.

**4 단계 — `_(추가 예정)_` 플레이스홀더.** 아직 채울 도메인 지식이 없으면 빈 파일을 `_(추가 예정)_` 한 줄로 둠. 작업 중 채워 넣는 흐름 지원 (지식 갱신 절차 참조).

### 내용 구성 원칙

각 카테고리 파일 내부 구조는 팀이 결정하지만, 실전 효과가 좋은 패턴:

- **scope** (또는 대응 카테고리): Routes / Models / Services 표. `/pilot:analyze` 가 이 표를 파싱해 프로젝트별 `## 핵심 서비스/모델` 을 자동 추출.
- **rules** (또는 대응 카테고리): 도메인 규칙·제약을 선언적으로. 코드 스니펫보단 정책 표현. "메모 포맷은 `[{액션}({필드})]`" 같은 구체 문자열을 **여기 한 곳에** 두고 agent 파일은 참조만.
- **enums**: 한 모델당 한 파일 (`{도메인}/{Model}.md`). 상태값·전환 규칙. 상단 `INDEX.md` 로 목차.

### agent 파일 책임 경계

프로젝트 `agents/*.md` (planner·generator·evaluator) 에:

- **담을 것**: 이 프로젝트만의 서비스 시그니처·콜백·특이 비즈니스 규칙 + `## 기능별 사전 확인 사항` (analyze 주입)
- **담지 말 것** (다른 곳이 SSOT):

| 내용 | 올바른 위치 |
|---|---|
| 도메인 비즈니스 규칙 (메모 포맷·상태값 의미 등) | MANIFEST 가 선언한 `rules` 카테고리 파일 |
| 파일 경로·모델 구조 | MANIFEST 가 선언한 `scope` 카테고리 파일 |
| 상태 enum | MANIFEST 가 선언한 `enums` 카테고리 |
| 언어 중립 메타 원칙 (우선순위·수정 최소화·검증 루프) | `${CLAUDE_PLUGIN_ROOT}/skills/context/shared/coding.md` |
| 언어·프레임워크 관행 (Rails 매크로, Kotlin 코루틴 규약 등) | 프로젝트 `conventions_doc` (`workspace/context/config.md` 선언) |
| 언어·프레임워크별 코드 검증 케이스 (controller/model/service 패턴 등) | 프로젝트 `conventions_evals` (`workspace/context/config.md` 선언) |
| TDD 절차 (Red·Green·Refactor) | `${CLAUDE_PLUGIN_ROOT}/skills/context/modes/rgr.md` |
| 컨텍스트 로드·detection 로직 | 래퍼 + `orchestrate-load.py` |

> 위 카테고리 이름 (`rules`·`scope`·`enums`) 은 한 가지 컨벤션 예시. 팀이 다른 이름을 선언했다면 그 이름으로 대체.

**하드코드 금지 원칙:** 같은 사실 데이터 (예: 특정 메모 문구) 가 `generator.md` 와 `evaluator.md` 양쪽에 복사되면 sync drift 발생. 도메인 규칙은 rules 카테고리에 두고 양쪽이 "이 규칙 확인" 으로 참조.

상세: `skills/context/lifecycle/projects/GUIDE.md`.

### 지식 갱신 절차 (제안 기반)

에이전트는 context/ 지식이 실제 코드와 다름을 발견해도 **직접 수정 금지**:

1. 즉시 Edit 금지 — 발견 시 기록만
2. 사용자에게 수정안 보고 (대상·before/after·근거)
3. 승인 후에만 Edit
4. MANIFEST 영향 있으면 함께 제안
5. **예외:** `_(추가 예정)_` 플레이스홀더는 처음 채울 때 승인 없이 반영 가능 (출처 주석 필수)

---

## Hooks & Tools

### Hooks (`hooks/hooks.json`)

| Hook | Matcher | 동작 |
|---|---|---|
| `commit-format.sh` | `PreToolUse: Bash` | 커밋 메시지 형식 검증 (scope: description, 한글, 50자 권장). 허용 scope 는 config.md `## 팀 설정` 의 `commit_scopes` 에서 로드 · 부재 시 기본 CSV fallback. |
| `scope-guard.sh` | `PreToolUse: Edit\|Write` | `config.md § Ignore` SSOT. 해당 패턴 파일의 Edit/Write 차단. 담당 범위 조정은 config.md 만 수정하면 됨. |
| `slack-notify.sh` | `PermissionRequest` + `Notification` | 권한 다이얼로그·알림 이벤트를 `tools/slack-notify.py` 로 릴레이 → 프로젝트별 `.slack.env` 로 발송. 백그라운드 POST 로 비차단. 설정 없는 프로젝트는 완전 no-op. |

### Tools (`tools/`)

| 스크립트 | 용도 |
|---|---|
| `orchestrate-load.py` | 에이전트 래퍼의 컨텍스트 로드 결정 (JSON 출력). 래퍼가 내부 호출. |
| `doctor.py` | workspace 정합성 검사 + `.gitignore secret` 자동 주입 + `.slack.env` tracked 검사. `/pilot:doctor` 가 호출. |
| `confluence.py` | Confluence API 연동. `.env` fallback + credential drift 경고. |
| `slack-notify.py` | Slack Incoming Webhook 전송. 프로젝트 단위 `.slack.env` 파싱 · webhook 없으면 no-op · `git ls-files` 이중 방어 · 실패해도 exit 0 (파이프라인 차단 금지). |

## 운영 — drift 감지 및 대응

### 언제 `/pilot:doctor` 를 돌리나

- 각 skill 완료 후 **자동 실행** (Batch 8). 별도 호출 불필요.
- 수동 진단: 오래된 프로젝트 재개 전, 팀원 간 인수인계 시, 이상 동작 의심 시.

### 언제 `--regen-agents` 를 돌리나

doctor 가 아래 WARN 을 출력할 때:

| WARN | 의미 |
|---|---|
| `features {N} → {M} (증가 {K})` | features 추가됨 → agents/*.md 가 구식일 수 있음 |
| `scope/*.md mtime > analyzed_at` | 도메인 지식 업데이트됨 |
| `duplicate section: ...` | 이전 regen 에서 비표준 섹션이 중복 주입됨 (수동 머지 필요) |

또는 팀이 scope 를 크게 개편한 직후, 장기간 쉬었던 프로젝트 재개 시.

### `--regen-agents` 안전 수순

1. 실행 직전 자동으로 `.agents.bak/{ISO-timestamp}/` 에 전체 백업
2. agents/planner.md·generator.md·evaluator.md 재작성
3. `.agent-state.yml` 의 `analyzed_at` / `last_analyzed_features` 갱신
4. post-check 로 doctor 자동 실행 → 중복 섹션 감지 시 WARN + 수동 머지 권고

사용자 수동 편집 섹션 (예: `## 주의사항`, `## 구현 패턴`) 은 **`[analyze-managed]` 주석이 없으면 보존**.

### credential drift 대응

`/pilot:doctor` 에 `workspace/.env credential drift` WARN 이 뜨면 `.env` 와 env var 값이 다름. 해시 프리픽스 + 길이만 출력 (값 노출 없음). `.env` 를 올바른 값으로 동기화.

---

## 주의사항

- **플러그인은 도메인 지식을 내장하지 않는다.** `workspace/context/` 는 팀이 직접 유지.
- **`.agent-state.yml` · `STATE.md` 는 로컬 상태.** `.gitignore` 권장.
- **`.agents.bak/` · `.focus.history/` 도 로컬 복구용.** gitignore 권장.
- **래퍼 에이전트는 별도 인스턴스.** 메인 대화 컨텍스트를 못 봄 → 필요하면 `/pilot:focus` 로 전달.
- **분리된 레이어.** 스킬 (환경 세팅) vs 에이전트 (작업 수행) vs 도메인 (팀 지식) — 섞지 않는다.
- **도메인 규칙 하드코드 금지.** 프로젝트 agent 파일에 메모 문구·상태값 리스트 등을 박으면 `rules/` 와 drift. "참조만" 원칙.

## 릴리스 및 업데이트

릴리스는 `gh` CLI 로 진행합니다.

### Semver 기준 (버전 결정)

`pilot/.claude-plugin/plugin.json` 의 `version` 을 다음 기준으로 올립니다:

| 종류 | 예 | 사용 시점 |
| --- | --- | --- |
| **patch** (`0.4.x`) | `0.4.1 → 0.4.2` | 버그 수정 / 도구 내부 정리 / 테스트 추가 — 사용자 워크플로우 변화 없음 |
| **minor** (`0.x.0`) | `0.4.2 → 0.5.0` | 신규 스킬·에이전트·도구 추가 / 기존 기능 확장 |
| **major** (`x.0.0`) | `0.x → 1.0.0` | 슬래시 커맨드명 변경, state 스키마 호환 깨짐 등 사용자 측 마이그레이션 필요 |

### 릴리스 흐름

```bash
# 1. plugin.json 의 version 을 올린 PR 을 main 에 머지
#    예: pilot/.claude-plugin/plugin.json → "version": "0.4.2"

# 2. main 동기화 후 릴리스 스크립트 실행
git checkout main && git pull --ff-only
./pilot/tools/release.sh        # plugin.json 버전을 자동 인식
# 또는 명시:  ./pilot/tools/release.sh 0.4.2
```

스크립트가 수행하는 일:

- main · clean · 동기화 상태 검증
- `pilot-v{version}` 태그 생성·푸시
- `gh release create --generate-notes` 로 GitHub Release 발행


### 사용자 측 업데이트

릴리스 후 각 사용자의 Claude Code 가 새 버전을 받아가는 방법:

```
# 터미널 CLI 세션에서
/plugin update pilot@claude-plugins
```

또는 `/plugin` → `Installed` 탭 → `pilot` → Update.

> ⚠️ **앱 (데스크톱/웹) 세션은 `/plugin` 슬래시 커맨드를 지원하지 않습니다.** 터미널에서 한 번 `claude` 로 띄워 업데이트한 뒤 앱 세션을 재시작하세요.

자동: Claude Code 재시작 시 마켓플레이스 메타데이터가 새로고침되며 다음 사용 시점에 다운로드됩니다.

`/plugin` 자체가 막힌 환경 (관리형·IDE 내장 등) 은 위 ["설치 및 초기 세팅 § `/plugin` 이 막힌 환경에서의 수동 업데이트"](#plugin-이-막힌-환경에서의-수동-업데이트--pilot-update) 의 `pilot-update` 헬퍼를 사용.

### 캐시 위치

플러그인은 사용자 환경에 버전별로 캐시됩니다:

```
~/.claude/plugins/cache/claude-plugins/pilot/{version}/
```

새 버전 다운로드 후 옛 버전 폴더는 자동으로 정리되지 않습니다. 디스크 정리가 필요하면 직접 삭제:

```bash
# 예: 0.4.0 이전 버전 모두 제거
ls ~/.claude/plugins/cache/claude-plugins/pilot/
rm -rf ~/.claude/plugins/cache/claude-plugins/pilot/0.{2,3}.*
```

---

## 추가 참조

- **Lifecycle 문서 인덱스** (라우터): [`skills/context/lifecycle/INDEX.md`](skills/context/lifecycle/INDEX.md)
- 구조 가이드: [`skills/context/lifecycle/projects/GUIDE.md`](skills/context/lifecycle/projects/GUIDE.md)
- state.yml 스키마: [`skills/context/lifecycle/state-schema.md`](skills/context/lifecycle/state-schema.md)
- TDD 활성화 절차: [`skills/context/modes/tdd-activation.md`](skills/context/modes/tdd-activation.md)
- TDD 사이클 규칙: [`skills/context/modes/rgr.md`](skills/context/modes/rgr.md)
- 코딩 컨벤션: [`skills/context/shared/coding.md`](skills/context/shared/coding.md)
- 초기 세팅: [`skills/context/lifecycle/setup/README.md`](skills/context/lifecycle/setup/README.md)

## 지원 환경

Claude Code 가 실행되는 모든 환경: CLI (`claude`), Desktop App, VS Code / JetBrains 확장, Web (claude.ai/code).
