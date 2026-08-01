# pilot — Delivery skills

작업 결과를 외부 시스템 (git·GitHub·Slack) 으로 내보낸다. 3 개 스킬: `commit` `pr` `slack`.

---

## `/pilot:commit`

git 커밋 작성 (`pilot/skills/commit/SKILL.md:3-7`).

- **사전 확인**: P1 (`pilot/skills/commit/SKILL.md:10-12`). 활성 행이 `| issue | {이슈명} |` 이어도 **종료하지 않고 진행한다** — 이슈 수정 커밋은 필수 경로라 P1 issue 판정의 명시적 예외다 (`pilot/skills/context/shared/preamble.md:38`).
- **커밋 규칙 로드** (`pilot/skills/commit/SKILL.md:14-18`): `${CLAUDE_PLUGIN_ROOT}/skills/context/shared/commit.md` 존재 시 Read, 부재 시 fallback (scope 없이 한국어 제목 + 50 자 이내 + 필요 시 본문).
- **수행** (`pilot/skills/commit/SKILL.md:20-22`): commit.md 의 **커밋 전 흐름**과 **커밋 메시지 규칙**을 그대로 따른다 — unstaged 파일이 있으면 포함 여부를 질의한 뒤, 규칙에 맞춘 메시지 초안을 사용자에게 확인받고 커밋한다 (fallback 시에도 unstaged 질의·사용자 확인 동일).

### 커밋 규칙 (`pilot/skills/context/shared/commit.md`)

- **1. 미스테이지 파일 확인** (`:9-26`) — `git status` 로 확인하고 **파일별로 포함 여부를 질의**한다. 한 번에 모아서 묻지 말고 파일 (또는 관련 묶음) 을 나열한 뒤 확인하며, 명백히 이번 작업과 무관한 파일은 별도로 언급한다.
- **형식** (`:36-46`): `{scope}: {한국어 설명}` 또는 티켓이 있으면 `[{티켓번호}] {한국어 설명}`.
- **scope 기준** (`:50-58`): `feat`(신규 기능) · `fix`(버그 수정) · `refactor`(기능 변경 없는 코드 개선) · `skills`(workspace/ 문서 작업) · `{기능명}`(특정 기능 국한). scope 없이 한국어 설명만으로도 무방.
- **작성 원칙** (`:60-65`): 한국어 · 제목 50 자 이내가 이상적 · 범위가 크면 본문 추가 · `wip` 은 이후 squash 예정 작업에만 허용.
- **주의사항** (`:81-85`): credentials/secrets 파일 (`.env`·`*.key`·`*credentials*` 등) 절대 미포함 · workspace/ 변경과 코드 변경은 가능하면 분리 · 푸시 전 브랜치 확인, `main`/`develop` 직접 푸시 금지.
- **훅 강제 여부** — `commit-format.sh` 는 PreToolUse:Bash 로 붙지만 **advisory 전용이라 항상 exit 0** 이고 차단하지 않는다 (`pilot/hooks/commit-format.sh:4-5·110-122`). 제목이 50 자 (UTF-8 문자 기준) 를 넘거나 scope 가 허용 목록 밖이면 stderr 경고만 낸다 (`:57·91-93·98`). scope 허용 목록의 SSOT 는 `workspace/context/config.md` `## 설정` 의 `commit_scopes` 행이며, 미설정 시 기본값은 `feat,fix,refactor,skills,wip` (`pilot/hooks/commit-format.sh:63·66-78`). `--amend` 는 검사에서 제외 (`:20`).

---

## `/pilot:pr`

현재 git 브랜치의 변경을 PR 로 올린다 (`pilot/skills/pr/SKILL.md:12`). 대상은 **현재 checkout 된 head** — 다른 브랜치 push 는 지원하지 않으므로 먼저 `git checkout` 이 필요하다 (`:14`).

