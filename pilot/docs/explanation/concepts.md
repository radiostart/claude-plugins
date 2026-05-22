# 핵심 개념

## pilot이 해결하는 문제

복잡한 project 환경에서 AI agent가 올바르게 작동하지 못하는 두 가지 *구조적 문제*가 있습니다:

### 1. 메인 대화의 의도가 subagent에게 전달되지 않는 문제

사용자가 대화 중 특정 결정을 내려도, 별도로 호출된 subagent(또는 task)는 개별 context만을 가지고 시작하므로 해당 사실을 인지하지 못합니다. 이로 인해 사용자가 동일한 지시를 반복해서 작성해야 하거나, 결정이 누락되어 엉뚱한 방향으로 구현이 진행되기도 합니다.

pilot은 이를 `.focus.md` 파일을 매개로 해결합니다. 사용자의 의도를 디스크에 기록하고, 각 subagent wrapper가 실행 시 이를 자동으로 read하여 hint로 주입합니다.

### 2. 도메인 지식이 code에만 흩어져 있어 AI가 한 번에 맥락을 파악하지 못하는 문제

대규모 레거시 codebase에서는 code를 매번 읽고 이해하는 데 따르는 context 비용이 매우 큽니다. 호출 시마다 전체 code를 다시 scan하며 핵심 도메인 사실(상태 enum, 비즈니스 규칙, 검증 순서 등)을 중복으로 분석하게 됩니다.

pilot은 `workspace/context/{domain}.md` 경로에 도메인 지식을 문서화하여 외부로 격리(SSOT)합니다. codebase에서 도메인 지식을 한 번 추출해두면(`/pilot:learn` 사용), 이후 모든 subagent가 해당 문서를 우선적으로 read하므로 token 효율과 context의 명확성을 크게 높일 수 있습니다.

## 두 가지 메타 구조

### `workspace/` — User-Facing 메타 구조

| 폴더 | 역할 |
|---|---|
| `STATE.md` | 현재 활성화된 active project 목록 (1개만 활성화 가능) |
| `context/` | 도메인 지식의 SSOT (`MANIFEST.md` 인덱스 및 세부 도메인 파일) |
| `projects/{P}/` | project별 산출물 (`.agent-state.yml`, `features/`, `docs/`, `prompts/`, `.focus.md` 등) |

### `pilot/` — 플러그인 SSOT

| 폴더 | 역할 |
|---|---|
| `agents/` | wrapper agent 정의 (planner / critic / generator / evaluator / code-review) |
| `skills/` | `/pilot:*` slash command (`SKILL.md` + `references/`) |
| `tools/` | 보조 CLI Python 도구 (`orchestrate-load`, `plan-validate`, `doctor`, `docs_build` 등) |

workspace는 사용자가 직접 수정하거나 상호작용하는 영역이며, plugin은 불변 영역입니다. drift가 감지되면 workspace를 실제 code에 동기화하거나 사용자 확인을 요청합니다.

## 명시적 호출 구조

pilot의 4개 agent 흐름은 완전히 자동화된 pipeline이 아닙니다.

```
@pilot-planner → 사용자 확인 → @pilot-planner-critic → 사용자 검토
              → @pilot-planner (수정) → @pilot-generator → @pilot-evaluator
```

각 phase 사이에서 사용자는 의사결정자(의장) 역할을 수행하며, plan을 검토하고, critic 피드백을 평가하고, 구현 및 검증 결과를 최종 승인합니다. 자동화의 편리함보다 사용자의 명확한 통제(control)를 확보하는 쪽에 초점을 맞춘 설계입니다. 단순한(trivial) 작업 시에는 번거로울 수 있지만, 대규모 리팩토링이나 기능 추가 시 엉뚱한 방향으로 진행되는 리스크를 확실히 방지합니다.

## 다음 단계

- [에이전트 흐름](agent-flow.md): 4개 agent의 역할 분리와 critic의 1.5-pass 구조
- [Workspace 레이아웃](workspace-layout.md): `workspace/` 구조와 단일 active project 제약의 이유
- [SSOT와 Derived](ssot-and-derivation.md): 데이터 및 문서의 SSOT 기준과 파생 관계
