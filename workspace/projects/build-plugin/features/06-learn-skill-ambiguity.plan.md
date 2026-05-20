# #06 learn SKILL.md 모호함 해소 — Implementation Plan

> source: features/06-learn-skill-ambiguity.md · 직전 plan 협상 (옵션 C — plan 만 저장, generator 호출은 별도)
> mode: standard (tdd: false)
> planner_at: 2026-05-20

## 사전 결정 사항 (Q1~Q3 + 공통 5건)

사용자가 모든 권고를 채택 (a 옵션 일괄). v0.3.0 LOW priority 3 features (#06·#07·#08) SKILL.md wording 명확화 turn 안에 결정.

| Q | 결정 | 근거 |
| --- | --- | --- |
| 공통-1 코드 변경 여부 | **SKILL.md 본문만**. doctor·script·fixture 변경 없음 | NS #5 cycle 검증 — LLM 사실상 거동 中. 명문화만. |
| 공통-2 PR 단위 | #06·#07·#08 **일괄 단일 PR** (`docs: pilot SKILL.md wording 명확화 #06·#07·#08`) | LOW priority + 코드 변경 없음 + 회귀 영향 없음 |
| 공통-3 version bump | v0.3.0 합본 PR 끝 일괄. 본 PR 단독 patch bump 안 함 | #16 Q9 답습 |
| 공통-4 회귀 fixture | **변경 없음**. `expected/` byte-diff 0 보장 | NS #5 검증 = 거동 동일 |
| 공통-5 getting-started.md drift | 본 PR 머지 시 `pilot/docs/getting-started.md` 의 Phase 1·5 출력 코드블록 점검 후 동기 수정 | 인수인계 line 128 (#14 후속) |
| Q1 Phase 1 fallback 위치 | learn SKILL.md:78-85 의 자동 도출 규칙 list 에 **sub-bullet 추가** | 도메인 도출은 list 형식 (표 부재) — spec line 19 의 "표 행 추가" 는 실제 list 항목 추가로 해석 |
| Q2 Phase 5 H2 정확 매칭 위치 | learn SKILL.md:292-301 의 형태 detect 표 직후 / step 4 직전 **blockquote 1 줄 + 정규식 인용** | spec line 22-23 wording 그대로 |
| Q3 A2 fallback 형태 | Phase 1: 부모 → 2단계 상위 → 사용자 질의 (abort 안 함). Phase 5: H2 매칭 실패 → 자동 섹션 생성 (기존 룰 유지) | spec line 25 |

## 인수인계 항목 소비 매핑 (project.md 미처리 항목)

| line | 항목 | 본 plan 활용 |
| --- | --- | --- |
| 31 | features/04 A2 runtime fallback — SKILL.md 본문 변경 (from #04) | Phase 1 부모 폴더명 fallback 도 A2 패턴 (사용자 질의 abort 안 함) 명시. step 1. |
| 109 | `_parse_md_tables_in_section` 코드블록 펜스 추적 보강 (from #10) | Phase 5 H2 정확 매칭이 동일 정책 (코드블록 안 string 무시) — spec 예외 케이스 명시. step 2. |
| 128 | #14 getting-started.md drift (from #14) | step 3 검증 방법에 1줄 — 본 PR 머지 시 getting-started.md Phase 1·5 출력 코드블록 점검. |

## 범위

### 포함

- learn SKILL.md Phase 1 도메인 도출 규칙에 **일반 진입파일 fallback** 1 항목 추가 (부모 폴더명 → 2단계 상위 → 사용자 질의)
- learn SKILL.md Phase 5 step 2 의 `## 도메인 분류` 형태 detect 표 직후 **H2 정확 매칭 blockquote** 1 단락 추가 (정규식 `^##\s+도메인\s*분류\s*$` 인용)
- 예외 케이스 — 절대경로 정규화 / 비ASCII sanitize / 코드블록 안 string 무시 본문 명시

### 제외 (v0.3.0 범위 외 또는 v0.4.0 이월)

- `--domain NAME` 옵션 v2 (features/01 OQ #4 이월, spec line 32)
- 회귀 픽스처 갱신 (NS #5 검증 = 거동 동일)
- 단위 테스트 신설 (spec line 39 — 기존 `parse_manifest_domain_files` 테스트로 충분)
- doctor·script 변경

## 변경 파일

### 수정

- [x] `pilot/skills/learn/SKILL.md`
  - Phase 1 (line 76-84) — 자동 도출 규칙 list 에 일반 진입파일 fallback sub-bullet 추가
  - Phase 5 (line 292-313 부근) — `## 도메인 분류` 형태 detect 표 직후 H2 정확 매칭 blockquote 1 단락 추가

### 신설 / 삭제

- 없음

## 단계별 구현 순서

1. **Phase 1 fallback sub-bullet 추가** (`pilot/skills/learn/SKILL.md` line 78-84)
   - 기존 자동 도출 규칙 (파일 suffix 제거 / 폴더명 / 폴더 내 동명 파일) 직후에 신규 bullet 추가:
     ```markdown
        - 파일명이 일반 진입점 (`main.*`·`app.*`·`server.*`·`index.*`·`__main__.py` 등 — 도메인 식별자·역할 suffix 없음) → **부모 폴더명을 도메인명으로 채택**. 부모 폴더도 일반 (`src/`·`app/`·`lib/`·`source/`) 이면 **2단계 상위 폴더명** 또는 **레포 root 디렉터리명** fallback. 모두 일반이면 사용자에게 도메인명 입력 prompt (A2 패턴 — abort 안 함).
     ```
   - 도메인명 sanitize 룰 1 줄 추가 (영숫자·하이픈 외 제거 + 소문자화. 정규화 결과 공집합이면 사용자 질의).
   - 절대경로 정규화 1 줄 (절대 → 상대 후 부모 추출. 정규화 실패 시 사용자 질의).

2. **Phase 5 H2 정확 매칭 blockquote 추가** (`pilot/skills/learn/SKILL.md` line 292-301 직후)
   - 기존 "기존 도메인 분류 구조 detect" 표 직후 (line 301 의 "파싱은 best-effort" blockquote 직전) 에 다음 blockquote 신규 삽입:
     ```markdown
     > **H2 헤더 정확 매칭 강제** — `## 도메인 분류` 섹션 detect 는 `^##\s+도메인\s*분류\s*$` 정규식 정확 매칭. 본문 prose 의 동일 string 등장 (가이드 주석·코드블록·표 본문 안 `## 도메인 분류` 인용) 은 무시한다. `orchestrate-load.py:parse_manifest_domain_files` 의 자동 파싱 호환을 위해 필수.
     >
     > **코드블록 안 `## 도메인 분류` 줄 무시** — 펜스 (` ```` ``` ```` `) 추적해 코드블록 안 줄은 H2 detect 대상에서 제외 (`_parse_md_tables_in_section` 헬퍼의 코드블록 추적 보강과 정합 — integrity.py:807·811-820).
     ```

3. **검증 방법 (Generator 자체 sanity)**
   - `pilot/skills/learn/SKILL.md` 두 변경 위치에서 markdown 구조 깨짐 없는지 확인 (Phase 1 list 형식 유지, Phase 5 blockquote 형식 유지).
   - `pilot/docs/getting-started.md` 의 Phase 1·5 관련 출력 코드블록이 본 wording 변경으로 drift 발생하는지 점검 (인수인계 line 128). 출력 변화 없으면 그대로, 있으면 함께 동기 수정.
   - 기존 회귀 fixture `pilot/tests/fixtures/v0.1.0-baseline/learn/expected/` 의 `python-sample` 도메인 도출 결과가 변경 없는지 확인 (`_input/python-sample/main.py` → 부모 폴더명 fallback 적용 시 도메인 = `python-sample` 동일).

## 검증 방법

- learn SKILL.md 본문 2곳 wording 적용 확인 (Phase 1 sub-bullet 추가 + Phase 5 blockquote 추가)
- `parse_manifest_domain_files` 기존 테스트 (`pilot/tests/tools/test_orchestrate_load.py`) 재실행 시 통과 (spec line 39 — 본 변경과 정합)
- 회귀 fixture `python-sample` 도메인 도출 결과 byte-diff 0 (`diff.sh` 자체 실행은 별도 — #00 의 5번 회귀 검증 대기 中)
- `pilot/docs/getting-started.md` drift 점검 후 필요 시 동기 수정 (인수인계 line 128)

## 주의사항

- **체크박스 갱신 권한 분리** (인수인계 line 99 #03) — 본 plan 의 generator 가 `project.md` 의 `## 목표` 의 #06 항목을 self-mark 하지 않는다. evaluator wrapper step 5 가 단독 권한자.
- **A2 runtime fallback 일관성** (인수인계 line 31 #04) — 사용자 질의 prompt 도 abort 가 아니라 fallback 단계의 마지막 옵션. WARN 또는 INFO 출력 형식은 기존 #01·#02 패턴 답습.
- **A2 패턴 wording 통일** — Phase 1 부모 폴더명 fallback bullet 안의 "abort 안 함" wording 은 features/01·02 의 동일 룰 wording 답습 (`fallback 사용`·`abort 하지 않는다`).
- **MANIFEST 자유 형식 원칙 보존** (learn SKILL.md:289) — H2 정확 매칭 blockquote 가 자유 형식 원칙과 충돌하지 않도록 wording 주의. "기존 정의가 있으면 그에 따르고, 정의가 없을 때만 새로 만든다" 는 본 변경이 강화하는 룰 — 본문 prose 안 string 을 "정의 있음" 으로 오판하지 않도록 H2 헤더 정확 매칭 강제.
- **`pilot/docs/getting-started.md` drift 점검** (인수인계 line 128) — 본 PR 머지 시 Phase 1 의 도메인 도출 출력 + Phase 5 의 MANIFEST 갱신 출력 코드블록을 1회 점검. 변화 없으면 그대로 유지, 있으면 본 PR 안에 동기 수정 포함.
- **회귀 fixture 변경 금지** — NS #5 검증 = 거동 동일 명문화. `pilot/tests/fixtures/v0.1.0-baseline/learn/expected/` 의 어떤 파일도 본 PR 에서 수정 안 함. byte-diff 0 검증 시 본 변경이 회귀 영향 없음을 확인.

## 교차 의존

- **features/00 (회귀 fixture)** — 본 PR 머지 후 회귀 검증 시 byte-diff 0 확인 (#00 의 5번 회귀 검증 — 0c PR 와 묶어 일괄, 본 PR 단독 검증 보류). 변경 fixture 없음.
- **features/07 (#07)** — 동일 PR 묶음. analyze SKILL.md 5-1.5 자동 생성이 본 #06 의 Phase 5 H2 매칭 변경과 정합 (둘 다 MANIFEST/scope 헤더 정확 매칭 강화).
- **features/08 (#08)** — 동일 PR 묶음. 독립 변경.
- **features/09·#10** — Phase 5 의 `## 외부 도메인 reference` 섹션 detect 도 동일 H2 정확 매칭 룰 적용 대상 (이미 #10 PR-1 에서 sub-string 매칭 + 코드블록 추적 보강 완료 — integrity.py:807·811-820, 인수인계 line 109·115). 본 #06 변경이 명문화 1 회 추가하는 것만으로 정합.
- **features/14 (#14)** — 인수인계 line 128 — getting-started.md drift 점검. 본 plan step 3 에 명시.
- **인수인계 line 31·109·128** — 본 plan step 1~3 에서 3 건 모두 소비. evaluator wrapper step 2 가 `project.md` 의 3 행 `[x]` 처리.