- **사전 확인**: P-1, P1 (`pilot/skills/pr/SKILL.md:16-20`).
- **PR 컨벤션 lookup** (`pilot/skills/pr/SKILL.md:20`) — **레포지터리 단위** (워크스페이스 공통): `workspace/context/pr.md` (override) → 부재 시 `shared/pr.md` (플러그인 default). 플러그인 내장이라 둘 다 부재는 정상 설치에서 발생하지 않지만, 최종 fallback 은 라벨·Q-템플릿 없는 Summary + Test plan 2 섹션 최소 본문이다.
- **Base branch 결정** (`pilot/skills/pr/SKILL.md:22-26`):

  ```
  .agent-state.yml 의 pr_base_branch 키 있음?
  ├─ Yes → "타겟: {값} (저장됨). Enter=유지 / 새 입력=변경"
  │         ├─ Enter     → base = 값. state 변경 없음
  │         └─ 새 값 입력 → base = 입력값. state 갱신
  └─ No  → "타겟 브랜치? (Enter={pr_default_base})"
            ├─ Enter     → base = pr_default_base. state 미저장
            └─ 새 값 입력 → base = 입력값. pr_base_branch 신규 기록
  ```

  `pr_default_base` 미설정이면 하드 fallback `develop`. base 결정 후 **PR 생성 전 필수**로 `git ls-remote --exit-code origin <base>` 검증, 실패 시 재질의 (최대 3 회 후 종료).
- **수행 절차 10 단계** (`pilot/skills/pr/SKILL.md:28-45`):
  1. **변경 확인** — `git status` / `git log <base>..HEAD --oneline` / `git diff <base>...HEAD --stat`.
  2. **uncommitted 차단** — staged·unstaged 있으면 `/pilot:commit` 선행 안내 후 종료.
  3. **광역 회귀 (soft gate)** — `config.md` 의 `regression_command` 설정 시 1 회 실행. 통과 → 진행 / 실패 → 요약 후 진행 여부 확인 (**자동 차단 안 함**) / 미설정 → skip + INFO 권장.
  4. **upstream push** — 브랜치가 origin 에 없거나 ahead 면 `git push -u origin <branch>`.
  5. **PR 본문 초안** — pr.md 구조를 따르되 `git log <base>..HEAD` 커밋 메시지가 1 차 재료. `project.md`(목표·체크리스트)→Summary, `features/*.md`→Notes, docs/ Confluence URL→Why. 팀 pr.md 에 Q1~Q6 형식이 있으면 그 형식 사용.
  6. **사용자 확인** — 제목·본문·base·head 승인 (수정 요청 1 라운드 반영).
  7. **PR 생성** — `gh pr create --base <base> --head <branch> --title <title> --body <body>` (HEREDOC).
  8. **state 갱신** — base 가 명시 입력이면 `pr_base_branch` 기록 (Enter=default 면 미저장).
  9. **Slack 알림** — `.slack.env` 활성 + `SLACK_EVENTS` 에 `pr` 포함 시 `tools/slack-notify.py --event pr`. `--no-slack` 시 skip. 실패해도 **비차단**.
  10. **완료 안내** — PR URL 출력.
- **옵션** (`pilot/skills/pr/SKILL.md:47-49`): `--draft` · `--base <branch>` (질의 skip, 명시 입력으로 state 기록) · `--no-slack` · `--title "..."`.
- **제약** (`pilot/skills/pr/SKILL.md:51-56`): 현재 브랜치가 base 와 동일하면 종료 · `gh` 미인증 시 `gh auth login` 안내 후 종료 · **`--no-verify`/hook 우회 사용 금지** · base 질의 루프 최대 3 회.

---

## `/pilot:slack`

활성 프로젝트의 Slack 알림 설정·테스트·확인·해제 (`pilot/skills/slack/SKILL.md:9`). `.slack.env` 가 SSOT (퍼미션 `0600`).

- **서브커맨드** (`pilot/skills/slack/SKILL.md:13-18`):

  | 인자 | 동작 |
  | --- | --- |
  | (없음) | `.slack.env` 생성 + 채널·이벤트 대화식 설정 |
  | `test` | 현재 설정으로 테스트 메시지 1 건 발송 |
  | `status` | `.slack.env` 존재·필드·gitignore 보호 여부 요약 |
  | `disable` | 비활성화 방법 안내 (파일 직접 삭제 — Claude 가 `rm` 직접 실행 금지) |

