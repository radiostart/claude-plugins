# 구현 계획: #19 정비 rewrite — 원칙 중심 재작성

> 모드: standard (tdd: false, mode: null) · 작성: 2026-07-24 planner
> 근거 SSOT: `docs/audits/2026-07-24-audit-3-instruction-excess.md` (스킬·에이전트별 불변 조건 체크리스트 = 재작성 검증 기준) / `2026-07-24-audit-2-duplication.md` § A (16 클러스터 정본 지정) / `docs/superpowers/specs/2026-07-24-pilot-skill-consolidation-design.md` § 1 (성공 기준)
> 전제: #18 prune 완료 (a18a429) — 삭제·B-드리프트 정정 확정 베이스. B-9 INFO 문구는 3곳 통일 완료 상태를 유지한다.
>
> **우선순위 규칙 (충돌 시)**: ① 감사 축 3 불변 조건 체크리스트 (전 항목 보존 — feature spec 명시) > ② 감사 축 2 정본 통합 제안 > ③ 100줄 목표. 예: issue 의 "P2 1행 교체" 는 A-1 중복이자 축 3 불변 — 요지 1줄 + preamble P2 참조로 보존한다 (통째 삭제 금지).
> **Open Q (d) 결정 확정 (2026-07-24 사용자)**: learn 은 **소폭 초과 ~120줄 허용** (references/ 분리 안 함). 스텝 2-b 착수 보류 해제 — feature spec (d) 체크 완료.
> **critic 합의 반영 (2026-07-25, `.plan.critic.md` C1~C7 전건 accepted)**: C1 사용자 재결정 — 총량 게이트 ≤3,680줄 완화 (#19 단독 감축률 약 27~28% 정직 기재, spec 30~35% 는 #20 합산 판정, lifecycle 문서 축소 미편입). C2 wrapper 잔류 최소 셋 4항 확장 (wrapper-protocol Read 지시). C3 autopilot grep 토큰 분리 교체. C4 frontmatter diff base 고정 (a18a429) + 최종 게이트 재검. C5 A-9·A-7 소비처 4곳 스텝 1 편입. C6 16항 정정. C7 pytest 경로 정정.

### 변경 파일

**스텝 1 — 정본 신설·context 재편**

- [x] `pilot/skills/context/shared/wrapper-protocol.md` — **신설** (A-2 정본): wrapper 공통 계약 (경고문·톤 SSOT 링크·경로 규칙·orchestrate-load 반환 JSON 처리·domain null 예외·상태 카테고리 부분 로드·drift/scope-exploration 공통 참조). "각 wrapper 잔류 최소 셋 = **4항**: ① [불변] 선언 ② orchestrate-load bash 블록 ③ error 종료 1줄 ④ **wrapper-protocol.md 를 Read 하고 그 계약을 따른다는 필수 지시 1줄**" 규칙을 본문에 명시 (critic C2 — orchestrate-load 의 files_to_read 는 이 파일을 반환하지 않으므로 (#19 Python 무변경), Read 지시 없이는 이동된 계약이 성공 경로에서 유실된다)
- [x] `pilot/skills/context/shared/guardrails.md` — § A2 runtime fallback 정의 신설 (A-15: "단계 실패 시 abort 금지 — default fallback + WARN/INFO 1줄 후 계속". 사용처 12곳+ 은 `(A2)` 표기만) + § 자동 체인 금지 원칙 선언 승격 (A-16: 에이전트·스킬은 다음 phase 를 자동 호출하지 않는다 — 시작점은 사용자 명시 호출, autopilot 만 opt-in 예외)
- [x] `pilot/skills/context/shared/preamble.md` — P1 정의부에 `workspace_missing` 케이스 보강 (B-6 부수: STATE.md 자체 부재 → messages.md `workspace_missing` 출력 후 종료 — `no_active_project`/`state_corrupt` 와 구분) + 스킬별 P 절차 적용표에 `code-review-init`·`review` 행 추가 (B-7 부수 — 각 SKILL.md 의 현행 사전 확인 선언과 일치하는 마크로)
- [x] `pilot/skills/context/shared/messages.md` — § Slack 발송 계약 1줄 신설 (A-8 정본: notifier 는 항상 exit 0·no-op 이어도 호출·실패 비차단)
- [x] `pilot/skills/context/INDEX.md` — 재작성 151 → ~60줄 (실측 82줄): STATE.md 갱신 규칙 → preamble P2 참조 (A-1), 프로젝트 폴더 트리 → projects/GUIDE.md 참조 (A-12 완전 통합), 에이전트 표 → wrapper-protocol/rgr 참조. **보존 앵커**: preamble P3 가 인용하는 "도메인별 컨텍스트 로딩" 규칙 (MANIFEST 우선 로드 + 경로 컨트랙트 표 + boundaries 글롭), docs/ 접근 규칙 (confl 계약 — 구조적 예외 2스킬 표), Fallback 표, 코드 생성 정책 (coding.md 로드)
- [x] `pilot/skills/doctor/SKILL.md` — A-9 정본 절 신설 (실측 63→46줄) ("임베디드 호출 시 출력 규칙": 다른 스킬이 doctor 를 마지막 단계로 실행할 때 ERROR/WARN 원문 출력·비차단) + 자체 축약 63 → ~55줄 (L50-56 "언제 실행하나" 삭제 — description 중복). `:46` "#20 validate.yml 신설 예정" 문구는 보존 (#18 전달사항 — #20 이 재갱신)
- [x] A-9·A-7 소비처 참조 교체 4곳 (critic C5 — 정본 통합 완결, A-9 절 신설과 동일 커밋): `pilot/skills/context/modes/tdd-activation.md:238-239` (A-9 → doctor SKILL 신설 절 참조) · `pilot/skills/analyze/references/prompts-update.md:196` (A-9 — 산식 밖 references/ 이지만 통합 완결성 차원 포함) · `pilot/skills/context/lifecycle/plan-schema.md:18` (A-7 → modes/characterize.md:10 참조) · `pilot/skills/context/lifecycle/state-schema.md:69` (A-7 동일)

**스텝 2 — 스킬 군별 재작성 (17개 중 13개 실변경, 군별 커밋)**

- [x] 2-a 앵커 결합군 (동일 커밋 — 실측 analyze 100·project 87·create-feature 76줄): `pilot/skills/analyze/SKILL.md` 202→~95 · `pilot/skills/project/SKILL.md` 170→~95 · `pilot/skills/create-feature/SKILL.md` 180→~85 — 단계 번호 앵커 (analyze 1~8·5-1·5-2·6-5) **번호 체계 불변** 결정. project:138·142 "분석 프로세스 1~5/6~7", create-feature:126 "5~6 단계"·:135 "6-5 단계" 인용 원문 유지. A-4 (interview.md)·A-5 (open-questions.md) 재서술 → 발동 조건·상한 (단건 4/일괄 8)·순서만 잔류
- [x] 2-b learn (단독 커밋 — 실측 109줄): `pilot/skills/learn/SKILL.md` 207 → **~120줄** (소폭 초과 허용 — 2026-07-24 사용자 결정, references/ 분리 안 함) — 실측 기반 규칙 전 항목 보존 (축 3 learn 체크리스트 16항 (critic C6 실측 정정): 1/2 rejection·폴더-suffix 미strip·≤10 자동 skip·Abort cleanup·MANIFEST H2 정규식 `^##\s+도메인\s*분류\s*$` 원문·boundary 계약 등)
- [x] 2-c 기계 계약군 (실측 autopilot 82·tdd 51·characterize 29줄): `pilot/skills/autopilot/SKILL.md` 198→~85 (auto_pilot.py CLI 3종·retry `{R}` +1 규칙·hard-stop enum 5종 원문 보존) · `pilot/skills/tdd/SKILL.md` 92→~60 (**A-6**: Detect literal 4종 하드코드 (:59·:75-79) → tdd-activation.md 참조로 교체, off 완료 블록 (:45-49) 축자 중복 제거 — literal 원문은 tdd-activation.md 에만 존재하게) · `pilot/skills/characterize/SKILL.md` 56→~35 (A-7: 우선순위 규칙 → modes/characterize.md:10 참조)
- [x] 2-d 절차 스킬군 (실측 pr 62·confl 73·slack 66·init 51·code-review-init 50·focus 56줄): `pilot/skills/pr/SKILL.md` 170→~80 (**A-13**: 최소 본문 규칙 20줄 → shared/pr.md § 3 참조 1줄, 예시 흐름 2종 삭제, base 결정 트리 → 산문) · `pilot/skills/confl/SKILL.md` 155→~75 (모드 판별·서브커맨드·출처 태그·원문 보존 원칙 유지) · `pilot/skills/slack/SKILL.md` 134→~75 (messages.md 키 6종·0600·CRITICAL 중단 계약 유지) · `pilot/skills/init/SKILL.md` 125→~75 (**config 표 헤더 리터럴 4종 원문 보존** — doctor strict 검증 키) · `pilot/skills/code-review-init/SKILL.md` 121→~65 · `pilot/skills/focus/SKILL.md` 102→~55
- [x] 무변경~경미 (완성형 3종): `pilot/skills/commit/SKILL.md` (22줄 — 재작성 참조 모델, 무변경) · `pilot/skills/issue/SKILL.md` (33줄, 무변경 — P2 재서술은 "요지 1줄+참조"로 이미 최소형) · `pilot/skills/review/SKILL.md` (41→39줄, `---` 구분선 스타일 정리만 — A-10/A-1 잔여 재서술 없음 확인)
- [x] A-10 공통 적용 (2-a~2-d 에 분산): P1 실패 메시지 재서술 8곳 (analyze·autopilot·characterize·confl·create-feature·focus·slack·tdd) → "preamble P1" 참조로 교체

**스텝 3 — 에이전트 5개 + 총량 검증·마무리**

- [x] `pilot/agents/pilot-planner.md` 134→~90 (실측 92·critic 126→~85 실측 86·generator 56→~50 실측 49·evaluator 88→~75 실측 77줄) · `pilot/agents/pilot-planner-critic.md` 126→~85 · `pilot/agents/pilot-generator.md` 56→~50 · `pilot/agents/pilot-evaluator.md` 88→~75 — 4벌 wrapper 헤더 → wrapper-protocol.md 참조 (A-2, 잔류 최소 셋 유지) + 모드 분기 → plan-schema.md § 모드 결정 참조 (A-3) + Slack exit-0 부연 → messages.md 참조 (A-8) + critic 의 A-11 (identity forbid 재서술)·A-14 (선택 호출 재서술) 참조화. **계약 보존 우선 — 축 3 에이전트 체크리스트 한도 밖 축약 금지.** evaluator 의 VERIFICATION REPORT 블록 (`status: READY | NOT_READY`·gates 6종·issues_to_fix 규칙) 원문 불변
- [x] `pilot/agents/pilot-code-review.md` 88→~70 (실측 62줄) — self-contained 유지 (orchestrate-load 미사용 — **wrapper-protocol 적용 대상 아님**), diff 수집 4종 나열 → 원칙 압축, 라우팅 enum 6종·REPORT 블록 원문 불변
- [x] `pilot/skills/context/lifecycle/projects/prompts-scaffold-notes.md` · `pilot/skills/context/lifecycle/projects/GUIDE.md` — 전수 grep 결과 두 파일 모두 재작성 대상 SKILL.md/agents 줄번호 인용 없음(재고정 불요, 확인만). `plan-schema.md:30` 의 `agents/pilot-planner.md` 줄번호 인용은 66-104→64-88 로 2 회 재고정 (spec 예외 케이스) **만** 수행. lifecycle 문서 추가 축약은 편입하지 않음 (critic C1 사용자 재결정 — 불변 조건 체크리스트가 없는 영역의 무감사 축약 금지)
- [x] `pilot/docs/tutorial/getting-started.md` — 대조 완료, 진짜 모순 없음(behavior 불변, wording 만 압축) — #00 선례("wording 차이 ≠ 회귀")에 따라 무변경. 유일한 미세 드리프트(learn Phase 2 게이트 "그대로 진행"→"진행")는 튜토리얼 산문 성격상 갱신 불요로 판단

### 구현 순서

1. **정본 신설·context 재편** — 소비처 참조 교체 (스텝 2·3) 전에 정본이 먼저 존재해야 죽은 참조가 안 생긴다 (#18 과 동일한 선행 원리).
   - wrapper-protocol.md 신설 → guardrails (A2·자동 체인 금지) → preamble (P1 보강·적용표 2행) → messages (Slack 계약) → INDEX.md 재작성 → doctor SKILL (A-9 절 신설 + 자체 축약).
   - INDEX.md 재작성 시 preamble P3 앵커 ("도메인별 컨텍스트 로딩") 섹션명을 유지하거나 preamble P3 인용부를 동일 커밋에서 함께 수정.
   - **게이트 1**: ① `python3 pilot/tools/docs_build.py` 정상 + `python3 -m pytest pilot/tests/tools/test_doc_links.py pilot/tests/tools/test_docs_build.py` 통과 (깨진 링크 0 — 경로 critic C7 정정) ② `git grep -n "A2" pilot/skills/context/shared/guardrails.md` 정의 존재 ③ `git grep -n "workspace_missing" pilot/skills/context/shared/preamble.md` 존재 ④ 적용표에 code-review-init·review 행 존재 ⑤ `python3 pilot/tools/doctor.py workspace` 클린.

2. **스킬 군별 재작성** — 군별 독립 커밋 (2-a 앵커군 → 2-b learn → 2-c 기계 계약군 → 2-d 절차군). 각 군의 작업 원리: "위임 후 본문에 남은 중복 요약 제거" (감사 축 3 공통 관찰) — 정본 링크가 이미 있는 재서술을 지우고, 없는 것은 스텝 1 정본으로 참조 교체. 축 3 의 해당 스킬 **불변 조건 체크리스트를 재작성 후 항목별 대조**하고 대조 결과를 커밋 메시지 본문 또는 PR 설명에 기록한다.
   - **게이트 2 (군별 반복)**: ① `wc -l` — 해당 군 전 스킬 ≤100줄 (learn 만 ≤120줄 — 2026-07-24 사용자 결정) ② 문자열 계약 grep — 앵커군: `git grep -n "분석 프로세스" pilot/skills/{project,create-feature}/SKILL.md` 매칭 유지 + analyze 단계 헤더 (5-1·5-2·6-5) 존재 / 기계 계약군: Detect literal 4종이 `modes/tdd-activation.md` 에 원문 존재 + `git grep -c "Red 계약 작성" pilot/skills/tdd/SKILL.md` = 0 (하드코드 제거 확인) + auto_pilot.py CLI 계약 **토큰 분리 grep** (critic C3 — 현행 본문이 `\` 줄바꿈 표기라 단일행 grep 은 재작성 전에도 매칭 실패): `for t in "--phase planner" "--plan-valid" "--phase critic" "--critic-file" "--phase evaluator" "--report-file" "--retries-used"; do git grep -q -e "$t" pilot/skills/autopilot/SKILL.md || echo "MISSING: $t"; done` → 출력 없음 (토큰별 개별 판정 — 다중 `-e` 의 `-c` 는 합산 카운트라 각 토큰 ≥1 판정 불가. `--retries-used {R}` 는 축 3 CLI 3종 계약의 일부) / learn: `git grep -n '\^##' pilot/skills/learn/SKILL.md` 로 MANIFEST H2 정규식 원문 확인 / 절차군: init 의 config 표 헤더 리터럴 (`| 언어 | 의존성 추출 패턴 |`·`| 역할 | 식별 패턴 |`·`| scope 헤더 | project.md 대상 H3 | 표 헤더 |`·`| 패턴 | 사유 |`) 원문 grep + confluence.py 서브커맨드 4종 유지 ③ frontmatter description diff 없음 — **base 고정** (critic C4: base 없는 diff 는 군별 커밋 후 false pass): `git diff -U0 a18a429..HEAD -- 'pilot/skills/*/SKILL.md' | grep '^[-+]description'` 이 비어야 함 (a18a429 = #18 완료 커밋 — 스텝 1 의 doctor/SKILL.md 포함 전 구간 커버) ④ docs_build + test_doc_links 통과.

3. **에이전트 재작성 + 총량 검증·인용 재고정·최종 게이트** — agents 는 wrapper-protocol (스텝 1)·모드 표·Slack 계약 참조가 전제라 마지막.
   - agents 5개 → prompts-scaffold-notes·GUIDE.md 인용 재고정 → getting-started.md 캡처 대조 → 총량 실측.
   - **게이트 3 (에이전트)**: ① 축 3 에이전트 체크리스트 전항 대조 ② `grep -n "VERIFICATION REPORT" pilot/agents/pilot-evaluator.md` + `status: READY | NOT_READY` 원문 존재 ③ 4벌 wrapper 각각에 orchestrate-load bash 블록 + [불변] 선언 + **wrapper-protocol.md Read 지시** 잔류 확인 (critic C2 — `git grep -c "wrapper-protocol" pilot/agents/pilot-{planner,planner-critic,generator,evaluator}.md` 각 ≥1) ④ pilot-code-review 에 wrapper-protocol 참조 **부재** 확인 (self-contained 오염 방지).
   - **최종 게이트 (사이클 공통 + #19 고유)**: ① `python3 -m pytest pilot/tests` 전체 통과 ② `python3 pilot/tools/doctor.py workspace` 클린 ③ `python3 pilot/tools/docs_build.py` + test_doc_links 통과 ④ **총량 산식** — `cat pilot/skills/*/SKILL.md | wc -l` (기준 2,071) + `cat pilot/agents/*.md | wc -l` (기준 492) + `find pilot/skills/context -name "*.md" ! -path "*example*" | xargs cat | wc -l` (기준 2,245) = 현 4,808 → **사후 합계 ≤ 3,680줄** (critic C1 사용자 재결정 2026-07-25 — plan 스텝별 목표 합산으로 산식이 닫히는 값. **#19 단독 감축률 약 27~28%** 로 정직 기재. spec 의 30~35% 는 #20 의 지시문 이관·정리 감축과 **합산해 판정**한다. lifecycle 문서 축소 미편입 — 미달 시 무감사 추가 축약 금지, 사용자 보고) ⑤ `references/` 로의 본문 이동은 감축으로 계상 금지 (산식 밖 이동 = 명목 감축·컨텍스트 비용 동일 — 게이밍 방지) ⑥ frontmatter 재검 1회 (critic C4): `git diff -U0 a18a429..HEAD -- 'pilot/skills/*/SKILL.md' | grep '^[-+]description'` 빈 출력.

### 주의사항

- **(d) 결정 기록 — learn 소폭 초과 (~120줄) 허용 확정 (2026-07-24 사용자)**: 근거 ① learn 은 이미 references/ 2개 (heuristics 129·cross-domain 152) 로 위임 완료 — 잔존 본문 대부분이 불변 계약·실측 교정치 ② references/ 분리는 총량 산식 밖 이동이라 감축이 명목상일 뿐 로드 컨텍스트 비용 동일 + hop 1 추가 ③ agents "계약 보존 우선" (감사 결정 4) 과 정합. feature spec Open Questions (d) 체크 완료.
- **문자열 원문 계약 불변** (spec 비즈니스 규칙 — 한 글자도 변경 금지): preamble P-단계 참조 표기 · messages.md 키 (`workspace_missing`·`no_active_project`·`state_corrupt`·`confl_no_match`·`slack.*` 등) · CLI 호출 시그니처 (orchestrate-load / plan-validate / auto_pilot / slack-notify / doctor.py / confluence.py / init_detect) · TDD Detect literal 4종 · init config 표 헤더 리터럴 · evaluator VERIFICATION REPORT 블록. 게이트 2·3 의 grep 이 검증 수단.
- **정본 지정 재조사 금지**: 클러스터별 정본은 감사 축 2 § A 제안 그대로 (A-1 preamble P2 · A-3 plan-schema · A-4 interview.md · A-5 open-questions.md · A-6 tdd-activation · A-7 modes/characterize · A-9 doctor SKILL 신설 절 · A-10 preamble P1 · A-11 identity.yml · A-13 shared/pr.md § 3 · A-14 pilot-planner.md). 재작성 중 정본이 틀려 보이면 drift-protocol 보고 — 임의 변경 금지.
- **learn SKILL 의 MANIFEST 정규식 인용은 현행 wording 유지** (#06 인수인계 — SKILL 인용 `^##\s+도메인\s*분류\s*$` vs orchestrate-load.py:264 실제 `##\s*도메인\s*분류` 의 기존 drift 는 코드 보강 옵션과 함께 #20 영역. #19 에서 어느 쪽으로도 "정정" 하지 않는다).
- **open-questions.md ↔ interview.md ↔ scope-sync.md 5-2 규칙 2 의 3곳 동기화 계약 유지** (#17 인수인계): A-4·A-5 참조화 시 행 형식 (`- [ ] ` prefix·`→` 답변 요약)·카테고리를 변경하지 않는다 — 참조 교체만.
- **wrapper 자기완결성 (critic C2 반영 — 잔류 최소 셋 4항)**: [불변] step 1 규칙 (호출 프롬프트 무시·orchestrate-load 최우선) 은 wrapper 본문에 반드시 잔류 — wrapper-protocol.md 로만 이동하면 아직 읽지 않은 파일이 진입 규칙을 들고 있는 모순이 생긴다. 이동된 계약 (JSON 처리 상세·domain null 예외·부분 로드 규칙) 은 잔류 4항의 "wrapper-protocol.md Read 필수 지시 1줄" 을 통해서만 성공 경로에 도달한다 — orchestrate-load 는 무변경 (#20 영역) 이라 files_to_read 배선에 기대지 않는다.
- **게이트 grep 문자열은 실측 매칭 확인 후 기재** (#18 critic C2·본 critic C3 동일 유형 재발 방지): 줄바꿈 (`\`) 연속 표기·untracked 산출물 오탐 등으로 "계약 보존인데 게이트 fail" 이 나면 실행자가 게이트를 임의 완화하거나 본문을 불필요하게 재조판하는 부작용 경로가 열린다. generator 는 게이트 실행 전 대상 파일에서 패턴 1회 사전 검증.
- **frontmatter description 축약 금지** (spec 비즈니스 규칙 — 트리거 판단용). learn description 이 최장이지만 유지 판단은 별도 — 이번 범위에서 변경하지 않는다.
- **workspace/context/pilot/spec.md·index.md 의 SKILL 라인 인용은 재작성 후 전면 stale** — #19 에서 직접 수정하지 않는다 (drift-protocol § A — 직접 Edit 금지). PR 머지 후 `/pilot:learn` 재실행으로 재학습 (커밋 418868a 선례). evaluator 전달사항으로 이월 기록 권장.
- **workspace/projects/build-plugin/prompts/*.md 의 analyze-managed 라인 인용도 stale 예정** — 다음 `/pilot:analyze --regen-agents` 가 재정렬 (design § 5: workspace 산출물 정리는 범위 외).
- 새 기능 추가 금지 (정비 전용 — design § 5). 재작성 중 "개선 아이디어" 는 전달사항으로 기록만.
- generator 는 `project.md` `## 목표` 체크박스 수정 금지 (evaluator 단독 권한 — #03 인수인계).
- 커밋 분리: 스텝 1 (정본) / 2-a / 2-b / 2-c / 2-d / 스텝 3 (agents+마무리) — 군별 revert 단위 확보. 전체는 단일 PR (#18 과 같은 branch 흐름) 권장.

### 교차 의존

- feature #20 (정비 slim) — #19 의 지시문 반영을 diff 로 확인 후 스크립트 삭제·이관이 #20 의 전제. `doctor/SKILL.md:46` validate.yml 문구는 보존 → #20 이 validate.yml 신설 시 동일 커밋 재갱신. `docs_build.py` 의 `cleanup_stale_outputs` 는 #18 산출 — #19 재작성이 삭제하는 docs/reference stale 산출물 정리에 그대로 사용 (함수 제거 금지). memory-hint·diagnose·init_detect 의 SKILL 참조 문구는 #19 재작성 후에도 호출 계약 원문 유지 — #20 이 삭제·이관 시 호출처 문서와 동일 커밋으로 제거.
- #19 재작성 완료 후 정비 사이클 최종 검증 (파이프라인 1사이클 실완주 dogfooding) 은 #20 완료 뒤 일괄 (design § 4).
