# 감사 축 1 — 참조 그래프 (원본 결과)

## A. 참조 그래프 요약

**진입점 4종에서 출발한 로드 체인** (전수 추적 완료):

1. **`.claude-plugin/plugin.json`** → `agents/*.md` 5개·`skills/*/SKILL.md` 17개·`hooks/hooks.json` 자동 발견. `PLUGIN_SCHEMA_NOTES.md` 는 doctor 도구·스킬이 역참조 (사용 중).
2. **`hooks/hooks.json`** → 셸 훅 5종 전부 연결 (`commit-format` `protect-managed` `scope-guard` `coding-rules` `slack-notify`). Python 호출은 인라인 `python3 -c` 와 `slack-notify.sh → tools/slack-notify.py` 뿐.
3. **`agents/*.md` 5개** → `tools/orchestrate-load.py`·`plan-validate.py`·`slack-notify.py` + `skills/context/` 의 `identity.yml` `guardrails.md` `state-schema.md` `plan-schema.md` `drift-protocol.md` `characterize.md` `rgr.md` `coding.md` `scope-exploration.md` `review-principles.md`.
4. **`skills/*/SKILL.md` 17개** → `tools/` 의 `doctor.py`(→`doctor/` 패키지 4모듈) `confluence.py` `init_detect.py` `auto_pilot.py`(→`verify-report-lint.py` 동적 로드) `plan-validate.py` `regen-verify.py` `memory-hint.py`(preamble 경유) + 각 스킬 `references/` 하위 문서 전부 + `examples/code-review/{lang}.md` + `setup/templates/` 3종 + `context/shared`·`modes`·`lifecycle` 문서.
5. **CI/사람 경로**: `.github/workflows/docs.yml` → `tools/docs_build.py` → mkdocs / `tests.yml` → `tests/` / `README.md` → `tools/pilot-update.sh`·`release.sh`.

**결론**: `tools/` 13개 파일 전부, `hooks/` 6개 전부, `skills/context/` 30개 문서 전부 참조 체인이 존재한다. 진짜 고아는 테스트 픽스처 1개 폴더와 examples README 1개뿐.

## B. 미참조 파일 (삭제 후보)

| 파일 | 줄수 | 역추적 근거 | 위험도 |
|---|---|---|---|
| `pilot/tests/fixtures/handoff-quality/bad/05-vague.plan.md` | 26 | `handoff-quality` 저장소 전체 grep → pilot/ 내부 0건. 소비 도구 `handoff-quality.py` 가 이전 감사(`docs/audits/2026-07-10-pilot-structure-audit.md` L9~L14, "소비처 없는 고아 도구")에서 삭제됐는데 픽스처만 잔존. `test_plan_validate.py` 는 픽스처 미사용(인라인 생성). 베이스네임 grep 도 0건 | 하 |
| `pilot/tests/fixtures/handoff-quality/bad/06-empty-changes.plan.md` | 13 | 동일 — `06-empty-changes` grep 0건 | 하 |
| `pilot/tests/fixtures/handoff-quality/good/03-payment.plan.md` | 27 | `03-payment` grep 1건은 `verify-reports/valid/01-ready-tdd.md` 내부의 `features/03-payment.md` 라는 우연한 동명 문자열 — 본 파일 참조 아님 | 하 |
| `pilot/tests/fixtures/handoff-quality/good/04-refund.plan.md` | 20 | 동일 — `04-refund` grep 0건 | 하 |
| `pilot/examples/code-review/README.md` | 53 | `code-review/README`·`examples/code-review` grep → 참조는 `code-review-init/SKILL.md` 의 `{lang}.md` 패턴뿐, README 자체 참조 0건. 단 유지보수자용 폴더 설명 문서라 삭제 대신 유지도 합리적 | 하 |

`examples/code-review/{java,javascript,kotlin,php,python,ruby,typescript}.md` 7종은 전부 `{lang}` 슬러그 매핑으로 실사용 — 삭제 후보 아님.

## C. 테스트 전용/약한 참조 파일

