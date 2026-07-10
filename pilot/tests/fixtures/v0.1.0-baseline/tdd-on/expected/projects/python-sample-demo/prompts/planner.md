# Planner — python-sample-demo

구현 대상 기능을 분석하고, Generator가 실행 가능한 단계별 계획을 수립한다.

> **⚠️ 이 파일은 `@pilot-planner` subagent 정의가 아닙니다.** 실제 subagent 는 플러그인의 [`${CLAUDE_PLUGIN_ROOT}/agents/pilot-planner.md`](${CLAUDE_PLUGIN_ROOT}/agents/pilot-planner.md) 에 등록돼 있고, wrapper 가 Read 로 **이 파일을 컨텍스트 문서로** 불러들입니다. 이 파일 편집은 다음 `@pilot-planner` 호출에 반영됩니다 (단 `<!-- [analyze-managed] -->` 섹션은 다음 `--regen-agents` 시 덮어쓰임).
>
> 스캐폴딩·analyze-managed·TDD 상세: [prompts-scaffold-notes.md](${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/projects/prompts-scaffold-notes.md) 참조.

<!-- [analyze-managed] -->
## 기능별 사전 확인 사항

_(analyze 실행 전 — 이 줄은 analyze 실행 시 feature 별 소항목으로 교체된다.)_

---

<!-- pilot-tdd-original-planner:start -->
<!-- pilot-tdd-original-planner:end -->

## TDD — Red 계약

이 프로젝트는 TDD 모드다. Planner 는 Red 계약만 남긴다 — **테스트 코드는 작성하지 않는다**. 스텝별 3 축 (테스트 경로 · 검증할 행동 · 기대 실패 유형) 을 `.plan.md` 에 기록한다. 상세: [`rgr.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/modes/rgr.md) 의 `Planner — Red Contract` 절 (래퍼가 자동 로드).
