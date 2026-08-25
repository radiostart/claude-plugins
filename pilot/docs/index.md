---
hide:
  - navigation
  - toc
---

# pilot

도메인 지식 기반의 agent workflow 플러그인입니다. Claude Code 내에서 *plan → critic → generate → evaluate*의 명시적 cycle로 project를 진행합니다.

!!! tip "v0.17.0 highlights"
    - **autopilot 신호 파서 fail-open 봉쇄** — 템플릿 에코 `READY | NOT_READY`·status 중복 키·장식 REPORT 헤더·critic 부분 파싱·통과 문구 서브스트링 오탐 등 9경로가 통과 대신 정지(fail-closed)로 전환. 적대적 검토(독립 에이전트 red-team) 기반, 테스트 +23종
    - **plan 판정 기계 소유** — `auto_pilot.py` 가 plan-validate 를 직접 실행하고 mode 를 `.agent-state.yml` 에서 직접 도출 (`--plan-file`·`--state-file` 신설, `--plan-valid` 폐지). 모델이 옮기는 것은 경로뿐
    - **reflect 후 plan 재검증 의무화** — critic 반영으로 수정된 plan 도 plan-validate 를 다시 통과해야 generator 진행
    - **정지 사유 정밀화** — 검증 실행 불능(경로·state 결함·plan-validate 크래시)은 `plan-validate` 가 아닌 `agent-error` 로 정지해 처방표 오도 방지

    [:octicons-arrow-right-24: 전체 버전 이력](release-notes.md)

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

[GitHub](https://github.com/radiostart/claude-plugins){ .md-button } [릴리스 노트](release-notes.md){ .md-button }
