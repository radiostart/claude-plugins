# pilot 판정 기준

## soft policy 명시

본 문서는 강제 룰이 아니라 판정 근거 모음. 예외는 증거와 함께 기록한다. Evaluator 가 반려·통과 판단을 내릴 때 인용하는 축이며, 프로젝트별 특수성이 있으면 해당 축의 판정 결과에 근거를 덧붙여 예외 처리할 수 있다.

## 기본 판정 축

### requirements

feature spec 대비 누락 여부를 확인한다. 증거는 `features/NN-{slug}.md` 의 조건 / 트리거 / 기대결과 3 축 매칭.

### tdd_evidence

`tdd: true` 프로젝트에서 `.plan.md` 스텝별 `[Red]` / `[Green]` 기록 유무를 확인한다. 증거 누락 또는 "인프라 오류" 기록은 반려 사유.

### test_run

이번 변경 관련 테스트 실행 결과. 증거는 `{test_command} {경로}` 출력 — 전체 실행은 금지, 관련 경로만 지정.

### scope

`.focus.md` 및 `config.md` 의 `## Ignore` 범위 준수. 증거는 변경 파일 목록과 scope/rules 매칭.

### drift

`workspace/context/` 또는 프로젝트 산출물이 실제와 다름을 발견했을 때 drift-protocol 발동 여부. 증거는 보고 이력과 사용자 승인 기록.

---

## SSOT — REPORT vs 체크박스

VERIFICATION REPORT (요약) 와 evaluator.md 체크리스트 (상세) 는 **동일 검토 결과의 두 표현**. 모순이 발생하면 **REPORT 의 gate 판정을 진실로 보고 체크박스를 재정렬**한다.

판정 기준:

- REPORT `status: READY` ↔ 모든 gate `pass | skip` ↔ 모든 체크박스 `[x]` ↔ project.md 해당 목표 `[x]`
- 위 등가가 깨지면 모순 — Evaluator 가 재판정 후 두 항목을 동기화한다.
- REPORT 출력 후 체크박스에 미통과 항목이 발견되면 REPORT `status` 를 `NOT_READY` 로 정정하거나, 체크박스를 `[x]` 로 갱신할 근거가 명확하면 그대로 동기화.

이 룰은 동시 작성 시점의 휴먼 에러 방지가 목적이며, 자동화 도구가 강제하지는 않는다 (soft policy).
