# #24 pilot-update.sh 고장 — 경로 stale + 설계 한계 + 잘못된 안내

> mode: standard (`tdd: false` · `mode: null`)
> source: `features/24-pilot-update-tool.md`
> planner_at: 2026-07-25 · critic 합의 반영: 2026-07-26 (C1~C8 전건 accepted)
> 결정 확정: 사용자 승인 2026-07-25 (Q0~Q5 전건 권고안 채택)

> **[선행 조건] 작업 브랜치** — 본 plan 확정 후 작업 트리가 `skills/23-doctor-parser-false-positives` (229b2a8) 로 이동했고, 그 브랜치에는 **`features/24-pilot-update-tool.md`(spec) 와 `25-*.md` 가 존재하지 않는다** (`skills/24-pilot-update-tool` 2225109 에만 있음). 본 plan·critic 파일은 untracked 라 브랜치를 따라다닌다. Generator 는 **`skills/24-pilot-update-tool` 로 전환한 뒤** 착수한다 — 현재 브랜치에서 시작하면 spec Read 가 실패하고 doctor `features=N` baseline 도 달라진다.

## 구현 계획: #24 pilot-update.sh 폐기 + 업그레이드 안내 정정

### 결정 (확정)

- **D1 — 도구 존치 여부: (iii) 폐기.** `pilot/tools/pilot-update.sh` 를 삭제하고 업그레이드 경로를 `/plugin` 으로 일원화한다.
  - **(i) 축소 존치 — 검토 후 배제**: 스크립트가 하는 일은 `/plugin marketplace update` 와 동일한 클론 fast-forward 뿐이라, `/plugin` 이 정상인 환경에선 중복이고 막힌 환경에선 나머지 절반(`/plugin update`)을 못 해 목적 미달이다.
  - **(ii) `cache/` + 레지스트리까지 확장 — 검토 후 배제**: feature spec `## 비즈니스 규칙` 이 전역 설치본·`installed_plugins.json` 직접 조작을 금지한다. 더불어 `/plugin` 의 캐시 생성·레지스트리 갱신 규약은 공개 spec 이 없어(spec Open Q (c)1) 재현 근거 자체가 없다.
- **D2 — 릴리스 노트 정정: 한다.** 배포 완료된 `pilot-v0.10.0` 노트의 `## 업그레이드` 블록을 `gh release edit` 로 교체한다.
- **D3 — 추가 stale 3곳 포함**: spec 이 지목하지 않은 `README.md:35`·`:42`·`:146` 의 `pilot@claude-plugins` 도 같은 사이클에서 정정한다 (spec 비즈니스 규칙 "stale 경로는 한 번에 정리").
- **D4 — `getting-started.md:340` 의 허구 서술 삭제**: `project.md` 의 `## 에이전트 간 전달사항` 에 "orchestrate-load 설정" 이 있다는 문장은 실재하지 않는 설정이라 같은 블록에서 삭제한다.

### 사전 실측 (근거)

- 마켓플레이스 name SSOT = `.claude-plugin/marketplace.json` → `"name": "radiostart-plugins"`. 로컬 실재 디렉터리 `~/.claude/plugins/marketplaces/radiostart-plugins` (git clone, HEAD `229b2a8`).
- `installed_plugins.json` → `pilot@radiostart-plugins` → `installPath: ~/.claude/plugins/cache/radiostart-plugins/pilot/0.10.0`. `cache/radiostart-plugins/pilot/` 에는 `0.1.0`·`0.4.0`·`0.10.0` 3개가 존재하고, `0.10.0` 은 사용자가 `/plugin` 을 실행한 뒤 생성됐다.
  → 스크립트가 갱신하는 `marketplaces/` 클론과 실제 로드 경로 `cache/` 는 **별개 계층**임이 재확인됨 (spec (B) 일치).
- 릴리스 노트 실측: `gh release view pilot-v0.10.0` 의 `## 업그레이드` 블록이 `pilot/tools/pilot-update.sh   # 캐시 갱신` 을 지시 중 (= spec (C) 의 잘못된 안내, 이미 배포됨).
  - **취득 명령 주의 (C1)** — `gh release view` 는 raw 본문이 아니라 `title:`~`published:` 메타 8줄 + `--` 구분선이 붙은 **렌더 출력**이다. 원본 마크다운은 `gh release view pilot-v0.10.0 --json body -q .body` 로만 얻는다.
