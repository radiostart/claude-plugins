# SSOT 와 derived

pilot 에서 *어디가 single source of truth (SSOT) 인지* 와 *무엇이 그것에서 파생되는지* 를 명시한 페이지. drift 가 발생하는 *경계 라인* 이 여기서 결정됩니다.

## 3 가지 SSOT 영역

### 1. 플러그인 코드 (`pilot/{agents,skills,tools}/`)

| SSOT 파일 | 무엇의 진실 |
|---|---|
| `pilot/agents/*.md` | wrapper 에이전트의 절차·역할·tools 권한 |
| `pilot/skills/*/SKILL.md` | 슬래시 커맨드의 동작 정의 |
| `pilot/tools/*.py` | 보조 CLI 의 구현 |
| `pilot/skills/context/shared/identity.yml` | 에이전트 계약 (`output`·`min_evidence`) + 에이전트별 역할·톤 정의 (`archetype`·`voice`·`phrasing`·`forbid`) |
| `pilot/skills/context/lifecycle/{state,plan}-schema.md` | `.agent-state.yml` 과 `plan.md` 의 형식 계약 |
| `pilot/skills/context/lifecycle/drift-protocol.md` | drift 대응 규약 |

이 영역은 *플러그인 release 단위* 로 변경됩니다. 사용자 워크스페이스에서는 *읽기 전용*.

### 2. 사용자 도메인 지식 (`workspace/context/`)

| SSOT 파일 | 무엇의 진실 |
|---|---|
| `MANIFEST.md` | 도메인 색인 (도메인명 → 진입 파일) |
| `config.md` | 워크스페이스 언어·도구 기본값 |
| `{domain}.md` 또는 `{domain}/` | 각 도메인의 *코드에서 추출한* 사실 |

이 영역은 *코드가 진화하면 사용자가 갱신* 합니다. `/pilot:learn` 으로 재추출하거나 수동 편집.

### 3. 프로젝트 산출물 (`workspace/projects/{P}/`)

| SSOT 파일 | 무엇의 진실 |
|---|---|
| `.agent-state.yml` | machine-readable 상태 (schema·tdd·mode·domain·plugin_version) |
| `project.md` | 사용자 작성 부분 (목표·제한사항·드리프트 메모) + `[analyze-managed]` 영역 |
| `features/NN-{slug}.md` | feature 명세 (사용자 작성 또는 `/pilot:analyze`·`/pilot:create-feature` 생성) |
| `prompts/{planner,generator,evaluator}.md` | 프로젝트별 사전 확인 사항 (대부분 `[analyze-managed]`) |

## Derived (SSOT 가 아닌 것들)

| Derived 파일 | SSOT 출처 | 갱신 트리거 |
|---|---|---|
| `pilot/README.md` (설치·부트스트랩 요약 + 문서 맵) | 본 매뉴얼 사이트 | 수동 (사이트 구조 변경 시) |
| **본 매뉴얼 사이트 `pilot/docs/reference/`** | `agents/`·`skills/`·`tools/`·`identity.yml` | `pilot/tools/docs_build.py` 자동 |
| `project.md` 의 `[analyze-managed]` 영역 | `features/NN-*.md` + 사용자 프롬프트 | `/pilot:analyze` · `/pilot:create-feature` 자동 |
| `prompts/*.md` 의 *기능별 사전 확인 사항* | `features/NN-*.md` | `/pilot:analyze --regen-agents` 자동 |
| `features/NN-*.plan.md` | `features/NN-*.md` + planner 추론 | `@pilot-planner` 자동 |
| `features/NN-*.plan.critic.md` | `plan.md` + critic 추론 | `@pilot-planner-critic` 자동 |

## drift 의 두 종류

derived 가 SSOT 와 어긋나는 두 경로:

1. **derived 쪽에 사용자가 손을 댐** — 예: `prompts/planner.md` 의 `[analyze-managed]` 영역을 직접 편집. 다음 `/pilot:analyze --regen-agents` 가 덮어쓰면서 사용자 편집 손실 위험.
2. **SSOT 가 바뀌었는데 derived 가 재생성 안 됨** — 예: SKILL.md 를 수정했는데 사이트 `docs/reference/skills/{name}.md` 가 옛 내용 그대로.

### 대응

| 종류 | 도구 |
|---|---|
| (1) `[analyze-managed]` 사용자 침범 | `/pilot:analyze` 는 사용자 영역 (마커 밖) 을 보존, 마커 안만 덮어씀 |
| (1) `prompts/*` 사용자 침범 | `--regen-agents` 시 `.prompts.bak/` 에 백업 후 갱신 |
| (2) reference 재생성 누락 | CI 가 `docs_build.py --check` 를 PR 단계에서 실행 → 어긋나면 fail |
| (2) `context/` 와 코드의 drift | [Drift Protocol](drift-protocol.md) 에 따라 발견·기록·사용자 결정 |

## "SSOT 가 한국어" 정책

pilot 의 모든 SSOT (skill / agent / tool / context) 가 한국어로 작성됩니다. 영어 매뉴얼은 *영구 derived 부담* 이 되므로 두지 않습니다. README 상단에 영어 abstract 1 단락만 두고, 깊이 보려는 사용자는 한국어 본문을 읽습니다.

이 정책은 *사용자 베이스가 한국어 우선* 이라는 전제에 기반합니다. 영어 사용자가 늘어나면 SSOT 자체를 영어로 옮길지 (한국어를 derived 로 두기), 또는 양쪽을 동등하게 유지할지 다시 판단.

## 다음

- [Drift Protocol](drift-protocol.md) — SSOT 와 코드의 어긋남 처리.
- [릴리스 · 업그레이드](release-and-upgrade.md) — SSOT (특히 플러그인 코드) 가 진화할 때 워크스페이스가 어떻게 따라가는지.
- Reference: [`docs_build.py`](../reference/tools/docs_build.md) · [identity SSOT](../reference/identity.md).
