# python-sample

> **FIXTURE — 실행 금지**
>
> 이 코드베이스는 `/pilot:learn`·`/pilot:project`·`/pilot:analyze` 회귀 픽스처 입력용 토이 코드입니다.
> 실제 실행을 목적으로 작성되지 않았습니다.
> - 외부 라이브러리 의존성 없음 (dataclass·typing·enum 만 사용)
> - `pip install` 없이 구문 파싱 가능
> - FastAPI import 는 try/except guard 로 보호

## 구조

```
python-sample/
├── main.py              # 진입점 (FastAPI app 팩토리)
├── routes.py            # HTTP 라우트 (GET/POST 6 개)
├── models/
│   ├── user.py          # User·UserProfile dataclass
│   └── order.py         # Order·OrderItem·OrderStatus
├── services/
│   ├── auth.py          # AuthService (사용자 인증·조회)
│   └── checkout.py      # CheckoutService (주문·결제·취소)
├── helpers.py           # 유틸리티 (to_dict·paginate·format_price)
└── docs/
    └── sample-spec.md   # 토이 기획서 (analyze 5-2 입력)
```

## 회귀 테스트 역할

| 스킬 | 입력 | expected 경로 |
| ---- | ---- | -------------- |
| `/pilot:learn main.py` | 이 폴더 | `learn/expected/` |
| `/pilot:project python-sample-demo` | — | `project/expected/` |
| `/pilot:analyze` | `docs/sample-spec.md` | `analyze/expected/` |
