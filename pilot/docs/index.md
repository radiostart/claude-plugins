---
hide:
  - navigation
  - toc
---

# pilot

도메인 지식 기반의 agent workflow 플러그인입니다. Claude Code 내에서 *plan → critic → generate → evaluate*의 명시적 cycle로 project를 진행합니다.

!!! tip "v0.10.1 highlights"
    - **doctor 오탐 2건 수정** — config 값 셀의 예시 표기(`예: \`context/conventions.md\``)를 선언으로 오인하던 건, features 카운트가 `.plan.md`·`.plan.critic.md` 파생 산출물을 spec 으로 세던 건. 실측 `4 WARN` → `1 WARN` (남은 1건은 `plugin_version` 정상 감지)
    - **판정을 구조 기반으로** — 값 셀은 "코드 스팬 단독 또는 공백 없는 평문" 일 때만 선언으로 인정하고, 그 외는 미선언 + INFO 로 강등. 한국어 `예:` 같은 문자열 규약에 의존하지 않는다
    - **파생 산출물 판정 SSOT 1곳** — `is_feature_spec_file()` 이 "stem 에 `.` 이 있으면 파생" 규칙을 단독 보유. 새 접미사가 늘어도 파서 수정이 필요 없다
    - v0.10.0 의 정비 3부작(#18 prune · #19 rewrite · #20 slim)이 dogfooding 게이트 통과로 전부 마감
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
