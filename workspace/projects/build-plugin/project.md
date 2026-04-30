# build-plugin

> **Orchestrator** — 프로젝트 전체 흐름을 조율한다.
> 구체적 구현 지식은 `prompts/` 의 에이전트 컨텍스트 파일을 참조한다.
>
> **이 파일은 스캐폴딩 템플릿이다.** `/pilot:project` 가 신규 프로젝트 생성 시 그대로 복사한다.
> `{프로젝트명}` 토큰만 실제 프로젝트명으로 치환하고, 본문의 `{…}` 플레이스홀더는 사용자 또는 `/pilot:analyze` 가 채운다.

## 개요

{프로젝트 목적과 배경을 1~2문장으로}

## 제한사항

- {구현 제약 사항 — 예: 특정 DB 단일 조회, 외부 API 호출 금지, 상태값 전환 규칙 등}

## 목표

- [x] 회귀 골든 픽스처 (v0.1.0 baseline 캡처) -> [상세](features/00-regression-fixture.md)
- [x] learn 언어 패턴 외부화 (D10 default 폐지) -> [상세](features/01-learn-language-pattern-externalize.md)
- [x] analyze scope 카테고리 외부화 -> [상세](features/02-analyze-scope-category-externalize.md)
- [x] project.md H3 동적 생성 + SSOT -> [상세](features/03-project-md-h3-dynamic.md)
- [x] doctor config 정합성 검증 (D10 행 수 0 허용) -> [상세](features/04-doctor-config-validation.md)
- [x] v0.1.0 → v0.2.0 자동 마이그레이션 (M1) -> [상세](features/05-config-default-migration.md)
- [x] cross-domain 처리 가이드 (V1 발견 main milestone) -> [상세](features/09-cross-domain-guide.md) `[v0.3.0 HIGH]`
- [x] MANIFEST.md 외부 도메인 섹션 자동 추가 -> [상세](features/10-manifest-external-domain-section.md) `[v0.3.0 HIGH]`
- [ ] feature spec Open Questions 템플릿 -> [상세](features/11-feature-spec-open-questions.md) `[v0.3.0 HIGH]`
- [ ] cross-domain transaction 패턴 가이드 -> [상세](features/12-cross-domain-transaction-contract.md) `[v0.3.0 MED]`
- [ ] learn SKILL.md 모호함 해소 (Phase 1 fallback + Phase 5 H2 매칭) -> [상세](features/06-learn-skill-ambiguity.md) `[v0.3.0 LOW]`
- [ ] analyze SKILL.md scope/{domain}.md 생성 절차 명시 -> [상세](features/07-analyze-scope-creation.md) `[v0.3.0 LOW]`
- [ ] project SKILL.md `{프로젝트명}` 치환 범위 명문화 -> [상세](features/08-project-token-substitution.md) `[v0.3.0 LOW]`

> `/pilot:analyze` 실행 시 features/ 파일과 동기화되어 이 목록이 자동 갱신된다.

## 에이전트 호출 흐름

**순서를 반드시 준수한다. 이전 단계 완료 전 다음 단계로 진행하지 않는다.**

### 1. Planner — 구현 계획 수립

- **진입 조건:** 새 기능 구현 시작 시 항상 실행
- **로드:** `prompts/planner.md`
- **완료 기준:** 구현 단계별 계획이 명시적으로 확정됨 → Generator 진행

### 2. Generator — 코드 구현

