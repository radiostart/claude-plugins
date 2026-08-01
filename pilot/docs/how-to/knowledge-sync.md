# 도메인 지식 환류 — cycle 이 만든 지식 되돌리기

!!! info "한 줄 요약"
    cycle 이 끝날 때 evaluator 가 "이번 변경이 도메인 문서에 반영할 지식을 만들었는지" 판정해 보고하고, 사용자가 승인하면 메인 대화가 `workspace/context/` 에 기록합니다. evaluator 는 **감지·보고까지만** 하고 직접 문서를 고치지 않습니다.

## 전제 조건

- `.agent-state.yml` 의 `domain` 이 설정되어 있어야 합니다 (`null` 이면 판정 기준 도메인이 없어 `skip`).
- 도메인 문서가 아직 없어도 됩니다 — 그 경우는 skip 이 아니라 `detected` 로 잡히고 `/pilot:learn` 신규 작성을 권고합니다.

## 왜 필요한가

[drift-protocol](../explanation/drift-protocol.md) 은 *기존 문서가 코드와 다른 것*을 우연히 발견했을 때의 절차입니다. 반대 방향, 즉 **이번 cycle 이 새로 만든 지식이 문서에 안 담기는 누락**은 아무도 눈치채지 못한 채 쌓입니다. 다음 planner 가 옛 문서를 근거로 잘못된 계획을 세우고 나서야 드러나죠. 이 절차는 그 누락을 cycle 종료 시점에 체계적으로 점검합니다.

## 작업 절차

### 1. evaluator REPORT 에서 판정 확인

`metrics` 블록에 기록됩니다. **gate 가 아니므로** `READY` 와 `detected` 는 정상적으로 공존합니다 — 지식 환류가 남았다고 해서 cycle 이 반려되지는 않습니다.

```
- metrics:
  - domain_impact: detected — enum: 발송상태 CANCELED 추가 → retail.md; 외부 의존: 재고 API 호출 신설 → boundaries/retail--inventory.md
```

| 값 | 의미 |
|---|---|
| `detected` | 라우트·모델·enum·외부 의존·비즈니스 용어 추가/변경, 또는 이미 문서화된 항목의 동작 변경 |
| `none` | 내부 리팩터·버그 수정·테스트만 변경·스타일 (공개 표면 불변) |
| `skip` | `domain: null` |

!!! tip "`none` 판정의 기준"
    "이 변경을 모르는 다음 planner 가 잘못된 계획을 세울 수 있는가" — 아니라면 `none` 입니다. 모든 diff 를 문서화 대상으로 삼지 않습니다.

### 2. 안내 블록에 답하기

`status: READY` 이면서 `detected` 일 때만 evaluator 가 REPORT 직후 승인 요청을 띄웁니다:

```
## 도메인 지식 환류 제안
이번 변경이 도메인 지식 문서에 반영할 항목을 만들었습니다:
| # | 유형 | 내용 | 대상 문서 |
|---|---|---|---|
| 1 | enum | 발송상태 CANCELED 추가 | retail.md |
기록할까요? 승인 시 항목별 before/after 미리 보기 후 반영합니다.
```

`NOT_READY` 면 이 블록이 뜨지 않습니다 — 재작업으로 판정이 뒤집힐 수 있으므로 다음 `READY` 재평가로 미룹니다. 판정은 diff 기준이라 이때 놓쳐도 소실되지 않습니다.

### 3. 승인 후 기록 (메인 대화)

승인하면 메인 대화가 항목별 before/after 를 제시하고 최종 확인을 받은 뒤 Edit 으로 반영합니다.

- 대상은 MANIFEST 가 가리키는 도메인 진입 파일과 그 하위 파일입니다.
- 파일 크기 정책을 따릅니다 — 진입/index 100줄, 본문 200줄 이내.
- 기록 문안에 feature 번호·티켓 키 같은 **프로젝트 생애주기 토큰을 남기지 않습니다.** 공유 context 는 프로젝트가 끝나도 살아남기 때문에, 이번 cycle 에서 발견한 사실이라도 도메인 표현으로 적습니다.

!!! warning "항목이 5건 이상이거나 섹션 구조를 바꿔야 하면"
    개별 Edit 대신 `/pilot:learn {진입점} --force` 재실행이 안전합니다. learn 산출 문서는 diff 모드 없이 덮어쓰기로 갱신되도록 설계돼 있습니다. 사용자가 직접 쓴 `rules/` 는 learn 이 건드리지 않으므로 그대로 보존됩니다.

### 4. 기본 브랜치에 조기 합류

`workspace/context/` 는 git 으로 추적되는 **공유 자산**입니다. 기록 커밋을 feature 브랜치에만 남겨두면 다른 브랜치·체크아웃에서는 그 지식이 보이지 않습니다. context 변경은 feature 머지를 기다리지 말고 별도 커밋으로 분리해 기본 브랜치에 먼저 올리세요.

## 기록하지 않는 것

`rules/{domain}.md` 같은 사용자 커스텀 layer 는 환류 대상이 아닙니다 — 정책은 코드에서 추론할 수 없기 때문입니다. 구현과 규칙이 어긋난 것을 발견했다면 그건 [drift-protocol](../explanation/drift-protocol.md) 경로입니다.

승인을 거부해도 됩니다. 기록하지 않은 지식은 이후 cycle 에서 drift 로 다시 발견되며, 이는 의도된 안전망입니다.

## 다음 단계

- :material-lightbulb-on: Explanation: [Drift 프로토콜](../explanation/drift-protocol.md) — 반대 방향(기존 문서가 실제와 다름) 절차
- :material-magnify-scan: How-to: [외부 도메인 연동](cross-domain-learn.md) — 외부 의존이 감지됐을 때의 경계 문서 작성
- :material-pencil: How-to: [도메인 암묵지 기록](tacit-domain-knowledge.md) — 코드에서 추출되지 않는 지식을 대화로 발굴
