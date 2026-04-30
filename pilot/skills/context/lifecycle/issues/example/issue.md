# TICKET-000 예제 이슈 — 상태 전환 검증 누락

> **이 폴더는 예제용입니다. 실제 작업에 사용하지 않습니다.**
>
> 본 예제는 한 가지 컨텍스트(상태머신 + 검증 누락)일 뿐이며, 도메인·언어·프레임워크는 사용자 환경에 맞춰 자유롭게 변경한다.

## 현상

- `<Entity>` 의 상태가 `<state_a>` → `<state_b>` 로 전환되지 않음
- 에러 메시지: `Validation failed: Status is invalid`
- 재현 경로: 어드민 화면 > `<Entity>` 상세 > 다음 단계 버튼 클릭

## 의심 영역

- `<Entity>` 모델의 상태 전환 validation
- `{source_root}/services/<entity>_<action>_service.{ext}`

## 원인

_(분석 후 자동 기입)_

`<Entity>#status` 의 상태 전환 조건에 `<flag>?` guard 가 추가되었으나, 해당 조건을 판단하는 `<flag>?` 메서드가 `nil` 을 반환하는 케이스가 누락됨.

## 조치

_(수정 완료 후 자동 기입)_

`<Entity>#<flag>?` 메서드에 nil guard 추가 (언어별 idiom 적용):

```
def <flag>?
  <amount_field>.to_i > 0
end
```

## 재발 방지

_(필요 시 자동 기입)_

- `<flag>?` 류 boolean 메서드는 nil-safe 하게 작성한다.
