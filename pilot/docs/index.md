---
hide:
  - navigation
  - toc
---

# pilot

도메인 지식 기반의 agent workflow 플러그인입니다. Claude Code 내에서 *plan → critic → generate → evaluate*의 명시적 cycle로 project를 진행합니다.

!!! tip "v0.11.0 highlights"
    - **doctor 스킬 → `pilot-doctor` 리네임** — 플러그인 스킬의 bare `/doctor` 별칭이 Claude Code 내장 `/doctor` 를 가리는 충돌 해소. 호출은 `/pilot:pilot-doctor` (도구 `tools/doctor.py` 는 무변경)
    - **Claude 5 하니스 정합** — preamble P-1 을 "진행 보드 선로딩" 으로 개편 (`TodoWrite`/`TaskCreate`·`TaskUpdate` 겸용 select), autopilot 에 wrapper 동기 호출·명시 호출 한정·게이트 이력 1줄 앵커 명시, guardrails 에 "사용자 게이트 생략 금지" 신설
    - **에이전트 모델·effort 조정** — planner·planner-critic `effort: xhigh`, generator `sonnet → opus` (재생성 루프 1회 비용 > 단가 차이)
    - **SessionStart 도메인 컨텍스트 포인터 훅** — 스킬 없이 메인 세션이 직접 도메인 코드를 만질 때도 MANIFEST·STATE 로딩 규칙을 안내
    - **훅 결함 수정 이식** — scope-guard 디렉토리 패턴 세그먼트 경계 매칭(`log/` 가 `dialog/` 오차단), commit-format 명령 앵커링·첫 `-m` 추출·HEREDOC 검증·UTF-8 길이, protect-managed `./` 접두 정규화·projects/ 상위 차단·focus 수명주기 예외, coding-rules 세션당 1회 발화·source_root 한정
    - **규율·가드 이식** — coding.md 주석 규율(표기 형태 불문) + evals `comment-discipline`, learn 프로젝트 식별자 배제, plan 분량 가드(30k자/1.5k라인 WARN)
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
