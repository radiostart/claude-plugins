# #08 project SKILL.md `{프로젝트명}` 치환 범위 명문화 — Implementation Plan

> source: features/08-project-token-substitution.md · 직전 plan 협상 (옵션 C — plan 만 저장, generator 호출은 별도)
> mode: standard (tdd: false)
> planner_at: 2026-05-20

## 사전 결정 사항 (Q1~Q3 + 공통 5건)

사용자가 모든 권고를 채택 (a 옵션 일괄). v0.3.0 LOW priority 3 features (#06·#07·#08) SKILL.md wording 명확화 turn 안에 결정.

| Q | 결정 | 근거 |
| --- | --- | --- |
| 공통-1 코드 변경 여부 | **SKILL.md 본문만**. example template 의 self-reference 정리는 이미 backtick wrap 완료 (현 상태 확인 — example/project.md:7) | NS #5 cycle 검증 — LLM 사실상 거동 中. 명문화만. |
| 공통-2 PR 단위 | #06·#07·#08 **일괄 단일 PR** (`docs: pilot SKILL.md wording 명확화 #06·#07·#08`) | LOW priority + 코드 변경 없음 + 회귀 영향 없음 |
| 공통-3 version bump | v0.3.0 합본 PR 끝 일괄. 본 PR 단독 patch bump 안 함 | #16 Q9 답습 |
| 공통-4 회귀 fixture | **변경 없음**. `project/expected/projects/python-sample-demo/` H1 = `# python-sample-demo` byte-diff 0 보장 | spec line 46 — 본 변경 후 cycle 재실행 시 동일 산출 |
| 공통-5 getting-started.md drift | 본 PR 머지 시 `pilot/docs/getting-started.md` 의 project 출력 코드블록 점검 후 동기 수정 | 인수인계 line 128 (#14 후속) |
| Q1 치환 범위 명시 위치 | project SKILL.md:63 의 "그대로 복사한 뒤 `{프로젝트명}` 토큰만 ... 치환" 직후 **신규 blockquote 1 단락** 추가 | spec line 22-25 wording 그대로 |
| Q2 example template self-reference 정리 | example/project.md:7 는 이미 `` `{프로젝트명}` `` backtick wrap 完. prompts/*.md 의 H1 (`# Planner — {프로젝트명}` 등) 은 self-reference 아니라 치환 대상. **추가 정리 없음** | 현 파일 grep 결과 — 이미 backtick wrap |
| Q3 정규식 채택 | spec line 35 "단순화 채택" 따름 — `^#\s+.*\{프로젝트명\}.*$` (단일 라인 H1 안 토큰) | prompts/ 의 `# Planner — {프로젝트명}` 형식 매칭 가능 |

## 인수인계 항목 소비 매핑 (project.md 미처리 항목)

| line | 항목 | 본 plan 활용 |
| --- | --- | --- |
| 31 | features/04 A2 runtime fallback — SKILL.md 본문 변경 (from #04) | 치환 범위 blockquote 내 A2 fallback 1 줄 (H1 토큰 부재 → 치환 skip + INFO + abort 안 함). step 1. |
| 99 | #03 체크박스 갱신 권한 분리 (from #03) | 본 plan generator 가 `## 목표` 체크박스 self-mark 금지 명시. 주의사항. |
| 101 | example/project.md 단순화 — 신규 프로젝트 생성 시점부터 적용 (from #03) | 본 #08 의 변경이 example template 본문 변경 없음 — backtick wrap 은 이미 완료. 회귀 영향 0. step 2. |
| 128 | #14 getting-started.md drift (from #14) | step 3 검증 방법 1줄 — 본 PR 머지 시 getting-started.md project 출력 코드블록 점검. |

## 범위

### 포함

- project SKILL.md `## 2. 프로젝트 폴더 생성/로드` (line 60-87) 의 토큰 치환 절차에 **치환 범위 명시 blockquote 1 단락** 추가
- H1 헤더 정확 매칭 정규식 인용 (`^#\s+.*\{프로젝트명\}.*$` — Q3 단순화 채택)
- 보존 대상 명시 (가이드 주석 prose · 코드블록 · 표 본문 안 `{프로젝트명}` self-reference)
- A2 runtime fallback (H1 토큰 부재 → 치환 skip + INFO + abort 안 함)
- 사용자 프로젝트명 sanitize 룰 1 줄 (`[a-zA-Z0-9가-힣\-_]` 외 차단 → 사용자 질의)

### 제외 (v0.3.0 범위 외 또는 v0.4.0 이월)

- example template 의 self-reference backtick wrap 정리 — **이미 완료** (현 파일 grep 결과). 본 PR 변경 없음.
- prompts/*.md 의 self-reference 정리 — prompts/ 의 `# Planner — {프로젝트명}` 등은 H1 치환 대상 (self-reference 아님). 변경 없음.
- H1 코드블록 안 위치 케이스 (spec line 35 — v0.3.0 범위 외, v1.1 milestone)
- 회귀 픽스처 갱신 (spec line 46 — byte-diff 0 보장)
- 단위 테스트 신설 (spec line 46 — 회귀 fixture H1 검증으로 충분)

## 변경 파일

### 수정

- [x] `pilot/skills/project/SKILL.md`
  - line 63 (없으면: 분기) 안의 "그대로 복사한 뒤 `{프로젝트명}` 토큰만 ... 치환" 문장 직후 **신규 blockquote 1 단락** (~10-15 줄) 추가

### 신설 / 삭제

- 없음 (example template 의 self-reference 는 이미 backtick wrap 完 — 본 PR 변경 없음)

## 단계별 구현 순서

1. **치환 범위 blockquote 1 단락 추가** (`pilot/skills/project/SKILL.md` line 63 직후)
   - 기존 `- **없으면**: ... 그대로 복사한 뒤 \`{프로젝트명}\` 토큰만 실제 프로젝트명으로 치환한다. **그 외 본문은 일절 재작성·요약·환각·도메인 예시 삽입 금지.**` 직후, 들여쓰기 유지하며 신규 blockquote:
     ```markdown
       > **치환 범위 (H1 헤더 정확 매칭)** — 토큰 치환은 다음 두 조건을 모두 만족하는 라인만 대상:
       >
       > - `^#\s+.*\{프로젝트명\}.*$` 정확 매칭 (단일 라인 H1 안 `{프로젝트명}` 토큰)
       > - 코드블록 (` ``` `) 외부 위치
       >
       > **보존 대상 (치환 안 함):**
       >
       > - 가이드 주석 (`> \`{프로젝트명}\` 토큰만 ...` 같은 self-reference) — example template 의 스캐폴딩 설명용. 본문 prose 안 백틱 토큰은 보존.
       > - 마크다운 코드블록 (` ``` `) 안의 `{프로젝트명}` — 예시 코드.
       > - 표 본문 셀 안의 `{프로젝트명}` — 예시 행.
       >
       > **사용자 프로젝트명 sanitize** — `[a-zA-Z0-9가-힣\-_]` 외 문자 (예: `{`·`}`·정규식 메타) 포함 시 차단하고 사용자 질의 prompt. sanitize 통과 후 H1 치환 진행.
       >
       > **A2 runtime fallback** — H1 헤더에 `{프로젝트명}` 토큰 부재 (사용자가 이미 H1 직접 작성 등) → 치환 skip + `[INFO] {프로젝트명} 토큰 부재 — 치환 skip, 기존 H1 보존` 1 줄. abort 하지 않는다.
       >
       > **대상 파일 (4 종)** — 본 단계가 치환하는 파일은 `project.md` 1 + `prompts/{planner,generator,evaluator}.md` 3 = 총 4 종. 각 파일의 H1 1 회씩 치환 (`# {프로젝트명}` / `# Planner — {프로젝트명}` / `# Generator — {프로젝트명}` / `# Evaluator — {프로젝트명}`).
     ```

2. **example template self-reference 확인 — 변경 없음** (grep 검증 결과)
   - `pilot/skills/context/lifecycle/projects/example/project.md`:
     - line 1: `# {프로젝트명}` ← H1 치환 대상 (정상)
     - line 7: `` > `{프로젝트명}` 토큰만 ... `` ← **이미 backtick wrap 완료** (현 상태 — 변경 없음, spec line 26-28 의 의도 이미 충족)
   - `pilot/skills/context/lifecycle/projects/example/prompts/{planner,generator,evaluator}.md`:
     - 각 line 1: `# Planner — {프로젝트명}` 등 ← H1 치환 대상 (정상)
     - 본문 안 self-reference 부재 — 변경 불요.
   - 결론: example template 본문 변경 없음. 본 PR 은 SKILL.md 본문 blockquote 1 단락 추가만.

3. **검증 방법 (Generator 자체 sanity)**
   - `pilot/skills/project/SKILL.md` line 63 직후 들여쓰기·blockquote 형식 유지 확인 (`- **없으면**:` list item 안 nested blockquote 정합).
   - 기존 `## 관련 파일 H3 동적 채움` blockquote (line 70-78) 와 충돌하지 않는지 확인 — 둘 다 같은 list item 의 sub-bullet 으로 자연스럽게 공존.
   - `pilot/docs/getting-started.md` 의 project 출력 코드블록 drift 점검 (인수인계 line 128). project SKILL.md 본문 변경이 출력 형식을 깨지 않는 한 변화 없음. 변화 있으면 본 PR 안에 동기 수정.
   - 기존 회귀 fixture `pilot/tests/fixtures/v0.1.0-baseline/project/expected/projects/python-sample-demo/project.md` 의 H1 = `# python-sample-demo` (NS #5 검증 결과) 가 본 변경 후에도 동일 산출 가능한지 확인 (spec line 46 — byte-diff 0 보장).

## 검증 방법

- project SKILL.md line 63 직후 blockquote 1 단락 추가 (~10-15 줄)
- 치환 범위 5 요소 (H1 정확 매칭 정규식 / 보존 대상 3 / sanitize 룰 / A2 fallback / 대상 파일 4종) 모두 포함
- example template 본문 변경 없음 (grep 검증 — `{프로젝트명}` 5건 위치 모두 정상)
- markdown 구조 (list item 안 nested blockquote 들여쓰기) 유지
- `pilot/docs/getting-started.md` project 출력 코드블록 drift 점검 후 필요 시 동기 수정 (인수인계 line 128)
- 기존 회귀 fixture `project/expected/projects/python-sample-demo/project.md` H1 byte-diff 0 (자체 검증은 #00 의 0c 회귀 검증과 묶어 일괄)

## 주의사항

- **체크박스 갱신 권한 분리** (인수인계 line 99 #03) — 본 plan 의 generator 가 `project.md` 의 `## 목표` 의 #08 항목을 self-mark 하지 않는다. evaluator wrapper step 5 가 단독 권한자.
- **example template 본문 변경 금지** (인수인계 line 101 #03) — example/project.md 의 단순화 결정 (H3+표 제거, H2+가이드 주석만) 은 신규 프로젝트 생성 시점부터 적용. 기존 build-plugin 의 project.md 는 영향 없음. 본 #08 PR 도 example template 본문 변경 안 함 — backtick wrap 은 이미 완료.
- **prompts/*.md H1 형식 정규식 정합** — `^#\s+.*\{프로젝트명\}.*$` 정규식이 `# {프로젝트명}` (project.md) 와 `# Planner — {프로젝트명}` (prompts/) 양쪽 매칭. 단순 정규식 채택 (Q3 — spec line 35 의 단순화 옵션) — `^#\s+\{프로젝트명\}\s*$` 정확 매칭이면 prompts/ 매칭 실패.
- **list item 안 nested blockquote 들여쓰기** — markdown 들여쓰기 (`  > **치환 범위**:`) 정확히 2 spaces. 깨지면 blockquote 가 list item 밖으로 빠져나가 SKILL.md 본문 구조 깨짐.
- **sanitize 룰의 한국어 처리** — `[a-zA-Z0-9가-힣\-_]` 정규식의 `가-힣` 범위가 한국어 음절 (`가` ~ `힣`) 만 포함. 한국어 자모 (`ㄱ`~`ㅎ`·`ㅏ`~`ㅣ`) 는 차단. NS #5 cycle 검증 = 음절만 사용 일반적 — 본 PR 범위 그대로.
- **`pilot/docs/getting-started.md` drift 점검** (인수인계 line 128) — 본 PR 머지 시 project Step 2 출력 코드블록 1회 점검. 치환 절차 wording 변경이 출력 형식 깨면 본 PR 안에 동기 수정 포함.
- **회귀 fixture 변경 금지** — spec line 46 — NS #5 검증 = 거동 동일 명문화. `pilot/tests/fixtures/v0.1.0-baseline/project/expected/` 의 어떤 파일도 본 PR 에서 수정 안 함. H1 byte-diff 0 검증으로 본 변경이 회귀 영향 없음을 확인.

## 교차 의존

- **features/00 (회귀 fixture)** — 본 PR 머지 후 회귀 검증 시 byte-diff 0 확인. 변경 fixture 없음.
- **features/03 (project.md H3 동적 생성)** — project SKILL.md 의 같은 `## 2. 프로젝트 폴더 생성/로드` 안에 H3 동적 채움 blockquote (line 70-78) 가 이미 존재. 본 #08 의 치환 범위 blockquote 가 그 직전 (line 63 직후) 에 추가됨 — 같은 list item 안 두 blockquote 가 공존. 들여쓰기 정합 확인 필요 (step 3 sanity).
- **features/04 (doctor 검증)** — 본 #08 변경은 doctor 검증과 무관 (SKILL.md 본문만).
- **features/06 (#06)** — 동일 PR 묶음. learn Phase 5 H2 정확 매칭 (#06) ↔ 본 #08 의 H1 정확 매칭 — 둘 다 헤더 정확 매칭 강화 흐름.
- **features/07 (#07)** — 동일 PR 묶음. 독립 변경.
- **features/13 (init wizard)** — wizard 의 `## 결과 출력` 안 "scope 후보: M개 매핑 ({폴더목록})" wording (인수인계 line 124) 은 본 #08 의 prompts/ 치환과 무관. 본 PR 변경 없음.
- **features/14 (#14)** — 인수인계 line 128 — getting-started.md drift 점검. 본 plan step 3 에 명시.
- **인수인계 line 31·99·101·128** — 본 plan step 1~3 에서 4 건 모두 소비. evaluator wrapper step 2 가 `project.md` 의 4 행 `[x]` 처리.
