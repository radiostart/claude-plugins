---
name: slack
description: >-
  현재 진행중인 프로젝트의 Slack 알림을 설정·테스트·확인·해제할 때
  사용한다. 활성화 시 완료·승인·PR 이벤트를 프로젝트 채널로 전송한다.
  설정 SSOT (`.slack.env`)·이벤트 상세는 본문.
---

현재 진행중인 프로젝트에 Slack 알림을 설정한다. `.slack.env` 가 SSOT (퍼미션 `0600`).

사용법: $ARGUMENTS

| 인자 | 동작 |
| --- | --- |
| (없음) | `.slack.env` 생성 + 채널·이벤트 대화식 설정 |
| `test` | 현재 설정으로 테스트 메시지 1건 발송 |
| `status` | `.slack.env` 존재·필드·gitignore 보호 여부 요약 |
| `disable` | 비활성화 방법 안내 (파일 직접 삭제 — Claude 가 rm 직접 실행 금지) |

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P1** 수행. 실패 시 [messages.md](../context/shared/messages.md) 의 `no_active_project` 출력 후 종료. `{PROJECT_DIR}` = `workspace/projects/{PROJECT}`.

**공통 선행 (모든 서브커맨드)** — 먼저 doctor 로 `.gitignore` 보호 상태를 점검한다 (secret 이 커밋되지 않도록 보장):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace 2>&1 | grep -E "\.gitignore secrets|\[CRITICAL\]" || true
```

`[CRITICAL]` 출력 시 **즉시 중단** + 원문 그대로 전달 (사용자의 `git rm --cached` + webhook 재발급 선행 필요 — 이후 서브커맨드 수행 금지). `.gitignore secrets: 누락 패턴 자동 주입` 출력 시 "리포 루트 `.gitignore` 에 `.slack.env` 가 자동 추가됨, 커밋하세요" 안내.

## 수행 절차

### (없음) — 활성화

`.slack.env` 이미 존재하면 [messages.md](../context/shared/messages.md) 의 `slack.already_active` 출력 후 종료 (파일 편집·`status`·`disable` 안내). 없으면 채널명(필수)·이벤트(기본 `complete,approval,pr`, 쉼표 구분) 대화식 입력 후 아래 env 필드로 `{PROJECT_DIR}/.slack.env` Write + `chmod 600`. **지원·기본 목록 SSOT 는 `tools/slack-notify.py` 의 `SUPPORTED_EVENTS`/`DEFAULT_EVENTS` 상수다** — 이벤트 추가 시 상수를 먼저 고치고 본 문서를 맞춘다:

```env
SLACK_WEBHOOK_URL=
SLACK_CHANNEL={채널명}
SLACK_EVENTS={이벤트목록}
```

`git check-ignore {PROJECT_DIR}/.slack.env` exit code ≠ 0 이면 `.gitignore` 미보호 — **파일을 즉시 삭제**하고 `slack.tracked_critical` 경고 출력 후 종료 (중앙 관리 등으로 리포 `.gitignore` 를 편집할 수 없으면 체크아웃 로컬 `.git/info/exclude` 에 `.slack.env` 를 추가해도 된다 — 커밋 불필요·본인 체크아웃 한정). 정상이면 `slack.activated` 출력({채널명}·{이벤트목록}·{프로젝트경로} 치환) + "webhook 을 붙여넣었다면 `/pilot:slack test` 실행" 안내.

### `test`

`.slack.env` 없으면 "활성화된 Slack 설정이 없습니다. `/pilot:slack` 으로 먼저 활성화하세요." 후 종료. 있으면:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/slack-notify.py --event approval --workspace workspace --message "테스트 메시지입니다 (/pilot:slack test)"
```

stderr 가 비면 `slack.test_ok` 출력, 있으면 원문 + `slack.test_fail` 안내 덧붙이기.

### `status`

`.slack.env` 존재 / `SLACK_WEBHOOK_URL` 설정됨·비어있음(**URL 값 자체는 출력 금지**) / `SLACK_CHANNEL` / `SLACK_EVENTS`(빈 값이면 기본값 표기) / `.gitignore` 패턴 여부 / git tracked 여부(`git -C {PROJECT_DIR} ls-files --error-unmatch .slack.env`) 를 표 1개로 출력. tracked 위험이면 `slack.tracked_critical` 의 `git rm --cached` 명령을 실제 경로로 치환해 함께 출력.

### `disable`

[messages.md](../context/shared/messages.md) 의 `slack.disable_hint` 를 `{프로젝트경로}` 치환해 출력. **Claude 가 직접 `rm` 을 실행하지 않는다** (destructive 조치는 사용자 확인 필요).

## 드리프트 대응

없음 — 이 스킬은 `.slack.env` 를 직접 쓰는 유일 경로라 drift 발생 소스가 없다.
