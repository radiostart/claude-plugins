# #18 정비 prune — 미사용·드리프트 정리

> source: prompt
> created: 2026-07-24T13:31:10Z
> user_prompt: "prune — 감사 승인된 미사용 파일 삭제·모순 드리프트 9건 정정·stale 참조 정리. 근거: docs/audits/2026-07-24-pilot-consolidation-audit.md § 3 (#18 prune 범위) + 축1·축2 부록"

## 요구사항

- **조건**: 2026-07-24 전수 감사 승인 완료 (통합 보고서 § 4 — 삭제 범위 = 후보 전체 승인). 동작 변경 없는 삭제·정정만 수행.
- **트리거**: 정비 3-feature 사이클의 1번 — #19 재작성 전에 삭제·정정을 확정해 죽은 참조를 방지.
- **기대결과**:
  - 삭제 (감사 축 1 § B·C 승인분): `pilot/tests/fixtures/handoff-quality/` 전체 (4파일) · `pilot/tests/fixtures/v0.1.0-baseline/` 의 수동 회귀 하네스 (diff.sh + learn/project/analyze/wizard/tdd-on/tdd-off/doctor-onboarding expected 37파일 — 자동 테스트가 쓰는 external-domain·transaction-contracts·config·migration·open-questions 픽스처는 보존) · `pilot/examples/code-review/README.md` · `pilot/skills/context/lifecycle/INDEX.md` · `pilot/skills/context/lifecycle/setup/README.md` · `pilot/skills/context/lifecycle/issues/example/issue.md`
  - 정정 (감사 축 2 § B 판정대로): B-1~B-9 모순 드리프트 — B-1·B-2 일부·B-6·A-12 는 `pilot/skills/context/INDEX.md` 의 문구 정정으로 처리 (삭제 대상 `lifecycle/INDEX.md` 와 별개 파일, preamble P3 런타임 참조라 삭제 불가 — 2026-07-24 planner 드리프트 보고·사용자 승인), 잔존 파일 쪽 (analyze/SKILL.md:202 B-2, pr/SKILL.md:49 B-4, GUIDE.md B-3·B-5, code-review-init B-7, tdd/SKILL.md:13 B-8, INFO 문구 B-9) 은 정본 기준으로 문구 정정
  - 삭제 파일을 가리키던 참조 (INDEX.md 링크 등) 정리 — 깨진 링크 0 유지
  - `docs_build.py` 에 stale 출력 정리 로직 추가 (감사 축 1 § D-2)

## 상태 전환

_(없음 — 상태 파일 무변경)_

## 비즈니스 규칙

- pytest 전체 통과 + `python3 pilot/tools/doctor.py workspace` 클린 + docs 빌드 정상 (사이클 공통 게이트)
- 스킬 동작·기계 계약 (문자열 리터럴·CLI 시그니처) 무변경 — 이 feature 는 삭제와 문구 정정만
- 드리프트 정정 시 정본 판단은 감사 축 2 § B 표의 판정 근거를 따른다 (재조사 불필요)

## 예외 케이스

- v0.1.0-baseline 삭제 시 자동 테스트가 참조하는 서브디렉터리 (`external-domain`·`transaction-contracts`·`config`·`migration`·`open-questions`) 를 오삭제하면 pytest 가 깨진다 — 삭제 전 테스트 참조 재확인 필수. `verify-reports` 는 v0.1.0-baseline 하위가 아닌 sibling `pilot/tests/fixtures/verify-reports/` (무관·보존 — 2026-07-24 위치 오기 정정)
- `test_doctor_migration.py` 의 migration 픽스처는 #20 (마이그레이션 코드 삭제) 전까지 보존

## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- (없음)

### (d) 비즈니스 결정 영역
- (없음 — 삭제 범위는 감사 § 4 결정 1 에서 사용자 승인 완료)
