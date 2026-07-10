# Slack 알림 설정

!!! info "한 줄 요약"
    프로젝트별 Slack 채널로 작업 완료 및 승인 요청 이벤트를 자동으로 전송합니다. 설정 정보는 `workspace/projects/{PROJECT}/.slack.env` 파일을 SSOT로 삼아 관리하며, 파일이 존재하지 않을 경우 notifier 모듈은 자동으로 no-op(동작 생략) 처리됩니다.

## 전제 조건

- 활성화된 project가 존재해야 합니다.
- Slack incoming webhook URL 또는 bot token 과 channel ID 가 미리 준비되어 있어야 합니다.
- 알림은 워크스페이스 전역이 아닌 *각 프로젝트 단위로 독립적*으로 설정 및 관리됩니다.

## 작업 절차

### 1. 설정 초기화 및 등록

```bash
/pilot:slack setup
```

대화형 wizard 가 실행되며 아래 절차를 밟습니다:

- Webhook URL 또는 Bot Token + Channel ID 설정을 입력 받습니다.
- 설정값을 `workspace/projects/{PROJECT}/.slack.env` 파일에 저장합니다 (보안을 위해 gitignored 처리를 권장하며, `pilot/.gitignore` 에 추가해 관리하십시오).
- 테스트 메시지를 1회 발송하여 연동이 성공했는지 검증합니다.

### 2. 지원하는 알림 이벤트 목록

연동 완료 시 다음 주요 이벤트 발생 단계에서 알림이 자동으로 전송됩니다:

| 이벤트 유형 | 발생 시점 | 알림 메시지 예시 |
|---|---|---|
| `complete` | `@pilot-evaluator` 가 최종 검증 후 `status: READY` 상태를 반환 시 | `✅ [Proj] #01 작업 완료 (evaluator READY)` |
| `approval` | `@pilot-planner` 가 계획 수립을 끝내고 사용자 승인을 대기할 때 (명시적 발송) | `⏸ [Proj] 승인 필요: 계획 확인 필요: #01 ...` |
| `approval` (hook 릴레이) | Claude Code harness 의 `PermissionRequest` 훅 — 권한 승인 다이얼로그가 표시되는 순간(도구 실행 전), `hooks/slack-notify.sh` 어댑터가 훅 stdin JSON 을 `tools/slack-notify.py --from-hook` 으로 백그라운드 릴레이 | `⏸ [Proj] 승인 필요: [Bash] ...` (도구명 + command/file_path 요약, 500자 잘림) |
| `approval` (hook 릴레이) | harness 의 `Notification` 훅 (`permission_prompt` · `idle_prompt` 등) — 위와 동일한 어댑터 경로로 릴레이 | `⏸ [Proj] 승인 필요: {알림 본문}` |

hook 릴레이 경로는 `hooks/hooks.json` 이 `PermissionRequest` · `Notification` 두 harness 이벤트에 `hooks/slack-notify.sh` 를 배선해 동작하며, `--from-hook` 처리(`tools/slack-notify.py`)에서 이벤트가 **항상 `approval` 로 분류**됩니다. 따라서 `.slack.env` 의 `SLACK_EVENTS` 에서 `approval` 을 제외하면 planner 명시 발송과 hook 릴레이 알림이 함께 비활성화됩니다.

알림 본문 메시지에는 구체적인 plan 설계안이나 소스 코드 등의 *민감 정보는 포함되지 않으며*, 단순히 처리 상태 변경 사실만 전달합니다.

!!! note "참고 — approval 알림의 중복 도착 가능성"
    `@pilot-planner` 가 계획 승인을 요청하며 명시적으로 발송하는 `approval` 알림과, 같은 대기 시점에 harness 가 발생시키는 `Notification`(예: `idle_prompt`) 훅 릴레이 알림이 겹쳐 하나의 대기 상황에 대해 알림이 2건 도착할 수 있습니다. 두 경로 모두 `approval` 이벤트로 분류되므로 현재는 `SLACK_EVENTS` 설정으로 경로별로 분리해 끌 수 없습니다. 알려진 고려사항으로, 중복이 확인되면 이벤트 분리 개선을 검토합니다.

### 3. 연동 상태 확인

```bash
/pilot:slack status
```

현재 활성화된 프로젝트의 `.slack.env` 파일 존재 유무와 연동된 알림 채널 정보를 출력합니다.

### 4. 테스트 메시지 발송

```bash
/pilot:slack test
```

현재 활성화된 설정 정보를 토대로 테스트용 메시지를 즉시 1회 발송하여, 슬랙 채널 권한 및 Webhook 유효성을 검증합니다.

### 5. 알림 일시 비활성화

```bash
/pilot:slack off
```

`.slack.env` 파일을 `.slack.env.disabled` 로 이름을 변경합니다. notifier 가 비활성화되어 알림이 발송되지 않으며, 기존 연동 설정은 보존되므로 필요 시 `/pilot:slack on` 을 실행해 즉시 연동을 복구할 수 있습니다.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:slack`](../reference/skills/slack.md) · [`tools/slack-notify.py`](../reference/tools/slack-notify.md)
- :material-lightbulb-on: Explanation: 설정 데이터가 워크스페이스 전역이 아닌 프로젝트 단위의 SSOT로 관리되는 구조적 배경은 [SSOT와 derivation](../explanation/index.md) 가이드에서 확인할 수 있습니다.
