# pilot — Claude Code 플러그인 (skills 도메인)

`pilot` 은 Claude Code 플러그인 (`pilot/.claude-plugin/plugin.json:1`) 으로 17 개의 슬래시 커맨드 스킬, 5 개의 래퍼 에이전트 (`pilot/agents/`), 5 개의 훅 스크립트 (`pilot/hooks/`) 를 제공한다. 이 문서는 **skills/ 만** 다룬다 (`/pilot:learn ./pilot/skills` 재학습, 2026-07-24).

> 본 문서의 인용 경로는 워크스페이스 루트 (`claude-plugins/`) 기준 상대 경로. 학습한 원본은 `pilot/skills/{name}/SKILL.md`.

## 스킬 17 개 — 역할별 cluster

| 스킬 | 진입 파일 | 카테고리 |
| --- | --- | --- |
| `/pilot:init` | `pilot/skills/init/SKILL.md` | lifecycle |
| `/pilot:project` | `pilot/skills/project/SKILL.md` | lifecycle |
| `/pilot:issue` | `pilot/skills/issue/SKILL.md` | lifecycle |
| `/pilot:doctor` | `pilot/skills/doctor/SKILL.md` | lifecycle |
| `/pilot:focus` | `pilot/skills/focus/SKILL.md` | lifecycle |
| `/pilot:confl` | `pilot/skills/confl/SKILL.md` | spec |
| `/pilot:analyze` | `pilot/skills/analyze/SKILL.md` | spec |
| `/pilot:create-feature` | `pilot/skills/create-feature/SKILL.md` | spec |
| `/pilot:learn` | `pilot/skills/learn/SKILL.md` | spec |
| `/pilot:tdd` | `pilot/skills/tdd/SKILL.md` | modes |
| `/pilot:characterize` | `pilot/skills/characterize/SKILL.md` | modes |
| `/pilot:autopilot` | `pilot/skills/autopilot/SKILL.md` | modes |
| `/pilot:review` | `pilot/skills/review/SKILL.md` | review |
| `/pilot:code-review-init` | `pilot/skills/code-review-init/SKILL.md` | review |
| `/pilot:commit` | `pilot/skills/commit/SKILL.md` | delivery |
| `/pilot:pr` | `pilot/skills/pr/SKILL.md` | delivery |
| `/pilot:slack` | `pilot/skills/slack/SKILL.md` | delivery |

## Cluster 진입

| Cluster | 진입 파일 | 다루는 스킬 |
| --- | --- | --- |
| **lifecycle** | [pilot/lifecycle.md](lifecycle.md) | workspace·세션 활성·정합성 (5) |
| **spec** | [pilot/spec.md](spec.md) | 기획서·feature·context 가공 (4) |
| **modes** | [pilot/modes.md](modes.md) | 실행 모드 전환·자율 진행 (3) |
| **review** | [pilot/review.md](review.md) | 사이클 내부 코드 리뷰 (2) |
| **delivery** | [pilot/delivery.md](delivery.md) | 외부 출력 — commit·PR·Slack (3) |

## 공통 사전 확인 (P-N) 매트릭스

스킬마다 진입 시 수행하는 공통 절차. **`pilot/skills/context/shared/preamble.md` 의 "스킬별 P 절차 적용표" 가 유일한 SSOT** — 아래는 그 표의 사본 + 표 밖 2 스킬 주석.

| 스킬 | P-1 (TodoWrite) | P0 (memory-hint) | P1 (활성 프로젝트) | P2 (STATE 갱신) | P3 (도메인 로드) |
| --- | --- | --- | --- | --- | --- |
| `project` | ✅ | ✅ | – | ✅ | ✅ |
| `issue` | ✅ | ✅ | – | ✅ | ✅ |
| `init` | – | – | – | – | – |
| `analyze` | ✅ | ✅ | ✅ | – | – |
| `confl` | – | – | ✅ | – | – |
| `tdd` | – | – | ✅ | – | – |
| `doctor` | – | – | – | – | – |
| `focus` | – | – | ✅ | – | – |
| `create-feature` | ✅ | ✅ | ✅ | – | – |
| `commit` | – | – | ✅ | – | – |
| `learn` | ✅ | ✅ | – | – | – |
| `characterize` | – | – | ✅ | – | – |
| `autopilot` | – | – | ✅ | – | – |
| `pr` | ✅ | – | ✅ | – | – |
| `slack` | – | – | ✅ | – | – |

> `doctor` 는 P 절차를 수행하지 않는다 — doctor.py 가 워크스페이스·프로젝트 해석을 자체 수행 (preamble.md 적용표 주석).
> `review`·`code-review-init` 은 preamble 적용표에 없다 — review 는 사전 확인 섹션 자체가 없고, code-review-init 은 P 라벨 없는 자체 사전 확인 (인자 파싱·workspace 존재 확인) 만 수행 (`pilot/skills/code-review-init/SKILL.md:18-37`).
