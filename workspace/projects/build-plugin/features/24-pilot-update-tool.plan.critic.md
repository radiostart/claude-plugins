# Plan Critic — #24 pilot-update.sh 폐기 + 업그레이드 안내 정정

> 입력 plan: `features/24-pilot-update-tool.plan.md` (검토 시각 2026-07-26T00:00:00+09:00)
> 입력 feature: `features/24-pilot-update-tool.md`
> 페르소나: `personas.planner-critic` (red-team)
> focus 반영: 없음 (`.focus.md` 부재 — orchestrate-load `focus: null`)
> severity 스케일: `blocking | major | minor` (호출자 지정)

## 반증 시도 결과 (챌린지로 승격하지 않은 항목 — 기록용)

plan 의 핵심 결정 D1 (삭제) 을 3 방향으로 반증 시도했고 **모두 실패**했다. 삭제 결정 자체는 유지 근거가 있다.

| 반증 가설 | 실측 | 결론 |
| --- | --- | --- |
| 구 마켓플레이스명(`claude-plugins`)으로 등록한 사용자에겐 스크립트가 유효 | 그 경우에도 스크립트는 `marketplaces/` 클론만 fast-forward — 로드 경로 `cache/{mp}/pilot/{ver}/` 미변경 (spec (B)). **목적 미달은 이름과 무관** | 반증 실패 |
| 다른 OS·경로 레이아웃에서 유효 | `installed_plugins.json` → `installPath` 구조는 Claude Code 자체 계약이라 OS 무관. 로컬 실측: `cache/radiostart-plugins/pilot/{0.1.0,0.4.0,0.10.0}` ↔ `marketplaces/` 별개 계층 확인 | 반증 실패 |
| 삭제는 되돌리기 어렵다 | `git rm` 은 `git revert` 로 완전 복원 가능. **되돌리기 어려운 것은 D1 이 아니라 D2 (공개 릴리스 노트 수정)** — C1 참조 | 위험 축 이동 |

## 챌린지

### C1 — `gh release edit` 절차가 본문을 손상시킨다 (백업·롤백 부재)

- **severity**: blocking
- **category**: risk
- **plan 인용**: 스텝 2 마지막 (`features/24-pilot-update-tool.plan.md:65`)
- **챌린지**: plan 은 "`gh release view pilot-v0.10.0` 로 본문을 받아 … `gh release edit pilot-v0.10.0 --notes-file -` 적용" 이라고 적었다. `gh release view` 는 **raw body 가 아니라 메타데이터 헤더가 붙은 렌더 출력**이다. 실측:

  ```
  $ gh release view pilot-v0.10.0 | head -8
  title:	pilot v0.10.0
  tag:	pilot-v0.10.0
  draft:	false
  prerelease:	false
  immutable:	false
  author:	radiostart
  created:	2026-07-25T14:00:45Z
  published:	2026-07-25T14:01:15Z
  ```

  이 출력을 그대로 `--notes-file -` 로 넣으면 공개 릴리스 노트 본문 첫머리에 `title:`·`draft:` 등 8줄이 삽입되고, 원본 마크다운(`---` 구분선·표·코드펜스)도 렌더 변형을 그대로 뒤집어쓴다. 게다가 이것은 저장소 밖 산출물이라 `git checkout` 롤백이 없다 — plan 의 어떤 게이트도(`git diff --stat` 포함) 이 손상을 검출하지 못한다.
- **제안**: (a) 취득을 `gh release view pilot-v0.10.0 --json body -q .body` 로 명시 (실측상 이것만 raw 본문을 준다) (b) 편집 **전** 원본을 파일로 백업하고 그 경로를 plan/evaluator 증거로 남길 것 (예: `gh release view pilot-v0.10.0 --json body -q .body > /tmp/pilot-v0.10.0.body.bak`) (c) 게이트에 "적용 후 `--json body` 재취득 → `## 업그레이드` 블록만 diff, 나머지 절 byte 동일" 1줄 추가. 참고로 `immutable: false` 라 편집 자체는 가능함을 실측 확인했다.

### C2 — 대체 경로("터미널에서 `claude` 실행")가 미검증 단정이다

