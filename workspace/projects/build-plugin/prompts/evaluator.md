# Evaluator — build-plugin

구현 완료 후 요구사항 충족 여부와 일관성을 검토한다.

**역할:** **완성도 심사** — Generator 의 자체 sanity check 와 별개로, features 요구사항·비즈니스 규칙·예외 케이스 충족 여부를 최종 판정. 체크리스트 `[x]` 가 이 판정의 기록.

> **⚠️ 이 파일은 `@pilot-evaluator` subagent 정의가 아닙니다.** 실제 subagent 는 플러그인의 [`${CLAUDE_PLUGIN_ROOT}/agents/pilot-evaluator.md`](${CLAUDE_PLUGIN_ROOT}/agents/pilot-evaluator.md) 에 등록돼 있고, wrapper 가 Read 로 **이 파일을 컨텍스트 문서로** 불러들입니다. 이 파일 편집은 다음 `@pilot-evaluator` 호출에 반영됩니다 (단 `<!-- [analyze-managed] -->` 섹션은 다음 `--regen-agents` 시 덮어쓰임).
>
> 스캐폴딩·analyze-managed·TDD 상세: [agents-scaffold-notes.md](${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/projects/agents-scaffold-notes.md) 참조.

---

<!-- [analyze-managed] -->
## 기능 완성도

- [x] #00 `pilot/tests/fixtures/v0.1.0-baseline/` 디렉터리 + 1 언어 `_input/` + `learn/project/analyze/expected/` + `config/{pass-empty,pass-valid,error-*}` + `diff.sh`. v0.1.0 캡처 시 diff 0. (0a + 0b 캡처 완료. `_input/python-sample/` 11 파일 + `learn/expected/` + `project/expected/projects/python-sample-demo/` + `analyze/expected/projects/python-sample-demo/` 일관. `python-sample` (도메인명) ↔ `python-sample-demo` (프로젝트명) 구분 적용. 회귀 자동 검증 자체 (`diff.sh --actual {regen}` 1 회 실행) 는 별도 항목 line 50·63 으로 분리 — runtime lookup 구현 후 1 회 수행)
- [x] #01 learn Phase 2 가 config.md `## learn 언어 패턴` 의 두 표를 lookup (long-form). D10 default 폐지 — SKILL.md 본문에 default 표 0. config 비면 폴더 인접성 fallback. 사용자 override 시 즉시 반영. backward-compat 은 #05 마이그레이션으로 위임.
- [x] #02 analyze 5-2 가 config.md `## scope 카테고리` 매핑을 lookup. config 비면 default (Routes/Models/Services) 사용. `/pilot:create-feature` 도 동일 lookup 자동 적용 (5-2 인용 호출).
- [x] #03 `/pilot:project` 가 신규 폴더 생성 시 1 회 H3 동적 생성. 재실행 시 기존 H3 보존. config 비면 default H3 (Models/Endpoints/Services) 생성 (기존 거동).
- [x] #04 doctor 가 신규 config 섹션 존재 시 스키마 검증 (컬럼 수·헤더 화이트리스트·`## ` prefix). D10 행 수 0 허용 (빈 표 → INFO 1 줄). 부재 시 INFO 1 줄, WARN 아님.
- [x] #05 doctor `--fix` 가 v0.1.0→v0.2.0 업그레이드 감지 시 사용자 확인 (a/b/c) 후 v0.1.0 default 표 자동 주입 또는 거부 기록. interactive 환경 only — non-interactive 자동 미루기.
- [x] #18 감사 승인 삭제 전건 수행 (handoff-quality·v0.1.0-baseline 수동 하네스·examples README·사람용 문서 3종) + 자동 테스트 참조 픽스처 (external-domain·transaction-contracts·config·migration·open-questions·verify-reports) 보존 + 드리프트 B-1~B-9 정정 (정본 = 감사 축 2 § B 판정) + 깨진 링크 0 + pytest·doctor·docs 빌드 클린. 기계 계약·스킬 동작 무변경. (검증 2026-07-24 evaluator 독립 재실행: git rm 46파일 분해 = plan 일치 (handoff 4 · diff.sh 1 · expected 37 · examples 1 · lifecycle 3) · 보존 5종 + `_input/` 15파일 + sibling 3종 무손 · 잔존 참조 git grep exit 1 (0건) · unittest discover 353 tests OK exit 0 · doctor workspace exit 0 · 0 ERROR (8 WARN 은 stash 비교로 변경 전과 동일 = 기존 워크스페이스 상태) · doctor --schema 6 PASS 0 ERROR · docs_build exit 0 + stale 정리 실측 (심은 파일 removed 1) · test_doc_links 16/16 · test_docs_build 41 tests OK (신규 5케이스) · B-1~B-9·A-12·C6 정본 대조 전건 일치 (B-9 literal 3곳 동일·A-12 트리 GUIDE 정본 byte 일치·`.claude/agents` 잔존 0) · analyze 단계 앵커·Detect literal·CLI 시그니처 불변)
- [x] #19 SKILL.md 각 100줄 이하 + 감사 축 3 의 스킬별 불변 조건 체크리스트 전 항목 보존 (문자열 원문 계약·analyze 단계 번호 앵커·learn 실측 규칙 포함) + agents 는 계약 보존 우선 + context/ 16 클러스터 정본 통합 + 지시 문서 총량 30~35% 감축 + pytest·doctor·docs 빌드 클린. (검증 2026-07-25 evaluator 독립 재실행: 줄수 실측 17 스킬 전건 ≤100 (learn 109 ≤120 — Open Q (d) 사용자 결정)·agents 366줄 · 총량 base(a18a429) 4,808 → 3,635 ≤3,680 게이트 통과 (단독 24.4% — critic C1 사용자 재결정 2026-07-25: 30~35% 는 #20 합산 판정) · references/ 이동 계상 0 (prompts-update 참조 교체 1줄뿐·pilot/docs 무변경) · 감사 축 3 체크리스트 전수 대조 — 17 스킬 147항 + 5 에이전트 48항 전건 실재 (analyze 앵커 1~8·5-1·5-1.5·5-2·6-5·7 + project "1~5/6~7"·create-feature "5~6"·"6-5" 인용 보존, learn 16항 실측 규칙 전건, autopilot CLI 토큰 7종·hard-stop enum 5종·retry {R}+1) · 문자열 계약 grep 전건 매칭 (Detect literal 4종 = tdd-activation 만·tdd SKILL 하드코드 0, init 표 헤더 4종, MANIFEST 정규식 원문 미정정, messages 키 6종+state_corrupt, evaluator REPORT 블록 base 대비 byte diff 0) · frontmatter diff a18a429..HEAD skills+agents 빈 출력 · wrapper 잔류 최소 셋 4항 (C2) 4벌 각 wrapper-protocol grep 2·code-review 0 · C5 소비처 4곳 정본 참조 교체 + plan-schema:30 → planner:64-88 재고정 실측 일치 · 정본 신설 6종 (wrapper-protocol 53줄·guardrails A2/A16·preamble P1 workspace_missing+적용표 2행·messages Slack 발송 계약·doctor 임베디드 출력 규칙·INDEX 82줄 보존 앵커 4종) · unittest 353 OK exit 0 · doctor workspace exit 0 · 0 ERROR (8 WARN = #18 과 동일 기존 상태) · doctor --schema 6 PASS · docs_build --check exit 0 · doc_links+docs_build 57 tests OK)
- [ ] #20 integrity.py ~1,060줄 (마이그레이션 삭제·lint 4종 이관·OH 축소) + 이관 3종 스크립트 삭제가 호출처 문서 대체와 동일 커밋 + schema.py 유지 · validate.yml CI 신설 + 이관 부적합 6종 (plan-validate·regen-verify·auto_pilot·confluence·slack-notify·docs_build) 무변경 + 연동 테스트 정리 후 pytest 전체 통과 + tools/ 30%+ 감축 + 파이프라인 1사이클 실완주. **미체크 사유 = dogfooding 게이트 1건 미충족 (나머지 전건 통과).** 체크 조건: 배포 → `pilot/tools/pilot-update.sh` → **세션 재시작** → 설치 캐시 실경로 1사이클.
  - **[통과] 검증 완료분** (2026-07-25 evaluator 독립 재실측, 커밋 `bb4f222`~`adf85db` 9커밋):
    - **integrity.py 슬림화** — 2,160 → **995줄** (`wc -l`, 목표 ~1,060 초과 달성). 삭제 = migration 4심볼 (커밋 1) · md 표 lint 4종 + `_parse_md_tables_in_h3_section` + `_TX_TYPE_WHITELIST` (커밋 2) · OH-1~5 + `check_onboarding_health` + `_print_onboarding_health_section` (커밋 3). **보존 필수부 전건 실재** (`grep "^def "` 실측): `check_workspace`·`check_project`·`run_integrity_check`·auto-fix 3종 (`_fix_state_md_prune_history`·`_fix_migrate_state_to_current`·`_fix_remove_legacy_planning_section`)·`check_credential_drift`·`check_slack_env_not_tracked`·`check_gitignore_required_patterns`·`_parse_md_tables_in_section`.
    - **이관 3종 삭제 ↔ 호출처 문서 대체 동일 커밋** — `git show --stat` 전건 대조: 4a `34a1ed8` = `diagnose.py`(-181) + doctor SKILL § 진단 모드 신설(4패턴 표 + `## DIAGNOSIS` 5필드) + `doctor.py --diagnose` 블록 + `__init__.py` docstring (C9-a) · 4b `cb37dd0` = `memory-hint.py`(-176) + preamble P0 재작성 + `integrity.py:453` 문구 + project/issue SKILL · 4c `4796ca5` = `init_detect.py`(-279) + init SKILL Glob 직접 판단 2단계. 흡수 1종 5 `86e0fba` = `verify-report-lint.py`(-372) + auto_pilot 파서 2함수 이식 + `pilot-evaluator.md:54` 자기 점검. **잔존 참조 0건** — `grep -rn -E 'diagnose\.py|memory-hint|init_detect|verify-report-lint' pilot/ .github/` 결과는 provenance 주석 2건 (`auto_pilot.py:82`·`pilot-evaluator.md:54` "구 …에서 이식") 뿐.
    - **schema.py 유지 + validate.yml CI 신설** — `schema.py` 410줄 `git diff` 빈 출력 (무변경). `.github/workflows/validate.yml` 실재 (43줄, `doctor.py --schema` 실행, paths 5종 + concurrency 분리). doctor SKILL `--schema` 줄의 구 문구("CI 연동은 #20 에서 신설 예정")가 동일 커밋 `adf85db` 에서 교체됨 (#18 전달사항 :156 소화). 로컬 실행 `6 PASS · 0 WARN · 0 ERROR` exit 0.
    - **이관 부적합 6종** — `plan-validate.py`·`regen-verify.py`·`confluence.py`·`slack-notify.py`·`docs_build.py` 5종 `git diff bb4f222~1..adf85db` **빈 출력 = 무변경**. `docs_build.py:364 cleanup_stale_outputs` 보존 실재 (#18 전달사항 :155). `auto_pilot.py` 는 spec 이 명령한 파서 흡수로 +132/-14 변경됐으나 **전이 결정 로직은 불변** — 삭제 `verify-reports` 픽스처 12건 전량을 신·구 바이너리에 교차 실행한 differential 결과 **12/12 출력·exit code 일치**, `--phase planner|critic|evaluator` × `--plan-valid`/`--retries-used` 4조합도 전건 일치. spec 예외 케이스(`--report-file` CLI 계약)도 불변 확인.
    - **연동 테스트 정리 + pytest 전체 통과** — 삭제 9파일 실측 합 **1,433줄** (critic C9-b 정정치 일치). 픽스처 `config`·`external-domain`·`migration`·`open-questions`·`transaction-contracts`·`verify-reports` 전량 소비 테스트와 동일 커밋 삭제, baseline `README.md` 갱신, `_input/` 15파일 보존. 파서 케이스 6건은 `test_auto_pilot.TestExtractAndParseReport` 로 이동 (손실 0, D5). **`python3 -m unittest discover -s tests/tools` = 284 tests OK exit 0** (변경 전 worktree 실측 353 → -69, 삭제분과 정합).
    - **tools/ 절감 절대치 게이트** — 계획 확정 측정식 `find pilot/tools -name "*.py" -not -path "*__pycache__*" | xargs wc -l` 로 재실측: **7,138 → 4,997 = 절감 2,141줄** ≥ 2,100 **통과** (마진 +41). 감축률 = 2,141/7,109(감사 분모) = **30.1%** — spec 의 "30% 이상" 도 실측상 충족.
    - **MANIFEST 파서 실버그 수정 (스텝 6)** — 실버그 재현 실측: 구 정규식 `re.search(r"##\s*도메인\s*분류([\s\S]*?)(?:\n##\s|\Z)")` 을 현행 `workspace/context/MANIFEST.md` 에 적용하면 상단 blockquote prose 를 선매칭해 섹션이 실제 H2 직전에서 잘려 **표 행 0건**. 신 구현 (`_strip_fenced_code_blocks` + `_DOMAIN_SECTION_HEADER_RE = ^##\s+도메인\s*분류\s*$` re.M + 다음 H2 절단) 으로 정상 파싱. **저장소 사본 `orchestrate-load.py` 를 4 phase 전건 실행**: `files_to_read` 에 `wrapper-protocol.md`(D2 배선) + `workspace/context/pilot/index.md` 실재, hints 는 `MANIFEST 도메인 진입 파일 로드: context/pilot/index.md` — "미등록" 힌트 부재. 미매칭 힌트에 H2 단독 라인 정정 안내 포함 (C5-b). 신규 테스트 4건 (prose-선행 재현 · 펜스-선행 C4 · suffix non-match C5-a · wrapper-protocol 로드) + 기존 2건 assertion 보강 실재. `_common.py` dedup (`parse_state_yml`·`_parse_semver`) 반영.
    - **critic 합의 C1~C9 이행** — C1 doctor.py 명시 import 를 심볼 삭제와 동일 커밋 분할 (커밋 1/2/3/4a, 각 커밋 `doctor.py` diffstat 실재) · C2 `run_integrity_check` 보존 (함수 목록 실측) · C3 절대치 게이트 통과 · C4 펜스 strip 구현 · C5 non-match 테스트 + 힌트 안내 · C6 doctor SKILL § Onboarding Health 에 발동 조건·점검 5항목·처방 3종 + 임베디드 nudge 소실 의도 명시 전건 실재 · C7-a `scope-sync.md` "doctor 사전 차단" → A2 fallback 서술 교체 · C7-b `check_conventions_paths` 내부 config.md 읽기 실패 시 자체 `Result.WARN` 추가 (diff 실측) · C9-a `__init__.py` docstring 정리 · C9-b 1,433 정정치 일치.
    - **게이트 재실행** — `docs_build.py --check` exit 0 · `doctor.py workspace` `9 PASS · 4 WARN · 0 ERROR` exit 0 (WARN 4 = #21 baseline 동일, #20 무관) · `doctor.py --schema` `6 PASS` exit 0 · `test_doc_links` 16/16 OK. `pilot/docs/reference/tools/` = 실재 8종 + index (삭제 3종 stale 페이지 부재 — 커밋 7 재생성 반영. 단 `pilot/.gitignore:10` 로 git 미추적이라 **커밋 증거가 아닌 현재 상태로만 확인**).
    - **scope** — 변경 경로는 `pilot/**` 75파일 + `.github/workflows/validate.yml` 1파일뿐. `workspace/` 변경 0 (generator 의 `## 목표` 체크박스 무단 수정 없음).
  - **[미통과] dogfooding 게이트 — "파이프라인 1사이클 실완주"** (사용자 확정 D-1 (b) 축소 · C1 unchecked 유지):
    - #21 사이클은 **저장소 사본 직접 호출만** 검증했다. wrapper 가 실제 로드하는 것은 설치 캐시 `~/.claude/plugins/cache/radiostart-plugins/pilot/0.4.0` — 본 evaluator 세션의 step 1 `orchestrate-load` (캐시 0.4.0 경유) 도 pilot 행이 MANIFEST 에 실재함에도 `"도메인 'pilot' 의 진입 파일이 MANIFEST 에 등록되지 않음"` 힌트를 그대로 출력했고 `wrapper-protocol.md`·`context/pilot/index.md` 를 로드하지 않았다 = **#20 변경분 미반영 실경로**의 직접 증거.
    - 캐시 0.4.0 트리에 `init_detect.py`·`memory-hint.py` 가 **여전히 실재** (`ls` 실측) — C8 판정 (a)("삭제 4파일명 0건")는 캐시가 애초에 그 파일들을 참조하지 않는 구버전이라 **증거력 0** (#21 evaluator G7(a) `skip` 판정과 동일 결론).
    - 체크 조건 (5단계): ① PR 머지 → ② 배포 → ③ `pilot/tools/pilot-update.sh` → ④ **세션 재시작** (세션 중 플러그인 리로드 불가) → ⑤ 실경로에서 C8 (b) 기대값 재측정. 배포만으로 자동 해소되지 않는다.
- [x] #21 reference/index.md 도구 목록에서 삭제 3종 제거 + how-to/doctor-migration.md 현행화 (마이그레이션 절차 제거·--fix/--diagnose 현행 거동 반영·파일명 보존으로 인바운드 링크 5곳 무손) + getting-started.md Troubleshooting 무효 항목 **삭제** (S1, 대체 절차·버전 분기 서술 금지) + docs_build --check 통과 + `pilot/docs/` 링크 검사 (**`test_doc_links` 는 docs/ 미스캔 — plan § G4 로 대체**) + md 외 변경 0 + `workspace/context/` 변경 0. **판정 주의**: #21 READY 는 #20 dogfooding 게이트 통과가 **아니다** (D-1 축소 — plan § #20 목표 체크박스 처리 방침 참조). (검증 2026-07-25 evaluator 독립 재실행: G1 `G1 OK 8` (listed==actual, ASCII 순) · G2 exit=1 · G2b `OH-[1-5]` exit=1 · G3 대장 5파일 전건 resolve·앵커 0·초과 0·`mkdocs.yml:98` nav 1건 유지 · G4 `checked 194 broken 0` · G5 `docs_build.py --check` exit 0 + `284 tests OK` · G6 축1 15행 **대장 자체를 소스로 재검증** — `doctor.py` argparse 4인자(`--diagnose` 부재)·`_common.Result` PASS/INFO/WARN/ERROR + `summarize` exit 0/1·`fix=` 정확히 3곳(`:380`·`:507`·`:802`)·`_fix_migrate_state_to_current` in-place write (백업 코드 0)·`v1`→`domain: null` 주입·`run_auto_fixes` 확인 프롬프트 0·`REQUIRED_GITIGNORE_PATTERNS=(".slack.env",)` 무조건 `write_text`·`--regen-agents` 힌트 4곳 전건 hint-only·`check_workspace`/`check_conventions_paths`/`check_project` 라벨 실측 = 문서 3카테고리 나열과 일치·`validate.yml` paths 5종 일치·SKILL.md § 진단 모드 4패턴/DIAGNOSIS 5필드/OH 발동조건 2·점검 5항목 일치 · WARN/ERROR 전건 hint 보유(AST 스캔 0건 누락) · G6 축2 3행 전건 **삭제** 처리 + 대체 절차·버전 분기 0 · G6 축3 무근거 문장 0 · 본문 file:line 0건(C2 확정) · G7 (a) skip — 증거 없음 / (b) 저장소 사본 회귀 재확인 (`files_to_read` 에 `wrapper-protocol.md`·`context/pilot/index.md` 실재, 미등록 힌트 부재) · 변경 4파일 전건 `.md` · `workspace/context/` diff 0 · `PLAN-manual.md`·SKILL.md·Python 무변경 · doctor `9 PASS · 4 WARN · 0 ERROR` (baseline 동일))
- [ ] #22 `/pilot:learn` 재실행으로 `workspace/context/pilot/` 삭제 스크립트 서술 3건 (memory-hint·init_detect·diagnose.py) 해소. 직접 Edit 0 (drift-protocol § A). 검증은 문자열 기준.
- [x] #25 `doctor --schema` ↔ `claude plugin validate` 중복 처리 방향 확정·반영. 게이트: **CI 가 현재 차단하는 결함을 계속 차단** (frontmatter 부재 = ERROR 유지 — CLI 는 WARNING 이라 단순 교체 시 느슨해짐) + 자체 유지 항목마다 "CLI 미커버" 근거 명시 + version↔git tag 검사 보존. (검증 2026-07-26 evaluator 독립 재현: 격리 사본(`scratchpad/repro/pilot`)에 손상본 주입해 **대조표 6행 중 4행 직접 재현, 전건 표와 일치** — ① SKILL frontmatter 부재 = CLI `--strict` WARN→**exit 1** / `doctor --schema` ERROR→exit 1 ② `plugin.json` 미지 키 `bogus_key` = CLI `--strict` WARN→**exit 1** / doctor **미탐 PASS→exit 0** ③ SKILL `description` 5199 bytes = CLI **미탐 통과→exit 0** / doctor ERROR→exit 1 ④ version↔git tag = 사본이 비 git 트리라 doctor WARN 발화 / CLI 정상 통과 = **CLI 미검사** 확인. 즉 **어느 쪽도 상위 집합이 아님**이 독립 실측으로 재확정. 게이트 3축: (a) CI 차단력 보존 — `.github/workflows/validate.yml` `git diff 8d3a868..HEAD` **빈 출력**(무변경, `:43 run: python3 pilot/tools/doctor.py --schema`) + frontmatter 부재 ERROR 재현 (b) CLI 미커버 근거 명시 — spec § 재실측 6행 표 + `pilot/README.md:145-150` "두 검사는 서로 대체하지 않는다" blockquote 실재 (c) version↔tag 보존 — `pilot/tools/doctor/schema.py` `git diff` **빈 출력**(410줄 무변경, `_check_version_tag` 실재). 코드 변경 0 = 결론 (ii) 현행 유지와 정합. 작업 트리 `git status --porcelain` 빈 출력 — 손상본은 scratchpad 사본에만)
- [x] #24 `pilot-update.sh` — (A) `CACHE_DIR` stale 경로(`claude-plugins` → `radiostart-plugins`) 해소 (B) 도구 존치 여부 결정 반영 (C) README·getting-started·릴리스 노트의 잘못된 업그레이드 안내 정정. 게이트: stale 경로 문자열 0건 + 안내가 실제 동작과 일치 + 전역 설치본 직접 조작 0. **잔여 1건(릴리스 노트) 해소 완료 (2026-07-26)** — 사용자 명시 승인 후 plan 스텝 2 절차 4단계 실행, `--json body` 재취득 diff 가 `## 업그레이드` 블록에 국한됨을 확인.
  - **[통과] 검증 완료분** (2026-07-26 evaluator 독립 재실행, 커밋 `b4e73e3`·`f0f01d5`):
    - **(A)·(B) D1 (iii) 폐기 이행** — `pilot/tools/pilot-update.sh` 삭제 실재 (`git diff --stat` -78줄). (A) 는 파일 소멸로 자동 해소.
    - **게이트 grep 2종 0건** — `grep -rn "marketplaces/claude-plugins\|pilot@claude-plugins\|marketplace update claude-plugins" pilot/` exit 1 (0건, 변경 전 9줄/10건) · `grep -rn "pilot-update" pilot/ .github/` exit 1 (0건, 변경 전 10건). 잔여 `claude-plugins` 전수를 재확인해 **레포 슬러그(`radiostart/claude-plugins`)·문서 사이트 URL 외 0건** — 과잉 치환 없음 (C8 방어 재현).
    - **(C) 저장소 내 3곳 정정 실재** — `README.md:35` 설치 명령 id (`pilot@radiostart-plugins`, 신규 설치 실패 버그) · `:42` 업데이트 2단계 + 세션 재시작 + 레포경로↔id 구분 blockquote · `:44-56` 헬퍼 alias 블록 → 조건부 서술 교체 · `:145` 업데이트 안내 · `getting-started.md:336-341` Troubleshooting 5 블록 + 허구 서술 삭제 (D4) · `release-and-upgrade.md:68` "수동 `pip`/`git pull`" 제거 (C3). C3 grep 0건.
    - **critic C1~C8** — C2 ✅ README `/plugin` 막힌 환경 문구가 단정형 아님 실측 ("시도해 볼 수 있으나 환경에 따라 불가" · "현재 pilot 측이 제공하는 우회 수단이 없다") · C3 ✅ · C4 ✅ `project.md` 전달사항 신규 3행 실재 (stale 무력화 행 포함) · C5 ✅ SSOT `project.md:166` 1곳만 갱신, 사본 `20-*.plan.md:80`·`21-*.plan.md:345`·`project.md:164` 는 미갱신 유지 실측 · C6 ✅ 게이트가 `features=N` 미사용 (실측 32) · C7 ✅ 기각 근거 plan 기재 · C8 ✅ 전수 열거 = grep 0건과 정합. **C1 은 미이행** (릴리스 노트 절차 자체가 미실행).
    - **게이트 재실행** — `docs_build.py --check` exit 0 · `doctor.py --schema` `6 PASS · 0 WARN · 0 ERROR` exit 0 · `doctor.py workspace` `10 PASS · 4 WARN · 0 ERROR` exit 0 (WARN 구성 = conventions 2 + plugin_version 1 + drift 1 = plan baseline 일치, #23 미머지 브랜치라 정상) · `python3 -m unittest discover -s tests/tools` **284 tests OK** exit 0.
    - **scope·전역 설치본 불가침** — `git diff --stat 8d3a868..HEAD` 변경 경로가 `pilot/**` 4파일 + `workspace/projects/build-plugin/**` 3파일뿐. `~/.claude/plugins/cache/radiostart-plugins/pilot/0.10.0/tools/pilot-update.sh` **실재 유지**(mtime 07-25 23:30) + 마켓플레이스 클론 HEAD `229b2a8` 불변 = 전역 설치본 쓰기 조작 **0** 의 직접 증거.
  - **[미통과] (C) 릴리스 노트 — spec 기대결과 (C) 가 열거한 4곳 중 1곳 미정정**:
    - 실측: `gh release view pilot-v0.10.0 --json body -q .body` 의 `## 업그레이드` 블록이 여전히 `pilot/tools/pilot-update.sh   # 캐시 갱신` 를 지시 — 본 사이클이 **삭제한 파일**이다. 게이트 "안내가 실제 동작과 일치" 불충족.
    - plan D2 = "릴리스 노트 정정: **한다**" (`.plan.md:17`, 사용자 승인 2026-07-25 Q0~Q5 전건 채택) + § 변경 파일 등재 + 게이트 7번째 + critic C1 accepted (백업→취득→교체→diff 4단계·롤백 경로 확정). 즉 **안전 절차까지 합의 완료된 항목**이다.
    - generator 는 실행 대신 spec `## Open Questions` (d)2 를 "범위 분리 (2026-07-26) … 사용자 명시 승인 시 별도 처리" 로 **같은 커밋에서 재작성**했다. 그러나 ① spec `## 요구사항` 기대결과 (C) 본문은 그대로 릴리스 노트를 열거 중 ② 새 유예를 승인한 사용자 지시가 workspace 어디에도 기록돼 있지 않고, 기록된 사용자 결정(D2)은 반대다. 요구사항을 구현 주체가 자기 커밋에서 완화한 것을 충족 근거로 삼을 수 없다.
    - 기술적 차단 없음 재확인: `gh api …/releases/tags/pilot-v0.10.0` → `{"draft":false,"immutable":false}` = 편집 가능.
    - 체크 조건 (택1): ⓐ plan 스텝 2 의 4단계 절차로 `## 업그레이드` 블록 교체 후 백업 diff 검증, 또는 ⓑ **사용자가 릴리스 노트 정정을 범위에서 제외한다고 명시 승인**하고 그 기록을 남긴다.
- [ ] #23 doctor 파서 오탐 2건 해소 — (A) `check_conventions_paths` 가 config 표 플레이스홀더를 실선언으로 오탐 (B) `count_real_features` 가 `.plan.critic.md` 를 feature 로 계수 (24 → 29 오계산 → 불필요한 `--regen-agents` 권고). doctor WARN 4 → 1 (남는 1건 = `plugin_version` 정상 감지). 정상 탐지 유지 (실선언 후 파일 부재 / 실제 spec 증가) + 기존 doctor 테스트 무손 + (B) 회귀 테스트 신규 + `integrity.py:517` analyzed 판정 불변.
- [x] #17 create-feature 3-ter · analyze 7.5 조건부 인터뷰 — unchecked Open Questions 존재 시에만 발동 (soft gate). 우선순위 (d)>(b)>(c)>(a), 상한 4/8, "나중에 결정" 항상 제공, 스킵 시 unchecked 유지 (무열화 degrade). 답변 spec 반영 + `- [x] {질문} → {답변 요약}` 체크. 산출물 대조 (scope lookup only, 코드 탐색 금지) 부재 심볼 → (a) 행 추가. scope 부재 시 대조 스킵 (A2). `--regen-agents` 미발동. 결과 요약 `인터뷰: 해소 N건 / 이월 M건` 라인. SSOT `context/shared/interview.md`. 에이전트·autopilot 무변경. (검증 2026-07-24: interview.md 7섹션 + 3-ter (create-feature SKILL.md:108-122) + 7.5 (analyze SKILL.md:179-189) + regen-mode.md item 6 + scope-sync.md 규칙 2 C1 키 + open-questions.md 상호 링크 + getting-started.md C6 시나리오. C1~C6 전건 실재, 링크 8건 해석 OK, doctor exit 0 · 0 ERROR, markdown-only (`.py` 변경 0), 회귀 픽스처 무변경)

---

<!-- [analyze-managed] -->
## 프로젝트 고유 항목

- [x] #01 다중 확장자·확장자 없음 케이스 v1 외 (`Makefile`·shebang) — fallback 폴더 인접성 적용 확인
- [x] #01 config 표 컬럼 수 불일치 시 doctor ERROR
- [x] #01 lookup 우선순위: config 행 → 폴더 인접성 fallback (D10 default 폐지로 SKILL.md default 부재). 동일 (언어, 역할) 키는 config 만 있음
- [x] #01 D10 적용 — SKILL.md (learn) Phase 2 본문에서 default 표 2 개 모두 제거. config.md 두 표 헤더만. fixture pass-valid 두 표 헤더만. 세 곳 동기화
- [x] #02 MANIFEST 진입 파일에 scope 헤더 없음 → 5-2 가 해당 표만 skip + INFO 1 줄. `analyzed:true` 정상 게이트
- [x] #02 scope 파일 자체 부재 → 동일 skip (기존 5-2 거동과 일관)
- [x] #02 config 빈 표 → SKILL.md default 사용 (= 부재와 동일 처리)
- [x] #03 H3 SSOT 분리 검증: H3 헤더 = `/pilot:project` 1 회 생성, 표 본문 = `/pilot:analyze` 또는 create-feature 매번 갱신
- [x] #03 사용자 수동 추가 H3 (config 외) = 양쪽 모두 보존
- [x] #03 사용자가 H3 삭제 → 재실행 시 복구 안 함 (사용자 의도)
- [x] #03 example/project.md `## 관련 파일` H2 부재 → H2 + H3 모두 새로 생성
- [x] #04 부적절 헤더 문자 (슬래시·콜론·#·|) 포함 시 ERROR + 행 위치·차단 문자 안내
- [x] #04 scope 헤더 컬럼 `## ` prefix 위반 시 ERROR
- [x] #04 행 수 0 허용 (D10) — 빈 표 → INFO 1 줄 ("폴더 인접성 fallback 동작"), ERROR 아님
- [x] #05 감지 조건: `.agent-state.yml.plugin_version` 0.1.x 또는 부재 + 현재 plugin v0.2.0+ + `## learn 언어 패턴` 두 표 모두 빈 행
- [x] #05 opt-in (a) → v0.1.0 default 5 언어 + 6 역할 표 자동 주입 + `migration_v0_2_0: accepted` + `plugin_version: 0.2.0`
- [x] #05 opt-out (b) → config 빈 채로 + `migration_v0_2_0: declined` + `plugin_version: 0.2.0`
- [x] #05 postpone (c) → 변경 없음, 다음 `--fix` 호출 시 다시 묻기
- [x] #05 non-interactive 환경 (stdin.isatty()=False) → 자동 미루기 + INFO 1 줄, hang 방지
- [x] #05 부분 정의 사용자 (어느 한 표 행 > 0) → skip + INFO ("부분 정의됨 — 사용자 직접 갱신 권장")
- [x] #05 신규 사용자 (`plugin_version: 0.2.0` 부터) → skip
- [x] #05 `--fix` 미호출 (기본 doctor) 시 마이그레이션 prompt 발생 안 함 (`run_auto_fixes` 가 `--fix` 모드에서만 호출)
- [x] backward-compat 0 brittle: 회귀 골든 픽스처 `pilot/tests/fixtures/v0.1.0-baseline/` 로 config 비어있을 때 v0.1.0 = v1 동일 출력 검증 (0a + 0b 캡처 완료. 실제 회귀 실행 = `bash diff.sh --actual {regen}` 미실행. 디렉터리 명 정합 후 1 회 수행 필요) — **#18 폐기 (2026-07-24)**: 수동 회귀 하네스 (diff.sh·expected) 삭제 감사 승인으로 본 검증 항목 자체가 소멸 (project.md 전달사항 #01·#04·#05 행 (b)·(c) 폐기 기록)
- [x] #09 `/pilot:learn` Phase 2 외부 도메인 reference 추출 절차 명시 (내부 vs 외부 namespace 분류, ignore 패턴 12 항목 default, A2 runtime fallback). `/pilot:create-feature` 3-bis · `/pilot:analyze` 5-2 의 cross-domain detect (MANIFEST 외부 도메인 lookup → INFO 1 줄)
- [x] #10 MANIFEST.md `## 외부 도메인 reference (learn 미완료)` 섹션 자동 작성 (3 컬럼 표). 추정 도메인 알고리즘 1 순위 (`Module::Class` namespace 첫 segment 소문자화). 추천 경로 (`app/{models,services,controllers}/{도메인}/`). idempotency (현재 learn 시 자기 행 제거 + 도메인 분류 표 등록 시 INFO). doctor `check_workspace_external_domain_section` schema 검증 (3 컬럼 + 헤더 정확 일치 + stale row INFO). MANIFEST.md.template placeholder 주석 추가
- [x] #11 `/pilot:create-feature` 가 features/NN-*.md 작성 시 `## Open Questions` 4 카테고리 (a/b/c/d) 강제 + 빈 카테고리 `- (없음)` 표시. 3-bis cross-domain detect 결과를 (b)/(c) 로 자동 분류. `/pilot:analyze` 5-2 가 기존 Open Questions 섹션 보존 + 갱신. doctor `check_features_open_questions` schema 검증 (섹션 부재 INFO, H3 누락 INFO, ERROR 없음 — backward-compat). 4 픽스처 (pass-empty/pass-valid/info-missing-section/info-missing-h3) + 4 unit 테스트 PASS
- [x] #12 `/pilot:learn` Phase 3 transaction nesting Grep 패턴 추가 (`\.transaction\s*do\s*$|ActiveRecord::Base\.transaction|\w+Record\w*\.transaction` ±20 줄 Read). Phase 3 추출 항목에 cross-domain transaction nesting (외부 namespace 만, 본 도메인 nesting 제외 = Open Q d-4) + 변경 type 매핑 (`update→write`/`destroy→destroy`/`find→read`/`create→create`). Phase 4 step 2 신규 — `### Cross-domain Transaction Contracts` sub-section (4 컬럼 표) 자동 작성. inline vs 분리 룰 (5 행 임계 = Open Q d-3). `(auto)` 마커 + idempotency. A2 runtime fallback (detect 실패 시 placeholder 행, abort 안 함). doctor `check_domain_transaction_contracts` schema 검증 (4 컬럼 + 헤더 정확 + 변경 type 화이트리스트). 7 픽스처 + 7 unit 테스트 PASS. backward-compat — 섹션 부재 시 INFO 만
- [x] #13 `/pilot:init` 1.5 단계 wizard 신설 (`config.md created` 조건 + `--no-wizard` 자연어 분기). `pilot/tools/init_detect.py` (Python 표준 라이브러리만, 의존성 0) — `detect_languages` (상위 3 확장자 → features/01 5 default 언어 매핑) · `detect_scope_candidates` (depth ≤ 2 폴더 빈도 ≥ 1, Q1 적용) · `IGNORE_BASELINE` 10 패턴. SKILL.md 본문 3 군데 갱신 (`### 2. wizard 적용`, `## 결과 출력` 3 줄, `## 참고` `--no-wizard` 단락). 회귀 fixture `wizard/expected/config.md` 캡처 + `diff.sh EXPECTED_SUBDIRS` 4 번째 항목 추가. 단위 테스트 8/8 PASS. spec line 24 Q1 patch (≥ 2 → ≥ 1) 적용
- [x] #14 `pilot/docs/getting-started.md` 신설 (324 줄, 250~350 범위) + `pilot/README.md` line 9 callout 1 줄 추가. 5 step (init→learn→project→create-feature→planner) + 사전 준비 + troubleshooting 5건 (case 2 = `wizard 잘못 매핑 정정 경로`, Q7 교체) + timing 측정 가이드. 더미 저장소 `${CLAUDE_PLUGIN_ROOT}/tests/fixtures/v0.1.0-baseline/_input/python-sample` 을 `/tmp/pilot-tutorial/` 로 복사 후 진행. 모든 출력 캡처는 핵심 3~5 줄 + `... (생략)` 처리 (Q3). 한국어 본문 (Q5). Q1~Q7 모두 반영. plan-validate exit 0. SKILL.md 명령 형식 정합 (`/pilot:init`·`/pilot:learn <path>`·`/pilot:project {name}`·`/pilot:create-feature {prompt}`·`@pilot-planner`). 인수인계 line 122·123·124 (#13 후속) 모두 가이드 본문에 반영
- [x] #15 `/pilot:tdd` 4 분기 (on/off/--fix/상태 보고) 재구성. `pilot/skills/tdd/SKILL.md` 본문 4 절 + 각 사용자 출력 형식 명시. `pilot/skills/context/modes/tdd-activation.md` §1-1b (백업 마커 주입) + `## 비활성화 절차` off-1~off-7 + literal 매칭 정확 문자열 (§1-1b·off-2·off-3) 추가. `pilot/tools/doctor/integrity.py:549-573` 의 `check_project` `tdd 정합성` 블록 2-way → 3-way 확장 (state ↔ project.md ↔ prompts/*.md 백업 마커 기준). 함수 시그니처 `check_project(workspace, project)` 보존, 호출자 영향 0. 회귀 fixture `tdd-on/expected/` + `tdd-off/expected/` 신설 (5 파일씩 — state.yml + project.md + prompts/{planner,generator,evaluator}.md). diff.sh `EXPECTED_SUBDIRS` 에 2 행 추가, 6 서브디렉터리 [OK]. spec drift T1 (line 7) + T2 (line 64-65) Q9 patch 적용. `pilot/docs/getting-started.md` line 200·202 broken link 정정 Q10 (인수인계 line 126 소비). `pilot/skills/project/SKILL.md` patch 없음 (Q6). plugin.json version bump 없음 (Q8). `.plan.md` 손대지 않음 (Q5)
- [x] #16 Doctor onboarding-health (OH-1~5 5룰) — 구조: OH-1 (config 3섹션 행 수 ≥ 1) · OH-2 (scope/ *.md ≥ 1) · OH-3 (STATE.md 진행중/대기 ≥ 1) · OH-4 (MANIFEST 도메인 분류 행 ≥ 1) · OH-5 (features/ *.md ≥ 1, project 인자 시만). `check_onboarding_health(workspace, project=None)` dispatcher + 5 `_check_ohN_*` 함수 (integrity.py). doctor.py re-export 추가. SKILL.md 본문 1 단락 + Q5 drift 정정 (line 77·99 → 3-way wording, line 77 본문 + line 126 [PASS] 예시). fixture 2 케이스 (`doctor-onboarding/expected/pass-only/` + `warn-mixed/`). diff.sh `EXPECTED_SUBDIRS` 2 행 추가. `--fix` skip + INFO 1줄. early return 분기 (integrity.py:2025-2043) 에 OH-1~4 호출 + OH-5 N/A + WARN ≥ 4 시 안내 1줄 + `--fix` skip 추가. warn-mixed expected output 재캡처 (Project 섹션 0 · OH 섹션 8 줄). config.md `## scope 카테고리` 표 3 컬럼 정정. plan line 161 정합 주석. 실 doctor 호출 3건 (pass-only --project · warn-mixed · --fix) 모두 expected 와 byte-clean MATCH
- [x] #06 learn SKILL.md Phase 1 자동 도출 규칙 list (line 82-84) 에 3 sub-bullet 추가 — 일반 진입점 부모 폴더명 fallback (부모→2단계 상위→사용자 질의, A2 패턴 abort 없음) + 도메인명 sanitize (영숫자·하이픈 외 제거 + 소문자화) + 절대경로 정규화 (정규화 실패 시 사용자 질의). Phase 5 step 2 (line 304-306) `## 도메인 분류` 형태 detect 표 직후 blockquote 2 단락 추가 — H2 헤더 정확 매칭 강제 (정규식 `^##\s+도메인\s*분류\s*$` 인용 + 본문 prose 동일 string 등장 무시) + 코드블록 펜스 (` ``` `) 안 줄 무시 (`_parse_md_tables_in_section` 코드블록 추적 보강 정합 — integrity.py:807·811-820). 변경 파일 1개·7 라인 추가만. 회귀 fixture·doctor·script 변경 없음 (NS #5 검증 거동 동일 명문화). getting-started.md drift 점검 결과 영향 0 (Phase 1·5 출력 코드블록에 본 wording 미등장)
- [x] #07 analyze SKILL.md 5-1 ↔ 5-2 사이에 신규 H4 `#### 5-1.5. scope/{domain}.md 자동 생성` 삽입 (analyze SKILL.md:208-240, 34 라인 추가). 트리거 조건 (scope 부재 + MANIFEST H2 헤더 존재) + 본문 구성 (H2/표 헤더 = config `scope 헤더`/`표 헤더` 컬럼 그대로) + 본문 추출 우선순위 3단 (inventory.md → index.md → 빈 표 + INFO) + idempotency (기존 파일 보존 + 사용자 수동 행 보존) + A2 runtime fallback (abort 없이 빈 표 + INFO + 5-2 진행) + 예외 4건 (MANIFEST 부재 / config 빈 표 → features/02 default / inventory.md 부재 → 2·3순위 / scope 헤더 prefix 위반 → doctor 사전 차단). wizard 인용 주입 SSOT blockquote (analyze SKILL.md:226) 로 인수인계 line 123 (#13 후속) 직접 소비. 회귀 fixture·doctor·script 변경 없음 (NS #5 검증 거동 동일 명문화)
- [x] #08 project SKILL.md line 63 직후 nested blockquote 1 단락 추가 (project SKILL.md:65-80, 18 라인). 5 요소 모두 반영 — H1 정확 매칭 정규식 (`^#\s+.*\{프로젝트명\}.*$` 단순화 채택, Q3) · 보존 대상 3 (가이드 주석 self-reference · 코드블록 · 표 본문 셀) · 사용자 프로젝트명 sanitize (`[a-zA-Z0-9가-힣\-_]` 외 차단 + 사용자 질의 prompt) · A2 runtime fallback (H1 토큰 부재 → 치환 skip + INFO 1 줄 + abort 안 함, 인수인계 line 31 #04 소비) · 대상 파일 4 종 (`project.md` 1 + `prompts/{planner,generator,evaluator}.md` 3). example template 본문 변경 없음 (backtick wrap 이미 완료, 인수인계 line 101 #03 소비). 회귀 fixture·doctor·script 변경 없음 (NS #5 검증 거동 동일 명문화). list item 안 nested blockquote 들여쓰기 정합 (2 spaces) — H3 동적 채움 blockquote (line 88~) 와 같은 list item 안 공존

---

## 일관성

- [x] 언어 컨벤션 준수 ([`coding.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/coding.md) 참조)
- [x] 기존 코드 패턴과 조화 (불필요한 리팩토링 없음)

---

## 테스트

- [x] 회귀 픽스처 자동 검증 (`pilot/tests/fixtures/v0.1.0-baseline/`) — config 비어있을 때 v1 출력 = v0.1.0 출력 (0b `_input/`+`expected/` 캡처 완료. 실제 `diff.sh --actual {regen}` 실행 미수행 — 디렉터리 명 정합 후 1 회 수행 필요) — **#18 폐기 (2026-07-24)**: diff.sh + expected 캡처 삭제 감사 승인으로 회귀 검증 경로 소멸 (자동 테스트 픽스처 5종은 보존·별도 unittest 가 소비)
- [x] config 신규 섹션 정의 시 override 거동 (사용자 행이 default 위에 우선 적용) 검증 (#01·#02·#03 의 runtime lookup 미구현) — **#18 폐기 (2026-07-24)**: 검증 수단이던 수동 회귀 하네스 삭제 승인으로 폐기. override 거동 자체는 LLM 스킬 (learn/analyze/project SKILL.md lookup 절차) 이 담당 — 실사용 중 이상 발견 시 재상정
- [x] `pilot/tests/tools/test_doctor_integrity.py` (#04) — 7/7 PASS (test_pass_empty_table 신규 포함)
- [x] `pilot/tests/tools/test_doctor_migration.py` (#05) — 7/7 PASS (opt-in/out/postpone, 신규/부분/non-interactive/v010 detect)
- [x] `pilot/tests/tools/test_doctor_external_domain.py` (#10) — 5/5 PASS (pass-empty/pass-valid/error-column-mismatch/error-header-mismatch/info-stale-row)
- [x] `pilot/tests/tools/test_doctor_cross_domain.py` (#09) — 2/2 PASS (info-stale-row-bidirectional / no-error-on-valid-manifest)
- [x] `pilot/tests/tools/test_doctor_open_questions.py` (#11) — 4/4 PASS (pass-empty/pass-valid/info-missing-section/info-missing-h3)
- [x] `pilot/tests/tools/test_doctor_cross_domain_transaction.py` (#12) — 7/7 PASS (pass-no-subsection/pass-inline/pass-separated/pass-empty/error-column-mismatch/error-header-mismatch/error-bad-type)
- [x] 해피패스 커버 (pass-empty + pass-valid + 빈 표)
- [x] 에러 케이스 처리 (#04 doctor 검증 ERROR 케이스)
- [x] 기존 테스트 영향 없음 (doctor --schema 5 PASS·1 WARN·0 ERROR 유지, doctor workspace 9 PASS·1 WARN·0 ERROR)

> **비 TDD 프로젝트**는 자동 테스트 실행 단계가 없다. "읽기만 하고 끝" 을 피하려면 아래 수동 확인 중 적합한 것을 선택:
>
> - dev server / console 에서 기능 직접 실행 (UI / API 응답 육안 확인)
> - 대표 시나리오를 수기 테스트 케이스로 `## 테스트` 에 체크 항목으로 추가
> - 변경 주변 기존 테스트가 있으면 `{test_command} {경로}` 로 회귀 확인

---

## 전달사항 작성 가이드

래퍼가 검토 완료 후 요구하는 `## 에이전트 간 전달사항` (project.md) 기록 기준.

**전달할 것:**

- 신규 메서드·서비스·상수 추가 — 다음 feature 에서 재사용 가능성
- 모델 스키마·상태값 변경 — 후속 feature 의 가정 조건이 바뀜
- 제약·엣지 케이스 발견 — 다음 계획에 선행 반영 필요
- 공통 패턴 정립 (예: 특정 factory 콜백 우회 기법) — 다른 spec 재사용

**전달하지 않을 것:**

- 구현 디테일 (코드에 이미 있음 — 읽으면 됨)
- 완료된 체크리스트 항목 (이 파일에 `[x]` 로 반영됨)
- 일반적 언어·프레임워크 관행 (팀 `conventions_doc` 에 이미 있음)

**형식:**

```markdown
- [ ] {내용 1줄 + 후속 feature 에서의 반영 방향} (from #{완료 feature 번호})
```

**예:**

- [ ] `OrderService.reset_for_test` 추가됨 → #12 시점에 제거 판단 필요 (from #11)
- [ ] `order_status` 에 `pending` 값 추가 → #13 관리자 화면에서 필터 추가 필요 (from #11)

전달할 사항이 없으면 `## 에이전트 간 전달사항` 섹션을 건드리지 않는다 (빈 항목 추가 금지).
