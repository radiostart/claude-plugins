# 핵심 개념

## pilot 이 해결하는 문제

복잡한 프로젝트에서 AI 에이전트가 잘 동작하지 않는 두 가지 *구조적 문제* 가 있습니다:

### 1. 메인 대화의 의도가 subagent 에게 안 전달된다

사용자가 메인 대화에서 "소프트 딜리트는 빼자" 라고 결정해도, subagent (Task 또는 별도 호출) 는 자기 컨텍스트만 가지고 시작합니다. 사용자가 같은 지시를 매번 다시 적거나, 또는 결정이 *암묵적으로 사라지고* 다음 작업이 다른 방향으로 갑니다.

pilot 은 이걸 `.focus.md` 매개로 해소합니다 — 사용자 지시를 디스크에 기록하고, 각 subagent wrapper 가 호출 시 자동 Read 해서 hint 로 주입.

### 2. 도메인 지식이 코드에만 있어서 AI 가 한 번에 다 못 본다

큰 레거시 코드베이스에서는 *코드를 읽는 비용* 이 너무 큽니다. 매 호출마다 같은 코드를 다시 스캔하면서 핵심 도메인 사실 (상태 enum · 비즈니스 규칙 · 검증 순서) 을 다시 추출합니다.

pilot 은 `workspace/context/{domain}.md` 에 *도메인 지식을 외부화* 합니다. 코드에서 한 번 추출하면 (`/pilot:learn`), 이후 모든 subagent 가 그 파일을 먼저 Read — 토큰 효율 + context 명확.

## 두 가지 메타구조

### `workspace/` — 사용자 facing 메타구조

| 폴더 | 역할 |
|---|---|
| `STATE.md` | 현재 *활성 프로젝트* 표 (1 개만 허용) |
| `context/` | 도메인 지식 SSOT (`MANIFEST.md` 색인 + 각 도메인 파일) |
| `projects/{P}/` | 프로젝트별 산출물 — `.agent-state.yml`·`features/`·`docs/`·`prompts/`·`.focus.md` |

### `pilot/` — 플러그인 SSOT

| 폴더 | 역할 |
|---|---|
| `agents/` | wrapper 에이전트 정의 (planner / critic / generator / evaluator / code-review) |
| `skills/` | `/pilot:*` 슬래시 커맨드 (`SKILL.md` + `references/`) |
| `tools/` | 보조 CLI Python 도구 (`orchestrate-load`·`plan-validate`·`doctor`·`docs_build` 등) |

워크스페이스는 *사용자가 만지는* 영역, 플러그인은 *불변* 영역. drift 발생 시 워크스페이스를 코드에 맞추거나 사용자에게 묻습니다.

## 명시 호출이 핵심

pilot 의 4 에이전트는 *자동 파이프라인이 아닙니다*:

```
@pilot-planner → 사용자 확인 → @pilot-planner-critic → 사용자 검토
              → @pilot-planner (수정) → @pilot-generator → @pilot-evaluator
```

각 단계 사이에 사용자가 *의장* 역할을 합니다 — plan 검토·critic 결과 평가·구현 결과 확인. 자동화의 이득과 *사용자 통제권* 의 trade-off 에서 pilot 은 후자 편입니다. trivial 변경에 비용이 들지만, 큰 변경에서는 잘못된 방향으로 빨리 가는 것을 막습니다.

## 다음

- [에이전트 흐름](agent-flow.md) — 4 에이전트의 책임 분리와 critic 의 1.5-pass 위치
- [Workspace 레이아웃](workspace-layout.md) — `workspace/` 의 구조와 단일 활성 프로젝트 강제 이유
- [SSOT 와 derived](ssot-and-derivation.md) — *어디가 SSOT* 인지의 명시적 경계
