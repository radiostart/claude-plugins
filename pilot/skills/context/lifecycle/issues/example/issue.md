# TICKET-000 예제 이슈 — 소매 주문 상태 전환 오류

> **이 폴더는 예제용입니다. 실제 작업에 사용하지 않습니다.**

## 현상

- 소매 주문 상태가 `paid` → `ready_to_ship`으로 전환되지 않음
- 에러 메시지: `ActiveRecord::RecordInvalid: Validation failed: Status is invalid`
- 재현 경로: 관리자 > 소매 주문 상세 > 배송 준비 버튼 클릭

## 의심 영역

- `RetailOrder` 모델 상태 전환 validation
- `app/services/retail_order_ship_service.rb`

## 원인

_(분석 후 자동 기입)_

`RetailOrder#status` 의 AASM 전환 조건에 `prepaid?` guard가 추가되었으나, 선결제 여부를 판단하는 `prepaid?` 메서드가 `nil`을 반환하는 케이스가 누락됨.

## 조치

_(수정 완료 후 자동 기입)_

`RetailOrder#prepaid?` 메서드에 nil guard 추가:

```ruby
def prepaid?
  prepay_amount.to_i > 0
end
```

## 재발 방지

_(필요 시 자동 기입)_

- `prepaid?` 류 boolean 메서드는 nil-safe하게 작성한다 (`to_i`, `present?` 등 활용)
