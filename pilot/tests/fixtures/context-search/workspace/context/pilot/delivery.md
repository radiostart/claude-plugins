# pilot — Delivery skills

작업 결과를 외부 시스템 (git·GitHub·Slack) 으로 내보낸다. 3 개 스킬: `commit` `pr` `slack`.

---

## `/pilot:commit`

git 커밋 작성 (`pilot/skills/commit/SKILL.md:1-8`).

- **사전 확인**: P1 (`pilot/skills/commit/SKILL.md:10-12`).
- **커밋 규칙 로드** (`pilot/skills/commit/SKILL.md:14-18`):
  - `${CLAUDE_PLUGIN_ROOT}/skills/context/shared/commit.md` 존재 시 Read.
  - 부재 시 fallback — scope 없이 한국어 제목 50자 이내.
- **수행** (`pilot/skills/commit/SKILL.md:20-22`): commit.md 의 **커밋 전 흐름**과 **커밋 메시지 규칙**을 그대로 따른다 — unstaged 파일이 있으면 포함 여부를 사용자에게 질의한 뒤, 메시지 초안을 사용자에게 확인받고 커밋 (fallback 시에도 동일).
- **scope 허용 목록** — `workspace/context/config.md` 의 `commit_scopes` 가 `hooks/commit-format.sh` 의 SSOT.

---

## `/pilot:pr`

현재 git 브랜치를 GitHub PR 로 올림 (`pilot/skills/pr/SKILL.md:12`).

- **대상 브랜치**: 현재 checkout 된 head. 다른 브랜치 push 미지원 — 먼저 `git checkout` 필요 (`pilot/skills/pr/SKILL.md:14`).
- **사전 확인**: P-1, P1 (`pilot/skills/pr/SKILL.md:18-20`).
- **PR 컨벤션 로드** (`pilot/skills/pr/SKILL.md:22-26`):
  - 워크스페이스 override: `workspace/context/pr.md` 우선.
  - fallback: `${CLAUDE_PLUGIN_ROOT}/skills/context/shared/pr.md`.
  - 둘 다 부재 시 **최소 본문 규칙** (Summary + Test plan 두 섹션만, 라벨·Q-템플릿 없음) (`pilot/skills/pr/SKILL.md:30-46`).
- **`pr_default_base` 결정** (`pilot/skills/pr/SKILL.md:49`): `workspace/context/config.md` 우선 → 둘 다 없으면 하드 fallback `develop`.
- **Base branch 결정** (`pilot/skills/pr/SKILL.md:53-65`):

  ```
  state 의 pr_base_branch 키 있음?
  ├─ Yes → "타겟: <X> (저장됨). Enter=유지 / 새 입력=변경" 질의
  │         ├─ Enter        → base = X. state 변경 없음
  │         └─ 새 값 입력    → base = 입력값. state 갱신
  └─ No  → "타겟 브랜치? (Enter=<pr_default_base>)" 질의
            ├─ Enter        → base = pr_default_base. state 미저장
            └─ 새 값 입력    → base = 입력값. state 신규 기록
  ```
- **Remote 검증** (필수, `pilot/skills/pr/SKILL.md:67-77`): `git ls-remote --exit-code origin <base>`. 비 0 → 재질의 루프 (최대 3 회).
- **수행 절차** (`pilot/skills/pr/SKILL.md:80-105` — 10 단계):
  1. **변경 확인** — `git status`, `git log <base>..HEAD --oneline`, `git diff <base>...HEAD --stat`.
  2. **uncommitted 차단** — staged·unstaged 있으면 "`/pilot:commit` 으로 먼저 커밋하세요" 안내 후 종료.
  3. **광역 회귀 (soft gate)** (`:84-87`) — config.md 의 `regression_command` 설정 시 PR 생성 전 1회 실행. 실패 → 요약 제시 후 진행 여부 사용자 확인 (자동 차단 안 함). 미설정 → skip + 설정 권장 INFO 1줄.
  4. **upstream push** (필요 시 `git push -u origin <branch>`).
  5. **PR 본문 초안** — pr.md 본문 구조 + `git log` 커밋 메시지 + `project.md` 목표·체크리스트 → Summary, `features/*.md` 링크 → Notes, `docs/` Confluence URL → Why.
  6. **사용자 확인** (제목·본문·base·head). 수정 1 라운드.
  7. **PR 생성** — `gh pr create --base <base> --head <branch> --title <title> --body <body>` (HEREDOC).
  8. **state 갱신** — base 명시 입력이면 `.agent-state.yml.pr_base_branch` 기록.
  9. **Slack 알림** — `.slack.env` 활성 + `SLACK_EVENTS` 에 `pr` 포함 (default: 포함) 시 PR URL 전송 (`tools/slack-notify.py --event pr`). `--no-slack` 으로 skip. 전송 실패는 PR 생성 차단 안 함.
  10. **완료 안내** — PR URL 출력.
