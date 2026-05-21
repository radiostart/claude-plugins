# Slack 알림 설정

!!! info "한 줄 요약"
    프로젝트별 Slack 채널로 작업 완료·승인 요청 이벤트를 자동 전송. 설정은 `workspace/projects/{PROJECT}/.slack.env` 가 SSOT. 파일이 없으면 notifier 는 자동 no-op.

## 전제

- 활성 프로젝트가 있다.
- Slack incoming webhook URL 또는 bot token + channel ID 가 준비돼 있다.
- 본 프로젝트 단위 알림이라는 점 — 워크스페이스 전역 설정이 아니라 *각 프로젝트가 독립* 설정.

## 절차

### 1. 설정

```bash
/pilot:slack setup
```

대화형 wizard 가:

- Webhook URL 또는 Bot Token + Channel ID 를 묻고
- `workspace/projects/{PROJECT}/.slack.env` 에 저장 (gitignored 권장 — `pilot/.gitignore` 에 추가)
- 테스트 메시지 1 회 전송해 정상 동작 확인

### 2. 알림 이벤트 종류

활성화 시 다음 이벤트에서 자동 전송:

| 이벤트 | 발생 시점 | 메시지 예 |
|---|---|---|
| `complete` | `@pilot-evaluator` 가 `status: READY` 출력 | `✅ [Proj] #01 작업 완료 (evaluator READY)` |
| `approval` | `@pilot-planner` 가 계획 확정 후 사용자 확인 대기 | `⏸ [Proj] 승인 필요: 계획 확인 필요: #01 ...` |

이벤트 본문에는 plan 내용·코드 같은 *민감 정보 미포함* — 사실 통지만.

### 3. 상태 확인

```bash
/pilot:slack status
```

현재 활성 프로젝트의 `.slack.env` 존재 여부와 어느 채널로 가는지 보고.

### 4. 테스트 발송

```bash
/pilot:slack test
```

현재 설정으로 테스트 메시지 1 회 전송 — 채널 권한·webhook 유효성 검증.

### 5. 해제

```bash
/pilot:slack off
```

`.slack.env` 를 `.slack.env.disabled` 로 rename. notifier 가 no-op 가 되지만 설정값은 보존 — `/pilot:slack on` 으로 즉시 복구 가능.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:slack`](../reference/skills/slack.md) · [`tools/slack-notify.py`](../reference/tools/slack-notify.md)
- :material-lightbulb-on: Explanation: SSOT 가 *프로젝트 단위* 인 이유 (워크스페이스 전역이 아닌) 는 [SSOT 와 derived](../explanation/index.md) 에서.
