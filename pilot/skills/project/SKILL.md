---
name: project
description: >-
  새 프로젝트를 시작하거나 기존 프로젝트를 재개할 때 사용한다.
  `workspace/projects/{PROJECT}/` 폴더를 생성·로드하고 STATE.md 를
  갱신한 뒤 도메인 컨텍스트를 적재한다. 인자로 Confluence URL 이 오면
  내부적으로 confl·analyze 를 위임 호출하고, `--tdd` 플래그로 TDD 모드를
  켤 수 있다. 단발 이슈는 `/pilot:issue` 를 사용한다.
---

프로젝트 개발 모드를 활성화한다.

대상 프로젝트: $ARGUMENTS

**옵션:** `--tdd` — TDD 모드 활성화 (신규·기존 모두) · `{URL}` — Confluence 기획서 URL/page_id (저장+분석 동시 수행)

**사용 예:** `/pilot:project MyProject` · `/pilot:project MyProject --tdd` · `/pilot:project MyProject https://wiki.example.com/pages/12345 --tdd`

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P-1, P0** 수행. P0 는 `{PROJECT}`·`{CONFL_URL}` 과 주변 키워드로 memory-hint 실행 후 출력 메모를 Read 하여 과거 이력 반영.

## 수행 절차

아래 순서대로 진행한다. 중간 단계마다 "다음 작업" 안내를 흘리지 않고 모든 단계를 마친 뒤 결과 출력에서 한 번만 안내한다 (실측 기반 규칙 — 단계마다 안내하면 후속 단계 호출을 놓치는 경우가 잦았다).

### 1. 인자 파싱

`$ARGUMENTS` 를 `--tdd`(`{TDD}` 플래그) · `http(s)://` 또는 순수 숫자(`{CONFL_URL}`) · 그 외(`{PROJECT}`) 로 분류. `{PROJECT}` 비어있으면 안내 후 종료. 예약어(`example`·`workspace`·`STATE`·`context`)면 안내 후 종료.

### 2. 프로젝트 폴더 생성/로드

`workspace/projects/{PROJECT}/` 존재 여부를 Glob 확인.

- **없으면**: [example/](../context/lifecycle/projects/example/) 4 종을 **그대로 복사**한 뒤 각 파일 H1 의 `{프로젝트명}` 토큰만 치환한다 (파일당 1 회). **본문 재작성·요약·환각·도메인 예시 삽입 절대 금지** — placeholder·표식 그대로 유지, GUIDE.md 본문 복사 금지. **A2 fallback**: H1 토큰 부재 시 치환 skip + INFO, abort 금지. 구조 상세: [GUIDE.md](../context/lifecycle/projects/GUIDE.md) (가이드 본문은 참고용 — 생성물에 복사하지 않는다).

  **`## 관련 파일` H3 동적 채움** — 복사 직후 1 회만. `config.md` `## scope 카테고리` 의 `project.md 대상 H3` 컬럼마다 `### {대상 H3}` + 빈 표를 `## 관련 파일` 에 추가 (config 비어있으면 [scope-sync.md](../analyze/references/scope-sync.md) 5-2 default, 잘못된 행은 WARN + default — A2). **SSOT 분리**: H3 헤더=본 단계 1 회 생성(재실행 시 보존) / 표 본문=analyze 5-2·create-feature 매번 갱신 / 사용자 수동 H3=양쪽 보존, 삭제 시 미복구. 예외: `## 관련 파일` H2 자체 부재면 H2+H3 모두 새로 생성.

  **`.agent-state.yml` 초기화**: `schema: v1.2` / `analyzed: false` / `tdd: false` / `domain: null` / `plugin_version`(획득 실패 시 라인 생략). `domain` 은 analyze 진입 시 사용자 확인 후 채워진다 — 여기서 자동 추론 금지.

- **있으면**: `project.md`·`prompts/` 로드. `.agent-state.yml` 없거나 `schema: v1` 이면 `/pilot:doctor --fix` 안내. **drift 체크** (v1.1+, `analyzed_at` 존재 시): `docs_last_fetched_at > analyzed_at` → 재분석 여부 질의(y→6·7·8 수행) / `features 개수 > last_analyzed_features+1` → `--regen-agents` 권장 / `scope mtime > analyzed_at` → `--regen-agents` 권장 (모두 안내만, 자동 실행 X).

### 3. STATE.md 갱신

[preamble.md](../context/shared/preamble.md) 의 **P2** 수행 (`| project | {PROJECT} | 진행중 |` 1행 교체).

### 4. 도메인 컨텍스트 로드

[preamble.md](../context/shared/preamble.md) 의 **P3** 수행.

### 5. TDD 모드 적용 (`{TDD}` 있을 때만)

[tdd-activation.md](../context/modes/tdd-activation.md) 절차 수행.

### 6. 기획서 저장 (`{CONFL_URL}` 있을 때만)

`/pilot:confl` 을 nested 호출하지 않고 이 턴에 직접 실행한다 (nested 호출은 컨텍스트 이중 적재·경로 어긋남 위험):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/confluence.py fetch "{CONFL_URL}"
```

성공 시 저장 경로·섹션 목록 출력. 실패 시 에러 안내 후 7·8 단계를 건너뛰고 9 단계로 (2 단계 템플릿 유지).

### 7. 기능 분석 (6단계 성공 시만)

사용자에게 **전체 분석 / 키워드 필터(실제 H2 예시 2~4개 제시) / 건너뛰기** 질의. 선택에 따라 [../analyze/SKILL.md](../analyze/SKILL.md) 의 "분석 프로세스" **1~5단계**를 실행한다. 건너뛰거나 실패 시 8단계 skip → 9단계.

### 8. prompts/ 갱신 및 자가 검증 (7단계에서 분석 수행 시만)

[../analyze/SKILL.md](../analyze/SKILL.md) 의 "분석 프로세스" **6~7단계**를 실행한다.

### 9. 무결성 검증 (자동)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace
```

출력 규칙: [`doctor/SKILL.md`](../doctor/SKILL.md) § 임베디드 호출 시 출력 규칙 참조.

### 10. 결과 출력

프로젝트 컨텍스트 요약 + 다음 작업 안내. TDD 모드면 "`@pilot-planner` 호출 시 Red 계약이 함께 수행됩니다" 안내 추가.

**다음 단계 안내** — features/ 존재 여부로 분기: **있음** → "`@pilot-planner` 를 호출해 구현을 시작하세요" / **없음** → `project.md` 보강 → `/pilot:confl`+`/pilot:analyze` 또는 `/pilot:create-feature` → `@pilot-planner` 순서 안내.

**공통**: "Slack 완료·승인 알림은 `/pilot:slack` 으로 활성화" 안내 1줄 (신규 프로젝트만 — 기존 재활성화 시 생략).
