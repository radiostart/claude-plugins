# 릴리스 노트

pilot 의 버전별 변경 이력입니다. 버전 SSOT 는 `pilot/.claude-plugin/plugin.json` 의 `version` 이며, 이 사이트의 표기는 그 값에서 파생됩니다.

!!! info "업데이트 방법"
    ```
    /plugin marketplace update radiostart-plugins
    /plugin update pilot@radiostart-plugins
    ```

    적용하려면 **세션을 재시작**해야 합니다. semver 기준·`.agent-state.yml` schema 마이그레이션은
    [릴리스 · 업그레이드](explanation/release-and-upgrade.md) 를 참조하세요.

커밋 단위의 원본 변경 목록은 [GitHub Releases](https://github.com/radiostart/claude-plugins/releases) 가 SSOT 입니다. 이 페이지는 사용자 관점의 요약만 담습니다.

## 버전 목록

| 버전 | 날짜 | 요약 |
|---|---|---|
| [**v0.17.0**](#v0170) | 2026-08-25 | autopilot 신호 파서 fail-open 봉쇄 · plan 판정 기계 소유 · reflect 재검증 |
| [v0.16.0](#v0160) | 2026-08-25 | 스킬 3종 신설 (qa · switch · ask) · learn 기재 규격 · scope-guard 경로 판정 |
| [v0.15.0](#v0150) | 2026-08-03 | evaluator REPORT 영속화 · 훅 양립 갱신 절차 · 스킬 description 감량 |
| [v0.14.0](#v0140) | 2026-08-01 | issue 단건 사이클 · Open Questions 게이트 · knowledge-sync · 스킬 리네임 |
| [v0.11.0](#v0110) | 2026-07-31 | doctor 리네임 · Claude 5 하니스 정합 · 에이전트 모델·effort 조정 |
| [v0.10.1](#v0101) | 2026-07-26 | doctor 오탐 2건 수정 — 판정을 문자열 규약에서 구조 기반으로 |
| [v0.10.0](#v0100) | 2026-07-25 | 스킬·에이전트 전면 재작성 · 도구 30% 슬림화 |
| [v0.9.0](#v090) | 2026-07-24 | 조건부 인터뷰 (Open Questions 소비) · 경량 산출물 대조 |
| [v0.8.0](#v080) | 2026-07-10 | 구조 감사 반영 · 광역 회귀 soft gate · 리뷰 축 통합 |
| [v0.7.1](#v071) | 2026-06-10 | `context/boundaries/` 를 문서·컨벤션에 반영 (문서 패치) |
| [v0.7.0](#v070) | 2026-06-10 | cross-domain 경계 계약 — 접점 비례 비용의 외부 도메인 학습 |
| [v0.6.0](#v060) | 2026-06-10 | evaluator 독립 검증 강화 · characterize 잠금 이중화 |
| [그 이전](#v050) | ~2026-05-21 | v0.5.0 · v0.3.1 · v0.2.1 · v0.2.0 |

---

## v0.17.0

*2026-08-25 · **현재 버전** — 태그·GitHub Release 미발행 (main 과 이 사이트에만 반영된 상태)*

`/pilot:autopilot` 의 전이 결정기(`tools/auto_pilot.py`)에 대한 HOTL 결함 수리 릴리스입니다. 파서에 실입력을 넣은 1차 검토와 독립 에이전트의 적대적(red-team) 검토로 확인된 fail-open 경로를 전부 정지(fail-closed)로 전환했습니다.

- **신호 파서 fail-open 9경로 봉쇄** — 멈춰야 할 때 통과하던 경로 전부 실측 재현 후 차단:
    - evaluator: 템플릿 에코 `- status: READY | NOT_READY` 가 첫-토큰 절삭으로 READY 판정되던 건 (status 는 이제 정확 매치) · 유보 붙은 `READY (조건부 …)` · 블록 내 `status` 키 중복 시 마지막 값 승 · REPORT 블록 복수(장식 헤더 `— 재평가 (2차)` 포함) 시 stale 블록 채택
    - critic: 챌린지 일부의 severity 만 파싱 실패 시 나머지로 판정 (blocking 은닉) · 헤더 없이 비표준 severity 값만 있을 때 0건 통과 · 통과 문구 `plan 통과` 서브스트링 오탐 (전체-행 정확 매치로 교체)
- **plan 판정 기계 소유** — planner 단계 판정을 `--plan-file`·`--state-file` 로 재정의: auto_pilot 이 plan-validate 를 직접 실행하고 mode 를 `.agent-state.yml` 에서 직접 도출한다 (`tdd: false` 의 인라인 주석도 정확 처리). `--plan-valid`(모델이 exit code 를 옮겨 적던 인자) 폐지. 잔존 신뢰 경계: 파일 경로 선택은 여전히 호출자 몫
- **정지 사유 정밀화** — 검증 실행 불능(plan/state 파일 부재·mode 도출 실패·plan-validate 크래시·usage 오류)은 `plan-validate` 대신 `agent-error` 로 정지 — 처방표가 "plan 보완"을 오도하지 않는다. plan-validate 의 stdout(JSON)은 폐기해 결정 JSON 과의 혼선 차단, stderr(누락 항목)는 통과
- **reflect 후 plan 재검증** — critic 챌린지 반영으로 plan 이 수정된 뒤 plan-validate 를 재실행해야 generator 로 진행 (실행당 최대 1회 — 루프 없음)
- **대소문자 severity 허용** — `Severity:` 표기가 signal-parse 정지 대신 정상 파싱되어, blocking 이면 처방이 더 정확한 `critic-blocking` 으로 안내
- 테스트 481 → 504 (적대적 입력 23종 추가 — 부분 파싱·decoy 재균형 등 파서가 못 잡는 자유형 일탈은 known limitation 으로 테스트에 명기)

!!! note "의도된 조임"
    계약을 지키는 산출물도 드물게 새로 정지할 수 있습니다 — 예: critic 제안 본문에 severity 인용 불릿, `- status: READY ✅` 글리프. 정지 비용은 사용자 확인 1회 + 해당 에이전트 재호출이며, [`stop-remediation.md`](https://github.com/radiostart/claude-plugins/blob/main/pilot/skills/autopilot/references/stop-remediation.md) 의 기존 처방이 그대로 적용됩니다.

## v0.16.0

*2026-08-25 · 태그 없음 — v0.17.0 릴리스에 포함*

- **신규 스킬 3종** — `/pilot:qa` (Jira 결함 처리 phase — qa/ 사이클·features 읽기 전용 잠금·회귀영향 게이트) · `/pilot:switch` (최근 작업 목록 조회·전환 — 미완 이슈 재발견) · `/pilot:ask` (도메인 컨텍스트 → 소스 순 읽기 전용 구현 질의)
- **learn 기재 규격 신설** — 기재 층위 L1/L2/L3 (구현 세부는 소스에 맡김) · Routes 표 선별 기재 + 고지 3줄 · 멀티 DB 귀속 전수 대조 · 부재 주장 반증 의무 · 심볼 앵커 우선 인용 → `learn/references/extraction.md`
- **doctor 인용 drift 검사** — context 문서의 소스 인용 mtime 대조로 stale 산출물 감지 (learn 재실행 처방)
- **scope-guard 경로 판정·gitignore 규약** — 심링크·비정규 표기에서의 무음 해제 차단, 루트 앵커 vs `**/` 임의 깊이 구분, substring 오차단 해소 (테스트 24종)
- **대상 plan 확정 SSOT (`plan-target.md`)** — wrapper 3종의 후보 조사·집계 규칙 단일화 (READY eval 필터·셸 글롭 금지), autopilot 은 wrapper 호출 프롬프트에 대상 명시 의무
- **Slack 이슈 오전송 차단** — 활성 행이 issue 면 동명 프로젝트 채널로 새지 않음. description 예산·preamble 커버리지 기계 게이트 신설

가이드: [QA 결함 처리](how-to/qa-cycle.md) · [작업 전환·재발견](how-to/switch-work.md) · [구현 질의](how-to/ask-code.md)

---

## v0.15.0

*2026-08-03 · [릴리스](https://github.com/radiostart/claude-plugins/releases/tag/pilot-v0.15.0)*

- 프로젝트 모드 evaluator REPORT 영속화 — `features/NN-{slug}.eval.md` 저장 + protect-managed 훅 재생성 예외
- critic·autopilot·focus 갱신 절차를 훅과 양립하게 개정 — 기존 파일 갱신은 Edit 기반
- Slack 활성화 기본 이벤트에 `pr` 포함 — `complete,approval,pr` 로 통일
- 스킬 description 7종 감량 — 상시 시스템 프롬프트 비용 3,777B → 2,208B

---

## v0.14.0

*2026-08-01 · [릴리스](https://github.com/radiostart/claude-plugins/releases/tag/pilot-v0.14.0) · v0.12.0 · v0.13.0 의 변경을 함께 담은 롤업 태그입니다 (그 두 버전은 별도 태그 없음).*

- **issue 단건 사이클 + 폴더 slug** — `/pilot:issue` 가 경량 모드에서 사이클 지원으로 재정의. orchestrate-load 가 STATE.md 의 `| issue | {이슈명} |` 행을 인식해 (`work_mode` 계약) planner→critic→generator→evaluator 를 `issues/{이슈명}/` 기반으로 구동한다. 폴더명(영문 kebab slug ≤40자)과 표시명(issue.md H1)을 분리해 유사 이슈 검색을 폴더명 `ls` + H1 `grep` 병행으로 수행 → [운영 이슈 단건 처리](how-to/issue-cycle.md)
- **Open Questions fail-closed 게이트** — 미해결 `- [ ]` 항목에 plan 처리 마커(`추정 구현`/`범위 제외`)가 없으면 `plan-validate` 가 차단. evaluator REPORT 에 `open_questions` gate 추가 (7 gates)
- **도메인 지식 환류 (knowledge-sync)** — evaluator 가 사이클 종료 시 이번 변경이 도메인 문서에 남길 지식을 감지해 `metrics.domain_impact` 로 보고. 기록 여부는 사용자 승인 후 메인 대화가 결정
- **`/pilot:init`·`/pilot:review` → `/pilot:pilot-init`·`/pilot:pilot-review`** — Claude Code 내장 `/init`·`/review` 와의 bare 별칭 충돌 해소 (v0.12.0)
- **issue 모드 경계 집행** — issues/ 훅 보호(기존 파일 Write·destructive 차단, Edit·신규 산출물 통과), focus 는 `issues/{이슈명}/.focus.md` 로 분기, commit 은 계속 동작하고 나머지 project 전용 스킬은 issue 행에서 종료
- **하니스 정합·규율 보강** — 진행 보드 겸용 선로딩, 계획 단계 effort 상향, plan 분량 가드(WARN), 주석 규율 eval, 훅 결함 4건 수정, SessionStart 컨텍스트 훅

---

## v0.11.0

*2026-07-31 · 태그 없음 — [v0.14.0 릴리스](https://github.com/radiostart/claude-plugins/releases/tag/pilot-v0.14.0) 에 포함되어 배포되었습니다.*

- **doctor 스킬 → `pilot-doctor` 리네임** — 플러그인 스킬의 bare `/doctor` 별칭이 Claude Code 내장 `/doctor` 를 가리는 충돌 해소. 호출은 `/pilot:pilot-doctor` (도구 `tools/doctor.py` 는 무변경)
- **Claude 5 하니스 정합** — preamble P-1 을 "진행 보드 선로딩" 으로 개편 (`TodoWrite`/`TaskCreate`·`TaskUpdate` 겸용 select), autopilot 에 wrapper 동기 호출·명시 호출 한정·게이트 이력 1줄 앵커 명시, guardrails 에 "사용자 게이트 생략 금지" 신설
- **에이전트 모델·effort 조정** — planner·planner-critic `effort: xhigh`, generator `sonnet → opus` (재생성 루프 1회 비용 > 단가 차이)
- **SessionStart 도메인 컨텍스트 포인터 훅** — 스킬 없이 메인 세션이 직접 도메인 코드를 만질 때도 MANIFEST·STATE 로딩 규칙을 안내
- **훅 결함 수정 이식** — scope-guard 디렉토리 패턴 세그먼트 경계 매칭(`log/` 가 `dialog/` 오차단), commit-format 명령 앵커링·첫 `-m` 추출·HEREDOC 검증·UTF-8 길이, protect-managed `./` 접두 정규화·projects/ 상위 차단·focus 수명주기 예외, coding-rules 세션당 1회 발화·source_root 한정
- **규율·가드 이식** — coding.md 주석 규율(표기 형태 불문) + evals `comment-discipline`, learn 프로젝트 식별자 배제, plan 분량 가드(30k자/1.5k라인 WARN)

---

## v0.10.1

*2026-07-26 · [릴리스](https://github.com/radiostart/claude-plugins/releases/tag/pilot-v0.10.1)*

- **doctor 오탐 2건 수정** — config 값 셀의 예시 표기(`예: context/conventions.md`)를 선언으로 오인하던 건, features 카운트가 `.plan.md`·`.plan.critic.md` 파생 산출물을 spec 으로 세던 건. 실측 `4 WARN` → `1 WARN` (남은 1건은 `plugin_version` 정상 감지)
- **판정을 구조 기반으로** — 값 셀은 "코드 스팬 단독 또는 공백 없는 평문" 일 때만 선언으로 인정하고, 그 외는 미선언 + INFO 로 강등. 한국어 `예:` 같은 문자열 규약에 의존하지 않는다
- **파생 산출물 판정 SSOT 1곳** — `is_feature_spec_file()` 이 "stem 에 `.` 이 있으면 파생" 규칙을 단독 보유. 새 접미사가 늘어도 파서 수정이 필요 없다
- v0.10.0 의 정비 3부작(#18 prune · #19 rewrite · #20 slim)이 dogfooding 게이트 통과로 전부 마감

---

## v0.10.0

*2026-07-25 · [릴리스](https://github.com/radiostart/claude-plugins/releases/tag/pilot-v0.10.0)*

- **스킬 전면 재작성** — 슬래시 커맨드 17개를 원칙 중심으로 압축해 전부 100줄 이하로. 에이전트 5종은 기계 계약(REPORT 블록·Detect literal·표 헤더) 보존을 우선해 재작성. 지시 문서 4,808 → 3,635줄
- **도구 슬림화** — `diagnose.py`·`memory-hint.py`·`init_detect.py` 3종을 모델 판단으로 이관해 삭제, `verify-report-lint.py` 파서는 `auto_pilot.py` 로 흡수. tools/ Python 7,138 → 4,997줄 (30.1% 감축)
- **wrapper 도메인 컨텍스트 로드 버그 수정** — MANIFEST 파서가 문서 상단 blockquote 를 먼저 매칭해 도메인 문서가 로드되지 않던 문제. anchored 정규식 + 코드블록 strip 으로 해소
- `doctor --schema` CI(`validate.yml`) 신설 · `how-to/doctor-migration.md` 를 현행 거동으로 전면 재작성

---

## v0.9.0

*2026-07-24 · [릴리스](https://github.com/radiostart/claude-plugins/releases/tag/pilot-v0.9.0)*

- **조건부 인터뷰 (Open Questions 소비)** — `/pilot:create-feature`(3-ter)·`/pilot:analyze`(7.5) 가 spec 의 미해결 Open Questions 를 우선순위((d) 비즈니스 결정 우선)로 사용자에게 조건부 질의하고 답변을 spec 에 반영. 질문이 없으면 발동하지 않는 soft gate — 기존 흐름 무중단
- **경량 산출물 대조** — spec 심볼을 `scope/{domain}.md` 산출물과 lookup 대조해 부재 심볼을 (a) 질문으로 승격 (코드 탐색은 planner 몫으로 역할 분리 유지)
- 소비 규칙 SSOT `context/shared/interview.md` 신설 — 작성 규칙(open-questions.md)과 짝, 해소된 (b) 행 재개봉 방지 판정 키 명문화

---

## v0.8.0

*2026-07-10 · [릴리스](https://github.com/radiostart/claude-plugins/releases/tag/pilot-v0.8.0)*

- **구조 감사 전면 반영** — prose 반복 지시를 기계 계층으로 이관 (orchestrate-load 가 `instructions` 필드로 공통 지시 emit, instincts.yaml 폐지, 스킬·에이전트 순감 약 1,300줄) + 문서 드리프트 일괄 수리
- **광역 회귀 soft gate** — config.md `regression_command` 설정 시 `/pilot:pr` 진입 전 1회 실행, 레거시 원거리 파손을 PR 경계에서 포착
- **리뷰 축 통합** — fix-review 스킬 폐지, 재진입 라우팅이 pilot-code-review REPORT 에 통합 (`trivial`·`new-feature`·`dismiss` 어휘 추가)
- 테스트 CI 배선 + 링크·훅 테스트 신설 — protect-managed 의 `rm -rf` 우회 버그, regen 백업 경로 버그를 테스트가 발견·수정
- critic 흐름 간소화 — 별도 스킵 동의 질의 없이 계획 확인 응답 1회로 통합 (스킵 주체는 사용자 유지)

---

## v0.7.1

*2026-06-10 · [릴리스](https://github.com/radiostart/claude-plugins/releases/tag/pilot-v0.7.1)*

- 문서 패치 — `context/boundaries/` 를 [Workspace 레이아웃](explanation/workspace-layout.md) 다이어그램과 `context/INDEX.md` 의 고정 컨벤션 경로로 반영. v0.7.0 의 boundary 자동 로드 도입으로 부정확해진 "context 하위 자유" 단언을 보정

---

## v0.7.0

*2026-06-10 · [릴리스](https://github.com/radiostart/claude-plugins/releases/tag/pilot-v0.7.0)*

- **cross-domain 경계 계약** — `/pilot:learn --boundary B --from A` 가 외부 도메인 B 전체 대신 A 가 호출하는 표면만 `boundaries/{A}--{B}.md` 로 추출 (접점 비례 비용)
- 경계 문서 자동 로드 — orchestrate-load 가 활성 도메인의 정방향·역방향 경계 계약을 에이전트에 자동 주입, 미학습 외부 의존은 boundary 처방 힌트로 안내
- doctor: 외부 도메인 reference 의 경계 부분 커버 상태 표시
- 가이드: [외부 도메인 연동](how-to/cross-domain-learn.md)

---

## v0.6.0

*2026-06-10 · [릴리스](https://github.com/radiostart/claude-plugins/releases/tag/pilot-v0.6.0)*

- `@pilot-evaluator` 독립 검증 강화 — `conventions_doc`/`conventions_evals` 를 evaluator 도 자동 로드, 표준 모드에서 `test_command` 설정 시 변경 관련 테스트 실행
- characterize 모드 `{source_root}` 잠금 이중화 — scope-guard 훅이 Edit/Write 시점에 사전 차단 (evaluator `git diff` 사후 검증과 병행)
- doctor: conventions 선언-실존 불일치 WARN 추가 · MANIFEST 도메인 분류 다중 진입 파일 지원
- generator 의 `project.md` 목표 체크박스 수정 금지 명문화 (evaluator 단독 권한)

---

## v0.5.0 이전 {#v050}

매뉴얼 사이트가 생기기(v0.6.0) 전의 버전입니다. 상세 변경 목록은 각 릴리스의 PR 목록을 참조하세요.

| 버전 | 날짜 | 요약 |
|---|---|---|
| [v0.5.0](https://github.com/radiostart/claude-plugins/releases/tag/pilot-v0.5.0) | 2026-05-21 | dp-skills 정합 + 의존성·하드닝 |
| [v0.3.1](https://github.com/radiostart/claude-plugins/releases/tag/pilot-v0.3.1) | 2026-05-20 | pilot-code-review 에이전트 · 코딩 규칙 훅 · onboarding-axis · init wizard contract fix |
| [v0.2.1](https://github.com/radiostart/claude-plugins/releases/tag/v0.2.1) | 2026-04-29 | hotfix — fixture `file:line` 인용 정정 |
| [v0.2.0](https://github.com/radiostart/claude-plugins/releases/tag/v0.2.0) | 2026-04-29 | pilot 범용화 — 도메인·언어 가정 제거 |

---

## 다음 단계

- [릴리스 · 업그레이드](explanation/release-and-upgrade.md) — semver 기준, `.agent-state.yml` schema 마이그레이션, wrapper contract 호환성
- [Doctor 진단·마이그레이션](how-to/doctor-migration.md) — 업그레이드 후 정합성 점검 절차
