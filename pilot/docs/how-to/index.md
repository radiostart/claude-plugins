# How-to

작업별 recipe를 제공합니다. 특정 작업을 수행하는 세부 절차와 팁을 담고 있습니다. 모든 문서는 일관된 구조(**한 줄 요약 → 전제 조건 → 작업 절차 → 다음 단계**)를 따르고 있어 인지적 부하 없이 필요한 정보를 빠르게 스캔할 수 있습니다.

동작 원리와 개념에 대한 이해가 필요하다면 [Explanation](../explanation/index.md), 구체적인 상세 스펙이 궁금하다면 [Reference](../reference/index.md)를 참고하세요.

## 개발 워크플로우

<div class="grid cards" markdown>

-   :material-test-tube:{ .lg .middle } __[TDD 모드 활성화](tdd-mode.md)__

    ---

    Red→Green→Refactor 개발 cycle을 강제하여 test 누락을 방지하고, planner가 실패하는 test를 먼저 정의하도록 유도합니다.

-   :material-history:{ .lg .middle } __[Characterize 모드](characterize-mode.md)__

    ---

    레거시 code의 *현재 동작 방식*을 test 코드로 작성하여 안전망을 확보합니다. 실제 구현 변경을 수반하지 않는 안전한 검증 방식입니다.

-   :material-shield-alert:{ .lg .middle } __[Critic 활용](critic-review.md)__

    ---

    `@pilot-planner-critic`을 통해 plan을 비판적 관점에서 검증하고 피드백 합의 표를 채우는 1.5-pass review flow를 다룹니다.

-   :material-code-tags-check:{ .lg .middle } __[코드 리뷰 (PR 전)](code-review.md)__

    ---

    `@pilot-code-review`가 git diff를 분석해 코드 품질을 검토하고, 결함 발견 시 재진입할 최적의 routing 단계를 가이드합니다.

-   :material-target:{ .lg .middle } __[Focus 로 방향 조정](focus-direction.md)__

    ---

    메인 대화 도중 이루어진 의사결정(예: '소프트 딜리트는 제외')을 다음 subagent 호출 시 명시적으로 주입하고 추적합니다.

-   :material-help-circle:{ .lg .middle } __[Open Questions 게이트](open-questions-gate.md)__

    ---

    미해결 전제가 남은 채로 구현이 시작되는 것을 차단합니다. 카테고리별 처리 방법과 plan 마커 작성 규칙을 다룹니다.

-   :material-comment-question:{ .lg .middle } __[구현 질의](ask-code.md)__

    ---

    구현된 기능의 동작·위치를 도메인 컨텍스트 → 소스 순으로 탐색해 `file:line` 인용으로 답하는 읽기 전용 질의입니다.

</div>

## 컨텍스트 관리

<div class="grid cards" markdown>

-   :material-file-document-multiple:{ .lg .middle } __[기획서로 features 만들기](analyze-docs.md)__

    ---

    `docs/` 디렉토리에 작성된 PM 기획서를 세부 feature 단위로 분할하여 `features/NN-*.md` 형식의 명세 파일들을 일괄 생성합니다.

-   :material-file-plus:{ .lg .middle } __[프롬프트로 feature 단건 추가](create-feature.md)__

    ---

    별도의 문서 없이 한 줄의 prompt 지시만을 바탕으로 단일 feature 명세를 생성합니다.

-   :material-magnify-scan:{ .lg .middle } __[외부 도메인 연동](cross-domain-learn.md)__

    ---

    의존 관계에 있는 다른 도메인의 구현 코드를 분석하여 `context/` 경로에 새로운 도메인 문서를 구성합니다.

-   :material-sync:{ .lg .middle } __[도메인 지식 환류](knowledge-sync.md)__

    ---

    cycle 이 만든 신규 지식(라우트·enum·외부 의존 등)을 evaluator 가 감지해 보고하고, 승인 후 `context/` 문서에 되돌려 기록합니다.

-   :material-pencil:{ .lg .middle } __[도메인 암묵지 기록](tacit-domain-knowledge.md)__

    ---

    자동 분석 도구(learn)가 파악하기 어려운 구현 의도나 비즈니스 context를 에이전트와의 대화를 통해 발굴하고 문서화합니다.

-   :material-gavel:{ .lg .middle } __[도메인 규칙 작성](authoring-domain-rules.md)__

    ---

    자동 분석 도구(learn)가 놓치기 쉬운 비즈니스 규칙을 사용자가 직접 기술하고 `MANIFEST.md`에 매핑합니다.

-   :material-file-cog:{ .lg .middle } __[워크스페이스 설정](workspace-config.md)__

    ---

    `config.md` 설정 파일에 필수 정보(언어, tool 기본값, ignore 대상, hook 상수 등)를 정의합니다.

-   :material-code-braces:{ .lg .middle } __[언어 컨벤션 공급](language-conventions.md)__

    ---

    사용 중인 언어 및 framework의 개발 규칙과 검증 케이스를 각각 `conventions_doc`과 `conventions_evals` 영역에 정의하여 반영합니다.

</div>

## 운영

<div class="grid cards" markdown>

-   :material-fire-extinguisher:{ .lg .middle } __[운영 이슈 단건 처리](issue-cycle.md)__

    ---

    누적 컨텍스트 기반으로 운영 이슈 1건을 진단·수정합니다. 코드 수정 시 project 와 동일한 4-에이전트 사이클을 이슈 단위로 사용합니다.

-   :material-bug-check:{ .lg .middle } __[QA 결함 처리](qa-cycle.md)__

    ---

    Jira 결함 티켓 1건을 qa phase 사이클로 처리합니다. features 읽기 전용 잠금·회귀영향 평가 게이트·qa/ 산출물 규약을 다룹니다.

-   :material-swap-horizontal:{ .lg .middle } __[작업 전환·재발견](switch-work.md)__

    ---

    최근 진행한 project·issue 목록을 조회하고 전환합니다. 하다 만 이슈가 `미완` 으로 표시되어 재발견됩니다.

-   :material-doctor:{ .lg .middle } __[Doctor 마이그레이션](doctor-migration.md)__

    ---

    `.agent-state.yml` 설정 파일의 schema 버전 자동 migration(예: v1.1 → v1.2) 및 구조 정합성을 검사합니다.

-   :material-cloud-sync:{ .lg .middle } __[Confluence 동기화](confluence-sync.md)__

    ---

    원격 Confluence 페이지를 조회 및 검색하여 `docs/` 디렉토리로 동기화(fetch)하고 다운로드합니다.

-   :material-bell-ring:{ .lg .middle } __[Slack 알림 설정](slack-notify.md)__

    ---

    project 단위로 설정된 Slack 채널에 작업 완료 및 승인 요청 알림 이벤트를 전송합니다.

-   :material-source-pull:{ .lg .middle } __[PR 컨벤션 설정](pr-conventions.md)__

    ---

    `workspace/context/pr.md` 설정을 활용하여 PR(Pull Request) 본문 작성 규칙을 소속 팀의 규칙에 맞춰 커스터마이징합니다.

</div>