- **진입 조건:** Planner 계획 확정 후
- **로드:** `prompts/generator.md` + [`coding.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/coding.md)
- **완료 기준:** 구현 완료 후 [`evals/coding.json`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/evals/coding.json) 해당 케이스 체크 통과 → Evaluator 진행

### 3. Evaluator — 검토

- **진입 조건:** Generator eval 체크 통과 후
- **로드:** `prompts/evaluator.md`
- **완료 기준:** 체크리스트 전 항목 확인 → 목표의 해당 항목 `[x]` 처리

> **TDD 모드** 활성화 시 (`/pilot:project {PROJECT} --tdd` 또는 `/pilot:tdd`) 이 섹션이 Red-Green-Refactor 흐름으로 자동 교체된다. 상세: [tdd-activation.md](${CLAUDE_PLUGIN_ROOT}/skills/context/modes/tdd-activation.md).

## 관련 파일

### Models

| Class | DB  | 목적 |
| ----- | --- | ---- |
|       |     |      |

### Endpoints

| 엔드포인트 | Method | 목적 |
| ---------- | ------ | ---- |
|            |        |      |

### Services

| Class | 파일 | 목적 |
| ----- | ---- | ---- |
|       |      |      |

> Models / Endpoints / Services 표는 `/pilot:analyze` 실행 시 `scope/{domain}.md` 에서 features 관련 행을 선별해 자동 기입한다.

## 에이전트 간 전달사항

- [ ] `Result.INFO` 레벨이 `pilot/tools/doctor/_common.py:36` 에 추가됨 → 후속 feature 의 doctor 출력에서 부재·default fallback 안내 시 재사용 가능 (from #04)
- [ ] `pilot/tools/doctor/integrity.py:785` 에 `_parse_md_tables_in_section(text, section_header)` 헬퍼 추가 → #01 (learn 두 표 lookup) · #02 (scope 카테고리 lookup) runtime 구현에서 재사용 가능. 단 현재 구현은 코드블록 (```` ``` ````) 펜스를 추적하지 않아, 코드블록 안 `| ... |` 줄을 표로 오판할 가능성. 실제 config.md 에서 코드블록 안에 표 예시를 둘 경우 false positive 보강 필요 (from #04)
- [ ] #00 의 회귀 픽스처는 0a 부분 (`config/` 5 fixture + `diff.sh` 골격 + `README.md`) 만 완료. `_input/`·`learn/expected/`·`project/expected/`·`analyze/expected/` 는 Open Q #1 (입력 언어 결정) 후 별도 0b PR 에서 추가. #01·#02·#03 완료 후 회귀 검증 자체는 0b 완료 시점까지 보류 (from #00)
- [ ] features/04 의 runtime fallback 결정 (A2: `/pilot:learn` `/pilot:analyze` `/pilot:project` `/pilot:create-feature` 가 잘못된 config 행을 abort 없이 default fallback + stderr WARN 1 줄) 은 SKILL.md 본문 변경이 필요. 본 #04 작업에는 doctor 검증 함수만 포함됨 → #01·#02·#03 의 SKILL.md 갱신 시 각 스킬에서 fallback 거동 직접 구현 필요 (from #04)
- [ ] D9 결정 적용 — 역할 분류 표 wide-form 폐기, long-form 2 컬럼 (`| 역할 | 식별 패턴 |`) 전환 완료. SKILL.md / config.md / pass-valid fixture / integrity.py / test_doctor_integrity.py 5 곳 일관 동기화. evaluator.md `## 기능 완성도` 의 #01 행 텍스트 ("lookup (wide-form)") 는 다음 `/pilot:analyze --regen-agents` 시 long-form 으로 갱신 필요 (from #01)
- [ ] #01 의 default 격하 blockquote 패턴 (`> default — workspace/context/config.md 의 ## {섹션명} 가 비어있을 때 사용. config 행이 있으면 그 행이 우선.`) 정착 — #02 (analyze 5-2 scope 카테고리) · #03 (project.md `## 관련 파일` H2 가이드) 의 default 격하에 동일 형식 재사용 (from #01)
- [ ] #01 의 A2 runtime fallback 절차 (잘못된 config 행 stderr WARN 1 줄 + default fallback, abort 금지) SKILL.md 본문 명시 패턴 정착 — #02 의 `/pilot:analyze` 5-2 SKILL.md 본문에도 동일 절차 명시 필요 (from #01)
- [ ] #01 의 long-form 표 doctor 검증 패턴 (정확히 2 컬럼 + 헤더 정확 일치 강제, integrity.py:899-932) — 향후 다른 신규 long-form 표 검증에 재사용 가능 (from #01)
- [ ] #02 의 5-2 본문이 (a) `> default — workspace/context/config.md 의 ## scope 카테고리 가 비어있을 때 사용. config 행이 있으면 그 행이 우선.` blockquote (b) A2 runtime fallback 절차 (config 표 행별 검증·잘못된 행 stderr WARN 1 줄 후 default fallback·abort 금지) (c) 3 가지 예외 (MANIFEST 헤더 없음·scope 파일 부재·config 빈 표) 명시 패턴 정착 — `/pilot:project` (#03 의 `## 관련 파일` H2 가이드) 에서 동일 형식 재사용 (from #02)
- [ ] #02 의 SKILL.md default 표 ↔ workspace/context/config.md `## scope 카테고리` ↔ pass-valid fixture 3 곳 본문 동일 검증 패턴 — #03 가 H3 SSOT 분리 (H3 헤더 = project.md 본문, 표 헤더 = config) 적용 시 동일 3 곳 동기화 검사 필요. 차이 발생 시 회귀 픽스처에서 PASS 케이스 위반 (from #02)
- [ ] #02 의 fixture pass-valid 헤더·prefix 교정은 #04 검증 룰 (3 컬럼·헤더 정확 일치·`## ` prefix·H3 화이트리스트) 와 features/02 default 양쪽에 정합. doctor 검증 룰 추가 보강 불필요 — #03 작업도 동일 정합을 유지하면 별도 룰 추가 불필요 (from #02)
- [ ] #02 의 spec.md line 63 의 `pilot/skills/analyze/SKILL.md:166-228` 라인 범위 참조는 5-2 본문 +30 라인 추가로 끝 라인이 어긋남. drift 정합성에는 영향 없으나 다음 `/pilot:learn` 또는 spec.md 갱신 시 재캡처 필요 (from #02)
- [ ] #03 generator 가 project.md `## 목표` 의 #03 항목을 self-mark `[x]` 로 처리한 사실 발견 (wrapper 책임 분리 위반). evaluator wrapper step 5 가 체크박스 갱신의 단독 권한자임. 후속 generator 호출 시 `## 목표` 체크박스 수정 금지를 명시 — generator 는 features/ 와 코드만 수정, 체크박스는 evaluator 만 (from #03)
- [ ] #03 의 SSOT 분리 패턴 (H3 헤더 = project skill 1 회 생성, 표 본문 = analyze 5-2 / create-feature 매번 갱신, 사용자 수동 H3 양쪽 보존, 삭제는 복구 안 함, example H2 부재 시 H2+H3 새로 생성) 정착. v1 핵심 4 features (#01·#02·#03·#04) 코드 변경 완료. 남은 작업 = 0b 회귀 픽스처 (`_input/`+`expected/`) · 5번 회귀 검증 · README · version bump (from #03)
- [ ] #03 의 example/project.md 단순화 (H3+표 제거, H2+가이드 주석만) 는 **신규 프로젝트 생성 시점부터** H3 동적 채움이 적용됨. 기존 build-plugin 의 project.md 는 영향 받지 않음 (이미 H3 가공된 상태로 존재) (from #03)
- [ ] #01·#04·#05 D10 일괄 적용 완료. 남은 후속 작업 = (a) version bump (`pilot/.claude-plugin/plugin.json` 0.1.0 → 0.2.0) — 본 변경 후 `migrate_v0_1_to_v0_2` 가 비로소 활성. (b) 0b 회귀 픽스처 (`_input/` + `learn/expected/` + `project/expected/` + `analyze/expected/`) — Open Q #1 (입력 언어 결정) 후 별도 PR. (c) #00 의 5번 회귀 검증 (config 비어있을 때 v0.1.0=v1 동일 출력) — 0b 완료 시점까지 보류. (d) `prompts/evaluator.md` 의 `[analyze-managed]` 영역은 현재 evaluator 가 직접 갱신했으나 다음 `/pilot:analyze --regen-agents` 시 재정렬 필요 (from #01·#04·#05)
- [ ] #05 의 마이그레이션 prompt 동작 검증은 **interactive 환경에서 실제 실행** 필요. 현재 plugin v0.1.0 환경이라 doctor 가 마이그레이션 WARN 을 발화 안 함 (`if cv < (0,2,0): return` 조기 반환). version bump 후 실제 사용자 환경에서 재검증 권장 (from #05)
- [ ] #05 의 `_inject_v010_defaults_into_config` 헬퍼는 헤더 정확 일치 (`| 언어 | 의존성 추출 패턴 |`·`| 역할 | 식별 패턴 |`) 가 사전조건. 사용자가 헤더를 임의 변경 (예: 영문화 `| Lang | Pattern |`) 한 경우 주입 실패 — 단 사전 doctor ERROR (헤더 불일치) 가 먼저 차단하므로 정상 흐름에서는 발생 안 함 (from #05)
- [ ] #05 의 `migration_v0_2_0` 필드는 프로젝트별 (`.agent-state.yml`). 한 workspace 다중 프로젝트 시 각 프로젝트가 첫 doctor --fix 호출 시 중복 prompt 발생 (config 는 1 회 주입 후 빈 상태 아님 → 이후 프로젝트는 `_is_learn_section_empty=False` 로 자동 skip). 정상 거동이지만 v0.3.0 deprecation 시 재검토 (from #05)
- [x] #00 의 0b 캡처 산출물 디렉터리 rename 완료 — `project/expected/projects/python-sample-demo/`·`analyze/expected/projects/python-sample-demo/` 양쪽 일관. README.md tree·재실행 절차 + `_input/python-sample/README.md` line 33 동기화. `python-sample` (도메인명) ↔ `python-sample-demo` (프로젝트명) 구분 명확. 회귀 자동 검증 (`diff.sh --actual {regen}` 1 회 실행) 은 #01·#02·#03 runtime lookup 구현 후 별도 수행 (from #00)
- [ ] #00 의 0b 캡처는 plan 의 `_input/` 8 파일 외에 `routes.py`·`helpers.py`·`README.md` 3 파일을 추가했음. 이는 `main.py` 가 `from routes import register_routes` 를 import 하기 위해 필요했고, 결과적으로 `inventory.md` 의 의존성 추적 표가 7 행으로 풍부해짐. plan 의 "1 도메인 단일 import" 표현은 literal 하게는 위반이지만 fixture 의 표현력을 위해 합리적 확장. 후속 plan 작성 시 `_input/` 의 파일 수를 명시적으로 합의 (from #00)
- [ ] #00 의 LLM 시뮬레이션 캡처 한계 — `analyze/expected/projects/python-sample/prompts/generator.md` 의 `[analyze-managed]` `## 핵심 변경 대상` 헤더는 SKILL.md spec 의 `## 핵심 서비스/모델` 과 wording 차이. README.md 의 "wording 차이 ≠ 회귀" 정책으로 허용. 실제 `/pilot:analyze` 1 회 실행 후 wording 재캡처 권장 (from #00)
- [ ] #09·#10 의 `_parse_md_tables_in_section` 헬퍼에 코드블록 (` ``` `) 추적 보강 완료 (integrity.py:807·811-820). 코드블록 안 `| ... |` 줄 = false positive 방지. 후속 신규 doctor schema 검증 함수에서도 동일 헬퍼 재사용 가능 — 별도 보강 불필요 (from #10)
- [ ] #09·#10 의 `check_workspace_external_domain_section` 신규 함수 (integrity.py:1077-1197) 는 `## 외부 도메인 reference` 헤더에 sub-string 매칭 (`(learn 미완료)` 등 사용자 편집 friendly). 후속 #11 (Open Questions) · #12 (transaction contracts) doctor 검증 함수 작성 시 동일 sub-string 패턴 재사용 가능 (from #10)
- [ ] #09 의 외부 도메인 ignore 패턴은 Ruby default 12 항목만 hardcoded (learn SKILL.md:101). config 의 `## learn 외부 도메인 ignore 패턴` 섹션 추가 가능 (선택). Python·TS 등 multi-language ignore 시스템은 v0.4.0 milestone (from #09)
- [ ] #09 의 cross-domain detect (`/pilot:create-feature` 3-bis, `/pilot:analyze` 5-2) 는 MANIFEST 의 `## 외부 도메인 reference` 표 lookup → INFO 1 줄. #11 의 Open Questions 4 카테고리 (b) 자동 입력은 PR-2 머지 후 wiring 필요 (from #09)
- [ ] #10 의 추정 도메인 알고리즘은 1 순위 (`Module::Class` namespace 첫 segment 소문자화) 만 구현. 2 순위 (snake_case 변환) 와 3 순위 (unclassified 카테고리) 는 v0.4.0 이월 (Open Q d-1 사용자 옵션 A 수락) (from #10)
- [ ] #09·#10 의 회귀 픽스처 `_input/python-sample/secondary-domain/` (4 파일) + `services/checkout.py` 1 줄 추가는 cross-domain detect end-to-end 시나리오용. expected output 캡처 (`learn/expected/.../inventory.md` 외부 의존 카테고리 + `MANIFEST.md` 외부 도메인 섹션) 는 후속 0c PR 에서 진행 예정 (from #09·#10)
