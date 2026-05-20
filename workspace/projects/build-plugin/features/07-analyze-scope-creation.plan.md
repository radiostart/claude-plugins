# #07 analyze SKILL.md scope/{domain}.md 생성 절차 명시 — Implementation Plan

> source: features/07-analyze-scope-creation.md · 직전 plan 협상 (옵션 C — plan 만 저장, generator 호출은 별도)
> mode: standard (tdd: false)
> planner_at: 2026-05-20

## 사전 결정 사항 (Q1~Q3 + 공통 5건)

사용자가 모든 권고를 채택 (a 옵션 일괄). v0.3.0 LOW priority 3 features (#06·#07·#08) SKILL.md wording 명확화 turn 안에 결정.

| Q | 결정 | 근거 |
| --- | --- | --- |
| 공통-1 코드 변경 여부 | **SKILL.md 본문만**. doctor·script·fixture 변경 없음 | NS #5 cycle 검증 — LLM 사실상 거동 中. 명문화만. |
| 공통-2 PR 단위 | #06·#07·#08 **일괄 단일 PR** (`docs: pilot SKILL.md wording 명확화 #06·#07·#08`) | LOW priority + 코드 변경 없음 + 회귀 영향 없음 |
| 공통-3 version bump | v0.3.0 합본 PR 끝 일괄. 본 PR 단독 patch bump 안 함 | #16 Q9 답습 |
| 공통-4 회귀 fixture | **변경 없음**. `expected/scope/python-sample.md` byte-diff 0 보장 | spec line 46 — 본 변경 후 cycle 재실행 시 동일 파일 산출 |
| 공통-5 getting-started.md drift | 본 PR 머지 시 `pilot/docs/getting-started.md` 의 analyze 출력 코드블록 점검 후 동기 수정 | 인수인계 line 128 (#14 후속) |
| Q1 자동 생성 절차 위치 | analyze SKILL.md:208 (5-2 H4) 직전에 **신규 H4 `#### 5-1.5. scope/{domain}.md 자동 생성`** 삽입 | 5-1 (목표 갱신) ↔ 5-2 (관련 파일 갱신) 사이에 자연스러운 단계 위치 |
| Q2 본문 추출 우선순위 | inventory.md → index.md → 빈 표 + INFO | spec line 22-25 그대로 |
| Q3 wizard 인용 주입 1줄 (인수인계 line 123) | 5-1.5 본문에 1줄 — "`/pilot:init` wizard 가 작성한 `## learn 언어 패턴` 표 행이 inventory.md 산출 형식의 SSOT — 표 헤더 일치 시 그 행 그대로 인용" | #13 인수인계 line 123 직접 소비 |

## 인수인계 항목 소비 매핑 (project.md 미처리 항목)

| line | 항목 | 본 plan 활용 |
| --- | --- | --- |
| 31 | features/04 A2 runtime fallback — SKILL.md 본문 변경 (from #04) | 5-1.5 의 본문 추출 3순위 fallback (빈 표 + INFO + 5-2 진행) 이 A2 패턴 명시. step 1. |
| 93 | #01 의 A2 runtime fallback 절차 SKILL.md 본문 명시 (from #01) | 5-1.5 의 본문 추출 실패 시 stderr WARN 1 줄 + abort 안 함 wording 답습. step 1. |
| 95 | #02 의 default 격하 blockquote 패턴 + A2 runtime fallback + 3 예외 (from #02) | 5-1.5 의 wording 형식 답습 (MANIFEST 진입파일 부재 / config 빈 표 / scope 파일 부재 3 예외). step 1. |
| 123 | #13 wizard 가 features/01 default 표 행 그대로 인용 주입 명시 (from #13) | **5-1.5 본문에 1줄 명시** — wizard 산출 ↔ inventory.md 산출 ↔ scope 헤더의 SSOT 관계. step 2. |
| 128 | #14 getting-started.md drift (from #14) | step 4 검증 방법에 1줄 — 본 PR 머지 시 getting-started.md analyze 출력 코드블록 점검. |

## 범위

### 포함

- analyze SKILL.md 5-1 (목표 갱신) ↔ 5-2 (관련 파일 갱신) **사이에 신규 H4 `#### 5-1.5. scope/{domain}.md 자동 생성`** 삽입
- scope 파일 생성 트리거 룰 (scope 파일 부재 + MANIFEST 진입파일에 표 헤더 존재) 본문 명시
- 본문 추출 우선순위 3단 (inventory.md → index.md → 빈 표 + INFO) 본문 명시
- idempotency 룰 (기존 scope 파일 존재 시 새로 만들지 않음, 사용자 수동 추가 행 보존) 본문 명시
- wizard 인용 주입 SSOT 1 줄 (인수인계 line 123)
- 예외 4건 (MANIFEST 진입파일 부재 / config 빈 표 default 사용 / inventory.md 부재 → index.md / scope 헤더 prefix 위반 → doctor 사전 차단) 본문 명시

### 제외 (v0.3.0 범위 외 또는 v0.4.0 이월)

- `/pilot:analyze --regen-scope` v2 옵션 (spec line 29 — 사용자 수동 자동 갱신 분리)
- `/pilot:analyze --multi-domain` v2 (spec line 37)
- 회귀 픽스처 갱신 (spec line 46 — byte-diff 0 보장)
- 단위 테스트 신설 (spec line 45 — LLM 절차 따르기로 검증)
- doctor·script 변경

## 변경 파일

### 수정

- [x] `pilot/skills/analyze/SKILL.md`
  - 5-1 (line 188-206) 와 5-2 (line 208~) 사이에 **신규 H4 `#### 5-1.5. scope/{domain}.md 자동 생성`** 1 단락 (~30-40 줄) 삽입

### 신설 / 삭제

- 없음

## 단계별 구현 순서

1. **신규 H4 `#### 5-1.5. scope/{domain}.md 자동 생성` 삽입** (`pilot/skills/analyze/SKILL.md` line 207 직후 / 208 의 5-2 H4 직전)
   - 본문 구조:
     ```markdown
     #### 5-1.5. scope/{domain}.md 자동 생성

     5-2 진입 전 scope 파일 부재를 detect 하고 자동 생성한다. NS #5 cycle 검증 결과 — LLM 이 사실상 5-2 진입 시 이 절차를 수행 中. 본 단계는 그 거동의 명문화.

     **트리거 조건 (둘 다 만족):**

     - `workspace/context/scope/{domain}.md` 부재 또는 빈 파일
     - MANIFEST 진입파일 (`workspace/context/{domain}/index.md` 또는 `workspace/context/{domain}.md`) 에 `config.md` 의 `## scope 카테고리` `scope 헤더` 컬럼 값과 일치하는 H2 헤더 존재

     **본문 구성:**

     - H2 헤더 = `config.md` 의 `scope 헤더` 컬럼 값 그대로 (예: `## Routes`·`## Models`·`## Services`).
     - 표 헤더 = `config.md` 의 `표 헤더` 컬럼 값 (예: `엔드포인트, Method, 목적`).
     - 표 본문 행은 아래 우선순위로 추출:
       1. `workspace/context/{domain}/inventory.md` 의 역할 분류 표 (learn 산출) — 해당 카테고리 행 추출. `## Routes` → 역할 = `routes`, `## Models` → 역할 = `models`. 각 행에 `(file:line)` 인용 그대로 복사.
       2. `workspace/context/{domain}/index.md` 본문의 매칭 표 (사용자 수동 정의 가능성).
       3. 본문 추출 실패 → 표 헤더만 있는 빈 표 + `[INFO] scope/{domain}.md 표 본문 추출 실패 — 사용자 수동 채움 권장` 1 줄.

     > **wizard 인용 주입 SSOT** — `/pilot:init` wizard 가 작성한 `workspace/context/config.md` 의 `## learn 언어 패턴` 표 행 (features/01 default 매핑) 이 inventory.md 산출 형식의 SSOT. 표 헤더 일치 시 그 행을 그대로 인용해 본문 추출 — wizard 결정과 analyze 산출 사이의 정합 보존.

     **idempotency:**

     - `scope/{domain}.md` 가 이미 존재 (빈 파일 아님) → 새로 만들지 않는다. 5-2 가 그대로 사용.
     - 사용자가 직접 작성한 행 (자동 생성 행 외) 도 그대로 보존. 자동 갱신은 별도 옵션 (`/pilot:analyze --regen-scope` v2 외).

     > **A2 runtime fallback**: 본 단계 실패 (MANIFEST 진입파일 부재·본문 추출 실패) → 빈 표 + INFO 1 줄 + 5-2 진행 (abort 안 함). 사용자 수동 채움 후 다음 analyze 호출 시 5-2 가 정상 추출.

     **예외:**

     - MANIFEST 진입파일 부재 → scope 파일 생성 skip + `[INFO] MANIFEST 진입 파일 없음 — scope 파일 생성 skip` 1 줄. 5-2 도 skip (5-2 의 기존 룰과 일관).
     - `config.md` 의 `## scope 카테고리` 빈 표 → features/02 default 매핑 사용 (Routes/Models/Services → Endpoints/Models/Services). scope 파일 헤더도 default 따라 작성.
     - `inventory.md` 부재 → 1순위 실패. 2순위 (`index.md`) 또는 3순위 (빈 표 + INFO) 적용.
     - `scope 헤더` 컬럼 값이 `## ` prefix 미준수 → features/04 의 doctor 검증이 사전 차단 (ERROR). 본 단계 진입 자체가 안 됨 — A2 fallback 으로 default 적용.
     ```

2. **wizard 인용 주입 SSOT 1줄 검토** — 위 본문의 blockquote 가 인수인계 line 123 의 "wizard 가 features/01 default 표 행을 인용 주입한다" wording 직접 명시. 추가 변경 없음.

3. **5-2 본문 정합 확인** — 5-1.5 신설 후 5-2 의 "scope 파일 자체가 없으면 동일하게 skip" wording (line 230) 이 5-1.5 의 자동 생성 룰과 모순되지 않는지 확인. 5-1.5 가 scope 파일을 만들면 5-2 의 skip 분기 진입 안 함 — 본문 변경 없이 정합.

4. **검증 방법 (Generator 자체 sanity)**
   - `pilot/skills/analyze/SKILL.md` 의 5-1·5-1.5·5-2 H4 순서가 깨지지 않는지 확인.
   - markdown 구조 (H4 들여쓰기·list·blockquote 형식) 유지 확인.
   - `pilot/docs/getting-started.md` 의 analyze 출력 코드블록 drift 점검 (인수인계 line 128). 출력 변화 없으면 그대로, 있으면 함께 동기 수정.
   - 기존 회귀 fixture `pilot/tests/fixtures/v0.1.0-baseline/analyze/expected/scope/python-sample.md` 의 본문이 본 변경 후에도 동일하게 산출 가능한지 확인 (spec line 46 — byte-diff 0 보장).

## 검증 방법

- analyze SKILL.md 5-1 ↔ 5-1.5 ↔ 5-2 H4 순서 유지
- 5-1.5 본문이 spec line 13-29 의 4 요소 (트리거 / 본문 구성 / idempotency / 사용자 수동 보존) 모두 포함
- 본문 추출 우선순위 3 단 명시 (inventory.md → index.md → 빈 표 + INFO)
- wizard 인용 주입 SSOT 1 줄 포함 (인수인계 line 123 직접 소비)
- 예외 4건 (MANIFEST 진입파일 / config 빈 표 / inventory.md / scope 헤더 prefix) 모두 포함
- A2 runtime fallback wording 답습 (features/01·02 의 wording 동일 패턴)
- 기존 회귀 fixture `analyze/expected/scope/python-sample.md` byte-diff 0 보장 (변경 후 cycle 재실행 시 동일 산출 — 자체 검증은 #00 의 0c 회귀 검증과 묶어 일괄)
- `pilot/docs/getting-started.md` analyze 출력 코드블록 drift 점검 후 필요 시 동기 수정 (인수인계 line 128)

## 주의사항

- **체크박스 갱신 권한 분리** (인수인계 line 99 #03) — 본 plan 의 generator 가 `project.md` 의 `## 목표` 의 #07 항목을 self-mark 하지 않는다. evaluator wrapper step 5 가 단독 권한자.
- **5-1.5 wording 정합** — 본문 wording 이 features/01·02 의 default 격하 blockquote 패턴 + A2 runtime fallback 절차 (인수인계 line 92·93·95) 답습. "stderr WARN 1 줄" / "abort 하지 않는다" / "fallback 사용" 표현 통일.
- **scope 파일 자동 생성의 사용자 수동 작성 보존 원칙** — 5-1.5 가 새로 만든 scope 파일도 사용자가 수동 추가·교정 가능. idempotency 룰이 그것을 보장 — generator 가 "자동 생성 = 매번 덮어쓰기" 로 잘못 구현하지 않도록 본문 wording 명확히 ("두 번째 호출 시 새로 만들지 않음" + "사용자 수동 추가 행 보존").
- **wizard 인용 주입 SSOT** (인수인계 line 123) — `/pilot:init` wizard 가 작성한 `## learn 언어 패턴` 표 행이 inventory.md 산출 형식 ↔ scope 헤더 ↔ project.md `## 관련 파일` 표의 SSOT 라는 흐름. 본 #07 의 5-1.5 본문이 이 흐름의 중간 노드 (scope 헤더) 를 명시화.
- **`pilot/docs/getting-started.md` drift 점검** (인수인계 line 128) — 본 PR 머지 시 analyze Step 4 출력 코드블록 1회 점검. scope 파일 자동 생성 거동 추가가 출력 형식을 깨는 경우 본 PR 안에 동기 수정 포함.
- **회귀 fixture 변경 금지** — spec line 46 — NS #5 검증 = 거동 동일 명문화. `pilot/tests/fixtures/v0.1.0-baseline/analyze/expected/` 의 어떤 파일도 본 PR 에서 수정 안 함. byte-diff 0 검증으로 본 변경이 회귀 영향 없음을 확인.

## 교차 의존

- **features/00 (회귀 fixture)** — 본 PR 머지 후 회귀 검증 시 byte-diff 0 확인. 변경 fixture 없음.
- **features/01 (learn 언어 패턴)** — 5-1.5 의 본문 추출 1순위 = inventory.md (learn 산출). #01 의 wizard 표 행 인용 주입 SSOT (인수인계 line 123) 가 본 #07 의 핵심 흐름.
- **features/02 (analyze scope 카테고리)** — 5-1.5 의 본문 추출 헤더 = config.md `## scope 카테고리` 의 `scope 헤더` 컬럼. #02 의 default 매핑 (Routes/Models/Services → Endpoints/Models/Services) 이 5-1.5 의 default fallback 분기. 본 #07 변경이 #02 의 5-2 직전 단계를 추가하는 형태.
- **features/03 (project.md H3 동적 생성)** — 5-1.5 (scope 파일 생성) → 5-2 (project.md 표 갱신) 흐름에서 #03 의 H3 SSOT (project skill 1회 생성 + analyze 매번 갱신) 가 정합. 본 #07 변경이 #03 흐름에 영향 없음.
- **features/04 (doctor config 검증)** — 5-1.5 예외 4건 中 "scope 헤더 prefix 위반 → doctor 사전 차단" 이 #04 의 검증 함수와 정합.
- **features/06 (#06)** — 동일 PR 묶음. learn Phase 5 의 H2 정확 매칭 (#06) 과 본 #07 의 scope 헤더 매칭이 둘 다 헤더 정확 매칭 강화 흐름.
- **features/08 (#08)** — 동일 PR 묶음. 독립 변경.
- **features/13 (init wizard)** — 인수인계 line 123 — 본 plan 의 5-1.5 본문에 wizard 인용 주입 SSOT 1줄 명시로 소비.
- **features/14 (#14)** — 인수인계 line 128 — getting-started.md drift 점검. 본 plan step 4 에 명시.
- **인수인계 line 31·93·95·123·128** — 본 plan step 1~4 에서 5 건 모두 소비. evaluator wrapper step 2 가 `project.md` 의 5 행 `[x]` 처리.
