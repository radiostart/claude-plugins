# 기획서 기반 feature 일괄 생성

!!! info "한 줄 요약"
    `docs/` 디렉터리의 PM 기획서(표 중심)를 기능 단위로 분할하여 `features/NN-{slug}.md` 파일을 일괄 생성합니다. 이 과정에서 `project.md` 의 목표 섹션과 `prompts/` 내 planner, generator, evaluator 템플릿의 *프로젝트 고유 사전 확인 사항* 도 자동 동기화됩니다.

## 전제 조건

- 활성화된 project가 존재해야 합니다.
- 기획서 파일이 `workspace/projects/{PROJECT}/docs/` 디렉터리에 이미 저장되어 있어야 합니다 (원격 문서 연동은 [Confluence sync](confluence-sync.md) 가이드 참고).
- 단건의 feature를 추가하는 경우에는 본 가이드 대신 [feature 단건 추가](create-feature.md) 가이드를 확인하십시오.

## 작업 절차

### 1. 기획서 위치 확인

```bash
ls workspace/projects/{PROJECT}/docs/
```

해당 경로에 존재하는 모든 파일이 분석 대상이 됩니다. 특정 파일만 분석하려면 다음 단계에서 직접 경로를 지정합니다.

### 2. analyze 실행

```bash
/pilot:analyze
```

또는 특정 파일만 지정하여 실행할 수도 있습니다:

```bash
/pilot:analyze docs/01_coupon_policy.md docs/02_refund_flow.md
```

이 명령은 다음 작업을 수행합니다:

- 각 기획서를 기능 단위(`features/NN-{slug}.md`)로 분할하여 생성합니다. (`NN` 번호는 기존 features 번호 다음부터 순차적으로 부여됩니다)
- `project.md` 의 목표 섹션 중 `[analyze-managed]` 마커 내 영역을 갱신합니다 (마커 외부의 사용자 작성 영역은 보존됩니다).
- `prompts/planner.md`, `prompts/generator.md`, `prompts/evaluator.md` 의 *기능별 사전 확인 사항* 섹션을 자동 작성합니다.
- `.agent-state.yml` 의 `analyzed: true` 설정을 업데이트합니다.

### 3. 결과 검토

생성된 features 목록을 확인하고 분할 단위가 적절한지 검토합니다:

```bash
ls workspace/projects/{PROJECT}/features/
```

분할이 너무 세분화되었거나 함께 묶어야 할 항목이 분리된 경우, 해당 파일을 직접 편집한 뒤 다음 명령을 실행하여 prompt 파일들만 재생성합니다:

```bash
/pilot:analyze --regen-agents
```

### 4. 구현 진행

```
@pilot-planner
```

가장 낮은 번호의 feature부터 순서대로 진행합니다. 이후의 cycle은 [Quick Start](../tutorial/quick-start.md) 3단계 이후와 동일하게 흘러갑니다.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:analyze`](../reference/skills/analyze.md)
- :material-tools: How-to: 기획서가 Confluence에 있다면 먼저 [Confluence sync](confluence-sync.md)를 실행하고, 단일 feature만 추가하려면 [feature 단건 추가](create-feature.md)를 활용하십시오.
- :material-lightbulb-on: Explanation: `[analyze-managed]` 마커의 동작 원리는 [SSOT와 derivation](../explanation/ssot-and-derivation.md)에서 자세히 설명합니다.
