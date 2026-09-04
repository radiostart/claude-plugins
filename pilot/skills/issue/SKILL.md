---
name: issue
description: >-
  운영 이슈 처리 모드 — `workspace/issues/{이슈명}/` 를 생성·로드해 버그
  대응·장애 분석·핫픽스 등 단발성 문제 1건을 해결한다. 필요 시 project 와
  동일한 4-에이전트 사이클을 issue 단위로 사용. 지속 기능 개발은 `/pilot:project`.
---

운영 이슈 처리 모드를 활성화한다.

**정의** — issue 는 **기존에 누적된 컨텍스트를 기반으로 특정 문제를 해결하는 단건 처리** 기능이다:

1. **누적 컨텍스트 기반**: projects/ 산출물과는 독립 — "프로젝트 컨텍스트 미참조" 는 projects/ 산출물 (project.md·features/·prompts/) 한정이며, 누적 컨텍스트 (`workspace/context/` 도메인 지식·과거 `issues/` 이력·메모리 P0) 는 진단의 기반이다.
2. **project 유사 구조의 단건 처리**: 이슈 폴더는 `issue.md` 1 건의 명세 + 사이클 파생 산출물로 구성된다 — feature N 건 대신 문제 1 건. 파생 산출물 명명은 [GUIDE.md](../context/lifecycle/issues/GUIDE.md) § 이슈 폴더 구조 를 따른다.
3. **기본 사이클 유지**: 코드 수정이 필요한 이슈는 `@pilot-planner → @pilot-planner-critic → @pilot-generator → @pilot-evaluator` 사이클을 그대로 사용한다 (orchestrate-load 가 STATE.md 의 `issue` 행을 인식해 issues/ 기반으로 로드 — `work_mode` 계약). 조사·회신만으로 끝나는 이슈는 사이클 없이 직접 처리해도 된다.

대상 이슈: $ARGUMENTS

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P-1, P0** 수행.

- P-1: 진행 보드 선로딩 (다단계 스킬).
- P0: 인자의 이슈명·키워드로 MEMORY.md 색인에서 관련 메모를 직접 선별해 Read 하여 유사 이슈 이력 반영.

## 수행 절차

1. **bare 진입** — `$ARGUMENTS` 가 비어있으면: "이슈명 없이 진입합니다 — 폴더·기록이 남지 않고 사이클 (`@pilot-*`) 도 비지원입니다. 기록과 사이클이 필요하면 `/pilot:issue {이슈명}` 으로 재진입, 진행하던 이슈를 찾으려면 `/pilot:switch`." 1 줄 고지 후 [GUIDE.md](../context/lifecycle/issues/GUIDE.md) 를 로드하고, 2·3 단계를 건너뛰어 (검색·slug 불가) 4 단계부터 진행한다 (5 단계는 질의 없이 MANIFEST 까지만, 6 단계 안내에서 사이클 항목 제외).
2. **유사 이슈 검색** — 폴더명과 제목을 **함께** 훑어 유사 이슈를 찾는다 (과거 원인·조치가 이번 진단의 출발점). 폴더명은 영문 slug 라 한글 키워드는 제목이 받는다:

   ```bash
   ls workspace/issues/ 2>/dev/null
   grep -H "^# " workspace/issues/*/issue.md 2>/dev/null
   ```

   - 유사 폴더 발견 → 사용자에게 제시: "유사 이슈가 있습니다: {목록}. 해당 이슈를 재개할까요, 새 이슈로 진행할까요?" (목록은 `{slug} — {제목}` 형식)
   - H1 제목이 없는 기존 이슈는 폴더명으로만 매칭한다 — 소급 기입하지 않는다.
   - 없으면 다음 단계로.
