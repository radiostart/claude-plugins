# SSOT와 Derived

pilot 내에서 *Single Source of Truth(SSOT)의 대상*과 *거기로부터 파생(derived)되는 항목*이 무엇인지를 명시합니다. drift 현상이 발생하는 경계가 이 관계에 의해 결정됩니다.

## 3가지 SSOT 영역

### 1. 플러그인 코드 (`pilot/{agents,skills,tools}/`)

| SSOT 파일 | 역할 및 목적 |
|---|---|
| `pilot/agents/*.md` | wrapper agent의 동작 절차, 역할 정의, 사용할 tools 권한 설정 |
| `pilot/skills/*/SKILL.md` | slash command의 기능 정의 및 세부 동작 |
| `pilot/tools/*.py` | 보조 CLI tool 구현체 |
| `pilot/skills/context/shared/identity.yml` | agent contract (`output`, `min_evidence`) 및 agent별 역할/tone 정의 (`archetype`, `voice`, `phrasing`, `forbid`) |
| `pilot/skills/context/lifecycle/{state,plan}-schema.md` | `.agent-state.yml` 및 `plan.md` 파일의 format contract |
| `pilot/skills/context/lifecycle/drift-protocol.md` | drift 대응 규약 |

이 영역은 *plugin release 단위*로 업데이트됩니다. 사용자 workspace 내에서는 *읽기 전용*으로 취급됩니다.

### 2. 사용자 도메인 지식 (`workspace/context/`)

| SSOT 파일 | 역할 및 목적 |
|---|---|
| `MANIFEST.md` | 도메인 인덱스 정보 (도메인명 → 진입 파일 경로) |
| `config.md` | workspace 언어 및 tool의 기본 설정값 |
| `{domain}.md` 또는 `{domain}/` | 개별 도메인의 구현 code에서 추출한 핵심 비즈니스 규칙 및 사양 |

이 영역은 *구현 코드가 진화함에 따라 사용자가 직접 갱신*해야 합니다. `/pilot:learn`을 사용하여 재추출하거나 수동으로 편집합니다.

### 3. 프로젝트 산출물 (`workspace/projects/{P}/`)

| SSOT 파일 | 역할 및 목적 |
|---|---|
| `.agent-state.yml` | machine-readable 상태 값 (schema, tdd, mode, domain, plugin_version 등) |
| `project.md` | 사용자 수동 작성 내용 (목표, 제약사항, 드리프트 메모) + `[analyze-managed]` 동적 영역 |
| `features/NN-{slug}.md` | feature 요구사항 및 명세 (사용자 작성 또는 `/pilot:analyze`, `/pilot:create-feature`로 생성) |
| `prompts/{planner,generator,evaluator}.md` | project별 사전 확인 사항 (대부분 `[analyze-managed]` 영역으로 자동 관리) |

## Derived (SSOT가 아닌 항목)

| 파생(Derived) 파일 | SSOT 출처 | 갱신 트리거 |
|---|---|---|
| `pilot/README.md` (설치·부트스트랩 요약 및 문서 맵) | 본 문서 사이트의 index | 구조 및 핵심 기능 변경 시 수동 업데이트 |
| **문서 사이트 `pilot/docs/reference/`** | `agents/` · `skills/` · `tools/` · `identity.yml` | `pilot/tools/docs_build.py` 스크립트를 통해 자동 갱신 |
| `project.md` 내 `[analyze-managed]` 영역 | `features/NN-*.md` 파일 목록 및 사용자 prompt | `/pilot:analyze` · `/pilot:create-feature` 실행 시 자동 갱신 |
| `prompts/*.md` 내 *기능별 사전 확인 사항* | `features/NN-*.md` | `/pilot:analyze --regen-agents` 실행 시 자동 갱신 |
| `features/NN-*.plan.md` | `features/NN-*.md` 요구사항 및 planner의 추론 결과 | `@pilot-planner` 실행 시 자동 갱신 |
| `features/NN-*.plan.critic.md` | `plan.md` 분석 내용 및 critic의 피드백 | `@pilot-planner-critic` 실행 시 자동 갱신 |

## Drift가 발생하는 두 가지 시나리오

파생 정보(derived)가 SSOT와 어긋나는 두 가지 경로:

1. **사용자가 파생 정보(derived) 영역을 임의로 수동 편집한 경우** — 예: `prompts/planner.md` 파일의 `[analyze-managed]` 영역을 직접 수정하면, 다음 `/pilot:analyze --regen-agents` 실행 시 덮어써져 사용자 변경사항이 유실될 수 있습니다.
2. **SSOT가 변경되었으나 파생 정보(derived)가 재생성되지 않은 경우** — 예: `SKILL.md`를 수정했으나 문서 사이트의 `docs/reference/skills/{name}.md`가 이전 내용 그대로 유지되고 있는 경우

### 대응 규약

| 원인 구분 | 대응 방법 |
|---|---|
| (1) `[analyze-managed]` 영역의 수동 수정 | `/pilot:analyze` 실행 시 사용자 영역(마커 외부)은 보존하고 마커 내부만 덮어씁니다. |
| (1) `prompts/*` 파일의 수동 수정 | `--regen-agents` 실행 시 기존 내용을 `.prompts.bak/` 디렉토리에 백업한 후 업데이트를 진행합니다. |
| (2) Reference 재생성 누락 | `docs/reference/`는 gitignore 대상이며 CI가 문서 빌드 시점에 `docs_build.py`로 SSOT에서 매번 재생성하므로, reference drift는 구조적으로 발생하지 않습니다. |
| (2) `context/` 파일과 구현 코드 간의 drift | [Drift Protocol](drift-protocol.md)에 따라 탐지, 기록 및 사용자 의사결정을 수행합니다. |

## "SSOT가 한국어" 정책

pilot의 모든 SSOT(skill, agent, tool, context)는 한국어를 기본으로 작성됩니다. 영어 가이드를 별도로 두는 것은 지속적인 다국어 파생 정보(derived) 관리 부담을 초래하므로 제외했습니다. `README.md` 상단에 영문 abstract 한 단락만 작성하여 제공하고, 상세 사양은 한국어 원본 문서를 참조하도록 안내합니다.

이 정책은 주 사용자층이 한국어 사용자라는 전제하에 설계되었습니다. 향후 영문 사용자층이 확대되면 SSOT 자체를 영어로 통합하고 한국어를 파생 정보로 둘지, 혹은 병행 유지할지 재검토합니다.

## 다음 단계

- [Drift Protocol](drift-protocol.md): SSOT와 실제 code 간의 동기화 불일치 대처법
- [릴리스 · 업그레이드](release-and-upgrade.md): SSOT(특히 플러그인 코드) 변경 시 사용자 workspace 업그레이드 방법
- Reference: [`docs_build.py`](../reference/tools/docs_build.md) · [identity SSOT](../reference/identity.md)
