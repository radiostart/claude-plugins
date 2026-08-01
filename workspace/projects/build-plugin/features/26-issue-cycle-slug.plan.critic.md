# Plan Critic — #26 issue 단건 사이클 + 폴더 slug 자동 명명 (dp-skills 0.25.0/0.30.0 포팅)

> 입력 plan: `features/26-issue-cycle-slug.plan.md` (검토 시각 2026-08-01T01:05:00+09:00)
> 입력 feature: `features/26-issue-cycle-slug.md`
> 페르소나: `personas.planner-critic` (red-team)
> focus 반영: 없음 (orchestrate-load 반환 `focus: null`)

## 검증 방법 요약

plan 의 사전 실측 표 전 행을 pilot 실코드 (파일:라인) 로 스팟체크하고, dp 원본 (`/Users/jay-p/Projects/deali-skills-plugin` HEAD `7dc24fb`) 의 orchestrate-load·wrapper 4종 이슈 블록·preamble·messages·focus·issue SKILL·GUIDE·protect-managed·doctor·how-to 를 전건 대조했다. `cf54939`(33파일)·`c1febc6`(7파일) 범위와 0.26~0.30.2 중간 커밋의 issue 관련 변경도 확인했다. 실행 검증: unittest (3.12/3.14 양쪽)·docs_build --check·버전 grep·sweep grep.

**통과 확인된 축 (챌린지 없음)**: ① 이식 제외 7항의 계획 내 스며듦 0건 (qa phase·verify-report-lint·supplementary·단일 도메인 자동 채택·5-bis 인터뷰·oq-gate 약속·persona 주입 — dp 소재 매핑과 plan 제외 지시가 전건 일치) ② 자기완결 인라인 치환표가 dp 원문의 qa 참조 전 소재 (planner 원형·`.r{N}` qa 준용·evaluator 3분류 참조·eval 저장 규약·issue SKILL 정의 ②·GUIDE 명명 문구·preamble "qa/SKILL.md 동일 원리" 괄호·critic 절차 3 치환규칙) 를 커버 — dp HEAD 의 3분류 (a)/(b)/(c) 원문과 D4 인라인 내용 일치 ③ orchestrate-load 하위호환 — 기존 legacy 4컬럼 픽스처 (`test_orchestrate_load.py:75,613,653`) 가 project 폴백으로 무손 통과, `BuildInstructions` 는 len 5 + ins[0..2] 만 단언 (:718-724) 이라 5번째 지시문 변경에 안전, `build_load_plan` kwarg default·step 8 `spec_md_abs` 재사용은 project 모드 거동 불변 ④ preamble P1 issue 판정 예외 (focus·commit) — 적용표 P1 적용 스킬 전수와 spec 의 "종료 8종 + 예외 2종" 이 정확히 합치, dp 원형 (commit 은 dp P1=팀확인만 수행·활성확인 미수행) 대비 등가 성립, D1 근거 (`commit/SKILL.md:10-22` `{PROJECT}` 실사용 없음) 실측 일치 ⑤ 테스트 계획의 게이트 커버 — spec (8) 열거 7축 (work_mode 판정·bare·부재·도메인 라인·prompts skip·focus 분기·--project 우회) 전건이 스텝 2 테스트에 1:1 존재, doctor 4 클래스·훅 6 케이스 도 spec (4)(7) 요구 커버 ⑥ auto_pilot REPORT 파서는 mode 를 enum 검증하지 않음 (`auto_pilot.py:165-170` 첫 토큰 저장만) — plan 주의사항의 조건부 확인은 "무변경" 으로 귀결, 계획 성립.

## 챌린지

### C1 — 게이트 baseline 2건이 이 워크트리 실측과 불일치 (테스트 270≠309 · docs_build --check exit 0≠1)

