# Plan Critic — #20 정비 slim — Python 슬림화

> 입력 plan: `features/20-consolidation-slim.plan.md` (검토 시각 2026-07-25T00:12:24Z)
> 입력 feature: `features/20-consolidation-slim.md`
> 페르소나: `personas.planner-critic` (red-team)
> focus 반영: 없음 (orchestrate-load focus=null. 호출자 지정 6축 — dedup 커플링 · OH 등가성 · #19 중복 · 삭제 오탐 · 게이트 실행 가능성 · MANIFEST 파서 파급 — 전축 실측 검증)

## 챌린지

### C1 — 커밋 1·2 가 doctor.py 명시 import 를 깨뜨림 (게이트 자기 모순)
- **severity**: blocking
- **category**: edge-case
- **plan 인용**: 구현 순서 #1·#2 vs #3 ("doctor.py re-export 정리"는 커밋 3)
- **챌린지**: `doctor.py:59-85` 의 re-export 는 wildcard 가 아닌 **명시 import** ("누락 시 즉시 ImportError" 주석 실측). 커밋 1 이 integrity.py 에서 `migrate_v0_1_to_v0_2`·`_inject_v010_defaults_into_config`·`_is_learn_section_empty`·`_has_partial_learn_definition` 를 삭제하면 doctor.py:61-84 import 가 즉시 실패한다. 커밋 2 도 동일 (`check_workspace_config_sections`·`check_workspace_external_domain_section`·`check_features_open_questions`·`check_domain_transaction_contracts`·`_parse_md_tables_in_h3_section` 5 심볼, doctor.py:64-81). `test_doctor_conventions.py:27`·`test_doctor_slack.py:20` 이 doctor.py 를 importlib 로 로드하므로 커밋 1·2 의 게이트 ("커밋마다 pytest 전체 통과" + 스텝 2 의 "doctor.py workspace 실행") 는 plan 대로면 **통과 불가능** — 플랜 내부 모순.
- **제안**: 각 삭제 커밋이 대응하는 doctor.py import 라인을 함께 제거하도록 스텝 1·2 에 명시 (커밋 1: :61,:64-66,:83 / 커밋 2: :68,:73-74,:80-81). 또는 re-export 블록 정리 전체를 커밋 1 로 앞당김. 잔존 테스트 2건의 패키지 직접 로드 전환 시점도 함께 재배치.

### C2 — OH 삭제 범위가 보존 필수 `run_integrity_check` 를 포함
- **severity**: blocking
- **category**: premise
- **plan 인용**: 변경 파일 integrity.py 항목 ("OH-1~5 + check_onboarding_health (:1849-2133)") + 구현 순서 #3 ("OH 전체 (:1849-2160) 삭제")
- **챌린지**: 실측 경계 — OH 블록은 :1848-2068 (helpers :1852-2032 + dispatcher `check_onboarding_health` :2035-2068), **`run_integrity_check` 는 :2075-2133** (축4 § B·spec 비즈니스 규칙의 보존 필수부), `_print_onboarding_health_section` 은 :2135-2160. plan 의 두 범위 표기는 모두 run_integrity_check 본체를 삭제 범위 안에 포함한다. 스텝 3 을 literal 하게 따르면 doctor default 모드 진입점이 소멸 — plan 자신의 주의사항 ("integrity.py 보존 필수부") 과 정면 모순.
- **제안**: 범위 정정 — 삭제 = :1848-2068 + :2135-2160, run_integrity_check (:2075-2133) 는 내부 호출 3줄만 제거 (:2113·:2131 print 호출 — :2092-2095 tx 호출은 스텝 2, :2123-2126 migration 호출은 스텝 1 소관).

### C3 — 30% 게이트 산식이 plan 자신의 숫자로 미달 (#19 C1 재발)
- **severity**: blocking
- **category**: risk
- **plan 인용**: 구현 순서 #7 ("예상: 이관 4종 1,008 + integrity ~1,100 + doctor.py ~60 + orchestrate-load ~50 − auto_pilot 이식 ~120 ≈ 2,100줄 / 7,109 ≈ 30%")
- **챌린지**: plan 의 산식 그대로면 1,008+1,100+60+50−120 = **2,098 / 7,109 = 29.5%** — spec 게이트 "tools/ 총 30% **이상**" 미달. 실측 재계산 (integrity 삭제 = migration 246 + lint 642 + OH 221 + print 헬퍼 26 + 호출부 ~14 ≈ 1,149) 으로도 2,147 / 7,138 (현재 실측 py 합계 — 감사 시점 7,109 에서 +29 드리프트) = **30.1%**, 마진 0.2pp 미만. 게다가 auto_pilot 이식은 `parse_report` (:99-218 ≈120줄) + `extract_report_block` (:81-97) + 필수 정규식·상수 (REPORT_HEADER_RE·_TOP_KEY_RE 군 등) 로 **~150-170줄**이 현실적 — 마진이 음수로 뒤집힐 수 있다. 측정 명령 `wc -l pilot/tools/**` 도 `__pycache__/*.pyc`·디렉터리가 섞여 판정 불가.
- **제안**: (a) 측정식 고정 — `find pilot/tools -name "*.py" | xargs wc -l` (테스트 제외), baseline 7,138 명기. (b) auto_pilot 이식 규모 실측 후 산식 재계산. (c) 마진이 1% 미만이면 게이트 문구를 감사 § D 원문 ("~2,100 — 전체의 30~35%", 이 표기 자체가 29.5% 의 관대한 반올림) 정합으로 "약 2,100줄 (약 30%)" 재협상하거나, 보존부 verbose Result 정리 등으로 마진 확보 — 어느 쪽이든 **사용자 재승인 필요** (게이트 완화는 planner 단독 결정 불가).

### C4 — anchored 정규식만으로는 learn SKILL 이 약속한 "코드블록 무시" 미구현
- **severity**: suggestion
- **category**: edge-case
- **plan 인용**: 구현 순서 #6-① + 주의사항 "정규식 강화의 하위 호환"
- **챌린지**: 인용 계약 `learn/SKILL.md:80` 은 "**코드블록**·prose 인용 무시" 를 약속한다. anchored `^##\s+...\s*$` + re.M 은 blockquote prose (`> ` 접두) 는 배제하지만, 펜스 코드블록 안 컬럼 0 의 `## 도메인 분류` 예시 라인은 여전히 **첫 매칭**되어 예시 표의 가짜 진입 경로를 로드할 수 있다 (MANIFEST 는 자유 형식 — 가이드 펜스 예시가 실 H2 보다 앞에 올 수 있음). #06 전달사항의 옵션 (b) (펜스 추적 재사용) 가 이번에 보존 확정된 `_parse_md_tables_in_section` 의 펜스 추적 로직과 정확히 겹친다.
- **제안**: 검색 전 펜스 블록 strip (~4줄) 또는 스텝 6-② dedup 배선에 펜스 추적 공유를 포함. `test_orchestrate_load` 신규 케이스에 prose-선행 재현과 함께 **펜스-선행 변형** 1건 추가.

### C5 — H2 suffix 변형 사용자의 조용한 회귀 (구계약에서는 동작하던 케이스)
- **severity**: suggestion
- **category**: edge-case
- **plan 인용**: 주의사항 "정규식 강화의 하위 호환" ("suffix 붙은 사용자 변형은 미매칭 → graceful degrade")
- **챌린지**: 현행 un-anchored 정규식은 `## 도메인 분류 (수동 관리)` 같은 suffix 변형에서도 표를 정상 파싱했다 — anchored 전환 시 이 사용자군은 **동작하던 자동 로드를 조용히 상실**한다 (힌트 1줄뿐). 같은 파일의 `## 외부 도메인 reference` 파서는 suffix 허용 (sub-string) 계약이라, 한 MANIFEST 안에서 두 H2 의 허용 규칙이 갈린다. 의도된 계약임은 learn SKILL:80 으로 확인했으므로 방향 자체는 수용 — 단 회귀 성격의 명시가 없다.
- **제안**: 재확인만 필요 + 2건 보강 — (a) suffix 변형 미매칭을 **의도된 non-match 로 문서화하는 테스트** 1건 (b) graceful degrade 힌트 문구에 "H2 를 단독 라인 `## 도메인 분류` 로 정정" 안내 포함 여부 결정.

### C6 — OH 대체 1문단의 등가성 조건 미정의 (발동 조건 + 임베디드 경로 소실)
- **severity**: suggestion
- **category**: scope
- **plan 인용**: 변경 파일 doctor SKILL 항목 ("OH 대체 1문단 — 신규 워크스페이스 감지 시 … 모델이 점검·안내") + 주의사항 "doctor 출력 축소의 소비자"
- **챌린지**: 현행 OH 는 **모든** doctor 실행 (learn:164·project:149·analyze 6-5 임베디드 포함) 에서 온보딩 시점마다 자동 발화한다 ("scope/ 미채움 → /pilot:learn 권장" 등). 삭제 후 대체 문단은 `/pilot:doctor` 스킬 경유 시에만 모델이 수행 — 임베디드 경로의 nudge 는 소실된다 ("자동 적응" 주의사항은 기계적으로만 참). 또 "신규 워크스페이스 감지" 의 판정 기준이 문안에 없다 — 현행 코드는 "OH 전 룰 WARN" (:2156) 이라는 명시 기준을 갖는다.
- **제안**: 대체 문안에 (i) 발동 조건 (예: MANIFEST 도메인 표 0행 또는 STATE 등록 0건) (ii) 5개 점검 항목 (config 3섹션·scope/·STATE·MANIFEST·features) (iii) 처방 명령 3종을 명시. 임베디드 경로 nudge 소실은 **의도된 다운그레이드**로 plan 에 1줄 기록 (근거: tutorial getting-started 가 온보딩 funnel 커버).

### C7 — lint 삭제의 참조 잔재 2건 — 스텝 2 sweep 누락 (#18 C1 유형)
- **severity**: suggestion
- **category**: edge-case
- **plan 인용**: 구현 순서 #2 (지시문 대체 목록)
- **챌린지**: (a) `analyze/references/scope-sync.md:58` — "`scope 헤더` 컬럼 값이 `## ` prefix 미준수 → **doctor 검증이 사전 차단 (ERROR)**" 는 삭제되는 `check_workspace_config_sections` 의 거동 약속 — 스텝 2 후 거짓 약속이 되는데 대체 목록에 없다. (b) `integrity.py:895` (보존 함수 `check_conventions_paths` 내부) — "읽기 실패는 check_workspace_config_sections 가 보고" 주석으로 보고 책임을 삭제 대상에 위임 — 삭제 후 config.md 읽기 실패가 **무보고 무음**이 되고 주석은 orphan.
- **제안**: 스텝 2 동일 커밋에 scope-sync.md:58 문구를 A2 fallback 서술로 교체 + integrity.py:895 를 자체 WARN 1건 또는 주석 정정으로 처리.

### C8 — dogfooding 완주 판정 "삭제 스크립트 호출 시도 0건" 측정 방법 부재
- **severity**: suggestion
- **category**: risk
- **plan 인용**: 구현 순서 "완료 후 최종 검증" (완주 기준)
- **챌린지**: `status: READY` 는 객관적이나 "호출 시도 0건" 은 세션 로그 채증 방법이 정의되지 않아 evaluator 가 증거로 인용할 수 없다 (guardrails "증거 없으면 통과 없음").
- **제안**: 판정을 채증 가능한 2건으로 교체 — (a) #21 사이클 산출물 (`.plan.md`·critic·REPORT) 과 사이클 중 Bash 오류 출력에 삭제 4파일명 (`diagnose.py`·`memory-hint.py`·`init_detect.py`·`verify-report-lint.py`) 문자열 0건 (b) 사이클의 orchestrate-load 결과 JSON 에 `context/pilot/index.md` 가 files_to_read 로 실재 + "미등록" 힌트 부재.

### C9 — 문서·수치 잔재 소소 3건
- **severity**: nit
- **category**: scope
- **plan 인용**: 구현 순서 #4a · 테스트 삭제 합계 · 변경 파일 init SKILL 항목
- **챌린지**: (a) `doctor/__init__.py:8` docstring 의 "`diagnose` : 런타임 실패 패턴 진단 (--diagnose)" 모듈 목록 행 — 4a 커밋 정리 대상 누락. (b) 테스트 삭제 합계 "~1,413줄" — 9파일 실측 합 **1,433줄** (278+136+135+97+107+154+192+137+197). (c) 감사 § C-1 의 대상 "init·**learn** SKILL" 에서 learn 을 조용히 제외 — learn 은 config 표를 쓰지 않으므로 타당하나 SSOT 초안과의 편차 사유 1줄 부기 권장.
- **제안**: (a) 4a 에 1줄 추가 (b) 수치 정정 (c) 주의사항에 사유 부기.

## 검증 통과 축 (챌린지 없음 — 근거 기록)

- **dedup 커플링 (스텝 6-②)**: `doctor/_common.py` 는 stdlib 전용·`__init__.py` 는 docstring 전용 — 순환 import 없음. `parse_state_yml` 양쪽 본문 동일, `parse_semver`↔`_parse_semver` 거동 동등 (falsy 입력 모두 None) 실측 — plan 의 "거동 차이 시 dedup 포기" 가드와 sys.path 패턴 명시로 충분.
- **#19 중복 (스텝 2 이관 지시문)**: C-2 멱등 (`cross-domain.md:148`) · C-3 4카테고리 필수 (`open-questions.md:11-12`, `create-feature/SKILL.md:36`) · C-4 화이트리스트 (`cross-domain.md:60`) 기존재 실측 — plan 의 "대조 후 부족분만" 원칙이 이중 서술을 실제로 방지.
- **삭제 오탐 전수 재확인**: memory-hint 참조 = preamble:21·integrity:453·project:21·issue:22 + docs/reference (스텝 7 재생성) — plan 목록과 일치, P0 경유 5스킬 중 analyze·create-feature·learn 은 preamble 참조만이라 무수정 타당. diagnose = doctor.py·doctor SKILL:18/:35 (+C9-a). init_detect = init SKILL:39-40 단독. verify-report-lint = auto_pilot 파서 2함수 소비만 실측 (`validate()` 런타임 소비자 없음). `test_doc_links` 는 skills/·agents/ 만 스캔 — docs/reference 재생성을 스텝 7 로 미뤄도 중간 커밋 게이트 안전.
- **doctor SKILL 라인 인용**: :18·:34·:35·:36 전건 현행 일치 실측. lint 호출부 :397·:412·:779·:2092 일치.
- **validate.yml**: `tests.yml` 실재 (unittest discover) — 패턴 답습 전제 성립.

## 합의 (planner 기입 2026-07-25)

| C# | 처리 | 메모 |
|----|------|------|
| C1 | accepted | doctor.py 명시 import 제거를 심볼 삭제와 동일 커밋 분할 — 커밋 1 (migration 4 심볼 :61·:64-66·:83) / 커밋 2 (lint 5 심볼 :68·:73-74·:80-81) / 커밋 3 (OH 심볼+잔여 블록+테스트 로드 전환) / 커밋 4a (diagnose 블록 :103-112). plan 변경 파일·스텝 1·2·3·4a 반영 |
| C2 | accepted | OH 삭제 범위 실측 경계로 정정 — :1848-2068 + `_print_onboarding_health_section` :2135-2160. `run_integrity_check` (:2075-2133) 보존, 내부 print 호출 :2113·:2131 만 제거. plan 변경 파일·스텝 3 반영 |
| C3 | accepted | **사용자 재결정 (2026-07-25)** — 게이트 절대치 전환: 절감 ≥2,100줄, 측정식 `find pilot/tools -name "*.py" -not -path "*__pycache__*" \| xargs wc -l` 고정, 감축률 분모 = 감사 7,109 고정, ≈29.5~30% 정직 기재 + "schema.py 유지로 30% 는 경계선" 주석. spec "30% 이상" 과의 차이는 evaluator 판정 기준 절대치 명시로 해소. 스텝 7 반영 |
| C4 | accepted | anchored 만으로는 learn SKILL.md:80 의 "코드블록 무시" 미이행 — 검색 전 펜스 strip (~4줄) + 펜스-선행 테스트 1건 추가. 스텝 6-①·test_orchestrate_load 신규 케이스 ② 반영 |
| C5 | accepted | suffix 변형 회귀 성격을 주의사항에 명시 (의도된 계약 수용) + (a) 의도 문서화 non-match 테스트 1건 (b) 미매칭 힌트에 "H2 단독 라인 정정" 안내 포함. 스텝 6·테스트 케이스 ③·주의사항 반영 |
| C6 | accepted | OH 대체 문안에 (i) 발동 조건 (MANIFEST 표 0행 또는 STATE 0건 — 현행 :2156 판정 지시문화) (ii) 점검 5항목 (iii) 처방 3종 명시. 임베디드 경로 nudge 소실 = 의도된 다운그레이드로 주의사항 기록 (funnel 은 tutorial getting-started 커버) |
| C7 | accepted | 참조 잔재 2건 스텝 2 동일 커밋 — (a) scope-sync.md:58 "doctor 사전 차단" → A2 fallback 서술 (b) integrity.py:895 위임 주석 → 자체 WARN 1건 (무음 방지). 변경 파일 2곳 반영 |
| C8 | accepted | 완주 판정을 채증 가능 2건으로 교체 — (a) #21 산출물 + Bash 오류 출력 삭제 4파일명 0건 (b) orchestrate-load JSON 에 `context/pilot/index.md` 실재 + "미등록" 힌트 부재. dogfooding 절 반영 |
| C9 | accepted | (a) `doctor/__init__.py:8` docstring 행 — 커밋 4a 추가 (b) 테스트 합계 1,413 → **1,433** 정정 (c) C-1 대상에서 learn 제외 사유 (config 표 미작성 스킬) 주의사항 부기 |
