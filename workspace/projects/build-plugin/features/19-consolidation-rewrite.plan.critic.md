# Plan Critic — #19 정비 rewrite — 원칙 중심 재작성

> 입력 plan: `features/19-consolidation-rewrite.plan.md` (검토 시각 2026-07-25)
> 입력 feature: `features/19-consolidation-rewrite.md`
> 페르소나: `personas.planner-critic` (red-team)
> focus 반영: 없음

## 챌린지

### C1 — 총량 게이트 ≤3,520 은 plan 자체의 스텝별 목표 합산으로 도달 불가 (~120~160줄 미달)
- **severity**: blocking
- **category**: premise
- **plan 인용**: 최종 게이트 ④ (`features/19-consolidation-rewrite.plan.md:50`) + 스텝 1~3 목표 줄수 전체 (:14-35)
- **챌린지**: plan 이 명시한 목표를 전부 최적 달성해도 산식이 안 닫힌다. 검산 — 스킬 목표 합 = 1,151줄 (2-a 95+95+85 · 2-b 120 · 2-c 85+60+35 · 2-d 80+75+75+75+65+55 · 스텝1 doctor 55 · 무변경 22+33+41), 에이전트 목표 합 = 370줄 (90+85+50+75+70). ≤3,520 이려면 context 는 2,245 → **1,999 (순감 246줄)** 이어야 한다. 그런데 plan 의 context 명시 감축은 INDEX 151→60 (-91) + GUIDE 271→~180 (**조건부** -91) = gross -182 뿐이고, 신설·보강 (wrapper-protocol +40~80 추정 · guardrails A2/자동체인 +~8 · preamble +~6 · messages +1) 이 +55~95줄 → **순감 ~88~128줄**. 예상 총합 3,640~3,680 으로 게이트를 **약 120~160줄 초과**한다. 감사 축 2 의 총 절감 추정도 142줄 (스킬·에이전트 절감분 포함) 이라 context 쪽 추가 여력을 뒷받침하지 않는다. 미달 시 보충 경로로 지목된 "lifecycle 문서의 중복 절" 은 감사 축 3 의 불변 조건 체크리스트가 **존재하지 않는 영역** — 여기서 ~150줄을 감사 없이 추가 축약하는 것은 사용자 확정 우선순위 ① (불변 체크리스트 > 총량) 이 경고하는 바로 그 경로다 (learn 총괄의 "자명해 보이는 줄이 실은 교정치" 리스크).
- **제안**: 셋 중 택일을 plan 에 명시 — (i) 총량 상한을 산식이 닫히는 값 (~3,680, 또는 "스킬 ≤1,160 · 에이전트 ≤375 · context 순감 ≥90" 분해식) 으로 재설정, (ii) lifecycle 문서 (state-schema 156 · GUIDE 잔여 · scaffold-notes 등) 추가 축약을 별도 불변 조건 식별 (미니 감사) 전제로 스텝 3 에 명시적 편성, (iii) wrapper-protocol.md 신설 분량 상한 (예: ≤60줄) 을 스텝 1 에 못박아 증가분 통제. 어느 쪽이든 사용자 재확인 필요 (게이트 수치는 사용자 확정 사항의 파생).

### C2 — wrapper "잔류 최소 셋" 에 wrapper-protocol.md Read 지시가 없어 이동된 계약이 런타임에 도달 불가
- **severity**: blocking
- **category**: edge-case
- **plan 인용**: 스텝 1 wrapper-protocol 신설 (`plan.md:14` — "잔류 최소 셋 = [불변] 선언 + orchestrate-load bash 블록 + error 종료 1줄") + 스텝 3 (:32) + 주의사항 wrapper 자기완결성 (:59)
- **챌린지**: 서브에이전트는 자기 agent 파일만 시스템 프롬프트로 받는다. orchestrate-load 의 `files_to_read` 에 wrapper-protocol.md 는 포함되지 않고 (본 세션 planner-critic phase 호출로 실측 — identity/instincts/guardrails/MANIFEST/project/prompts 만 반환), #19 는 Python 무변경 (#20 영역) 이라 배선 추가도 없다. 잔류 최소 셋을 문자 그대로 시행하면 wrapper 는 bash 실행 + error 종료만 알고, JSON 처리 규칙·domain null 예외·상태 카테고리 부분 로드는 **링크 뒤에 놓인 채 아무도 Read 하라고 지시받지 않는다**. 현행 wrapper 조차 "반환 JSON 의 instructions 를 따른다" 요지 1줄 + state-schema 참조를 인라인 유지 중이다 (`pilot/agents/pilot-planner.md:24`) — 최소 셋이 현행보다 좁다. orchestrate-load 실패 시 error 종료 잔류는 안전하지만, **성공 경로**에서 이동된 계약이 유실된다.
- **제안**: 잔류 최소 셋을 4항으로 확장 — ① [불변] 선언 ② bash 블록 ③ error 종료 1줄 ④ **"wrapper-protocol.md 를 Read 하고 그 계약을 따른다" 필수 지시 1줄** (또는 JSON 처리 요지 1줄 잔류). 게이트 3 ③ 에 "4벌 각각에 wrapper-protocol Read 지시 존재" grep 을 추가해 기계 검증.