- **사전 확인**: P1 (`pilot/skills/slack/SKILL.md:20-22`). `{PROJECT_DIR}` = `workspace/projects/{PROJECT}`.
- **공통 선행 — 모든 서브커맨드** (`pilot/skills/slack/SKILL.md:24-30`): secret 이 커밋되지 않도록 먼저 doctor 로 `.gitignore` 보호 상태를 점검한다.

  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace 2>&1 | grep -E "\.gitignore secrets|\[CRITICAL\]" || true
  ```

  `[CRITICAL]` 출력 시 **즉시 중단** + 원문 그대로 전달 (사용자의 `git rm --cached` + webhook 재발급 선행 필요, 이후 서브커맨드 수행 금지). `.gitignore secrets: 누락 패턴 자동 주입` 이면 "리포 루트 `.gitignore` 에 `.slack.env` 가 자동 추가됨, 커밋하세요" 안내.
- **활성화 (인자 없음)** (`pilot/skills/slack/SKILL.md:34-44`): `.slack.env` 이미 존재하면 `slack.already_active` 후 종료. 없으면 채널명 (필수) · 이벤트 (기본 `complete,approval`) 대화식 입력 → `SLACK_WEBHOOK_URL`·`SLACK_CHANNEL`·`SLACK_EVENTS` 3 필드 Write + `chmod 600`. `git check-ignore` exit ≠ 0 이면 `.gitignore` 미보호 — **파일을 즉시 삭제**하고 `slack.tracked_critical` 경고 후 종료.
- **`test`** (`pilot/skills/slack/SKILL.md:46-54`): `.slack.env` 없으면 안내 후 종료. 있으면 `slack-notify.py --event approval --workspace workspace --message "..."`. stderr 가 비면 `slack.test_ok`, 있으면 원문 + `slack.test_fail`.
- **`status`** (`pilot/skills/slack/SKILL.md:56-58`): 존재 / `SLACK_WEBHOOK_URL` 설정됨·비어있음 (**URL 값 자체는 출력 금지**) / `SLACK_CHANNEL` / `SLACK_EVENTS` / `.gitignore` 패턴 / git tracked 여부를 표 1 개로. tracked 위험이면 `git rm --cached` 명령을 실제 경로로 치환해 함께 출력.
- **`disable`** (`pilot/skills/slack/SKILL.md:60-62`): `slack.disable_hint` 출력만. **Claude 가 직접 `rm` 을 실행하지 않는다** — destructive 조치는 사용자 확인 경로.
- **드리프트 대응** (`pilot/skills/slack/SKILL.md:64-66`): 없음 — 이 스킬이 `.slack.env` 를 직접 쓰는 유일 경로라 drift 발생 소스가 없다.
- **발송 도구 계약** (`pilot/tools/slack-notify.py`): 지원 이벤트는 `complete`·`approval`·`pr` (`:35·193-198`). `--from-hook` 은 훅 stdin JSON 을 읽어 `event="approval"` 로 강제하고 `--event`/`--message` 를 무시한다 (`:209-224`). **모든 경로가 return 0** 이라 훅·파이프라인을 차단하지 않으며 (`:22-23·267`), `.slack.env` 가 git tracked 이면 `[CRITICAL]` stderr 와 함께 발송을 하드 차단한다 (`:253-261`). HTTP 타임아웃 3 초, 훅 detail 500 자 절단 (`:37-38`).
- **훅 배선** (`pilot/hooks/hooks.json:59-80`): `slack-notify.sh` 가 `PermissionRequest` 와 `Notification` 두 이벤트에 등록돼 있고, stdin 을 그대로 `slack-notify.py --from-hook` 에 중계한다 (`pilot/hooks/slack-notify.sh:28·62-64`). 워크스페이스는 `$CLAUDE_PROJECT_DIR/workspace`, 없으면 `git worktree list --porcelain` 으로 메인 워크트리의 workspace 를 찾는다 (`:34-43`). POST 는 백그라운드 + `disown`, 항상 exit 0 (`:61-70`).
