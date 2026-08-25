---
hide:
  - navigation
  - toc
---

# pilot

도메인 지식 기반의 agent workflow 플러그인입니다. Claude Code 내에서 *plan → critic → generate → evaluate*의 명시적 cycle로 project를 진행합니다.

!!! tip "v0.16.0 highlights"
    - **신규 스킬 3종** — `/pilot:qa` (Jira 결함 처리 phase — qa/ 사이클·features 읽기 전용 잠금·회귀영향 게이트) · `/pilot:switch` (최근 작업 목록 조회·전환 — 미완 이슈 재발견) · `/pilot:ask` (도메인 컨텍스트 → 소스 순 읽기 전용 구현 질의)
    - **learn 기재 규격 신설** — 기재 층위 L1/L2/L3 (구현 세부는 소스에 맡김) · Routes 표 선별 기재 + 고지 3줄 · 멀티 DB 귀속 전수 대조 · 부재 주장 반증 의무 · 심볼 앵커 우선 인용 → `learn/references/extraction.md`
    - **doctor 인용 drift 검사** — context 문서의 소스 인용 mtime 대조로 stale 산출물 감지 (learn 재실행 처방)
    - **scope-guard 경로 판정·gitignore 규약** — 심링크·비정규 표기에서의 무음 해제 차단, 루트 앵커 vs `**/` 임의 깊이 구분, substring 오차단 해소 (테스트 24종)
    - **대상 plan 확정 SSOT (`plan-target.md`)** — wrapper 3종의 후보 조사·집계 규칙 단일화 (READY eval 필터·셸 글롭 금지), autopilot 은 wrapper 호출 프롬프트에 대상 명시 의무
    - **Slack 이슈 오전송 차단** — 활성 행이 issue 면 동명 프로젝트 채널로 새지 않음. description 예산·preamble 커버리지 기계 게이트 신설

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
