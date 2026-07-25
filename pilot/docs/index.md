---
hide:
  - navigation
  - toc
---

# pilot

도메인 지식 기반의 agent workflow 플러그인입니다. Claude Code 내에서 *plan → critic → generate → evaluate*의 명시적 cycle로 project를 진행합니다.

!!! tip "v0.10.0 highlights"
    - **스킬 전면 재작성** — 슬래시 커맨드 17개를 원칙 중심으로 압축해 전부 100줄 이하로. 에이전트 5종은 기계 계약(REPORT 블록·Detect literal·표 헤더) 보존을 우선해 재작성. 지시 문서 4,808 → 3,635줄
    - **도구 슬림화** — `diagnose.py`·`memory-hint.py`·`init_detect.py` 3종을 모델 판단으로 이관해 삭제, `verify-report-lint.py` 파서는 `auto_pilot.py` 로 흡수. tools/ Python 7,138 → 4,997줄 (30.1% 감축)
    - **wrapper 도메인 컨텍스트 로드 버그 수정** — MANIFEST 파서가 문서 상단 blockquote 를 먼저 매칭해 도메인 문서가 로드되지 않던 문제. anchored 정규식 + 코드블록 strip 으로 해소
    - `doctor --schema` CI(`validate.yml`) 신설 · `how-to/doctor-migration.md` 를 현행 거동으로 전면 재작성
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
