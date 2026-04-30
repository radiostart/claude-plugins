# #12 cross-domain transaction 패턴 가이드

> source: V1-Full Step D 시나리오 C 제안 C — `{domain}.md` 의 "다중 DB" 섹션 확장. 다른 도메인 transaction 영향 명시

## 요구사항

- **조건**: V1 결과, wms 도메인의 `Wms::TaskService#cancel_after_completion` 같은 메서드가 외부 도메인 (schoice) 의 `SsmSPackageSheet`, `SsmSOrderSheetPackageInvoice` 를 outer transaction 으로 감쌈. 산출물의 "다중 DB" 섹션이 transaction nesting 패턴은 인용했지만 **schoice 측 어떤 status 값을 어떻게 변경하는지 contract 명시 부재**. cross-domain transaction 의 input/output contract 가이드 부재.
- **트리거**: `/pilot:learn` Phase 4 (도메인 구조 결정 + 산출물 생성) 단계.
- **기대결과**: 도메인 산출물 (예: `wms/index.md`) 에 "Cross-domain Transaction Contracts" sub-section 자동 추가. 다른 도메인 transaction 영향 (어떤 클래스 / 어떤 메서드 / 어떤 status 변경) 명시.

## 비즈니스 규칙

- **표 스키마**: `| 본 도메인 entry | 외부 도메인 영향 | 변경 type | file:line |` (4 컬럼)
  - 본 도메인 entry: 본 도메인의 메서드/서비스 (예: `Wms::TaskService#cancel_after_completion`)
  - 외부 도메인 영향: 외부 클래스 + 영향 영역 (예: `Schoice::SsmSPackageSheet status / SsmSOrderSheetPackageInvoice destroy`)
  - 변경 type: `read` / `write` / `destroy` / `create` 또는 조합
  - file:line: transaction nesting 코드 위치 (예: `task_service.rb:44-67`)
- **자동 detect 알고리즘**:
  - Phase 3 Read 시 transaction 패턴 (`ApplicationRecordWms.transaction do ... ApplicationRecordSchoice.transaction do ... end ... end`) detect
  - inner transaction 안 외부 클래스 호출 (예: `SsmSPackageSheet.update`) 추출
  - 변경 type 추론: `update` / `destroy` / `find` / `create` Rails ActiveRecord 메서드 → `read` / `write` / `destroy` / `create` 매핑
- **위치**: `{domain}/index.md` 의 "다중 DB" 섹션 직후. 단일 파일 도메인이면 `{domain}.md` 의 동일 위치.
- **idempotency**: 두 번째 `/pilot:learn` 호출 시 사용자 수동 추가 행 보존, 자동 detect 행만 갱신.
- **빈 결과**: cross-domain transaction 0 → "Cross-domain Transaction Contracts" sub-section 자체 추가 안 함. 단일 도메인 시나리오 정상.
- **A2 runtime fallback**: detect 알고리즘 실패 시 → "Cross-domain Transaction Contracts" 헤더 + "(자동 detect 실패 — 수동 작성 권장)" placeholder. abort 안 함.

## 예외 케이스

- **단일 DB 시스템**: cross-domain transaction 자체 0. 본 sub-section 추가 안 함. 산출물 그대로.
- **다단계 transaction nesting** (A.transaction → B.transaction → C.transaction): 모든 단계 캡처. 표 행이 다단계 표시 (예: `task_service.rb:44-67 (3 단계 nesting)`).
- **외부 도메인이 아직 학습 안 됨**: contract 표의 "외부 도메인 영향" 컬럼에 클래스명 만 (`Schoice::SsmSPackageSheet`). 후속 `/pilot:learn schoice` 후 detail 보강.
- **transaction 외 cross-domain 호출**: transaction nesting 안 아닌 단순 method call (예: `Schoice::SomeService.find(id)`) → `read` type 으로 표시. 단 위험성 낮음 (transaction 외라 atomic 보장 안 됨).
- **사용자 직접 작성 transaction contract**: 자동 detect 와 별개로 보존. 자동 detect 행 끝 ` (auto)` 마커 (선택, `#10` 과 정합).

## 관련 파일 범위

- **변경**: `pilot/skills/learn/SKILL.md`
  - Phase 3 Read 본문에 "transaction 패턴 detect" 단계 추가
  - Phase 4 산출물 생성 본문에 "다중 DB 섹션 + Cross-domain Transaction Contracts sub-section" 명시
- **변경**: `pilot/skills/context/domain/{template}.md` (도메인 산출 template 가 있다면)
  - "다중 DB" + "Cross-domain Transaction Contracts" sub-section 헤더 placeholder
- **변경**: `pilot/tools/doctor/integrity.py`
  - 도메인 산출물 의 "Cross-domain Transaction Contracts" 섹션 schema 검증 (4 컬럼)
- **단위 테스트**: `pilot/tests/tools/test_doctor_cross_domain_transaction.py` — schema + idempotency 케이스
- **회귀 픽스처**: `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/` 에 multi-domain transaction sample 추가 (예: `secondary-domain/` + transaction nesting)
- **사용자 영향**: cross-domain feature 작성 시 어떤 외부 도메인 어떤 영역에 transaction 영향 미치는지 한 곳 (도메인 산출물) 에서 확인 가능. 후속 `/pilot:learn` 우선순위 결정 명료.
