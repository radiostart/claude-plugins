# Explanation

pilot의 구조 설계 배경과 철학, 아키텍처, 트레이드오프를 설명합니다. 구체적인 작업 방법(How-to)이나 명세(Reference)보다는 설계에 반영된 멘탈 모델(Mental Model)을 다룹니다.

## 시작점

<div class="grid cards" markdown>

-   :material-lightbulb-on:{ .lg .middle } __[핵심 개념](concepts.md)__

    ---

    pilot이 해결하고자 하는 문제 — 메인 대화의 의도가 subagent에게 온전히 전달되지 않는 단절 현상을 해결하고, 도메인 지식을 코드가 아닌 SSOT 메타 구조로 관리해야 하는 이유를 다룹니다.

</div>

## 에이전트 시스템

<div class="grid cards" markdown>

-   :material-account-group:{ .lg .middle } __[에이전트 흐름](agent-flow.md)__

    ---

    planner → critic → generator → evaluator로 이어지는 명시적 호출 cycle을 설명합니다. 4개 agent의 역할 및 관점 분리, 그리고 critic의 1.5-pass 구조를 다룹니다.

-   :material-folder-multiple:{ .lg .middle } __[Workspace 레이아웃](workspace-layout.md)__

    ---

    `STATE.md`, `context/`, `projects/{P}/` 디렉토리 구조의 역할 분리를 설명합니다. 왜 하나의 workspace 내에서 단 하나의 active project만 실행되도록 강제되는지 설명합니다.

</div>

## 모드·운영

<div class="grid cards" markdown>

-   :material-toggle-switch:{ .lg .middle } __[모드 — Standard / TDD / Characterize](modes.md)__

    ---

    `.agent-state.yml` 설정의 `tdd`, `mode` 값에 따른 진입 분기와 각 mode별 plan-schema의 차이를 비교합니다.

-   :material-magnify-scan:{ .lg .middle } __[Drift Protocol](drift-protocol.md)__

    ---

    `workspace/` 내 도메인 지식과 실제 구현 코드가 어긋났을 때, 각 agent(planner / generator / evaluator)가 이를 어떻게 감지하고 동기화(drift protocol)하는지 설명합니다.

</div>

## SSOT · 릴리스

<div class="grid cards" markdown>

-   :material-source-branch:{ .lg .middle } __[SSOT 와 derived](ssot-and-derivation.md)__

    ---

    `skills/`, `agents/`, `tools/`, `identity.yml`을 SSOT로 정의하고, README 및 이 문서 사이트가 어떻게 파생(derived)되는지와 drift 감지 메커니즘을 다룹니다.

-   :material-tag-arrow-up:{ .lg .middle } __[릴리스 · 업그레이드](release-and-upgrade.md)__

    ---

    schema migration 정책, wrapper contract 호환성, `plugin_version` 비교의 의미를 다룹니다.

</div>
