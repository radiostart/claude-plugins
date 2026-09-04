---
name: pr
description: >-
  사용자가 "PR 올려줘" 등 현재 브랜치의 GitHub Pull Request 생성을 요청할
  때 사용한다. base branch 는 자동 결정 (사용자 명시가 우선), 제목·본문
  컨벤션은 본문 규약을 따른다.
---

# /pilot:pr

현재 git 브랜치의 변경을 PR 로 올린다.

대상 브랜치: 현재 checkout 된 head (다른 브랜치 push 는 지원하지 않음 — 먼저 `git checkout`).

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P-1, P1** 수행 (`{PROJECT}` 획득).

PR 컨벤션 lookup 순서 (**레포지터리 단위** — 워크스페이스 공통): `workspace/context/pr.md`(워크스페이스 override) → 부재 시 [`shared/pr.md`](../context/shared/pr.md)(플러그인 default). 플러그인 내장이라 이 둘이 **모두 부재**하는 상황은 정상 설치에서 발생하지 않지만, 만일을 대비한 최종 fallback(라벨·Q-템플릿 없는 Summary+Test plan 2 섹션 최소 본문)은 [`shared/pr.md`](../context/shared/pr.md) § 3 과 동일 구조를 따른다.

## Base branch 결정

`.agent-state.yml` 의 `pr_base_branch` 존재 여부로 분기: 있으면 "타겟: {값} (저장됨). Enter=유지 / 새 입력=변경" 질의(Enter 시 state 미변경) — 없으면 "타겟 브랜치? (Enter={pr_default_base})" 질의(Enter 시 config 의 `pr_default_base` 사용, state 미저장 — 새 값 입력 시에만 `pr_base_branch` 신규 기록). `pr_default_base` 미설정이면 하드 fallback `develop`.

base 결정 후 **PR 생성 전 필수**: `git ls-remote --exit-code origin <base>` 검증. 실패 시 "origin 에 없습니다. 다시 입력하세요" 후 재질의 (최대 3회 후 종료).

## 수행 절차

1. **변경 확인** — `git status` / `git log <base>..HEAD --oneline` / `git diff <base>...HEAD --stat` 으로 PR 범위 확인.
2. **uncommitted 차단** — staged·unstaged 있으면 `/pilot:commit` 선행 안내 후 종료.
3. **광역 회귀 (soft gate)** — `config.md` 의 `regression_command` 설정 시 1회 실행. 통과 → 진행 / 실패 → 결과 요약 후 진행 여부 확인(자동 차단 안 함) / 미설정 → skip + INFO 권장.
4. **upstream push** — 브랜치가 origin 에 없거나 ahead 면 `git push -u origin <branch>`.
5. **PR 본문 초안** — pr.md(팀/플러그인) 구조 따라 작성. `git log <base>..HEAD` 커밋 메시지가 1차 재료. `project.md`(목표·체크리스트)→Summary, `features/*.md`→Notes, docs/ Confluence URL→Why. 팀 pr.md 에 Q1~Q6 형식 있으면 그 형식 사용.
6. **사용자 확인** — 제목·본문·base·head 를 보여주고 승인 받음 (수정 요청 1 라운드 반영). 이 게이트에 예외는 없다 — PR 은 외부 노출 경계라 `/pilot:autopilot` 사이클 진행 중에도 사후화하지 않는다.
7. **PR 생성** — `gh pr create --base <base> --head <branch> --title <title> --body <body>` (HEREDOC 사용).
8. **state 갱신** — base 가 명시 입력이면 `pr_base_branch` 기록 (Enter=default 면 미저장).
9. **Slack 알림** — `.slack.env` 활성 + `SLACK_EVENTS` 에 `pr` 포함(default 포함) 시:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/tools/slack-notify.py --event pr --workspace workspace --message "<title> — <pr_url>"
   ```

   `--no-slack` 시 skip. 발송 계약([messages.md](../context/shared/messages.md) § Slack 알림 메시지) 대로 실패해도 비차단.
10. **완료 안내** — PR URL 출력.

## 옵션 (인자)

`$ARGUMENTS` 파싱: (없음) 위 절차 그대로 · `--draft` → `gh pr create --draft` · `--base <branch>` → base 질의 skip(입력값 사용, state 에 명시 입력으로 기록) · `--no-slack` → Slack skip · `--title "..."` → 제목 자동 생성 skip.

## 제약

- 현재 브랜치가 base 와 동일하면 종료 ("base 와 head 가 동일").
- `gh` CLI 미인증 시 `gh auth login` 안내 후 종료.
- `--no-verify`/hook 우회 사용 금지.
- base 질의 루프는 최대 3회 — 3회 모두 실패하면 종료.

## 참조

- PR 컨벤션 (default): [`shared/pr.md`](../context/shared/pr.md)
- state 스키마 (`pr_base_branch`): [`lifecycle/state-schema.md`](../context/lifecycle/state-schema.md)
- 커밋 선행: `/pilot:commit`
