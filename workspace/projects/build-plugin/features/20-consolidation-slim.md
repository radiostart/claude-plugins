# #20 정비 slim — Python 슬림화

> source: prompt
> created: 2026-07-24T13:31:10Z
> user_prompt: "slim — integrity.py 등 거대 스크립트 축소, 모델 이관 대상 스크립트 삭제, 연동 테스트 정리. 근거: docs/audits/2026-07-24-pilot-consolidation-audit.md § 3 (#20 범위) + 축4 부록"

## 요구사항

- **조건**: #19 rewrite 완료 후 (이관 원칙이 재작성된 스킬 지시문에 반영됐는지 diff 로 확인 가능한 상태).
- **트리거**: 정비 3-feature 사이클의 3번 (마지막).
- **기대결과** (감사 축 4 `docs/audits/2026-07-24-audit-4-python.md` 가 SSOT):
  - integrity.py 슬림화: v0.1→v0.2 마이그레이션 삭제 (-246), md 표 lint 4종 모델 이관 (-642), Onboarding Health 축소 (-221) → 2,160 → 약 1,060줄
  - 이관 후 삭제: `diagnose.py`·`memory-hint.py`·`init_detect.py` — 각 호출처 문서 (doctor SKILL·preamble P0·init SKILL·integrity.py:453) 의 지시문 대체와 **동일 커밋**에서 수행 (축 4 § C 초안 활용)
  - `doctor/schema.py` 는 **유지** + stale 이던 `validate.yml` 을 실제 CI 워크플로로 신설 (감사 § 4 결정 2)
  - verify-report-lint.py: validate()+렌더+CLI 삭제, 파서 2함수는 auto_pilot.py 로 흡수. doctor.py backward-compat re-export 정리, orchestrate-load 중복 유틸 정리
  - 연동 테스트·픽스처 삭제 (~1,380줄): test_doctor_migration·test_doctor_integrity·test_doctor_external_domain·test_doctor_cross_domain·test_doctor_open_questions·test_doctor_cross_domain_transaction·test_init_detect·test_memory_hint + verify-report-lint 테스트 부분 축소 + 관련 픽스처
  - tools/ 총 30% 이상 감축

## 상태 전환

_(없음)_

## 비즈니스 규칙

- **이관 부적합 판정 준수** (축 4 § D): plan-validate.py (autopilot hard-stop 신호) · regen-verify.py (모델 자기 인증 방지) · auto_pilot.py (전이 결정성) · confluence.py · slack-notify.py · docs_build.py 는 유지
- integrity.py 보존 필수부 (축 4 § B): check_workspace·check_project·auto-fix 3종·credential/Slack secret 검사·run_integrity_check — 파일시스템·git·시각 비교는 모델 대체 금지
- 스크립트 삭제 커밋마다 pytest 전체 통과 유지 (테스트 삭제는 대상 스크립트 삭제와 같은 커밋)
- pytest + doctor + docs 빌드 게이트 (공통). 완료 후 파이프라인 1사이클 실완주 (dogfooding 최종 검증)

## 예외 케이스

- auto_pilot.py 가 verify-report-lint 를 동적 로드하는 현 구조 — 파서 흡수 시 autopilot 스킬의 CLI 계약 (`--report-file`) 이 깨지지 않아야 함
- md 표 lint 이관 후에도 orchestrate-load 가 실소비하는 `## 도메인 분류`·`## 외부 도메인 reference` 표의 graceful degrade 는 그대로 동작해야 함

## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- (없음)

### (d) 비즈니스 결정 영역
- (없음 — schema.py 처분·삭제 범위는 감사 § 4 에서 사용자 승인 완료)