### C3 — 게이트 2 ② autopilot 시그니처 grep 은 재작성 전 현재도 매칭 0 (달성 불가 게이트 — #18 C2 동류)
- **severity**: blocking
- **category**: premise
- **plan 인용**: 게이트 2 ② 기계 계약군 (`plan.md:45` — "auto_pilot.py 호출 시그니처 3종 (`--phase planner --plan-valid`·`--phase critic --critic-file`·`--phase evaluator --report-file`) 원문 유지")
- **챌린지**: 실측 — `pilot/skills/autopilot/SKILL.md:101-102` 는 `--phase critic \` + 줄바꿈 + `--critic-file …`, `:125-126` 은 `--phase evaluator \` + 줄바꿈 + `--report-file …` 로 표기돼 있어 단일행 문자열 grep 은 **현행 파일에서 이미 2/3 이 실패**한다 (`--phase planner --plan-valid` 만 :89 에서 단일행 매칭). 계약이 완벽 보존돼도 게이트가 fail 을 보고 → 실행자가 게이트를 임의 완화하거나 본문을 불필요하게 한 줄로 재조판하는 부작용 경로.
- **제안**: 토큰 분리 grep 으로 교체 — `git grep -c -e "--phase planner" -e "--plan-valid" -e "--phase critic" -e "--critic-file" -e "--phase evaluator" -e "--report-file" -e "--retries-used" pilot/skills/autopilot/SKILL.md` 각 토큰 ≥1. `--retries-used {R}` 도 축 3 autopilot 체크리스트의 CLI 3종 계약에 포함되므로 게이트에 추가.

### C4 — 게이트 2 ③ frontmatter diff 는 base 미지정 — 스텝 1 의 doctor 재작성은 어떤 게이트도 frontmatter 를 검사하지 않는다
- **severity**: blocking
- **category**: risk
- **plan 인용**: 게이트 2 ③ (`plan.md:45` — "`git diff -U0 -- pilot/skills/*/SKILL.md | grep "^[-+]description"` 이 비어야 함") + 스텝 1 doctor 항목 (:19) + 게이트 1 (:42)
- **챌린지**: base 없는 `git diff` 는 working tree vs HEAD — 군별 커밋 **후** 실행하면 빈 diff 로 무조건 통과 (false pass) 하고, 앞 군에서 커밋된 description 변경은 이후 어느 게이트도 못 잡는다 (최종 게이트에 frontmatter 재검 없음). 더 확실한 구멍: **doctor/SKILL.md 는 스텝 1 에서 재작성** (63→55) 되는데 게이트 1 에는 frontmatter 검사가 아예 없고, 게이트 2 시점에는 스텝 1 이 이미 커밋돼 diff 에서 사라진다 — 실행 순서를 완벽히 지켜도 doctor 의 frontmatter 는 검증 무풍지대다. "한 글자도 변경 금지" 계약 (spec 비즈니스 규칙) 의 유일한 기계 검증이 이 게이트다.
- **제안**: base 고정 — `git diff -U0 a18a429..HEAD -- 'pilot/skills/*/SKILL.md' | grep '^[-+]description'` (a18a429 = #18 완료 커밋, plan 전제부에 이미 명시된 앵커) 이 비어야 함. 이 형태로 게이트 2 에서 사용하고 **최종 게이트에도 동일 검사 1회 추가** (스텝 1 doctor 포함 전 구간 커버).