- **severity**: blocking
- **category**: premise
- **plan 인용**: 스텝 1 두 번째 불릿 (`features/24-pilot-update-tool.plan.md:55`) → 스텝 2 의 `README.md:44-56` 교체 (`:61`)
- **챌린지**: plan 은 `~/.claude` 공유를 근거로 "IDE 밖 터미널에서 `claude` 실행 → `/plugin …`" 을 대체 경로로 단정하고, 이 문장을 그대로 README 사용자 안내로 승격한다. 그런데 § 사전 실측·§ planner 재실측 어디에도 이 경로의 **실측 근거가 없다**. 현행 README 가 지목하는 차단 환경은 두 종류다 — `pilot/README.md:44` "IDE 내장·관리형 환경". 후자(관리형/원격 세션)는 사용자가 임의 터미널을 못 여는 경우를 포함하므로 대체 경로가 성립하지 않을 수 있다. 검증 없이 내보내면 **spec (C) 가 고치려던 실패 모드**(`features/24-pilot-update-tool.md:28` "사용자가 따라 해도 업그레이드가 되지 않는다")를 안내 문구만 바꿔 재생산한다.

  (단, 이 챌린지는 D1 삭제 결정을 흔들지 않는다 — 스크립트는 (B) 때문에 애초에 그 환경에서도 목적 미달이었다. 문제는 "대체 수단이 있다" 는 **서술의 사실성** 하나다.)
- **제안**: 둘 중 하나. (a) IDE 내장 환경에서 터미널 `claude` → `/plugin update` 로 `cache/{mp}/pilot/{새버전}/` 이 실제로 생성되는지 1회 실측하고 그 결과를 plan § 사전 실측에 추가 (b) 실측을 생략한다면 README 문구를 "IDE 내장 환경이라면 별도 터미널에서 `claude` 를 띄워 같은 `~/.claude` 설정으로 `/plugin` 을 쓸 수 있다 (환경에 따라 불가)" 처럼 **범위·불확실성을 명시**하고, plan 에도 "미검증 서술" 임을 기록. 어느 쪽이든 plan 이 이미 요구한 "이것으로도 안 되면 `/plugin` 이 유일한 지원 경로" 문장은 유지.

### C3 — 업그레이드 안내가 남아 있는 문서 1곳이 변경 파일 목록에 없다

- **severity**: major
- **category**: edge-case
- **plan 인용**: § 변경 파일 (`features/24-pilot-update-tool.plan.md:46-50`) · 게이트 grep 2종 (`:71-72`)
- **챌린지**: `pilot/docs/explanation/release-and-upgrade.md:68` 이 사용자 업그레이드 절차를 이렇게 서술한다 — "plugin 패키지가 새 버전으로 업데이트됩니다 (Claude Code Marketplace 또는 수동 `pip` / `git pull` 실행)". 이 문장은 본 feature 가 확정한 사실((B): 클론을 당겨도 로드 경로는 안 바뀐다)과 **정면으로 어긋난다** — "수동 `git pull`" 은 폐기하는 스크립트가 하던 바로 그 동작이고, `pip` 는 이 플러그인의 배포 수단이 아니다. 이 페이지는 mkdocs 사이트에 포함되어 있고(`pilot/docs/explanation/index.md:63` 에서 링크), `#21` 이 이미 "업데이트 절차의 실행 시점을 `explanation/release-and-upgrade.md` 에 명문화할 필요" 를 남겨 뒀다(`features/21-consolidation-docs-sync.plan.md:382`).

  plan 의 게이트 2종은 **문자열 grep**(`claude-plugins` / `pilot-update`)이라 이 문장을 못 잡는다. 즉 evaluator 는 "안내 문구가 실제 동작과 일치"(`prompts/evaluator.md:43` 게이트)를 통과 판정하면서 실제로는 틀린 안내를 남기게 된다.
- **제안**: `pilot/docs/explanation/release-and-upgrade.md:68` 을 변경 파일에 추가하고 1문장을 `/plugin marketplace update` → `/plugin update` → 세션 재시작으로 정정한다. 범위를 늘리기 싫다면 최소한 plan 에 "의식적 이월 — 별도 feature" 를 근거와 함께 명시할 것(방치 결정도 기록되면 evaluator 오탐이 사라진다).

### C4 — 삭제된 스크립트를 실행하라는 지시가 **본 사이클 evaluator** 부터 노출된다

