# How-to

작업별 레시피. *어떻게* 특정 일을 처리하는지에 답합니다. 모든 페이지는 같은 구조 — **한 줄 요약 → 전제 → 절차 → 다음 단계** — 라 인지 부하 없이 스캔 가능합니다.

개념 설명이 필요하면 [Explanation](../explanation/index.md), 정확한 값이 필요하면 [Reference](../reference/index.md) 로 가세요.

## 개발 워크플로우

<div class="grid cards" markdown>

-   :material-test-tube:{ .lg .middle } __[TDD 모드 활성화](tdd-mode.md)__

    ---

    Red→Green→Refactor 강제. 테스트 작성 누락을 막고 planner 가 실패 테스트를 먼저 만들도록.

-   :material-history:{ .lg .middle } __[Characterize 모드](characterize-mode.md)__

    ---

    레거시 코드의 *현재 동작* 을 테스트로 포착. 구현 변경 없이 안전망 먼저.

-   :material-shield-alert:{ .lg .middle } __[Critic 활용](critic-review.md)__

    ---

    `@pilot-planner-critic` 으로 plan 을 adversarial 검증 후 합의 표를 채우는 1.5-pass 흐름.

-   :material-target:{ .lg .middle } __[Focus 로 방향 조정](focus-direction.md)__

    ---

    메인 대화의 결정 (예: "소프트 딜리트 빼자") 을 다음 subagent 호출에 명시 전달.

</div>

## 컨텍스트 관리

<div class="grid cards" markdown>

-   :material-file-document-multiple:{ .lg .middle } __[기획서로 features 만들기](analyze-docs.md)__

    ---

    `docs/` 의 PM 기획서를 feature 단위로 분할해 `features/NN-*.md` 일괄 생성.

-   :material-file-plus:{ .lg .middle } __[프롬프트로 feature 단건 추가](create-feature.md)__

    ---

    docs 없이 한 줄 프롬프트로 단일 feature 명세를 만든다.

-   :material-magnify-scan:{ .lg .middle } __[외부 도메인 부트스트랩](cross-domain-learn.md)__

    ---

    의존하는 다른 도메인의 코드를 읽어 `context/` 의 도메인 문서를 새로 만든다.

-   :material-gavel:{ .lg .middle } __[도메인 규칙 작성](authoring-domain-rules.md)__

    ---

    learn 이 못 잡는 비즈니스 규칙을 직접 정리하고 MANIFEST 에 연결한다.

</div>

## 운영

<div class="grid cards" markdown>

-   :material-doctor:{ .lg .middle } __[Doctor 마이그레이션](doctor-migration.md)__

    ---

    `.agent-state.yml` schema v1.1 → v1.2 등 자동 마이그레이션 + 정합성 검사.

-   :material-cloud-sync:{ .lg .middle } __[Confluence 동기화](confluence-sync.md)__

    ---

    원격 Confluence 페이지를 `docs/` 로 fetch · 검색 · 일괄 가져오기.

-   :material-bell-ring:{ .lg .middle } __[Slack 알림 설정](slack-notify.md)__

    ---

    프로젝트별 채널로 작업 완료·승인 요청 이벤트 전송.

</div>

## 통합

<div class="grid cards" markdown>

-   :material-link-variant:{ .lg .middle } __[MOAI-ADK 연동](moai-adk-integration.md)__

    ---

    MOAI-ADK SPEC-First TDD 흐름과 pilot 의 3-phase 에이전트 사이클을 함께 사용.

</div>
