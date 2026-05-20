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

**옵션:**

- `--tdd` — 프로젝트를 TDD 모드로 활성화한다 (신규·기존 모두 적용)
- `{URL}` — Confluence 기획서 URL 또는 page_id. 기획서 저장과 분석까지 한번에 수행

**사용 예:**

```
/pilot:project MyProject
/pilot:project MyProject --tdd
/pilot:project MyProject https://wiki.example.com/pages/12345
/pilot:project MyProject https://wiki.example.com/pages/12345 --tdd
```

---

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P-1, P0** 수행.

- P-1: TodoWrite 선로딩 (다단계 스킬).
- P0: 인자의 `{PROJECT}`·`{CONFL_URL}` 과 주변 키워드로 memory-hint 실행. 출력된 메모 파일을 Read 하여 과거 동일·유사 주제의 이력을 컨텍스트에 반영 (선행 구현 코드·정책 점검 이력 등).

---

## 수행 절차

아래 순서대로 진행한다. 중간 단계에서 "다음 작업" 안내를 출력하지 않고 모든 단계를 마친 뒤 결과 출력에서 한 번만 안내한다 — 단계마다 안내를 흘리면 사용자가 파편적으로 인지하고 후속 단계 호출을 놓치는 경우가 잦았다.

### 1. 인자 파싱

`$ARGUMENTS` 를 아래 3가지 토큰으로 분류한다:

| 토큰 패턴 | 분류 |
| --- | --- |
| `--tdd` | `{TDD}` 플래그 |
| `http://`, `https://` 로 시작 또는 순수 숫자 | `{CONFL_URL}` |
| 그 외 | `{PROJECT}` |

검증:

- `{PROJECT}` 가 비어있으면 [messages.md](../context/shared/messages.md) 의 `project_name_required` 출력 후 종료.
- `{PROJECT}` 가 예약어(`example`, `workspace`, `STATE`, `context`)이면 [messages.md](../context/shared/messages.md) 의 `project_name_reserved` 출력 후 종료.

### 2. 프로젝트 폴더 생성/로드

`workspace/projects/{PROJECT}/` 폴더 존재 여부를 Glob 으로 확인한다.