- **severity**: major
- **category**: risk
- **plan 인용**: 스텝 3 두 번째 불릿 (`features/24-pilot-update-tool.plan.md:69`) · § 변경 파일 `:50`
- **챌린지**: plan 은 `prompts/evaluator.md:24`·`:39` 를 analyze-managed 로 보고 미수정 + "전달사항에 기록해 다음 `--regen-agents` 가 재정렬" 로 처리했다. 미수정 결정 자체는 SSOT 규칙상 옳다. 그러나 두 가지가 비었다.
  1. **창이 "다음 사이클" 이 아니라 즉시다.** `@pilot-evaluator` wrapper 는 매 호출마다 `prompts/evaluator.md` 를 읽는다 — 즉 **이 feature 를 판정할 evaluator 본인**이 `:24`("체크 조건: 배포 → `pilot/tools/pilot-update.sh` → 세션 재시작")·`:39`(5단계 ③ 동일)를 읽는다. 그 시점에 파일은 이미 삭제돼 있다.
  2. **전달사항 신규 행 추가가 § 변경 파일에 없다.** `:50` 은 `project.md` 를 "전달사항 `:166` 절차 ③ **본문 문구만** 교체" 로만 한정한다. 스텝 3 본문이 말하는 "전달사항에 기록" 에 해당하는 **신규 항목 추가**가 변경 파일 목록에 없으므로, 요구사항 밖 추가를 금지당한 generator 가 이를 건너뛸 수 있다.
- **제안**: § 변경 파일의 `project.md` 항목을 "① `:166` 본문 문구 교체(체크박스 `[ ]` 유지) ② `## 에이전트 간 전달사항` **신규 1행 추가**" 로 분리 기재하고, 신규 행 문구에 (a) #20 게이트 ③ 이 `/plugin` 경로로 바뀐 사실 (b) `prompts/evaluator.md:24`·`:39` 는 stale 이며 다음 `/pilot:analyze --regen-agents` 까지 **문자 그대로 실행하지 말 것** 을 포함시킨다.

### C5 — "과거 기록" 분류에 **미완 게이트의 살아있는 지시**가 섞여 있다

- **severity**: minor
- **category**: scope
- **plan 인용**: § 주의사항 2번째 불릿 (`features/24-pilot-update-tool.plan.md:80`)
- **챌린지**: plan 은 `workspace/**/*.plan.md` 의 stale 문자열을 일괄 "버그 증거·감사 기록" 으로 분류해 정정 대상에서 뺐다. 대부분은 타당하나 `features/20-consolidation-slim.plan.md:80` 은 성격이 다르다 — #20 은 `project.md:39` 에서 아직 `[ ]` 이고 `RESUME.md:12` 도 `NOT_READY — 게이트 1건만 남음` 이다. 그 파일의 해당 줄은 과거 서술이 아니라 **앞으로 수행할 재확인 절차**("③ `pilot/tools/pilot-update.sh` 실행")를 규정하는 살아있는 지시다. 같은 성격의 잔존이 `features/21-consolidation-docs-sync.plan.md:345`, `project.md:164`(완료 기록이지만 5단계 절차를 재서술), `RESUME.md:18`·`:45` 에도 있다.
- **제안**: 결정을 뒤집으라는 게 아니라 **판정을 1줄 남기라**는 것. 예: "#20 게이트 절차의 SSOT 는 `project.md:166` 1곳으로 하고, `20-*.plan.md:80`·`21-*.plan.md:345`·`project.md:164` 의 사본은 이력이므로 갱신하지 않는다" 를 § 주의사항에 명시. `RESUME.md` 는 사이클 종료 시 갱신 대상인지 여부만 밝히면 충분하다.

### C6 — doctor 게이트를 출력 문자열이 아니라 **개수**로 못박아야 한다

