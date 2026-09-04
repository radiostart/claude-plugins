# pilot — Review skills

PR 이전, 사이클 내부에서 작성된 코드를 품질 관점으로 리뷰한다. 2 개 스킬: `pilot-review` `code-review-init`. evaluator 의 요구사항·게이트 판정과는 **별개 축** (`pilot/skills/pilot-review/SKILL.md:7`).

---

## `/pilot:pilot-review`

변경분 (git diff) 을 대상으로 `@pilot-code-review` 에이전트를 호출한다 (`pilot/skills/pilot-review/SKILL.md:12`).

- **사전 확인**: 없음 — 사전 확인 없이 target 을 결정해 self-contained 에이전트에 위임한다 (`pilot/skills/context/shared/preamble.md:90·100`).
- **target 결정** (`pilot/skills/pilot-review/SKILL.md:18-22`):
  - 인자 없음 → 변경분 전체 (uncommitted + 현재 브랜치 커밋)
  - 경로 인자 (예: `app/services/`) → 해당 경로 한정
  - 커밋 범위 인자 (예: `HEAD~3..HEAD`) → 해당 범위
- **동작** (`pilot/skills/pilot-review/SKILL.md:24`): 에이전트가 변경분을 수집해 언어별 규칙 + baseline 루브릭으로 리뷰하고 `CODE REVIEW REPORT` 를 출력한다. **코드는 수정하지 않으며**, 결함마다 재진입 라우팅 (`feature`/`planner`/`generator`/`trivial`/`new-feature`/`dismiss`) 을 제시해 사용자가 선택한다. REPORT 의 routing 요약이 trivial 일괄 커밋·one-shot 묶음·full-cycle 후보까지 직접 안내한다.
- **언어별 규칙** (`pilot/skills/pilot-review/SKILL.md:28`): `workspace/context/review/{lang}.md` 가 있는 언어는 그 규칙 + plugin baseline, 없는 언어는 baseline 만. 작성 템플릿은 `pilot/skills/context/shared/review-rules-template.md`.
- **역할 경계** (`pilot/skills/pilot-review/SKILL.md:30-35`):
  - `/pilot:pilot-review` — 팀 규칙 파일 적용·사이클 재진입 라우팅이 필요한 리뷰. 대화창에 리포트 + 라우팅 출력.
  - 내장 `/code-review` — 범용 정확성 리뷰 패스 (로컬 변경분·GitHub PR 모두). 팀 규칙·라우팅이 필요 없으면 이쪽.
  - `@pilot-evaluator` — 요구사항 충족·게이트 통과 **판정**. 사이클의 일부.
  - 내장 `/security-review` — 심층 보안 패스. 보안이 중요한 변경에 별도 권장.

### `@pilot-code-review` 에이전트 (`pilot/agents/pilot-code-review.md` — 이 파일이 SSOT)

**사이클·orchestrate-load 와 독립** — 4 벌 wrapper 가 공유하는 공통 프로토콜을 사용하지 않는 self-contained 에이전트다 (`pilot/agents/pilot-code-review.md:7·12`, `pilot/skills/context/shared/wrapper-protocol.md:5`). 호출자가 넘긴 target 을 그대로 쓴다. 도구는 `Read, Glob, Grep, Bash` (`:4`).

1. **대상 확정** (`:14`) — **uncommitted 우선** (`git diff --stat HEAD` + `git diff HEAD`), 비어 있으면 브랜치 커밋 범위 (`git diff @{u}..HEAD` 또는 `git diff $(git merge-base HEAD main)..HEAD`). diff 가 완전히 비면 "리뷰할 변경분이 없습니다." 후 종료.
2. **언어 감지** (`:16`) — 변경 파일 확장자로 언어 집합 도출. 매핑에 없으면 baseline 만.
3. **규칙 로드** (`:18-21`) — **항상** `shared/review-principles.md` Read (baseline 루브릭) + 감지 언어별 `workspace/context/review/{lang}.md` 존재 시 Read. 그 파일 상단에 `lint:` 줄이 있으면 해당 언어 변경 파일 경로로 Bash 1 회 실행해 findings 판단에 반영 (줄이 없으면 lint 미실행).
4. **현재 feature 파악 (라우팅용)** (`:23`) — STATE.md → 진행중 프로젝트 → `project.md` 의 미체크 feature. 여럿이면 변경분과 가장 직접 관련된 1 개, **판별이 어려우면 번호를 추정하지 말고** `feature` 라우팅을 "feature 명세 점검 필요" 로 일반화한다. 파일 부재·파싱 실패해도 리뷰는 계속.
5. **리뷰** (`:25-29`) — 결함마다 severity (`blocking`/`suggestion`/`nit`, 격상 기준은 `review-principles.md`, **취향·스타일 차이는 올리지 않는다**) · 근거 `file:line` · 개선안 · 재진입 라우팅 1 개. 모호하면 **보수적으로 상향** (trivial→generator→planner→feature). 요구사항 충족 판정 영역 finding 은 `dismiss` + "evaluator 책임 영역" 명시. **변경분 밖의 기존 코드는 지적하지 않는다.**
6. **[필수] CODE REVIEW REPORT 출력** (`:31-56`) — `target` · `languages` · `summary: blocking N · suggestion N · nit N` · `findings` · `routing` 6 행 (full-cycle feature 부터 / full-cycle planner 부터 / one-shot generator 1 회 / trivial 일괄 커밋 / new-feature / dismiss) · `다음:` 안내. 결함 없으면 findings `- none`, routing 6 행 모두 `none`. **에이전트가 코드를 직접 고치지 않는다.**

