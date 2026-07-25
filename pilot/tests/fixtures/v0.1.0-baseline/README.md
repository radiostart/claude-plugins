# v0.1.0-baseline fixture

## 목적

과거 doctor 검증 로직 (`pilot/tools/doctor/integrity.py` 등) 단위 테스트가 소비하던
고정 픽스처 모음이었다. 수동 회귀 하네스 (`diff.sh` + `learn/project/analyze/wizard/tdd-on/tdd-off/doctor-onboarding`
의 `expected/` 캡처)는 2026-07-24 감사 승인으로 삭제됐다 — 자동 테스트 참조 0건이었고
LLM 시뮬레이션 캡처 특성상 유지보수 비용만 발생했다 (`docs/audits/2026-07-24-pilot-consolidation-audit.md` § 3).

## 보존 픽스처 5종 삭제 완료 (`#20` — Python 슬림화)

`migration/`·`config/`·`external-domain/`·`open-questions/`·`transaction-contracts/` 는
`#20` 스텝 1(마이그레이션)·스텝 2(md 표 lint 4종)에서 각각 소비 테스트·소비 검증 함수
삭제와 동일 커밋으로 함께 제거됐다 (schema lint 를 모델 자기 검증 지시문으로 이관 —
근거: `docs/audits/2026-07-24-audit-4-python.md` § C). 이 디렉터리 아래 이제
`_input/` 만 남는다.

## `_input/` — 보존 (튜토리얼 더미 저장소)

`_input/python-sample/` (15파일, FastAPI 토이 코드베이스)은 배포 튜토리얼
[`pilot/docs/tutorial/getting-started.md`](../../../docs/tutorial/getting-started.md) 가
`cp -r` 로 복사해 walkthrough 의 더미 저장소로 사용한다. 수동 회귀 하네스 삭제와 무관하게
**보존** — 삭제 시 배포 문서의 사전 준비 절차가 파손된다.
