---
name: slack
description: >-
  현재 진행중인 프로젝트의 Slack 알림을 설정·테스트·확인·해제할 때 사용한다.
  활성화 시 작업 완료·사용자 승인 이벤트가 해당 프로젝트 채널로 전송된다.
  설정은 `workspace/projects/{PROJECT}/.slack.env` 를 SSOT 로 관리한다.
---

현재 진행중인 프로젝트에 Slack 알림을 설정한다.

사용법: $ARGUMENTS

**서브커맨드:**

| 인자 | 동작 |
| --- | --- |
| (없음) | `.slack.env` 를 생성하고 채널·이벤트를 대화식으로 설정 |
| `test` | 현재 설정으로 테스트 메시지 1건 발송 |
| `status` | `.slack.env` 존재·필드·gitignore 보호 여부 요약 |
| `disable` | 비활성화 방법 안내 (파일 직접 삭제) |

**사용 예:**

```
/pilot:slack
/pilot:slack test
/pilot:slack status
/pilot:slack disable
```

---

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P1** 수행.

- P1 적용 안 함 (workspace 자체 초기화).
- P2: 진행중 프로젝트 `{PROJECT}` 확인. 없으면 `no_active_project` 출력 후 종료.

`{PROJECT_DIR}` = `workspace/projects/{PROJECT}`.

---

## 공통 선행 절차 (모든 서브커맨드)

모든 서브커맨드는 **먼저 doctor 로 .gitignore 보호 상태를 점검**한다. 누락 시 즉시 주입되므로 secret 이 절대 커밋되지 않도록 보장.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace 2>&1 | grep -E "\.gitignore secrets|\[CRITICAL\]" || true
```

- `[CRITICAL]` 이 출력되면 **즉시 중단**하고 사용자에게 원문을 그대로 보여준다. 이후 서브커맨드 수행 금지 — 사용자의 `git rm --cached` + webhook 재발급이 선행되어야 한다.
- `.gitignore secrets: 누락 패턴 자동 주입` 이 출력되면 사용자에게 "리포 루트 `.gitignore` 에 `.slack.env` 가 자동 추가되었습니다. 이 변경을 커밋하세요." 안내.

---

## 수행 절차

### 서브커맨드: (없음) — 활성화

1. `{PROJECT_DIR}/.slack.env` 존재 여부 확인.
   - **있으면**: [messages.md](../context/shared/messages.md) 의 `slack.already_active` 출력 후 종료. 파일 편집·`slack status`·`slack disable` 을 안내한다.
2. **대화식 입력:**
   - 채널명 (예: `#project-x`) — 필수. 빈 값이면 재질의.
   - 이벤트 — 기본값 `complete,approval`. 사용자가 엔터만 치면 기본값 적용. 별도 입력 시 `complete`·`approval` 중 쉼표 구분.
3. `{PROJECT_DIR}/.slack.env` 를 아래 내용으로 **Write** (파일 퍼미션 `0600`):

   ```env
   # pilot Slack notifier — do NOT commit
   # 리포 루트 .gitignore 에 `.slack.env` 가 있어야 안전합니다.
   SLACK_WEBHOOK_URL=
   SLACK_CHANNEL={채널명}
   SLACK_EVENTS={이벤트목록}
   ```

4. 퍼미션 설정:

   ```bash
   chmod 600 {PROJECT_DIR}/.slack.env
   ```

5. `git check-ignore {PROJECT_DIR}/.slack.env` 실행. exit code ≠ 0 이면 `.gitignore` 가 제대로 동작하지 않는 것 — **파일을 즉시 삭제하고** `slack.tracked_critical` 요지의 경고를 출력한 뒤 종료.

6. [messages.md](../context/shared/messages.md) 의 `slack.activated` 를 `{채널명}`·`{이벤트목록}`·`{파일경로}` 로 치환해 출력.

7. 사용자에게 "SLACK_WEBHOOK_URL 을 파일에 붙여넣으셨다면 `/pilot:slack test` 를 실행하세요." 안내.

### 서브커맨드: `test`

1. `{PROJECT_DIR}/.slack.env` 없으면 `"활성화된 Slack 설정이 없습니다. /pilot:slack 으로 먼저 활성화하세요."` 출력 후 종료.
2. 아래 Bash 명령 실행:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/tools/slack-notify.py \
     --event approval \
     --workspace workspace \
     --message "테스트 메시지입니다 (/pilot:slack test)"
   ```

3. stderr 가 비어 있으면 [messages.md](../context/shared/messages.md) 의 `slack.test_ok` 출력.
4. stderr 에 내용이 있으면 원문 그대로 출력 + `slack.test_fail` 의 "원인/재시도" 안내 덧붙이기.

### 서브커맨드: `status`

1. 아래 항목을 **표 1개**로 출력:

   | 항목 | 상태 |
   | --- | --- |
   | `.slack.env` | 존재 / 없음 (없으면 이후 행 전부 `-`) |
   | `SLACK_WEBHOOK_URL` | 설정됨 / 비어있음 (URL 자체는 출력 금지) |
   | `SLACK_CHANNEL` | 값 그대로 |
   | `SLACK_EVENTS` | 값 그대로 (빈 값이면 기본값 `complete,approval`) |
   | `.gitignore` 패턴 | ✅ / ❌ (`grep -q "^\.slack\.env$" {리포루트}/.gitignore` 로 판단) |
   | git tracked | 안전 (untracked) / 위험 (tracked) |

   판단 명령:

   ```bash
   # tracked 검사
   git -C {PROJECT_DIR} ls-files --error-unmatch .slack.env
   # gitignore 패턴
   grep -q "^\.slack\.env$" $(git rev-parse --show-toplevel)/.gitignore
   ```

2. `git tracked: 위험` 이면 [messages.md](../context/shared/messages.md) 의 `slack.tracked_critical` 의 `git rm --cached` 명령을 실제 경로로 치환해 함께 출력.

### 서브커맨드: `disable`

[messages.md](../context/shared/messages.md) 의 `slack.disable_hint` 를 `{프로젝트경로}` 치환해 출력. **Claude 가 직접 `rm` 을 실행하지 않는다.** destructive 조치는 사용자 확인이 필요한 경로.

---

## 드리프트 대응

없음. 이 스킬은 `.slack.env` 를 직접 쓰는 유일 경로이므로 drift 가 발생할 소스가 없다.
