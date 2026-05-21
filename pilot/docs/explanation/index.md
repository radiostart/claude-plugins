# Explanation

*왜* pilot 이 이런 모양인지 — 철학·아키텍처·트레이드오프.

!!! note "작성 중"
    아래 항목은 매뉴얼 plan 의 §2 로 정의된 explanation 페이지들입니다. 본 사이트 step 1 에서는 골격만, Mermaid 다이어그램 4 개와 본문은 §9 step 5 에서 채웁니다.

## 핵심 개념

- pilot 이 해결하는 문제 — "메인 대화의 의도가 subagent 에게 안 전달되는" 단절
- workspace/ 메타구조 — 왜 SSOT 가 코드가 아니라 도메인 지식인지

## 에이전트 시스템

- **planner → critic → generator → evaluator** 흐름과 페르소나 분리 (`identity.yml` 의 archetype: architect / red-team / craftsman / auditor)
- planner-critic 의 책임 경계 — *plan/코드 직접 수정 안 함*, 별도 `.plan.critic.md` 작성
- pilot-code-review 와의 차이 — critic 은 *작성된 계획*, code-review 는 *작성된 코드* (git diff)

## 모드

- Standard / TDD / Characterize 진입 분기와 각각의 plan schema 차이

## 운영

- **drift-protocol** — `workspace/` 가 실제 코드와 어긋났을 때 누가 어떻게 수정하는지
- **SSOT 와 derived** — README, 매뉴얼 사이트, prompts/ 등이 어떻게 한 SSOT 에서 파생되는지
- **릴리스·업그레이드** — schema 마이그레이션 정책과 wrapper 계약 호환성
