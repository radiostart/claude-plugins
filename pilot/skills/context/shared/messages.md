# 표준 메시지 (SSOT)

스킬 / 에이전트가 사용자에게 출력하는 안내·에러 메시지의 단일 소스.
각 스킬은 메시지 key 를 참조하고, 본문은 본 문서 기준을 따른다.

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

### `project_name_required`

```
프로젝트명을 입력해주세요. 예: `/pilot:project MyProject`
```

### `project_name_reserved`

```
`{이름}` 은 예약어라 프로젝트명으로 사용할 수 없습니다. 다른 이름을 선택하세요.
예약어: example, workspace, STATE, context
```

---

## 결과 메시지

### `confl_saved`

```
저장 완료. `/pilot:confl {검색어}` 로 필요한 섹션을 검색하세요.
```

### `confl_no_match`

```
검색 결과 없음. `/pilot:confl {url}` 로 먼저 기획서를 저장하세요.
```

### `confl_search_source_rovo`

```
[source: rovo-mcp] 검색 결과는 Atlassian Rovo MCP 가 반환한 시맨틱 매칭입니다.
원문 인용·정책 점검에는 `/pilot:confl {page_id}` 로 fetch 한 docs/ 파일을 근거로 사용하세요.
```

### `confl_search_source_local`

```
[source: local] 검색 결과는 docs/ 에 저장된 원문 기준입니다.
```

### `confl_mcp_unavailable`

```
Atlassian Rovo MCP 호출에 실패하여 로컬 docs/ 검색으로 폴백했습니다.
원인: {원인}
강제로 로컬만 사용하려면 `/pilot:confl {검색어} --local` 을 사용하세요.
```

### `confl_policy_review_local_only`

```
정책 이행 점검 모드에서는 로컬 docs/ 원문만 근거로 사용해야 합니다.
`/pilot:confl {검색어} --local` 또는 `/pilot:confl all` 로 전환하세요.
```

### `analyze_all_done`

```
모든 기획서가 이미 분석되었습니다. 재분석하려면 `/pilot:analyze --force` 를 사용하세요.
```

### `tdd_already_active`

```
이 프로젝트는 이미 TDD 모드입니다. 누락된 항목만 보완합니다.
```

### `verification_report_example`

```
## VERIFICATION REPORT
- status: READY
- feature: #10 주문 취소 API
- gates:
  - requirements: pass — features/10-order-cancel.md § 조건/트리거/기대결과
  - tdd_evidence:  pass — .plan.md 스텝 1~4 모두 [Red][Green] 기록
  - test_run:      pass — bundle exec rspec spec/services/order_cancel_spec.rb (exit 0)
  - scope:         pass — .focus.md 범위 내 (app/services/order_cancel_service.rb)
  - drift:         none
- issues_to_fix:
  - none
- next: #11 취소 이력 조회
```

NOT_READY 예시:

```
## VERIFICATION REPORT
- status: NOT_READY
- feature: #10 주문 취소 API
- gates:
  - requirements: fail — 환불 트리거 미구현 (features/10-order-cancel.md § 기대결과 3)
  - tdd_evidence:  fail — .plan.md 스텝 3 [Red] 누락
  - test_run:      pass — bundle exec rspec spec/services/order_cancel_spec.rb (exit 0)
  - scope:         pass
  - drift:         none
- issues_to_fix:
  - [high] 환불 트리거 미구현 — app/services/order_cancel_service.rb:42
  - [med]  스텝 3 [Red] 증거 누락 — .plan.md:15
- next: null
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

### 발송 본문 (참고)

`slack-notify.py build_message()` 가 생성하는 Slack 본문. 변경 시 `tools/slack-notify.py` 수정.

- complete: `✅ [{project}] {channel} #{feature_id} 작업 완료 (evaluator READY)`
- approval: `⏸ [{project}] {channel} 승인 필요: {message}`

---

## 적용 규칙

- 스킬 SKILL.md 는 "실패 시 `messages.md:no_active_project` 출력 후 종료" 와 같이 **key 로 참조**한다.
- 본문을 복제하지 않는다. 메시지 문구 변경 시 이 파일만 수정한다.
- 치환 가능한 파라미터는 `{변수}` 로 표기한다.
