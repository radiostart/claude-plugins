# pilot — Review skills

PR 이전, 사이클 내부에서 작성된 코드를 품질 관점으로 리뷰한다. 2 개 스킬: `pilot-review` `code-review-init`. evaluator 의 요구사항·게이트 판정과는 **별개 축** (`pilot/skills/pilot-review/SKILL.md:3-7`).

---

## `/pilot:pilot-review`

변경분 (git diff) 을 대상으로 `@pilot-code-review` 에이전트를 호출한다 (`pilot/skills/pilot-review/SKILL.md:12`).

- **target 결정** (`pilot/skills/pilot-review/SKILL.md:20-23`):
  - 인자 없음 → 변경분 전체 (uncommitted + 현재 브랜치 커밋)
  - 경로 인자 (예: `app/services/`) → 해당 경로 한정
  - 커밋 범위 인자 (예: `HEAD~3..HEAD`) → 해당 범위
- **동작** (`pilot/skills/pilot-review/SKILL.md:26`): 에이전트가 변경분을 수집해 언어별 규칙 + baseline 루브릭으로 리뷰하고 `CODE REVIEW REPORT` 출력. **코드는 수정하지 않으며**, 결함마다 재진입 라우팅 (`feature`/`planner`/`generator`/`trivial`/`new-feature`/`dismiss`) 을 제시해 사용자가 선택. REPORT 의 routing 요약이 trivial 일괄 커밋·one-shot 묶음·full-cycle 후보까지 안내. 상세 절차: `pilot/agents/pilot-code-review.md`.
- **언어별 규칙** (`pilot/skills/pilot-review/SKILL.md:32`): `workspace/context/review/{lang}.md` 존재 언어는 그 규칙 + plugin baseline, 부재 언어는 baseline 만. 템플릿: `pilot/skills/context/shared/review-rules-template.md`.
- **역할 경계** (`pilot/skills/pilot-review/SKILL.md:36-41`):
  - `/pilot:pilot-review` — 팀 규칙 파일 적용·사이클 재진입 라우팅이 필요한 리뷰.
  - 내장 `/code-review` — 범용 정확성 리뷰 (팀 규칙·라우팅 불필요 시).
  - `@pilot-evaluator` — 요구사항 충족·게이트 **판정** (사이클의 일부).
  - 내장 `/security-review` — 심층 보안 패스.

---

## `/pilot:code-review-init`

워크스페이스에 언어별 코드 리뷰 룰 파일 `workspace/context/review/{lang}.md` 를 1 회성 셋업 (`pilot/skills/code-review-init/SKILL.md:12`).

- **사전 확인** (`pilot/skills/code-review-init/SKILL.md:18-37`): P 라벨 없는 자체 확인 —
  1. `$ARGUMENTS` 첫 토큰 = `{lang}` 슬러그. 비어있으면 `git ls-files` dominant 확장자로 추론 후 사용자 확인.
  2. `workspace/context/` 부재 → `/pilot:pilot-init` 먼저 안내 후 종료.
  3. `workspace/context/review/` 없으면 생성.
  4. 대상 파일 기존재 시 → 덮어쓰기/백업 후 생성/취소 질의 (백업: `{경로}.bak.{timestamp}`).
- **시작 전략 3 종** (`pilot/skills/code-review-init/SKILL.md:41-85`) — 사용자 택 1:
  - **A. 예시 복사** — `${CLAUDE_PLUGIN_ROOT}/examples/code-review/{lang}.md` 존재 시. 프레임워크 확인 (Rails/Laravel/Spring/React 등) 후 미사용 섹션 제거.
  - **B. 빈 템플릿** — `review-rules-template.md` 본문만 남기고 placeholder 치환. 사용자가 직접 채움.
  - **C. AI 생성** — 코드베이스 상위 5~10 파일 Read 로 컨벤션 추출해 draft 생성. **자동 저장 금지** — 미리보기 → 사용자 승인 필수.
- **Do-NOT** (`pilot/skills/code-review-init/SKILL.md:108-113`): 사용자 확인 없는 덮어쓰기 금지 · 전략 C 자동 저장 금지 · 생성 룰 정확성 보증 안 함 (draft 도우미) · `workspace/` 외부 Write 금지.
- **호출 시점** (`pilot/skills/code-review-init/SKILL.md:117-121`): `/pilot:pilot-review` 에서 `{lang}.md` 부재 인지 후 · 새 언어 도입 시 · `/pilot:pilot-init` 후 주력 언어 셋업.
