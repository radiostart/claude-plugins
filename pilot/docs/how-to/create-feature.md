# feature 단건 추가

!!! info "한 줄 요약"
    기획서(docs) 없이 한 줄의 프롬프트 입력을 통해 단일 feature 명세를 추가합니다. `features/NN-{slug}.md` 파일을 prompt-origin 템플릿으로 생성하고, `project.md` 및 `prompts/` 내 템플릿 파일들을 `/pilot:analyze` 실행 시와 동일한 방식으로 동기화합니다.

## 전제 조건

- 활성화된 project가 존재해야 합니다.
- 추가하려는 feature가 요구사항, 조건, 기대결과 등을 한 문장으로 요약하여 *한 줄로 표현할 수 있는* 단일 단위여야 합니다.
- 기획서(`docs/`)를 기반으로 여러 feature를 분할하여 일괄 생성하려는 경우, 본 가이드 대신 [기획서 기반 feature 일괄 생성](analyze-docs.md) 가이드를 확인하십시오.

## 작업 절차

### 1. 한 줄 프롬프트 명령 실행

```bash
/pilot:create-feature "쿠폰 발급 전 사용자 자격 검증 (블랙리스트·기간 만료·중복 발급 차단)"
```

이 명령은 다음 작업을 수행합니다:

- 다음 순번으로 `features/NN-{slug}.md` 파일을 생성합니다. (`slug` 명칭은 입력 프롬프트 내용을 기반으로 자동 추출하여 `pre-issue-eligibility-check` 와 같은 kebab-case 형태로 정규화됩니다)
- 템플릿 구성: `# 제목`, `## 요구사항` (조건, 트리거, 기대결과), `## 상태 전환`, `## 비즈니스 규칙`, `## 예외 케이스`, `## Open Questions` 등의 섹션이 포함됩니다.
- `project.md` 의 목표 및 관련 파일 섹션 중 `[analyze-managed]` 마커 내부 영역을 동기화합니다.
- `prompts/planner.md`, `prompts/generator.md`, `prompts/evaluator.md` 의 *기능별 사전 확인 사항* 표에 해당 feature 행을 추가합니다.

### 2. 도메인 지정 (최초 1회 질의)

`.agent-state.yml` 파일 내에 `domain` 설정이 비어 있고 `project.md` 에서도 추출할 수 없는 경우, 사용자에게 연동할 도메인을 묻는 대화식 질의를 1회 수행한 뒤 그 결과를 `.agent-state.yml` 에 기록합니다. (이후 실행 시에는 질의가 생략됩니다)

### 3. 생성된 명세 보완

자동 생성된 `features/NN-{slug}.md` 파일을 열어 비어 있는 세부 섹션(상태 전환, 비즈니스 규칙, 예외 케이스, Open Questions 등)을 보강합니다. 세부 기획 내용을 충분히 채워 두어야 planner가 임의로 사양을 추측하거나 가정을 내리는 위험을 방지할 수 있습니다.

### 4. 구현 진행

```
@pilot-planner
```

이후의 cycle 진행 흐름은 [Quick Start](../tutorial/quick-start.md) 3단계 이후와 동일합니다.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:create-feature`](../reference/skills/create-feature.md)
- :material-tools: How-to: 추가한 feature의 요구사항이 복잡하여 계획 단계부터 꼼꼼히 검증하고 싶다면 [Critic 활용](critic-review.md) 가이드를, 외부 도메인 영역을 다루어야 한다면 [외부 도메인 연동](cross-domain-learn.md) 가이드를 먼저 확인하십시오.
- :material-lightbulb-on: Explanation: prompt-origin 및 docs-origin 에 따른 feature 속성 차이는 [컨텍스트 관리](../explanation/index.md)에서 자세히 설명합니다.
