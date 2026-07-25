# 감사 축 2 — 중복 지시 (원본 결과)

기준 경로: `pilot/` (이하 모든 인용은 이 경로 기준 상대 표기, 줄번호는 감사 시점 HEAD 실측)

## A. 중복 클러스터

### A-1. STATE.md 갱신 규칙 (P2)
- **주제**: 활성 프로젝트 행 갱신 방식 (1행 유지 vs 보류 누적)
- **발생 위치**:
  - `skills/context/shared/preamble.md:47` — "테이블 본문 전체 삭제 후 `| {mode} | {이름} | 진행중 |` 1 행만 추가" (정본)
  - `skills/context/shared/preamble.md:49` — "`보류`·`완료` 행을 누적하지 않는다"
  - `skills/context/INDEX.md:53` — "기존 `진행중` 행을 모두 `보류`로 변경 후 새 행을 추가한다" (**모순**)
  - `skills/project/SKILL.md:109` — "테이블 본문을 … 1행으로 교체. 기존 다른 이름 행은 모두 삭제 (이력은 git log)" (P2 참조하면서 본문 재서술)
  - `skills/issue/SKILL.md:30` — 동일 문장 재서술
- **제안 정본**: `preamble.md` P2 (project/issue 스킬 실동작과 일치, "절차 본문을 복제하지 않는다" 자체 선언 보유)
- **예상 절감**: 약 6줄 / **위험도**: **상** — 모순 드리프트 포함 (B-1)

### A-2. 에이전트 wrapper 공통 프로토콜
- **주제**: wrapper 헤더 4종 (경고·톤 SSOT·경로 규칙·[불변] step1) + orchestrate-load 호출 블록
- **발생 위치**: 사실상 동일 블록 4벌 — `agents/pilot-planner.md:8-24`, `agents/pilot-planner-critic.md:8-30`, `agents/pilot-generator.md:8-24`, `agents/pilot-evaluator.md:8-24`. 추가: `pilot-generator.md:26` ↔ `pilot-evaluator.md:26` "상태·유형 카테고리 부분 로드" 준동일 2벌
- **제안 정본**: 신설 `skills/context/shared/wrapper-protocol.md` (또는 `state-schema.md` 에 § wrapper 공통 계약). 각 wrapper 는 phase 명 + 링크 2~3줄만. 단 subagent 프롬프트는 자기완결성이 필요하므로 bash 블록 1개는 잔류 허용.
- **예상 절감**: 약 36줄 / **위험도**: 중 — 4벌 동시 수정 누락 시 드리프트 1순위 후보

### A-3. 모드 분기 매핑 (tdd/mode → standard·tdd·characterize)
- **발생 위치**: `plan-schema.md:10-18` (정본 표) / `pilot-planner.md:33-37` / `pilot-generator.md:38-41` / `pilot-evaluator.md:28-31` / `autopilot/SKILL.md:77-78`
- **제안 정본**: `plan-schema.md` § 모드 결정. 에이전트는 판정식 대신 표 참조.
- **예상 절감**: 약 8줄 / **위험도**: 중

### A-4. 조건부 인터뷰 절차 재요약 (wrapper 반복)
- **발생 위치**: `interview.md` 전체 (자칭 SSOT) / `create-feature/SKILL.md:112-120` 재서술 후 링크 / `analyze/SKILL.md:183-189` 재서술 후 링크 / 결과 리포트 문구 3벌 (`interview.md:68`·`analyze:193`·`create-feature:159`)
- **제안 정본**: `interview.md`. 호출 스킬에는 발동 시점 + 상한 값(4/8)만 잔류 (상한은 스킬별 파라미터).
- **예상 절감**: 약 12줄 / **위험도**: 중

### A-5. cross-domain detect + Open Questions 작성 재서술
- **발생 위치**: `open-questions.md:47-57` (정본) / `create-feature/SKILL.md:100-106` 알고리즘 재서술 / `create-feature:96` 4 카테고리 헤더 인라인 재나열 / `analyze/SKILL.md:167` 재서술
- **제안 정본**: `open-questions.md`. 스킬 쪽은 1줄 위임.
- **예상 절감**: 약 8줄 / **위험도**: 중 — INFO 문구 2종으로 이미 분기 (B-9)

