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
- [x] feature spec Open Questions 템플릿 -> [상세](features/11-feature-spec-open-questions.md) `[v0.3.0 HIGH]`
- [x] cross-domain transaction 패턴 가이드 -> [상세](features/12-cross-domain-transaction-contract.md) `[v0.3.0 MED]`
- [x] learn SKILL.md 모호함 해소 (Phase 1 fallback + Phase 5 H2 매칭) -> [상세](features/06-learn-skill-ambiguity.md) `[v0.3.0 LOW]`
- [x] analyze SKILL.md scope/{domain}.md 생성 절차 명시 -> [상세](features/07-analyze-scope-creation.md) `[v0.3.0 LOW]`
- [x] project SKILL.md `{프로젝트명}` 치환 범위 명문화 -> [상세](features/08-project-token-substitution.md) `[v0.3.0 LOW]`
- [x] 부트스트랩 마법사 (`/pilot:init` 확장) -> [상세](features/13-init-bootstrap-wizard.md) `[v0.3.0 HIGH]`
- [x] Onboarding 시나리오 가이드 (5분 완주 문서) -> [상세](features/14-onboarding-guide.md) `[v0.3.0 HIGH]`
- [x] TDD 모드 사후 토글 (`/pilot:tdd on|off`) -> [상세](features/15-tdd-mode-toggle.md) `[v0.3.0 MED]`
- [x] Doctor onboarding-health 점검 -> [상세](features/16-doctor-onboarding-health.md) `[v0.3.0 MED]`
- [x] 조건부 인터뷰 (Open Questions 소비) -> [상세](features/17-conditional-interview.md)
- [x] 정비 prune — 미사용·드리프트 정리 -> [상세](features/18-consolidation-prune.md) `[consolidation 1/3]`
- [x] 정비 rewrite — 원칙 중심 재작성 -> [상세](features/19-consolidation-rewrite.md) `[consolidation 2/3]`
- [x] 정비 slim — Python 슬림화 -> [상세](features/20-consolidation-slim.md) `[consolidation 3/3]`
- [x] 정비 후속 — 문서 정합 (#20 반영) -> [상세](features/21-consolidation-docs-sync.md) `[dogfooding]`
- [ ] 정비 후속 — context 드리프트 재학습 (D-2, 실측 3건) -> [상세](features/22-context-drift-relearn.md) `[후속]`
- [x] doctor 파서 오탐 2건 (conventions 플레이스홀더 + features 카운트) -> [상세](features/23-conventions-placeholder-false-positive.md) `[후속]`
- [x] pilot-update.sh 고장 — 경로 stale + 설계 한계 + 잘못된 안내 -> [상세](features/24-pilot-update-tool.md) `[후속]` (evaluator 2026-07-26: 저장소 내 전건 통과 + 잔여 1건이던 v0.10.0 릴리스 노트도 사용자 승인 후 정정 완료)
- [x] doctor --schema ↔ claude plugin validate 중복 검토 (결론: 현행 유지) -> [상세](features/25-schema-vs-claude-validate.md) `[후속]`

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

- [x] `Result.INFO` 레벨이 `pilot/tools/doctor/_common.py:36` 에 추가됨 → 후속 feature 의 doctor 출력에서 부재·default fallback 안내 시 재사용 가능 (from #04) — #16 OH 처방·`--fix` skip 안내·OH-5 N/A 줄에서 재사용
- [x] `pilot/tools/doctor/integrity.py:785` 에 `_parse_md_tables_in_section(text, section_header)` 헬퍼 추가 → #01 (learn 두 표 lookup) · #02 (scope 카테고리 lookup) runtime 구현에서 재사용 가능. 단 현재 구현은 코드블록 (```` ``` ````) 펜스를 추적하지 않아, 코드블록 안 `| ... |` 줄을 표로 오판할 가능성. 실제 config.md 에서 코드블록 안에 표 예시를 둘 경우 false positive 보강 필요 (from #04) — #16 OH-1 3 섹션 표 행 수 검증 + OH-4 도메인 분류 표 행 수 검증에서 재사용. 코드블록 펜스 추적은 #10 PR-1 에서 보강 완료
- [x] #00 의 회귀 픽스처는 0a 부분 (`config/` 5 fixture + `diff.sh` 골격 + `README.md`) 만 완료. `_input/`·`learn/expected/`·`project/expected/`·`analyze/expected/` 는 Open Q #1 (입력 언어 결정) 후 별도 0b PR 에서 추가. #01·#02·#03 완료 후 회귀 검증 자체는 0b 완료 시점까지 보류 (from #00) — 0b 완료 확인 (2026-06-10): `_input/python-sample`·`learn/expected/`·`project/`·`analyze/` 모두 존재
- [x] features/04 의 runtime fallback 결정 (A2: `/pilot:learn` `/pilot:analyze` `/pilot:project` `/pilot:create-feature` 가 잘못된 config 행을 abort 없이 default fallback + stderr WARN 1 줄) 은 SKILL.md 본문 변경이 필요. 본 #04 작업에는 doctor 검증 함수만 포함됨 → #01·#02·#03 의 SKILL.md 갱신 시 각 스킬에서 fallback 거동 직접 구현 필요 (from #04) — 구현 확인 (2026-06-10): learn SKILL.md:69 A2 문구 정착, analyze 는 references/scope-sync.md 5-2 위임
- [x] D9 결정 적용 — 역할 분류 표 wide-form 폐기, long-form 2 컬럼 (`| 역할 | 식별 패턴 |`) 전환 완료. SKILL.md / config.md / pass-valid fixture / integrity.py / test_doctor_integrity.py 5 곳 일관 동기화. evaluator.md `## 기능 완성도` 의 #01 행 텍스트 ("lookup (wide-form)") 는 다음 `/pilot:analyze --regen-agents` 시 long-form 으로 갱신 필요 (from #01) — 갱신 확인 (2026-06-10): prompts/ 에 "wide-form" 텍스트 잔존 없음
- [x] #01 의 default 격하 blockquote 패턴 (`> default — workspace/context/config.md 의 ## {섹션명} 가 비어있을 때 사용. config 행이 있으면 그 행이 우선.`) 정착 — #02 (analyze 5-2 scope 카테고리) · #03 (project.md `## 관련 파일` H2 가이드) 의 default 격하에 동일 형식 재사용 (from #01) — #02·#03 완료로 소화 (2026-06-10)
- [x] #01 의 A2 runtime fallback 절차 (잘못된 config 행 stderr WARN 1 줄 + default fallback, abort 금지) SKILL.md 본문 명시 패턴 정착 — #02 의 `/pilot:analyze` 5-2 SKILL.md 본문에도 동일 절차 명시 필요 (from #01) — #02 완료로 소화 (2026-06-10)
- [x] #01 의 long-form 표 doctor 검증 패턴 (정확히 2 컬럼 + 헤더 정확 일치 강제, integrity.py:899-932) — 향후 다른 신규 long-form 표 검증에 재사용 가능 (from #01) — 재사용 메모, #16 OH 검증까지 반영 완료 (2026-06-10)
- [x] #02 의 5-2 본문이 (a) `> default — workspace/context/config.md 의 ## scope 카테고리 가 비어있을 때 사용. config 행이 있으면 그 행이 우선.` blockquote (b) A2 runtime fallback 절차 (config 표 행별 검증·잘못된 행 stderr WARN 1 줄 후 default fallback·abort 금지) (c) 3 가지 예외 (MANIFEST 헤더 없음·scope 파일 부재·config 빈 표) 명시 패턴 정착 — `/pilot:project` (#03 의 `## 관련 파일` H2 가이드) 에서 동일 형식 재사용 (from #02) — #03 완료로 소화 (2026-06-10)
- [x] #02 의 SKILL.md default 표 ↔ workspace/context/config.md `## scope 카테고리` ↔ pass-valid fixture 3 곳 본문 동일 검증 패턴 — #03 가 H3 SSOT 분리 (H3 헤더 = project.md 본문, 표 헤더 = config) 적용 시 동일 3 곳 동기화 검사 필요. 차이 발생 시 회귀 픽스처에서 PASS 케이스 위반 (from #02) — #03 완료로 소화 (2026-06-10)
- [x] #02 의 fixture pass-valid 헤더·prefix 교정은 #04 검증 룰 (3 컬럼·헤더 정확 일치·`## ` prefix·H3 화이트리스트) 와 features/02 default 양쪽에 정합. doctor 검증 룰 추가 보강 불필요 — #03 작업도 동일 정합을 유지하면 별도 룰 추가 불필요 (from #02) — #03 완료로 소화 (2026-06-10)
- [x] #02 의 spec.md line 63 의 `pilot/skills/analyze/SKILL.md:166-228` 라인 범위 참조는 5-2 본문 +30 라인 추가로 끝 라인이 어긋남. drift 정합성에는 영향 없으나 다음 `/pilot:learn` 또는 spec.md 갱신 시 재캡처 필요 (from #02) — 재캡처 완료 (2026-06-10): spec.md 61-65 라인 인용 5 건 현행 라인으로 일괄 갱신
- [x] #03 generator 가 project.md `## 목표` 의 #03 항목을 self-mark `[x]` 로 처리한 사실 발견 (wrapper 책임 분리 위반). evaluator wrapper step 5 가 체크박스 갱신의 단독 권한자임. 후속 generator 호출 시 `## 목표` 체크박스 수정 금지를 명시 — generator 는 features/ 와 코드만 수정, 체크박스는 evaluator 만 (from #03) — 명시 완료 (2026-06-10): pilot-generator.md step 4 에 `## 목표` 수정 금지 예외 추가
- [x] #03 의 SSOT 분리 패턴 (H3 헤더 = project skill 1 회 생성, 표 본문 = analyze 5-2 / create-feature 매번 갱신, 사용자 수동 H3 양쪽 보존, 삭제는 복구 안 함, example H2 부재 시 H2+H3 새로 생성) 정착. v1 핵심 4 features (#01·#02·#03·#04) 코드 변경 완료. 남은 작업 = 0b 회귀 픽스처 (`_input/`+`expected/`) · 5번 회귀 검증 · README · version bump (from #03) — #18 planner 소비 (2026-07-24): 수동 회귀 하네스 삭제 승인으로 0b 픽스처·회귀 검증 폐기, version bump 는 v0.9.0 으로 기완료
- [ ] #03 의 example/project.md 단순화 (H3+표 제거, H2+가이드 주석만) 는 **신규 프로젝트 생성 시점부터** H3 동적 채움이 적용됨. 기존 build-plugin 의 project.md 는 영향 받지 않음 (이미 H3 가공된 상태로 존재) (from #03)
- [x] #01·#04·#05 D10 일괄 적용 완료. 남은 후속 작업 = (a) version bump (`pilot/.claude-plugin/plugin.json` 0.1.0 → 0.2.0) — 본 변경 후 `migrate_v0_1_to_v0_2` 가 비로소 활성. (b) 0b 회귀 픽스처 (`_input/` + `learn/expected/` + `project/expected/` + `analyze/expected/`) — Open Q #1 (입력 언어 결정) 후 별도 PR. (c) #00 의 5번 회귀 검증 (config 비어있을 때 v0.1.0=v1 동일 출력) — 0b 완료 시점까지 보류. (d) `prompts/evaluator.md` 의 `[analyze-managed]` 영역은 현재 evaluator 가 직접 갱신했으나 다음 `/pilot:analyze --regen-agents` 시 재정렬 필요 (from #01·#04·#05) — #18 planner 소비 (2026-07-24): (a) 기완료 (현재 0.9.0), (b)·(c) 하네스 삭제 승인으로 폐기, (d) 는 다음 `--regen-agents` 시 자동 재정렬
- [x] #05 의 마이그레이션 prompt 동작 검증은 **interactive 환경에서 실제 실행** 필요. 현재 plugin v0.1.0 환경이라 doctor 가 마이그레이션 WARN 을 발화 안 함 (`if cv < (0,2,0): return` 조기 반환). version bump 후 실제 사용자 환경에서 재검증 권장 (from #05) — #20 planner 소비 (2026-07-25): 마이그레이션 코드 자체가 #20 스텝 1 에서 삭제 확정 — 검증 대상 소멸
- [x] #05 의 `_inject_v010_defaults_into_config` 헬퍼는 헤더 정확 일치 (`| 언어 | 의존성 추출 패턴 |`·`| 역할 | 식별 패턴 |`) 가 사전조건. 사용자가 헤더를 임의 변경 (예: 영문화 `| Lang | Pattern |`) 한 경우 주입 실패 — 단 사전 doctor ERROR (헤더 불일치) 가 먼저 차단하므로 정상 흐름에서는 발생 안 함 (from #05) — #20 planner 소비 (2026-07-25): 해당 헬퍼가 #20 스텝 1 삭제 대상 — 사전조건 노트 소멸
- [x] #05 의 `migration_v0_2_0` 필드는 프로젝트별 (`.agent-state.yml`). 한 workspace 다중 프로젝트 시 각 프로젝트가 첫 doctor --fix 호출 시 중복 prompt 발생 (config 는 1 회 주입 후 빈 상태 아님 → 이후 프로젝트는 `_is_learn_section_empty=False` 로 자동 skip). 정상 거동이지만 v0.3.0 deprecation 시 재검토 (from #05) — #20 planner 소비 (2026-07-25): migration 흐름 전체 삭제 (스텝 1) 로 중복 prompt 시나리오 소멸 — state 의 `migration_v0_2_0` 잔존값은 무해
- [x] #00 의 0b 캡처 산출물 디렉터리 rename 완료 — `project/expected/projects/python-sample-demo/`·`analyze/expected/projects/python-sample-demo/` 양쪽 일관. README.md tree·재실행 절차 + `_input/python-sample/README.md` line 33 동기화. `python-sample` (도메인명) ↔ `python-sample-demo` (프로젝트명) 구분 명확. 회귀 자동 검증 (`diff.sh --actual {regen}` 1 회 실행) 은 #01·#02·#03 runtime lookup 구현 후 별도 수행 (from #00)
- [x] #00 의 0b 캡처는 plan 의 `_input/` 8 파일 외에 `routes.py`·`helpers.py`·`README.md` 3 파일을 추가했음. 이는 `main.py` 가 `from routes import register_routes` 를 import 하기 위해 필요했고, 결과적으로 `inventory.md` 의 의존성 추적 표가 7 행으로 풍부해짐. plan 의 "1 도메인 단일 import" 표현은 literal 하게는 위반이지만 fixture 의 표현력을 위해 합리적 확장. 후속 plan 작성 시 `_input/` 의 파일 수를 명시적으로 합의 (from #00) — #18 planner 소비 (2026-07-24): critic C1 재결정으로 `_input/` 은 튜토리얼 더미 저장소용 보존 확정, expected 캡처 전면 폐기로 파일 수 합의 논점 자체가 소멸
- [x] #00 의 LLM 시뮬레이션 캡처 한계 — `analyze/expected/projects/python-sample/prompts/generator.md` 의 `[analyze-managed]` `## 핵심 변경 대상` 헤더는 SKILL.md spec 의 `## 핵심 서비스/모델` 과 wording 차이. README.md 의 "wording 차이 ≠ 회귀" 정책으로 허용. 실제 `/pilot:analyze` 1 회 실행 후 wording 재캡처 권장 (from #00) — #18 planner 소비 (2026-07-24): analyze/expected 삭제 승인으로 폐기
- [x] #09·#10 의 `_parse_md_tables_in_section` 헬퍼에 코드블록 (` ``` `) 추적 보강 완료 (integrity.py:807·811-820). 코드블록 안 `| ... |` 줄 = false positive 방지. 후속 신규 doctor schema 검증 함수에서도 동일 헬퍼 재사용 가능 — 별도 보강 불필요 (from #10) — #20 planner 소비 (2026-07-25): md 표 lint 4종 이관 (스텝 2) 으로 doctor schema 검증 함수 신설 계보 종료 — 헬퍼 자체는 `check_conventions_paths` 소비로 보존
- [x] #09·#10 의 `check_workspace_external_domain_section` 신규 함수 (integrity.py:1077-1197) 는 `## 외부 도메인 reference` 헤더에 sub-string 매칭 (`(learn 미완료)` 등 사용자 편집 friendly). 후속 #11 (Open Questions) · #12 (transaction contracts) doctor 검증 함수 작성 시 동일 sub-string 패턴 재사용 가능 (from #10) — #16 OH-1 의 `## learn 언어 패턴`·`## scope 카테고리`·`## Ignore` 헤더 매칭에서 sub-string 패턴 재사용
- [ ] #09 의 외부 도메인 ignore 패턴은 Ruby default 12 항목만 hardcoded (learn SKILL.md:101). config 의 `## learn 외부 도메인 ignore 패턴` 섹션 추가 가능 (선택). Python·TS 등 multi-language ignore 시스템은 v0.4.0 milestone (from #09)
- [x] #09 의 cross-domain detect (`/pilot:create-feature` 3-bis, `/pilot:analyze` 5-2) 는 MANIFEST 의 `## 외부 도메인 reference` 표 lookup → INFO 1 줄. #11 의 Open Questions 4 카테고리 (b) 자동 입력은 PR-2 머지 후 wiring 필요 (from #09) — wiring 완료 확인 (2026-07-24, #17 planner): create-feature SKILL.md:98-106 (3-bis) + analyze SKILL.md:167-169 실재. #17 의 3-ter/7.5 인터뷰가 이 (b) 행 출력을 소비
- [ ] #10 의 추정 도메인 알고리즘은 1 순위 (`Module::Class` namespace 첫 segment 소문자화) 만 구현. 2 순위 (snake_case 변환) 와 3 순위 (unclassified 카테고리) 는 v0.4.0 이월 (Open Q d-1 사용자 옵션 A 수락) (from #10)
- [x] #09·#10 의 회귀 픽스처 `_input/python-sample/secondary-domain/` (4 파일) + `services/checkout.py` 1 줄 추가는 cross-domain detect end-to-end 시나리오용. expected output 캡처 (`learn/expected/.../inventory.md` 외부 의존 카테고리 + `MANIFEST.md` 외부 도메인 섹션) 는 후속 0c PR 에서 진행 예정 (from #09·#10) — #18 planner 소비 (2026-07-24): 하네스 (learn/expected 등) 삭제 승인으로 0c PR 폐기 (`_input/` 자체는 critic C1 재결정으로 튜토리얼용 보존)
- [x] #11 의 `check_features_open_questions` 신규 함수 (integrity.py:1203-1258) 는 features/NN-*.md 의 `## Open Questions` H2 부재 시 INFO 1 줄 (backward-compat — 기존 v0.2.x features 13 건 모두 INFO 만, ERROR 없음). 후속 #12 (transaction contracts) doctor 검증 함수 작성 시 동일 sub-string 패턴 + INFO-only 거동 재사용 가능 (from #11) — #16 OH-5 의 features 디렉터리 순회 + `.md` glob 패턴 재사용
- [x] #11 의 create-feature SKILL.md 3-bis 가 cross-domain detect 결과를 Open Questions (b) 행으로 자동 추가하는 wiring (PR-1 머지 후) 은 본 PR-2 에서 명문화 완료. PR-1 의 MANIFEST `## 외부 도메인 reference` 표 lookup 거동과 결합되어 end-to-end 동작. doctor 픽스처 `pass-valid` 의 (a)·(c) 행은 추상 placeholder (FooService·ExternalApi) 사용 — 후속 픽스처 작성 시 도메인 단어 누출 회피 패턴 답습 권장 (from #11) — #17 planner 가 3-ter 결합 지점 확인 (행 형식 대조, plan 참조) 으로 소비 (2026-07-24). #17 은 픽스처 무변경이라 placeholder 권고는 미해당 — 향후 픽스처 작성 시 여전히 유효한 가이드
- [ ] #11 의 example/features template 신규 생성 안 함 (S5 결정 반영). create-feature SKILL.md inline 템플릿이 SSOT. v0.4.0 에서 별도 template 시스템 도입 시 재고 (from #11)
- [x] #12 의 `_parse_md_tables_in_h3_section` 신규 헬퍼 (integrity.py:1271-1326) 는 H3 (`### ...`) 섹션 안 표 파싱 + 코드블록 펜스 추적. 후속 신규 H3 sub-section schema 검증에 재사용 가능 (#10 의 `_parse_md_tables_in_section` H2 버전과 짝). 후속 feature 에서 H3 단위 검증 필요 시 활용 (from #12) — #20 planner 소비 (2026-07-25): H3 헬퍼가 tx contracts 검증과 함께 삭제 (스텝 2) — 재사용 노트 소멸
- [x] #12 의 `_TX_TYPE_WHITELIST` (integrity.py:1264-1269) 는 Rails ActiveRecord 메서드 → CRUD type 매핑 결과의 화이트리스트. `read` / `write` / `destroy` / `create` + `·` 조합 14 항목. v0.4.0 multi-language ignore 시스템 도입 시 재고 (from #12) — #20 planner 소비 (2026-07-25): 화이트리스트가 tx contracts 검증과 함께 삭제 (스텝 2) — 조합 규칙은 learn 지시문 (축4 § C-4) 으로 이관
- [ ] #12 의 transaction nesting Grep 패턴 (`\.transaction\s*do\s*$|ActiveRecord::Base\.transaction|\w+Record\w*\.transaction`) 은 Ruby 전용. Python (`with conn:` / `@transaction.atomic`) · TS (`prisma.$transaction`) 다른 언어는 v0.4.0 multi-language pattern 도입 시 추가 (from #12)
- [ ] #12 inline vs 분리 5 행 임계 (Open Q d-3) 는 SKILL.md 본문 가이드만. 실제 5 행 초과 시 자동 분리 거동은 `/pilot:learn` 실제 호출에서 LLM 이 판단. doctor 는 분리 파일 (`{domain}/transaction-contracts.md`) 도 별도 entry path 추적 안 함 — index.md 만 검증 (분리 파일 = INFO only). 후속 v0.4.0 에서 분리 파일 자동 추적 추가 검토 (from #12)
- [x] #13 의 `pilot/tools/init_detect.py` 는 의존성 0 (Python 표준 라이브러리만) + `(list, list)` / `(dict, list)` tuple 반환 패턴 정착 — 후속 init 확장 (예: `--rewizard` v2, `language` 키 자동 주입) 작성 시 동일 시그니처·info_messages 전달 패턴 재사용 가능 (from #13) — #20 planner 소비 (2026-07-25): init_detect.py 삭제 (스텝 4c, Glob 직접 판단 이관) — 시그니처 재사용 노트 소멸
- [x] #13 wizard 가 채운 `## learn 언어 패턴` 표의 "의존성 추출 패턴" 셀 (예: `from foo import X · import foo.bar`) 출처가 SKILL.md 본문에 명시되지 않음 — `init_detect.py` 는 언어명만 반환하고 패턴 텍스트는 features/01 default 표에서 인용해야 함. #14 (onboarding 가이드) 또는 #07 (analyze SKILL.md 절차) 작성 시 "wizard 가 features/01 default 표의 행 전체를 인용 주입한다" 1 줄 명시 권장 (from #13) — #07 의 5-1.5 본문 blockquote (analyze SKILL.md:226) 에 "wizard 인용 주입 SSOT" 명시로 소비
- [ ] #13 의 Q1 결정 (빈도 ≥ 1) 부작용 — 사용자 저장소에 우연히 `controllers/` 단일 존재 시 자동 매핑됨. SKILL.md `## 결과 출력` 의 "scope 후보: M개 매핑 ({폴더목록})" 줄이 실제 폴더 목록을 노출하므로 사용자가 잘못 매핑 시 수동 정정 가능. #14 onboarding 가이드 작성 시 이 정정 경로 명문화 권장 (from #13)
- [x] #13 의 `wizard/expected/config.md` 회귀 fixture 는 v0.3.0 환경 manual 캡처. `diff.sh --actual {regen}` 실제 1 회 검증은 plan step 7 에 명시됐으나 별도 실행 보류 (회귀 자동 검증은 #00 의 0c PR 와 묶어 일괄 — 기존 미실행 상태와 동일). v0.3.0 합본 PR (Q7) 직전 1 회 수행 필요 (from #13) — #18 planner 소비 (2026-07-24): wizard/ 삭제 승인으로 폐기
- [x] #14 가이드 `## 다음 단계` 절 (pilot/docs/getting-started.md:200·202) 의 features/15·#16 링크가 `../../workspace/projects/build-plugin/features/...` 로 작성됨 — spec line 25 의 "외부 workspace/projects/... 경로 사용 금지 (사용자 환경마다 다름)" 정책 위반. 사용자가 자체 workspace 만든 후 가이드 따라가면 broken link. 후속 hotfix 또는 #15·#16 구현 완료 시 일괄 정정 권고. 대안: (a) `pilot/skills/tdd/SKILL.md`·`pilot/skills/doctor/SKILL.md` 같은 플러그인 내부 상대 경로로 교체 (b) 링크 제거 후 "TDD 모드 전환 (#15 작업 중) · doctor 점검 (#16 작업 중)" 텍스트만 유지 (from #14) — #15 Q10 으로 정정 완료 (line 200: `../skills/tdd/SKILL.md` · line 202: `../skills/doctor/SKILL.md`)
- [ ] #14 가이드의 Step 4 = `/pilot:create-feature` 가 spec line 12-18 의 5-step 정의 (사전준비→init→learn→project→planner) 에는 명시 안 됨. plan line 45 의 의식적 결정 — "planner 진입 전 feature spec 필요 → create-feature 또는 사용자 수동 작성" 으로 step 추가. 사용자 인지 비용으로 step 5 → 6 증가. features/05 dogfooding 실측 시 step 추가가 5분 budget 에 영향 주는지 확인 필요 (from #14)
- [x] #14 가이드 본문의 명령 출력 캡처 (Step 1~5) 는 v0.3.0 시점 SKILL.md 형식. 후속 SKILL.md wording 변경 (예: #06·#07·#08 LOW priority feature 들이 SKILL.md 본문 갱신 시) drift 발생 위험. `golden_output` reference 인프라 (v0.4.0) 도입 전까지 수동 갱신 — `pilot/docs/getting-started.md` 의 출력 코드블록을 SKILL.md 변경 PR 에서 함께 갱신 (from #14) — #21 S1 로 소비 (2026-07-25): #20 이 무효화한 doctor 관련 3곳 (OH-1 ID · config 표 schema 검증 · MANIFEST 헤더 정합성 검사) 삭제 정정. 잔여 출력 캡처는 evaluator 실측상 현행 SKILL.md 형식과 정합 (init `## 결과 출력` 3요소 · learn a/b/c/d 게이트 · create-feature `인터뷰: 해소 N건 / 이월 M건` · project `doctor: all checks passed`)
- [x] #15 의 `check_project` 시그니처는 plan 의 `check_project(project_dir: Path)` 표기와 달리 실제로는 `check_project(workspace: Path, project: str)` 임. plan/spec drift — 의미상 동일 (1 호출자 `integrity.py:1804` 동일 유지) 이지만 후속 plan 에서 함수 인용 시 정확 시그니처 사용 권장 (from #15) — #16 의 OH dispatcher `check_onboarding_health(workspace, project=None)` 가 동일 (workspace, project) 시그니처 패턴 답습
- [ ] #15 의 백업 마커 명명 패턴 (`<!-- pilot-tdd-original-{flow|planner|generator|evaluator}:start --> ... :end -->`) 정착 — 후속 토글성 메타 모드 (예: characterize 모드, snapshot 모드) 도입 시 동일 인라인 마커 패턴 + 3-way doctor 룰 답습 권장. `integrity.py:556-569` 의 prompts loop 가 재사용 reference (from #15)
- [x] #15 fixture `tdd-on/expected/` 의 prompts/*.md 캡처는 백업 마커가 **빈 쌍** (`<!-- ...:start -->\n<!-- ...:end -->`) 상태 — 즉 신규 프로젝트가 `--tdd` 로 시작해 표준 본문 부재 시 빈 마커만 남는 합리적 거동. 기존 프로젝트가 `/pilot:tdd on` 시는 prompts 표준 본문이 마커 안에 들어감 — fixture 가 이 두 케이스 중 전자만 캡처. 후속 fixture 확장 시 후자 (기존 프로젝트 on 케이스) 도 추가 권장 (from #15) — #18 planner 소비 (2026-07-24): tdd-on/·tdd-off/ 삭제 승인으로 폐기
- [x] #15 `pilot/skills/doctor/SKILL.md` 본문은 spec line 62-63 의 "tdd 3-way 일치 룰 추가 + --fix 시 /pilot:tdd --fix 위임" 명시가 plan 변경 파일 목록에 누락. 실제 doctor 본체 (`integrity.py`) 는 3-way 검증 추가됐으나 SKILL.md 본문은 미수정 — 후속 doctor 룰 추가 시 (#16 onboarding-health) doctor SKILL.md 본문 갱신과 함께 일괄 처리 권장 (from #15) — #16 Q5 로 정확 소비. SKILL.md line 77 본문 + line 126 [PASS] 예시 3-way wording 적용
- [x] #16 의 `run_integrity_check` (integrity.py) 는 (a) 활성 프로젝트 있음 분기 (line 2047~) (b) 활성 프로젝트 없음 early return 분기 (line 2017~) 두 경로에서 OH 섹션 출력을 중복 (DRY 위반) — 후속 룰 추가 시 두 경로 모두 갱신 필요. v0.4.0 milestone 에서 OH 출력 함수 추출 (예: `_print_onboarding_health(workspace, project, fix)`) 권장 (from #16) — **cleanup PR 에서 `_print_onboarding_health_section` 헬퍼 추출 완료**
- [x] #16 fixture `pass-only/` 의 `.agent-state.yml` 부재 — 의도적 ERROR 1건 (`sample-project/.agent-state.yml: 없음`) 발생. 본 fixture 의 "pass-only" 의미는 "OH 섹션 5건 PASS" 한정. 후속 fixture 확장 시 `.agent-state.yml` 도 추가 캡처해 전체 ERROR 0 으로 정돈하거나, fixture 이름을 `oh-pass-only/` 등으로 명시화 검토 (from #16) — **cleanup PR 에서 `.agent-state.yml` 추가 + doctor-output 재캡처 (14 PASS · 0 WARN · 0 ERROR)**
- [x] #16 `--fix` 호출 시 `[--fix] 자동 수정 대상 없음.` 메시지 가 OH skip INFO 1줄과 인접 출력. 후속 doctor 출력 정돈 시 두 줄을 통합 또는 위치 조정 검토 (run_auto_fixes 가 결과 0건일 때 silent 가 적절한지 재검토 — 현재는 항상 1줄 발화) (from #16) — **cleanup PR 에서 `run_auto_fixes` 대상 0건 시 silent 처리**
- [x] #06 SKILL.md 본문이 인용한 정규식 `^##\s+도메인\s*분류\s*$` (anchor + `\s+`) 와 `orchestrate-load.py:264` 의 실제 정규식 `##\s*도메인\s*분류` (anchor 없음 + `\s*`, `re.search`) 가 wording drift. 현재 MANIFEST 에서는 prose 매칭 후에도 표 행 매칭이 우선 동작해 false positive 0 — 그러나 SKILL.md 가 약속한 "본문 prose 의 동일 string 등장 무시" 거동은 코드에 미구현. 후속 보강 옵션: (a) `parse_manifest_domain_files` 정규식을 `re.search(r"^##\s+도메인\s*분류\s*$", text, re.M)` 로 강화 + 첫 매칭 후 다음 H2 까지 section 추출 (b) `_parse_md_tables_in_section` 의 코드블록 펜스 추적 헬퍼 (integrity.py:807·811-820) 를 orchestrate-load 로 재사용 (from #06) — #20 planner 소비 (2026-07-25): **실버그 전이 확인** (현행 MANIFEST 상단 blockquote prose 선매칭 → 파서 빈 리스트 실측, wrapper 세션 도메인 진입 파일 로드 누락) — 옵션 (a) anchored 정규식으로 스텝 6 수정 (D1 승인)
- [x] #06 plan 의 공통-2 (PR 단위 = #06·#07·#08 일괄 단일 PR `docs: pilot SKILL.md wording 명확화`) 가 본 #06 완료 시점에는 commit·PR 미생성 상태. #07·#08 generator 완료 후 3 features 묶어 단일 PR 추진 권장 — 본 SKILL.md 7 라인 변경 단독 PR 금지 (LOW priority 합본 정책) (from #06) — v0.9.0 릴리스로 해소 (2026-07-24 사용자 확인)
- [ ] #06 의 H2 정확 매칭 wording 패턴 (`^##\s+{헤더}\s*$` 정규식 인용 + 본문 prose 동일 string 무시 + 코드블록 펜스 무시 blockquote) — #09·#10 의 `## 외부 도메인 reference` 섹션 detect, #07 의 analyze 5-1.5 가 생성하는 scope 카테고리 H2 detect 등 후속 H2 정확 매칭이 필요한 SKILL.md 본문에 동일 wording 답습 가능 (from #06)
- [ ] #07 의 5-1.5 본문이 (a) 트리거 조건 (scope 부재 + MANIFEST H2 헤더 존재) (b) 본문 추출 우선순위 3단 (inventory.md → index.md → 빈 표 + INFO) (c) idempotency (기존 파일 보존 + 사용자 수동 행 보존) (d) A2 runtime fallback (abort 없이 빈 표 + INFO + 5-2 진행) (e) 예외 4건 (MANIFEST 부재 / config 빈 표 / inventory.md 부재 / scope 헤더 prefix 위반) 명시 패턴 정착 — #08 의 `/pilot:project` `{프로젝트명}` 치환 범위 명문화에서 동일 wording 답습 가능 (from #07)
- [ ] #07 의 wizard 인용 주입 SSOT blockquote (analyze SKILL.md:226) — `/pilot:init` wizard 산출 ↔ inventory.md 산출 형식 ↔ scope 헤더 ↔ project.md `## 관련 파일` 표의 SSOT 흐름 명문화. 후속 SKILL.md 본문에서 wizard 산출 인용 시 동일 blockquote 형식 (`> **wizard 인용 주입 SSOT** — ...`) 재사용 권장 (from #07)
- [x] #07 의 `pilot/docs/getting-started.md` analyze 출력 코드블록 drift 점검 (인수인계 line 128) 은 plan step 4 에서 "출력 변화 없으면 그대로" 결정. 본 PR 머지 후 실 `/pilot:analyze` 1 회 실행 결과가 5-1.5 신설로 stderr `[INFO]` 1 줄 추가될 가능성 — 실제 분기 진입 시 (scope 부재 + MANIFEST 헤더 존재) 만 발화. getting-started.md 본문 출력 코드블록은 happy path 가정이라 영향 0 으로 잠정 판단. v0.3.0 합본 PR 머지 후 실 호출 1 회로 재확인 권장 (from #07) — #21 무변경 확인으로 소비 (2026-07-25): 현행 `docs/tutorial/getting-started.md` 에 analyze 출력 코드블록 자체가 없음 (grep 0건) — drift 표면 0
- [ ] #08 의 치환 범위 blockquote 본문 (project SKILL.md:65-80) — list item 안 nested blockquote (2 spaces 들여쓰기) 패턴 정착. 후속 SKILL.md 본문에 같은 list item 안 다단 blockquote 추가 시 동일 들여쓰기 + 빈 라인 분리 (`  >`·`  >` 사이 `  >`) 답습 권장. project SKILL.md 의 H3 동적 채움 blockquote (line 88~) 와 자연스럽게 공존 (from #08)
- [x] #08 plan 의 공통-2 (PR 단위 = #06·#07·#08 일괄 단일 PR `docs: pilot SKILL.md wording 명확화`) — 본 #08 완료 시점에 commit·PR 미생성. #06·#07·#08 generator 완료분 묶어 단일 PR 추진 필요 (LOW priority 합본 정책). v0.3.0 합본 PR (Q7) 와 별개 가능 (LOW 3 건은 코드 변경 없음·회귀 영향 없음) (from #08) — v0.9.0 릴리스로 해소 (2026-07-24 사용자 확인)
- [ ] #08 의 H1 단순화 정규식 채택 (Q3 — `^#\s+.*\{프로젝트명\}.*$`) — prompts/*.md 의 `# Planner — {프로젝트명}` 같은 콜론·대시 구분자 H1 형식 매칭 가능. spec line 36 의 2 옵션 (정확 매칭 vs 단순화) 중 단순화 답습. 후속 SKILL.md 본문에 H1 토큰 치환 패턴 추가 시 동일 정규식 형태 재사용 가능 (from #08)
- [x] #08 의 `pilot/docs/getting-started.md` project 출력 코드블록 drift 점검 (인수인계 line 128) 은 plan step 3 에서 "치환 절차 wording 변경이 출력 형식 깨지 않는 한 변화 없음" 결정. blockquote 추가 → SKILL.md 본문 한정 (사용자 출력 미관여) → getting-started.md 영향 0 으로 잠정. v0.3.0 합본 PR 머지 후 실 `/pilot:project` 1 회 호출로 재확인 (from #08) — #21 무변경 확인으로 소비 (2026-07-25): Step 3 출력의 `doctor: all checks passed` 1줄이 현행 임베디드 호출 출력 규칙 (`doctor/SKILL.md` § 임베디드 호출 시 출력 규칙) 과 일치
- [x] `workspace/context/pilot/spec.md` stale (drift-protocol A 보고, #17 plan 주의사항 예고분) — analyze "8 단계 프로세스" (spec.md:58-66) 에 7.5 (조건부 인터뷰) 부재 + step 8 인용 `SKILL.md:242-263` 어긋남 (실제 191-193), create-feature 단계 기술 (spec.md:71-98) 에 3-bis·3-ter 부재 + 라인 인용 shift (+17줄). `/pilot:learn` 재실행 또는 drift-protocol 승인 하 갱신 필요 — 직접 Edit 금지 준수 (from #17) — 해소 확인 (2026-07-24, #18 planner): 커밋 418868a 재학습으로 spec.md:66 (7.5)·:96 (3-ter) 반영 완료
- [ ] open-questions.md (작성 SSOT) ↔ interview.md (소비 SSOT) 짝 패턴 정착 — 후속 feature 가 Open Questions 행 형식·카테고리를 변경하면 interview.md 행 파싱 규칙 (`- [ ] ` prefix 판정 · 마지막 `→` 뒤 = 답변 요약) 과 scope-sync.md 5-2 규칙 2 (중복 판정 키 = 외부 도메인명) 3곳 동시 동기화 필요 (from #17)
- [x] `docs_build.py` 에 `cleanup_stale_outputs(root, files)` 추가됨 (write 경로 전용·빈 카테고리 가드·`--check` 불변) → #20 의 "docs_build 이관 부적합·무변경" 판정 기준은 #18 이후 상태 — 함수 제거 금지 (from #18) — #20 planner 소비 (2026-07-25): docs_build.py 무변경·cleanup_stale_outputs 보존을 plan 주의사항에 명시 (스텝 7 은 재생성 실행만)
- [x] `doctor/SKILL.md:46` "CI 연동은 #20 에서 `validate.yml` 신설 예정 — 현재는 수동 실행" 문구 → #20 에서 validate.yml 신설 시 동일 커밋으로 재갱신 필요 (from #18) — #20 planner 소비 (2026-07-25): 스텝 7 에서 validate.yml 신설 + doctor SKILL (:36 현행) 동일 커밋 재갱신 반영
- [x] `v0.1.0-baseline/migration/` 픽스처 + `test_doctor_migration.py` 는 #20 마이그레이션 코드 삭제 시 함께 정리 (baseline README.md 표에도 보존 기한 명시됨) (from #18) — #20 planner 소비 (2026-07-25): 스텝 1 에서 migration 픽스처·test_doctor_migration.py 동일 커밋 정리 + baseline README 갱신 반영
- [x] #19 이월분 (plan 교차 의존 명시): A-1~A-16 중복 통합 전체 · B-6 부수 (preamble P1 `workspace_missing` 케이스 보강) · B-7 부수 (preamble 적용표 code-review-init·review 행) · A-12 완전 통합 · A-6 tdd Detect literal 참조화. `context/INDEX.md` 는 #19 재작성 대상 — #18 정정은 최소 문구만 반영된 상태 (from #18) — #19 planner 소비 (2026-07-24): 전 항목 plan 반영 (스텝 1 = B-6·B-7 부수 + A-12 완전 통합 + INDEX 재작성, 스텝 2-c = A-6, 스텝 1~3 분산 = A-1~A-16 통합) — #19 evaluator 검증 완료 (2026-07-25): 전 항목 구현 실재 확인
- [ ] `workspace/context/pilot/spec.md`·`index.md` 의 SKILL.md 라인 인용은 #19 재작성으로 전면 stale — PR 머지 후 `/pilot:learn` 재실행으로 재학습 (커밋 418868a 선례, drift-protocol § A 직접 Edit 금지). `prompts/*.md` analyze-managed 라인 인용도 stale — 다음 `/pilot:analyze --regen-agents` 가 재정렬 (from #19)
- [x] `wrapper-protocol.md` (A-2 정본) 는 orchestrate-load `files_to_read` 에 미배선 — 각 wrapper 본문의 "Read 지시 1줄" (잔류 최소 셋 ④) 이 유일한 도달 경로 (critic C2 합의). #20 에서 orchestrate-load.py 수정 시 files_to_read 배선 추가로 이중화 검토 (from #19) — #20 planner 소비 (2026-07-25): D2 승인 — 스텝 6-③ 에서 4 phase 공통 files_to_read 배선 확정
- [ ] **[R-3 알려진 잔존 모순]** 신규 `pilot/docs/how-to/doctor-migration.md` ("doctor 는 `--fix` 없이도 `.gitignore` 를 수정 · `--fix` 는 확인 없이 즉시 적용" — 실측 참) ↔ `pilot/docs/reference/skills/doctor.md:71-72` ("검사는 **비파괴** — 읽기만 함, 파일 수정 안 함" · "fix 제안은 출력하되 자동 적용 안 함") 가 같은 docs 사이트에 공존. 후자는 `pilot/skills/doctor/SKILL.md:79-80` 의 `docs_build.py` 파생물이고 SKILL.md 는 #21 spec 비즈니스 규칙상 범위 밖이라 이번에 못 고침. **후속 feature 로 `SKILL.md:34`(`--fix` 설명에 `.gitignore` 주입이 섞임 — 실제로는 `--fix` 무관 무조건 실행) 와 한 건으로 묶어 처리** → 수정 후 `docs_build.py` 재생성으로 reference 페이지 동기화 (from #21)
- [x] `20-consolidation-slim.plan.md:78` 의 판정 범위 축소 blockquote 에 D-1 (a) 기각 사유가 구버전("마켓플레이스가 GitHub 클론이라 캐시 갱신에 머지·배포 선행 필요")으로 잔존 — critic C9 가 정정한 실사유(사용자 전역 설치본 변조 부적절 + 세션 중 플러그인 리로드 불가)는 `21-*.plan.md` § D-1 에만 반영됨. 배포 후 실경로 재확인 담당자가 "배포만 되면 자동 해소" 로 오해할 위험 → #20 재확인 착수 시 문구 정정 필요 (from #21) — **#20 evaluator 정정 완료 (2026-07-25, drift-protocol § B)**: 잔존 확인 후 해당 문장을 critic C9 정정본(① 전역 설치본 변조 부적절 ② 세션 중 리로드 불가로 실경로 재현 불성립)으로 교체 + "후속 확인 필요" 항목에 5단계 절차(머지→배포→`pilot-update.sh`→세션 재시작→(b) 재측정) 명시. "배포만 되면 자동 해소가 아니다" 문구 추가
- [ ] `pilot/docs/reference/{agents,skills,tools}/` 는 `pilot/.gitignore:10` 로 **git 미추적** — `docs_build.py` 재생성 여부는 `git diff`·커밋 diffstat 로 증명 불가하고 **현재 파일 상태 + `--check` exit code** 로만 확인된다. 후속 evaluator 가 "docs 재생성 실행" 류 항목을 판정할 때 커밋 증거를 요구하면 오탐 — 상태 기반 증거(생성 페이지 목록 ↔ 소스 실재 목록 일치)로 대체할 것 (from #20)
- [ ] **#20 dogfooding 체크 조건** — `project.md` `## 목표` 의 #20 은 `[ ]` 가 정상 상태 (미완 누락 아님). 체크 조건 = 배포 후 **설치 캐시 실경로** 1사이클 검증. 절차 5단계: ① PR 머지 → ② 배포 → ③ `/plugin marketplace update radiostart-plugins` + `/plugin update pilot@radiostart-plugins` (#24 로 `pilot-update.sh` 삭제됨) → ④ **세션 재시작** (세션 중 플러그인 리로드 불가) → ⑤ 실경로에서 G7 기대값 재측정 (`files_to_read` 에 `wrapper-protocol.md`·`context/pilot/index.md` 실재 + 미등록 힌트 부재) (from #21)
- [ ] `pilot/docs/PLAN-manual.md:264` — `schema 버전 감지 → migration 경로 (v1.0→v1.1→v1.2)` 표기가 실제 라벨(`v1`·`v1.1`·`v1.2`) + 직접 bump 거동과 불일치. `PLAN-manual.md` 는 mkdocs 제외 메타 산출물이라 #21 spec 범위 외 — 메타 산출물 갱신 시 함께 정정 (from #21)
- [ ] **#24 로 `pilot/tools/pilot-update.sh` 는 삭제됨** — 지원 업그레이드 경로는 `/plugin marketplace update radiostart-plugins` → `/plugin update pilot@radiostart-plugins` → **세션 재시작** 하나뿐이다. `prompts/evaluator.md:24`·`:39` 와 `prompts/generator.md:50` · `prompts/planner.md:140-147` 의 `pilot-update.sh` 언급은 `[analyze-managed]` 영역이라 미수정 상태로 stale — **문자 그대로 실행하지 말 것**. 다음 `/pilot:analyze --regen-agents` 가 재정렬한다 (from #24)
- [ ] **v0.10.0 GitHub Release 노트의 `## 업그레이드` 블록이 여전히 `pilot-update.sh` 를 지시 중** — #24 에서 저장소 밖 상태 변경이라 범위 분리했다 (사용자 명시 승인 시 처리). 절차는 `features/24-pilot-update-tool.plan.md` 스텝 2: ① `gh release view pilot-v0.10.0 --json body -q .body > 백업` (`gh release view` 무플래그 출력은 메타 8줄이 섞이므로 입력 금지) → ② `## 업그레이드` 블록만 교체 → ③ `gh release edit --notes-file` → ④ `--json body` 재취득 후 백업과 diff 해 **해당 블록 외 byte 동일** 확인 (from #24) — **#24 evaluator 판정 (2026-07-26)**: 이 항목은 "선택적 후속" 이 아니라 **#24 의 마지막 미충족 요구사항**이다 (spec 기대결과 (C) 가 열거한 4곳 중 1곳). 실측상 노트 본문에 삭제된 `pilot/tools/pilot-update.sh` 지시가 그대로 살아 있고, `gh api …/releases/tags/pilot-v0.10.0` → `immutable: false` 로 **기술적 차단도 없다**. plan D2(사용자 승인 2026-07-25)는 "정정한다" 였으므로, 유예하려면 사용자의 **명시 범위 제외 승인**을 이 행에 기록해야 한다. 둘 중 하나가 끝나야 `## 목표` 의 #24 를 `[x]` 로 올린다 — **해소 완료 (2026-07-26)**: 사용자 명시 승인(`수정 실행`) 후 plan 스텝 2 4단계 실행. 백업 md5 `bda2a46…` → 교체 → `gh release edit --notes-file` → `--json body` 재취득 diff 가 `## 업그레이드` 블록 + 말미 개행 1줄에만 국한됨을 확인. 새 본문은 `/plugin` 2단계 + 정정 사유 blockquote. `## 목표` #24 `[x]` 처리
- [ ] **`doctor --schema` 와 `claude plugin validate --strict` 는 서로 대체하지 않는다** (#25 결론 (ii) 현행 유지, 2026-07-26 실측). CLI 만 잡는 것 = `plugin.json` 미지 키. `schema.py` 만 잡는 것 = SKILL `description` 바이트 상한 · version↔git tag. **JSON 문법 파손은 양쪽 다 잡는다** — 최초 서술이 이를 "CLI 만" 으로 적었던 것은 2026-07-25 구표의 "(문법 파손은 미검증)" 을 "미탐" 으로 오독한 결과이며, code-review blocking 지적으로 정정됐다 (미검증을 실측으로 단정하지 말 것). CI(`validate.yml`)는 러너 CLI 설치·인증이 필요 없는 `doctor --schema` 단독 유지이고, CLI 는 릴리스 전 로컬 보조 수단으로 `pilot/README.md` 에 문서화됐다. **`schema.py` 를 CLI 로 대체하자는 제안이 다시 올라오면 이 표를 먼저 볼 것** (from #25). `prompts/planner.md:155` 와 `features/25-*.md:21`·`:29` 는 정정 전 서술("CLI 만 잡는 것 = JSON 문법 파손") 이 남아 있다 — 전자는 `[analyze-managed]` 영역이라 미수정(다음 `--regen-agents` 가 재정렬), 후자는 구표 기록이라 대체 표시만 달았다 (from #25)
- [ ] **[#20 dogfooding 게이트 해소 — 위 `#20 dogfooding 체크 조건` 항목은 소화됨]** 2026-07-26 #23 사이클이 설치 캐시 실경로 `~/.claude/plugins/cache/radiostart-plugins/pilot/0.10.0` 에서 planner→generator→evaluator 완주. 판정 (a) 삭제 스크립트 4종 호출 0건 · (b) `files_to_read` 에 `wrapper-protocol.md`·`context/pilot/index.md` 실재 + 미등록 힌트 부재 — 3구간 전건 충족으로 `project.md` #20 목표 `[x]` 처리. 후속 사이클은 이 게이트를 다시 판정할 필요 없다 (from #23)
- [ ] `is_feature_spec_file(p)` 가 `pilot/tools/doctor/_common.py:197` 에 신설 — "features/ 의 `*.md` 중 stem 에 `.` 이 있으면 파생 산출물" 이 **파생 판정 SSOT**. 새 파생 접미사(`.plan.review.md` 등)를 추가해도 파서 수정 불필요. **알려진 경계** = spec 파일명 stem 에 점을 쓰면(`05-v1.0-release.md`) 미카운트 — `test_doctor_features_count.py::DottedSpecStemNotCounted` 가 고정. features 명명 규약을 바꾸는 후속 feature 는 이 테스트를 먼저 확인할 것 (from #23)
- [ ] **orchestrate-load placeholder leak (후속 feature 대상)** — `parse_lang_config` (`pilot/tools/orchestrate-load.py:141-172`) 가 config.md 같은 표를 파싱하며 `test_framework_hints=자유 텍스트` 같은 **플레이스홀더를 실값으로 반환** (#23 evaluator step 1 반환 JSON 에서 재실측: `config: {"test_framework_hints": "자유 텍스트"}`). 성격은 #23 (A) 와 동일하나 wrapper hints 출력이 바뀌므로 별건 — #23 이 만든 구조 기반 판정(`integrity.py:_extract_declared_path`)을 재사용해 해소 가능 (from #23)
