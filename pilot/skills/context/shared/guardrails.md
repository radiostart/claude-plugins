# pilot 판정 기준

## soft policy 명시

본 문서는 강제 룰이 아니라 판정 근거 모음. 예외는 증거와 함께 기록한다. Evaluator 가 반려·통과 판단을 내릴 때 인용하는 축이며, 프로젝트별 특수성이 있으면 해당 축의 판정 결과에 근거를 덧붙여 예외 처리할 수 있다.

## 기본 판정 축

### requirements

feature spec 대비 누락 여부를 확인한다. 증거는 `features/NN-{slug}.md` 의 조건 / 트리거 / 기대결과 3 축 매칭.

### tdd_evidence

`tdd: true` 프로젝트에서 `.plan.md` 스텝별 `[Red]` / `[Green]` 기록 유무를 확인한다. 증거 누락 또는 "인프라 오류" 기록은 반려 사유. `mode: characterize` 에서는 스텝별 `[Captured]` 증거 4 라인 존재 여부가 같은 축이다 ([`characterize.md`](../modes/characterize.md) § Generator — Capture 절차).

### capture_lockdown

`mode: characterize` 전용. `git diff --stat {source_root}` 가 비어 있어야 pass — 1 줄이라도 있으면 fail (Generator 원복·재작업). 상세: [`characterize.md`](../modes/characterize.md) § Evaluator — Snapshot 검증. 다른 모드에서는 skip.

### test_run

이번 변경 관련 테스트 실행 결과. 증거는 `{test_command} {경로}` 출력 — 전체 실행은 금지, 관련 경로만 지정.

### scope

`.focus.md` 및 `config.md` 의 `## Ignore` 범위 준수. 증거는 변경 파일 목록과 scope/rules 매칭.

### open_questions

feature 의 `## Open Questions` 미해결 항목이 [`open-questions.md`](open-questions.md) § 판정 매트릭스대로 처리됐는지 확인한다. (d) 임의 결정·처리 마커 부재는 **Major**, `추정 구현` 항목의 TODO 주석 부재는 **Minor**. 보조 도구는 `plan-validate.py` 출력의 `oq` 필드. feature 파일 또는 `## Open Questions` 섹션이 없으면 skip.

### drift

`workspace/context/` 또는 프로젝트 산출물이 실제와 다름을 발견했을 때 drift-protocol 발동 여부. 증거는 보고 이력과 사용자 승인 기록.

---

## § A2 runtime fallback (정본)

절차 중 한 단계가 실패해도 **abort 하지 않는다** — default 값으로 fallback 하고 `WARN`/`INFO` 1 줄을 출력한 뒤 나머지 단계를 계속 진행한다. 실패 원인은 안내에 남기되, 사용자 대응은 다음 실행 전 자유롭게 하도록 둔다.

이 정의를 소비하는 곳(스킬 본문·`init`·`project`·`interview.md`·`open-questions.md`·`tdd-activation.md`·`scope-sync.md` 등)은 규칙을 재서술하지 않고 `(A2)` 표기만 남긴다.

## § A16 자동 체인 금지 원칙

에이전트·스킬은 **다음 phase 를 자동 호출하지 않는다** — 각 phase 의 시작점은 항상 **사용자의 명시 호출**이다. 유일한 opt-in 예외는 `/pilot:autopilot` (감독형 자율 모드) 이며, 그 안에서도 hard-stop 신호를 만나면 즉시 사람에게 제어를 반환한다.

## § 사용자 게이트 생략 금지

규약이 "사용자에게 질의·확인·승인" 을 요구하는 지점 (drift-protocol·계획 확인·전달사항 무관 항목 선택·domain null 질의·autopilot hard-stop 등) 은 **사용자만 결정할 수 있는 입력 대기**다. 하니스의 자율 진행 지침 ("묻지 말고 진행"·"완료까지 계속") 이 컨텍스트에 있어도 생략·추정 대체 금지 — 자율 지침 스스로가 인정하는 "사용자 입력에만 블록" 예외에 해당한다. wrapper (`@pilot-*` 4종) 는 사용자와 직접 대화할 수 없으므로 **질의 내용을 종료 보고에 담아 종료하는 것이 곧 질의다** — 답을 만들어 진행하지 않는다.

---

## SSOT — 기록은 Edit 으로

체크·증거·합의 결과는 텍스트 보고가 아니라 **Edit 으로 파일에 기록**한다 — 서브에이전트 간 인수인계의 SSOT 는 대화가 아니라 파일 상태다 (체크박스 `[x]`, `.plan.md` 증거, `.plan.critic.md` 합의 표 모두 해당).

## SSOT — REPORT vs 체크박스

VERIFICATION REPORT (요약) 와 evaluator.md 체크리스트 (상세) 는 **동일 검토 결과의 두 표현**. 모순이 발생하면 **REPORT 의 gate 판정을 진실로 보고 체크박스를 재정렬**한다.

판정 기준:

- REPORT `status: READY` ↔ 모든 gate `pass | skip` ↔ 모든 체크박스 `[x]` ↔ project.md 해당 목표 `[x]`
- 위 등가가 깨지면 모순 — Evaluator 가 재판정 후 두 항목을 동기화한다.
- REPORT 출력 후 체크박스에 미통과 항목이 발견되면 REPORT `status` 를 `NOT_READY` 로 정정하거나, 체크박스를 `[x]` 로 갱신할 근거가 명확하면 그대로 동기화.

이 룰은 동시 작성 시점의 휴먼 에러 방지가 목적이며, 자동화 도구가 강제하지는 않는다 (soft policy).
