# pilot + moai-adk 보완 사용 가이드

> source: V1-Full 충실성 검증 (2026-04-30) 결과 — pilot 과 moai-adk 가 다른 추상화 layer 라 보완 사용 가능

## 한 문장 요약

**pilot 으로 큰 레거시의 도메인 지식을 외부화하고, moai-adk 로 그 도메인 안에서 quality code 산출.**

## 두 도구의 추상화 layer 차이

| 차원 | pilot | [moai-adk](https://github.com/modu-ai/moai-adk) |
|------|-------|----------|
| **추상화 layer** | workspace 도메인 지식 layer | 코드 + SPEC document layer |
| **레거시 접근** | 코드에서 도메인 지식을 추출해 외부 문서화 (`/pilot:learn`) | DDD ANALYZE-PRESERVE-IMPROVE (코드 안에서 refactor) |
| **AI 활용 효율** | 도메인 지식만 load — 토큰 효율 + context 명확 | 코드 + SPEC + tests 모두 load |
| **재사용 단위** | 1 workspace / N projects (같은 도메인 지식 공유) | repo 단위 |
| **target pain** | "내 레거시 코드 너무 커서 AI 가 한 번에 이해 못 함" | "AI 에 위임해서 quality code 만들고 싶음" |
| **자동화 수준** | wrapper 호출 명시적 (planner → generator → evaluator) | autonomous (Alfred SuperAgent + Self-Verify Loop) |
| **언어 지원** | config 외부화 (사용자 자유 정의) | 18 programming languages auto-detect |

→ **두 도구는 직접 경쟁이 아닌 보완 가능.**

## 보완 사용 시나리오

### 시나리오 1: 큰 레거시 + 새 feature

```
1. /pilot:learn {레거시 진입점}  →  workspace/context/{domain}/ 산출 (도메인 지식 외부화)
2. /pilot:project {새 프로젝트}  →  workspace/projects/{P}/ 작업 틀 생성
3. /pilot:analyze {기획서} 또는 /pilot:create-feature  →  features/ 명세 작성
4. (선택) moai-adk 의 /moai run SPEC-XXX  →  features 명세를 SPEC 으로 변환해 autonomous code 산출
   또는
   pilot 의 @pilot-planner → @pilot-generator → @pilot-evaluator wrapper 흐름 진행
```

### 시나리오 2: 큰 레거시 + 부분 refactor

```
1. /pilot:characterize {레거시 모듈}  →  현재 동작 spec 포착
2. moai-adk 의 DDD cycle (ANALYZE-PRESERVE-IMPROVE)  →  behavior preservation 으로 refactor
```

### 시나리오 3: 신규 프로젝트 + 도메인 지식 미존재

```
1. moai-adk 의 SPEC-First 흐름 (사용자가 EARS spec 직접 작성)
2. (선택) /pilot:learn {산출 코드}  →  도메인 지식 추출해 보관 (다음 새 feature 위해)
```

→ pilot 은 **레거시 시나리오 우선**, moai-adk 는 **신규/일반 프로젝트 우선**.

## 결합 사용 시 운영 패턴

### workspace 구조 (pilot 기반)

```
workspace/
├── STATE.md                   ← 활성 프로젝트/이슈 추적 (pilot)
├── context/
│   ├── MANIFEST.md            ← 도메인 SSOT (pilot)
│   ├── config.md              ← 런타임 설정 SSOT (pilot)
│   └── {domain}/              ← 도메인 지식 외부화 (pilot:learn 산출)
└── projects/
    └── {project}/
        ├── .agent-state.yml
        ├── docs/              ← 기획서 (pilot:confl 또는 직접)
        ├── features/          ← 기능 명세 (pilot:analyze 또는 pilot:create-feature)
        └── prompts/           ← planner/generator/evaluator 컨텍스트 (pilot)
```

moai-adk 호출 시 위 구조의 `context/{domain}/` + `features/` 를 컨텍스트로 활용 가능. pilot 의 wrapper (planner/generator/evaluator) 는 옵션 — moai-adk 의 autonomous flow 로 대체 가능.

### 결정 기준 — 어느 도구 언제

| 상황 | 권장 도구 |
|------|--------|
| 레거시 코드베이스 (수만~수십만 라인+) 첫 진입 | **pilot** — `/pilot:learn` 으로 도메인 외부화 우선 |
| 도메인 지식 외부화 후 새 feature 구현 | **둘 다 가능** — pilot wrapper 또는 moai-adk autonomous |
| 신규 greenfield 프로젝트 | **moai-adk** 단독 — SPEC-First autonomous |
| 다국어 / 다 OS / 18 언어 | **moai-adk** — multi-language auto-detect 강점 |
| 한국 enterprise PM-Dev 협업 (Confluence/Jira/Slack) | **pilot** — 통합 편의 기능 |
| 큰 레거시의 cross-domain feature | **pilot** + 후속 `/pilot:learn` 다른 도메인 (v0.3.0 의 #09 cross-domain 가이드) |
| TDD/DDD with autonomous quality gate | **moai-adk** — Self-Verify Loop autonomous |
| TDD 사후 적용 (이미 구현 코드) | **pilot** — `/pilot:tdd` |

## 한계 인지

- **pilot 의 cross-domain 한계** (v0.2.x 시점): single domain 산출물만으로 cross-domain feature spec 부분 막힘. v0.3.0 milestone 의 #09 가이드로 처리 예정.
- **moai-adk 와 pilot 통합 자동화 미존재** (2026-04 시점): 위 결정 기준 표는 사용자가 수동 적용. 두 도구 사이 자동 routing 또는 shared context 메커니즘 없음. v1.x milestone 후 검토 가능.

## 결론

pilot 과 moai-adk 는 같은 영역 (Claude Code dev workflow) 의 **다른 추상화 layer**. 한 도구로 100% 해결 안 되는 큰 레거시 시나리오에서 두 도구 결합이 가치. 단독 사용도 valid:

- pilot 단독 — 한국 enterprise PM-Dev 협업 + 큰 레거시 + 명시적 wrapper 흐름 원할 때
- moai-adk 단독 — autonomous SPEC-First quality code + multi-language 원할 때
- 결합 — 큰 레거시 + autonomous quality 둘 다 원할 때

선택은 사용자 시나리오 fit 에 따라.
