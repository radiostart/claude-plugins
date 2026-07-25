# 구현 계획: #20 정비 slim — Python 슬림화

> 모드: standard (tdd: false, mode: null) · 작성: 2026-07-25 planner
> 근거 SSOT: `docs/audits/2026-07-24-audit-4-python.md` (분류표 § A · integrity 상세 § B · 대체 지시문 초안 § C · 테스트 절감 § D) + feature spec 승인 결정 (schema.py 유지 + validate.yml CI 신설 · 이관 부적합 6종 무변경)
> 원칙: 이관 대상 4개 스크립트는 전부 **살아있는 호출처가 있다** — 삭제는 호출처 문서 대체와 **동일 커밋**. 스크립트-테스트 삭제도 동일 커밋, 커밋마다 pytest 전체 통과 (spec 비즈니스 규칙).
> **실측 발견 (2026-07-25 planner)**: #06 전달사항의 MANIFEST 정규식 drift 가 **실버그로 전이** — 현행 MANIFEST 상단 blockquote prose 의 `## 도메인 분류` 문자열을 anchor 없는 `re.search` 가 먼저 매칭해 `parse_manifest_domain_files` 가 빈 리스트 반환 (재현: 본 세션 orchestrate-load 가 pilot 행 실재에도 "진입 파일 미등록" 힌트 + `context/pilot/index.md` 로드 누락). 스텝 6 에서 수정.
> **승인 기록 (2026-07-25)**: D1~D5 전건 권고안대로 사용자 승인 (메인 대화 중계) — 하단 `### 사용자 결정 (승인됨 2026-07-25)` 참조. #20 관련 전달사항 12건 project.md `[x]` + 소비 사유 부기 완료, 무관 19건은 D4 승인대로 unchecked 이월.
> **critic 합의 반영 (2026-07-25, `.plan.critic.md` C1~C9 전건 accepted)**: C1 doctor.py 명시 import 제거를 심볼 삭제와 동일 커밋으로 분할 재배치 (커밋 1·2·3·4a). C2 OH 삭제 범위 실측 경계 정정 (:1848-2068 + :2135-2160, `run_integrity_check` :2075-2133 보존). C3 **사용자 재결정** — 총량 게이트를 절대치 (절감 ≥2,100줄) 로 전환, 측정식·분모 고정, 감축률 ≈29.5~30% 정직 기재. C4 펜스 코드블록 strip 추가. C5 suffix 변형 non-match 문서화 테스트 + 힌트 문구 정정 안내. C6 OH 대체 문안에 발동 조건·5항목·처방 명시 + 임베디드 nudge 소실 의도 기록. C7 lint 삭제 참조 잔재 2건 (scope-sync.md:58 · integrity.py:895) 스텝 2 동일 커밋 처리. C8 dogfooding 완주 판정을 채증 가능 2건으로 교체. C9 nit 3건 반영 (아래 각 위치).

### 변경 파일

**스크립트 삭제 (이관 3종 + 흡수 1종 + 사용자 문서 1종)**

- [x] `pilot/tools/doctor/diagnose.py` — 삭제 (181줄. 휴리스틱 패턴 매칭 → doctor SKILL 지시문 진단으로 이관, 축4 § C-6) — 커밋 4a (34a1ed8)
- [x] `pilot/tools/memory-hint.py` — 삭제 (176줄. 키워드 점수 선별 → preamble P0 "MEMORY.md 색인 직접 선별 Read" 로 이관, § C-7) — 커밋 4b (cb37dd0)
- [x] `pilot/tools/init_detect.py` — 삭제 (279줄. 확장자 빈도·폴더 감지 → init SKILL Glob 직접 판단 지시로 이관, § C-8) — 커밋 4c (4796ca5)
- [x] `pilot/tools/verify-report-lint.py` — 삭제 (372줄. validate()+렌더+CLI 폐기, 파서 2함수 `extract_report_block`·`parse_report` 만 auto_pilot.py 로 흡수, § C-5) — 커밋 5 (86e0fba)
- [x] `pilot/skills/doctor/references/migration.md` — 삭제 (마이그레이션 코드 삭제와 동일 커밋 — 죽은 참조 방지) — 커밋 1 (bb4f222)

**스크립트 변경**

