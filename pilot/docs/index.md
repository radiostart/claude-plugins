---
hide:
  - navigation
  - toc
---

# pilot

도메인 지식 기반의 agent workflow 플러그인입니다. Claude Code 내에서 *plan → critic → generate → evaluate*의 명시적 cycle로 project를 진행합니다.

!!! tip "v0.13.0 highlights"
    - **issue 단건 사이클** — `/pilot:issue` 가 경량 모드에서 사이클 지원으로 재정의. orchestrate-load 가 STATE.md 의 `| issue | {이슈명} |` 행을 인식해 (`work_mode` 계약) planner→critic→generator→evaluator 를 `issues/{이슈명}/` 기반으로 구동 — 이슈명을 프로젝트로 오인하던 오도성 에러·doctor 오진 제거
    - **이슈 폴더 slug 자동 명명** — 폴더명(영문 kebab slug ≤40자)과 표시명(issue.md H1 한글 요약) 분리, 팀 용어는 도메인 문서의 코드 표기 우선. 유사 이슈 검색은 폴더명 `ls` + H1 `grep` 병행
    - **issues/ 훅 보호 확장** — 기존 이슈 파일 Write·destructive 차단 (Edit·신규 파생 산출물·`.focus.*` 통과), issues/ 상위 폴더 차단
    - **focus·commit issue 모드 지원** — focus 는 `issues/{이슈명}/.focus.md` 로 분기, commit 은 P1 issue 판정 예외로 계속 동작. 나머지 project 전용 스킬은 issue 행에서 명확히 종료
    - 가이드: [운영 이슈 단건 처리](how-to/issue-cycle.md)

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
