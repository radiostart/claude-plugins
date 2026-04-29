# pilot — Claude Code 플러그인 (skills 도메인)

`pilot` 은 Claude Code 플러그인 (`pilot/.claude-plugin/plugin.json:1`) 으로 14 개의 슬래시 커맨드 스킬, 3 개의 래퍼 에이전트, 4 개의 훅을 제공한다. 이 문서는 **skills/ 만** 다룬다 (`/pilot:learn ./pilot` b1 좁히기 결과).

> 본 문서의 인용 경로는 워크스페이스 루트 (`claude-plugins/`) 기준 상대 경로. 학습한 원본은 `pilot/skills/{name}/SKILL.md`.

## 스킬 14 개 — 역할별 cluster

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
| `/pilot:commit` | `pilot/skills/commit/SKILL.md` | delivery |
| `/pilot:pr` | `pilot/skills/pr/SKILL.md` | delivery |
| `/pilot:slack` | `pilot/skills/slack/SKILL.md` | delivery |

## Cluster 진입

| Cluster | 진입 파일 | 다루는 스킬 |
| --- | --- | --- |
| **lifecycle** | [pilot/lifecycle.md](lifecycle.md) | workspace·세션 활성·정합성 (5) |
| **spec** | [pilot/spec.md](spec.md) | 기획서·feature·context 가공 (4) |
| **modes** | [pilot/modes.md](modes.md) | 실행 모드 전환 (2) |
| **delivery** | [pilot/delivery.md](delivery.md) | 외부 출력 — commit·PR·Slack (3) |

## 공통 사전 확인 (P-N) 매트릭스

스킬마다 진입 시 수행하는 공통 절차. 본문은 `pilot/skills/context/shared/preamble.md:71-86` 의 적용표를 따른다.

| 스킬 | P-1 (TodoWrite) | P0 (memory-hint) | P1 (활성 프로젝트) | P2 (STATE 갱신) | P3 (도메인 로드) |
| --- | --- | --- | --- | --- | --- |
| `init` | – | – | – | – | – |
| `project` | ✅ | ✅ | – | ✅ | ✅ |
| `issue` | ✅ | ✅ | – | ✅ | ✅ |
| `doctor` | – | – | ✅ | – | – |
| `focus` | – | – | ✅ | – | – |
| `confl` | – | – | ✅ | – | – |
| `analyze` | ✅ | ✅ | ✅ | – | – |
| `create-feature` | ✅ | ✅ | ✅ | – | – |
| `learn` | ✅ | ✅ | – (workspace 만 필요) | – | – |
| `tdd` | – | – | ✅ | – | – |
| `characterize` | – | – | ✅ | – | – |
| `commit` | – | – | – | – | – |
| `pr` | ✅ | – | ✅ | – | – |
| `slack` | – | – | ✅ | – | – |

> 본 표는 SKILL.md 의 "사전 확인" 섹션과 preamble.md 의 적용표를 종합. SKILL.md 가 정본 — 불일치 시 그쪽 우선 (`/pilot:doctor` 가 mtime drift 감지).
