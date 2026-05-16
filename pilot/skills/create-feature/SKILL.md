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

[preamble.md](../context/shared/preamble.md) 의 **P1** 수행.

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

`## 예외 케이스` 섹션 직후에 아래 Open Questions 섹션을 반드시 추가한다:

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

**Open Questions 작성 규칙:**

- 4 카테고리 헤더는 항상 모두 포함한다. 카테고리 자체를 생략하지 않는다.
- 한 카테고리에 질문이 없으면 `- (없음)` 으로 표시 (작성자가 "정말 없는지" 의식적 확인 강제).
- 산출물 lookup 시 답할 수 없는 영역이 발견되면 아래 3-bis 의 분류 기준에 따라 해당 카테고리에 `- [ ] {질문}: ...` 행을 추가한다.
- A2 runtime fallback: detect 알고리즘 실패 시 → 4 카테고리 헤더 + `- (없음)` placeholder 만 작성. abort 안 함.

### 3-bis. cross-domain 의존성 detect + Open Questions 분류 (#09 + #11)

feature spec 작성 후, 산출물 lookup 시 답할 수 없는 영역이 있는지 MANIFEST 를 조회하고, 발견된 영역을 Open Questions 4 카테고리로 분류한다.

1. `workspace/context/MANIFEST.md` 를 Read.
2. 사용자 프롬프트 및 작성된 feature spec 에 등장하는 클래스/도메인 키워드를 추출한다.
3. 키워드를 MANIFEST 의 `## 도메인 분류` 표와 `## 외부 도메인 reference` 표 양쪽에서 lookup:
   - `## 외부 도메인 reference` 표에 매칭되는 도메인이 있으면:
     - Open Questions `### (b) cross-domain 산출물 부재` 에 `- [ ] {외부 도메인} 산출물 부재 → \`/pilot:learn {추천 경로}\` 권장` 행 추가.
     - INFO 1 줄: `[INFO] 이 feature 는 {외부 도메인} 의존성이 감지됨 — 먼저 \`/pilot:learn {추천 경로}\` 권장`
   - 매칭 없음이지만 산출물로 cover 되지 않는 영역 (외부 시스템 API 등) 이 있으면 Open Questions `### (c) 외부 시스템 spec 부재` 에 `- [ ] {외부 시스템} spec 별도 확보 필요` 행 추가.

**Open Questions 카테고리 분류 기준:**

- **(a) 같은 도메인 추가 read 필요**: scope/{domain}.md 에서 메서드 시그니처는 캡처됐지만 line-by-line detail 부족한 경우.
- **(b) cross-domain 산출물 부재**: MANIFEST `## 외부 도메인 reference` 표에 매칭되는 미학습 도메인.
- **(c) 외부 시스템 spec 부재**: 코드 외부 시스템 (외부 API, 사내 다른 서비스 등).
- **(d) 비즈니스 결정 영역**: PM/PO 결정 영역 (코드로 결정할 수 없는 비즈니스 판단).

> **A2 runtime fallback**: MANIFEST lookup 실패 또는 키워드 추출 실패 시 → spec 진행 (abort 안 함). Open Questions 에는 4 카테고리 헤더 + `- (없음)` placeholder 만 기입. INFO 출력 안 함.

### 4. `project.md` 및 `prompts/*` 자동 갱신

신규 feature 파일 생성 후 [../analyze/SKILL.md](../analyze/SKILL.md) 의 **"분석 프로세스" 5 ~ 6 단계** 를 그대로 수행한다 — 분석 소스가 docs/ 가 아니라 **현재 features/ 전체** 라는 점만 다르다.

수행 항목:

- **도메인 결정** (5 단계 prelude). `.agent-state.yml.domain` 이 null 이면 analyze 와 동일한 우선순위로 후보 제시 후 사용자 확인 → state 에 기록. non-null 이면 그대로 사용 (재질의 금지).
- **5-1. `## 목표` 갱신** — features 전체로 체크리스트 정렬 갱신. 기존 `[x]` 체크는 보존, 신규 feature 항목이 NN 순서에 추가된다.
- **5-2. `## 관련 파일` 갱신** — `config.md` 의 `## scope 카테고리` (없으면 SKILL.md default) 매핑에 따라 `scope/{domain}.md` 의 해당 H2 표를 추출해 `## 관련 파일` 표 자동 기입. config lookup·A2 runtime fallback 상세는 [analyze/SKILL.md](../analyze/SKILL.md) 5-2 참조.
- **6-1 ~ 6-3. prompts/\* 갱신** — `[analyze-managed]` 섹션을 features 전체 + scope 매칭 결과로 regen. `[analyze-managed]` 밖 사용자 수동 편집 영역 (`## 주의사항`·`## 구현 패턴` 등) 과 evaluator 의 `[x]` 체크는 보존.
- **6-4. `.agent-state.yml` 갱신** — `analyzed: true`, `analyzed_at`, `last_analyzed_features` 기록. domain 이 이번에 처음 결정됐다면 함께 기록.

**보존 규칙 요약** (analyze 와 동일):

- 기존 features 의 `### {기능명}` 블록은 그대로 유지되고 신규 feature 의 블록만 추가된다 (NN 순).
- 첫 feature 추가 시 (`analyzed: false`) 는 example 템플릿 placeholder 가 features 기반 실내용으로 교체된다 (보존할 게 없음).
- `[analyze-managed]` 안에 사용자가 수동으로 끼워 넣은 내용은 덮어써진다 (analyze 와 동일한 트레이드오프).

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