3. **이슈 slug 결정 + 폴더 생성/로드** — 폴더명 (= 이슈명) 은 `$ARGUMENTS` 원문이 아니라 원문에서 도출한 **영문 kebab slug** 다. 원문은 버리지 않는다 — 제목·현상으로 보존한다 ([GUIDE.md](../context/lifecycle/issues/GUIDE.md) § 폴더명 (slug) 규약 이 명명 SSOT).
   - **slug 도출** — 원문의 핵심 키워드를 소문자 영문 kebab-case 로 축약한다 (`[a-z0-9-]` 만, 40 자 이내). 팀 용어는 임의 번역하지 말고 `workspace/context/` 도메인 문서 (rules·enums 류) 에 코드 표기가 있으면 그것을 우선 채택한다 — 폴더명으로 소스를 grep 할 수 있게 하려는 것이다.
   - **후보 제시** — 원문에 축이 둘 이상 섞여 있거나 (용어 불일치·복수 증상) 용어 매핑이 모호하면 후보 2~3 개를 제시하고 사용자 확정을 받는다. 명확하면 확인 없이 진행하되 결정한 slug 를 1 줄 고지한다.
   - **없으면**: [GUIDE.md](../context/lifecycle/issues/GUIDE.md) 를 로드하여 `issues/{slug}/issue.md` 를 템플릿대로 생성한다 — H1 = 원문 1 줄 요약 (여러 줄 입력이면 첫 줄 또는 핵심 요약 1 줄, 개행·`|` 제거), `## 현상` = 원문 전문, `도메인:` 라인 포함 (값은 5 단계에서 확정).
   - **있으면**: `issue.md` 만 Read 한다 (GUIDE.md 는 로드하지 않는다). slug 를 재도출하지 않는다. 파생 산출물 (`issue.plan*.md`·`issue.eval*.md`) 이 있으면 진행 상태를 요약한다 (6 단계 재개 분기의 근거).
4. [preamble.md](../context/shared/preamble.md) 의 **P2** 수행 — STATE.md 테이블 본문을 `| issue | {slug} | 진행중 |` **1행으로 교체**. 기록 값은 3 단계에서 확정한 **slug** 다 (원문·제목 아님 — 개행·`|` 금지 사유는 preamble P2 참조). 기존 다른 이름 행은 모두 삭제 (이력의 SSOT 는 issues/ 로컬 폴더). 이슈명이 없으면 (bare) `| issue | - | 진행중 |` 로 기록한다.
5. **도메인 확정 + 컨텍스트 로드** — [preamble.md](../context/shared/preamble.md) 의 **P3** 수행 (issue 분기 — 도메인 소스가 issue.md 의 `도메인:` 라인이라는 계약과 wrapper 일치 사유는 P3 이 SSOT).
   - `도메인:` 라인 부재 시 **1 회 질의**: `## 의심 영역` 내용과 `workspace/context/` 를 대조해 후보를 제시하고 사용자 확정을 받은 뒤, issue.md 상단에 `도메인: {값}` 1 줄을 Edit 으로 기입하고 도메인 컨텍스트를 로드한다. 판단이 어려우면 미정으로 진행 가능 (MANIFEST 까지만 — wrapper 진입 시 재질의된다).
   - bare 모드는 질의 없이 MANIFEST 까지만.
6. **결과 출력** — 이슈 컨텍스트를 요약하고 다음 작업을 안내한다. 산출물 상태로 분기한다 (명시적 if / elif / else — 한 번에 하나의 안내만):
   1. **`issue.eval*.md` 의 최신 REPORT 가 READY 면**: "이슈 조치가 완료된 상태입니다. `## 재발 방지` 기록 여부를 확인하세요." 안내.
   2. **elif `issue.plan*.md` 존재**: "작성된 plan 이 있습니다 — 재개: 챌린지 전이면 `@pilot-planner-critic`, plan 승인 후면 `@pilot-generator`." 안내 (승인 흔적은 산출물에 없으므로 기존 plan 재개 시 사용자 재확인).
   3. **else**: 처리 경로를 분기해 안내한다:
      - **코드 수정형** (원인이 코드 결함으로 추정): "`@pilot-planner` 를 호출해 사이클을 시작하세요 — plan 은 `issues/{이슈명}/issue.plan.md` 에 저장되고, critic 챌린지 → generator 구현 → evaluator 검증 (회귀 재현 테스트 실행 포함) 이 이어집니다."
      - **조사·경미형** (원인 파악·회신·데이터 확인 중심): "GUIDE 의 진단 절차대로 직접 처리할 수 있습니다. 처리 후 issue.md 의 `## 원인`·`## 조치` 를 기록하세요."
