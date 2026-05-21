# 프롬프트로 feature 단건 추가

!!! info "한 줄 요약"
    docs 없이 사용자 프롬프트 한 줄로 단일 feature 명세를 추가. `features/NN-{slug}.md` 를 prompt-origin 템플릿으로 생성하고 `project.md`·`prompts/*` 를 `/pilot:analyze` 와 동일한 방식으로 동기화.

## 전제

- 활성 프로젝트가 있다.
- 추가할 feature 가 *한 줄로 표현 가능* 한 단일 단위 (요구사항·조건·기대결과를 한 문장으로 요약 가능).
- 기획서 (`docs/`) 기반 다건 분할이면 [기획서로 features 일괄 생성](analyze-docs.md) 이 적합.

## 절차

### 1. 한 줄 프롬프트로 호출

```bash
/pilot:create-feature "쿠폰 발급 전 사용자 자격 검증 (블랙리스트·기간 만료·중복 발급 차단)"
```

수행하는 일:

- 다음 번호로 `features/NN-{slug}.md` 작성 — `slug` 는 프롬프트에서 자동 추출 + 정규화 (`pre-issue-eligibility-check` 같은 kebab-case).
- 템플릿: `# 제목` · `## 요구사항` (조건·트리거·기대결과 3 축) · `## 상태 전환` · `## 비즈니스 규칙` · `## 예외 케이스` · `## Open Questions`.
- `project.md` 의 목표·관련 파일 섹션 동기화 (`[analyze-managed]` 마커 안).
- `prompts/{planner,generator,evaluator}.md` 의 *기능별 사전 확인 사항* 에 본 feature 행 추가.

### 2. 도메인 미지정 시 1 회 질의

`.agent-state.yml` 에 `domain` 이 비어 있고 `project.md` 에서도 추출 불가하면 사용자에게 한 번 묻고 `.agent-state.yml` 에 기록 — 이후 호출은 자동.

### 3. 자동 작성된 명세 보완

생성된 `features/NN-{slug}.md` 를 열어 *비어 있는 섹션* (상태 전환·비즈니스 규칙·예외 케이스·Open Questions) 을 보강한다. 빈 채로 두면 planner 가 추측·가정을 만들 위험.

### 4. 구현 진입

```
@pilot-planner
```

이후 흐름은 [Quick Start](../tutorial/quick-start.md) step 3 이후와 동일.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:create-feature`](../reference/skills/create-feature.md)
- :material-tools: How-to: feature 가 복잡해 plan 검증이 필요하면 [Critic 활용](critic-review.md). 외부 도메인을 만지면 [외부 도메인 부트스트랩](cross-domain-learn.md) 을 먼저.
- :material-lightbulb-on: Explanation: prompt-origin vs docs-origin feature 의 차이는 [컨텍스트 관리](../explanation/index.md) 에서.
