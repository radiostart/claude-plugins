---
hide:
  - navigation
  - toc
---

# pilot

도메인 지식 기반의 agent workflow 플러그인입니다. Claude Code 내에서 *plan → critic → generate → evaluate*의 명시적 cycle로 project를 진행합니다.

!!! tip "v0.18.0 highlights"
    - **`context-search` 도구 신설** — `workspace/context` 지식 파일을 H2/H3 섹션 단위로 색인해 결정적 점수(헤딩 10 · 경로 8 · 인용 6 · 헤딩 부분 5 · description 4 · 본문 2)로 순위. 질의 3형식(`select:`·키워드·`+필수어`), json/md 출력, 라인 범위 `read_hint`, 표준 라이브러리만
    - **soft 배선** — orchestrate-load 가 도메인 진입 파일 로드 직후 `[검색]` 힌트 1줄, wrapper-protocol §6 부분 로드가 도구 호출 권장으로, Explore 서브에이전트 계약(scope 경로·thoroughness·결론만) 명시. 래퍼 필수 step 추가 0 · 지시 문서 순증 2줄
    - **confluence 로컬 검색 개선** — 같은 랭커로 점수순·상한 5건·첫 일치 스니펫, 랭커 로드 실패 시 기존 substring 폴백
    - 도메인 지식 검색·계층 탐색 로드맵 — #28 신선도 힌트 · #29 frontmatter 매니페스트 · #30 경로 트리거 (계획서 `docs/superpowers/plans/2026-09-04-context-retrieval-feature-plan.md`)

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