- **severity**: blocking
- **category**: premise
- **plan 인용**: 사전 실측 표 (`features/26-issue-cycle-slug.plan.md:33-34`) · 게이트 1 (`:187`) · 게이트 5 (`:191`) · 주의사항 "게이트 실행 인터프리터" (`:172`)
- **챌린지**: 이 워크트리에서 `/opt/homebrew/bin/python3.12 -m unittest discover -s pilot/tests/tools` 는 **OK (309)** (2회 재현, 테스트 최종 변경 커밋 = 기준점 `bac0375` 이므로 plan 작성 시점에도 309) 이고 `python3.12 pilot/tools/docs_build.py --check` 는 **exit 1** (34 페이지 drift — `docs/reference/{agents,skills,tools}/`·`identity.md` 가 git 미추적이라 워크트리에 부재) 인데, plan 은 각각 "OK (270)"·"exit 0" 을 실측이라 주장한다 — "270" 은 python3.14 실측치 (Ran 269 + errors 1, test_docs_build 41건 수집 탈락) 와 사실상 같은 수치라 인터프리터 혼동 또는 타 체크아웃 (reference 페이지가 남아있는 본 저장소) 측정 정황이며, 이 잘못된 앵커가 게이트 1 의 "기존 무손" 판정을 최대 39건 테스트 소실까지 못 보게 만든다.
- **제안**: 사전 실측 표 2행과 게이트 1 의 기준 수치를 이 워크트리 실측 (**309**) 으로 정정하고, docs_build 행·게이트 5 를 "미추적 reference 페이지 부재로 fresh worktree 는 `--check` 실패가 정상 — 게이트는 스텝 10 재생성 **후** exit 0" 으로 재서술한다 (전달사항 ②의 상태 기반 증거 원칙과도 정합). evaluator 가 게이트 1 을 "270 + 신규" 로 판정하지 않도록 plan 재확정 필요.

### C2 — bare issue 경로의 절차 세부 (2·3 건너뜀·GUIDE 로드·6단계 사이클 안내 제외) 가 plan 에 미고정

- **severity**: suggestion
- **category**: edge-case
- **plan 인용**: 스텝 8 (`features/26-issue-cycle-slug.plan.md:140-142` — "수행 절차 6단계는 spec §(6) ①~⑥ 이 확정 본문 … plan 확정 보충 3건만 추가")
- **챌린지**: dp HEAD issue SKILL 절차 1 은 bare 진입 시 "고지 후 **GUIDE.md 로드 + 2·3 단계 건너뛰고 4 단계부터** 진행 (5 는 MANIFEST 까지만, **6 단계 안내에서 사이클 항목 제외**)" 를 명시하는데, spec §(6) ① 은 "bare 진입 1줄 고지 (기록·사이클 비지원)" 로 축약돼 있고 plan 의 보충 3건 (i)~(iii) 에도 이 흐름이 없어 — generator 가 "spec 이 확정 본문" 지시대로만 쓰면 bare 경로에서 6단계 else 분기가 `@pilot-planner` 사이클을 안내하는 자기모순 (orchestrate-load 의 bare 에러가 backstop 하지만 사용자 혼란) 이 남을 수 있다.
- **제안**: 스텝 8 보충에 (iv) 1줄 추가 — "bare: 고지 후 2·3 단계 건너뜀 (검색·slug 불가), GUIDE 로드 후 4단계 (`| issue | - |` 기록) 부터 진행, 6단계 안내에서 사이클 항목 제외" (dp HEAD 절차 1 원문 준거).

### C3 — 배포되는 preamble P2 본문에 내부 감사 식별자 ("감사 F22"·"이 저장소") 가 스며듦

- **severity**: suggestion
- **category**: scope
- **plan 인용**: 스텝 6 preamble P2 (`features/26-issue-cycle-slug.plan.md:131`)
- **챌린지**: plan 이 P2 원칙 단락 치환문 안에 "— 이 저장소도 감사 F22 로 gitignore —" 를 포함시키는데, `preamble.md` 는 플러그인으로 배포되는 사용자 문서라 "이 저장소" 는 사용자 관점에서 지시 대상이 모호하고 "감사 F22" 는 build-plugin 내부 감사 ID 로 무의미하다 — dp HEAD 동일 단락은 일반형 ("STATE.md·projects/ 는 통상 gitignore 라 … 예외 구성에서만 git log 보조 가능") 으로 이 문제가 없다.
- **제안**: 배포 본문은 dp HEAD 일반형 문구를 그대로 채택하고, "감사 F22" 근거는 plan/spec (작업 기록) 에만 남긴다. spec (3) 의 문구도 정정 *사유* 로 읽히므로 spec 위반 아님.

