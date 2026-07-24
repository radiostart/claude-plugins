# Plan Critic — #17 조건부 인터뷰 (Open Questions 소비)

> 입력 plan: `features/17-conditional-interview.plan.md` (검토 시각 2026-07-24T00:00:00Z)
> 입력 feature: `features/17-conditional-interview.md`
> 페르소나: `personas.planner-critic` (red-team)
> focus 반영: 없음

plan 의 인용 검증 결과 (챌린지 아님 — 통과 확인): create-feature 3-bis 위치 (SKILL.md:98-106) · step 4 의 analyze 5~6 인용 (SKILL.md:110) · analyze 7/8 단계 위치 (SKILL.md:175-181) · 5-2 detect (SKILL.md:167-169) · open-questions.md 행 형식 3종 (:11 / :51 / :53) · `check_features_open_questions` 위치·행 형식 무관 거동 (integrity.py:1317-1372) · autopilot hard-stop (SKILL.md:40 부근) · regen-mode item 6 · getting-started.md Step 4 캡처의 (a)·(d) 2건 unchecked 시나리오 (docs/tutorial/getting-started.md:134-138) · analyze/expected 픽스처 unchecked OQ 행 0건 — 전부 원문과 일치.

## 챌린지

### C1 — 3-ter 해소 직후 step 4 의 5-2 detect 가 동일 (b) 행을 unchecked 로 재추가할 수 있음
- **severity**: blocking
- **category**: edge-case
- **plan 인용**: `## 3-ter · 7.5 본문 계약` create-feature 절 (3-ter 를 step 4 앞에 배치) + `## spec Open Question (a) 해소` 의 체크 형식 (`- [x] {원문} → {답변 요약}` append)
- **챌린지**: create-feature 흐름에서 3-ter 가 (b) 행을 해소 (`- [x] ... → 답변`) 한 직후, step 4 가 analyze 5-2 를 그대로 수행한다 (SKILL.md:110). 5-2 의 cross-domain detect 는 외부 도메인이 여전히 미학습이면 다시 매칭되고, `scope-sync.md:120` 의 중복 판정 기준은 "중복 행은 skip" 한 줄뿐이다. plan 이 정의한 체크 형식 (checkbox 변경 + 답변 append) 은 detect 가 추가하려는 행 원문과 **텍스트가 반드시 달라지므로**, 문자 그대로 해석하면 중복이 아니게 되어 방금 해소한 질문이 같은 실행 안에서 unchecked 로 재개봉된다 — 결과 요약 `해소 1건` 과 spec 상태가 모순. 기존 features 의 checked (b) 행 + 후속 analyze 실행 조합에서도 동일하게 재발한다 (7.5 는 신규 features 만 대상이라 재질의도 안 됨). 이 충돌은 plan 자신이 만든 것 (append 형식 + step 4 후행 배치) 인데 대응이 없고, `scope-sync.md` 는 변경 파일 목록에도 없다.
- **제안**: 중복 판정을 체크 상태·append 무시 기준으로 명문화 — "동일 외부 도메인의 (b) 행이 존재하면 (`- [x]` 체크·답변 append 포함) 추가 skip". 위치는 `scope-sync.md` 5-2 규칙 2 에 1 줄 추가 (변경 파일 목록에 추가) 하거나, 최소한 interview.md 행 파싱 규칙에 명시 + scope-sync 에서 상호 링크. planner 가 둘 중 하나를 plan 에 반영해야 함.

### C2 — create-feature 3-ter 시점의 {domain} 확정 소스 미명시
- **severity**: suggestion
- **category**: premise
- **plan 인용**: `## interview.md 구성 명세` 3항 (산출물 대조 — `scope/{domain}.md` lookup) + 3-ter 배치 (step 4 앞)
- **챌린지**: 도메인 결정은 analyze 5 단계 전제 (analyze SKILL.md:137) 로, create-feature 에서는 **step 4 에서야** 수행된다. 3-ter 는 그보다 앞이므로 첫 feature (`.agent-state.yml.domain` null) 케이스에서 대조 대상 scope 파일 자체를 특정할 수 없다. A2 fallback (scope 부재 → 스킵) 이 안전망이긴 하나 "domain null" 이 "scope 부재" 로 읽힌다는 보장이 없고, 실행 LLM 이 도메인 결정 질의를 3-ter 로 앞당기거나 자체 추론하는 out-of-spec 거동 여지가 남는다.
- **제안**: interview.md 3항에 1 줄 추가 — "{domain} 은 `.agent-state.yml.domain` 만 사용. null 이면 산출물 대조 스킵 (A2, 도메인 결정을 앞당기지 않는다)". analyze 7.5 는 5 단계에서 이미 결정·Read 됐으므로 영향 없음.

