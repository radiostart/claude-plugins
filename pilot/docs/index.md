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

!!! tip "v0.15.0 highlights"
    - 프로젝트 모드 evaluator REPORT 영속화 — `features/NN-{slug}.eval.md` 저장 + protect-managed 훅 재생성 예외
    - critic·autopilot·focus 갱신 절차를 훅과 양립하게 개정 — 기존 파일 갱신은 Edit 기반
    - Slack 활성화 기본 이벤트에 `pr` 포함 — `complete,approval,pr` 로 통일
    - 스킬 description 7종 감량 — 상시 시스템 프롬프트 비용 3,777B → 2,208B

!!! tip "v0.14.0 highlights"
    - **issue 단건 사이클 + 폴더 slug** — `/pilot:issue` 가 경량 모드에서 사이클 지원으로 재정의. orchestrate-load 가 STATE.md 의 `| issue | {이슈명} |` 행을 인식해 (`work_mode` 계약) planner→critic→generator→evaluator 를 `issues/{이슈명}/` 기반으로 구동한다. 폴더명(영문 kebab slug ≤40자)과 표시명(issue.md H1)을 분리해 유사 이슈 검색을 폴더명 `ls` + H1 `grep` 병행으로 수행 → [운영 이슈 단건 처리](how-to/issue-cycle.md)
    - **Open Questions fail-closed 게이트** — 미해결 `- [ ]` 항목에 plan 처리 마커(`추정 구현`/`범위 제외`)가 없으면 `plan-validate` 가 차단. evaluator REPORT 에 `open_questions` gate 추가 (7 gates)
    - **도메인 지식 환류 (knowledge-sync)** — evaluator 가 사이클 종료 시 이번 변경이 도메인 문서에 남길 지식을 감지해 `metrics.domain_impact` 로 보고. 기록 여부는 사용자 승인 후 메인 대화가 결정
    - **`/pilot:init`·`/pilot:review` → `/pilot:pilot-init`·`/pilot:pilot-review`** — Claude Code 내장 `/init`·`/review` 와의 bare 별칭 충돌 해소
    - **issue 모드 경계 집행** — issues/ 훅 보호(기존 파일 Write·destructive 차단, Edit·신규 산출물 통과), focus 는 `issues/{이슈명}/.focus.md` 로 분기, commit 은 계속 동작하고 나머지 project 전용 스킬은 issue 행에서 종료
    - **하니스 정합·규율 보강** — 진행 보드 겸용 선로딩, 계획 단계 effort 상향, plan 분량 가드(WARN), 주석 규율 eval, 훅 결함 4건 수정, SessionStart 컨텍스트 훅

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
