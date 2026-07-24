# #17 조건부 인터뷰 (Open Questions 소비) — Implementation Plan

> source: features/17-conditional-interview.md · 2026-07-24 사용자 인터뷰 확정 설계
> mode: standard (tdd: false)
> planner_at: 2026-07-24

## 사전 확정 사항 (2026-07-24 사용자 인터뷰 — spec 기재 완료)

| 항목 | 결정 |
| --- | --- |
| 발동 조건 | unchecked `- [ ]` 항목 ≥ 1 일 때만 soft-gate 발동. `- (없음)` 뿐이면 현행과 완전 동일 무중단. 인터뷰는 게이트 아님. |
| 통합 지점 | create-feature 3-bis 직후 신설 **3-ter** / analyze 7↔8 사이 신설 **7.5** (신규 features 일괄 질의). `--regen-agents` 미발동. |
| 우선순위·상한 | (d) > (b) > (c) > (a). 단건 4 문항 · 일괄 8 문항. 초과분 `미질의 N건` 리포트. |
| 스킵 경로 | 모든 질문에 "나중에 결정" 항상 제공. 스킵 시 unchecked 유지 (무열화 degrade). |
| 산출물 대조 | spec 심볼 ↔ `scope/{domain}.md` lookup 만. **코드베이스 Grep/Read 금지** (planner 영향 분석과 역할 분리). scope 부재 시 A2 fallback 스킵. |
| SSOT 위치 | 신설 `pilot/skills/context/shared/interview.md` — open-questions.md (작성 규칙) 와 짝 (소비 규칙). |
| 무변경 범위 | 에이전트 4종 · autopilot · Python 도구 · 테스트 · 회귀 픽스처. markdown-only 변경. |

## spec Open Question (a) 해소 — 행 형식 대조 결과

spec 의 unchecked 항목 "open-questions.md 의 행 형식을 그대로 파싱 소스로 쓸 수 있는지 SKILL.md 원문 대조 필요" 에 대한 판정:

- `open-questions.md:11` — 일반 행: `- [ ] {질문}: ...` (colon형)
- `open-questions.md:51` — (b) 자동 행: `` - [ ] {외부 도메인} 산출물 부재 → `/pilot:learn {추천 경로}` 권장 `` (colon 없음, `→` 포함)
- `open-questions.md:53` — (c) 자동 행: `- [ ] {외부 시스템} spec 별도 확보 필요` (colon 없음)
- `create-feature/SKILL.md:96·104` · `analyze/SKILL.md:169` — 행 형식 자체 정의 없음, open-questions.md 위임 (자체 형식 fork 없음)

**결론: 사용 가능 — 단 unchecked 판정은 `- [ ] ` prefix 만 기준** (본문 형식 3종 혼재라 `: ` 구분자 의존 금지). 체크 형식은 `- [x] {원문 그대로} → {답변 요약}` — 원문 보존 + ` → {답변 요약}` 1회 append. (b) 행처럼 원문에 `→` 가 이미 있어도 **마지막 `→` 뒤 = 답변 요약** 규약으로 충돌 없음. 이 규칙을 interview.md 에 명문화한다 (step 1).

doctor 영향 없음 확인: `check_features_open_questions` (`pilot/tools/doctor/integrity.py:1317-1372`) 는 `## Open Questions` H2 + 4 카테고리 H3 존재만 검증 — `- [x]` 행·행 형식 무관.

## critic 반영 (C1~C6 — `.plan.critic.md` 합의 표와 동기)

| C# | 처리 | 본 plan 반영 위치 |
| --- | --- | --- |
| C1 (blocking) | accepted | `scope-sync.md` 변경 파일 추가 + 5-2 규칙 2 중복 판정 기준 명문화 (아래 "중복 판정 기준" 절 + step 4) + interview.md 2항 상호 링크 |
| C2 (suggestion) | accepted | interview.md 3항 — `{domain}` 은 `.agent-state.yml.domain` 만 사용, null 이면 대조 스킵 (A2) |
| C3 (suggestion) | accepted | interview.md 3항 — 대조 대상 = spec 본문 명시 심볼만 + (a) 행 추가 수 상한 (질의 상한과 동일 4/8) |
| C4 (nit) | accepted | interview.md 4항 — "(단건) 파일 내 등장 순" 추가 |
| C5 (nit) | accepted | interview.md 6항 — M·K 산술 규약 (N+M+K = 발동 대상 총수) |
| C6 (nit) | accepted | step 6 — 캡처 안내 문장에 "2건 질의 후 모두 '나중에 결정'" 시나리오 명시 |