- [x] `pilot/tools/doctor/integrity.py` — 2,160 → 995줄 (계획 대비 초과 절감):
  - 삭제 (시효 만료): `_is_learn_section_empty`·`_has_partial_learn_definition`·`_inject_v010_defaults_into_config`·`migrate_v0_1_to_v0_2` (:1600-1845, 246줄) + `run_integrity_check` 내 호출 (:2123) — 커밋 1 (bb4f222)
  - 삭제 (md 표 lint 4종 이관): `check_workspace_config_sections` (:938-1171) + 호출 (:412) · `check_workspace_external_domain_section` (:1174-1314) + 호출 (:397) · `check_features_open_questions` (:1317-1372) + 호출 (:779) · `_parse_md_tables_in_h3_section`+`_TX_TYPE_WHITELIST`+`check_domain_transaction_contracts` (:1379-1589) + 호출 (:2092) — 커밋 2 (f77f7d5)
  - 삭제 (OH 축소, critic C2 실측 경계): OH-1~5 헬퍼 + dispatcher `check_onboarding_health` (:1848-2068) + `_print_onboarding_health_section` (:2135-2160). **`run_integrity_check` (:2075-2133) 는 보존** — 내부 OH print 호출 2줄만 제거 — 커밋 3 (ffc1836)
  - 문구 교체: `check_auto_memory_presence` 의 memory-hint 안내 → P0 신문안 동기화 — 커밋 4b (cb37dd0)
  - 주석 정리 (critic C7-b): `check_conventions_paths` 내부 위임 주석 → 자체 WARN 1건으로 교체 — 커밋 2 (f77f7d5)
  - **보존 확인**: `_parse_md_tables_in_section`(`check_conventions_paths` 잔존 소비 실측), auto-fix 3종, credential/Slack secret, `check_workspace`·`check_project`·`run_integrity_check` 전부 무변경 보존
- [x] `pilot/tools/doctor.py` — 163 → 77줄. `--diagnose` 플래그·diagnose import 블록 삭제, backward-compat re-export 블록 정리(기능상 필요한 심볼만 유지 — 잔존 테스트 2건은 패키지 직접 로드로 전환). `--schema`·`--fix`·default 모드 유지. 심볼 삭제-동일 커밋 분할(critic C1) 그대로 수행: 커밋 1(bb4f222)=migration 4심볼 / 커밋 2(f77f7d5)=lint 5심볼 / 커밋 3(ffc1836)=OH심볼+잔여 블록 전체 정리+테스트 로드 전환 / 커밋 4a(34a1ed8)=diagnose 블록
- [x] `pilot/tools/doctor/__init__.py` — docstring diagnose 행 제거 + backward-compat 문단 정정(critic C9-a) — 커밋 4a (34a1ed8)
- [x] `pilot/tools/auto_pilot.py` — 193 → 311줄 (`extract_report_block`·`parse_report` 원문 이식), `_load_report_lint` 동적 로드 제거. CLI 계약(`--report-file`) 스모크 테스트로 불변 확인 — 커밋 5 (86e0fba)
- [x] `pilot/tools/orchestrate-load.py` — ① `parse_manifest_domain_files` H2 anchored 매칭 + 펜스 코드블록 strip — learn SKILL.md:80 "코드블록·prose 인용 무시" 완전 구현 (실버그 수정 확인 — 본 workspace 재현 테스트 통과, D1 승인 + critic C4). suffix 변형 미매칭 힌트에 정정 안내 포함(critic C5-b) ② `parse_state_yml`·`parse_semver` 를 `doctor/_common.py` 와 dedup ③ wrapper-protocol.md files_to_read 배선(D2 승인) — 커밋 6 (3262feb). 순 라인 수는 신규 펜스-strip 헬퍼·확장 docstring·신규 테스트로 상쇄되어 762→762 (0 순감, 실측 54 삭제/54 추가) — 정확성 우선, 총량은 다른 파일 절감분으로 게이트 충족

**지시문 대체 (이관 삭제와 동일 커밋)**