### A-6. TDD Detect literal · on/off 완료 출력 블록
- **발생 위치**: `tdd-activation.md:51,88,104,118` (정본 literal 4종) / `tdd/SKILL.md:59,75-79` 동일 literal 하드코드 / `tdd/SKILL.md:45-49` ↔ `tdd-activation.md:197-201` off 완료 블록 축자 중복
- **제안 정본**: `tdd-activation.md`. tdd SKILL 은 참조로 교체.
- **예상 절감**: 약 10줄 / **위험도**: **상** — literal 이 한쪽만 바뀌면 `/pilot:tdd`·`--fix` 침묵 오판

### A-7. characterize 우선순위 규칙 (5벌)
- **발생 위치**: `modes/characterize.md:10` (정본) / `plan-schema.md:18` / `state-schema.md:69` / `characterize/SKILL.md:54` / `tdd/SKILL.md:13` (정본 포인터 불일치 — B-8)
- **예상 절감**: 약 3줄 / **위험도**: 하

### A-8. Slack notifier exit-0 계약 (3벌)
- **발생 위치**: `pilot-planner.md:64` / `pilot-evaluator.md:75` / `pr/SKILL.md:104`
- **제안 정본**: `messages.md` § Slack 발송 계약 1줄.
- **예상 절감**: 약 2줄 / **위험도**: 하

### A-9. doctor 후처리 출력 규칙 (4벌 축자)
- **발생 위치**: `project/SKILL.md:152-153` / `create-feature/SKILL.md:141` / `tdd-activation.md:238-239` / `analyze/references/prompts-update.md:196`
- **제안 정본**: `doctor/SKILL.md` 에 "임베디드 호출 시 출력 규칙" 절 신설 후 참조.
- **예상 절감**: 약 6줄 / **위험도**: 하

### A-10. P1 실패 메시지 재서술 (8곳)
- **발생 위치**: `preamble.md:33-36` (정본) 외 `analyze:26`·`autopilot:32-33`·`characterize:22`·`confl:21`·`create-feature:33`·`focus:35`·`slack:37`·`tdd:18`
- **제안 정본**: `preamble.md` P1 — 단 P1 정의부에 `workspace_missing` 케이스 누락, 정본 먼저 보강 (B-6).
- **예상 절감**: 약 10줄 / **위험도**: 중

### A-11. "취향·스타일 차이 blocking 격상 금지" (5벌)
- **발생 위치**: `identity.yml:35,49` (forbid 정본) / `pilot-planner-critic.md:67` / `pilot-code-review.md:42` / `review-principles.md:5`
- **예상 절감**: 약 3줄 / **위험도**: 하

### A-12. 프로젝트 폴더 구조 트리 (3벌)
- **발생 위치**: `projects/GUIDE.md:13-25` (정본 — `.plan.md` 행 포함 최신) / `INDEX.md:56-68` (`.plan.md` 행 없음 — 미세 드리프트) / `setup/README.md:60-78`
- **예상 절감**: 약 12줄 / **위험도**: 하~중

### A-13. PR 최소 본문 규칙 (도달 불가 fallback)
- **발생 위치**: `pr/SKILL.md:28-47` (20줄) — `shared/pr.md:45-57` § 3 과 실질 동일. `shared/pr.md` 는 플러그인 내장이라 "둘 다 부재"는 정상 설치에서 발생 불가.
- **제안 정본**: `shared/pr.md` § 3. SKILL 쪽은 1줄.
- **예상 절감**: 약 15줄 / **위험도**: 중

### A-14. critic 선택 호출·스킵 규칙 (3벌)
- **발생 위치**: `pilot-planner.md:66-72` (정본 — 절차 주체) / `pilot-planner-critic.md:122` / `autopilot/SKILL.md:181-189`
- **예상 절감**: 약 3줄 / **위험도**: 하

### A-15. "A2 fallback" 정책 — 정본 부재 상태의 분산 재정의 (12곳+)
- **발생 위치**: `init:54`·`project:67,75`·`interview.md:29,35`·`open-questions.md:14,57`·`tdd-activation.md:207`·`scope-sync.md:52,58,66,111,126` — **"A2" 정의 정본이 없음**, 사용처마다 괄호 재설명.
- **제안 정본**: `guardrails.md` 에 "§ A2 runtime fallback" 정의 1개 추가, 사용처는 `(A2)` 표기만.
- **예상 절감**: 약 6줄 / **위험도**: 중

