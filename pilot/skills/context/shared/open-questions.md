# Open Questions 4 카테고리

`/pilot:analyze` 와 `/pilot:create-feature` 가 공유하는 Open Questions 작성 규칙과 분류 기준. features/NN-*.md 작성 시 `## Open Questions` 섹션의 SSOT. 생성 후 **미해결 항목의 게이트 판정 기준**(§ 판정 매트릭스)도 본 문서가 SSOT — `@pilot-planner`·`@pilot-generator`·`@pilot-evaluator` 와 `tools/plan-validate.py` 가 공유한다.

> **소비 규칙(조건부 인터뷰)** 은 [`interview.md`](interview.md) 가 SSOT — unchecked (`- [ ] `) 행이 여기 작성 규칙대로 만들어지므로, 본 문서의 행 형식을 바꾸면 `interview.md` 의 행 파싱 규칙도 함께 동기화해야 한다.
> **게이트 판정(사이클 시점)** 은 아래 § 판정 매트릭스가 SSOT — 인터뷰가 명세 생성 시점에 항목을 선해소(`[x]`)할 수 있으나 인터뷰는 게이트가 아니며, 미해소 잔존분은 매트릭스 기준 그대로다.

---

## 작성 규칙

- 4 카테고리 헤더는 항상 모두 포함한다. 카테고리 자체를 생략하지 않는다.
- 한 카테고리에 질문이 없으면 `- (없음)` 으로 표시 (작성자가 "정말 없는지" 의식적 확인 강제).
- 산출물 lookup 시 답할 수 없는 영역이 발견되면 아래 분류 기준에 따라 해당 카테고리에 `- [ ] {질문}: ...` 행 추가.
- A2 runtime fallback: detect 알고리즘 실패 시 → 4 카테고리 헤더 + `- (없음)` placeholder 만 작성. abort 안 함.

---

## 템플릿

```markdown
## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- (없음)

### (d) 비즈니스 결정 영역
- (없음)
```

---

## 카테고리 분류 기준

- **(a) 같은 도메인 추가 read 필요**: scope/{domain}.md 에서 메서드 시그니처는 캡처됐지만 line-by-line detail 부족한 경우.
- **(b) cross-domain 산출물 부재**: MANIFEST `## 외부 도메인 reference` 표에 매칭되는 미학습 도메인.
- **(c) 외부 시스템 spec 부재**: 코드 외부 시스템 (외부 API, 사내 다른 서비스 등).
- **(d) 비즈니스 결정 영역**: PM/PO 결정 영역 (코드로 결정할 수 없는 비즈니스 판단).

---

## cross-domain 의존성 detect 시 분류 매핑

1. `workspace/context/MANIFEST.md` 를 Read.
2. 사용자 프롬프트 및 작성된 feature spec 에 등장하는 클래스/도메인 키워드를 추출.
3. 키워드를 MANIFEST 의 `## 도메인 분류` 표와 `## 외부 도메인 reference` 표 양쪽에서 lookup:
   - `## 외부 도메인 reference` 표에 매칭되는 도메인이 있으면:
     - `### (b) cross-domain 산출물 부재` 에 `- [ ] {외부 도메인} 산출물 부재 → \`/pilot:learn {추천 경로}\` 권장` 행 추가.
     - INFO 1 줄: `[INFO] {외부 도메인} 의존성 감지 — 먼저 \`/pilot:learn {추천 경로}\` 권장`.
   - 매칭 없음이지만 산출물로 cover 되지 않는 영역 (외부 시스템 API 등) 이 있으면 `### (c) 외부 시스템 spec 부재` 에 `- [ ] {외부 시스템} spec 별도 확보 필요` 행 추가.

> **A2 runtime fallback**: MANIFEST lookup 실패 또는 키워드 추출 실패 시 → spec 진행 (abort 안 함). Open Questions 에는 4 카테고리 헤더 + `- (없음)` placeholder 만 기입. INFO 출력 안 함.

---

## 판정 매트릭스 (게이트)

feature 명세 `## Open Questions` 의 **미해결 항목 처리·판정 기준**. `@pilot-planner` · `@pilot-generator` · `@pilot-evaluator` 세 wrapper 와 `tools/plan-validate.py` 가 본 매트릭스를 단일 기준으로 공유한다 — 세 에이전트가 서로 다른 기준으로 통과/반려를 판정하는 것을 막는다.

> **경계** — 카테고리 (a)~(d) 의 생성·분류 기준은 위 § 카테고리 분류 기준. 본 절은 생성된 항목의 **게이트 판정**만 다룬다. 명세 생성 시점의 조건부 인터뷰([`interview.md`](interview.md))가 항목을 선해소(`[x]`)할 수 있다 — 판정 매트릭스는 불변이며, 미해소 잔존분은 아래 기준 그대로다.

