# 정지 사유별 해소 조치

`/pilot:autopilot` 이 **정지한 뒤에만** 소비하는 처방표다. 정지 없이 완주하는
호출에서는 읽지 않는다 (본문의 STOP 보고는 보고 형식과 정지 원칙만 유지).

정지 보고 시 아래에서 해당 사유의 행을 골라 제시한다. 재개 안내
(`/pilot:autopilot {NN}` 재실행 → 재개 확인 경유) 는 본문이 SSOT 이므로 여기서
반복하지 않는다.

| 정지 사유 | 해소 조치 |
| --------- | --------- |
| feature 부재 (사전 확인 hard-stop) | `/pilot:create-feature` 로 명세 생성 후 재실행 |
| `plan-validate` (invalid) | stderr 누락 항목 확인 → `@pilot-planner` 재호출 (plan 보완). `oq` 실패면 [open-questions.md](../../context/shared/open-questions.md) § 에스컬레이션 경로의 두 갈래 — `@pilot-planner` 재호출 (plan 에 처리 마커 보완) 또는 (d) 는 사용자가 결정을 답하면 메인 세션이 feature 파일 항목을 `- [x] {항목} → 결정: {내용}` 으로 Edit. **`/pilot:focus` 로는 안 풀린다** — `oq` 검증은 feature 체크박스·plan 마커만 본다 |
| `critic-blocking` | `@pilot-planner` 재호출 — 챌린지 반영 + `## 합의` 표 기입. 합의 후 재실행 |
| `signal-parse` | 신호 산출물의 형식 결함 — critic 단계면 `@pilot-planner-critic` 재호출로 `.plan.critic.md` 재작성 (이전 라운드 잔존 정리 포함 — critic 의 Edit 후 자기 점검), evaluator 단계면 `@pilot-evaluator` 재호출로 REPORT 재출력 (step 7 형식 자기 점검) |
| `retry-exhausted` | `.eval.md` 의 `issues_to_fix` 확인 → 구현 결함이면 `@pilot-generator` 수동 재작업, 계획 결함이면 `@pilot-planner` 재호출 (재계획) |
| `agent-error` (예외·빈 출력) | wrapper 가 보고한 원인을 먼저 해소한다 — `orchestrate-load` error 는 원문의 처방 (state 재생성·프로젝트 재활성 등) 을 따른다. 해소 후 그 단계부터 수동 재개 또는 재실행 |
| wrapper 의 사용자 질의로 중단 (enum 밖 — domain null·대상 plan 복수 후보 등) | 질의에 답한다 — 후속 wrapper 호출에도 남겨야 하는 결정이면 `/pilot:focus` 로 기록 |

## 처방이 아닌 것

- **`/pilot:focus` 는 `plan-validate`(oq) 정지를 풀지 못한다** — 기계 검증은
  feature 파일·plan 파일 상태만 보며 `.focus.md` 를 읽지 않는다.
- **`/pilot:pilot-review` 는 본 정지의 처방이 아니다** — 사이클 밖 코드 품질
  리뷰 (CODE REVIEW REPORT) 전용이며, 위 정지 사유 중 어느 것도 해소하지 않는다.