### A-16. 자동 체인 금지 / 수동 명시 호출 기본
- **발생 위치**: `pilot-planner.md:66` / `pilot-generator.md:44` / `create-feature:170` / `autopilot:13-15,181-183` / `rgr.md:21` — phase 별 종료 지시는 기능적 반복이라 대부분 잔류 타당. 원칙 선언부만 guardrails 로 승격.
- **예상 절감**: 약 2줄 / **위험도**: 하

## B. 모순 드리프트 목록

| # | 주제 | 쌍 | 판정 (올바른 쪽 / 근거) |
|---|---|---|---|
| **B-1** | STATE.md 갱신 | `INDEX.md:53` "진행중 행을 보류로 변경 후 추가" ↔ `preamble.md:47-49` "1행만, 누적 금지" | **preamble 현행.** project·issue 실동작 일치. INDEX 는 P2 이전 구규칙 잔존 |
| **B-2** | TDD 에서 planner 역할 | `INDEX.md:109,117`·`analyze/SKILL.md:202` "planner 가 실패 테스트 작성" ↔ `rgr.md:30-34,46` "Planner 는 테스트 코드를 쓰지 않는다, Red 작성은 Generator" | **rgr.md 현행.** pilot-planner.md:38·tdd-activation 템플릿 일치. Red-계약 도입 이전 서술 잔존 |
| **B-3** | feature 파일 필수 섹션 | `projects/GUIDE.md:173` 구템플릿 섹션명 ↔ `analyze:100-115`·`create-feature:75-96` 현행 4섹션 + Open Questions | **analyze·create-feature 현행** (생성기·인터뷰(#17)·plan 검증이 소비) |
| **B-4** | pr_default_base fallback 체인 | `pr/SKILL.md:49` 같은 경로 2회 자기순환 오문 ↔ frontmatter·`state-schema.md:104` "state→config→develop" | **state-schema 체인이 올바름.** SKILL:49 는 오타성 드리프트 |
| **B-5** | wrapper 경로 표기 | `GUIDE.md:208`·`prompts-scaffold-notes.md:56` "`.claude/agents/…`" ↔ 동일 파일 내 "`${CLAUDE_PLUGIN_ROOT}/agents/…`" | **`${CLAUDE_PLUGIN_ROOT}/agents/` 올바름** — 플러그인화 이전 경로 잔존 |
| **B-6** | STATE.md 부재 시 동작 | `INDEX.md:137` "빈 테이블 생성 후 계속" ↔ 스킬 8곳 "workspace_missing 출력 후 종료" | **스킬·messages.md 현행.** 부수: preamble P1 정의부에 workspace_missing 케이스 누락 — 정본 보강 필요 |
| **B-7** | workspace 미초기화 메시지 | `code-review-init/SKILL.md:31` 자체 문구 ↔ `messages.md:20-22` `workspace_missing` 키 | **messages.md 정본.** code-review-init 이 key 미참조. 아울러 preamble 적용표(:67-83)에 `code-review-init`·`review` 행 부재 |
| **B-8** | characterize 우선순위 정본 포인터 | `tdd/SKILL.md:13` → characterize/SKILL.md ↔ 실제 정본 `modes/characterize.md:10` | 위임 사슬 한 단계 오지정 (내용 모순은 아직 없음) |
| **B-9** | cross-domain INFO 문구 | `open-questions.md:54` ↔ `analyze/SKILL.md:167` 문구 2종 | **open-questions.md 로 통일 권장** (소비·작성 규칙 SSOT) |

## C. 합계

16개 클러스터 총 예상 절감 **약 142줄**.

**우선 처리 권고 (위험도 상):**
1. **B-1/A-1** — `INDEX.md:50-54` STATE.md 규칙을 preamble P2 링크로 교체 (현재 규칙이 반대로 적혀 있음).
2. **B-2** — `INDEX.md:109,117`·`analyze/SKILL.md:202` 의 "planner 가 실패 테스트 작성" 문구를 rgr.md 역할 분담으로 정정.
3. **A-6** — `tdd/SKILL.md` 의 Detect literal 4종 하드코드를 tdd-activation 참조로 교체.

전반 평가: SSOT 선언 문화는 강함. 실제 위반의 주 패턴은 (1) 정본 링크를 걸면서 본문을 다시 요약하는 wrapper 반복(A-4·A-5·A-10), (2) 4벌 에이전트 wrapper 의 구조적 복제(A-2), (3) INDEX.md·projects/GUIDE.md 두 개관 문서의 구서술 잔존(B-1·B-2·B-3·B-5).