- [x] `pilot/skills/doctor/SKILL.md` — diagnose.py SSOT 언급 정리 · `--fix` 마이그레이션 문구+migration.md 링크 제거 · `--diagnose` 를 지시문 진단(§ 진단 모드 신설: loop/red-miss/repeat-not-ready/scope-violation 4패턴 + `## DIAGNOSIS` 블록)으로 교체 · validate.yml 신설 반영 재갱신(동일 커밋 7, adf85db) · OH 대체 문단(critic C6 등가성 요건 3종 전부 명시) — 커밋 1/3/4a/7 분산 (bb4f222/ffc1836/34a1ed8/adf85db)
- [x] `pilot/skills/analyze/references/scope-sync.md` — "doctor 검증이 사전 차단" 문구를 A2 fallback 서술로 교체(critic C7-a) — 커밋 2 (f77f7d5)
- [x] `pilot/skills/init/SKILL.md` — "doctor strict 검증" 을 모델 자기 검증 문안으로 재작성(§ C-1) — 커밋 2 (f77f7d5) · `init_detect.py` 함수 호출 2건을 Glob 기반 직접 판단 지시로 교체(§ C-8, 동일 판정 기준 유지) — 커밋 4c (4796ca5)
- [x] `pilot/skills/context/shared/preamble.md` — P0 정의부를 "MEMORY.md 색인에서 직접 선별 Read" 로 교체 (Read-only 원칙·stale 재확인 문구 보존) — 커밋 4b (cb37dd0)
- [x] `pilot/skills/project/SKILL.md`(:21)·`pilot/skills/issue/SKILL.md`(:22) — "memory-hint 실행" 표현을 P0 신문안 정합으로 갱신 — 커밋 4b (cb37dd0)
- [x] `pilot/skills/learn/SKILL.md` + `references/cross-domain.md` — § C-2·§ C-4 대조 완료 — #19 재작성본에 이미 존재(cross-domain.md:64,73-76 멱등·:60 화이트리스트) 확인, **무변경** (critic 검증 통과 축과 일치)
- [x] `pilot/skills/create-feature/SKILL.md` 또는 `shared/open-questions.md` — § C-3 대조 완료 — create-feature SKILL.md:36 에 기존재 확인, **무변경**
- [x] `pilot/agents/pilot-evaluator.md` — § C-5: REPORT 출력 직전 형식 자기 점검 1줄 (status 값·gates 6개 키 — 실측 정정, 계획의 "5종" 은 drift 포함 누락 표기였음) 기존 :54 문구에 통합 — 커밋 5 (86e0fba)

**CI 신설**

- [x] `.github/workflows/validate.yml` — `python3 pilot/tools/doctor.py --schema` 실행 워크플로 신설(tests.yml 패턴 답습, trigger paths 계획대로, concurrency 그룹 분리) — 커밋 7 (adf85db). YAML 구문 검증 + `--schema` 로컬 실행(6 PASS·0 WARN·0 ERROR) 확인

**테스트·픽스처 (대상 스크립트와 동일 커밋 삭제)**