### C3 — 산출물 대조가 spec 에 추가하는 (a) 행 수에 상한 없음
- **severity**: suggestion
- **category**: risk
- **plan 인용**: `## interview.md 구성 명세` 3·4항 (부재 심볼 → (a) 행 추가, 질의 상한은 4/8)
- **챌린지**: 상한 4/8 은 **질의 수** 상한이고, 대조가 `### (a)` 에 **행을 추가하는 수** 는 무제한이다. scope/{domain}.md 가 부실한 (막 생성된 5-1.5 자동 생성 등) 상태면 spec 의 핵심 심볼 다수가 "부재" 로 판정되어 질의되지도 않을 unchecked (a) 행이 spec 을 오염시킨다 — 이월 행이 많을수록 후속 analyze·doctor 출력 noise 도 커진다.
- **제안**: interview.md 3항에 행 추가 기준·상한 명시 — 예: "대조 대상 심볼은 spec 본문에 명시 기재된 것만 (유추 심볼 금지), 대조로 추가하는 (a) 행도 질의 상한 (단건 4 / 일괄 8) 을 넘지 않는다". 정확한 수치는 planner 판단 — 상한 존재 자체가 핵심.

### C4 — 단건 (create-feature) 의 동일 카테고리 내 정렬 규칙 미정의
- **severity**: nit
- **category**: scope
- **plan 인용**: `## interview.md 구성 명세` 4항 — "동일 카테고리 내: (일괄) 파일 NN 순 → 파일 내 등장 순"
- **챌린지**: 정렬 규칙이 (일괄) 케이스만 정의됐다. 단건도 상한 4 초과 시 어떤 행이 미질의로 밀리는지가 정렬에 의존하므로 미정의는 비결정 요소.
- **제안**: "(단건) 파일 내 등장 순" 1 구 추가.

### C5 — 결과 리포트 산술 규약 미정의 (이월 M 에 미질의 K 포함 여부)
- **severity**: nit
- **category**: edge-case
- **plan 인용**: `## interview.md 구성 명세` 6항 — `인터뷰: 해소 N건 / 이월 M건` (+ ` / 미질의 K건`)
- **챌린지**: M 이 "질의 후 스킵된 항목" 만인지 "잔여 unchecked 전체 (미질의 K 포함)" 인지 미정의. 정의에 따라 N+M 또는 N+M+K = 발동 대상 총수라는 합산이 달라져, getting-started 캡처 (`해소 0건 / 이월 2건`) 와 실제 출력이 어긋날 수 있다.
- **제안**: 6항에 1 줄 — "M = 질의 후 스킵 항목, K = 상한 초과 미질의 항목 (M 에 불포함). N+M+K = 발동 대상 총수".

### C6 — getting-started 캡처가 발동 케이스인데 질의 상호작용이 출력 예시에 없음
- **severity**: nit
- **category**: scope
- **plan 인용**: 단계 6 (getting-started.md Step 4 캡처 보강) · `## 주의사항` happy-path 항목
- **챌린지**: 기대 출력에 `해소 0건 / 이월 2건` 라인만 추가하면 독자는 (d)·(a) 2건 질의가 실제로 일어났는지 알 수 없다. plan 의 안내 문장 1~2 개가 부분적으로 커버하므로 재확인만 필요.
- **제안**: 안내 문장에 "(d)·(a) 2건 질의 후 모두 '나중에 결정' 을 선택한 시나리오" 임을 명시하면 캡처와 산술이 자기 완결됨. 출력 코드블록 재캡처는 불필요 ("과도한 재캡처 금지" 유지).

## 합의 (planner 가 재호출되어 채움 — 처음에는 비워둠)

| C# | 처리 | 메모 |
|----|------|------|
| C1 | accepted | `scope-sync.md` 를 변경 파일 목록에 추가 (plan step 4-(b)). 5-2 규칙 2 의 "(중복 행은 skip)" 을 판정 기준 명문화로 확장 — 키 = 외부 도메인명, 체크 `- [x]`·답변 append 무관 skip. interview.md 2항 + 3-ter 본문에서 상호 링크 (plan "C1 해결" 절). 후속 analyze 재실행의 checked 행 재개봉도 동일 기준으로 방어 (주의사항 추가). |
| C2 | accepted | interview.md 3항에 명시 — `{domain}` 은 `.agent-state.yml.domain` 만 사용, null 이면 산출물 대조 스킵 (A2). 도메인 결정을 3-ter 로 앞당기거나 자체 추론하는 out-of-spec 거동 봉인. 3-ter 본문 절차 ① 에도 반영. |
| C3 | accepted | interview.md 3항에 명시 — 대조 대상 = spec 본문 명시 기재 심볼만 (유추 금지) + (a) 행 추가 수 상한 = 질의 상한과 동일 수치 (단건 4 / 일괄 8), 초과 부재 심볼은 행 미추가 (spec 오염 방지). 별도 리포트 토큰 신설은 안 함 (출력 단순성 유지). |
| C4 | accepted | interview.md 4항 — "(단건) 파일 내 등장 순" 추가. 상한 초과 시 미질의로 밀리는 행이 결정적. |
| C5 | accepted | interview.md 6항 — N = 해소·체크, M = 질의 후 스킵 (K 불포함), K = 상한 초과 미질의. N+M+K = 발동 대상 총수. getting-started 캡처 (해소 0 / 이월 2 / 미질의 0) 와 정합 확인. |
| C6 | accepted | plan step 6 — 안내 문장에 "(d)·(a) 2건 질의 후 모두 '나중에 결정' 선택 시나리오" 명시. 출력 코드블록 재캡처는 안 함 ("과도한 재캡처 금지" 유지). |