- **없으면**: [skills/context/lifecycle/projects/example/](../context/lifecycle/projects/example/) 의 파일 4종 (`project.md`, `prompts/planner.md`, `prompts/generator.md`, `prompts/evaluator.md`) 을 **그대로 복사**한 뒤 `{프로젝트명}` 토큰만 실제 프로젝트명으로 치환한다. **그 외 본문은 일절 재작성·요약·환각·도메인 예시 삽입 금지.**

  > **치환 범위 (H1 헤더 정확 매칭)** — 토큰 치환은 다음 두 조건을 모두 만족하는 라인만 대상:
  >
  > - `^#\s+.*\{프로젝트명\}.*$` 정확 매칭 (단일 라인 H1 안 `{프로젝트명}` 토큰)
  > - 코드블록 (` ``` `) 외부 위치
  >
  > **보존 대상 (치환 안 함):**
  >
  > - 가이드 주석 (`` > `{프로젝트명}` 토큰만 ... `` 같은 self-reference) — example template 의 스캐폴딩 설명용. 본문 prose 안 백틱 토큰은 보존.
  > - 마크다운 코드블록 (` ``` `) 안의 `{프로젝트명}` — 예시 코드.
  > - 표 본문 셀 안의 `{프로젝트명}` — 예시 행.
  >
  > **사용자 프로젝트명 sanitize** — `[a-zA-Z0-9가-힣\-_]` 외 문자 (예: `{`·`}`·정규식 메타) 포함 시 차단하고 사용자 질의 prompt. sanitize 통과 후 H1 치환 진행.
  >
  > **A2 runtime fallback** — H1 헤더에 `{프로젝트명}` 토큰 부재 (사용자가 이미 H1 직접 작성 등) → 치환 skip + `[INFO] {프로젝트명} 토큰 부재 — 치환 skip, 기존 H1 보존` 1 줄. abort 하지 않는다.
  >
  > **대상 파일 (4 종)** — 본 단계가 치환하는 파일은 `project.md` 1 + `prompts/{planner,generator,evaluator}.md` 3 = 총 4 종. 각 파일의 H1 1 회씩 치환 (`# {프로젝트명}` / `# Planner — {프로젝트명}` / `# Generator — {프로젝트명}` / `# Evaluator — {프로젝트명}`).

  - example 은 실구현 콘텐츠 없이 구조·세만틱 명시만 담긴 순수 템플릿이다. 본문의 `{…}` 플레이스홀더와 `_(analyze 실행 전 …)_` 같은 표식은 그대로 유지한다.
  - 섹션명·순서는 `/pilot:analyze` 주입 대상과 동기화되어 있다. 임의 변경 금지.
  - `## 개요` / `## 제한사항` / `## 목표` / `관련 파일` 표는 이후 사용자가 수동으로 또는 `/pilot:analyze` 가 자동으로 채운다. 스캐폴딩 단계에서 추측·기입하지 않는다. (base 브랜치는 `/pilot:pr` 가 state/config 로 자체 관리하므로 project.md 에 기록하지 않는다.)
  - 구조·섹션 의미에 대한 상세는 [GUIDE.md](../context/lifecycle/projects/GUIDE.md) 를 참조하되 **가이드 본문을 생성물에 복사하지 않는다** (가이드는 구조 참고용, example 이 실제 스캐폴딩 소스).
  - **신규 프로젝트의 `## 관련 파일` H3 동적 채움** — example 복사 직후 1 회만 수행. 재실행 시 기존 H3 보존.

    > **config lookup**: `workspace/context/config.md` 의 `## scope 카테고리` 섹션을 Read. `project.md 대상 H3` 컬럼의 각 값에 대해 `workspace/projects/{PROJECT}/project.md` 의 `## 관련 파일` 안에 `### {대상 H3}` + 빈 표 (`표 헤더` 컬럼의 3 컬럼) 1 행 추가. config 비어있으면 SKILL.md default (아래 표) 사용. 잘못된 행은 stderr `[WARN] config.md ## scope 카테고리: {사유} — default 사용` 1 줄 후 default fallback (A2 runtime, abort 안 함).

    > default — `workspace/context/config.md` 의 `## scope 카테고리` 가 비어있을 때 사용. config 행이 있으면 그 행이 우선.

    | 대상 H3 | 표 헤더 |
    | --- | --- |
    | Models | Class, DB, 목적 |
    | Endpoints | 엔드포인트, Method, 목적 |
    | Services | Class, 파일, 목적 |

    **SSOT 분리:**
    - H3 헤더 = 본 단계가 1 회 생성. 재실행 시 기존 H3 보존 (덮어쓰기 금지).
    - 표 본문 = `/pilot:analyze` 5-2 또는 `/pilot:create-feature` 가 매번 갱신.
    - 사용자 수동 추가 H3 (config 외) = 본 단계와 analyze 5-2 양쪽 모두 보존.
    - 사용자 H3 삭제 = 본 단계 재실행 시 복구하지 않음 (사용자 의도로 간주).

    **예외:** example/project.md 자체에 `## 관련 파일` H2 가 부재면 H2 + H3 모두 새로 생성. (이 케이스는 사용자가 template 을 손댄 비정상 상황이지만 graceful 처리.)

  - **`.agent-state.yml` 초기화** — 프로젝트 루트에 아래 내용으로 생성한다 (스키마 상세: [state-schema.md](../context/lifecycle/state-schema.md)):

    ```yaml
    schema: v1.2
    analyzed: false
    tdd: false
    domain: null
    plugin_version: "{PLUGIN_VERSION}"
    ```

    `{PLUGIN_VERSION}` 은 Bash 로 `python3 -c "import json,os; print(json.load(open(os.environ['CLAUDE_PLUGIN_ROOT']+'/.claude-plugin/plugin.json'))['version'])"` 를 실행해 얻은 현재 플러그인 버전으로 치환한다. 환경변수 미설정 등으로 값을 얻지 못하면 해당 라인 자체를 생략한다 (`plugin_version` 은 optional — 다음 writer 이벤트에서 채워짐).

    `domain` 은 `/pilot:analyze` 진입 시 사용자 확인을 거쳐 값이 채워진다. 여기서 자동 추론·기입 금지.
- **있으면**: `project.md` 및 `prompts/` 문서를 로드한다.
  - `.agent-state.yml` 이 없거나 `schema: v1` 이면 **사용자에게 `/pilot:doctor --fix` 실행을 안내** (v1 → v1.2 업그레이드 필요).
  - **drift 체크** (state 가 v1.1+ 이고 `analyzed: true`, `analyzed_at` 존재 시):
    - `docs_last_fetched_at > analyzed_at` → "기획서가 analyze 이후 변경됐습니다. 재분석할까요? (y/n)" 질의. `y` 면 6·7·8단계 수행, `n` 이면 스킵.
    - `count(features/*.md) > last_analyzed_features + 1` → "features 가 N 건 추가됐습니다. `/pilot:analyze --regen-agents` 권장" 안내 (자동 실행 X).
    - `scope/{domain}.md` mtime > `analyzed_at` → "scope 업데이트됨 → `--regen-agents` 권장" 안내.

