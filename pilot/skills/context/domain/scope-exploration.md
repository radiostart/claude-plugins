# 스코프 기반 탐색 규칙

planner / generator / evaluator 래퍼가 코드베이스를 탐색할 때 따르는 공통 규칙. 전체 codebase 무차별 스캔을 금지하고 scope 내 탐색을 강제하여 컨텍스트 폭발·오판을 방지한다.

---

## 공통 원칙

1. 파일 탐색·참조는 **1단계에서 로드한 scope 내용** (각 에이전트의 `agents/*.md` 선별본 또는 scope 원본 fallback) 의 **경로 범위 내에서만** 수행한다 (Read / Grep / Glob).
2. 내장 `Explore` 서브에이전트를 호출할 때는 **반드시** prompt 에 scope 파일의 대상 경로 목록을 명시한다. scope 없이 전체 codebase 스캔 금지.
3. 범위 밖 무차별 탐색은 이유를 불문하고 금지.

---

## Fallback — scope 미정 / 매칭 실패 시

scope 에 명시된 경로에서 대상을 찾지 못하면 전체 스캔 대신 **구체 패턴 기반 확장** 을 시도한다:

- feature·이슈 키워드를 근거로 **구체 패턴** 을 구성한다.
  - 예 (Rails): `app/models/*{keyword}*.rb`, `app/services/*{keyword}*.rb`, `app/controllers/**/*{keyword}*.rb`
- 패턴으로도 찾지 못하면 사용자에게 **범위 확장 허가** 를 요청한다.
- 여전히 무차별 `**/*.{ext}` 류 전체 스캔은 금지.

---

## 에이전트별 적용 범위

| 에이전트 | 주 탐색 목적 | 전형적 scope |
| --- | --- | --- |
| Planner | 영향 범위 파악·기존 코드 탐색 (계획 수립) | 도메인 전체 (models / services / controllers) |
| Generator | 구현 대상 파일·의존성 확인 | 구현 중인 feature 관련 경로 중심 |
| Evaluator | 검토 대상 파일·규칙 위반 검출 | 이번 변경 대상 + 직접 의존 경로 |

적용 원칙은 동일. 차이는 scope 가 어느 각도로 선별되느냐일 뿐.
