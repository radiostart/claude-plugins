# #08 project SKILL.md `{프로젝트명}` 치환 범위 명문화

> source: v0.2.1 hotfix discovery (NS #5 cycle, 2026-04-29) — hotfix 후보 #4

## 요구사항

- **조건**: NS #5 cycle 시뮬레이션에서 `pilot/skills/project/SKILL.md` 의 `{프로젝트명}` 토큰 치환 단계가 **치환 범위 모호**함을 발견. SKILL.md 는 "토큰만 실제 프로젝트명으로 치환" 이라 적었으나 본문 prose (가이드 주석) 에 같은 토큰이 자기 참조로 등장 (예: example template 의 가이드 주석에서 `{프로젝트명}` 라는 placeholder 설명) — 명시적 범위 룰이 없으면 LLM 이 prose 안 자기 참조까지 치환하는 회귀 가능성.
- **트리거**: `/pilot:project {프로젝트명}` 호출. example template 복사 직후 토큰 치환 단계.
- **기대결과**: 치환 범위가 본문에 명문화 — H1 헤더 (`# {프로젝트명}`) 만 치환, 본문 prose 의 가이드 주석에 등장하는 `{프로젝트명}` 자기 참조는 보존 (스캐폴딩 설명용).

## 비즈니스 규칙

- **치환 대상 = H1 헤더 1 곳만**:
  - `^#\s+\{프로젝트명\}\s*$` 정확 매칭. example template 의 `# {프로젝트명}` 라인 1 회.
  - `prompts/{planner,generator,evaluator}.md` 의 H1 헤더도 동일 (`# Generator — {프로젝트명}` 같은 형태).
- **치환 보존 대상 = 본문 prose**:
  - 가이드 주석 (`> {프로젝트명} 토큰만 실제 프로젝트명으로 치환` 같은 self-reference) — **보존**.
  - 마크다운 코드블록 (` ``` `) 안의 `{프로젝트명}` — **보존** (예시 코드).
  - 표 본문의 `{프로젝트명}` — 보존 (예시 행).
- **책임 위치**: SKILL.md 의 토큰 치환 단계 본문에 명시 1 단락 추가:
  ```markdown
  > **치환 범위**: H1 헤더 (`^# \{프로젝트명\}\s*$`) 만 치환. 본문 prose
  > (가이드 주석·코드블록·표 예시) 의 `{프로젝트명}` 자기 참조는 보존.
  > example template 의 스캐폴딩 설명이 깨지지 않도록 H1 헤더만 정확 매칭.
  ```
- **example template 의 자기 참조 표현 정리**:
  - 가이드 주석 안의 `{프로젝트명}` 토큰을 명시적으로 backtick 으로 감싸 (`` `{프로젝트명}` ``) self-reference 표시.
  - LLM 이 prose 안 backtick 토큰을 H1 토큰과 다르게 인식하도록 유도.
- **A2 runtime fallback 정합**: H1 헤더에 `{프로젝트명}` 토큰 부재 (사용자가 이미 H1 직접 작성 등) → 치환 skip + INFO 1 줄 (`{프로젝트명} 토큰 부재 — 치환 skip, 기존 H1 보존`). abort 안 함.

## 예외 케이스

- **사용자가 example template 직접 수정해 H1 토큰 제거**: H1 토큰 부재 → 치환 skip. 기존 H1 보존.
- **사용자 프로젝트명에 특수문자 (`{`·`}`·정규식 메타) 포함**: sanitize 룰 — `[a-zA-Z0-9가-힣\-_]` 외 차단. 위반 시 사용자 질의 prompt.
- **H1 헤더가 코드블록 안에 위치**: 일반적이지 않은 케이스. 펜스 추적 후 코드블록 안 H1 무시 — features/04 의 코드블록 펜스 추적 v1.1 보강과 정합. 본 v0.3.0 은 H1 헤더 = 파일 시작부 1 줄 가정 (코드블록 안 H1 사례 v0.3.0 범위 외).
- **prompts/ 의 H1 패턴이 다른 형식** (예: `# Planner: {프로젝트명}` 콜론 사용): 정확 매칭 정규식이 콜론 등 구분자 허용. SKILL.md 본문 패턴 = `^#\s+(?:[^\n]+?\s+)?\{프로젝트명\}\s*$`. 단 본 v0.3.0 은 단순화 — `^#\s+\{프로젝트명\}\s*$` (정확 매칭) 또는 `^#.*\{프로젝트명\}.*$` (단일 라인 H1 안 토큰) 둘 중 단순화 채택.

## 관련 파일 범위

- **변경**: `pilot/skills/project/SKILL.md`
  - 토큰 치환 단계 본문 (line 추정 70~100 범위) 에 치환 범위 명시 1 단락 추가.
- **변경**: `pilot/skills/context/lifecycle/projects/example/project.md`
  - 가이드 주석 안의 `{프로젝트명}` 자기 참조 표현을 backtick 으로 감싸 명시 (`` `{프로젝트명}` ``).
- **변경 (선택)**: `pilot/skills/context/lifecycle/projects/example/prompts/{planner,generator,evaluator}.md`
  - 동일 self-reference 정리 (backtick wrap).
- **단위 테스트**: 본 v0.3.0 은 SKILL.md 본문 보강만 — 단위 테스트 신설 없음. 회귀 픽스처 (`project/expected/projects/python-sample-demo/`) 의 H1 = `# python-sample-demo` 가 정확 산출되는지로 검증.
- **사용자 영향**: 0 ~ 미미. v0.2.x cycle 에서도 LLM 이 사실상 H1 만 치환하고 있었음 (NS #5 cycle 검증 결과). 본 변경은 그 거동의 명문화 + example template 의 self-reference 표현 정리.
