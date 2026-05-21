# How-to

작업별 레시피. *어떻게* 특정 일을 처리하는지에 답합니다. (개념 설명이 필요하면 [Explanation](../explanation/index.md), 정확한 값이 필요하면 [Reference](../reference/index.md).)

!!! note "작성 중"
    아래 목록은 v0.4.0 매뉴얼 plan 의 §2 로 정의된 페이지들입니다. 본 사이트 step 1 단계에서는 골격만 두고 다음 단계에서 채웁니다.

## 개발 워크플로우

- TDD 모드 활성화 (`/pilot:tdd` — Red 계약 강제)
- Characterize 모드 — 레거시 코드 보강 시 사용
- **Critic 활용** — planner 의 plan 을 챌린지해 합의 표를 채우는 흐름 (v0.4.0 신규)
- Focus 로 방향 조정 — `.focus.md` 로 다음 subagent 호출에 의도 전달

## 컨텍스트 관리

- analyze — docs/ 기획서 → features/ 일괄 생성
- create-feature — docs 없이 프롬프트로 단건 추가
- cross-domain learn — 외부 도메인 부트스트랩

## 운영

- doctor migration — schema v1.1 → v1.2 등 마이그레이션
- Confluence 동기화
- Slack 알림

## 통합

- MOAI-ADK 와의 연동