| 파일 | 줄수 | 역추적 근거 | 위험도 |
|---|---|---|---|
| `pilot/tests/fixtures/v0.1.0-baseline/diff.sh` | 115 | 자동 테스트 미참조 — 픽스처 README 의 수동 회귀 절차에서만 호출 | 중 |
| `v0.1.0-baseline/{learn,project,analyze,wizard,tdd-on,tdd-off,doctor-onboarding}/` (계 37파일) | ~1,338 | `diff.sh` 의 `EXPECTED_SUBDIRS` 로만 소비 (수동 회귀 하네스). 자동 테스트가 쓰는 것은 `external-domain`·`transaction-contracts`·`config`·`migration`·`open-questions` 뿐 | 중 |
| `pilot/skills/context/lifecycle/INDEX.md` | 59 | 런타임 로더 0건 (`lifecycle/INDEX` grep 외부 참조 없음). 본문 스스로 "에이전트 wrapper — 본 INDEX 미참조" 명시. 사람용 라우터로 의도된 문서 | 상 |
| `pilot/skills/context/lifecycle/setup/README.md` | 80 | `lifecycle/INDEX.md` 링크뿐. `/pilot:init` 은 `setup/templates/` 를 직접 참조. 사람용 온보딩 문서 | 상 |
| `pilot/skills/context/lifecycle/issues/example/issue.md` | 40 | `lifecycle/INDEX.md` 링크뿐. `/pilot:issue` 는 `issues/GUIDE.md`(인라인 템플릿 보유)를 로드하고 example 은 미링크 — `projects/example/` 이 `/pilot:project` 에서 런타임 복사되는 것과 대조적 | 중 |
| `pilot/docs/PLAN-manual.md` | 291 | `mkdocs.yml` 의 영구 exclude 에만 등장 ("SDLC 메타 산출물, 사이트 콘텐츠 아님" — 의도적 보존) | 상 |
| `pilot/tools/pilot-update.sh` / `tools/release.sh` | 78 / 99 | 에이전트 런타임 참조 0 — `README.md` 의 사람 실행 절차(업데이트 alias·릴리스)에서만 참조. 의도된 ops 스크립트 | 상 |
| `pilot/tools/docs_build.py` | 420 | 스킬·에이전트·훅 참조 0 — `.github/workflows/docs.yml` 이 CI 에서 실행 + `tests/test_docs_build.py`. **CI 전용, 실사용** | 상 |

## D. 특이사항

1. **docs ↔ docs-site 관계**: `docs/` 가 mkdocs 소스(tutorial·how-to·explanation 은 커밋됨). `docs/reference/{agents,skills,tools}/` 와 `reference/identity.md` 는 `docs_build.py` 생성물로 **gitignored** (커밋된 것은 `reference/index.md` 뿐). `docs-site/` 는 `mkdocs build` 산출물 전체가 gitignored — 로컬에 116파일 존재하나 git 추적 0. CI(`docs.yml`)가 PR 마다 재생성·strict 검증, main push 시 `gh-deploy` 로 gh-pages 배포. 구조적으로 drift 불가 — 건전.
2. **로컬 stale 생성물**: `docs/reference/skills/fix-review.md` — fix-review 스킬은 커밋 `e078d88` 에서 삭제됐으나 `docs_build.py` 가 출력 디렉터리를 clean 하지 않아 로컬에만 잔존(untracked, CI 는 fresh checkout 이라 무해). `docs_build.py` 에 stale 출력 정리 로직 추가 여지.
3. **깨진 참조 없음**: `skills/`·`agents/`·`hooks/` 의 `${CLAUDE_PLUGIN_ROOT}` 및 상대 링크 260건 실존 검증 → 실제 깨진 참조 0 (검출된 것은 `projects/GUIDE.md` 의 `features/01-<slug>.md` 류 플레이스홀더와 `protect-managed.sh` 정규식 오탐뿐).
4. **code-review-init 의 미구현 언어**: SKILL 이 `go`·`rust`·`swift`·`sql` 슬러그를 언급하나 `examples/code-review/` 에 해당 파일 없음 — SKILL 이 "부재 시 비활성 (전략 B/C 만 제시)" 로 명시적 graceful 처리라 결함 아님.
5. **(환경 관찰)** 감사 세션에 로드된 pilot 스킬은 15종으로 `autopilot`·`code-review-init` 이 빠져 있음 — 설치본(마켓플레이스 캐시) 버전 차이로 추정, 저장소 파일 문제 아님.

**총평**: 이전 감사(2026-07-10)가 고아 도구를 이미 정리해 참조 위생이 좋은 상태. 확실한 삭제 후보는 `tests/fixtures/handoff-quality/` 4파일(86줄)이 유일하고, 나머지는 사람용 문서·수동 하네스로 의도된 약한 참조다.
