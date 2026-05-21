# Explanation

*왜* pilot 이 이런 모양인지 — 철학·아키텍처·트레이드오프. 무엇을 *해야 하는지* (How-to) 또는 정확한 값 (Reference) 이 아니라, *어떤 사고 모델로 설계됐는지*.

## 시작점

<div class="grid cards" markdown>

-   :material-lightbulb-on:{ .lg .middle } __[핵심 개념](concepts.md)__

    ---

    pilot 이 해결하는 문제 — "메인 대화의 의도가 subagent 에게 안 전달되는" 단절 · 도메인 지식을 코드가 아니라 SSOT 메타구조에 두는 이유.

</div>

## 에이전트 시스템

<div class="grid cards" markdown>

-   :material-account-group:{ .lg .middle } __[에이전트 흐름](agent-flow.md)__

    ---

    planner → critic → generator → evaluator 의 명시 호출 사이클. 페르소나 (`architect`·`red-team`·`craftsman`·`auditor`) 의 책임 분리와 critic 의 1.5-pass 위치.

-   :material-folder-multiple:{ .lg .middle } __[Workspace 레이아웃](workspace-layout.md)__

    ---

    `STATE.md` · `context/` · `projects/{P}/` 의 역할 분리. 왜 *한 워크스페이스에 활성 프로젝트 1 개* 가 강제되는지.

</div>

## 모드·운영

<div class="grid cards" markdown>

-   :material-toggle-switch:{ .lg .middle } __[모드 — Standard / TDD / Characterize](modes.md)__

    ---

    `.agent-state.yml` 의 `tdd`·`mode` 값에 따른 진입 분기. 각 모드의 plan-schema 차이.

-   :material-magnify-scan:{ .lg .middle } __[Drift Protocol](drift-protocol.md)__

    ---

    `workspace/` 의 도메인 지식이 실제 코드와 어긋났을 때 누가 (planner / generator / evaluator) 어떻게 복구하는지.

</div>

## SSOT · 릴리스

<div class="grid cards" markdown>

-   :material-source-branch:{ .lg .middle } __[SSOT 와 derived](ssot-and-derivation.md)__

    ---

    `skills/`·`agents/`·`tools/`·`identity.yml` 이 SSOT, README 와 본 사이트는 derived. drift 감지 메커니즘.

-   :material-tag-arrow-up:{ .lg .middle } __[릴리스 · 업그레이드](release-and-upgrade.md)__

    ---

    schema 마이그레이션 정책 · wrapper 계약 호환성 · `plugin_version` 비교의 의미.

</div>