### C4 — 사전 실측 표 "docs 의 issue 언급 0건" 은 문자 그대로는 부정확 (1건 존재)

- **severity**: nit
- **category**: premise
- **plan 인용**: 사전 실측 표 (`features/26-issue-cycle-slug.plan.md:31`)
- **챌린지**: `pilot/docs/how-to/create-feature.md:22` 에 예시 slug `pre-issue-eligibility-check` 로 "issue" 부분 문자열이 1건 존재해 "언급 0건" 단정은 grep 재현이 안 된다 — 다만 issue 모드 서술이 아니라 무관 예시라 표의 결론 (신설 외 stale 화 위험 없음) 자체는 유지된다.
- **제안**: 표 서술을 "issue 모드 서술 0건 (무관 예시 slug 1건 제외)" 으로 정확화. 재확인만 필요.

### C5 — generator 이슈 블록: plan 부재 시 step 2 "없으면 skip" 이 변경 범위 게이트를 무력화

- **severity**: nit
- **category**: edge-case
- **plan 인용**: 스텝 5 generator ② (`features/26-issue-cycle-slug.plan.md:118`) · 현행 `pilot/agents/pilot-generator.md:21` (step 2 "없으면 이 단계 skip")
- **챌린지**: 사용자가 planner 없이 `@pilot-generator` 를 직접 호출한 issue 세션에서는 로드할 `issue.plan*.md` 가 없어 step 2 의 기존 "없으면 skip" 이 적용되고, 그 결과 이슈 블록 ① 변경 범위 게이트의 기준 (`결함 함수:` 1줄) 이 존재하지 않는 채 구현이 진행될 수 있다 — dp HEAD 도 동일 공백이므로 (이식 원칙상 임의 개선 금지) 채택 여부는 planner 재량.
- **제안**: 이슈 블록 ② 에 "plan 부재 시 skip 이 아니라 'plan 없음 — `@pilot-planner` 먼저 호출' 안내 후 종료" 1줄 추가 검토. 미채택 시 dp-parity 사유 1줄로 기각해도 무방 (재확인만 필요).

## 합의 (planner 재호출 2026-08-01 — 독립 재검증 후 전건 accepted)

| C# | 처리 | 메모 |
|----|------|------|
| C1 | accepted | 합의 라운드 독립 재실측으로 재현: unittest(3.12) **OK (309)** (tests 최종 변경 커밋 = 기준점 `bac0375` — plan 작성 시점에도 309) · `docs_build.py --check` **exit 1** (34페이지 drift — 미추적 reference 페이지가 fresh worktree 에 부재). 3.14 는 `Ran 269 + errors 1` 재현 — "270" 은 인터프리터 혼동 정황 합치. plan 정정: 사전 실측 표 2행 + 게이트 1 앵커 309 + 게이트 5 "생성 실행 → --check exit 0" 순서 재서술 |
| C2 | accepted | dp HEAD issue SKILL 절차 1 원문 실측 일치 ("고지 후 GUIDE 로드, 2·3 건너뛰고 4부터, 5 는 MANIFEST 까지만, 6 안내에서 사이클 항목 제외"). 스텝 8 보충에 (iv) bare 흐름 1건 추가 — spec §(6) ① 축약분의 plan 확정 보충 |
| C3 | accepted | dp HEAD preamble :56 일반형 원문 확인 (내부 감사 ID·저장소 특정 문구 없음). 배포 치환문을 dp 일반형 그대로 채택 — "감사 F22"·"이 저장소" 는 배포 본문에서 제거, 저장소 특정 근거는 plan·spec 기록에만 잔존 |
| C4 | accepted | grep 재확인 — `how-to/create-feature.md:22` 의 무관 예시 slug (`pre-issue-eligibility-check`) 1건 실재. 표 서술을 "issue 모드 서술 0건 (무관 예시 slug 1건 제외)" 로 정확화 — 결론 (stale 화 위험 없음) 불변 |
| C5 | accepted | dp HEAD `ag-generator.md:58` 도 동일 "없으면 건너뛴다" 공백 실측 — 가드 신설 제안은 미채택 (이식 원칙: dp 패리티·임의 개선 금지), 주의사항에 "dp 동일 공백·임의 개선 금지" 명문화 1줄로 소화 (제안이 허용한 대안 경로) |
