# v0.1.0-baseline fixture

## 목적

doctor 검증 로직 (`pilot/tools/doctor/integrity.py` 등) 단위 테스트가 소비하는
고정 픽스처 모음. 수동 회귀 하네스 (`diff.sh` + `learn/project/analyze/wizard/tdd-on/tdd-off/doctor-onboarding`
의 `expected/` 캡처)는 2026-07-24 감사 승인으로 삭제됐다 — 자동 테스트 참조 0건이었고
LLM 시뮬레이션 캡처 특성상 유지보수 비용만 발생했다 (`docs/audits/2026-07-24-pilot-consolidation-audit.md` § 3).

## 보존 픽스처 5종 — 소비 테스트 매핑

| 서브디렉터리 | 소비 테스트 |
| --- | --- |
| `config/` | `pilot/tests/tools/test_doctor_integrity.py` |
| `external-domain/` | `pilot/tests/tools/test_doctor_external_domain.py` · `test_doctor_cross_domain.py` |
| `migration/` | `pilot/tests/tools/test_doctor_migration.py` (`#20` 마이그레이션 코드 삭제 전까지 보존) |
| `open-questions/` | `pilot/tests/tools/test_doctor_open_questions.py` |
| `transaction-contracts/` | `pilot/tests/tools/test_doctor_cross_domain_transaction.py` |

각 픽스처는 `pass-*`/`error-*` 등 케이스별 서브폴더에 `config.md`·`workspace/` 조합을 두고,
대응 테스트가 `FIXTURE_BASE / "{서브디렉터리}"` 경로로 직접 읽는다. 신규 doctor 검증 함수를
추가할 때 이 디렉터리 구조를 참고해 케이스를 확장한다.

## `_input/` — 보존 (튜토리얼 더미 저장소)

`_input/python-sample/` (15파일, FastAPI 토이 코드베이스)은 배포 튜토리얼
[`pilot/docs/tutorial/getting-started.md`](../../../docs/tutorial/getting-started.md) 가
`cp -r` 로 복사해 walkthrough 의 더미 저장소로 사용한다. 수동 회귀 하네스 삭제와 무관하게
**보존** — 삭제 시 배포 문서의 사전 준비 절차가 파손된다.
