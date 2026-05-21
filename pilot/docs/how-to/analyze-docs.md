# 기획서로 features 일괄 생성

!!! info "한 줄 요약"
    `docs/` 의 PM 기획서 (표 중심) 를 기능 단위로 분할해 `features/NN-{slug}.md` 일괄 생성. `project.md` 의 목표 섹션과 `prompts/{planner,generator,evaluator}.md` 의 *프로젝트 고유 사전 확인 사항* 도 자동 동기화.

## 전제

- 활성 프로젝트가 있다.
- 기획서 파일이 `workspace/projects/{PROJECT}/docs/` 에 이미 저장돼 있다 — 원격에서 가져오는 작업은 [Confluence 동기화](confluence-sync.md) 가 담당한다.
- 단건 추가는 본 스킬이 아니라 [프롬프트로 feature 단건 추가](create-feature.md) 가 적합.

## 절차

### 1. 기획서 위치 확인

```bash
ls workspace/projects/{PROJECT}/docs/
```

여러 파일이 있으면 *모든 파일* 이 분석 대상이 된다. 일부만 분석하려면 다음 step 에서 명시.

### 2. analyze 실행

```bash
/pilot:analyze
```

또는 특정 파일만:

```bash
/pilot:analyze docs/01_coupon_policy.md docs/02_refund_flow.md
```

수행하는 일:

- 각 기획서를 기능 단위 (`features/NN-{slug}.md`) 로 분할 — `NN` 은 기존 features 다음 번호부터 자동.
- `project.md` 의 목표 섹션을 갱신 (기존 `[analyze-managed]` 마커 안만 — 사용자 작성 영역은 보존).
- `prompts/planner.md`·`prompts/generator.md`·`prompts/evaluator.md` 의 *기능별 사전 확인 사항* 섹션 자동 작성.
- `.agent-state.yml` 의 `analyzed: true` 갱신.

### 3. 결과 검토

생성된 features 를 훑고 *분할 단위가 적절한지* 사용자가 판단:

```bash
ls workspace/projects/{PROJECT}/features/
```

분할이 너무 잘게 됐거나 같이 가야 할 항목이 갈라졌다면 — 직접 편집 후 `/pilot:analyze --regen-agents` 로 prompts/ 만 재생성.

### 4. 구현 진입

```
@pilot-planner
```

가장 작은 번호 feature 부터 진행. 사이클은 [Quick Start](../tutorial/quick-start.md) step 3 이후와 동일.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:analyze`](../reference/skills/analyze.md)
- :material-tools: How-to: 기획서가 Confluence 에 있다면 먼저 [Confluence 동기화](confluence-sync.md), 단일 feature 만 필요하면 [프롬프트로 feature 단건 추가](create-feature.md).
- :material-lightbulb-on: Explanation: `[analyze-managed]` 마커의 동작 원리는 [SSOT 와 derived](../explanation/index.md) 에서.
