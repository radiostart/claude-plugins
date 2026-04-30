# secondary_domain — cross-domain 테스트 픽스처

> 이 폴더는 `python-sample` 도메인이 외부 도메인 (`secondary_domain`) 에 의존하는
> cross-domain reference 시나리오를 검증하기 위한 회귀 픽스처입니다.
>
> **실제 애플리케이션 코드가 아닙니다.**

## 목적

- `services/checkout.py` 가 `secondary_domain.auth_service.AuthService` 를 import → cross-domain detect 발동
- `/pilot:learn python-sample/services/` 실행 시 MANIFEST 의 `## 외부 도메인 reference` 섹션에 `secondary_domain` 행 자동 추가 검증
- 후속 `/pilot:learn secondary-domain/` 실행 시 해당 행 자동 제거 (idempotency) 검증

## 파일

| 파일 | 설명 |
| ---- | ---- |
| `auth_service.py` | 외부 도메인 인증 서비스 스텁 |
| `user_model.py` | 외부 도메인 사용자 모델 스텁 |
