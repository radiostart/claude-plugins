# 외부 도메인 연동 (`/pilot:learn`)

!!! info "한 줄 요약"
    의존성이 있는 다른 도메인의 코드를 진입점부터 N단계까지 추적 분석하여 `workspace/context/{domain}.md` 파일(혹은 `{domain}/` 폴더)을 생성합니다. `/pilot:analyze` 가 기획서(docs)를 기능(features)으로 분할하는 도구라면, `/pilot:learn` 은 코드를 컨텍스트(context)로 변환하는 도구입니다.

## 전제 조건

- 활성화된 project가 존재해야 합니다.
- 다루려는 feature가 현재 프로젝트 도메인 외부의 코드를 참조하고 있어야 합니다 (예: `coupon_service` 구현을 위해 `auth_service` 코드를 참조해야 하는 경우).
- 분석을 시작할 명확한 진입점(특정 파일, 폴더, 클래스명 등)을 알고 있어야 합니다.

## 작업 절차

### 1. 진입점을 지정하여 learn 실행

```bash
/pilot:learn app/services/auth/
```

또는 단일 파일을 지정할 수도 있습니다:

```bash
/pilot:learn app/services/external/coupon_request_service.rb
```

이 명령은 다음 작업을 수행합니다:

- 진입점 코드에 대한 정적 분석을 실행하여 메소드, 라우트, 상태값, 검증 규칙 등을 추출합니다.
- 지정된 N단계(기본값 2단계)까지 의존성 코드를 추적하여 호출되는 연계 클래스 및 모듈을 스캔합니다.
- 코드의 규모와 구조적 복잡도에 따라 컨텍스트를 분할 저장합니다:
    - 단일 `{domain}.md` 파일 (규모가 작고 단순한 경우)
    - `{domain}/` 디렉터리 및 다중 `*.md` 파일 (복잡도가 높은 경우)
- `workspace/context/MANIFEST.md` 의 `## 도메인 분류` 표에 새 도메인 정보를 추가 등록합니다.

!!! warning "추측 배제 — 비즈니스 규칙 미추출"
    `learn` 은 코드로 명시된 팩트 정보만을 `file:line` 인용 형태로 수집합니다. AI가 추론을 통해 주관적인 판단을 내리지 않습니다. 따라서 환불의 성격이나 상태 전이의 비즈니스적 맥락 같은 **비즈니스 정책 및 규칙**은 자동으로 채워지지 않으므로, [도메인 규칙 작성](authoring-domain-rules.md) 가이드를 참고하여 직접 보완해야 합니다.

### 2. 생성된 컨텍스트 검토

```bash
ls workspace/context/
cat workspace/context/MANIFEST.md
```

수출된 도메인 진입점의 정보가 정확한지 훑어봅니다. 누락된 부분이 발견되면 직접 보강하거나, 추가 진입점을 지정하여 learn 명령을 재실행합니다.

### 3. 다음 cycle 진행 시 자동 연동

이후 planner 가 호출되면 `orchestrate-load.py` 가 `MANIFEST.md` 설정을 판별하여, 작업 대상 feature에 속하는 도메인의 **컨텍스트 진입 파일을 에이전트에게 자동으로 로드**합니다. 사용자가 매번 컨텍스트 파일을 주입할 필요가 없습니다.

## 다음 단계

- :material-book-open-variant: Reference: [`/pilot:learn`](../reference/skills/learn.md) · [도메인 분류 — MANIFEST.md](https://github.com/radiostart/claude-plugins/blob/main/pilot/skills/context/INDEX.md)
- :material-pencil: How-to: learn 명령은 구조적 사실만 기계적으로 정리합니다. 코드에 숨겨진 기획 의도나 비즈니스 맥락은 [도메인 암묵지 기록](tacit-domain-knowledge.md) 가이드를 참고하여 명문화하십시오.
- :material-tools: How-to: 연관 도메인 컨텍스트 준비가 끝났다면 [feature 단건 추가](create-feature.md) 또는 [기획서 기반 feature 일괄 생성](analyze-docs.md)으로 넘어가 실제 구현 작업을 착수하십시오.
- :material-lightbulb-on: Explanation: pilot의 도메인 컨텍스트 시스템에 대한 상세 내용은 [핵심 개념](../explanation/index.md)을 참고하십시오.
