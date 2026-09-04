# #27 경로 트리거 — 소스 파일을 건드리는 순간 도메인 포인터 로드

> source: prompt
> created: 2026-09-04T02:50:24Z
> user_prompt: "feature 생성해줘 — docs/superpowers/plans/2026-09-04-context-retrieval-feature-plan.md §4 F-C 등록"
> plan: `docs/superpowers/plans/2026-09-04-context-retrieval-feature-plan.md` § F-C (설계 상세·근거 SSOT. §2 P3 패턴, 부록 B 하네스 근거)

## 요구사항

- **조건**: #26 머지 — 도메인별 `sources` frontmatter 가 있다. 없으면 지식 파일 인용 경로의 공통 디렉토리 접두로 glob 을 추정(INFO 표기). **선행 검증(실측) 완료 후 C1/C2 확정** — 실측 전에는 구현을 시작하지 않는다.
- **트리거**: 에이전트(주로 `@pilot-generator`) 가 `sources` glob 에 매칭되는 소스 파일을 Read/Edit/Write 한다.
- **기대결과**:
  - 해당 도메인의 **포인터 3~8줄**(진입 index 1 · `type` 이 rules·services·enums 인 본문 최대 3 · 경계 문서 최대 2 · `context-search` 사용 1줄) 이 컨텍스트에 나타난다. 본문 복사는 없다. SSOT 는 `workspace/context/` 에 그대로.
  - **C1 (기본, 하네스 네이티브)**: `/pilot:learn` Phase 5 가 `.claude/rules/pilot-{domain}.md` 를 생성 — frontmatter `paths:` = `sources` glob, 본문 = 관리 마커 `<!-- managed by /pilot:learn — 수동 편집 금지. 재생성으로 갱신 -->` + 포인터. Claude Code 조건부 규칙이 매칭 파일 Read/Edit/Write 시 자동 로드.
  - **C2 (대체, 플러그인 훅)**: `pilot/hooks/hooks.json` `PostToolUse` (matcher `Edit|Write|Read`) 스크립트가 `tool_input.file_path` → 도메인 판정 → `{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"<포인터 3줄>"}}` 출력. 같은 턴·같은 도메인 1회, 총 500자, 실행 100ms 이내.
  - doctor: 포인터 경로 존재 검증 · 도메인 삭제 후 남은 규칙 파일(stale) WARN · `paths` ↔ `sources` 불일치 INFO.

## 상태 전환

_(없음)_

## 비즈니스 규칙

- **포인터만.** 지식 본문을 규칙 파일이나 additionalContext 에 복사하지 않는다. 초과 항목은 "그 외 N개 — index 참조".
- **규칙 파일은 파생물** — `/pilot:learn` 재실행으로 언제든 재생성. **관리 마커가 있는 파일만 덮어쓴다.** 마커 없는(사용자 수정) 파일은 건드리지 않고 INFO.
- **선행 검증 절차(필수, 계획서 § F-C)**: 규칙 파일 1개 생성 → 래퍼(서브에이전트) 로 매칭 경로 파일을 Read 하는 최소 작업 실행 → 래퍼 응답에 규칙 본문 반영 여부 확인. 결과(성공/실패·하네스 버전) 를 **이 feature 본문 § 실측 기록** 에 남긴 뒤 C1/C2 확정 (Open Q (d) 확정: 실측 후 결정). 소스 정황 — `attachments.ts` 의 `nested_memory` 첨부가 메인/서브 공통 첨부 목록(`:872`) 에 있어 발화가 기대되지만 실측 전 확정 금지.
- 규칙 파일 위치는 `workspace/` 와 같은 저장소 루트의 `.claude/rules/` 한 곳 (모노레포 다층 `.claude` 여도 1곳).
- C2 채택 시 hooks.json 매처 추가는 기존 `PreToolUse Edit|Write`(scope-guard) 와 독립 — 차단 훅과 컨텍스트 훅을 섞지 않는다.

## 예외 케이스

- 한 소스 파일이 여러 도메인 `sources` 에 매칭 → 최대 2 도메인 포인터 + "그 외 N".
- `sources` 없는 도메인 → 인용 경로 공통 접두 glob 추정 + INFO 로 추정 사실 표기. 추정 불가(인용 0건) → 규칙 파일 생성 skip + INFO.
- 매칭 실패(C2) → 침묵(exit 0, 출력 없음).
- 규칙 파일이 gitignore 대상 디렉토리에 놓임 → 하네스가 로드하지 않음 — doctor 가 `.gitignore` 매칭 시 WARN.
- 실측 결과 C1 미발화 + C2 도 훅 미지원 환경(예: 하네스 버전 차) → 본 feature 는 "규칙 파일 생성만" 으로 축소하고 사람이 직접 Read 하는 용도로 남긴다 (사용자 확인 후).

## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- [ ] Claude Code 조건부 규칙(`.claude/rules/*.md` `paths:`) 이 래퍼 **서브에이전트** 실행 중에도 로드되는지 공식 spec 부재 — 위 선행 검증 절차로 실측 (2026-09-04 사용자 결정: 실측 후 결정 → 이월)

### (d) 비즈니스 결정 영역
- [x] C1(.claude/rules paths) vs C2(PostToolUse 훅) → 실측 후 결정. (c) 실측이 발화면 C1, 미발화면 C2 (2026-09-04 사용자 확정)

## 실측 기록

_(선행 검증 수행 후 기입 — 일자 · Claude Code 버전 · 절차 · 결과 · C1/C2 확정)_

## 검증 기준

- `/pilot:learn` 골든 출력에 규칙 파일 1개 (frontmatter `paths` 3줄 이내 + 마커 + 포인터 ≤8줄).
- 관리 마커 보존 테스트: 마커 제거한 규칙 파일은 재생성 시 무변경 + INFO.
- doctor 테스트: stale 규칙 파일 WARN · 포인터 경로 부재 WARN · `paths`↔`sources` 불일치 INFO.
- C2 시: 훅 스크립트 단위 테스트(매칭·비매칭·다중 도메인·상한 500자) + hooks.json 스키마 확인.
- dogfooding: 후속 feature 사이클에서 generator 가 `pilot/skills/**` 수정 시 `pilot` 도메인 포인터가 나타난 기록.

## 관련 파일 범위

- **변경**: `pilot/skills/learn/SKILL.md` Phase 5 (`:75`) — `.claude/rules/pilot-{domain}.md` 생성 단계 (C1) · `references/heuristics.md` 포인터 선정 규칙
- **변경**: `pilot/tools/doctor/integrity.py` `check_workspace` (`:320`) — 규칙 파일 검증 3종
- **C2 시 신규**: `pilot/hooks/context-pointer.sh` · `pilot/hooks/hooks.json` `PostToolUse` `Edit|Write|Read` 매처 · `pilot/tests/tools/test_context_pointer.py`
- **참조**: `pilot/hooks/scope-guard.sh:10` (stdin JSON 파싱 패턴) · `pilot/skills/context/lifecycle/setup/templates/` (init 시 `.claude/rules/` 안내 필요 여부)
- **문서**: `pilot/docs/explanation/workspace-layout.md` — 파생물 `.claude/rules/pilot-*.md` 행 추가
