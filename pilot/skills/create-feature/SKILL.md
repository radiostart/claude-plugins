---
name: create-feature
description: >-
  활성 프로젝트에 프롬프트 한 줄로 단일 feature 명세(features/NN-{slug}.md)를
  추가하고 project.md·prompts/* 를 동기화한다. 기획서(docs/) 기반 다건 분할은
  `/pilot:analyze`. 실행은 @pilot-planner 호출로 시작 — 자동 파이프라인 아님.
---

# /pilot:create-feature

활성 프로젝트에 **단일 기능** 을 프롬프트로 추가한다. `features/` 폴더에 명세 파일을 생성하고 `project.md` (목표·관련 파일) 와 `prompts/*.md` 를 `/pilot:analyze` 와 동일한 절차로 동기화한다. 구현 흐름은 `@pilot-planner` 호출로 시작.

대상: $ARGUMENTS (기능 지시문 — 예: "지연 주문 UI 정렬 기능 — 기본 내림차순, 출고일 필터")

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P-1, P0, P1** 수행. 실패 시 [messages.md](../context/shared/messages.md) 의 `workspace_missing`/`no_active_project` 출력 후 종료. `$ARGUMENTS` 가 비어있으면 안내 후 종료.

## 동작

### 1. 기능명·slug·번호 결정

프롬프트에서 **기능명**(한국어 허용, 30자 이내) · **slug**(kebab-case, 최대 30자) 추출. **NN** = `features/*.md` (`.plan.md` 제외) 최댓값+1 (폴더 없으면 `01`). slug 모호하면 후보 2~3개 제시 후 선택받는다.

### 2. features/ 폴더 확인·생성

없으면 생성.

### 3. `features/NN-{slug}.md` 작성

`> source: prompt` + `> created:` + `> user_prompt:` 메타 + analyze 와 동일 4 섹션(요구사항/상태 전환/비즈니스 규칙/예외 케이스) 템플릿으로 Write. 프롬프트에서 명시 추출 가능한 요소만 채우고 **추측성 내용은 placeholder 로 남긴다**.

`## 예외 케이스` 직후 `## Open Questions` 4 카테고리(a~d) + `- (없음)` placeholder 필수. 템플릿·분류 기준: [`../context/shared/open-questions.md`](../context/shared/open-questions.md).

### 3-bis. cross-domain 의존성 detect + Open Questions 분류 (#09 + #11)

MANIFEST 를 조회해 산출물 lookup 으로 답할 수 없는 영역을 detect 하고 Open Questions 4 카테고리로 분류한다 — 매칭 외부 도메인은 `### (b)` 에 행 + INFO, 코드 외부 시스템은 `### (c)` 에 행. 알고리즘·A2 fallback 상세: [`../context/shared/open-questions.md`](../context/shared/open-questions.md) `cross-domain 의존성 detect 시 분류 매핑`.

### 3-ter. 조건부 인터뷰 — Open Questions 소비 (#17)

step 4(prompts 갱신) 보다 **앞**에 위치 — 답변이 spec 에 먼저 반영돼야 재생성이 최신 spec 기준으로 동작한다. **발동 조건**: unchecked(`- [ ] `) 항목 ≥1 (soft gate — `- (없음)` 뿐이면 skip). 절차: (1) spec 명시 심볼 ↔ `scope/{domain}.md` 대조(`{domain}` 은 `.agent-state.yml.domain` 만, null 이면 스킵) (2) (d)>(b)>(c)>(a) 순 최대 4문항 질의("나중에 결정" 항상 제공) (3) 답변 반영 후 `- [x] {원문} → {답변 요약}` 체크. 상세: [`../context/shared/interview.md`](../context/shared/interview.md).

**재개봉 방지**: 3-ter 가 해소한 `### (b)` 행은 step 4(analyze 5-2 재detect)에서 재추가되지 않는다 — 판정 키는 [`../analyze/references/scope-sync.md`](../analyze/references/scope-sync.md) 5-2 규칙 2(외부 도메인명)가 SSOT.

### 4. `project.md` 및 `prompts/*` 자동 갱신

[../analyze/SKILL.md](../analyze/SKILL.md) 의 **"분석 프로세스" 5 ~ 6 단계**를 그대로 수행한다 (도메인 결정·5-1·5-2·6-1~6-4 절차·보존 규칙 모두 analyze 가 SSOT). 실제 차이는 2 가지뿐: 분석 소스가 docs/ 가 아니라 **현재 features/ 전체**, 첫 feature 추가 시(`analyzed: false`)는 example placeholder 가 실내용으로 교체된다.

### 5. 무결성 검증 (자동)

[../analyze/SKILL.md](../analyze/SKILL.md) 의 **6-5 단계**와 동일:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace
```

출력 규칙: [`../pilot-doctor/SKILL.md`](../pilot-doctor/SKILL.md) § 임베디드 호출 시 출력 규칙 참조.

### 6. 결과 요약

생성(`features/{NN}-{slug}.md`) + 갱신(project.md/prompts 3종/.agent-state.yml) + 검증 결과 + (3-ter 발동 시) `인터뷰: 해소 {N}건 / 이월 {M}건` + 다음 단계 안내 — `/pilot:autopilot {NN}` (자동 진행) 또는 `@pilot-planner` (수동 시작) 병기.

## 제약

- **이 스킬은 에이전트를 자동 호출하지 않는다.** Planner → Generator → Evaluator 흐름은 사용자가 각각 명시 호출. feature 시작점은 `@pilot-planner`.
- **prompt-origin feature 는 `> source: prompt`** 로 표시 — `/pilot:analyze --force` 가 이 tag 를 감지해 덮어쓰기 승인을 받는다.
- **docs 기반 feature 생성은 `/pilot:analyze`** 사용. 이 스킬은 docs 없이 단건 추가 용도.

## 참고

- `/pilot:analyze` — docs/ 기획서 벌크 분석
- `/pilot:focus` — ad-hoc 사용자 지시 기록 (features/ 밖)
- `@pilot-planner` — features/{NN}-{slug}.md 를 읽어 구현 계획 수립
- `/pilot:autopilot {NN}` — 생성한 feature 1건을 자동 순차 진행 (opt-in)
