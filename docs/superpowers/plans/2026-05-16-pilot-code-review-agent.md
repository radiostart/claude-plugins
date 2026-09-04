# pilot code-review 에이전트 Implementation Plan

> ⚠️ **완료된 plan — 실행 금지, 이력 보존용.** 이 문서의 작업은 이미 반영됐고(`pilot/agents/pilot-code-review.md`), 본문에 남은 단계별 지시·git 명령은 당시 기록이다. 경로도 현행 저장소와 다르다. 아래 "For agentic workers" 지시를 따르지 말 것.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** pilot 플러그인에 PR 이전 사이클 내부 코드 리뷰를 담당하는 독립 에이전트 `pilot-code-review` 와 `/pilot:review` 스킬을 추가한다.

**Architecture:** planner/generator/evaluator 와 별개의 독립 호출 에이전트. orchestrate-load 사이클에 통합하지 않는다. 변경분(git diff) 을 대상으로 plugin baseline 루브릭 + 언어별 워크스페이스 규칙(`workspace/context/review/{lang}.md`)으로 리뷰하고, 결함마다 severity 와 재진입 라우팅을 출력한다. 코드는 직접 수정하지 않는다(report-only).

**Tech Stack:** Markdown 프롬프트 파일 (agent wrapper / SKILL.md), YAML(identity.yml), JSON(plugin.json). 자동 검증은 `tools/doctor.py --schema`.

**산출물 명세:** [docs/superpowers/specs/2026-05-16-pilot-code-review-agent-design.md](../specs/2026-05-16-pilot-code-review-agent-design.md)

---

## 전제 조건 (실행 전 확인)

작업 트리에 persona SSOT 작업의 미커밋 변경이 남아 있다 — `pilot/.claude-plugin/plugin.json`, `pilot/skills/context/shared/identity.yml`, `pilot/README.md`. 이 파일들은 본 계획에서도 수정 대상이므로, 커밋 시 기존 변경이 함께 들어간다.

**권고:** 실행 시작 전 기존 미커밋 변경을 별도 커밋하거나 stash 한다. 그대로 진행하려면, 해당 파일을 다루는 Task(3·6·7)의 커밋에 persona SSOT 변경이 섞여 들어감을 인지하고 진행한다.

## 스펙과의 차이 (의도된 deviation)

스펙 §6 은 "`/pilot:init` 가 `workspace/context/review/` 폴더와 `_TEMPLATE.md` 를 생성"한다고 했으나, `skills/init/SKILL.md` 는 "`rules/`·`scope/`·`enums/` 등 카테고리 폴더는 생성하지 않는다 — 사용자가 파일 추가 시 만든다"는 확립된 컨벤션을 갖는다. 이를 따르기 위해 **init 을 수정하지 않는다.** 대신 템플릿을 플러그인에 `review-rules-template.md` 로 두고, 사용자가 `workspace/context/review/{lang}.md` 로 복사한다. 에이전트는 파일 부재 시 baseline 으로 graceful fallback 한다.

## 파일 구조

**신규 (4):**

| 경로 | 책임 |
| --- | --- |
| `pilot/skills/context/shared/review-principles.md` | 언어 무관 baseline 리뷰 루브릭. 에이전트가 항상 로드. |
| `pilot/skills/context/shared/review-rules-template.md` | `workspace/context/review/{lang}.md` 작성용 템플릿. 사용자가 복사. |
| `pilot/agents/pilot-code-review.md` | 에이전트 wrapper. 변경분 수집 → 규칙 로드 → 리뷰 → REPORT 출력. |
| `pilot/skills/review/SKILL.md` | `/pilot:review` 스킬. 인자 파싱 후 `@pilot-code-review` dispatch. |

**수정 (3):**

| 경로 | 변경 |
| --- | --- |
| `pilot/skills/context/shared/identity.yml` | `personas.code-review` 추가 + personas 주석 갱신. |
| `pilot/.claude-plugin/plugin.json` | description 갱신 + version `0.2.1`→`0.3.0`. |
| `pilot/README.md` | 에이전트 목록·역할 경계에 `pilot-code-review`·`/pilot:review` 반영. |

