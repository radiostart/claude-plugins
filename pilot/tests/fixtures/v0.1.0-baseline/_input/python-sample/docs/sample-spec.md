# python-sample 기획서

> FIXTURE NOTE: 이 파일은 /pilot:analyze 회귀 테스트 입력용 토이 기획서입니다.

## 주문 생성 기능

사용자가 상품을 선택한 뒤 주문을 생성한다.

- **조건**: 로그인한 사용자만 주문 가능
- **트리거**: `POST /orders` 호출
- **기대결과**: 새 Order (status=PENDING) 반환

### 비즈니스 규칙

- 주문 항목이 1 개 이상이어야 한다
- 재고 부족 시 주문 생성 불가

## 결제 처리 기능

주문에 대한 결제를 처리하여 상태를 PAID 로 전환한다.

- **조건**: 주문이 PENDING 상태여야 한다
- **트리거**: `POST /orders/{id}/pay` 호출
- **기대결과**: Order 의 status 가 PAID 로 변경됨

### 상태 전환

| 전환 전 | 전환 후 | 조건 | 처리 |
| ------- | ------- | ---- | ---- |
| PENDING | PAID | 정상 결제 | status 갱신 |
| PAID | - | 이미 결제 | ValueError |
| CANCELLED | - | 취소된 주문 | ValueError |