| 카테고리 | Planner 처리 (원칙) | 미해결 잔존 시 plan 마커 | Generator | Evaluator |
|---|---|---|---|---|
| **(a) 같은 도메인 추가 read 필요** | 해당 scope 파일 추가 Read → 해결되면 feature 항목 `[x]` Edit | `범위 제외` 또는 `추정 구현` | plan-validate 통과 시 진행 | 마커 부재 → **Major** |
| **(b) cross-domain 산출물 부재** | `/pilot:learn {추천 경로}` 실행을 사용자에게 먼저 권고 (산출물 없이 구현하면 환각 위험). 사용자가 "그냥 진행" 명시 시에만 `추정 구현` 마킹 | `추정 구현` (사용자 명시 전제) 또는 `범위 제외` | `추정 구현` 항목은 TODO 주석 필수 (아래 규약) | 마커 부재 → **Major** |
| **(c) 외부 시스템 spec 부재** | 사용자에게 spec 확보 여부 먼저 질의. 없으면 해당 인터페이스를 구현 범위에서 제외하고 plan 에 `범위 제외` + TODO 마킹 | `범위 제외` (기본) 또는 `추정 구현` (사용자 명시 전제) | 동일 | 마커 부재 → **Major** |
| **(d) 비즈니스 결정 영역** | **반드시** 사용자에게 질의해 답을 받은 뒤 `- [x] {항목} → 결정: {내용}` 으로 Edit. **임의 결정 금지** | `범위 제외` 만 (사용자가 결정 보류를 명시한 경우 한정). `추정 구현` **불인정** | 동일 | 구현이 임의 결정 → **Major** |

공통 원칙: **임의로 채우거나 "합리적 추정" 으로 건너뛰기 금지** — 한 번 잘못된 전제가 들어가면 generator·evaluator 전체가 오염된다.

### 마커 어휘 (기계 검증 계약)

`plan-validate.py` 가 미해결 항목이 있는 **카테고리마다** plan 본문(fenced 코드블록 제외)에서 다음을 요구한다:

1. **정밀 마커 (권장)** — 카테고리 키(`(a)`~`(d)`)와 마커 어휘가 **같은 라인**에 등장.

   ```markdown
   ### Open Questions 처리

   - (b) 결제 도메인 산출물 부재: 추정 구현 — 사용자 "그냥 진행" 승인 (2026-06-10)
   - (c) PG API spec 부재: 구현 범위에서 제외 — 인터페이스부 TODO 마킹
   ```

   - `추정 구현` — 산출물·spec 없이 추정으로 구현. **사용자 "그냥 진행" 명시가 전제.** 권장 전체 문구: "산출물 부재 상태에서 추정 구현".
   - `범위 제외` (또는 `범위에서 제외`) — 해당 인터페이스·결정 영역을 이번 구현 범위에서 제외.

2. **포괄 마커 (하위 호환)** — 키 없이 "산출물 부재 상태에서 추정 구현" 전체 문구. **(d) 를 제외한** 모든 미해결 카테고리를 커버. 신규 plan 은 정밀 마커 권장.

3. **(d) 특칙** — `추정 구현` 불인정 (임의 결정 금지의 기계적 표현). `(d)` 키 + `범위 제외` 동일 라인(사용자가 결정 보류를 명시한 경우) 또는 해결(`[x]`)만 통과.

검증 호출 지점은 [`plan-schema.md`](../lifecycle/plan-schema.md) § 호출 지점과 동일 — Planner step 6 (plan 저장 직후) · Generator step 2 (plan Read 직전). **둘 다 같은 도구를 실행하므로 판정이 어긋날 수 없다.**

> 기존 운영 plan 중 표준 어휘 없이 작성된 것은 재검증 시 invalid 가 될 수 있다 — fail-closed 의 의도된 결과. `@pilot-planner` 재호출로 마커를 보완한다.

### 에스컬레이션 경로 (게이트 실패 시)

Generator·Evaluator 가 게이트 실패를 발견한 시점에 **planner 인스턴스는 이미 종료되어 있다** — "Planner 에 재확인" 은 대화가 아니라 **새 `@pilot-planner` 호출**(stateless 재진입)로 수행한다. 발견한 에이전트는 직접 라우팅하지 않고 미해결 항목·plan 경로를 사용자에게 보고한 뒤 다음 두 갈래를 안내하고 종료한다:

1. **plan 보완** — 오케스트레이터가 `@pilot-planner` 를 재호출. planner 가 본 매트릭스대로 항목을 해결(`[x]`)하거나 plan 에 마커를 명시 → plan-validate 재통과 후 `@pilot-generator` 재진입.
2. **(d) 직접 해결** — 사용자가 결정을 답하면 메인 세션이 feature 파일 해당 항목을 `- [x] {항목} → 결정: {내용}` 으로 Edit 한 뒤 중단된 단계(`@pilot-generator` 또는 `@pilot-evaluator`)를 재호출.

자동 라우팅 금지 — 항상 사용자 보고 후 선택 ([`guardrails.md`](guardrails.md) § A16 의 자동 실행 금지 원칙과 동일).

### Generator TODO 주석 규약

plan 에 `추정 구현` 마커로 진행하는 항목은 해당 인터페이스 코드에 다음 주석을 달아 명확히 표시한다 (언어별 주석 문법 적용):

```
# TODO: Open Questions (b)/(c) 미해결 — 확보 후 재구현 필요
```

Evaluator 는 `추정 구현` 항목에 이 주석이 없으면 **Minor** 로 escalate 한다.

### 변경 시

게이트 기준 변경은 다음 파일과 동기화:

- `tools/plan-validate.py` — 마커 매칭 로직 (`check_open_questions`)
- `tests/tools/test_plan_validate.py` — `OpenQuestionsGate` 회귀 테스트
- `agents/pilot-planner.md` § 플래닝 프로세스 1 · `agents/pilot-generator.md` step 2·3 · `agents/pilot-evaluator.md` step 3 — 참조 지점
- [`plan-schema.md`](../lifecycle/plan-schema.md) § Open Questions 게이트 검사
- [`guardrails.md`](guardrails.md) § 기본 판정 축 — `open_questions` gate