### 3. STATE.md 갱신

[preamble.md](../context/shared/preamble.md) 의 **P2** 수행 — 테이블 본문을 `| project | {PROJECT} | 진행중 |` **1행으로 교체**. 기존 다른 이름 행은 모두 삭제 (이력은 git log). 현재 활성 이름이 `{PROJECT}` 와 동일하면 변경 없음.

### 4. 도메인 컨텍스트 로드

[preamble.md](../context/shared/preamble.md) 의 **P3** 수행.

### 5. TDD 모드 적용 (`{TDD}` 있을 때만)

[tdd-activation.md](../context/modes/tdd-activation.md) 절차를 수행한다.

### 6. 기획서 저장 (`{CONFL_URL}` 있을 때만)

아래 Bash 명령을 이 턴에 직접 실행한다. `/pilot:confl` 스킬을 nested 호출하지 않고 동일 도구를 Bash 로 직접 사용한다 — nested 호출은 컨텍스트가 두 번 적재되거나 작업 경로가 어긋나 후속 7·8 단계와 동기화되지 않는다.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/confluence.py fetch "{CONFL_URL}"
```

- 성공 시 저장된 파일 경로와 섹션 목록을 출력한다.
- 실패 시 에러 메시지를 안내하고 7·8단계를 건너뛰어 9단계로 진행한다. 2단계 템플릿은 유지된다.

### 7. 기능 분석 (6단계 성공 시만)

사용자에게 분석 범위를 질의한다:

- **전체 분석** — docs/ 모든 내용
- **키워드 필터** — 특정 영역만 (다운로드된 docs 의 H2 섹션을 훑어 실제 키워드 2~4개를 예시로 제시. 예: "ADMIN" · "API" · "정책")
- **건너뛰기** — 나중에 `/pilot:analyze` 로 별도 실행

사용자 선택에 따라 [../analyze/SKILL.md](../analyze/SKILL.md) 의 "분석 프로세스" 1~5단계를 실행한다. 건너뛰거나 분석 실패 시 8단계를 건너뛰고 9단계로 진행한다.

### 8. project.md 및 prompts/ 갱신 (7단계에서 분석 수행 시만)

[../analyze/SKILL.md](../analyze/SKILL.md) 의 "분석 프로세스" 6~7단계를 실행한다 (project.md 목표 동기화 + prompts/ 갱신).

### 9. 무결성 검증 (자동)

모든 단계 완료 후 아래를 실행한다:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace
```

- ERROR 또는 WARN 있으면 **원문을 사용자에게 그대로 출력**한다.
- 모두 PASS 면 `doctor: all checks passed` 한 줄만 표시.

### 10. 결과 출력

프로젝트 컨텍스트를 요약하고 다음 작업을 안내한다.

- `project.md` 제한사항에 **TDD 모드** 문구가 있으면: "이 프로젝트는 TDD 모드입니다. `@pilot-planner` 호출 시 스텝 분할과 실패 테스트 작성이 함께 수행됩니다." 안내 추가.

**다음 단계 안내** — features/ 존재 여부로 분기:

- **features/ 있음** (6~8단계 완료): 생성된 features 와 갱신된 파일을 요약하고 "`@pilot-planner` 를 호출해 구현을 시작하세요." 안내.
- **features/ 없음**: 생성된 파일(`project.md`, `prompts/`)을 요약하고 아래 순서 안내:
  1. `project.md` 의 개요·목표·관련 파일을 채운다
  2. **기획서 기반 다건 생성** — `/pilot:confl {url}` → `/pilot:analyze`
  3. **프롬프트 기반 단건 생성** — `/pilot:create-feature "<한 줄 설명>"` (기획서 없을 때)
  4. 준비되면 `@pilot-planner` 호출

**선택 안내 (공통):** "작업 완료·승인 알림을 Slack 으로 받고 싶으면 `/pilot:slack` 으로 활성화하세요." 한 줄을 덧붙인다. 기존 프로젝트 재활성화 시에는 출력하지 않는다 (이미 알고 있거나 의도적으로 비활성).
