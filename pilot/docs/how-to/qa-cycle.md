# QA 결함 처리 (qa)

기능 개발이 끝난 project 의 QA 단계에서 Jira 결함 티켓 1건을 분석·수정 사이클로 처리합니다. 다건 추적·잔여 현황은 Jira UI 가 SSOT — 로컬 보드뷰를 만들지 않습니다.

## 전제 조건

- 활성 project 가 있어야 합니다 (`/pilot:project {PROJECT}`). project 컨텍스트가 필요 없는 단발 운영 이슈는 [`/pilot:issue`](issue-cycle.md) 를 사용합니다.
- Jira 연동 환경변수 — `.env` 또는 `workspace/.env` 에 기록:

```env
ATLASSIAN_BASE_URL=https://your-domain.atlassian.net
ATLASSIAN_EMAIL=you@example.com
ATLASSIAN_TOKEN={API 토큰}
```

- (선택) `workspace/context/config.md` § 설정의 `jira_qa_project_key` — 키 화이트리스트. prefix 불일치 시 확인 질의가 나옵니다.

## 작업 절차

### 1. 결함 티켓 진입

```
/pilot:qa QAPRJ-1234
```

- development phase 였다면 **qa phase 로 자동 전환**됩니다 (`.agent-state.yml` 의 `phase: qa` — STATE.md 는 불변).
- `tools/jira.py fetch` 가 티켓 본문을 가져와 `qa/{KEY}.md` 를 prefill 하고, 작업 브랜치 `fix/{KEY}` 를 만듭니다 (재작업이면 `fix/{KEY}-2` 식 자동 회피).
- 같은 티켓 재진입은 기존 `qa/{KEY}.md` 를 보존하고 새 회차 (`.r{N}`) 로 이어갑니다.

### 2. 수정 사이클

`@pilot-planner` 호출로 시작합니다 — 에이전트들이 qa phase 를 인식해 **결함 수정 모드**로 동작합니다:

- planner: 최소 변경 원칙 + plan 에 `결함 함수: {file}#{symbol}` 1줄과 **회귀영향 후보** 절 필수. 산출물은 `qa/{KEY}.plan[.r{N}].md`.
- generator: plan 의 결함 함수 한 곳 안에서만 수정. `qa/{KEY}.md` 의 `## 조치` 기입.
- evaluator: **회귀영향 평가** (후보별 3분류 판정) + 회귀 재현 테스트 직접 실행 (`test_run` skip 금지). REPORT 는 `qa/{KEY}.eval[.r{N}].md`.

qa phase 동안 `features/**/*.md` 는 **읽기 전용**입니다 (protect-managed 훅이 차단) — features 수정이 필요하면 development 복귀 후 별도 사이클로 진행합니다.

### 3. 회신·복귀

- Jira 회신: `python3 ${CLAUDE_PLUGIN_ROOT}/tools/jira.py comment {KEY} "..."` — 회신 이력의 SSOT 는 Jira 코멘트입니다 (`qa/{KEY}.md` 에 회신 섹션을 두지 않음).
- development 복귀: `/pilot:qa off` 또는 `/pilot:project {PROJECT} --qa off` (`qa_started_at`·`qa/` 폴더는 보존).

## 다음 단계

- qa/ 산출물 명명 규약·재작업 회차 규칙: Reference → Skills → qa
- phase 정합성 점검: [Doctor 진단·마이그레이션](doctor-migration.md)
