# Planner — build-plugin

구현 대상 기능을 분석하고, Generator가 실행 가능한 단계별 계획을 수립한다.

> **⚠️ 이 파일은 `@pilot-planner` subagent 정의가 아닙니다.** 실제 subagent 는 플러그인의 [`${CLAUDE_PLUGIN_ROOT}/agents/pilot-planner.md`](${CLAUDE_PLUGIN_ROOT}/agents/pilot-planner.md) 에 등록돼 있고, wrapper 가 Read 로 **이 파일을 컨텍스트 문서로** 불러들입니다. 이 파일 편집은 다음 `@pilot-planner` 호출에 반영됩니다 (단 `<!-- [analyze-managed] -->` 섹션은 다음 `--regen-agents` 시 덮어쓰임).
>
> 스캐폴딩·analyze-managed·TDD 상세: [agents-scaffold-notes.md](${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/projects/agents-scaffold-notes.md) 참조.

<!-- [analyze-managed] -->
## 기능별 사전 확인 사항

### #00 회귀 골든 픽스처 (features/00-regression-fixture.md)

- 조건: `pilot/tests/fixtures/v0.1.0-baseline/` 미존재. v0.1.0 의 `/pilot:learn` `/pilot:project` `/pilot:analyze` 산출물 + #04 의 PASS/ERROR 케이스 fixture 캡처 가능.
- 트리거: 수동 1 회 캡처 + Next Steps 5번에서 `diff.sh` 재실행.
- 기대결과: config 비어있을 때 v1 출력이 v0.1.0 capture 와 diff 0 (#01·#02·#04 backward-compat 1 차 검증). #03 default H3 도 v0.1.0 의 하드코드 H3 와 동일.

**관련 파일 범위**:
- 신설: `pilot/tests/fixtures/v0.1.0-baseline/` (전체 트리, 1 언어 input)
- 참조: `pilot/skills/{learn,analyze,project}/SKILL.md` 의 default 섹션 + `example/project.md`

### #01 learn 언어 패턴 외부화 (features/01-learn-language-pattern-externalize.md)

- 조건: `workspace/context/config.md` 신규 섹션 `## learn 언어 패턴` 정의 가능, SKILL.md 본문의 두 표 default 섹션 격하 + "config 비면 사용" 주석.
- 트리거: `/pilot:learn` 호출 시 진입 파일 확장자에서 언어 추론 → config.md lookup → 매칭 없으면 default.
- 기대결과: config 비면 0.1.0 동일 거동 (회귀 픽스처 검증), 사용자 override 시 즉시 반영.

**관련 파일 범위**:
- 변경: `pilot/skills/learn/SKILL.md` (Phase 2 본문 lookup 추가)
- 변경: `workspace/context/config.md` (신규 섹션, 표 1·2)
- 회귀 픽스처: `pilot/tests/fixtures/v0.1.0-baseline/learn/`

### #02 analyze scope 카테고리 외부화 (features/02-analyze-scope-category-externalize.md)

- 조건: config.md 신규 섹션 `## scope 카테고리` 정의 가능, SKILL.md default (Routes/Models/Services 매핑) 격하.
- 트리거: `/pilot:analyze` 또는 `/pilot:create-feature` 의 5-2 진입.
- 기대결과: scope/{domain}.md 의 매칭 H2 표를 추출해 project.md `## 관련 파일` 안 H3 표로 기입. config 빈 행 또는 MANIFEST 표 부재 시 해당 표만 skip + INFO 1 줄, `analyzed:true` 정상 게이트.

**관련 파일 범위**:
- 변경: `pilot/skills/analyze/SKILL.md` (5-2 본문 lookup 추가, MANIFEST 부재 처리)
- 변경: `pilot/skills/create-feature/SKILL.md` (5-2 인용 호출 — 동일 거동 자동 적용)
- 변경: `workspace/context/config.md` (신규 섹션)

### #03 project.md H3 동적 생성 + SSOT (features/03-project-md-h3-dynamic.md)

- 조건: example/project.md 의 `## 관련 파일` H2 본문이 가이드 주석만 갖고 H3 비어있음.
- 트리거: `/pilot:project {PROJECT}` 신규 폴더 생성 시점 (template 복사 직후 1 회 가공).
- 기대결과: project skill 이 config 의 `project.md 대상 H3` 컬럼을 보고 H3 + 빈 표 채움. 재실행 시 기존 H3 보존. 사용자 H3 삭제 후 재실행 시 복구 안 함 (사용자 의도).

**관련 파일 범위**:
- 변경: `pilot/skills/project/SKILL.md` (template 복사 후 1 회 가공 단계 추가)
- 변경: `pilot/skills/context/lifecycle/projects/example/project.md` (`## 관련 파일` H3 + 표 제거, H2 + 가이드 주석만 유지)

### #04 doctor config 정합성 검증 (features/04-doctor-config-validation.md)

- 조건: `pilot/tools/doctor/integrity.py` 에 신규 검사 함수 추가.
- 트리거: `/pilot:doctor` 또는 `python3 .../doctor.py workspace`.
- 기대결과: 신규 섹션 존재 시 스키마 검증 (컬럼 수·헤더 화이트리스트·`## ` prefix). 부재 시 INFO 1 줄. 위반 시 ERROR + 수정 안내.

**관련 파일 범위**:
- 변경: `pilot/tools/doctor/integrity.py` (신규 검증 함수)
- 신규: `pilot/tests/tools/test_doctor_integrity.py` (`test_doctor_slack.py` 패턴 답습 — unittest + importlib.util)
- 회귀 픽스처: `pilot/tests/fixtures/v0.1.0-baseline/config/{pass-empty,pass-valid,error-*}` (test 와 fixture 공유)

> `workspace/context/scope/pilot.md` · `workspace/context/rules/pilot.md` 부재 — 본 프로젝트는 사용자 커스텀 layer 미작성. features/ 의 file:line 인용을 1 차 근거로 활용한다 (예: `pilot/skills/learn/SKILL.md:90-111`).

---

<!-- [analyze-managed] 영역 끝 — 아래는 사용자 수동 영역 (다음 `/pilot:analyze --regen-agents` 시 보존) -->

## v0.3.0 implementation 계획 (HIGH 4 건)

> 작성일: 2026-04-30. 출처: V1-Full nimda Rails monolith dogfooding 결과 (`.focus.md` SSOT). 대상 features: #09·#10·#11·#12. focus.md 권고 진행 순서 (#09+#10 묶음 → #11 → #12) 따름.

### A. 의존 그래프 + 실행 순서

```
                ┌─────────────────────────────────────────────┐
                │  #09 cross-domain 처리 가이드 (main milestone) │
                │  - learn Phase 2 외부 reference detect          │
                │  - create-feature/analyze cross-domain detect    │
                │  - INFO 1줄 후속 learn 추천                    │
                │  - A2 runtime fallback                       │
                └────┬────────────────────────────────────┬────┘
                     │ 산출 메커니즘 = MANIFEST.md 외부    │
                     │ 도메인 섹션 (강한 의존)             │
                     ▼                                     │
                ┌─────────────────────────────────────┐   │
                │  #10 MANIFEST 외부 도메인 섹션 자동  │   │
                │  - 표 스키마 3 컬럼                  │   │
                │  - Ruby Module::Class 추정 알고리즘  │   │
                │  - idempotency (학습 후 행 제거)     │   │
                └────┬────────────────────────────────┘   │
                     │                                     │
       ┌─────────────┴─────────────────┐                  │
       │                               │                  │
       ▼                               ▼                  ▼
  ┌──────────────┐             ┌──────────────────────────────┐
  │ #11 Open Q   │             │ #12 cross-domain transaction  │
  │ 템플릿       │             │ 패턴 가이드 (MED)             │
  │ - 4 카테고리 │             │ - 다중 DB 섹션 확장           │
  │ - 빈 = (없음)│             │ - transaction nesting detect  │
  │ - doctor INFO│             │ - 4 컬럼 표                   │
  └──────────────┘             └──────────────────────────────┘
   (독립 — analyze /             (의존: #09 cross-domain detect +
    create-feature SKILL.md)       #10 MANIFEST 외부 도메인 lookup)
```

**병합 PR 단위 권고:**

- **PR-1 (#09 + #10 묶음)**: 강한 의존성. 분리 시 #10 단독으로는 `/pilot:learn` 의 외부 reference 추출이 의미가 없고, #09 단독으로는 MANIFEST 갱신 메커니즘 부재. 한 PR 으로 처리하는 것이 backward-compat 검증·회귀 픽스처 갱신 단위 효율적.
- **PR-2 (#11 단독)**: analyze / create-feature SKILL.md + features template 추가만. PR-1 와 독립 (단 PR-1 의 cross-domain detect 결과가 (b) 카테고리에 자동 입력되는 통합점은 PR-1 머지 후 wiring).
- **PR-3 (#12 단독)**: learn Phase 3·4 변경 + 도메인 산출 template + doctor 검증. PR-1 의 inventory 시 외부 클래스 reference 추출 결과가 transaction 패턴 detect 의 입력. PR-1 머지 후 진행 권장.

### B. feature 별 단계 분해

#### #09 cross-domain 처리 가이드 (PR-1 일부)

**S1. learn Phase 2 외부 도메인 reference 추출 절차 명시 (SKILL.md 본문)**

- `pilot/skills/learn/SKILL.md` line 81-127 (Phase 2) 본문에 신규 sub-step 추가:
  - "의존성 추적 시 같은 도메인 내부 클래스 ↔ 외부 클래스 구분 룰":
    - 본 도메인 namespace prefix (예: 진입점이 `app/services/wms/` 면 `Wms::*`) 매칭 → 내부.
    - 그 외 namespace 첫 segment (`Schoice::*`, `Sinsang::*`, `ApplicationRecord` 등) → 외부 후보.
  - "외부 후보 중 standard library / framework 제외" — config 의 ignore 패턴 (default: `ActiveRecord::Base`, `ApplicationRecord`, `String`, `Hash`, `Time`, `Date`, `BigDecimal` ... 등) lookup. config 부재 시 hardcoded default fallback (10~20 항목).
  - 제외 후 남는 외부 클래스 목록을 메모리에 누적 (Phase 5 에서 MANIFEST 갱신 시 사용).
- A2 runtime fallback: 외부 reference 추출 알고리즘 실패 (예: namespace 추출 불가) → 해당 클래스를 단순 무시 + WARN 1 줄, 본 도메인 학습은 정상 진행.

**S2. create-feature SKILL.md cross-domain detect 절차**

- `pilot/skills/create-feature/SKILL.md` 의 "3. features/NN-{slug}.md 작성" (line 62-92) 와 "4. project.md 및 prompts/* 자동 갱신" (line 94-110) 사이에 신규 sub-step 추가:
  - "feature spec 작성 후 산출물 lookup 시 답할 수 없는 영역 발견" 룰:
    - 사용자 prompt 에 등장한 클래스/도메인 키워드를 MANIFEST.md `## 도메인 분류` 표 + `## 외부 도메인 reference` 표 양쪽 lookup.
    - "외부 도메인 reference" 표 매칭 → INFO 1 줄: `[INFO] 이 feature 는 {외부 도메인} 의존성 — 먼저 \`/pilot:learn {외부 도메인}\` 권장`
    - 매칭 없음 + 산출물 cover 안 됨 → #11 의 Open Questions (b) 카테고리에 자동 행 추가.
- A2 runtime fallback: lookup 실패 시 → spec 진행, INFO 안 띄움, Open Questions (b) 만 자동 추가.

**S3. analyze SKILL.md 5-2 cross-domain detect 절차**

- `pilot/skills/analyze/SKILL.md` line 209-246 (5-2) 의 "갱신 규칙" 직후 신규 sub-step 추가:
  - features/ 의 features 키워드 ↔ scope/{domain}.md 매칭 시도 시 cover 안 되는 클래스 reference detect.
  - MANIFEST `## 외부 도메인 reference` lookup → 매칭되면 INFO 1 줄 + Open Questions (b) 자동 추가.

**S4. learn Phase 5 MANIFEST 갱신 (#10 와 통합)** — 자세한 단계는 #10 의 단계로 위임.

**관련 파일 (#09)**

- 변경: `pilot/skills/learn/SKILL.md` (Phase 2)
- 변경: `pilot/skills/create-feature/SKILL.md` (3 ↔ 4 사이 신규)
- 변경: `pilot/skills/analyze/SKILL.md` (5-2 갱신 규칙 직후)
- 변경: `pilot/tools/doctor/integrity.py` (외부 도메인 lookup 시 stale row INFO; #10 와 공유)

#### #10 MANIFEST 외부 도메인 섹션 자동 추가 (PR-1 일부)

**S1. MANIFEST.md template 에 placeholder 추가**

- `pilot/skills/context/lifecycle/setup/templates/MANIFEST.md.template` 에 `## 도메인 분류` 직후 다음 placeholder 추가 (주석으로 처리 — 빈 섹션 강제 안 함, 첫 cross-domain reference detect 시 자동 작성):
  ```markdown
  <!-- 외부 도메인 reference 섹션 placeholder. 첫 `/pilot:learn` 호출 시 외부 클래스 reference 가
       발견되면 자동으로 `## 외부 도메인 reference (learn 미완료)` H2 + 3 컬럼 표가 생성된다. -->
  ```
- `pilot/skills/init/SKILL.md` 본문에 init 시 MANIFEST.md 가 placeholder 만 갖는다는 점 1 줄 보강 (line 33 의 표 직후).

**S2. learn Phase 5 MANIFEST 갱신 시 외부 도메인 섹션 작성 절차**

- `pilot/skills/learn/SKILL.md` line 237-292 (Phase 5) 의 step 4 (orchestrate-load 와 호환성) 와 step 5 (doctor 실행) 사이에 신규 step "4-bis. 외부 도메인 reference 섹션 갱신" 삽입:
  - Phase 2 에서 누적된 외부 클래스 목록을 추정 도메인별 grouping (Ruby `Module::Class` namespace 첫 segment 소문자화).
  - 추정 도메인이 이미 `## 도메인 분류` 표에 등록된 도메인이면 제외 (이미 학습됨).
  - 추정 도메인 별로 추천 경로 탐색: `app/{models,services,controllers}/{추정 도메인}/` 패턴 Glob (사용자 코드베이스 root 기준). 존재하면 그 경로 추천, 없으면 "(경로 자동 추정 실패 — 사용자 직접 지정)".
  - MANIFEST 의 `## 외부 도메인 reference (learn 미완료)` 섹션이 이미 존재하면 표에 행 갱신 (idempotency: 같은 추정 도메인 행이 있으면 클래스 목록 / 갯수 갱신, 사용자 수동 추가 행은 보존). 없으면 섹션 + 표 신규 생성.
  - 자동 추가 행 끝에 ` (auto)` 마커 (선택 — 사용자 수동 추가 행과 구분).
- A2 runtime fallback: 추정 도메인 추출 실패 시 → 섹션 작성 자체 skip + WARN 1 줄 (`[WARN] 외부 도메인 reference 추출 실패 — 수동 관리 권장`). learn 본 작업은 정상 종료.

**S3. learn 완료 후 idempotency — 후속 learn 시 stale row 제거**

- `pilot/skills/learn/SKILL.md` Phase 5 step 4-bis 직후에 추가:
  - 본 learn 의 `{domain}` 이 MANIFEST `## 외부 도메인 reference` 표의 행으로 존재하면 → 그 행 제거 (이미 학습됨 표시).

**S4. doctor schema 검증 (`integrity.py`)**

- `check_workspace_external_domain_section(manifest_path: Path) -> list[Result]` 신규 함수 (integrity.py 의 기존 `check_workspace_config_sections` 패턴 답습):
  - `## 외부 도메인 reference` H2 (정확 일치 또는 `(learn 미완료)` 등 sub-string 허용 — 사용자 편집 친화) lookup.
  - 부재 → INFO 1 줄: `## 외부 도메인 reference 미정의 — 첫 cross-domain reference detect 시 자동 작성`. (배포 직후 backward-compat: 모든 사용자가 부재 상태 → INFO 만 발화, ERROR 없음.)
  - 존재 → `_parse_md_tables_in_section` 으로 표 파싱:
    - 컬럼 수 검증: 정확히 3 컬럼 (`추정 도메인`, `클래스 (개수)`, `추천 후속 학습`).
    - 헤더 정확 일치 검증.
    - 위반 시 ERROR + 수정 안내.
  - 추가 검증: 표 행의 추정 도메인이 `## 도메인 분류` 표에 이미 있으면 INFO 1 줄 (`[INFO] '{domain}' 은 이미 학습됨 — 외부 도메인 표 행 제거 권장`).
- `run_integrity_check` (integrity.py:1322) 에 위 함수 호출 1 줄 추가.

**관련 파일 (#10)**

- 변경: `pilot/skills/learn/SKILL.md` (Phase 5 step 4-bis + step 4-ter idempotency)
- 변경: `pilot/skills/init/SKILL.md` (1 줄 보강)
- 변경: `pilot/skills/context/lifecycle/setup/templates/MANIFEST.md.template`
- 변경: `pilot/tools/doctor/integrity.py` (신규 함수 + run_integrity_check 등록)

#### #11 feature spec Open Questions 템플릿 (PR-2)

**S1. create-feature SKILL.md 템플릿에 Open Questions 4 카테고리 강제**

- `pilot/skills/create-feature/SKILL.md` line 62-92 의 "3. features/NN-{slug}.md 작성" 템플릿에 `## 예외 케이스` 직후 다음 추가:
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
- 본문에 "빈 카테고리 = '(없음)' 표시 강제. 카테고리 자체 생략 안 함" 룰 명시.

**S2. create-feature SKILL.md 자동 detect 절차 (#09 의 S2 와 통합)**

- "산출물 lookup 시 답할 수 없는 영역 발견 → 카테고리 분류" 알고리즘:
  - cross-domain 의존성 (MANIFEST 외부 도메인 매칭) → (b)
  - scope/{domain}.md 의 같은 도메인이지만 line-by-line detail 부족 → (a)
  - 외부 시스템 (예: API spec, 다른 회사 시스템) → (c)
  - PM/PO 결정 영역 (코드 외) → (d)
- 사용자 prompt 에 명시적 키워드가 있는 경우 우선 카테고리 분류, 모호하면 (작성자 직접 채움) placeholder 만.
- A2 runtime fallback: detect 알고리즘 실패 → 4 카테고리 헤더 + "(없음)" / "(작성자 직접 채움)" placeholder 만 작성, abort 안 함.

**S3. analyze SKILL.md 5-2 의 features/ 갱신 시 Open Questions 보존**

- `pilot/skills/analyze/SKILL.md` line 209-246 (5-2) 의 "갱신 규칙" 마지막에 추가:
  - "features/ 가 이미 존재하면 기존 Open Questions 섹션 보존, 자동 detect 결과는 적절한 카테고리에 행 추가만 (기존 (없음) 행은 그대로)."

**S4. doctor schema 검증**

- `check_features_open_questions(features_dir: Path) -> list[Result]` 신규 함수 (integrity.py):
  - `workspace/projects/*/features/NN-*.md` 의 각 파일에 `## Open Questions` H2 부재 → INFO 1 줄 (`[INFO] features/{path} 에 Open Questions 섹션 부재 — 추측 회피 위해 권장`).
  - 존재 → 4 카테고리 H3 (`### (a) 같은 도메인 추가 read 필요`, `### (b) cross-domain 산출물 부재`, `### (c) 외부 시스템 spec 부재`, `### (d) 비즈니스 결정 영역`) 모두 존재 검증. 일부 누락 → INFO (ERROR 아님 — 사용자 수동 작성 friendly).
  - 4 카테고리 모두 빈 (`- (없음)` 만) → PASS (정상 단순 feature).
- `check_project` (integrity.py:458) 에서 features 디렉터리 순회 시 호출.

**S5. example template 부재 — 신규 추가 여부 결정**

- `pilot/skills/context/lifecycle/projects/example/features/` 폴더 부재 (확인됨). 신규 생성 가능하나 init / project skill 이 features template 을 사용하지 않음 (create-feature 가 직접 inline 템플릿 사용). 본 작업에서는 example/features template 신규 생성 **하지 않음** — create-feature SKILL.md 의 inline 템플릿 변경 (S1) 만으로 충분. 재고 시 추가 가능.

**관련 파일 (#11)**

- 변경: `pilot/skills/create-feature/SKILL.md` (line 62-92 템플릿 + S2 자동 detect)
- 변경: `pilot/skills/analyze/SKILL.md` (5-2 갱신 규칙 직후)
- 변경: `pilot/tools/doctor/integrity.py` (신규 함수 + check_project 등록)

#### #12 cross-domain transaction 패턴 가이드 (PR-3)

**S1. learn Phase 3 transaction 패턴 detect 절차**

- `pilot/skills/learn/SKILL.md` line 129-179 (Phase 3) 의 "Targeted Read 시 Grep 패턴" 표에 신규 행 추가:
  - 추출 대상: `transaction nesting (cross-domain)`
  - Grep 패턴 (Ruby 예): `\.transaction\s+do\s*$|ActiveRecord::Base\.transaction|ApplicationRecord\w+\.transaction`
  - 매칭 시 ±20 줄 추가 Read (transaction block 안 외부 클래스 호출 추출).
- "각 파일에서 추출" sub-list 의 "business rule" 직후 신규 항목:
  - **cross-domain transaction nesting** — outer / inner transaction 의 receiver 가 다른 도메인 namespace 면 nesting detect. inner 안 외부 클래스 메서드 호출 (`update`/`destroy`/`find`/`create`) 추출 → `read`/`write`/`destroy`/`create` type 매핑.

**S2. learn Phase 4 산출물 생성 시 "Cross-domain Transaction Contracts" sub-section**

- `pilot/skills/learn/SKILL.md` line 181-235 (Phase 4) 의 step 1 (구조 결정) 직후 / step 6 (batch Write) 직전에 신규 sub-step "다중 DB 섹션 + Cross-domain Transaction Contracts sub-section 작성":
  - cross-domain transaction nesting 0 → sub-section 자체 추가 안 함.
  - >= 1 → `{domain}/index.md` (또는 단일 파일 도메인이면 `{domain}.md`) 의 "다중 DB" 섹션 직후 (다중 DB 섹션 부재 시 신규 H2 `## 다중 DB` + sub-section 한 번에 추가):
    ```markdown
    ## 다중 DB

    ### Cross-domain Transaction Contracts

    | 본 도메인 entry | 외부 도메인 영향 | 변경 type | file:line |
    | --- | --- | --- | --- |
    | Wms::TaskService#cancel_after_completion | Schoice::SsmSPackageSheet status / SsmSOrderSheetPackageInvoice destroy | write·destroy | task_service.rb:44-67 |
    ```
- A2 runtime fallback: detect 알고리즘 실패 → sub-section 헤더 + "(자동 detect 실패 — 수동 작성 권장)" placeholder.
- idempotency: 두 번째 learn 호출 시 자동 detect 행 갱신, 사용자 수동 추가 행 보존 (`(auto)` 마커 활용).

**S3. doctor schema 검증**

- `check_domain_transaction_contracts(workspace: Path) -> list[Result]` 신규 함수:
  - `workspace/context/{domain}/index.md` 또는 `{domain}.md` 의 `### Cross-domain Transaction Contracts` H3 lookup (MANIFEST `## 도메인 분류` 표에서 등록된 도메인 별).
  - 부재 → INFO 1 줄 (`[INFO] {domain} 산출물에 Cross-domain Transaction Contracts 부재 — 단일 DB 시스템이거나 미작성`).
  - 존재 → `_parse_md_tables_in_section` (sub-section 단위 파서 보강 필요 — 본 함수 헬퍼 추가 또는 기존 파서 재사용 가능 여부 확인) 으로 표 파싱:
    - 컬럼 수 정확히 4: `본 도메인 entry`, `외부 도메인 영향`, `변경 type`, `file:line`.
    - 헤더 정확 일치 검증.
    - `변경 type` 컬럼 값이 화이트리스트 (`read`, `write`, `destroy`, `create`, `read·write` 등 조합) 에 속하는지 검증.
- `run_integrity_check` 에 호출 1 줄 추가.

**관련 파일 (#12)**

- 변경: `pilot/skills/learn/SKILL.md` (Phase 3 grep 표 + Phase 4 sub-step)
- 변경: `pilot/tools/doctor/integrity.py` (신규 함수)
- (선택) 변경: `pilot/skills/context/domain/{template}.md` — 도메인 산출 template 부재 (확인됨, `pilot/skills/context/domain/` 만 존재). 이번 작업에서는 template 신규 생성 안 함, learn SKILL.md 본문 가이드만으로 충분.

### C. 변경 파일 목록 (focus.md hint 정합)

| 파일 | feature | 변경 요지 | focus.md hint 정합 |
| ---- | ------- | --------- | ------------------ |
| `pilot/skills/learn/SKILL.md` | #09·#10·#12 | Phase 2 외부 detect + Phase 5 MANIFEST 갱신 + Phase 3·4 transaction | OK |
| `pilot/skills/analyze/SKILL.md` | #09·#11 | 5-2 cross-domain detect + Open Questions 보존 | OK |
| `pilot/skills/create-feature/SKILL.md` | #09·#11 | cross-domain detect + Open Questions 4 카테고리 템플릿 + 자동 detect | OK |
| `pilot/skills/init/SKILL.md` | #10 | MANIFEST template placeholder 1 줄 보강 | OK |
| `pilot/skills/context/lifecycle/setup/templates/MANIFEST.md.template` | #10 | 외부 도메인 placeholder 주석 | OK |
| `pilot/tools/doctor/integrity.py` | #09·#10·#11·#12 | 신규 검증 함수 4 종 + run_integrity_check 등록 | OK |
| `pilot/skills/context/lifecycle/projects/example/features/` | #11 | (생성 안 함 — S5 결정) | hint 와 다름 (focus 의 `만약 template 있다면` 조건부) |
| `pilot/skills/context/domain/{template}.md` | #12 | (생성 안 함 — S3 결정) | hint 와 다름 (조건부) |

> focus.md hint 의 "{template}" 류 조건부 위치 두 곳은 **현재 부재 확인**, 신규 생성하지 않고 SKILL.md 본문 inline 가이드로 처리. v0.4.0 에서 별도 template 시스템 도입 시 재고.

### D. 신규 단위 테스트 명세 (doctor schema 검증 위주)

기존 `pilot/tests/tools/test_doctor_integrity.py` 패턴 답습 (`unittest` + `importlib.util` + fixture 디렉터리).

| 테스트 파일 | 대상 함수 | 케이스 |
| ---------- | -------- | ------ |
| `pilot/tests/tools/test_doctor_external_domain.py` | `check_workspace_external_domain_section` | (1) `pass-empty`: 섹션 부재 → INFO, ERROR 없음 (2) `pass-valid`: 3 컬럼 + 헤더 정확 → ERROR 없음 (3) `error-column-mismatch`: 2 컬럼 → ERROR + "컬럼 수" (4) `error-header-mismatch`: 헤더 wording 변경 → ERROR + "헤더" (5) `info-stale-row`: 추정 도메인이 도메인 분류 표에도 등록 → INFO + "이미 학습됨" |
| `pilot/tests/tools/test_doctor_open_questions.py` | `check_features_open_questions` | (1) `pass-no-section`: Open Q 부재 → INFO 1 줄 (2) `pass-all-empty`: 4 카테고리 모두 (없음) → ERROR 없음 (3) `pass-with-items`: (a)·(b) 행 있음 → ERROR 없음 (4) `info-missing-category`: (c) 누락 → INFO (ERROR 아님) |
| `pilot/tests/tools/test_doctor_cross_domain_transaction.py` | `check_domain_transaction_contracts` | (1) `pass-no-subsection`: 단일 DB 도메인 → INFO 1 줄 (2) `pass-valid`: 4 컬럼 + 헤더 정확 + 변경 type 화이트리스트 → ERROR 없음 (3) `error-column-mismatch`: 3 컬럼 → ERROR (4) `error-bad-type`: 변경 type "delete" 등 화이트리스트 외 → ERROR + "변경 type" |
| `pilot/tests/tools/test_doctor_cross_domain.py` | (#09 의 INFO/WARN 검증) | (1) `info-circular-dependency`: 두 도메인 모두 외부 도메인 표 양쪽 등장 → INFO 1 줄 (2) `info-detect-failure`: namespace 추출 실패 → WARN 1 줄 (mock learn 시뮬레이션) — 단 #09 의 detect 알고리즘 자체는 SKILL.md 가이드라 단위 테스트 어려움. **본 테스트는 doctor 내 별도 함수 (`check_external_domain_circular`) 가 추가되면 작성, 아니면 skip** |

> **fixture 디렉터리 신설**: `pilot/tests/fixtures/v0.1.0-baseline/external-domain/{pass-empty, pass-valid, error-*}/`, `.../open-questions/{...}/`, `.../transaction-contracts/{...}/`. 기존 `config/{pass-empty, pass-valid, error-*}` 패턴 답습.
>
> **#09 의 SKILL.md 가이드 자체** (외부 reference 추출 알고리즘) 는 단위 테스트 대상 아님. 회귀 픽스처 (E 항목) 의 `_input/python-sample/secondary-domain/` end-to-end 시나리오로 검증.

### E. 회귀 픽스처 갱신 계획

**E1. `_input/python-sample/secondary-domain/` 신설**

- 위치: `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/secondary-domain/`
- 목적: cross-domain detect end-to-end 시나리오 (현재 `python-sample/` 은 단일 도메인이라 #09 detect 검증 불가능).
- 구조 (예시 — Python sample 정합):
  ```
  secondary-domain/
    __init__.py
    auth_service.py        # 외부 도메인 클래스
    user_model.py
    README.md
  python-sample/services/order_service.py  # 기존 — secondary_domain.auth_service.AuthService import 추가
  python-sample/main.py                    # 기존 — 동일
  ```
- 변경: 기존 `_input/python-sample/services/order_service.py` 에 `from secondary_domain.auth_service import AuthService` import 1 줄 추가 → cross-domain reference 발생.
- 결과: `/pilot:learn _input/python-sample/services/` 호출 시 `secondary_domain` 외부 reference detect → MANIFEST `## 외부 도메인 reference` 표에 행 추가.

**E2. expected 갱신 (`learn/expected/`)**

- 기존: `pilot/tests/fixtures/v0.1.0-baseline/learn/expected/.../inventory.md` 에 의존성 추적 표 7 행.
- 신규: `secondary_domain` 외부 reference 행 추가 + MANIFEST.md 의 `## 외부 도메인 reference` 표 신규 캡처.
- expected output 파일 추가:
  - `learn/expected/projects/python-sample/context/MANIFEST.md` (외부 도메인 섹션 포함)
  - `learn/expected/projects/python-sample/context/python-sample/inventory.md` (외부 의존 카테고리 추가)

**E3. `expected/features/` 의 Open Questions 섹션 sample**

- 기존: `analyze/expected/projects/python-sample-demo/features/01-*.md` 에 4 카테고리 모두 (없음) 표시 추가 (단일 도메인 시나리오).
- secondary-domain 추가 후: features 의 일부에 (b) cross-domain 산출물 부재 카테고리에 행 자동 추가된 sample.

**E4. `diff.sh` 검증**

- 기존: `pilot/tests/fixtures/v0.1.0-baseline/diff.sh` 가 `_input` ↔ regen 비교.
- v0.3.0: cross-domain 검증을 위해 비교 대상 확장 (MANIFEST.md, 외부 도메인 섹션 포함). diff.sh 본문 변경 최소 — 비교 디렉터리 path 만 갱신.

**E5. 회귀 검증 시점**

- PR-1 (#09+#10) 머지 후 secondary-domain fixture + expected 캡처. PR-1 의 머지 전제 조건이 fixture 캡처는 아님 (코드 변경 후 fixture 갱신).
- PR-2 (#11), PR-3 (#12) 도 각 머지 직후 expected 갱신.

### F. migration / backward-compat 처리 방안

**기존 v0.2.x 사용자 대상:**

| 조건 | v0.3.0 거동 | migration 필요? |
| ---- | ----------- | --------------- |
| MANIFEST.md 에 `## 외부 도메인 reference` 섹션 부재 | doctor INFO 1 줄. 첫 cross-domain reference detect 시 자동 작성 (idempotent). | **자동** (사용자 액션 불필요) |
| MANIFEST.md 에 사용자가 수동으로 외부 도메인 섹션 작성한 경우 | 헤더 정확 일치 시 doctor PASS. 컬럼 수 / 헤더 불일치 시 ERROR + 수정 안내. | 사용자 수동 (drift) |
| features/NN-*.md 에 Open Questions 섹션 부재 | doctor INFO 1 줄. 권장만, ERROR 아님. 신규 `/pilot:create-feature` 호출 시점부터 새 템플릿 적용. 기존 features 는 그대로. | **자동** (강제 안 함) |
| 도메인 산출물에 `### Cross-domain Transaction Contracts` 부재 | doctor INFO 1 줄. 단일 DB 시스템이면 정상. 다음 `/pilot:learn` 호출 시 transaction nesting detect 시 자동 추가. | **자동** |
| `workspace/context/config.md` 에 외부 reference ignore 패턴 부재 | hardcoded default fallback (10~20 항목). config 추가는 사용자 옵션. | **자동** |

**자동 마이그레이션 함수 (`migrate_v0_2_to_v0_3`) 작성 여부:**

- v0.2.x → v0.3.0 시 강제 변경 없음. 모든 신규 섹션은 부재 시 INFO 만, 첫 신규 호출 시 자동 작성. 따라서 별도 마이그레이션 함수 **작성 안 함**.
- 단 `.agent-state.yml` 의 schema 라벨 v1.2 → v1.3 bump 는 **선택**. v0.3.0 에서 신규 state 필드 추가가 없다면 schema 변경 없이 v1.2 유지.

**version bump:**

- `pilot/.claude-plugin/plugin.json` 의 `version`: `0.2.1` → `0.3.0`.
- `pilot/CHANGELOG.md` (있다면) 에 v0.3.0 entry 추가.

### G. 인수인계 항목 반영 (project.md 미처리 19 건 중)

- **#04 인수인계 1** (`Result.INFO` 레벨): #09·#10·#11·#12 의 doctor 검증에서 INFO 1 줄 알림 (섹션 부재·stale row·detect 실패) 에 재사용. 새 `Result.WARN` 레벨 필요 여부 검토 — focus.md 의 "WARN 1 줄" 표현은 stderr WARN (스킬 본문) 와 doctor INFO 가 혼재. doctor 내부에서는 INFO 로 통일 권장.
- **#04 인수인계 2** (`_parse_md_tables_in_section` 헬퍼): 본 작업의 4 종 doctor 검증 함수 모두 재사용. 단 코드블록 펜스 false positive 는 외부 도메인 섹션·Open Questions 섹션·transaction contracts 섹션 모두 코드블록 안에 표 예시를 둘 가능성 (특히 SKILL.md 가이드 안 example) 있어 **본 PR 에서 헬퍼 보강 1 회 필요**. 변경: `_parse_md_tables_in_section` 에 코드블록 (` ```` ``` ```` `) 추적 1~3 줄 추가, 코드블록 안 `| ... |` 줄 무시.
- **#01 인수인계 long-form 표 검증 패턴** (정확히 N 컬럼 + 헤더 정확 일치 강제, integrity.py:899-932): 본 작업의 4 종 doctor 검증 함수 모두 동일 패턴 답습.

### H. 주의사항

- **체크박스 갱신 권한 분리** (#03 인수인계 반영): 본 v0.3.0 작업의 generator 가 `project.md` 의 `## 목표` 체크박스를 직접 수정하지 않도록. evaluator wrapper step 5 가 단독 권한자.
- **A2 runtime fallback 일관성**: 신규 4 종 detect 알고리즘 모두 실패 시 abort 안 함, default fallback + WARN/INFO 1 줄. 패턴은 v0.2.x 의 #01·#02 와 동일.
- **doctor 출력 noise 관리**: v0.3.0 첫 실행 시 기존 v0.2.x workspace 에서 INFO 4 줄 추가 (외부 도메인 부재 + Open Q 부재 + transaction 부재 + ignore 패턴 부재 — 후자는 hardcoded default 라 발화 안 함). 사용자 가시성에 부담 없도록 INFO 메시지 wording 일관성 확인.
- **회귀 픽스처 input 표현력 합의** (#00 인수인계 반영): secondary-domain 추가 시 `_input/` 의 파일 수 변경을 본 plan 에서 명시적 합의 — 위 E1 의 4 파일 추가 + 기존 1 파일 수정 명시.
- **MANIFEST 자유 형식 원칙 보존**: `## 외부 도메인 reference` 섹션은 `## 도메인 분류` 와 동일하게 자유 형식 권장 (표·산문 모두 허용 — 단 표는 자동 갱신, 산문은 사용자 수동 관리). 단 doctor 검증은 `## 외부 도메인 reference` H2 + 표 형식만 검증 (표 부재 시 검증 skip + INFO).

### I. focus 반영 사항

- **focus.md 권고 진행 순서 그대로 반영**: PR-1 (#09+#10) → PR-2 (#11) → PR-3 (#12). focus 의 "(선택) #06~#08 LOW 이월 또는 함께" 는 본 plan 에서 분리 — v0.3.0 HIGH 4 건 완료 후 별도 plan.
- **focus.md 영향 범위 hint 와 본 plan 의 변경 파일 목록 정합**: 위 C 표 우측 컬럼 OK / 조건부 부재. 차이점 (example/features template, domain template) 명시.
- **focus.md 핵심 제약 모두 반영**: md / script 한정, A2 runtime fallback, doctor INFO 1 줄, backward-compat 자동, TDD 비활성 (단 doctor schema 검증 단위 테스트 4 건 신설).

### J. Open Questions (planner 가 spec 읽으며 발견 — 사용자 결정 필요)

#### (a) 같은 도메인 추가 read 필요

- (없음 — features/09~12.md spec 본문이 충분)

#### (b) cross-domain 산출물 부재

- (없음 — 본 플러그인이 single domain. cross-domain 의존성은 본 작업의 대상 자체)

#### (c) 외부 시스템 spec 부재

- (없음)

#### (d) 비즈니스 결정 영역 — **사용자 결정 필요**

1. **#10 외부 도메인 추정 알고리즘 우선순위**: spec line 17-20 에 1~3순위 명시되어 있으나, 2 순위 ("클래스 prefix 의 snake_case 변환 — 첫 prefix `ssm_s` ?") 가 모호함. `SsmSPackageSheet` → `ssm_s_package_sheet` → 첫 prefix 가 `ssm` 인지 `ssm_s` 인지 결정 필요. **권고: 1 순위 (Module::Class namespace) 만 구현 + 실패 시 unclassified 카테고리. 2 순위는 v0.4.0 이월**.
2. **#10 ignore 패턴 default 목록 출처**: Ruby framework 클래스 (`ActiveRecord::Base`, `ApplicationRecord`, `String`, `Hash`, `Time`, `Date`, `BigDecimal`, `OpenStruct`, `Struct`, `Set`, `Array`) 12 항목 가량. Python·TS 등 다른 언어는 어떻게? **권고: Ruby default 만 v0.3.0 hardcoded, config.md 의 신규 섹션 `## learn 외부 도메인 ignore 패턴` (선택) 으로 사용자 추가 가능. 다른 언어는 v0.4.0 multi-language ignore 시스템 도입**.
3. **#11 doctor 검증 강도**: features/NN-*.md 의 Open Questions 부재가 INFO (권장) 인지 ERROR (강제) 인지. spec line 37 은 INFO 명시. **권고: INFO 유지 (강제 시 사용자 수동 작성 features 위반)**.
4. **#11 example template 신규 생성 여부**: spec line 53 은 "만약 template 있다면" 조건부. 현재 `pilot/skills/context/lifecycle/projects/example/features/` 부재. **권고: S5 결정대로 신규 생성 안 함, create-feature SKILL.md inline 템플릿만 변경**.
5. **#12 단일 파일 도메인 vs 폴더 도메인 location 룰**: spec line 22 는 `{domain}/index.md` 또는 `{domain}.md` 둘 다 허용. 후자의 경우 "다중 DB" H2 가 도메인 본문 안에 추가되는데, 도메인 본문 길이 (200 줄 budget) 위반 위험. **권고: transaction contracts 섹션이 5 행 이상이면 `{domain}/transaction-contracts.md` 분리 권장 (heuristics 추가). 5 행 미만은 inline OK**.
6. **#12 transaction nesting 의 inner receiver 가 외부 도메인이 아닌 본 도메인일 경우**: cross-domain transaction 이 아니라 본 도메인 nested transaction. spec line 18-19 의 detect 알고리즘이 본 도메인 nesting 도 매칭 가능. **권고: 본 도메인 nesting 은 sub-section 에서 제외, 외부 namespace 만 캡처**.
7. **버전 bump 시점**: PR-1·PR-2·PR-3 머지 시점 vs 셋 다 머지 후 일괄 bump. **권고: 셋 다 머지 후 일괄 v0.3.0 bump (PR 마다 0.2.2·0.2.3·0.2.4 처럼 patch bump 안 함)**.
8. **PR 단위 권고 vs 단일 PR**: 본 plan 의 PR-1·PR-2·PR-3 분리 vs 단일 PR. **권고: 분리 — 회귀 픽스처 갱신 단위 + review 비용 + git history 가독성**.

> 위 Open Q 8 건 중 (d)1·2·5·6 은 **사용자 결정 필요** (구현 영역 정책). 나머지 (3·4·7·8) 는 권고 그대로 진행 가능. main agent 가 사용자에게 (d)1·2·5·6 를 우선 보고 후 결정 받기를 권장.
