# 공통 사전 확인 절차 (SSOT)

모든 스킬이 진입 전 수행하는 공통 준비 절차. 각 스킬 SKILL.md 는 본 문서를 참조하고 자신의 고유 로직만 기술한다.

각 SKILL.md 는 "사전 확인: P-1, P0, P1 수행" 과 같이 **참조만** 한다. 절차 본문을 복제하지 않는다. 어떤 스킬이 어떤 P 를 수행하는지는 아래 **스킬별 P 절차 적용표**가 유일한 SSOT 다 — P 정의부는 절차 내용만 기술한다.

---

## P-1. 진행 보드 선로딩 (다단계 스킬 진입 시)

3 단계 이상 수행하는 스킬은 **첫 tool call 로 `ToolSearch select:TodoWrite,TaskCreate,TaskUpdate` 를 수행**하고, 로드된 것 중 가용한 도구로 단계 목록을 세워 사용자에게 게시하고 진행하며 갱신한다 — 진행 보드 도구는 하니스 세대에 따라 이름이 다르다 (구세대 `TodoWrite` / 신세대 `TaskCreate`·`TaskUpdate`). 아무것도 로드되지 않으면 텍스트 체크리스트로 대체한다 (스킬 중단 사유 아님).

진행 보드 도구는 deferred tool 이므로 ToolSearch 선로딩 없이 직접 호출하면 InputValidationError 가 발생하고, 존재하지 않는 단일 이름만 select 하면 0-결과가 된다. 겸용 select 는 중간에 시스템 리마인더를 받고서야 로드하는 상황과 세대 불일치 공회전을 함께 방지한다.

**미적용:** 단일 수행 스킬 (3 단계 미만).

---

## P0. 관련 메모 선조회

`~/.claude/projects/{slug(cwd)}/memory/MEMORY.md` 색인을 Read (`slug` = cwd 절대경로의 `/` 를 `-` 로 치환. worktree 슬롯이면 `--claude-worktrees-` 이전 부분으로 복원한 원본 cwd 의 memory/ 도 후보로 함께 확인).

- 색인 부재 시 skip (정상 — auto-memory 가 없거나 미사용).
- 색인 항목(`- [{Title}]({file}.md) — {hook}` 형식)의 title·hook·description 을 현재 작업 키워드(스킬 인자·프로젝트명)와 비교해 **관련도 높은 항목만 직접 선별해 Read**한다 (전체 파일 순회 금지 — 무관한 메모까지 열람하지 않는다).
- memory 파일에 stale 경고가 붙어 있으면 "verify against current code" 원칙에 따라 인용 전 소스 재확인.

auto-memory (`~/.claude/projects/{slug(cwd)}/memory/`) 는 Claude Code harness 소유. 플러그인은 **Read 만** 수행하고 생성·수정·삭제 금지.

---

## P1. 활성 프로젝트 확인

`workspace/STATE.md` 를 Read 하여 `진행중` 행의 프로젝트명을 `{PROJECT}` 로 사용한다.

- `workspace/STATE.md` 자체가 없으면 [messages.md](messages.md) 의 `workspace_missing` 메시지를 출력하고 종료한다 (아래 두 케이스와 구분 — 파일 자체 부재).
- 진행중 행이 없으면 [messages.md](messages.md) 의 `no_active_project` 메시지를 출력하고 종료한다.
- 진행중 행이 2개 이상이면 [messages.md](messages.md) 의 `state_corrupt` 메시지를 출력하고 종료한다.
- **진행중 행의 mode 열이 `issue` 면** (`| issue | {이슈명} | 진행중 |`): [messages.md](messages.md) 의 `issue_active_not_project` 메시지를 출력하고 종료한다 — 이슈명을 `{PROJECT}` 로 오인해 `projects/{이슈명}/` 유령 경로를 만들거나 부재 state 에 기록하는 것을 막는다. **예외:** `focus` 는 종료하지 않고 issues/ 경로로 분기한다 (focus/SKILL.md § 경로 계약), `commit` 은 종료하지 않고 진행한다 (이슈 수정 커밋은 필수 경로 — commit/SKILL.md 사전 확인 참조), `pilot-doctor` 는 P 절차 밖 (doctor.py 자체 인식).

---

## P2. STATE.md 갱신 (project / issue 진입 시)

STATE.md 는 **"지금 활성" 1행만** 유지하는 현재 상태 파일이다. 헤더 + 최대 1 데이터 행.

갱신 규칙:

- 기존 활성 행이 `{이름}` 과 동일 (모드까지): 변경 없음 (idempotent 재실행)
- 그 외 (다른 이름·모드·`보류`/`완료` 등 모든 과거 행 포함): **테이블 본문 전체 삭제 후** `| {mode} | {이름} | 진행중 |` 1 행만 추가
- issue 모드의 기록 값은 issue SKILL 3단계가 확정한 **slug** 다 — 표는 1행 규약이라 개행·`|` 가 섞이면 행 파서가 깨진다.

