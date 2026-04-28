# 공통 사전 확인 절차 (SSOT)

모든 스킬이 진입 전 수행하는 공통 준비 절차. 각 스킬 SKILL.md 는 본 문서를 참조하고 자신의 고유 로직만 기술한다.

---

## P-1. TodoWrite 선로딩 (다단계 스킬 진입 시)

3 단계 이상 수행하는 스킬(`project`, `issue`, `analyze`, `create-feature`)은 **첫 tool call 로 `ToolSearch select:TodoWrite` 를 수행**한다. 직후 단계 목록을 세워 사용자에게 게시하고 진행하며 갱신한다.

TodoWrite 는 deferred tool 이므로 ToolSearch 선로딩 없이 직접 호출하면 InputValidationError 가 발생한다. 중간에 시스템 리마인더를 받고서야 로드하는 상황을 방지한다.

**미적용:** 단일 수행 스킬 (`commit`, `focus`, `doctor`, `init`, `confl`).

---

## P0. 관련 메모 선조회 (모든 스킬 공통)

`python3 ${CLAUDE_PLUGIN_ROOT}/tools/memory-hint.py "{PROJECT_OR_ARGS}" [KEYWORDS...]` 실행.

- 출력이 있으면 목록된 파일들을 Read 하여 세션 컨텍스트에 반영한다 (과거 동일 주제·유사 프로젝트의 메모).
- 출력이 비어 있으면 스킵 (정상 — auto-memory 가 없거나 매칭 없음).
- memory 파일에 stale 경고가 붙어 있으면 "verify against current code" 원칙에 따라 인용 전 소스 재확인.

auto-memory (`~/.claude/projects/{slug(cwd)}/memory/`) 는 Claude Code harness 소유. 플러그인은 **Read 만** 수행하고 생성·수정·삭제 금지.

**적용 스킬:** `project`, `issue`, `analyze`, `feature` (1차 릴리스).

---

## P1. 활성 프로젝트 확인 (project 생성·이슈 모드 제외)

`workspace/STATE.md` 를 Read 하여 `진행중` 행의 프로젝트명을 `{PROJECT}` 로 사용한다.

- 진행중 행이 없으면 [messages.md](messages.md) 의 `no_active_project` 메시지를 출력하고 종료한다.
- 진행중 행이 2개 이상이면 [messages.md](messages.md) 의 `state_corrupt` 메시지를 출력하고 종료한다.

**적용 스킬:** `analyze`, `confl`, `tdd`, `commit`

**미적용 스킬:** `project`, `issue` (자신이 STATE.md 를 갱신함)

---

## P2. STATE.md 갱신 (project / issue 진입 시)

STATE.md 는 **"지금 활성" 1행만** 유지하는 현재 상태 파일이다. 헤더 + 최대 1 데이터 행.

갱신 규칙:

- 기존 활성 행이 `{이름}` 과 동일 (모드까지): 변경 없음 (idempotent 재실행)
- 그 외 (다른 이름·모드·`보류`/`완료` 등 모든 과거 행 포함): **테이블 본문 전체 삭제 후** `| {mode} | {이름} | 진행중 |` 1 행만 추가

**원칙 — 이력은 git log 로.** `보류`·`완료` 행을 누적하지 않는다. 과거 작업 이력은 `git log workspace/STATE.md` 또는 `workspace/projects/*/` 폴더가 SSOT.

**적용 스킬:** `project`, `issue`

**갱신 전 사용자 확인:**

기존 행이 삭제되는 경우 (다른 이름으로 교체될 때), 작업 내용이 여전히 유효하면 해당 프로젝트 폴더는 그대로 남으므로 나중에 `/pilot:project {이전이름}` 로 재활성화 가능. STATE.md 행 제거 = 폴더 삭제가 아님을 사용자가 오해할 수 있으면 한 줄 안내.

---

## P3. 도메인 컨텍스트 로드 (project / issue 진입 시)

[INDEX.md](../INDEX.md) 의 "도메인별 컨텍스트 로딩" 규칙에 따라 SCOPE, DOMAIN, ENUMS 를 선택적으로 로드한다.

**적용 스킬:** `project`, `issue`

---

## 스킬별 P 절차 적용표

| 스킬        | P-1 | P0 | P1 | P2 | P3 |
| ----------- | --- | -- | -- | -- | -- |
| `project`   | ✅  | ✅ |    | ✅ | ✅ |
| `issue`     | ✅  | ✅ |    | ✅ | ✅ |
| `init`      |     |    |    |    |    |
| `analyze`   | ✅  | ✅ | ✅ |    |    |
| `confl`     |     |    | ✅ |    |    |
| `tdd`       |     |    | ✅ |    |    |
| `doctor`    |     |    | ✅ |    |    |
| `focus`     |     |    | ✅ |    |    |
| `create-feature` | ✅ | ✅ | ✅ |    |    |
| `commit`    |     |    |    |    |    |

> `init` 은 workspace 가 없는 상태에서 실행되므로 P1 을 수행하지 않는다 (workspace/STATE.md 를 처음 생성하는 스킬).

각 SKILL.md 는 "사전 확인: P-1, P0, P1 수행" 과 같이 참조만 한다. 절차 본문을 복제하지 않는다.

---

## 스킬에서 자주 쓰는 deferred 도구

ToolSearch 선로딩이 필요한 주요 도구:

| 도구 | 용도 | 로드 트리거 |
| ---- | ---- | ----------- |
| `TodoWrite` | 다단계 스킬 진행 보드 | P-1 자동 수행 |
| `WebFetch` | 외부 기획서·문서 fetch (confl 외 케이스) | URL 감지 시 |
| `AskUserQuestion` | 선택지 있는 질의 (현재 pilot 는 자유 질의 위주로 미사용) | 선택지 고정 질의가 필요한 스킬에서 옵션 |
