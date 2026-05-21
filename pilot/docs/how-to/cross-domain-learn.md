# 외부 도메인 부트스트랩 (`/pilot:learn`)

!!! info "한 줄 요약"
    의존하는 *다른 도메인* 의 코드를 진입점부터 N 단계까지 따라가 `workspace/context/{domain}.md` (또는 `{domain}/` 폴더) 를 새로 만든다. `/pilot:analyze` 가 docs → features 라면, `/pilot:learn` 은 *코드 → context* 의 짝.

## 전제

- 활성 프로젝트가 있다.
- 만질 feature 가 현재 프로젝트 도메인 외의 코드를 *참조* 한다 (예: `coupon_service` feature 가 `auth_service` 를 호출).
- 진입점이 명확하다 — 단일 파일·폴더·클래스명.

## 절차

### 1. 진입점 지정해서 호출

```bash
/pilot:learn app/services/auth/
```

또는 단일 파일:

```bash
/pilot:learn app/services/external/coupon_request_service.rb
```

수행하는 일:

- 진입점 코드 정적 분석 — 메서드·라우트·상태값·검증 규칙 추출.
- 의존성을 N 단계 (기본 2) 까지 follow — 호출되는 다른 클래스·모듈도 같이 스캔.
- 코드 양·구조에 따라:
    - 단일 `{domain}.md` (가벼우면)
    - `{domain}/` 폴더 + 여러 `*.md` (복잡하면)
- `workspace/context/MANIFEST.md` 의 `## 도메인 분류` 표에 새 행 추가.

!!! warning "추측 금지"
    learn 은 *코드에 적힌 것만* file:line 인용으로 정리한다. 추론으로 채우지 않는다 — 비어 있는 항목은 사용자가 채우거나 별도 사이클로.

### 2. 결과 검토

```bash
ls workspace/context/
cat workspace/context/MANIFEST.md
```

도메인 진입 파일의 정확도를 훑고, 누락이 있으면 직접 보강 또는 추가 진입점으로 재호출.

### 3. 다음 사이클에 자동 반영

이제 planner 가 호출되면 `orchestrate-load.py` 가 MANIFEST 에서 본 feature 의 도메인을 매칭해 *새로 만든 컨텍스트 진입 파일* 을 자동 Read 한다. 별도 설정 불필요.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:learn`](../reference/skills/learn.md) · [도메인 분류 — MANIFEST.md](https://github.com/radiostart/claude-plugins/blob/main/pilot/skills/context/INDEX.md)
- :material-tools: How-to: 외부 도메인 컨텍스트가 준비됐으면 [프롬프트로 feature 단건 추가](create-feature.md) 또는 [기획서로 features 일괄 생성](analyze-docs.md) 으로 진입.
- :material-lightbulb-on: Explanation: pilot 의 도메인 컨텍스트 시스템 — [핵심 개념](../explanation/index.md).
