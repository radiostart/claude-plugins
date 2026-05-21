# #04 환불 처리 — Plan

> mode: standard

## 구현 계획

### 변경 파일

- [ ] `app/services/refund_service.rb` — 환불 비즈니스 로직 진입점
- [ ] `app/controllers/admin/refunds_controller.rb` — 어드민 환불 endpoint
- [ ] `app/models/refund.rb` — 환불 상태 모델
- [ ] `db/migrate/20260504_create_refunds.rb` — refunds 테이블 마이그레이션
- [ ] `spec/services/refund_service_spec.rb` — 서비스 spec

### 구현 순서

1. 마이그레이션 생성 (refunds 테이블 스키마)
2. Refund 모델 작성 (validation 포함)
3. RefundService 작성 (Order 와 연관)
4. Admin::RefundsController 작성 (POST /admin/refunds)