- **severity**: minor
- **category**: edge-case
- **plan 인용**: 게이트 4번째 (`features/24-pilot-update-tool.plan.md:74`) · 재실측 표 doctor baseline 행 (`:41`)
- **챌린지**: baseline 은 실측으로 확인됐다 — `python3 pilot/tools/doctor.py workspace` → `10 PASS · 4 WARN · 0 ERROR`, `features=31`. 그런데 `count_real_features` 는 `.plan.md` 만 제외하고 `.plan.critic.md` 는 센다(`pilot/tools/doctor/_common.py:200-204`, = #23 (B) 오탐). **지금 이 critic 파일이 생성된 것만으로** drift WARN 문구가 `features 26 → 31` 에서 `26 → 32` 로 바뀐다. WARN 개수(4)와 ERROR(0)는 불변이라 게이트 취지는 유지되지만, plan 이 `features=31` 을 baseline 값으로 표에 박아 둔 탓에 evaluator 가 출력 동일성을 요구하면 오탐이 난다.
- **제안**: 게이트 문구를 "`WARN 4 · ERROR 0` (개수 기준). WARN 구성 = conventions 2 + plugin_version 1 + drift 1. **`features=N` 값은 `.plan.critic.md` 계수(#23 (B)) 로 증가하는 것이 정상**이므로 판정 근거에서 제외" 로 정정.

### C7 — spec `## 예외 케이스` 중 1건이 판정 없이 통과됐다

- **severity**: minor
- **category**: premise
- **plan 인용**: § 사전 실측 (`features/24-pilot-update-tool.plan.md:21-42`) ↔ spec `features/24-pilot-update-tool.md:43`
- **챌린지**: spec 예외 케이스는 "개명 전 이름(`claude-plugins`)으로 마켓플레이스를 추가해 둔 기존 사용자가 있을 수 있다 — 경로를 하드코딩하지 말고 탐지하는 편이 안전하다" 고 적었다. plan 은 스크립트를 삭제하면서 새 안내에 `radiostart-plugins` 를 **하드코딩**하는데(스텝 2 `:59-63`), 그 사용자에겐 `/plugin marketplace update radiostart-plugins` 가 실패한다. plan 은 이 예외를 채택도 기각도 하지 않았다.

  다만 red-team 으로서 실측한 결과 **영향은 사실상 0** 이다 — 구 이름 노출 창은 `c3df02c`(2026-04-28T23:40+09:00) ~ `19a7ff9`(2026-04-29T11:42+09:00) 약 12시간이고, 첫 릴리스 `v0.2.0` 은 그 **이후**(2026-04-29T12:49Z)다. 즉 외부 사용자가 구 id 로 등록했을 가능성은 희박하다.
- **제안**: 결정 변경 불필요. 위 12시간·릴리스 이전 실측을 § 사전 실측에 1줄 추가하고 "spec 예외 케이스(구 id 사용자) = **기각**, 근거 = 노출 창 12시간·릴리스 이전" 을 명시한다. 그래야 evaluator 의 requirements 축(spec 3축 매칭)에서 누락 판정이 나지 않는다.

### C8 — stale 전수 "9곳" 표기가 열거와 어긋난다 (치환 계획 자체는 전수 커버 확인)

- **severity**: minor
- **category**: scope
- **plan 인용**: § 사전 실측 stale 전수 (`features/24-pilot-update-tool.plan.md:25-28`)
- **챌린지**: 독립 재현 결과 `pilot/` 내 stale 마켓플레이스 id 는 **9줄 / 10건**이다 (`README.md:42` 한 줄에 `marketplace update claude-plugins` + `pilot@claude-plugins` 2건). plan 은 "9곳" 이라 쓰고 열거에서는 `:42`(2건) 로 10건을 적어 라벨과 열거가 불일치한다. 또한 `pilot-update` 문자열은 plan 이 든 곳 외에 `README.md:54`·`:55`(alias 사용 예)·`pilot/tools/pilot-update.sh:2`·`:12`·`:13`·`:41` 에도 있다 — **전부 삭제 대상 블록·파일 안**이라 실질 누락은 아니지만 "0건" 게이트의 커버 근거로는 열거가 불완전하다.

  과잉 치환 방어는 재현 확인했다 — `radiostart/claude-plugins`(레포 슬러그)는 `README.md:31`·`:34`, `mkdocs.yml:3-5`, `README.md:7`·`:21`·`:96`·`:108-113`(문서 사이트 URL) 에 존재하며 이들은 **보존 대상**이 맞다. `docs_build.py` 가 `tools/*.py` 만 글로브하는 것도 확인(`pilot/tools/docs_build.py:330`) — `.sh` 삭제에 따른 reference 재생성 diff 없음이 정상이라는 plan 주장(`:83`)은 참이다.
- **제안**: 라벨을 "9줄 / 10건" 으로 정정하고, `pilot-update` 문자열 전수(`README.md:50`·`:54`·`:55`·`:147` · `getting-started.md:338` · 삭제 파일 내부 4건)를 열거해 "0건" 게이트의 커버 근거를 명시.

## 합의 (planner 가 재호출되어 채움 — 처음에는 비워둠)

> planner 재호출 2026-07-26. 각 챌린지의 인용 file:line 을 독립 재현한 뒤 판정. 형식적 동의를 피하려 8건 전부 원문 대조했고, **사실 오류로 기각할 항목은 없었다** (C6 만 부분 정정 — 아래 메모).

| C# | 처리 | 메모 |
|----|------|------|
| C1 | accepted | 재현 확인: `gh release view pilot-v0.10.0` 는 `title:`~`published:` 8줄 + `--` 구분선이 붙은 렌더 출력, `--json body -q .body` 만 raw 본문. 제안 (a)(b)(c) 전건 채택 — 스텝 2 를 ①백업(`/tmp/pilot-v0.10.0.body.bak`) → ②`--json body -q .body` 취득 → ③`## 업그레이드` 블록만 교체 → ④적용 후 재취득 diff 4단계로 재작성하고, 롤백 경로(`gh release edit --notes-file {백업}`)를 명시. 게이트에 "나머지 절 byte 동일" 1줄 추가 |
| C2 | accepted | 지적 수용 — 미검증 경로를 사실처럼 쓰면 spec (C) 의 실패 모드를 안내 문구만 바꿔 재생산한다는 논지가 맞다. **제안 (b) 채택** (사용자 지시 2026-07-26: 실측 시도 금지, 범위 한정 서술로 해소). README 문구를 조건부("`/plugin` 을 쓸 수 있는 세션에서는 … / `/plugin` 자체가 제공되지 않는 환경은 현재 pilot 측 우회 수단 없음")로 낮추고, plan § 주의사항에 **미검증 가정**임을 명시. "`/plugin` 이 유일한 지원 경로" 문장은 유지 |
| C3 | accepted | 재현 확인: `pilot/docs/explanation/release-and-upgrade.md:68` = "plugin 패키지가 새 버전으로 업데이트됩니다 (Claude Code Marketplace 또는 수동 `pip` / `git pull` 실행)". 본 feature 가 확정한 (B) 와 정면 충돌하고 문자열 grep 게이트 2종이 못 잡는다. mkdocs nav 등재(`mkdocs.yml:119`)·`explanation/index.md:63` 링크도 확인. **이월이 아니라 이번 정정** — § 변경 파일에 추가 |
| C4 | accepted | 재현 확인: `prompts/evaluator.md:24`·`:39` 는 `<!-- [analyze-managed] -->` 영역이고 `@pilot-evaluator` wrapper 는 매 호출 이 파일을 Read → **본 사이클 evaluator 가 삭제된 스크립트 실행 지시를 읽는다**. § 변경 파일의 `project.md` 행을 ①`:166` 본문 교체(체크박스 `[ ]` 유지) ②`## 에이전트 간 전달사항` **신규 1행 추가**로 분리 기재. 신규 행에 (a) 게이트 ③ 의 `/plugin` 전환 (b) `evaluator.md:24`·`:39` stale — 문자 그대로 실행 금지 명시 |
| C5 | accepted | 결정(미정정)은 유지하고 **판정 1줄을 명시**하라는 취지에 동의. § 주의사항에 "#20 게이트 절차 SSOT = `project.md:166` 1곳, `20-*.plan.md:80`·`21-*.plan.md:345`·`project.md:164` 사본은 이력이라 미갱신, `RESUME.md` 는 사이클 종료 시 갱신 대상" 추가. (인용 `RESUME.md:12`·`:18` 은 그 사이 파일이 갱신돼 현재 `:14`·`:18` — 라인만 shift, 내용 동일) |
| C6 | accepted (부분 정정) | 취지 수용 — 게이트는 개수(`WARN 4 · ERROR 0`) 기준이어야 하고 `features=N` 은 판정 근거에서 제외. 다만 critic 이 든 불안정 요인(`.plan.critic.md` 계수, #23 (B))**만이 아니다**: planner 재호출 시점 실측은 `features=30`(drift `24 → 30`)으로, critic 이 기록한 `31` 과도 다르다 — 작업 트리가 `skills/23-…` 브랜치로 이동해 `features/24-*.md`·`25-*.md` 2개가 트리에서 빠진 탓. **N 은 브랜치에도 종속**이므로 baseline 표의 `features=31` 은 값 자체를 삭제하고 "N 은 판정 근거 아님" 으로 대체 |
| C7 | accepted | 실측 재현: `c3df02c` 2026-04-28 23:40 KST → `19a7ff9` 2026-04-29 11:42 KST = **12시간 2분**, 첫 릴리스 `v0.2.0` 은 2026-04-29T12:49Z(= 21:49 KST)로 **개명 이후**. spec 예외 케이스(구 id 사용자)를 **기각**으로 명시하고 근거를 § 사전 실측 표에 1행 추가 — evaluator requirements 축의 누락 오탐 방지 |
| C8 | accepted | 재현 확인: stale id 는 **9줄 / 10건**(`README.md:42` 한 줄에 2건). `pilot-update` 문자열은 `README.md:50`·`:54`·`:55`·`:147` · `getting-started.md:338` · 삭제 파일 내부 `:2`·`:9`·`:12`·`:13`·`:41` = 10건이며 전부 삭제 대상 블록·파일 안 — 라벨을 "9줄 / 10건" 으로 정정하고 `pilot-update` 전수를 열거해 "0건" 게이트 커버 근거로 삼는다. 과잉 치환 방어(레포 슬러그 보존) 재현도 확인 |