### C1 해결 — (b) 행 중복 판정 기준 (scope-sync.md 5-2 규칙 2 보강)

충돌 시나리오: create-feature 3-ter 가 (b) 행을 해소 (`- [x] {원문} → {답변}`) 한 직후 step 4 가 analyze 5-2 를 수행 → 외부 도메인이 여전히 미학습이면 재detect 되는데, 현행 `scope-sync.md:120` 의 "(중복 행은 skip)" 은 판정 기준이 없어 원문이 달라진 체크 행을 중복으로 못 보고 unchecked 행을 재추가할 수 있다 (같은 실행 안에서 해소 항목 재개봉 — 결과 요약 `해소 N건` 과 spec 모순). 기존 features 의 checked (b) 행 + 후속 analyze 재실행 조합도 동일.

**보강 내용** (`scope-sync.md` 5-2 규칙 2 를 다음 취지로 확장): 중복 판정 키는 **외부 도메인명** — 행 원문 전문 매칭이 아니다. 해당 feature 의 `### (b)` 에 동일 외부 도메인을 가리키는 행이 이미 존재하면 **체크 상태 (`- [x]`)·답변 append 여부와 무관하게** 추가 skip. interview.md 행 파싱 규칙 (2항) 에서 이 기준을 상호 링크한다.

## 인수인계 항목 소비 매핑 (project.md 미처리 항목 중 관련분)

| line | 항목 | 본 plan 활용 |
| --- | --- | --- |
| 113 | #09 cross-domain detect → OQ (b) 자동 입력 wiring (PR-2 후 필요) | **완료 확인** — create-feature SKILL.md:98-106 (3-bis) + analyze SKILL.md:167-169 에 wiring 실재. #17 의 3-ter/7.5 가 이 출력 (unchecked (b) 행) 을 인터뷰 입력으로 소비. plan 확정 후 `[x]` 처리. |
| 117 | #11 3-bis wiring 명문화 완료 + 픽스처 placeholder 답습 권고 | 결합 지점 확인 (위 OQ (a) 해소) 에 소비. #17 은 픽스처 무변경이라 placeholder 권고는 미해당. plan 확정 후 `[x]` 처리. |
| 129 | #14 가이드 출력 캡처 — SKILL.md 변경 PR 에서 함께 갱신 (상시 정책) | step 6 에서 `pilot/docs/tutorial/getting-started.md` Step 4 캡처 갱신으로 이행. 상시 정책이라 체크는 유보 (사용자 결정 — 보고서 참조). |
| 139 | #06 H2 정확 매칭 wording 패턴 답습 가능 | interview.md 의 `## Open Questions` H2 매칭 규칙에 동일 wording (`^## Open Questions\s*$` + 코드블록 펜스 안 무시) 답습. 상시 재사용 메모라 체크 유보. |
| 140 | #07 명시 패턴 (트리거 조건 / A2 fallback / 예외 열거) 답습 가능 | 3-ter · 7.5 본문 + interview.md 를 동일 명시 패턴으로 작성. 상시 재사용 메모라 체크 유보. |

## 범위

### 포함

- 인터뷰 규칙 SSOT 신설 (`interview.md`) — 발동 조건 · 행 파싱 · 산출물 대조 · 질의 규칙 · 답변 반영 · 결과 리포트 · 미발동 컨텍스트
- create-feature 3-ter 단계 신설 + step 6 결과 요약에 `인터뷰: 해소 N건 / 이월 M건` 라인 (발동 시에만 표기)
- analyze 7.5 단계 신설 + 8 단계 결과 출력에 동일 라인 + 해소 ≥ 1 건 시 `--regen-agents` 권장 INFO 1 줄
- regen-mode.md 에 7.5 미발동 명시 1 줄
- scope-sync.md 5-2 규칙 2 의 (b) 행 중복 판정 기준 명문화 (C1 — 외부 도메인명 키, 체크 상태 무관)
- open-questions.md ↔ interview.md 상호 링크 (작성 SSOT ↔ 소비 SSOT 짝 명시)
- getting-started.md Step 4 출력 캡처 보강 (인수인계 line 129 정책 이행)

### 제외

