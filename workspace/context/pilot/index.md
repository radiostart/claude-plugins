# pilot — Claude Code 플러그인 (skills 도메인)

`pilot` 은 Claude Code 플러그인 (`pilot/.claude-plugin/plugin.json:2-3` — `name: pilot` · `version: 0.14.0`) 으로 17 개의 슬래시 커맨드 스킬, 5 개의 에이전트 (`pilot/agents/`), 6 개의 훅 스크립트 (`pilot/hooks/`) 를 제공한다. 이 문서는 **`pilot/skills/` 를 진입점으로** 학습했고, 스킬이 호출하는 `tools/`·`hooks/`·`agents/` 표면은 인용 지점에서만 다룬다 (`/pilot:learn ./pilot/skills --domain pilot --force`, 2026-08-01).

> 인용 경로는 워크스페이스 루트 기준 상대 경로. 학습 원본은 `pilot/skills/{name}/SKILL.md`.

## 스킬 17 개 — 역할별 cluster

| 스킬 | 진입 파일 | 카테고리 |
| --- | --- | --- |
| `/pilot:pilot-init` | `pilot/skills/pilot-init/SKILL.md` | lifecycle |
| `/pilot:project` | `pilot/skills/project/SKILL.md` | lifecycle |
| `/pilot:issue` | `pilot/skills/issue/SKILL.md` | lifecycle |
| `/pilot:pilot-doctor` | `pilot/skills/pilot-doctor/SKILL.md` | lifecycle |
| `/pilot:focus` | `pilot/skills/focus/SKILL.md` | lifecycle |
| `/pilot:confl` | `pilot/skills/confl/SKILL.md` | spec |
| `/pilot:analyze` | `pilot/skills/analyze/SKILL.md` | spec |
| `/pilot:create-feature` | `pilot/skills/create-feature/SKILL.md` | spec |
| `/pilot:learn` | `pilot/skills/learn/SKILL.md` | spec |
| `/pilot:tdd` | `pilot/skills/tdd/SKILL.md` | modes |
| `/pilot:characterize` | `pilot/skills/characterize/SKILL.md` | modes |
| `/pilot:autopilot` | `pilot/skills/autopilot/SKILL.md` | modes |
| `/pilot:pilot-review` | `pilot/skills/pilot-review/SKILL.md` | review |
| `/pilot:code-review-init` | `pilot/skills/code-review-init/SKILL.md` | review |
| `/pilot:commit` | `pilot/skills/commit/SKILL.md` | delivery |
| `/pilot:pr` | `pilot/skills/pr/SKILL.md` | delivery |
| `/pilot:slack` | `pilot/skills/slack/SKILL.md` | delivery |

> `pilot/skills/context/` 는 스킬이 아니라 **다른 스킬·에이전트가 참조하는 자료 컨테이너**다 (`pilot/skills/context/INDEX.md:3`). 분류: `shared/`·`domain/`·`modes/`·`lifecycle/`.

## Cluster 진입

| Cluster | 진입 파일 | 다루는 스킬 |
| --- | --- | --- |
| **lifecycle** | [pilot/lifecycle.md](lifecycle.md) | workspace·세션 활성·정합성 (5) |
| **spec** | [pilot/spec.md](spec.md) | 기획서·feature·context 가공 (4) |
| **modes** | [pilot/modes.md](modes.md) | 실행 모드 전환·자율 진행 (3) |
| **review** | [pilot/review.md](review.md) | 사이클 내부 코드 리뷰 (2) |
| **delivery** | [pilot/delivery.md](delivery.md) | 외부 출력 — commit·PR·Slack (3) |

## 공통 사전 확인 (P-N) 매트릭스

스킬마다 진입 시 수행하는 공통 절차. **`pilot/skills/context/shared/preamble.md:72-90` 의 "스킬별 P 절차 적용표" 가 유일한 SSOT** — 아래는 그 표의 사본이다 (`preamble.md:70`).