### C5 — A-7·A-9 소비처 중 context·references 파일 4곳이 변경 파일 목록에 미배정 (정본 통합 미완)
- **severity**: suggestion
- **category**: scope
- **plan 인용**: 스텝 1 doctor A-9 정본 절 신설 (`plan.md:19`) + 스텝 2-c A-7 (:25) — 소비처 교체 범위
- **챌린지**: 감사 축 2 기준 A-9 소비처 4곳 중 project·create-feature 는 2-a 에 포함되지만 `modes/tdd-activation.md:238-239` 와 `analyze/references/prompts-update.md:196` 은 plan 의 어느 스텝에도 없다. A-7 (characterize 우선순위 5벌) 도 `plan-schema.md:18`·`state-schema.md:69` 소비처가 미배정 (tdd/SKILL.md:13 은 #18 에서 기정정). 정본 신설 후에도 구 재서술이 잔존하면 "정본 통합" (우선순위 ②) 이 해당 클러스터에서 미완이고, 차기 드리프트 재발 지점이 된다. 부수적으로 context 총량 몇 줄 절감 (C1 완화에 미미하게 기여).
- **제안**: 스텝 1 (tdd-activation·prompts-update 는 A-9 절 신설과 동일 커밋) 또는 스텝 3 마무리에 4곳 참조 교체를 명시 추가. prompts-update.md 는 산식 밖 (references/) 이지만 통합 완결성 차원에서 포함.

### C6 — learn 불변 체크리스트 "20항" 은 실제 16항 — 대조 기준 수치 부정확
- **severity**: nit
- **category**: premise
- **plan 인용**: 스텝 2-b (`plan.md:24` — "축 3 learn 체크리스트 20항")
- **챌린지**: 감사 축 3 learn 체크리스트 (`docs/audits/2026-07-24-audit-3-instruction-excess.md:184-200`) 실측 16항. 항목별 대조 시 "4항 누락" 오인 소지.
- **제안**: 재확인만 필요 — "16항" 으로 정정하거나 "전 항목" 으로 수치 제거.

### C7 — 게이트 1 pytest 인자 경로 접두 누락
- **severity**: nit
- **category**: edge-case
- **plan 인용**: 게이트 1 ① (`plan.md:42` — "`python3 -m pytest pilot/tests/tools/test_doc_links.py test_docs_build.py`")
- **챌린지**: 두 번째 인자에 디렉터리 접두가 없어 저장소 루트에서 실행 시 `test_docs_build.py` 를 못 찾는다 (파일은 `pilot/tests/tools/` 에 실재 확인).
- **제안**: 재확인만 필요 — `pilot/tests/tools/test_doc_links.py pilot/tests/tools/test_docs_build.py` 로 정정.

## 합의 (planner 가 재호출되어 채움 — 처음에는 비워둠)

| C# | 처리 | 메모 |
|----|------|------|
| C1 | accepted | 사용자 재결정 (2026-07-25): 제안 (i) 채택 — 총량 게이트 ≤3,680줄 완화. #19 단독 감축률 약 27~28% 정직 기재 + spec 30~35% 는 #20 합산 판정 주석. lifecycle 문서 축소 (제안 ii) 는 미편입 — 무감사 축약 금지 명문화 |
| C2 | accepted | 잔류 최소 셋 4항으로 확장 (④ wrapper-protocol.md Read 필수 지시 1줄). 게이트 3 ③ 에 4벌 grep 검증 추가. 주의사항의 자기완결성 항목도 성공 경로 도달 논리로 갱신 |
| C3 | accepted | 게이트 2 ② 를 토큰 분리 grep 으로 교체 + `--retries-used` 토큰 추가. 재발 방지 문구 (게이트 grep 실측 사전 검증) 주의사항 신설 |
| C4 | accepted | 게이트 2 ③ base 고정 `a18a429..HEAD` + 최종 게이트 ⑥ 동일 검사 1회 추가 (스텝 1 doctor/SKILL.md 포함 전 구간 커버) |
| C5 | accepted | A-9 소비처 2곳 (tdd-activation:238-239·prompts-update:196) + A-7 소비처 2곳 (plan-schema:18·state-schema:69) 을 스텝 1 변경 파일에 편입 (A-9 절 신설과 동일 커밋) |
| C6 | accepted | learn 체크리스트 "20항" → "16항" 정정 (audit-3:184-200 실측) |
| C7 | accepted | 게이트 1 pytest 인자를 `pilot/tests/tools/test_doc_links.py pilot/tests/tools/test_docs_build.py` 로 정정 |