**의존 순서:** review-principles.md → review-rules-template.md → identity.yml(persona) → pilot-code-review.md(앞 3개 참조) → review/SKILL.md(에이전트 참조) → plugin.json → README.md.

---

## Task 1: baseline 리뷰 루브릭

**Files:**
- Create: `pilot/skills/context/shared/review-principles.md`

- [ ] **Step 1: review-principles.md 작성**

아래 내용 그대로 작성한다:

```markdown
# 코드 리뷰 baseline 루브릭

`pilot-code-review` 에이전트가 **항상** 로드하는 언어 무관 리뷰 기준. 언어별 추가 규칙(`workspace/context/review/{lang}.md`)이 있으면 이 위에 덧붙는다.

> **critic 페르소나 전제** — 결함은 근거 없이 지나치지 않되, 취향·스타일 차이를 `blocking` 으로 격상하지 않는다. 각 항목의 **blocking 격상 기준**을 지킨다.

## 항목

### 명확성·네이밍
이름이 역할을 드러내는가. 오해를 부르는 이름·약어.
- blocking 격상: 이름이 실제 동작과 **반대·모순**되어 호출자가 오용할 위험이 있을 때.

### 함수·책임 크기
한 함수가 한 가지 일을 하는가. 과도한 길이·중첩.
- blocking 격상: 단독으로는 안 됨(suggestion). 분리 불가로 다른 blocking 결함이 가려질 때만.

### 중복·불필요한 추상화
같은 로직 반복, 또는 한 곳에서만 쓰는 추상화 신설.
- blocking 격상: 중복 분기 중 하나만 수정되어 **동작 불일치**가 이미 발생했을 때.

### 에러 처리 경계
시스템 경계(사용자 입력·외부 API)에서만 검증한다. 내부 코드·프레임워크 보장에 대한 과잉 방어는 결함.
- blocking 격상: 경계에서 **검증 누락**으로 잘못된 입력이 그대로 전파될 때.

### 죽은 코드·미사용
도달 불가 코드, 미사용 변수·import.
- blocking 격상: 안 됨(nit~suggestion).

### 보안
주입(SQL·명령·XSS), 비밀값 하드코딩. 심층 보안 패스는 `/security-review` 가 담당하므로 여기서는 변경분의 **명백한** 패턴만 본다.
- blocking 격상: 변경분에 주입 가능 경로 또는 평문 비밀값이 새로 추가됐을 때.

### 테스트 가능성
부수효과·전역 상태 의존으로 테스트가 어려운 구조.
- blocking 격상: 안 됨(suggestion).

## 변경분 한정

리뷰 대상은 **이번 diff 의 변경 라인**이다. 변경분 밖의 기존 결함은 보고하지 않는다(별도 이슈로 다룰 사안).
```

- [ ] **Step 2: 커밋**

```bash
git -C /Users/jay-p/Projects/claude-plugins add pilot/skills/context/shared/review-principles.md
git -C /Users/jay-p/Projects/claude-plugins commit -m "feat(code-review): baseline 리뷰 루브릭 추가"
```

---

## Task 2: 언어별 규칙 템플릿

**Files:**
- Create: `pilot/skills/context/shared/review-rules-template.md`

- [ ] **Step 1: review-rules-template.md 작성**

아래 내용 그대로 작성한다:

```markdown
# 언어별 리뷰 규칙 — 작성 템플릿

이 파일은 **템플릿**이다. `workspace/context/review/{lang}.md` 로 복사해 언어별 리뷰 규칙을 채운다.
`{lang}` 은 `pilot-code-review` 가 파일 확장자로 감지하는 언어명(예: `ruby`, `kotlin`, `typescript`, `python`, `go`).

- 이 파일이 있는 언어 → 아래 규칙 + plugin baseline(`review-principles.md`) 적용.
- 없는 언어 → baseline 만 적용.

복사 후 아래 `---` 밑 내용만 `{lang}.md` 에 남기고 채운다.

---

<!-- 선택: lint 명령을 한 줄 선언하면 에이전트가 해당 언어 변경 파일에 1회 실행한다. 불필요하면 이 줄을 지운다. -->
lint: bundle exec rubocop

# {언어} 리뷰 규칙

## 관용구·패턴
<!-- 이 언어에서 권장/금지하는 관용구. 예: Ruby — guard clause 선호, 명시적 nil 체크 지양 -->

## 자주 나오는 결함
<!-- 체크리스트 형식 권장 -->
- [ ] 예: N+1 쿼리

## blocking 격상 기준 (선택)
<!-- baseline 외에 이 언어에서 blocking 으로 볼 항목 -->
```