| 스킬 | P-1 (진행 보드 선로딩) | P0 (관련 메모 선조회) | P1 (활성 프로젝트 확인) | P2 (STATE.md 갱신) | P3 (도메인 컨텍스트 로드) |
| --- | --- | --- | --- | --- | --- |
| `project` | ✅ | ✅ | – | ✅ | ✅ |
| `issue` | ✅ | ✅ | – | ✅ | ✅ |
| `pilot-init` | – | – | – | – | – |
| `analyze` | ✅ | ✅ | ✅ | – | – |
| `confl` | – | – | ✅ | – | – |
| `tdd` | – | – | ✅ | – | – |
| `pilot-doctor` | – | – | – | – | – |
| `focus` | – | – | ✅ | – | – |
| `create-feature` | ✅ | ✅ | ✅ | – | – |
| `commit` | – | – | ✅ | – | – |
| `learn` | ✅ | ✅ | – | – | – |
| `characterize` | – | – | ✅ | – | – |
| `autopilot` | – | – | ✅ | – | – |
| `pr` | ✅ | – | ✅ | – | – |
| `slack` | – | – | ✅ | – | – |
| `code-review-init` | – | – | – | – | – |
| `pilot-review` | – | – | – | – | – |

> P-1 은 `ToolSearch select:TodoWrite,TaskCreate,TaskUpdate` 겸용 선로딩 — 하니스 세대별로 진행 보드 도구 이름이 달라 겸용 select 로 세대 불일치를 흡수한다 (`preamble.md:11-13`).
> `pilot-init` 은 workspace/STATE.md 를 처음 만드는 스킬이라 P1 미적용 (`preamble.md:92`). `pilot-doctor` 는 P 절차 밖 — `doctor.py` 가 워크스페이스·프로젝트 해석을 자체 수행 (`preamble.md:94`). `learn` 은 workspace 부트스트랩 단계라 활성 프로젝트 없이 실행 (`preamble.md:96`). `code-review-init` 은 활성 프로젝트가 아니라 `workspace/context/` 존재만 확인 (`preamble.md:98`). `pilot-review` 는 사전 확인 없이 target 을 정해 self-contained 에이전트에 위임 (`preamble.md:100`).
> **P1 issue 예외 3 종** — 활성 행이 `| issue | ... |` 이면 기본은 `issue_active_not_project` 출력 후 종료지만, `focus` 는 issues/ 경로로 분기, `commit` 은 그대로 진행, `pilot-doctor` 는 P 절차 밖이다 (`preamble.md:38`).

## 스킬이 호출하는 플러그인 표면

| 표면 | 파일 | 스킬 쪽 호출 지점 |
| --- | --- | --- |
| 정합성 검사 | `pilot/tools/doctor.py` (인자 `workspace` + `--project`·`--fix`·`--schema`, `pilot/tools/doctor.py:43-60`) | `pilot-doctor`·`project` 9 단계·`create-feature` 5 단계·`slack` 공통 선행 |
| wrapper 컨텍스트 로드 | `pilot/tools/orchestrate-load.py` (`--phase` 필수, `pilot/tools/orchestrate-load.py:634-638`) | 4 벌 wrapper (`pilot/skills/context/shared/wrapper-protocol.md:22`) |
| plan 형식 검증 | `pilot/tools/plan-validate.py` (`--mode standard\|tdd\|characterize`, `pilot/tools/plan-validate.py:34·461-466`) | `autopilot` 1 단계 |
| autopilot 전이 결정 | `pilot/tools/auto_pilot.py` (`--phase planner\|critic\|evaluator`, `pilot/tools/auto_pilot.py:295-297`) | `autopilot` 각 단계 |
| Confluence | `pilot/tools/confluence.py` (`fetch`·`search`·`search-local`·`all`, `pilot/tools/confluence.py:847-857`) | `confl`·`project` 6 단계 |
| Slack | `pilot/tools/slack-notify.py` (`--event complete\|approval\|pr`, `pilot/tools/slack-notify.py:193-198`) | `slack`·`pr` 9 단계 |
| 훅 6 종 | `pilot/hooks/hooks.json:4-80` — SessionStart(`session-context.sh`) · PreToolUse:Bash(`commit-format.sh`→`protect-managed.sh`) · PreToolUse:Edit\|Write(`scope-guard.sh`→`protect-managed.sh`) · PostToolUse:Edit\|Write(`coding-rules.sh`) · PermissionRequest·Notification(`slack-notify.sh`) | 스킬 무관 상시 |
