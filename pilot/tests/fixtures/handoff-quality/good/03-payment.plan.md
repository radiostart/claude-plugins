# #03 결제 처리 — Plan

> mode: tdd
> source: features/03-payment.md

## 구현 계획

### 변경 파일

- [ ] `app/services/payment_service.rb` — PG 호출 메서드 신설
- [ ] `app/models/order.rb` — 결제완료 상태 전환 hook 추가
- [ ] `spec/services/payment_service_spec.rb` — 신규 spec 파일
- [ ] `spec/models/order_spec.rb` — 상태 전환 케이스 추가

### 스텝 목록

1. **[스텝 1]** PaymentService.charge 호출 → PG API 응답 매핑 검증

   - 테스트 대상: `PaymentService#charge`
   - 검증할 행동: 결제 요청 인자가 PG client 의 charge 메서드로 그대로 전달되고, 응답 객체가 도메인 객체로 변환되어 반환된다
   - 기대 실패 유형: NoMethodError (charge 미구현)

2. **[스텝 2]** Order 의 결제완료 상태 전환

   - spec 대상: `Order#mark_paid`
   - 검증할 행동: Order.state 가 'pending' 에서 'paid' 로 전환되고 paid_at 타임스탬프가 기록된다
   - 기대 실패 유형: NoMethodError (mark_paid 미구현)
