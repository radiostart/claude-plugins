---
hide:
  - navigation
  - toc
---

# pilot

도메인 지식 기반의 agent workflow 플러그인입니다. Claude Code 내에서 *plan → critic → generate → evaluate*의 명시적 cycle로 project를 진행합니다.

!!! tip "v0.8.0 highlights"
    - **구조 감사 전면 반영** — prose 반복 지시를 기계 계층으로 이관 (orchestrate-load 가 `instructions` 필드로 공통 지시 emit, instincts.yaml 폐지, 스킬·에이전트 순감 약 1,300줄) + 문서 드리프트 일괄 수리
    - **광역 회귀 soft gate** — config.md `regression_command` 설정 시 `/pilot:pr` 진입 전 1회 실행, 레거시 원거리 파손을 PR 경계에서 포착
    - **리뷰 축 통합** — fix-review 스킬 폐지, 재진입 라우팅이 pilot-code-review REPORT 에 통합 (`trivial`·`new-feature`·`dismiss` 어휘 추가)
    - 테스트 CI 배선 + 링크·훅 테스트 신설 — protect-managed 의 `rm -rf` 우회 버그, regen 백업 경로 버그를 테스트가 발견·수정
    - critic 흐름 간소화 — 별도 스킵 동의 질의 없이 계획 확인 응답 1회로 통합 (스킵 주체는 사용자 유지)
    - 상세 변경사항: [Explanation → Release Note](explanation/index.md)

---

## 처음이라면

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } __Tutorial__

    ---

    설치부터 첫 plan 작성까지 — pilot의 한 cycle을 직접 실행하며 workflow 흐름을 익힙니다.

    [:octicons-arrow-right-24: Quick Start](tutorial/quick-start.md)

    [:octicons-arrow-right-24: Deep Walkthrough](tutorial/getting-started.md)

</div>

## 특정 작업이 필요할 때

<div class="grid cards" markdown>

-   :material-tools:{ .lg .middle } __How-to__

    ---

    TDD 활성화, critic 활용, 외부 domain bootstrap 등 *작업별 recipe*.

    [:octicons-arrow-right-24: How-to 목록](how-to/index.md)

-   :material-book-open-variant:{ .lg .middle } __Reference__

    ---

    agent, skill, CLI, configuration key 등의 *정확한 스펙*.

    [:octicons-arrow-right-24: Reference 목록](reference/index.md)

-   :material-lightbulb-on:{ .lg .middle } __Explanation__

    ---

    *동작 원리와 철학* — agent 역할 분리, drift-protocol, SSOT와 derived의 구분.

    [:octicons-arrow-right-24: Explanation 목록](explanation/index.md)

</div>

---

## 한 줄 요약

pilot은 대화의 맥락과 domain context를 유지할 수 있도록 `workspace/` 구조와 독립된 4개의 agent(`planner` / `planner-critic` / `generator` / `evaluator`)를 활용해 명시적인 호출 flow를 유지합니다. 완전히 자동화된 pipeline이 아닌, 각 phase 사이에 사용자가 개입할 수 있는 workflow입니다.

[GitHub](https://github.com/radiostart/claude-plugins){ .md-button } [CHANGELOG](https://github.com/radiostart/claude-plugins/releases){ .md-button }