- doctor 신규 검증 룰 (기존 OQ check 로 충분 — 위 무영향 확인)
- Python 도구 · 테스트 · 회귀 픽스처 변경 (markdown-only)
- 에이전트 4종 (`pilot/agents/*.md`) · autopilot SKILL.md 변경 — autopilot 은 create-feature/analyze 를 호출하지 않음 확인 (`pilot/skills/autopilot/SKILL.md:40` — feature 부재 시 create-feature 안내 후 종료)
- open-questions.md 의 행 형식 · 템플릿 변경 (상호 링크 1~2 줄만)
- `.agent-state.yml` 스키마 변경 (spec 명시 — 상태값 변화 없음)
- 상한 (4/8) · 우선순위의 config.md 외부화 (v0.4.0+ 재고)

## 변경 파일

### 신설

- [x] `pilot/skills/context/shared/interview.md` — 조건부 인터뷰 규칙 SSOT (open-questions.md 와 동일 위상 · 동일 문체)

### 수정

- [x] `pilot/skills/create-feature/SKILL.md` — 3-bis 직후 `### 3-ter. 조건부 인터뷰` 신설 + step 6 결과 요약 템플릿에 인터뷰 라인 추가
- [x] `pilot/skills/analyze/SKILL.md` — 7 과 8 사이 `### 7.5 조건부 인터뷰` 신설 + 8 단계 결과 출력에 인터뷰 라인 추가
- [x] `pilot/skills/analyze/references/regen-mode.md` — step 목록 item 6 끝에 "7.5 (조건부 인터뷰) 미발동 — features 신규 생성 없음" 명시
- [x] `pilot/skills/analyze/references/scope-sync.md` — 5-2 규칙 2 (line 120) 의 "(중복 행은 skip)" 에 중복 판정 기준 명문화 (C1 — 판정 키 = 외부 도메인명, 체크 상태·답변 append 무관)
- [x] `pilot/skills/context/shared/open-questions.md` — 소비 규칙 SSOT (interview.md) 상호 링크 1~2 줄
- [x] `pilot/docs/tutorial/getting-started.md` — Step 4 기대 출력에 `인터뷰: 해소 0건 / 이월 2건` 라인 + "나중에 결정 스킵 시 현행 동일" 안내 1~2 문장 (인수인계 line 129 소비)

## interview.md 구성 명세 (Generator 가 직접 작성)

open-questions.md 의 문체·구조 (H1 + 한 줄 위상 설명 + `---` 구획 H2) 답습. 섹션 구성:

1. **발동 조건 (soft gate)** — 대상 spec 의 `## Open Questions` (H2 정확 매칭 `^## Open Questions\s*$`, 코드블록 펜스 안 등장 무시 — #06 wording 패턴) 하위에 `- [ ] ` prefix 행 ≥ 1. `- (없음)` · `- [x]` 만이면 무발동. **인터뷰는 게이트가 아님** — 어떤 실패·스킵도 스킬 본 흐름을 중단하지 않는다.
2. **행 파싱 규칙** — unchecked 판정은 `- [ ] ` prefix 만 (본문 3종 혼재 허용 — 위 대조 결과 인용). 체크 반영: `- [x] {원문 그대로} → {답변 요약}` (원문 보존 + append 1회, 마지막 `→` 뒤 = 답변 요약). **체크된 (b) 행은 5-2 재detect 의 재추가 대상이 아님** — 중복 판정 기준 (외부 도메인명 키, 체크 상태 무관) 은 `scope-sync.md` 5-2 규칙 2 가 SSOT, 여기서 상호 링크 (C1).
3. **산출물 대조 (경량 갭 체크)** — 질의 전 1회: spec 의 핵심 심볼 (상태값·메서드·필드·클래스) ↔ `workspace/context/scope/{domain}.md` lookup. **`{domain}` 은 `.agent-state.yml.domain` 만 사용 — null 이면 대조 스킵 (A2), 도메인 결정을 인터뷰 단계로 앞당기거나 자체 추론하지 않는다** (C2 — create-feature 3-ter 는 도메인 결정 (step 4 의 analyze 5 단계 전제) 보다 앞이므로 이 규칙이 첫 feature 케이스를 봉인). **대조 대상은 spec 본문에 명시 기재된 심볼만 — 유추 심볼 금지. 대조로 추가하는 (a) 행 수도 질의 상한과 동일 상한 (단건 4 / 일괄 8) — 초과 부재 심볼은 행 추가 자체를 하지 않는다 (spec 오염 방지)** (C3). 부재 심볼 → `### (a)` 에 `- [ ] {심볼}: scope/{domain}.md 미기재 — 실제 위치·시그니처 확인 필요` 행 추가 후 인터뷰 대상 포함. **코드베이스 Grep/Read 탐색 금지 — 심층 영향 분석은 @pilot-planner 책임 (역할 중복 금지)**. A2 fallback: scope 부재·빈 파일 → 대조 스킵, 기존 unchecked 만으로 진행, abort 금지.
4. **질의 규칙** — 우선순위 (d) > (b) > (c) > (a). 동일 카테고리 내: (단건) 파일 내 등장 순 / (일괄) 파일 NN 순 → 파일 내 등장 순 (C4 — 상한 초과 시 미질의로 밀리는 행이 결정적이 되도록). 상한: 단건 4 / 일괄 8 — 대조로 추가된 (a) 행도 상한 카운트 포함 ((a) 최하위라 초과 시 자연스럽게 미질의로 밀림). 초과분은 질의하지 않고 `미질의 N건` 리포트. 모든 질문에 "나중에 결정" 항상 제공. 질의는 메인 대화 (스킬 실행 컨텍스트) 에서만 — 서브에이전트·autopilot 은 인터뷰 미수행 (답변 전달은 spec 파일 경유).
5. **답변 반영** — 카테고리 → spec 섹션 매핑 가이드: (d) → `## 비즈니스 규칙` (요구사항 성격이면 `## 요구사항`) / (b)·(c) → `## 요구사항` 또는 `## 예외 케이스` / (a) → 해당 심볼이 언급된 섹션. **답변 원문 요지만 반영 — 답변에 없는 내용 추측 보강 금지** (analyze 추측 금지 원칙 동일). 스킵 항목은 spec 무변경 + unchecked 유지.
6. **결과 리포트** — `인터뷰: 해소 N건 / 이월 M건` (+ 상한 초과 시 ` / 미질의 K건`). **산술 규약 (C5): N = 답변으로 해소·체크된 항목, M = 질의 후 "나중에 결정" 으로 스킵된 항목 (K 불포함), K = 상한 초과로 질의되지 않은 항목. N + M + K = 발동 대상 unchecked 총수** (산출물 대조로 추가된 행 포함). 무발동 시 라인 자체 생략 (현행 출력과 동일 = 무중단 보장).
7. **미발동 컨텍스트** — analyze `--regen-agents` (features 신규 생성 없음) / 에이전트 4종·autopilot (무변경 — spec 파일 경유로만 결과 전달).

## 3-ter · 7.5 본문 계약 (배치·핵심 wording)

### create-feature `### 3-ter. 조건부 인터뷰 — Open Questions 소비 (#17)`

- 위치: 3-bis (line 98-106) 직후, `### 4.` 앞. **step 4 (prompts 갱신) 보다 앞이므로 답변이 prompts/ 에 자연 반영되는 순서** — 이 근거를 본문에 1 줄 명시.
- 본문: 발동 조건 (unchecked ≥ 1, `- (없음)` 뿐이면 skip) → 절차 3 항 (① 산출물 대조 — `{domain}` 은 `.agent-state.yml.domain`, null 이면 스킵 (C2) ② 우선순위 정렬 + 최대 4 문항 질의 ③ 답변 반영 + `- [x]` 체크) 요약 + 상세는 interview.md 링크 (3-bis 가 open-questions.md 를 위임하는 기존 패턴 답습).
- **C1 봉인 1 줄**: "3-ter 가 해소한 (b) 행은 step 4 (analyze 5-2 인용) 의 재detect 에서 재추가되지 않는다 — 중복 판정 기준: scope-sync.md 5-2 규칙 2" 를 본문에 명시 (같은 실행 안 재개봉 방지의 근거 링크).
- step 6 결과 요약 코드블록: `검증:` 라인 뒤에 `인터뷰: 해소 {N}건 / 이월 {M}건` 라인 추가 + "(3-ter 발동 시에만 표기)" 주석.

### analyze `### 7.5 조건부 인터뷰 — 신규 features Open Questions 일괄 소비 (#17)`

- 위치: `### 7.` (line 175-177) 직후, `### 8.` 앞.
- 본문: 대상은 **이번 실행에서 신규 생성된 features 만** (기존 features 의 unchecked 는 대상 아님) → 절차 3 항 (① 신규 features 각각 산출물 대조 — 5 단계에서 이미 Read 한 `scope/{domain}.md` 재사용, 추가 Read 불필요 ② 전체 unchecked 를 (d)>(b)>(c)>(a) → 파일 NN 순 정렬, 최대 8 문항 일괄 질의 ③ 답변 반영 + 체크) + `--regen-agents` 미발동 1 줄 + 상세는 interview.md 링크.
- 8 단계 (line 179-181): 출력 항목에 `인터뷰: 해소 N건 / 이월 M건` (7.5 발동 시) 추가. **해소 ≥ 1 건이면** `[INFO] 인터뷰 답변이 spec 에 반영됨 — prompts 최신화가 필요하면 /pilot:analyze --regen-agents 권장` 1 줄 추가 — 7.5 가 prompts 생성 (6 단계) 이후라는 위치 트레이드오프의 보완 (사용자 확정 위치 존중, 자동 재생성 금지).

## 단계별 구현 순서

1. **`pilot/skills/context/shared/interview.md` 신설** — 위 구성 명세 7 섹션. 참조 대상 (SSOT) 먼저 생성해야 후속 step 의 링크가 유효.
   - 영향 파일: `pilot/skills/context/shared/interview.md`
2. **create-feature SKILL.md 에 3-ter 신설 + step 6 결과 요약 라인 추가** — 위 본문 계약대로. 3-bis 의 위임 문체 (요약 + SSOT 링크) 답습.
   - 영향 파일: `pilot/skills/create-feature/SKILL.md`
3. **analyze SKILL.md 에 7.5 신설 + 8 단계 라인 추가** — 위 본문 계약대로.
   - 영향 파일: `pilot/skills/analyze/SKILL.md`
4. **analyze references 보강 (regen-mode + scope-sync)** — (a) regen-mode.md item 6 (`7 단계 — ... 7-2, 7-3 만 수행`) 끝에 " · 7.5 (조건부 인터뷰) 는 미발동 (features 신규 생성 없음)" append — regen-mode 가 자체 step enumeration 을 가지므로 암묵 skip 에 의존하지 않고 명시. (b) scope-sync.md 5-2 규칙 2 (line 120) 의 "(중복 행은 skip)" 를 "(중복 행은 skip — 판정 키는 **외부 도메인명**: 동일 외부 도메인을 가리키는 (b) 행이 이미 있으면 체크 상태 `- [x]`·답변 append 여부와 무관하게 skip. 소비 규칙: [interview.md](../../context/shared/interview.md))" 취지로 확장 (C1).
   - 영향 파일: `pilot/skills/analyze/references/regen-mode.md` · `pilot/skills/analyze/references/scope-sync.md`
5. **open-questions.md 상호 링크** — 도입부 (line 3 문단 직후) 에 blockquote 1~2 줄: 소비 (조건부 인터뷰) 규칙은 `interview.md` 가 SSOT, 행 형식 (`- [ ]` prefix) 이 파싱 소스이므로 본 문서의 행 형식 변경 시 양쪽 동기화.
   - 영향 파일: `pilot/skills/context/shared/open-questions.md`
6. **getting-started.md Step 4 캡처 보강** — 기대 출력 코드블록 끝에 `인터뷰: 해소 0건 / 이월 2건` 라인 추가 (예시 시나리오는 (a)·(d) 2 건 unchecked → 발동 케이스) + line 143 문단에 "unchecked 항목이 있으면 조건부 인터뷰가 발동 — **이 예시는 (d)·(a) 2 건이 질의된 뒤 모두 '나중에 결정' 을 선택한 시나리오** (해소 0 / 이월 2 / 미질의 0). 스킵하면 기존 흐름과 완전히 동일" 취지 1~2 문장 (C6 — 캡처와 산술 규약 (C5) 이 자기 완결되도록). 출력 코드블록 재캡처는 하지 않는다. `quick-start.md` 는 출력 캡처 없음 확인 — 무변경.
   - 영향 파일: `pilot/docs/tutorial/getting-started.md`
7. **doctor 검증 + markdown-only 확인** — `python3 pilot/tools/doctor.py workspace` 실행 (기존 룰 위반 0 확인, features/17 의 `- [x]` 체크 행 무해 재확인) + `git diff --stat` 에 `.py` 변경 0 건 확인.
   - 영향 파일: (검증만 — 변경 없음)

## 검증 방법

- **무발동 경로 동일성**: `- (없음)` 만인 spec 기준으로 3-ter/7.5 본문이 "건너뛴다" 를 명시하고, 결과 요약 인터뷰 라인이 "발동 시에만 표기" 인지 확인 → 현행 출력과 diff 0.
- **상호 링크 유효성**: `../context/shared/interview.md` (create-feature·analyze 기준) · `interview.md` (open-questions.md 기준) 상대 경로 실재 확인.
- **doctor exit 0 유지** (step 7).
- **C1 봉인 확인**: scope-sync.md 5-2 규칙 2 에 중복 판정 기준 (외부 도메인명 키·체크 상태 무관) 존재 + interview.md 2항·create-feature 3-ter 본문에서 상호 링크 — 3-ter 해소 행이 같은 실행의 step 4 에서 재개봉되지 않는 설계 근거가 3곳에서 일관.
- **역할 분리 명문화 확인**: interview.md 에 "코드베이스 Grep/Read 금지 — @pilot-planner 책임" 문구 존재.
- **회귀 픽스처 무영향**: `analyze/expected/` 캡처는 인터뷰 무발동 경로 (OQ 전부 `(없음)`) 라 diff 0 — 픽스처 무변경 근거. 향후 recapture 시 unchecked 가 있는 케이스는 "나중에 결정" 일괄 선택으로 파리티 유지 (주의사항 참조).

## 주의사항

- **추측 금지 원칙과의 정합**: 인터뷰는 사용자 답변만 spec 에 반영한다. 답변에 없는 내용의 추측 보강 금지 — analyze 의 "원본에 없는 내용 추측 금지" (SKILL.md:120) 와 동일 축.
- **질의 도구 중립**: interview.md 는 질의 형식 (우선순위·상한·"나중에 결정") 만 규정하고 특정 도구 (AskUserQuestion 등) 를 지정하지 않는다 — 스킬 본문 관례 유지.
- **analyze 7.5 위치 트레이드오프**: prompts (6 단계) 는 인터뷰 전 spec 기준으로 생성됨. 해소 ≥ 1 건 시 `--regen-agents` 권장 INFO 1 줄로 보완하고 자동 재실행은 하지 않는다 (사용자 확정 위치 + A2 철학).
- **create-feature 는 analyze 5~6 단계만 인용** (SKILL.md:110) → 3-ter 와 7.5 의 이중 발동 없음. 7.5 본문의 "신규 생성된 features 만" 한정이 이 경계의 SSOT.
- **checked (b) 행 재개봉 방지는 후속 실행에도 적용** (C1): 기존 features 의 `- [x]` (b) 행이 있는 상태에서 후속 `/pilot:analyze` 가 5-2 재detect 를 수행해도 scope-sync 중복 판정 기준 (외부 도메인명 키) 이 재추가를 막는다 — 7.5 가 신규 features 만 대상이라 재질의도 없으므로 이 기준이 유일한 방어선.
- **상한 카운트**: 산출물 대조로 추가된 (a) 행 포함. 단건 4 / 일괄 8 은 "질의 수" 상한 — 대조가 spec 에 **추가하는 (a) 행 수도 동일 상한** (C3, 초과 부재 심볼은 행 미추가). 질의는 상한까지만.
- **체크박스 갱신 권한**: generator 는 `project.md` 의 `## 목표` 체크박스를 self-mark 하지 않는다 (evaluator wrapper 단독 권한 — #03 인수인계).
- **문체 답습**: interview.md 는 open-questions.md 의 H1 + 위상 설명 + `---` H2 구획 문체, 3-ter/7.5 는 #07 명시 패턴 (트리거 조건 / 절차 / A2 fallback / 예외 열거 — 인수인계 line 140) 답습. 새 형식 발명 금지.
- **getting-started.md 캡처는 happy-path 예시** — "wording 차이 ≠ 회귀" 정책 (README) 하에서 SKILL.md 결과 요약과 1:1 일치를 강제하지 않는다. 인터뷰 라인 1 줄 + 안내 문장만 추가 (과도한 재캡처 금지).
- **도메인 지식 stale 예고**: `workspace/context/pilot/spec.md` 의 analyze "8 단계 프로세스" · create-feature 단계 기술은 본 변경 후 stale — 구현 후 `/pilot:learn` 재실행 또는 drift-protocol 승인 하 갱신 (별도, 본 plan 범위 외. 드리프트 보고서 참조).