- [ ] **Step 2: 커밋**

```bash
git -C /Users/jay-p/Projects/claude-plugins add pilot/skills/context/shared/review-rules-template.md
git -C /Users/jay-p/Projects/claude-plugins commit -m "feat(code-review): 언어별 리뷰 규칙 템플릿 추가"
```

---

## Task 3: code-review 페르소나 (identity.yml)

**Files:**
- Modify: `pilot/skills/context/shared/identity.yml`

- [ ] **Step 1: personas 섹션 주석 갱신**

`identity.yml` 의 `personas:` 바로 아래 주석 3줄을 찾는다:

```yaml
personas:
  # 적용 범위: 에이전트 wrapper 전용 (pilot-planner/pilot-generator/pilot-evaluator).
  # 키는 orchestrate-load 의 `--phase` 와 1:1 매칭 (CLI 인자는 prefix 없음).
  # 스킬 페르소나는 각 SKILL.md 상단에 inline 으로 둔다 (자기 완결 SSOT).
```

아래로 교체한다:

```yaml
personas:
  # 적용 범위: 에이전트 wrapper 전용 (pilot-planner/pilot-generator/pilot-evaluator/pilot-code-review).
  # planner/generator/evaluator 키는 orchestrate-load 의 `--phase` 와 1:1 매칭 (CLI 인자는 prefix 없음).
  # code-review 는 orchestrate phase 가 아닌 독립 호출 에이전트 — phase 매칭 예외.
  # 스킬 페르소나는 각 SKILL.md 상단에 inline 으로 둔다 (자기 완결 SSOT).
```

- [ ] **Step 2: code-review 페르소나 추가**

`personas:` 의 마지막 항목인 `evaluator:` 블록 끝(파일 끝)에 이어 붙인다. 현재 파일 끝은:

```yaml
  evaluator:
    archetype: auditor
    voice: "증거 없으면 통과 없음. 반려에 인색하지 않다"
    phrasing: "gate 별 pass|fail|skip + 인용 (file:line 또는 명령 출력)"
    forbid:
      - "의도 추정으로 통과"
      - "증거 없는 status: READY"
```

이 뒤에 추가한다:

```yaml
  code-review:
    archetype: critic
    voice: "변경분만 본다. 결함은 근거 없이 지나치지 않는다"
    phrasing: "severity(blocking|suggestion|nit) + file:line 인용 + 개선안 + 재진입 라우팅"
    forbid:
      - "취향·스타일 차이를 blocking 으로 격상"
      - "변경분 밖 코드 지적"
```

- [ ] **Step 3: YAML 파싱 검증**

Run: `python3 -c "import yaml; d=yaml.safe_load(open('pilot/skills/context/shared/identity.yml')); print(sorted(d['personas']))"`
Expected: `['code-review', 'evaluator', 'generator', 'planner']` 출력 (에러 없음)

- [ ] **Step 4: 커밋**

```bash
git -C /Users/jay-p/Projects/claude-plugins add pilot/skills/context/shared/identity.yml
git -C /Users/jay-p/Projects/claude-plugins commit -m "feat(code-review): identity.yml 에 critic 페르소나 추가"
```

> 주의: identity.yml 에 persona SSOT 작업의 미커밋 변경이 있었다면 이 커밋에 함께 포함된다(전제 조건 참조).

---

## Task 4: pilot-code-review 에이전트

**Files:**
- Create: `pilot/agents/pilot-code-review.md`