- [x] 삭제 9파일 (1,433줄 실측 합 — critic C9-b 정정): `test_doctor_migration.py`(278)·`test_doctor_integrity.py`(136)·`test_doctor_external_domain.py`(135)·`test_doctor_cross_domain.py`(97)·`test_doctor_open_questions.py`(107)·`test_doctor_cross_domain_transaction.py`(154)·`test_init_detect.py`(192)·`test_memory_hint.py`(137)·`test_verify_report_lint.py`(197 — 파서 케이스는 test_auto_pilot.py 로 이동 후 삭제, D5 승인됨) — 커밋 1/2/4b/4c/5 분산
- [x] 삭제 픽스처: `pilot/tests/fixtures/v0.1.0-baseline/{config,external-domain,migration,open-questions,transaction-contracts}/` (소비 테스트와 동일 커밋. `_input/` 은 튜토리얼 더미용 보존 — #18 critic C1 재결정) · `verify-reports/` 전량(파서 테스트가 fixture 미소비 실측 — 전량이 validate 전용분) — 커밋 1/2/5
- [x] `pilot/tests/fixtures/v0.1.0-baseline/README.md` — 보존 표에서 삭제 5종 제거, `_input/` 설명만 잔존 (#18 전달사항 :154 의 "보존 기한 명시" 소화) — 커밋 1/2
- [x] `pilot/tests/tools/test_auto_pilot.py` — 파서 2함수 테스트 6건 흡수 + `_load_report_lint` 제거 반영 — 커밋 5 (86e0fba)
- [x] `pilot/tests/tools/test_orchestrate_load.py` — 정규식 강화·dedup·배선 반영 + 신규 케이스 5건: ① prose-선행 MANIFEST 실버그 재현 ② 펜스 코드블록-선행 변형(critic C4) ③ suffix 변형 의도된 non-match 문서화(critic C5-a) ④⑤ wrapper-protocol.md 로드 확인 2건 — 커밋 6 (3262feb)
- [x] `pilot/tests/tools/test_doctor_conventions.py`·`test_doctor_slack.py` — `doctor.integrity` 패키지 직접 로드로 전환 — 커밋 3 (ffc1836)
- [x] `pilot/docs/reference/**` — docs_build 재생성 실행(`docs_build.py` 자체 무변경, cleanup_stale_outputs 가 3개 stale 페이지 자동 정리) + `--check` 통과 확인 — 커밋 7 (adf85db)

### 구현 순서

1. **마이그레이션 삭제** (커밋 1) — integrity.py :1600-1845 + 호출 (:2123) + **doctor.py migration 4 심볼 import 제거 (:61·:64-66·:83 — critic C1, 명시 import 라 미제거 시 즉시 ImportError)** + `references/migration.md` + doctor SKILL :34 문구 + `fixtures/migration/` + `test_doctor_migration.py` 를 한 커밋으로. `migration_v0_2_0` 잔존 언급 grep (state-schema.md 등) — 있으면 함께 정리. 게이트: `python3 -m unittest discover -s tests/tools` (pilot CWD) 전체 통과.
2. **md 표 lint 4종 이관** (커밋 2) — lint 함수 4종+헬퍼(H3)+화이트리스트+호출부 삭제 + **doctor.py lint 5 심볼 import 제거 (:68·:73-74·:80-81 — critic C1)** ↔ 대체 지시문 (init :37 재작성 · learn/cross-domain.md·create-feature/open-questions.md 대조 보강) 동일 커밋. **참조 잔재 2건 동일 커밋 처리 (critic C7)**: scope-sync.md:58 "doctor 사전 차단" → A2 fallback 서술 · integrity.py:895 위임 주석 → 자체 WARN. 연동 테스트 5파일 (`integrity`·`external_domain`·`cross_domain`·`open_questions`·`cross_domain_transaction`) + 픽스처 4종 삭제 + baseline README 갱신. `_parse_md_tables_in_section` 은 보존 (conventions :896 소비). 게이트: pytest + `doctor.py workspace` 실행 (출력에 삭제 검사 잔재 0).
3. **OH 축소 + doctor.py 슬림** (커밋 3) — OH 삭제 = **:1848-2068 + `_print_onboarding_health_section` :2135-2160 (critic C2 실측 경계 — `run_integrity_check` :2075-2133 보존, 내부 print 호출 :2113·:2131 만 제거)** + doctor SKILL OH 대체 1문단 (C6 등가성 요건 — 발동 조건·5항목·처방 3종) 동일 커밋. doctor.py OH 심볼 + 잔여 re-export 블록 정리 + 잔존 테스트 2건 (conventions·slack) 패키지 직접 로드 전환. 게이트: pytest + doctor 실행.
4. **모델 이관 3종 삭제** (커밋 4a/4b/4c — 각각 호출처 대체와 동일 커밋, 커밋별 pytest):
   - 4a `diagnose.py`: doctor SKILL :18·:35 지시문 진단 교체 + doctor.py `--diagnose`·diagnose import 블록 (:103-112) 제거 + `doctor/__init__.py:8` docstring 행 정리 (critic C9-a)
   - 4b `memory-hint.py`: preamble P0 교체 + integrity.py:453 동기화 + project/issue SKILL 문구 + `test_memory_hint.py` 삭제
   - 4c `init_detect.py`: init SKILL :39-40 Glob 직접 판단 교체 + `test_init_detect.py` 삭제
5. **verify-report-lint 흡수** (커밋 5) — auto_pilot.py 에 파서 2함수 원문 이식 → `_load_report_lint` 제거 → `verify-report-lint.py`+`test_verify_report_lint.py` 삭제 (파서 케이스는 test_auto_pilot.py 이동, D5) → verify-reports 픽스처 정리 → evaluator 자기 점검 1줄 (§ C-5). 게이트: pytest + `auto_pilot.py` CLI 스모크 (`--report-file` 경로 — spec 예외 케이스).
6. **orchestrate-load 정비** (커밋 6) — ① `parse_manifest_domain_files` 를 `re.search(r"^##\s+도메인\s*분류\s*$", text, re.M)` + 다음 H2 까지 섹션 절단 + **검색 전 펜스 코드블록 strip** 으로 강화 (D1 승인됨 + critic C4 — learn SKILL.md:80 "코드블록·prose 인용 무시" 완전 구현. 실버그 재현 테스트 선행 추가 → 수정 → 통과 확인, 신규 케이스 3건은 변경 파일 목록 참조). 미매칭 힌트에 H2 단독 라인 정정 안내 포함 (critic C5-b) ② `_common.py` dedup — 함수 동등성 diff 선행, 다르면 로컬 유지 ③ wrapper-protocol.md files_to_read 배선 (D2 승인됨, 4 phase 공통 선두 추가). 게이트: pytest (test_orchestrate_load 676줄 전체) + 본 workspace 에서 orchestrate-load 실행해 `context/pilot/index.md` 로드 실측 확인.
7. **validate.yml 신설 + 총량 마감** (커밋 7) — validate.yml + doctor SKILL :36 재갱신 **동일 커밋** (#18 전달사항 :153) → `docs_build.py` 재생성 (reference 정리) → **감축 총량 게이트 (critic C3, 사용자 재결정 2026-07-25 — 절대치 전환)**:
   - 게이트 = **절감 ≥ 2,100줄**. 측정식 고정: `find pilot/tools -name "*.py" -not -path "*__pycache__*" | xargs wc -l` (`.pyc`·`__pycache__` 제외, 테스트 제외) — #20 직전 HEAD 실측 합 − 완료 시점 실측 합.
   - 감축률 표기 = 절감 / **7,109 (감사 축4 분모 고정)** ≈ **29.5~30%** 로 정직 기재. 주석: "schema.py 유지 결정 (감사 § 4 결정 2) 으로 30% 는 경계선 — spec 의 '30% 이상' 문구는 evaluator 판정 기준을 절대치 (≥2,100줄) 로 명시해 해소".
   - 게이트: pytest + doctor + `docs_build.py --check`.

**완료 후 최종 검증 — 파이프라인 1사이클 실완주 (dogfooding, spec 게이트)**

> **[판정 범위 축소 — 2026-07-25, D-1 (b) 사용자 승인. #21 planner 가 정정]**
> 본 게이트의 판정 근거는 **저장소 사본(`pilot/tools/…`) 직접 실행 결과로 한정**한다. wrapper 가 실제로 로드하는 것은 설치 캐시 `~/.claude/plugins/cache/radiostart-plugins/pilot/` 의 **0.4.0** 이고 저장소는 `plugin.json` 기준 **0.9.0** 이라, 사이클 완주가 #20 변경분의 **실경로 통과를 의미하지 않는다**. 마켓플레이스가 GitHub 클론이라 캐시 갱신에는 머지·배포가 선행돼야 해 사이클 내 해소가 불가능했다.
> **한계 명시** — 캐시 0.4.0 은 애초에 삭제 대상 4파일을 참조하지 않는 구버전이므로, 무증상 통과를 하위호환 신호로도 해석할 수 없다.
> **후속 확인 필요** — 배포로 캐시가 0.9.0 으로 갱신된 뒤, 실경로(설치 캐시 경유 wrapper 세션)에서 아래 (b) 기대값을 1회 재확인해야 한다. 본 항목은 **미완**으로 남는다.

- [ ] **미실행 — 사유: 본 세션은 `@pilot-generator` 서브에이전트 단독 실행이며 서브에이전트는 다른 에이전트(`@pilot-planner`·`@pilot-generator`·`@pilot-evaluator`)를 호출할 권한이 없다.** #21 등록 + 3-agent 사이클 완주는 메인 대화(호출자)가 이 세션 종료 후 별도로 수행해야 한다 (사용자 지시로 본 구현 범위에서 명시 제외).
  - 단, C8 판정 기준 (b)는 본 세션에서 **저장소 사본 기준 선행 실측 확인 완료**: `python3 pilot/tools/orchestrate-load.py --phase generator --workspace workspace` 실행 결과 JSON 에 `workspace/context/pilot/index.md` 가 `files_to_read` 로 실재하고 "진입 파일 미등록" 힌트가 부재함을 확인 (스텝 6 실버그 수정 검증). **설치 캐시 경유 실경로는 미검증** (위 판정 범위 축소 blockquote). 판정 기준 (a) (사이클 산출물 + Bash 오류에 삭제 4파일명 0건)는 실제 3-agent 사이클 실행이 전제이므로 메인 대화 수행 시점까지 미확정.

방법: 소형 검증 feature 를 `/pilot:create-feature` 로 등록 (D3 승인됨 — 소재 = #21 소형 문서성 feature, spec.md 재학습 후속 정정 계열) → `@pilot-planner` → `@pilot-generator` → `@pilot-evaluator` 1사이클 완주. 이 사이클은 #20 변경분의 **저장소 사본을 직접 호출한 명령에 한해** 검증한다 (~~실경로를 통과한다~~ — 위 판정 범위 축소 참조): orchestrate-load 정규식 수정 (도메인 진입 파일 로드 실측)·wrapper-protocol 배선 (D2)·preamble P0 신문안 (memory-hint 부재 확인)·doctor 슬림 출력 (evaluator 게이트)·plan-validate (무변경 확인). wrapper 가 자동 실행하는 캐시본(0.4.0)은 이 목록 중 어느 것도 통과시키지 않는다. **완주 판정 — 채증 가능 2건 (critic C8)**: (a) #21 사이클 산출물 (`.plan.md`·critic·VERIFICATION REPORT `status: READY`) + 사이클 중 Bash 오류 출력에 삭제 4파일명 (`diagnose.py`·`memory-hint.py`·`init_detect.py`·`verify-report-lint.py`) 문자열 0건 (b) 사이클의 orchestrate-load 결과 JSON 에 `context/pilot/index.md` 가 files_to_read 로 실재 + "진입 파일 미등록" 힌트 부재.

### 주의사항

- **동일 커밋 원칙 2종** — (a) 이관 스크립트 삭제 ↔ 호출처 문서 대체 (축4 § 오탐 방지), (b) 스크립트 삭제 ↔ 연동 테스트·픽스처 삭제 (spec). 커밋마다 pytest 전체 통과.
- **이관 부적합 6종 무변경** — plan-validate.py·regen-verify.py·auto_pilot.py (전이 결정성)·confluence.py·slack-notify.py·docs_build.py. 특히 docs_build 의 `cleanup_stale_outputs` 제거 금지 (#18 전달사항 :152).
- **integrity.py 보존 필수부** (축4 § B) — check_workspace·check_project·auto-fix 3종·credential/Slack·run_integrity_check·`_parse_md_tables_in_section`. 파일시스템·git·시각 비교는 모델 대체 금지.
- **#19 재작성본 기준 재확인** — 감사 § C 의 호출처 라인 인용은 감사 시점 (재작성 전) 기준. 실측 갱신분: preamble P0=:21 · init SKILL=:37,:39-40 · doctor SKILL=:18,:34,:35,:36 · integrity=:453 · project=:21 · issue=:22. C-2·C-3·C-4 는 재작성본에 상당 부분 기반영 (critic 실측: cross-domain.md:148 멱등 · open-questions.md:11-12+create-feature :36 · cross-domain.md:60 화이트리스트) — **대조 후 부족분만** 보강, 중복 서술 금지. 감사 C-1 대상 "init·learn SKILL" 중 **learn 은 제외 (critic C9-c)**: learn 은 config.md 표를 생성·수정하지 않아 헤더 리터럴 지시가 무의미 — init 만 적용 (SSOT 초안과의 의도적 편차).
- **orchestrate-load 는 wrapper 전면 의존** — dedup 시 `doctor/_common.py` import 는 doctor.py 와 동일한 sys.path 패턴 사용, 함수 거동 차이 발견 시 dedup 포기하고 로컬 유지 (컨텍스트 로드 SSOT 가 doctor 패키지 결함으로 다운되면 안 됨). graceful degrade (`## 도메인 분류` 미매칭 → 빈 리스트 + 힌트) 계약 불변 (spec 예외 케이스).
- **정규식 강화의 하위 호환** — anchored 매칭은 `## 도메인 분류` H2 가 정확 단독 라인일 때만 매칭. **suffix 변형 (`## 도메인 분류 (수동 관리)` 등) 사용자는 구계약에서 동작하던 자동 로드를 상실하는 회귀 성격 (critic C5)** — 의도된 계약 (learn SKILL.md:80) 이므로 수용하되, 의도 문서화 테스트 1건 + 미매칭 힌트에 정정 안내로 완화. 같은 파일의 `parse_manifest_external_refs` 는 suffix 허용 계약 별도 (기존 anchored) — 무변경. 코드가 문서를 따라가는 방향이므로 SKILL 문구 무변경.
- **doctor 출력 축소의 소비자** — learn:164·project:149·analyze 6-5·tdd-activation §6 의 임베디드 doctor 호출은 "원문 그대로 출력" 규칙만 참조 — 검사 감소에 자동 적응, SKILL 수정 불요 (doctor SKILL § 임베디드 규칙 무변경). 단 **임베디드 경로의 OH 온보딩 nudge 는 소실 — 의도된 다운그레이드 (critic C6)**: 대체 지시문은 `/pilot:doctor` 스킬 경유 시에만 수행되며, 온보딩 funnel 은 `docs/tutorial/getting-started.md` 가 커버.
- **OH 삭제로 stale 참조 동반 소멸** — OH INFO 의 `pilot/docs/getting-started.md` 경로는 이미 죽은 경로 (실파일은 `docs/tutorial/getting-started.md`) — OH 삭제로 자연 해소, 별도 정정 불요.
- **generator 는 project.md `## 목표` 체크박스 수정 금지** — evaluator 단독 권한 (#03 전달사항 정착 룰).

### 사용자 결정 (승인됨 2026-07-25 — D1~D5 전건 권고안대로 확정)

- **D1. MANIFEST 파서 정규식 강화** — **승인됨**. 실버그 재현 확인 (본 세션 로드 실패). #06 전달사항 옵션 (a) anchored H2 + 섹션 절단 채택 — 스텝 6-① 확정.
- **D2. wrapper-protocol.md files_to_read 배선** (#19 전달사항 :157) — **승인됨**. 4 phase 공통 선두 추가 (이중화) — 스텝 6-③ 확정.
- **D3. dogfooding 소재** — **승인됨**. #21 소형 문서성 feature 신규 등록 (spec.md 재학습 후속 정정 계열) 확정.
- **D4. 무관 전달사항 19건 disposition** — **승인됨**. 전건 이월 (unchecked 유지, v0.4.0 참고 노트·재사용 패턴 메모).
- **D5. test_verify_report_lint "부분 축소" 해석** — **승인됨**. 파일 삭제 + 파서 케이스 test_auto_pilot.py 이동 확정 (케이스 손실 0).

### 전달사항 소비 (처리 완료 2026-07-25)

#20 관련 12건 — plan 반영 + project.md `[x]` 소비 사유 부기 완료: :107·:108·:109 (#05 마이그레이션 3건 — 코드 삭제로 소멸, 스텝 1) · :113 (#09·#10 헬퍼 보강 노트 — lint 소비자 삭제로 소멸, 헬퍼 자체는 보존) · :122 (H3 헬퍼 재사용 — 삭제로 소멸) · :123 (TX 화이트리스트 v0.4.0 재고 — 삭제로 소멸) · :126 (init_detect 시그니처 재사용 — 삭제로 소멸) · :140 (#06 정규식 drift — 스텝 6 실버그 수정, D1) · :152 (docs_build 무변경 준수) · :153 (validate.yml 동일 커밋 재갱신 — 스텝 7) · :154 (migration 픽스처 정리 — 스텝 1) · :157 (wrapper-protocol 배선 — D2)

무관 19건 (D4 승인 — 전건 이월, unchecked 유지): :105 · :115 · :117 · :121 · :124 · :125 · :128 · :131 · :132 · :134 · :142 · :143 · :144 · :145 · :146 · :148 · :149 · :151 · :156 (spec.md 재학습은 PR 머지 후 `/pilot:learn` 재실행 — 이월 유지)

### 교차 의존

- 없음 — #18·#19 완료 상태 위에서의 삭제·이관만. 단 PR 머지 후 `workspace/context/pilot/spec.md`·`index.md` 재학습 (#19 전달사항 :156) 시 본 feature 의 tools 삭제분이 재학습 산출물에 반영되어야 함 (learn 재실행이 자연 흡수).