**원칙 — 이력은 STATE.md 에 쌓지 않는다.** `보류`·`완료` 행을 누적하지 않는다. 과거 작업 이력의 SSOT 는 `workspace/projects/*/`·`issues/*/` **로컬 폴더** 자체다 (STATE.md·projects/ 는 통상 gitignore 라 `git log` 로는 회수되지 않는다 — 저장소가 이들을 추적하는 예외 구성에서만 git log 보조 가능).

**갱신 전 사용자 확인:**

기존 행이 삭제되는 경우 (다른 이름으로 교체될 때), 작업 내용이 여전히 유효하면 해당 프로젝트 폴더는 그대로 남으므로 나중에 `/pilot:project {이전이름}` 로 재활성화 가능. STATE.md 행 제거 = 폴더 삭제가 아님을 사용자가 오해할 수 있으면 한 줄 안내.

---

## P3. 도메인 컨텍스트 로드 (project / issue 진입 시)

[INDEX.md](../INDEX.md) 의 "도메인별 컨텍스트 로딩" 규칙에 따라 SCOPE, DOMAIN, ENUMS 를 선택적으로 로드한다.

- **issue 모드**: 도메인 소스는 `.agent-state.yml` 이 아니라 **issue.md 의 `도메인:` 라인**이다 (state 파일 미신설 — 기록처는 이슈 자신의 기록물). 라인이 있으면 그 값으로 도메인 컨텍스트를 로드하고, 없으면 issue SKILL 5단계의 1회 질의가 확정 후 기입한다. orchestrate-load 도 같은 라인을 파싱하므로 wrapper 사이클과 소스가 일치한다.

---

## 스킬별 P 절차 적용표

**이 표가 스킬별 P 절차 적용의 유일한 SSOT 다.** 각 SKILL.md 의 "사전 확인" 선언과 이 표가 어긋나면 둘 중 하나가 drift — doctor 점검 대상.

| 스킬             | P-1 | P0 | P1 | P2 | P3 |
| ---------------- | --- | -- | -- | -- | -- |
| `project`        | ✅  | ✅ |    | ✅ | ✅ |
| `issue`          | ✅  | ✅ |    | ✅ | ✅ |
| `init`           |     |    |    |    |    |
| `analyze`        | ✅  | ✅ | ✅ |    |    |
| `confl`          |     |    | ✅ |    |    |
| `tdd`            |     |    | ✅ |    |    |
| `pilot-doctor`   |     |    |    |    |    |
| `focus`          |     |    | ✅ |    |    |
| `create-feature` | ✅  | ✅ | ✅ |    |    |
| `commit`         |     |    | ✅ |    |    |
| `learn`          | ✅  | ✅ |    |    |    |
| `characterize`   |     |    | ✅ |    |    |
| `autopilot`      |     |    | ✅ |    |    |
| `pr`             | ✅  |    | ✅ |    |    |
| `slack`          |     |    | ✅ |    |    |
| `code-review-init` |   |    |    |    |    |
| `review`         |     |    |    |    |    |

> `init` 은 workspace 가 없는 상태에서 실행되므로 P1 을 수행하지 않는다 (workspace/STATE.md 를 처음 생성하는 스킬).
>
> `pilot-doctor` 는 P 절차를 수행하지 않는다 — doctor.py 가 워크스페이스·프로젝트 해석을 자체 수행한다.
>
> `learn` 은 workspace 부트스트랩 단계라 활성 프로젝트 없이 실행 가능 — P1 을 수행하지 않는다.
>
> `code-review-init` 은 활성 프로젝트가 아니라 `workspace/context/` 존재 여부만 확인한다 (`messages.md` 의 `workspace_missing` 참조) — P1 미적용.
>
> `review` 는 사전 확인 없이 target 을 결정해 `@pilot-code-review` 에 위임한다 (그 에이전트가 self-contained).

---

## 스킬에서 자주 쓰는 deferred 도구

ToolSearch 선로딩이 필요한 주요 도구:

| 도구 | 용도 | 로드 트리거 |
| ---- | ---- | ----------- |
| `TodoWrite` / `TaskCreate`·`TaskUpdate` | 다단계 스킬 진행 보드 (하니스 세대별 택일 — 겸용 select) | P-1 자동 수행 |
| `WebFetch` | 외부 기획서·문서 fetch (confl 외 케이스) | URL 감지 시 |
| `AskUserQuestion` | 선택지 있는 질의 (현재 pilot 는 자유 질의 위주로 미사용) | 선택지 고정 질의가 필요한 스킬에서 옵션 |