- [ ] **Step 1: pilot-code-review.md 작성**

아래 내용 그대로 작성한다:

````markdown
---
name: pilot-code-review
description: 프로젝트 진행 중 작성된 코드(git diff)를 품질 관점에서 리뷰한다. PR 이전 사이클 내부 리뷰 전용. evaluator 와 별개.
tools: Read, Glob, Grep, Bash
---

> **이 파일은 wrapper입니다.** 직접 실행하지 않는다 — `/pilot:review` 또는 `@pilot-code-review` 로 호출.
> **톤·페르소나 SSOT:** [`identity.yml`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/identity.yml) (`personas.code-review` = critic)
>
> **경로 규칙:** 플러그인 지식 `${CLAUDE_PLUGIN_ROOT}/skills/` · 프로젝트 상태 `workspace/` (CWD)
>
> **사이클·orchestrate-load 와 독립** — planner/generator/evaluator 와 달리 orchestrate-load.py 를 실행하지 않는다. 호출자가 넘긴 target(diff 범위·경로)을 그대로 사용한다.

1. **대상 확정** — 호출자가 target 을 명시했으면 그 범위를, 없으면 변경분 전체를 수집한다.

   uncommitted 변경 우선:

   ```bash
   git diff --stat HEAD
   git diff HEAD
   ```

   uncommitted 변경이 비어 있으면 현재 브랜치 커밋 범위:

   ```bash
   git diff @{u}..HEAD 2>/dev/null || git diff $(git merge-base HEAD main)..HEAD
   ```

   target 이 경로면 `git diff HEAD -- {경로}`, 커밋 범위면 `git diff {범위}` 를 사용한다.
   diff 가 완전히 비어 있으면 "리뷰할 변경분이 없습니다." 출력 후 종료.

2. **언어 감지** — 변경 파일 확장자로 언어 집합을 도출한다 (예: `.rb`→ruby, `.kt`→kotlin, `.ts`/`.tsx`→typescript, `.py`→python, `.go`→go). 확장자가 매핑에 없으면 해당 파일은 baseline 으로만 본다.

