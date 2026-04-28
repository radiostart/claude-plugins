---
name: pr
description: >-
  사용자가 "PR 올려줘", "풀 리퀘스트 생성" 등 현재 브랜치를 GitHub Pull
  Request 로 올리길 요청할 때 사용한다. base branch 는 state·config·
  공통 config 순으로 자동 결정하며 사용자 명시 입력 시 state 에 저장한다.
  제목·본문 컨벤션은 `skills/context/shared/pr.md` 를 따른다.
---

# /pilot:pr

현재 git 브랜치의 변경을 PR 로 올린다.

대상 브랜치: 현재 checkout 된 head. (다른 브랜치 push 는 지원하지 않음 — 먼저 `git checkout`)

---

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P-1, P1** 수행. (`{PROJECT}` 획득)

PR 컨벤션 로드 (PR 템플릿은 **레포지터리 단위** — 워크스페이스 공통):

- 워크스페이스 override: `workspace/context/pr.md` 가 존재하면 우선 Read.
- 부재 시 fallback: `${CLAUDE_PLUGIN_ROOT}/skills/context/shared/pr.md` Read.
- 둘 다 부재면 아래 **최소 본문 규칙** 으로 진행 (label·Q-템플릿 없는 default 본문).

### 최소 본문 규칙 (fallback)

팀·플러그인 pr.md 가 모두 부재할 때 사용하는 default 본문 구조. 라벨·Q1~Q6 템플릿 없이 두 섹션만 채운다.

```markdown
## Summary

- <변경 요점 1>
- <변경 요점 2>

## Test plan

- [ ] <검증 항목 1>
- [ ] <검증 항목 2>
```

- **제목**: 첫 커밋의 메시지 한 줄 (50자 이내). 여러 커밋이면 가장 의미 있는 한 줄을 선택.
- **Summary**: `git log <base>..HEAD --oneline` 결과를 bullet 으로 재구성 (1~5 항목).
- **Test plan**: 변경 영역을 검증할 수동 체크 항목. 자동 생성 못 하면 `- [ ] 동작 확인` 한 줄.
- 추가 섹션·라벨·assignee 미설정.

`pr_default_base` 키 결정 — `workspace/context/config.md` 에 정의되어 있으면 그 값, 없으면 `workspace/context/config.md`, 둘 다 없으면 하드 fallback `develop`. (orchestrate-load 의 toolchain merge 와 동일 우선순위.)

---

## Base branch 결정

state 파일: `workspace/projects/{PROJECT}/.agent-state.yml`

```
pr_base_branch 키 존재?
├─ Yes → "타겟: <X> (저장됨). Enter=유지 / 새 입력=변경" 질의
│         ├─ Enter        → base = X. state 변경 없음
│         └─ 새 값 입력    → base = 입력값. state 의 pr_base_branch 갱신
└─ No  → "타겟 브랜치? (Enter=<pr_default_base>)" 질의
          ├─ Enter        → base = pr_default_base. state 미저장
          └─ 새 값 입력    → base = 입력값. state 에 pr_base_branch 신규 기록
```

### remote 존재 검증 (필수)

base 결정 후 **PR 생성 전** 검증:

```bash
git ls-remote --exit-code origin <base>
```

- 종료 코드 0 → 진행
- 비 0 → "타겟 브랜치 `<base>` 가 origin 에 없습니다. 다시 입력하세요" 출력 후 재질의 루프

---

## 수행 절차

1. **변경 확인** — `git status`, `git log <base>..HEAD --oneline`, `git diff <base>...HEAD --stat` 으로 PR 에 포함될 변경 범위 확인.
2. **uncommitted 차단** — staged·unstaged 변경이 있으면 "`/pilot:commit` 으로 먼저 커밋하세요" 안내 후 종료.
3. **upstream push** — 현재 브랜치가 origin 에 없거나 ahead 면 `git push -u origin <branch>`.
4. **PR 본문 초안** — pr.md (팀/플러그인) 의 본문 구조에 따라 작성.
   - 변경 요약은 `git log <base>..HEAD` 의 커밋 메시지를 1차 재료로 사용.
   - 프로젝트 컨텍스트 주입: `project.md` 의 목표·완료 체크리스트 → Summary, features/*.md 링크 → Notes, docs/ Confluence URL → Why.
   - Q1~Q6 형식이 팀 pr.md 에 있으면 그 형식 사용.
5. **사용자 확인** — 제목·본문·base·head 를 보여주고 승인 받음. 수정 요청 시 한 라운드 반영.
6. **PR 생성** — `gh pr create --base <base> --head <branch> --title <title> --body <body>` (HEREDOC 사용).
7. **state 갱신** — base 가 명시 입력이면 `pr_base_branch` 를 .agent-state.yml 에 기록 (Enter=default 면 미저장).
8. **Slack 알림** — `.slack.env` 활성 + `SLACK_EVENTS` 에 `pr` 포함 (default: 포함) 시 PR URL 을 채널로 전송. 호출:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/tools/slack-notify.py \
     --event pr --workspace workspace \
     --message "<title> — <pr_url>"
   ```

   `--no-slack` 플래그 시 skip. 전송 실패는 PR 생성을 차단하지 않음 (slack-notify 는 항상 exit 0).
9. **완료 안내** — PR URL 을 사용자에게 출력.

---

## 옵션 (인자)

`$ARGUMENTS` 파싱:

| 인자 | 동작 |
|---|---|
| (없음) | 위 절차 그대로 |
| `--draft` | `gh pr create --draft` |
| `--base <branch>` | base 질의 skip, 입력값 사용. state 에는 기록 (명시 입력 취급) |
| `--no-slack` | Slack 알림 skip |
| `--title "..."` | 제목 자동 생성 skip, 입력값 사용 |

---

## 예시 흐름

### 첫 실행 (state 부재)

```
$ /pilot:pr
타겟 브랜치? (Enter=develop): release/4.5
✓ origin/release/4.5 확인
✓ 현재 브랜치 feature/foo push (3 commits ahead)

제목: feat: foo 기능 추가
base: release/4.5  head: feature/foo

본문 미리보기:
  ## Summary
  ...
  
승인? (y/n): y
✓ PR 생성: https://github.com/org/repo/pull/123
✓ .agent-state.yml 갱신: pr_base_branch=release/4.5
✓ Slack 알림 전송 (#myproject)
```

### 재실행 (state 존재)

```
$ /pilot:pr
타겟: release/4.5 (저장됨). Enter=유지 / 새 입력=변경: ⏎
✓ origin/release/4.5 확인
...
```

---

## 제약

- 현재 브랜치가 base 와 동일하면 종료 ("base 와 head 가 동일").
- `gh` CLI 미인증 시 `gh auth login` 안내 후 종료.
- `--no-verify` / hook 우회 사용 금지 (PR 자체엔 hook 없지만 push 단계 hook 우회 안 함).
- base 질의 루프는 최대 3회. 3회 모두 stale 면 종료.

---

## 참조

- PR 컨벤션 (default): [`shared/pr.md`](../context/shared/pr.md)
- state 스키마 (`pr_base_branch`): [`lifecycle/state-schema.md`](../context/lifecycle/state-schema.md)
- 후속 — AI 리뷰 처리: `/pilot:ai-review`
- 커밋 선행: `/pilot:commit`