- **stale 마켓플레이스 id 전수** (`pilot/` 한정, **9줄 / 10건** — C8 정정. `README.md:42` 는 한 줄에 2건):
  - `pilot/tools/pilot-update.sh:6`·`:9`·`:17`·`:29` (파일 삭제로 소멸)
  - `pilot/README.md:35`·`:42`(2건)·`:50`·`:146`
  - `pilot/docs/tutorial/getting-started.md:338`
- **`pilot-update` 문자열 전수** (게이트 "0건" 의 커버 근거 — C8, 총 10건):
  - 개별 수정: `README.md:50`·`:54`·`:55`(삭제 블록 안)·`:147` · `getting-started.md:338`
  - 파일 삭제로 소멸: `pilot-update.sh:2`·`:9`·`:12`·`:13`·`:41`
  - `.github/` 참조 0건 (CI 무영향)
- **정상이라 손대지 않는 문자열**: `pilot/README.md:34` 의 `/plugin marketplace add radiostart/claude-plugins` 는 GitHub **레포 경로**다 (레포명 = `claude-plugins`, 마켓플레이스 id = `radiostart-plugins`). 과잉 치환 금지.

#### planner 재실측 (2026-07-25 재호출 — 설치 캐시 0.10.0 실경로 세션)

위 실측을 독립 재확인했고 **불일치 0건**. 추가로 확정한 baseline:

| 항목 | 값 | 근거 |
| --- | --- | --- |
| 개명 커밋 `19a7ff9` 변경 범위 | `.claude-plugin/marketplace.json` **1파일 1줄** — 전파 누락 확정 | `git show --stat 19a7ff9` |
| `radiostart/claude-plugins` (레포 슬러그, **보존**) | 4건 — `README.md:31`·`:34` · `pilot-update.sh:5`·`:28` | grep |
| `.github/` 의 `pilot-update` 참조 | **0건** — CI 영향 없음 | grep |
| `docs_build.py` 글로브 | `tools/*.py` 한정 → `.sh` 는 생성 reference 페이지 **없음** (`reference/index.md:25` 도구 8종에 미포함) | 파일 실독 |
| doctor baseline (변경 전) | **10 PASS · 4 WARN · 0 ERROR** — WARN 4 = conventions 2 + plugin_version 1 + drift 1 (전부 #23·#22 소관, 본 feature 무관). **`features=N` 은 baseline 아님** (C6 — 아래 주) | `python3 pilot/tools/doctor.py workspace` |
| `prompts/evaluator.md` 의 `pilot-update.sh` 언급 | `#20`·`#21` 판정 행 — `<!-- [analyze-managed] -->` 영역이라 **직접 수정 금지**. 단 본 사이클 evaluator 가 이미 읽는다 (C4 — 스텝 3 신규 전달사항 행으로 무력화) | 파일 실독 |
| spec 예외 케이스 "구 id(`claude-plugins`)로 등록한 기존 사용자" | **기각** — 구 id 노출 창은 `c3df02c`(2026-04-28 23:40 KST) ~ `19a7ff9`(2026-04-29 11:42 KST) **12시간 2분**이고, 첫 릴리스 `v0.2.0` 은 2026-04-29T12:49Z 로 **개명 이후**. 외부 사용자가 구 id 로 등록했을 경로가 없다 (C7) | `git log -1 --date=iso` · `gh release list` |

> **C6 주 — `features=N` 을 판정 근거로 쓰지 말 것.** 이 값은 두 방향으로 흔들린다. ① `count_real_features` 가 `.plan.md` 만 제외하고 `.plan.critic.md` 를 세므로(`pilot/tools/doctor/_common.py:197-204`, #23 (B) 오탐) critic 파일이 하나 생길 때마다 증가한다. ② 브랜치에 따라 spec 파일 수가 다르다 — critic 실측 `31`, planner 재호출 실측 `30`(drift `24 → 30`)로 이미 어긋났다. 게이트는 **`WARN 4 · ERROR 0` 개수와 WARN 구성 4종**으로만 판정한다.

### 변경 파일

- [ ] `pilot/tools/pilot-update.sh` — **파일 삭제** (79줄, D1 (iii))
- [ ] `pilot/README.md` — `:35`·`:42` 마켓플레이스 id 정정 · `:44-56` "`/plugin` 이 막힌 환경" 블록을 터미널 `claude` 안내로 교체 · `:146-147` 업데이트 안내 정정 (`pilot-update` 헬퍼 문장 제거)
- [ ] `pilot/docs/tutorial/getting-started.md` — `:336-341` Troubleshooting 5 의 업데이트 명령 블록 정정 + 허구 서술 문장 삭제 (D4)
- [ ] `pilot/docs/explanation/release-and-upgrade.md` — `:68` "Release 시 사용자 Workflow" 1번 문장 정정 (**C3 신규**). 현재 "수동 `pip` / `git pull`" 을 업데이트 수단으로 서술 — 본 feature 가 확정한 (B)(클론을 당겨도 로드 경로 불변) 와 정면 충돌하고, `pip` 는 이 플러그인의 배포 수단도 아니다
- [ ] GitHub Release `pilot-v0.10.0` — `## 업그레이드` 블록 교체 (`gh release edit`, 파일 아님, D2). **사전 백업 필수** (C1)
- [ ] `workspace/projects/build-plugin/project.md` — **2건 (C4 분리 기재)**
  - ① 전달사항 `:166` 절차 ③ **본문 문구만** 교체 (**체크박스 `[ ]` 유지**)
  - ② `## 에이전트 간 전달사항` **신규 1행 추가** (stale 지시 무력화 — 문구는 스텝 3 참조)

### 구현 순서

1. **스크립트 폐기** — `git rm pilot/tools/pilot-update.sh`.
   - 지원 경로는 `/plugin` 하나다: `/plugin marketplace update radiostart-plugins` → `/plugin update pilot@radiostart-plugins` → **세션 재시작**. 전역 설치본(`~/.claude/plugins/`)을 직접 건드리는 절차는 어떤 형태로도 안내하지 않는다.
   - **[C2] 대체 경로는 단정하지 않는다 (미검증).** "IDE 밖 터미널에서 `claude` 를 띄우면 된다" 는 **실측된 바 없다**. 문서 문구는 반드시 조건부로 쓴다 — *"`/plugin` 을 쓸 수 있는 세션에서 실행하세요. IDE 내장 세션이라면 같은 `~/.claude` 설정을 쓰는 다른 터미널의 `claude` 에서 시도해 볼 수 있습니다(환경에 따라 불가). 관리형 세션 등 `/plugin` 자체가 제공되지 않는 환경에는 현재 pilot 측이 제공하는 우회 수단이 없습니다."* — 검증되지 않은 안내를 사실처럼 쓰는 것이 곧 spec (C) 의 재생산이다.
   - 이 스텝 단독 커밋 금지 — 스텝 2 와 같은 커밋/PR 로 묶는다 (spec 비즈니스 규칙: (A) 만 고치면 조용한 실패가 된다).

2. **사용자 대면 안내 정정** (`pilot/README.md` · `pilot/docs/tutorial/getting-started.md` · 릴리스 노트)
   - `README.md:35` → `/plugin install pilot@radiostart-plugins`
   - `README.md:42` → `` `/plugin marketplace update radiostart-plugins` → `/plugin update pilot@radiostart-plugins` ``
   - `README.md:44-56` (`#### /plugin 이 막힌 환경` 블록 + alias 코드블록 2개) → **블록 전체 삭제**하고, 그 자리에 스텝 1 의 **조건부 문구**(C2) 2~3줄로 대체. 단정형("이렇게 하면 된다") 금지, "`/plugin` 이 유일한 지원 경로" 는 유지.
   - `README.md:146-147` → `/plugin update pilot@radiostart-plugins` 로 정정 + `` `/plugin` 이 막힌 환경은 위 `pilot-update` 헬퍼를 쓴다 `` 문장 제거.
   - `getting-started.md:336-339` 코드블록 → `pilot-update` 줄 제거, `/plugin marketplace update radiostart-plugins` + `/plugin update pilot@radiostart-plugins` + 세션 재시작 안내로 교체.
   - `getting-started.md:341` 마지막 문장(`## 에이전트 간 전달사항` 의 "orchestrate-load 설정" 운운) 삭제 (D4). *(planner 재실측 2026-07-25: 코드블록은 `:336`(```bash)~`:339`(```), 허구 문장은 `:341` — 초안의 `:337-339`/`:340` 은 1줄 어긋남. 문자열 기준으로 찾을 것.)*
   - `release-and-upgrade.md:68` (**C3**) → "plugin 패키지가 새 버전으로 업데이트됩니다 (Claude Code Marketplace 또는 수동 `pip` / `git pull` 실행)" 에서 **"수동 `pip` / `git pull`" 을 제거**하고 `/plugin marketplace update radiostart-plugins` → `/plugin update pilot@radiostart-plugins` → 세션 재시작으로 정정. 같은 페이지의 semver·schema 표는 손대지 않는다.
   - 릴리스 노트 (**C1 — 4단계, 순서 준수**):
     1. **백업**: `gh release view pilot-v0.10.0 --json body -q .body > /tmp/pilot-v0.10.0.body.bak` (이 경로를 evaluator 증거로 남긴다)
     2. **취득**: 같은 명령의 출력을 편집 대상으로 삼는다. `gh release view` (플래그 없음) 출력은 **절대 입력으로 쓰지 않는다** — `title:`~`published:` 메타 8줄이 본문에 삽입된다.
     3. **교체**: `## 업그레이드` 코드블록만 위 `/plugin` 절차로 교체 → `gh release edit pilot-v0.10.0 --notes-file {수정본}`
     4. **검증**: 적용 후 `--json body -q .body` 재취득 → 백업본과 `diff` → **`## 업그레이드` 블록 외 나머지 절이 byte 동일**임을 확인
     - 롤백: 손상 시 `gh release edit pilot-v0.10.0 --notes-file /tmp/pilot-v0.10.0.body.bak`. 저장소 밖 산출물이라 `git checkout` 이 듣지 않는 유일한 변경 대상이다.

3. **내부 절차 참조 갱신 + 게이트 검증**
   - `workspace/projects/build-plugin/project.md:166` 전달사항의 절차 ③ `` `pilot/tools/pilot-update.sh` 실행 `` → `` `/plugin marketplace update radiostart-plugins` + `/plugin update pilot@radiostart-plugins` `` 로 **본문 문구만 교체**. 체크박스는 `[ ]` 유지 — #20 dogfooding 게이트는 여전히 미충족이다.
   - `workspace/projects/build-plugin/prompts/evaluator.md:24`·`:39` 의 동일 문구는 `<!-- [analyze-managed] -->` 영역이므로 **직접 수정하지 않는다**. 대신 **`## 에이전트 간 전달사항` 에 신규 1행을 추가**해 무력화한다 (**C4** — 이 창은 다음 사이클이 아니라 **본 feature 를 판정할 evaluator 부터** 열린다):
     > `- [ ] #24 로 `pilot/tools/pilot-update.sh` 는 **삭제됨**. #20 dogfooding 게이트 5단계의 ③ 은 `/plugin marketplace update radiostart-plugins` + `/plugin update pilot@radiostart-plugins` 로 대체됐다. `prompts/evaluator.md:24`·`:39` 는 `[analyze-managed]` 영역이라 미수정 상태로 stale — **문자 그대로 실행하지 말 것**. 다음 `/pilot:analyze --regen-agents` 가 재정렬한다 (from #24)`
   - 게이트 실행:
     - `grep -rn "marketplaces/claude-plugins\|pilot@claude-plugins\|marketplace update claude-plugins" pilot/` → **0건** (변경 전 9줄/10건)
     - `grep -rn "pilot-update" pilot/` → **0건** (변경 전 10건 — § 사전 실측 전수 열거가 커버 근거)
     - `grep -rn "pip\` / \`git pull\|수동 \`git pull" pilot/docs/` → **0건** (C3 정정 확인)
     - `python3 pilot/tools/docs_build.py --check` → exit 0
     - `python3 pilot/tools/doctor.py workspace` → **`WARN 4 · ERROR 0`** (WARN 구성 = conventions 2 + plugin_version 1 + drift 1). **`features=N` 값은 판정 근거에서 제외** (C6)
     - 릴리스 노트: 적용 후 `--json body -q .body` ↔ `/tmp/pilot-v0.10.0.body.bak` diff 결과가 **`## 업그레이드` 블록에만 국한** (C1)
     - `git diff --stat` 변경 경로가 `pilot/**` + `workspace/projects/build-plugin/project.md` 뿐 (전역 설치본 조작 0)

### 주의사항

- **과잉 치환 금지** — `radiostart/claude-plugins` 는 GitHub 레포 경로(정상)이고 `claude-plugins` **마켓플레이스 id** 만 stale 이다. `README.md:34` 는 손대지 않는다.
- **과거 기록은 정정 대상 아님** — `docs/audits/2026-07-24-audit-*.md`, `workspace/**/*.plan.md`, `features/24-pilot-update-tool.md` 의 stale 문자열은 버그 증거·감사 기록이다. 게이트 grep 범위를 `pilot/` 로 한정한다.
- **[C5] #20 게이트 절차의 SSOT 판정** — 살아있는 지시(#20 은 아직 `[ ]`)와 이력을 구분한다. **SSOT = `project.md:166` 1곳**만 갱신하고, `features/20-consolidation-slim.plan.md:80` · `features/21-consolidation-docs-sync.plan.md:345` · `project.md:164` 의 사본은 **작성 시점 기록이므로 갱신하지 않는다**. `RESUME.md`(`:14`·`:18`·`:35`·`:53-57`)는 plan 산출물이 아니라 세션 인계 문서 — **사이클 종료 시 갱신 대상**이며 본 스텝 범위 밖이다.
- **[C2] 미검증 가정 명시** — "IDE 밖 터미널의 `claude` 로 `/plugin` 을 쓸 수 있다" 는 **본 사이클에서 실측하지 않았다** (사용자 지시로 실측 생략). 따라서 문서에는 조건부로만 기술하고, 이 문장을 근거로 "대체 수단이 있다" 고 판정하지 않는다. 관리형 세션처럼 `/plugin` 자체가 없는 환경은 **현재 미지원**임을 명시하는 것이 정확한 서술이다.
- **[C7] spec 예외 케이스 판정** — "구 id 사용자" 는 **기각**(근거: 노출 창 12시간·첫 릴리스 이전, § 사전 실측 표). 새 안내에 `radiostart-plugins` 를 하드코딩하는 것이 옳다. evaluator 는 이 항목을 "미판정 누락" 으로 보지 말 것.
- **전역 설치본 불가침** (spec 비즈니스 규칙) — 본 사이클의 어떤 변경도 `~/.claude/plugins/` 를 쓰기 조작하지 않는다.
- **(A) 단독 수정 금지** (spec 비즈니스 규칙) — 스텝 1·2 는 같은 커밋/PR. 경로만 고치고 안내를 방치하면 "실행은 되나 업그레이드는 안 되는" 더 나쁜 상태가 된다.
- **reference 페이지 증거 규칙** (전달사항 `project.md:165`) — `pilot/docs/reference/` 는 `pilot/.gitignore:10` 로 git 미추적이고 `docs_build.py` 는 `tools/*.py` 만 글로브한다. 따라서 `.sh` 삭제 시 reference 재생성 diff 가 **없는 것이 정상**이다. 커밋 증거를 요구하지 말고 `--check` exit code 로 판정한다.
- **#20 게이트 연쇄** — 본 feature 이후 #20 재확인 절차 5단계의 ③ 은 `/plugin` 경유가 된다. ④ (세션 재시작) 는 그대로 필수이며, "배포만 되면 자동 해소" 가 아니라는 문구도 유지한다.
- **generator 권한** — `project.md` 의 `## 목표` 체크박스는 수정 금지 (evaluator 단독 권한). 스텝 3 에서 건드리는 것은 `## 에이전트 간 전달사항` 의 **기존 행 본문 문구 1건 교체 + 신규 1행 추가** 뿐이며, `:166` 항목의 `[ ]` 상태와 신규 행의 `[ ]` 초기 상태를 모두 유지한다.
- **릴리스 노트는 롤백 불가 영역** — 저장소 밖 산출물이라 `git diff --stat`·`git checkout` 게이트가 전혀 듣지 않는다. 스텝 2 의 백업(1) → 검증(4) 순서를 건너뛴 채 `gh release edit` 를 먼저 실행하지 않는다 (C1).

### 교차 의존

- feature #20 (정비 slim) — dogfooding 게이트 5단계 ③ 이 본 feature 의 결정에 종속. 문구는 갱신하되 게이트 자체는 **미충족 유지**.
- feature #23 (doctor 파서 오탐) — doctor WARN 4건 baseline 을 공유. 본 feature 는 WARN 수치를 바꾸지 않는다.

### 전달사항 처리 (wrapper step 2)

| 항목 | 처리 |
| --- | --- |
| `project.md:166` (#20 dogfooding 게이트 ③ = pilot-update.sh) | **이번 반영** — 스텝 3 에서 문구 교체. 단 #20 게이트 미충족이므로 체크박스 `[ ]` 유지 |
| `project.md:165` (reference/ git 미추적 증거 규칙) | **이번 반영** — 위 § 주의사항에 게이트 판정 규칙으로 명시 |
| 나머지 12항 (`:110`·`:120`·`:122`·`:126`·`:129`·`:130`·`:133`·`:136`·`:139`·`:147`·`:148`·`:149`·`:151`·`:153`·`:156`·`:161`·`:163`·`:167` 중 무관분) | **다음 이월** — 사용자 확정 (2026-07-25). 체크하지 않는다. `:163` R-3 도 별도 feature 등록 없이 이월 |

### spec Open Questions 해소 (사용자 확정 2026-07-25)

- (c)1 `/plugin` 캐시·레지스트리 규약 공개 spec 부재 → **(ii) 확장안 배제 근거로 소화**.
- (d)1 도구 존치 여부 → **(iii) 폐기**.
- (d)2 v0.10.0 릴리스 노트 정정 → **정정한다** (스텝 2).

> Generator 는 위 3건을 `features/24-pilot-update-tool.md` 의 `## Open Questions` 에 `- [x] {질문} → {답변 요약}` 형식으로 반영한다. (해당 spec 파일은 `skills/24-pilot-update-tool` 브랜치에만 존재 — 상단 [선행 조건] 참조.)

### critic 합의 (`24-pilot-update-tool.plan.critic.md` § 합의)

C1~C8 **전건 accepted** (2026-07-26). 반영 위치:

| C# | severity | 본 plan 반영 위치 |
| --- | --- | --- |
| C1 | blocking | § 사전 실측 "취득 명령 주의" · 스텝 2 릴리스 노트 4단계 + 롤백 · 게이트 diff 1줄 · § 주의사항 "롤백 불가 영역" |
| C2 | blocking | 스텝 1 두 번째 불릿(조건부 문구 원문) · 스텝 2 `README.md:44-56` · § 주의사항 "미검증 가정 명시" |
| C3 | major | § 변경 파일 신규 행 · 스텝 2 신규 불릿 · 게이트 grep 3번째 |
| C4 | major | § 변경 파일 `project.md` ①② 분리 · 스텝 3 신규 전달사항 행 원문 |
| C5 | minor | § 주의사항 "#20 게이트 절차의 SSOT 판정" |
| C6 | minor | 재실측 표 doctor 행 + C6 주 · 게이트 4번째 |
| C7 | minor | 재실측 표 신규 행(기각 근거) · § 주의사항 "spec 예외 케이스 판정" |
| C8 | minor | § 사전 실측 "9줄 / 10건" 정정 + `pilot-update` 전수 열거 · 게이트 1·2번째 |