3. **규칙 로드**
   - **항상** [`review-principles.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/review-principles.md) 를 Read 한다 (baseline 루브릭).
   - 감지된 각 언어 `{lang}` 에 대해 `workspace/context/review/{lang}.md` 가 존재하면 Read 해 규칙에 추가한다. 없으면 baseline 만 적용.
   - `review/{lang}.md` 상단에 `lint:` 로 시작하는 줄이 있으면, 해당 언어의 변경 파일 경로를 인자로 그 명령을 Bash 로 1회 실행하고 출력을 findings 판단에 반영한다. `lint:` 줄이 없으면 lint 를 실행하지 않는다.

4. **현재 feature 파악 (라우팅용)** — `workspace/STATE.md` 를 Read 해 `진행중` 프로젝트를 확인하고, `workspace/projects/{PROJECT}/project.md` 에서 진행 중 feature 번호를 파악한다. 파일이 없거나 파싱에 실패해도 리뷰는 계속한다 (이 경우 `feature` 라우팅은 "feature 명세 점검 필요" 로 일반화).

5. **리뷰** — 수집한 diff 헌크를 로드한 규칙 대비 검토한다. 발견한 결함마다:
   - **severity** — `blocking` / `suggestion` / `nit`. blocking 격상은 `review-principles.md` 의 항목별 격상 기준을 따른다. 취향·스타일 차이를 blocking 으로 올리지 않는다.
   - **근거** — `file:line` 인용.
   - **개선안** — 구체적 수정 방향.
   - **재진입 라우팅** — 아래 기준으로 1개 선택:
     - `feature` — feature 명세 자체의 누락·오류가 결함의 원인 (스펙 빈틈)
     - `planner` — 설계·구조 결함 (책임 분리, 의존성 방향, 잘못된 추상화)
     - `generator` — 구현 수준 결함 (로직 버그, 패턴 미준수, 누락된 처리)
     - `local` — 국소·단순 수정 (네이밍, nit)
   - 변경분 밖의 기존 코드는 지적하지 않는다.

6. **[필수] CODE REVIEW REPORT 출력** — 메시지 끝에 아래 블록을 붙인다. 코드는 수정하지 않는다.

   ```
   ## CODE REVIEW REPORT
   - target: {diff 범위 / 경로}
   - languages: {감지된 언어 — 각 언어 규칙 파일 적용 여부}
   - summary: blocking N · suggestion N · nit N
   - findings:
     - [blocking] {요약} — {file:line}
       개선안: {...}
       재진입: generator | planner | feature | local
     - [suggestion] {요약} — {file:line}
       개선안: {...}
       재진입: ...
     - [nit] {요약} — {file:line}
   - routing:
     - feature 단계부터: #{finding 번호}… | none
     - planner 부터: #{finding 번호}… | none
     - generator 부터: #{finding 번호}… | none
     - 로컬 수정: #{finding 번호}… | none
   - 다음: 위 라우팅 중 선택해 주세요
   ```

   - 결함이 없으면 `findings:` 를 `- none`, `routing:` 4행을 모두 `none`, `summary` 를 `blocking 0 · suggestion 0 · nit 0` 으로 출력.
   - 사용자가 라우팅을 선택하면 해당 단계 진입을 안내한다 (`feature` → `features/NN-{slug}.md` 수정 후 사이클 재실행, `planner`/`generator` → 해당 에이전트 재호출, `local` → 즉시 수정). 에이전트가 코드를 직접 고치지 않는다.

---

## 탐색 제약

리뷰 범위는 이번 변경분 + 결함 판단에 필요한 직접 의존 경로로 한정한다. 변경분과 무관한 코드베이스 광역 탐색은 하지 않는다.
````

- [ ] **Step 2: 에이전트 frontmatter 스키마 검증**

Run: `python3 pilot/tools/doctor.py --schema`
Expected: `agents/*.md` frontmatter 항목 PASS, ERROR 0건 (exit 0). `pilot-code-review.md` 가 `name`·`description`·`tools` 보유.

- [ ] **Step 3: 커밋**

```bash
git -C /Users/jay-p/Projects/claude-plugins add pilot/agents/pilot-code-review.md
git -C /Users/jay-p/Projects/claude-plugins commit -m "feat(code-review): pilot-code-review 에이전트 추가"
```

---

## Task 5: /pilot:review 스킬

**Files:**
- Create: `pilot/skills/review/SKILL.md`

- [ ] **Step 1: review/SKILL.md 작성**

아래 내용 그대로 작성한다:

````markdown
---
name: review
description: >-
  프로젝트 진행 중 작성된 코드를 PR 이전에 품질 관점에서 리뷰한다.
  변경분(git diff)을 대상으로 pilot-code-review 에이전트를 호출하며,
  결함마다 severity 와 재진입 라우팅(feature/planner/generator)을 제시한다.
  evaluator 의 요구사항·게이트 판정과는 별개 축이다.
---

# /pilot:review

PR 생성 이전, 사이클 내부에서 작성된 코드를 품질 관점으로 리뷰한다.

대상: $ARGUMENTS

---

## 동작

1. **target 결정**
   - 인자 없음 → 변경분 전체 (uncommitted + 현재 브랜치 커밋)
   - 경로 인자 (예: `app/services/`) → 해당 경로로 한정
   - 커밋 범위 인자 (예: `HEAD~3..HEAD`) → 해당 범위
2. 결정한 target 을 전달하며 `@pilot-code-review` 를 호출한다.

에이전트가 변경분을 수집해 언어별 규칙 + baseline 루브릭으로 리뷰하고 `CODE REVIEW REPORT` 를 출력한다. 코드는 수정하지 않으며, 결함마다 재진입 단계(feature/planner/generator/local)를 제시해 사용자가 선택한다. 상세 절차: [`pilot-code-review.md`](${CLAUDE_PLUGIN_ROOT}/agents/pilot-code-review.md).

---

## 언어별 규칙

언어별 리뷰 규칙은 `workspace/context/review/{lang}.md` 에 둔다. 파일이 있는 언어는 그 규칙 + plugin baseline 이, 없는 언어는 baseline 만 적용된다. 작성 템플릿: [`review-rules-template.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/review-rules-template.md).

---

## 역할 경계

- `/pilot:review` (이 스킬) — **PR 이전** 로컬 변경분의 품질 리뷰. 대화창에 리포트 + 재진입 라우팅 출력.
- `@pilot-evaluator` — 요구사항 충족·게이트 통과 **판정**. 사이클의 일부.
- 공식 `/code-review` — **PR 생성 후** GitHub PR 대상 자동 리뷰, PR 코멘트 게시. `/pilot:pr` 다음 단계로 권장.
- 내장 `/security-review` — 심층 보안 패스. 보안이 중요한 변경에 별도 권장.
````

- [ ] **Step 2: SKILL.md frontmatter 스키마 검증**

Run: `python3 pilot/tools/doctor.py --schema`
Expected: `skills/*/SKILL.md` frontmatter 항목 PASS, ERROR 0건 (exit 0). `review/SKILL.md` 가 `name`·`description` 보유, description 1024 bytes 이하.

- [ ] **Step 3: 커밋**

```bash
git -C /Users/jay-p/Projects/claude-plugins add pilot/skills/review/SKILL.md
git -C /Users/jay-p/Projects/claude-plugins commit -m "feat(code-review): /pilot:review 스킬 추가"
```

---

## Task 6: plugin.json 갱신

**Files:**
- Modify: `pilot/.claude-plugin/plugin.json`

- [ ] **Step 1: description·version 수정**

현재 파일:

```json
{
  "name": "pilot",
  "version": "0.2.1",
  "description": "Domain-knowledge-driven agent workflow plugin for complex projects (pilot-planner → pilot-generator → pilot-evaluator)",
  "author": {
    "name": "Jay-P",
    "email": "noreply@example.com"
  }
}
```

아래로 교체한다 (`version` 과 `description` 만 변경, `author` 유지):

```json
{
  "name": "pilot",
  "version": "0.3.0",
  "description": "Domain-knowledge-driven agent workflow plugin for complex projects (pilot-planner → pilot-generator → pilot-evaluator) + pilot-code-review for pre-PR code review",
  "author": {
    "name": "Jay-P",
    "email": "noreply@example.com"
  }
}
```

- [ ] **Step 2: JSON 유효성 + 스키마 검증**

Run: `python3 -c "import json; json.load(open('pilot/.claude-plugin/plugin.json'))" && python3 pilot/tools/doctor.py --schema`
Expected: JSON 파싱 에러 없음. doctor `--schema` 의 `plugin.json` 필수·금지 키 PASS. `version` ↔ git tag 불일치는 WARN 일 수 있음 (ERROR 아님 — 허용).

- [ ] **Step 3: 커밋**

```bash
git -C /Users/jay-p/Projects/claude-plugins add pilot/.claude-plugin/plugin.json
git -C /Users/jay-p/Projects/claude-plugins commit -m "chore(code-review): plugin v0.3.0 — pilot-code-review 반영"
```

> 주의: plugin.json 에 미커밋 변경이 있었다면 이 커밋에 함께 포함된다(전제 조건 참조).

---

## Task 7: README 갱신

**Files:**
- Modify: `pilot/README.md`

- [ ] **Step 1: 에이전트·스킬 언급 반영**

`pilot/README.md` 를 Read 해 아래 3곳을 수정한다. 정확한 라인은 Read 후 확인한다.

a. TOC 의 `[에이전트 (3종)](#에이전트-3종)` 항목 — `pilot-code-review` 가 사이클 3종과 별개 독립 에이전트임이 드러나도록 인접 줄에 한 줄 보강 (예: 동일 절 안에 "독립: pilot-code-review" 언급). 절 제목 자체를 바꿔 앵커가 깨지지 않도록 주의.

b. 설치 확인 문장 (`@pilot-planner`·`@pilot-generator`·`@pilot-evaluator` subagent 호출 가능) — `@pilot-code-review` 를 목록에 추가.

c. "스킬 vs 에이전트" 또는 인접 절 — `/pilot:review` 가 PR 이전 코드 리뷰용 스킬임을 한 줄 추가. 가능하면 공식 `/code-review` 와의 시점 차이(PR 이전 vs 이후)도 한 줄.

문서 산문이므로 정확한 워딩은 주변 문체에 맞춘다. 새 절을 만들지 말고 기존 문장에 최소 보강한다.

- [ ] **Step 2: 커밋**

```bash
git -C /Users/jay-p/Projects/claude-plugins add pilot/README.md
git -C /Users/jay-p/Projects/claude-plugins commit -m "docs(code-review): README 에 pilot-code-review·/pilot:review 반영"
```

> 주의: README.md 에 미커밋 변경이 있었다면 이 커밋에 함께 포함된다(전제 조건 참조).

---

## Task 8: 통합 검증

**Files:** (없음 — 검증만)

- [ ] **Step 1: 전체 스키마 검증**

Run: `python3 pilot/tools/doctor.py --schema`
Expected: ERROR 0건 (exit 0). `agents/pilot-code-review.md` 와 `skills/review/SKILL.md` 가 frontmatter 검사를 통과.

- [ ] **Step 2: 참조 무결성 점검**

Run: `grep -rn 'review-principles.md\|review-rules-template.md\|pilot-code-review' pilot/agents/pilot-code-review.md pilot/skills/review/SKILL.md`
Expected: 각 참조 경로의 실제 파일이 존재한다. 다음으로 확인:
`ls pilot/skills/context/shared/review-principles.md pilot/skills/context/shared/review-rules-template.md pilot/agents/pilot-code-review.md pilot/skills/review/SKILL.md`
Expected: 4개 파일 모두 존재.

- [ ] **Step 3: 수동 동작 검증 (소비 워크스페이스에서)**

자동 테스트로 프롬프트 동작은 검증되지 않는다. pilot 워크스페이스가 있는 프로젝트에서 다음을 수동 확인한다:
- 변경분이 있는 상태에서 `/pilot:review` 실행 → `@pilot-code-review` 가 dispatch 되고 `CODE REVIEW REPORT` 블록이 출력되는가.
- diff 가 비어 있을 때 → "리뷰할 변경분이 없습니다." 출력 후 종료하는가.
- `workspace/context/review/` 폴더가 없어도 baseline 으로 리뷰가 진행되는가.
- 코드 파일이 수정되지 않는가 (report-only).

검증 결과를 사용자에게 보고한다. 실패 시 해당 Task 로 돌아간다.

---

## Self-Review

**Spec coverage:**
- 신규 에이전트 `pilot-code-review` → Task 4 ✅
- `/pilot:review` 스킬 → Task 5 ✅
- baseline 루브릭 `review-principles.md` → Task 1 ✅
- 언어별 규칙 파일 컨벤션 + 템플릿 → Task 2 (스펙 §6 의 init 수정은 의도적 deviation — 위 "스펙과의 차이" 참조) ✅
- `personas.code-review` (critic) → Task 3 ✅
- plugin.json description·version → Task 6 ✅
- 공식 `/code-review` 와의 경계 명시 → Task 5 SKILL.md 역할 경계 절 ✅
- git diff 기본 대상 + 인자 지정 → Task 4 step 1, Task 5 step 1 ✅
- 재진입 라우팅 출력 → Task 4 step 5·6 ✅
- report-only (코드 미수정) → Task 4 step 6, Task 8 step 3 ✅
- CODE REVIEW REPORT 형식 → Task 4 step 6 ✅

**Placeholder scan:** 모든 파일 내용이 완전히 기재됨. Task 7 만 README 산문 특성상 정확 워딩을 실행자 재량에 맡기되 수정 위치 3곳과 제약(앵커 보존·새 절 금지)을 명시 — 코드 placeholder 아님.

**Type consistency:** severity 값 `blocking|suggestion|nit`, 라우팅 값 `feature|planner|generator|local`, persona 키 `code-review`, 파일명 `review-principles.md`·`review-rules-template.md`·`pilot-code-review.md` — 전 Task 일관.
