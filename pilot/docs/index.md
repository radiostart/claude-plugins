---
hide:
  - navigation
  - toc
---

# pilot

도메인 지식 기반 에이전트 워크플로우 플러그인 — Claude Code 안에서 *plan → critic → generate → evaluate* 의 명시적 사이클로 복잡한 프로젝트를 진행합니다.

!!! tip "v0.5.0 highlights"
    - `@pilot-planner-critic` 추가 — planner 의 plan 을 반론 시각으로 챌린지하는 adversarial 1.5-pass 리뷰
    - doctor 마이그레이션·진단 강화 (schema v1.1 → v1.2 자동 업그레이드)
    - init wizard contract 보강
    - 자세한 변경사항: [Explanation → 릴리스](explanation/index.md)

---

## 처음이라면

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } __Tutorial__

    ---

    설치부터 첫 plan 까지 — pilot 의 한 사이클을 직접 돌려보면서 워크플로우의 모양을 익힙니다.

    [:octicons-arrow-right-24: Quick Start](tutorial/quick-start.md)

    [:octicons-arrow-right-24: Deep Walkthrough](tutorial/index.md)

</div>

## 특정 작업이 필요할 때

<div class="grid cards" markdown>

-   :material-tools:{ .lg .middle } __How-to__

    ---

    TDD 활성화, critic 활용, 외부 도메인 부트스트랩 등 *작업별 레시피*.

    [:octicons-arrow-right-24: How-to 목록](how-to/index.md)

-   :material-book-open-variant:{ .lg .middle } __Reference__

    ---

    에이전트·스킬·CLI·설정 키의 *정확한 값*.

    [:octicons-arrow-right-24: Reference 목록](reference/index.md)

-   :material-lightbulb-on:{ .lg .middle } __Explanation__

    ---

    *왜 이렇게 동작하는지* — 에이전트 역할 분리, drift-protocol, SSOT 와 derived 의 경계.

    [:octicons-arrow-right-24: Explanation 목록](explanation/index.md)

</div>

---

## 한 줄로

pilot 은 메인 대화의 의도와 도메인 컨텍스트를 잃지 않도록 `workspace/` 메타구조와 4 개의 분리된 에이전트(`planner` / `planner-critic` / `generator` / `evaluator`)를 통해 *명시적 명시 호출* 흐름을 강제합니다. 자동 파이프라인이 아니라 *phase 사이 사용자 개입 가능* 한 워크플로우입니다.

[GitHub](https://github.com/radiostart/claude-plugins){ .md-button } [CHANGELOG](https://github.com/radiostart/claude-plugins/releases){ .md-button }
