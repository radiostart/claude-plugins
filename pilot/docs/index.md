---
hide:
  - navigation
  - toc
---

# pilot

도메인 지식 기반의 agent workflow 플러그인입니다. Claude Code 내에서 *plan → critic → generate → evaluate*의 명시적 cycle로 project를 진행합니다.

!!! tip "v0.19.0 highlights"
    - **탐색 → 선별 → 주입 3단계** — `context-search.py "<키워드>" --scope D --format manifest --limit 8` 로 후보를 1줄씩 받고, 에이전트가 1~3개를 고른 뒤 `'select:{file}#{heading},…' --inject` 한 번으로 본문을 받습니다(렌더 총량 12,000B·섹션당 400줄 상한). wrapper-protocol §6 · `/pilot:ask` 배선
    - **한글 결합어 양방향** — `선발송 접수 [상태]` ↔ `선발송접수[상태]`, `진입파일` ↔ `진입 파일` 을 본문·description·헤딩에서 대조. 붙여 쓴 텍스트와 띄어 쓴 텍스트의 점수가 같습니다. 골든 질의 4 → 6, 점수·순서 스냅샷 fixture
    - **frontmatter** — `description`·`domain`·`type`·`sources` 파싱. `type`·`domain` 은 결과 필드로, `sources` glob(gitignore 의미)은 소스 경로 질의의 파일 보너스로만. mtime 신선도 점수는 결정성 때문에 채택하지 않았습니다
    - **경로 트리거 규칙 포인터 (#30 C1)** — `/pilot:learn` 이 `.claude/rules/pilot-{domain}.md` 를 생성하고 Claude Code 조건부 규칙이 매칭 소스를 읽을 때 진입·규칙·경계 문서 포인터(≤8줄·≤500자)를 주입합니다. Write·Edit 미발화 실측에 따라 `hooks/domain-pointer.sh` 가 세션·도메인당 1회 보완, `/pilot:doctor` 가 정합 검사, `hooks/rules-trace.sh` 로 로드 계측(opt-in)
    - 두 작업 모두 별도 에이전트 red-team 검토(12건·10건)를 거쳐 반영 — `docs/superpowers/plans/2026-09-08-*.md`

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
