# 표준 메시지 (SSOT)

스킬 / 에이전트가 사용자에게 출력하는 안내·에러 메시지의 단일 소스.
각 스킬은 메시지 key 를 참조하고, 본문은 본 문서 기준을 따른다.
소비처가 정확히 1곳인 메시지는 해당 소비 파일에 인라인한다 — 이 파일에는
다소비 key 와 공유 파일(preamble.md 등)이 소비하는 key 만 남긴다.

톤 원칙:

- **상황 설명 → 해결 명령** 2단 구조
- 경어체 ("~하세요")
- 명령은 백틱으로 감싸 복사 가능하게

---

## 전제조건 메시지

### `workspace_missing`

```
workspace/ 가 없습니다. 먼저 `/pilot:init` 으로 초기화하세요.
```

### `no_active_project`

```
진행중인 프로젝트가 없습니다. `/pilot:project {프로젝트명}` 으로 먼저 활성화하세요.
```

### `state_corrupt`

```
STATE.md 의 `진행중` 행이 2개 이상이거나 형식이 깨졌습니다.
`/pilot:project {프로젝트명}` 또는 `/pilot:issue` 로 다시 활성화하세요.
```

### `docs_missing`

```
docs/ 에 기획서가 없습니다. `/pilot:confl {url}` 로 먼저 기획서를 저장하세요.
```

---

## 결과 메시지

### `confl_no_match`

```
검색 결과 없음. `/pilot:confl {url}` 로 먼저 기획서를 저장하세요.
```

### `analyze_all_done`

```
모든 기획서가 이미 분석되었습니다. 재분석하려면 `/pilot:analyze --force` 를 사용하세요.
```

---

## Slack 알림 메시지

프로젝트별 Slack Incoming Webhook 으로 발송하는 알림. 설정 SSOT: `workspace/projects/{PROJECT}/.slack.env`.
발송 주체: `tools/slack-notify.py`. 사용자 인터랙션 주체: `/pilot:slack`.

### `slack.activated`

```
Slack 알림이 활성화되었습니다.
  채널: {채널명}
  이벤트: {이벤트목록}
  파일: {프로젝트경로}/.slack.env

SLACK_WEBHOOK_URL 을 파일에 붙여넣은 뒤 `/pilot:slack test` 로 확인하세요.
```

### `slack.already_active`

```
이 프로젝트에는 이미 `.slack.env` 가 있습니다. 파일을 직접 편집하거나 `/pilot:slack status` 로 상태를 확인하세요.
```

### `slack.test_ok`

```
✅ 테스트 메시지를 {채널명} 으로 전송했습니다. Slack 에서 확인하세요.
```

### `slack.test_fail`

```
❌ 테스트 전송 실패. 원인: {원인}
SLACK_WEBHOOK_URL 값과 네트워크 연결을 확인한 뒤 재시도하세요.
```

### `slack.disable_hint`

```
비활성화하려면 해당 프로젝트의 `.slack.env` 를 삭제하세요.
  rm {프로젝트경로}/.slack.env
파일을 지우면 알림이 영구 스킵됩니다.
```

### `slack.webhook_missing` (stderr 전용)

```
slack-notify: {파일경로} 에 SLACK_WEBHOOK_URL 이 비어있어 알림을 건너뜁니다.
```

### `slack.tracked_critical` (stderr 전용)

```
slack-notify: [CRITICAL] {파일경로} 가 git 에 추적되고 있습니다. 즉시 `git rm --cached {파일경로}` 실행 후 webhook URL 을 재발급하세요. 안전을 위해 이번 알림은 전송하지 않습니다.
```

### 발송 본문

구현·문구 SSOT: `tools/slack-notify.py` 의 `build_message()`.

---

## 적용 규칙

- 스킬 SKILL.md 는 "실패 시 `messages.md:no_active_project` 출력 후 종료" 와 같이 **key 로 참조**한다.
- 본문을 복제하지 않는다. 메시지 문구 변경 시 이 파일만 수정한다.
- 치환 가능한 파라미터는 `{변수}` 로 표기한다.
