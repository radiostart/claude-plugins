---
hide:
  - navigation
  - toc
---

# pilot

도메인 지식 기반의 agent workflow 플러그인입니다. Claude Code 내에서 *plan → critic → generate → evaluate*의 명시적 cycle로 project를 진행합니다.

!!! tip "v0.9.0 highlights"
    - **조건부 인터뷰 (Open Questions 소비)** — `/pilot:create-feature`(3-ter)·`/pilot:analyze`(7.5) 가 spec 의 미해결 Open Questions 를 우선순위((d) 비즈니스 결정 우선)로 사용자에게 조건부 질의하고 답변을 spec 에 반영. 질문이 없으면 발동하지 않는 soft gate — 기존 흐름 무중단
    - **경량 산출물 대조** — spec 심볼을 `scope/{domain}.md` 산출물과 lookup 대조해 부재 심볼을 (a) 질문으로 승격 (코드 탐색은 planner 몫으로 역할 분리 유지)
    - 소비 규칙 SSOT `context/shared/interview.md` 신설 — 작성 규칙(open-questions.md)과 짝, 해소된 (b) 행 재개봉 방지 판정 키 명문화
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
