---
name: create-feature
description: >-
  활성 프로젝트에 사용자 프롬프트 한 줄로 단일 feature 명세를 추가할 때
  사용한다. features/NN-{slug}.md 를 prompt-origin 템플릿으로 생성하고
  `/pilot:analyze` 와 동일하게 project.md (목표·관련 파일) 와 prompts/*
  (planner·generator·evaluator) 를 함께 동기화한다. 기획서(docs/) 기반
  다건 분할은 `/pilot:analyze` 를 사용한다. 실행은 @pilot-planner 호출로 시작 —
  자동 파이프라인 아님.
---

# /pilot:create-feature

활성 프로젝트에 **단일 기능** 을 프롬프트로 추가한다. `features/` 폴더에 명세 파일을 생성하고 `project.md` (목표·관련 파일) 와 `prompts/*.md` 를 `/pilot:analyze` 와 동일한 절차로 동기화한다. 구현 흐름은 `@pilot-planner` 호출로 시작.

대상: $ARGUMENTS (기능 지시문 — 예: "지연 주문 UI 정렬 기능 — 기본 내림차순, 출고일 필터")

**사용 예:**

```
/pilot:create-feature 지연 주문 UI 에 정렬·필터 추가
/pilot:create-feature 알림 발송 기능 — 비동기 큐 사용
```

---

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P-1, P0, P1** 수행.

- P-1: TodoWrite 선로딩 (다단계 스킬).
- P0: `{PROJECT}` 와 `$ARGUMENTS` 키워드로 memory-hint 실행. 출력된 메모를 Read 하여 과거 동일·유사 기능 이력 확인.
- P1: `{PROJECT}` 획득. 실패 시 [messages.md](../context/shared/messages.md) 의 `workspace_missing` / `no_active_project` 출력 후 종료.

`$ARGUMENTS` 가 비어있으면 **"기능 지시문을 입력하세요. 예: `/pilot:create-feature 정렬 기능 추가`"** 안내 후 종료.

---

## 동작

### 1. 기능명·slug·번호 결정

프롬프트에서 추출:

- **기능명** — 지시문의 핵심 표현 (한국어 허용, 30자 이내)
- **slug** — 기능명을 kebab-case 로 변환 (영문·한글 혼합 허용, 특수문자 제거, 최대 30 자)
- **NN** — `workspace/projects/{PROJECT}/features/*.md` 의 `.plan.md` 제외 번호 중 최댓값 + 1. 폴더 없으면 `01` 부터.

예:

```
지시문: "지연 주문 UI 에 정렬·필터 추가"
→ 기능명: "지연 주문 UI 정렬·필터"
→ slug: "delayed-order-sort-filter" (또는 "지연-주문-정렬-필터")
→ NN: 06 (기존 features 5 개인 경우)
```

slug 결정이 모호하면 사용자에게 후보 2-3 개 제시 후 선택받는다.

### 2. features/ 폴더 확인·생성

`workspace/projects/{PROJECT}/features/` 가 없으면 생성.

### 3. `features/NN-{slug}.md` 작성

아래 템플릿으로 Write:

```markdown
# #{NN} {기능명}

> source: prompt
> created: {ISO 8601 UTC timestamp}
> user_prompt: "{원문 지시}"

## 요구사항

- **조건**: _(상세 필요 — @pilot-planner 가 영향 분석 시 보강)_
- **트리거**: _(상세 필요)_
- **기대결과**: _({프롬프트에서 추출 가능한 결과})_

## 상태 전환

_(상태값 변화가 있는 기능만 작성)_

## 비즈니스 규칙

- _(프롬프트에서 읽히는 규칙이 있으면 기재)_

## 예외 케이스

- _(초기 비움 — @pilot-planner 가 영향 분석 중 발견 시 추가)_
```

프롬프트에서 명시적으로 추출 가능한 요소 (상태 값·정렬 기준·트리거 등) 는 해당 섹션에 채워 넣는다. 추측성 내용은 **넣지 않는다** — placeholder 로 둠.

`## 예외 케이스` 섹션 직후에 `## Open Questions` 4 카테고리 섹션 (`### (a) 같은 도메인 추가 read 필요` · `### (b) cross-domain 산출물 부재` · `### (c) 외부 시스템 spec 부재` · `### (d) 비즈니스 결정 영역`) + 각 카테고리 `- (없음)` placeholder 를 반드시 추가한다. 4 카테고리 분류 기준·템플릿·작성 규칙: [`../context/shared/open-questions.md`](../context/shared/open-questions.md).

### 3-bis. cross-domain 의존성 detect + Open Questions 분류 (#09 + #11)

feature spec 작성 후 MANIFEST 를 조회해 산출물 lookup 으로 답할 수 없는 영역을 detect 하고, 발견된 영역을 Open Questions 4 카테고리로 분류한다.

1. `workspace/context/MANIFEST.md` Read.
2. 사용자 프롬프트·작성된 spec 에서 클래스/도메인 키워드 추출.
3. MANIFEST 의 `## 도메인 분류` 표·`## 외부 도메인 reference` 표에서 lookup → 매칭 외부 도메인은 `### (b)` 에 행 추가 + INFO 출력 / 코드 외부 시스템은 `### (c)` 에 행 추가.

매핑 알고리즘·INFO 메시지·A2 fallback 상세: [`../context/shared/open-questions.md`](../context/shared/open-questions.md) `cross-domain 의존성 detect 시 분류 매핑` 섹션.

### 3-ter. 조건부 인터뷰 — Open Questions 소비 (#17)

3-bis 직후, step 4(prompts 갱신)보다 앞에 위치한다 — 답변이 spec 에 먼저 반영돼야 step 4 의 prompts/ 재생성이 최신 spec 을 기준으로 동작한다.

**발동 조건:** `## Open Questions` 하위 unchecked(`- [ ] `) 항목이 1 개 이상. `- (없음)` 뿐이면 이 단계를 건너뛴다(soft gate — 발동하지 않아도 흐름은 계속됨).

**절차:**

1. **산출물 대조** — spec 명시 심볼 ↔ `scope/{domain}.md` lookup. `{domain}` 은 `.agent-state.yml.domain` 만 사용하며 null 이면 대조를 스킵한다.
2. **우선순위 정렬 + 질의** — (d) > (b) > (c) > (a) 순, 동일 카테고리는 파일 내 등장 순. 최대 4 문항까지 사용자에게 질의(모든 질문에 "나중에 결정" 제공).
3. **답변 반영** — 해당 spec 섹션에 반영 후 항목을 `- [x] {원문} → {답변 요약}` 으로 체크. 스킵 항목은 unchecked 유지.

상세 규칙(행 파싱·상한 산술·미발동 컨텍스트 등): [`../context/shared/interview.md`](../context/shared/interview.md).

> **재개봉 방지(C1):** 3-ter 가 해소한 `### (b)` 행은 step 4(analyze 5-2 인용)의 cross-domain 재detect 에서 재추가되지 않는다 — 중복 판정 기준은 [`../analyze/references/scope-sync.md`](../analyze/references/scope-sync.md) 5-2 규칙 2(판정 키 = 외부 도메인명, 체크 상태·답변 append 무관)가 SSOT.

### 4. `project.md` 및 `prompts/*` 자동 갱신

신규 feature 파일 생성 후 [../analyze/SKILL.md](../analyze/SKILL.md) 의 **"분석 프로세스" 5 ~ 6 단계** 를 그대로 수행한다 (도메인 결정·5-1·5-2·6-1~6-4 절차와 보존 규칙 모두 analyze 가 SSOT).

analyze 와의 실제 차이는 2 가지뿐:

- 분석 소스가 docs/ 가 아니라 **현재 features/ 전체**다.
- 첫 feature 추가 시 (`analyzed: false`) 는 example 템플릿 placeholder 가 features 기반 실내용으로 교체된다 (보존할 게 없음).

### 5. 무결성 검증 (자동)

[../analyze/SKILL.md](../analyze/SKILL.md) 의 **6-5 단계** 와 동일 — 아래를 실행한다:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace
```

ERROR 또는 WARN 있으면 원문을 사용자에게 그대로 출력. 모두 PASS 면 `doctor: all checks passed` 한 줄만.

### 6. 결과 요약

```
Feature 생성 완료: #{NN} {기능명}

생성:
  - features/{NN}-{slug}.md  (prompt-origin 템플릿)

갱신:
  - project.md           (목표 +1, 관련 파일 동기화)
  - prompts/planner.md    (기능별 사전 확인 사항)
  - prompts/generator.md  (기술 레퍼런스)
  - prompts/evaluator.md  (체크리스트)
  - .agent-state.yml     (analyzed: true)

검증: {doctor 결과 한 줄 요약}
인터뷰: 해소 {N}건 / 이월 {M}건  (3-ter 발동 시에만 표기)

다음 단계:
→ 명세가 부족하면 features/{NN}-{slug}.md 직접 편집
→ `@pilot-planner` 를 호출해 구현 계획을 수립하세요.
```

---

## 제약

- **이 스킬은 에이전트를 자동 호출하지 않는다.** Planner → Generator → Evaluator 흐름은 사용자가 각각 명시 호출. feature 의 시작점은 `@pilot-planner`.
- **prompt-origin feature 는 `> source: prompt`** 로 표시된다. `/pilot:analyze --force` 실행 시 이 tag 를 감지해 사용자에게 덮어쓰기 여부를 확인한다 (의도되지 않은 데이터 손실 방지).
- **docs 기반 feature 생성은 `/pilot:analyze`** 사용. 이 스킬은 docs 없이 단건 추가 용도.

---

## 참고

- `/pilot:analyze` — docs/ 기획서 벌크 분석
- `/pilot:focus` — ad-hoc 사용자 지시 기록 (features/ 밖)
- `@pilot-planner` — features/{NN}-{slug}.md 를 읽어 구현 계획 수립