- **옵션** (`pilot/skills/pr/SKILL.md:109-119`): `--draft` · `--base <branch>` · `--no-slack` · `--title "..."`.
- **제약** (`pilot/skills/pr/SKILL.md:157-164`):
  - 현재 브랜치 == base → 종료.
  - `gh` 미인증 → `gh auth login` 안내 후 종료.
  - `--no-verify` / hook 우회 금지.
  - base 질의 루프 최대 3 회.

---

## `/pilot:slack`

활성 프로젝트의 Slack 알림 설정·테스트 (`pilot/skills/slack/SKILL.md:9`).

- **서브커맨드** (`pilot/skills/slack/SKILL.md:13-19`):

  | 인자 | 동작 |
  | --- | --- |
  | (없음) | `.slack.env` 생성 + 채널·이벤트 대화식 설정 |
  | `test` | 현재 설정으로 테스트 메시지 1 건 |
  | `status` | `.slack.env` 존재·필드·gitignore 보호 요약 |
  | `disable` | 비활성화 방법 안내 (Claude 가 직접 `rm` 안 함) |

- **사전 확인**: P1 — `{PROJECT}` 획득 (`pilot/skills/slack/SKILL.md:33-40`).
- **공통 선행 절차** — gitignore 보호 점검 (`pilot/skills/slack/SKILL.md:44-53`):
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace 2>&1 | grep -E "\.gitignore secrets|\[CRITICAL\]" || true
  ```
  - `[CRITICAL]` → **즉시 중단**. 사용자 `git rm --cached` + webhook 재발급 선행.
  - `.gitignore secrets: 누락 패턴 자동 주입` → "리포 루트 `.gitignore` 에 `.slack.env` 자동 추가됨, 이 변경을 커밋하세요" 안내.
- **활성화 — 인자 없음** (`pilot/skills/slack/SKILL.md:59-86`):
  1. `.slack.env` 존재 확인 → 있으면 `slack.already_active`.
  2. 채널명·이벤트 (기본 `complete,approval`) 대화식 입력.
  3. `.slack.env` Write (퍼미션 `0600`):
     ```env
     # pilot Slack notifier — do NOT commit
     SLACK_WEBHOOK_URL=
     SLACK_CHANNEL={채널명}
     SLACK_EVENTS={이벤트목록}
     ```
  4. `chmod 600`.
  5. `git check-ignore` 검증. 실패 시 파일 즉시 삭제 + `slack.tracked_critical` 출력.
  6. `slack.activated` 출력.
- **`test`** (`pilot/skills/slack/SKILL.md:88-101`): `.slack.env` 없으면 안내 후 종료. 있으면:
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/tools/slack-notify.py \
    --event approval \
    --workspace workspace \
    --message "테스트 메시지입니다 (/pilot:slack test)"
  ```
- **`status`** (`pilot/skills/slack/SKILL.md:103-126`): `.slack.env`·`SLACK_WEBHOOK_URL` (값 출력 금지)·`SLACK_CHANNEL`·`SLACK_EVENTS`·gitignore 패턴·git tracked 표 출력. tracked: 위험 시 `slack.tracked_critical` 의 `git rm --cached` 명령 함께 출력.
- **`disable`** (`pilot/skills/slack/SKILL.md:127-129`): `slack.disable_hint` 출력. **Claude 가 직접 `rm` 실행하지 않는다** — destructive 조치는 사용자 확인 경로.
- **드리프트 대응** (`pilot/skills/slack/SKILL.md:133-135`): 없음. 이 스킬이 `.slack.env` 직접 쓰는 유일 경로이므로 drift 발생 소스 없음.
