# Planner

<!-- [analyze-managed] -->
## 기능별 사전 확인 사항

### 결제 처리 (features/01-payment.md)

- 조건: 회원 결제 단계 진입
- 트리거: 결제 버튼 클릭
- 기대결과: 주문 결제완료 상태 전환

### 환불 처리 (features/02-refund.md)

- 조건: 결제완료 주문 보유
- 트리거: 환불 신청 + 관리자 승인
- 기대결과: refund 레코드 생성 + 상태 전환

## 플래닝 프로세스

사용자 수동 편집 영역 — 추가 가이드 작성.

- 영향 범위 분석은 controller·service·model 3 단계 추적
- 외부 의존 (PG·이메일) 은 mock 우선

## 주의사항

- 기존 `Order#paid?` 메서드 시그니처 변경 금지