**탐색 제약** (`:62`): 리뷰 범위는 이번 변경분 + 결함 판단에 필요한 직접 의존 경로로 한정. 변경분과 무관한 광역 탐색은 하지 않는다.

---

## `/pilot:code-review-init`

워크스페이스의 언어별 코드 리뷰 룰 파일 `workspace/context/review/{lang}.md` 를 1 회성 셋업한다 (`pilot/skills/code-review-init/SKILL.md:12`).

- **사전 확인** — P 라벨 없는 자체 확인 (`pilot/skills/code-review-init/SKILL.md:16-20`):
  1. `$ARGUMENTS` 첫 토큰을 `{lang}` 슬러그로 사용. 비어있으면 `git ls-files | awk -F. '{print $NF}' | sort | uniq -c | sort -rn | head -5` 로 dominant 확장자를 감지해 추론 (`.py→python`·`.ts/.tsx→typescript`·`.rb→ruby` 등, 매칭 없으면 질의) 후 "**{추정 lang} 로 진행할까요?**" 확인.
  2. `workspace/context/` 없으면 `messages.md` 의 `workspace_missing` 안내 후 종료 (활성 프로젝트가 아니라 workspace 존재만 확인 — `pilot/skills/context/shared/preamble.md:98`).
  3. 대상 경로 폴더 없으면 생성. **이미 존재하면 사용자 확인 없이 덮어쓰지 않는다** — "덮어쓰기 / 백업 후 새로 생성(`{경로}.bak.{timestamp}`) / 취소" 질의.
- **시작 전략 3 종 — 택 1 질의** (`pilot/skills/code-review-init/SKILL.md:22-34`):
  - **A. 사전 작성된 예시 복사** (`:24-26`) — `${CLAUDE_PLUGIN_ROOT}/examples/code-review/{lang}.md` **존재 시만 제시** (부재 시 비활성, B/C 만). 헤더 안내 블록 제거 → 사용 프레임워크 확인 (ruby→Rails · php→Laravel/Symfony · kotlin→Android/서버사이드 · java→Spring · js/ts→React 등) → 미사용 프레임워크 섹션 제거 → Write. 제공 예시 7 종: `java`·`javascript`·`kotlin`·`php`·`python`·`ruby`·`typescript` (`pilot/examples/code-review/`).
  - **B. 빈 형식 템플릿 복사** (`:28-30`) — `shared/review-rules-template.md` Read → 안내부 제거 → `{언어}` placeholder 치환 (lint 예시도 해당 언어로 또는 삭제) → Write → "본문의 관용구·결함 섹션을 직접 채우세요" 안내.
  - **C. AI 생성 (코드베이스 기반)** (`:32-34`) — `git ls-files | grep -E '\.({lang 확장자})$' | head -50` 로 상위 파일 Read 해 컨벤션 (logger·테스트 프레임워크·DI·ORM) 파악 → 템플릿 형식에 반영 → **미리보기 제시 후 "이대로 저장/수정 후 저장/취소" 질의**. **자동 저장 금지**, LLM 추측 기반 draft 임을 명시.
- **결과 출력** (`pilot/skills/code-review-init/SKILL.md:36-38`): 생성 경로·전략·룰 섹션 수·유지된 프레임워크 섹션 + 다음 단계 (본문 검토·편집 → `/pilot:pilot-review` 실행 시 자동 로드).
- **Do-NOT** (`pilot/skills/code-review-init/SKILL.md:40-45`): 사용자 확인 없는 덮어쓰기 금지 · 전략 C 자동 저장 금지 · 생성 룰의 정확성 보증 안 함 (사용자 책임, draft 도우미) · `workspace/` 외부 경로 Write 금지.
- **호출 시점** (`pilot/skills/code-review-init/SKILL.md:47-50`): `/pilot:pilot-review` 결과에서 `{lang}.md` 부재로 baseline 만 적용됐음을 인지했을 때 사용자가 명시 호출 · 새 언어 도입 시 선제 호출 · `/pilot:pilot-init` 후 주력 언어 셋업.
