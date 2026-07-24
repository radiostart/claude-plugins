# #17 조건부 인터뷰 (Open Questions 소비)

> source: prompt
> created: 2026-07-24T05:44:05Z
> user_prompt: "조건부 인터뷰 — Open Questions 소비 단계: create-feature/analyze 가 spec 생성 후 unchecked Open Questions 항목이 있으면 우선순위(d>b>c>a)로 사용자에게 조건부 질의하고 답변을 spec 에 반영, spec 심볼을 scope 산출물과 경량 대조해 부재 심볼을 (a) 질문으로 추가"

## 요구사항

- **조건**: feature spec 의 `## Open Questions` 에 unchecked `- [ ]` 항목이 1 개 이상 존재할 때만 발동. `- (없음)` placeholder 뿐이면 무발동 — 현행과 동일하게 무중단 진행 (soft gate, 인터뷰는 게이트가 아님).
- **트리거**: (1) `/pilot:create-feature` — 3-bis (cross-domain detect) 직후 신설 3-ter 단계. (2) `/pilot:analyze` — 7 단계 (자가 검증) 와 8 단계 (결과 출력) 사이 신설 7.5 단계, 신규 생성된 전체 features 의 unchecked 항목을 모아 일괄 질의.
- **기대결과**: 답변은 spec 의 해당 섹션 (요구사항 / 비즈니스 규칙 / 예외 케이스) 에 반영되고 해당 Open Questions 항목은 `- [x] {질문} → {답변 요약}` 으로 체크된다. 미답변 (스킵) 항목은 unchecked 로 유지된다. 결과 요약에 `인터뷰: 해소 N건 / 이월 M건` 라인이 추가된다.

## 상태 전환

_(상태값 변화 없음 — .agent-state.yml 스키마 변경 없음)_

## 비즈니스 규칙

- 질의 우선순위: (d) 비즈니스 결정 > (b) cross-domain 산출물 부재 > (c) 외부 시스템 spec 부재 > (a) 같은 도메인 추가 read.
- 질의 상한: 단건 (create-feature) 최대 4 문항, 일괄 (analyze) 최대 8 문항. 초과분은 질의하지 않고 결과 출력에 `미질의 N건` 리포트.
- 모든 질문에 "나중에 결정" 선택지를 항상 제공한다. 스킵 시 항목이 unchecked 로 남아 현행과 동일하게 동작 (무열화 degrade).
- **산출물 대조 (경량 갭 체크)**: spec 에 기재된 핵심 심볼 (상태값·메서드·필드) 을 `workspace/context/scope/{domain}.md` 산출물에서 lookup 하고, 부재 심볼은 `### (a)` 에 질문 행으로 추가한 뒤 인터뷰 대상에 포함한다. 코드베이스 전체 탐색 (Grep/Read) 은 하지 않는다 — 심층 영향 분석은 @pilot-planner 책임 (역할 중복 금지).
- 인터뷰 규칙의 SSOT 는 신설 `pilot/skills/context/shared/interview.md` — create-feature·analyze 양쪽이 참조 (open-questions.md 와 동일 위상).
- 에이전트 (planner / planner-critic / generator / evaluator) 와 autopilot 은 변경하지 않는다. 답변 전달은 spec 파일 경유 (서브에이전트는 사용자 질의 불가).

## 예외 케이스

- `scope/{domain}.md` 부재 또는 빈 파일 → 산출물 대조 스킵 (A2 runtime fallback, abort 금지), 인터뷰는 기존 unchecked 항목만으로 진행.
- 사용자가 모든 질문을 스킵 → spec 변경 없음, 결과 요약에 `인터뷰: 해소 0건 / 이월 M건` 만 출력.
- unchecked 항목이 상한 초과 → 우선순위순으로 상한까지만 질의, 초과분은 `미질의 N건` 으로 보고.
- analyze `--regen-agents` 모드 → 인터뷰 미발동 (features 신규 생성이 없는 모드).

## Open Questions

### (a) 같은 도메인 추가 read 필요
- [x] create-feature 3-bis·analyze 5-2 의 기존 detect 출력 형식과 3-ter 인터뷰 입력의 결합 지점 — `open-questions.md` 의 행 형식 (`- [ ] {질문}: ...`) 을 그대로 파싱 소스로 쓸 수 있는지 planner 가 SKILL.md 원문 대조 필요 → 대조 완료 (plan 참조): 행 본문 형식 3종 혼재 (colon형 :11 / 화살표형 (b) :51 / 자유형 (c) :53) 이므로 unchecked 판정은 `- [ ] ` prefix 만 기준으로 사용 가능. SKILL.md 양쪽은 행 형식을 자체 정의하지 않고 open-questions.md 에 위임 — fork 없음. 체크 형식은 원문 보존 + ` → {답변 요약}` 1회 append (마지막 `→` 뒤 = 답변 요약) 로 interview.md 에 명문화

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- (없음)

### (d) 비즈니스 결정 영역
- (없음) — 마찰 허용치 (조건부만) · 갭 체크 위치 (spec 단계) · 적용 범위 (양쪽 + analyze 일괄) · 상한 (4/8) 모두 2026-07-24 사용자 인터뷰로 확정됨
