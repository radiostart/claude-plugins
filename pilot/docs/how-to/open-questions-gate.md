# Open Questions 게이트 — 미해결 전제 차단

!!! info "한 줄 요약"
    feature 명세의 `## Open Questions` 에 미해결 항목(`- [ ]`)이 남아 있으면, plan 에 처리 마커를 명시하기 전까지 `plan-validate` 가 cycle 진행을 **차단(fail-closed)** 합니다. 특히 비즈니스 결정 영역은 에이전트가 임의로 결정할 수 없습니다.

## 전제 조건

- `/pilot:analyze` 또는 `/pilot:create-feature` 로 생성된 feature 명세에는 `## Open Questions` 4 카테고리가 항상 포함됩니다. 이 섹션이 없는 명세(직접 작성한 파일 등)는 게이트가 `skip` 됩니다.
- 게이트는 planner 가 plan 을 저장한 직후, generator 가 plan 을 읽기 직전 **두 지점에서 같은 도구로** 검사됩니다. 두 단계의 판정이 어긋날 수 없습니다.

## 왜 차단하는가

미해결 전제를 "합리적 추정" 으로 채우면 그 전제가 planner → generator → evaluator 전체를 오염시킵니다. 잘못된 가정 위에 쌓인 구현은 검토 단계에서도 걸러지지 않습니다 — 세 에이전트가 같은 잘못된 전제를 공유하기 때문입니다. 그래서 **모르는 것은 모른다고 표시하고 진행 여부를 사람이 정하도록** 강제합니다.

## 작업 절차

### 1. 차단 신호 확인

planner 또는 generator 단계에서 다음과 같이 보고됩니다:

```
(b) 미해결 1건 — plan 에 처리 마커 없음
```

`plan-validate` 출력 JSON 의 `oq` 필드에 미해결 카테고리와 항목이 담깁니다.

### 2. 카테고리별로 처리 방법 선택

카테고리마다 허용되는 처리가 다릅니다.

| 카테고리 | 원칙 | plan 에 쓸 수 있는 마커 |
|---|---|---|
| **(a)** 같은 도메인 추가 read 필요 | 해당 문서를 추가로 읽어 해결 | `범위 제외` 또는 `추정 구현` |
| **(b)** cross-domain 산출물 부재 | `/pilot:learn` 으로 해당 도메인을 먼저 학습하도록 권고 | `추정 구현` (사용자가 "그냥 진행" 을 명시한 경우) 또는 `범위 제외` |
| **(c)** 외부 시스템 spec 부재 | spec 확보 여부를 사용자에게 질의 | `범위 제외` (기본) 또는 `추정 구현` |
| **(d)** 비즈니스 결정 영역 | **반드시 사용자에게 질의**해 답을 받는다 | `범위 제외` 만 — **`추정 구현` 불인정** |

가장 좋은 해결은 마커를 다는 것이 아니라 **항목 자체를 해소**하는 것입니다. 답을 얻었다면 feature 명세에서 해당 줄을 이렇게 바꿉니다:

```markdown
- [x] 부분 환불 시 수수료 부담 주체 → 결정: 판매자 부담 (2026-08-01 확정)
```

### 3. 해소가 안 되면 plan 에 마커 명시

plan 본문에 카테고리 키와 마커 어휘를 **같은 줄에** 적습니다:

```markdown
### Open Questions 처리

- (b) 결제 도메인 산출물 부재: 추정 구현 — 사용자 "그냥 진행" 승인
- (c) PG API spec 부재: 구현 범위에서 제외 — 인터페이스부 TODO 마킹
```

!!! warning "코드블록 안의 마커는 인정되지 않습니다"
    ` ``` ` 펜스 안에 적힌 마커는 파서가 무시합니다. 예시가 아니라 실제 처리 기록이라면 펜스 밖 본문에 적으세요.

### 4. `추정 구현` 으로 진행했다면 코드에 TODO 를 남긴다

generator 는 해당 인터페이스에 다음 주석을 답니다 (언어별 주석 문법 적용):

```
# TODO: Open Questions (b)/(c) 미해결 — 확보 후 재구현 필요
```

evaluator 는 이 주석이 없으면 Minor 이슈로 보고합니다.

### 5. 재검증

planner 를 재호출하면 매트릭스대로 항목을 해결하거나 마커를 보완하고, `plan-validate` 가 다시 통과하면 generator 로 진행합니다. **게이트 실패를 발견한 에이전트가 planner 를 직접 호출하지는 않습니다** — 사용자에게 보고하고 선택을 받습니다.

## evaluator 의 판정

VERIFICATION REPORT 의 `open_questions` gate 로 보고됩니다.

- `pass` — 미해결 항목이 없거나 모두 마커로 처리됨
- `fail` — 마커 없는 미해결 항목이 있거나, 구현이 (d) 를 임의로 결정함 (Major 이슈로 반려)
- `skip` — feature 파일이 없거나 `## Open Questions` 섹션이 없음

## 다음 단계

- :material-file-plus: How-to: [프롬프트로 feature 단건 추가](create-feature.md) — 명세 생성 시점의 조건부 인터뷰가 항목 일부를 미리 해소합니다.
- :material-magnify-scan: How-to: [외부 도메인 연동](cross-domain-learn.md) — (b) 카테고리의 근본 해결책입니다.
- :material-shield-alert: How-to: [Critic 활용](critic-review.md) — critic 이 plan 의 전제를 함께 검증합니다.
