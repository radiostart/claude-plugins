# #09 cross-domain 처리 가이드 (V1 발견 기반 main milestone)

> source: V1-Full Step D 시나리오 C — nimda Rails monolith dogfooding 결과
> 일자: 2026-04-30. nimda 의 wms 도메인 산출물로 cross-domain feature spec 시도 → schoice 외부 도메인 부재 시 명확히 막힘. cross-domain 처리 가이드 부재 = pilot 의 진짜 gap.

## 요구사항

- **조건**: V1 검증 결과, pilot 의 stated purpose 가 single domain 영역에서는 충족 (22.4% 압축, 100% 인용 정확) 이지만 cross-domain 의존성이 있는 feature 작성 시 명확히 막힘. 사용자가 "이 feature 는 schoice 도메인이 필요하다 — 어떻게 처리할지" 가이드 받지 못함.
- **트리거**: `/pilot:learn {domain1}` 후 `/pilot:create-feature` 또는 `/pilot:analyze` 호출 시 산출 feature 가 다른 도메인 의존 시.
- **기대결과**: pilot 이 cross-domain 의존성을 detect → 사용자에게 "다른 도메인 추가 learn 권장" 가이드 + feature spec 의 "Open Questions" 섹션에 cross-domain 영역 명시.

## 비즈니스 규칙

- **cross-domain 의존성 detect 메커니즘**:
  - `/pilot:learn` Phase 2 (Inventory) 가 의존성 추적 시 외부 클래스 reference 발견 (예: `wms` 도메인 코드가 `Schoice::SsmSPackageSheet` 참조)
  - 외부 클래스를 inventory.md 에 "외부 의존" 카테고리로 분류
  - 외부 클래스의 module/namespace 분석 → 추정 도메인명 추출 (예: `Schoice::*` → `schoice`)
- **MANIFEST.md 외부 도메인 자동 추가** (#10 과 짝):
  - `/pilot:learn` Phase 5 종료 시 inventory 의 외부 reference 를 분석해 MANIFEST.md 에 신규 섹션 자동 작성:
  ```markdown
  ## 외부 도메인 reference (learn 미완료)
  | 추정 도메인 | 클래스 (개수) | 추천 후속 학습 |
  | --- | --- | --- |
  | schoice | SsmSPackageSheet, SsmSOrderSheetPackageInvoice... (15) | `/pilot:learn app/models/schoice/` |
  ```
  - 사용자가 후속 `/pilot:learn` 으로 외부 도메인 학습하면 해당 행 제거
- **`/pilot:create-feature` 의 cross-domain detect**:
  - feature spec 작성 중 산출물에서 답할 수 없는 영역 발견 시 → MANIFEST 의 "외부 도메인 reference" 섹션 lookup
  - 매칭되는 도메인 있으면 INFO 1 줄: `[INFO] 이 feature 는 {외부 도메인} 의존성 — 먼저 /pilot:learn {외부 도메인} 권장`
  - 매칭 없으면 spec 의 Open Questions 섹션에 명시 (#11 과 짝)
- **`/pilot:analyze` 의 cross-domain detect**:
  - 5-2 단계에서 features/ 매칭 시 외부 도메인 의존성 detect → 동일 가이드
- **A2 runtime fallback 정합**: cross-domain 의존성 detect 실패 시 → spec 진행 (abort 안 함). 사용자가 spec 의 Open Questions 보고 결정.
- **idempotency**: 두 번째 `/pilot:learn {외부 도메인}` 호출 시 MANIFEST 의 "외부 도메인 reference" 행 제거. 또는 사용자가 명시적 ignore 가능 (예: 외부 시스템 spec 같은 절대 learn 불가능 영역).

## 예외 케이스

- **외부 클래스가 standard library / framework**: detect 제외. 예: `ActiveRecord::Base`, `ApplicationRecord`, `String`, `Hash` 등은 도메인 reference 가 아님. config 의 ignore 패턴으로 명시 가능.
- **외부 도메인 추정 실패**: 클래스명에서 namespace 가 명확하지 않으면 (예: `OrderHelper`) detect 안 함. 사용자가 수동으로 MANIFEST 의 "외부 도메인" 섹션 편집 가능.
- **모든 외부 reference 가 한 도메인**: `wms` 도메인 코드가 100% `Schoice::*` 만 참조하면 MANIFEST 에 `schoice` 1 행만. 단순 케이스.
- **다단계 cross-domain**: A → B → C 의존성 chain. 본 v0.3.0 은 1 단계 (직접 의존) 만. 다단계는 v0.4.0 milestone.
- **순환 의존성** (A → B, B → A): MANIFEST 의 "외부 도메인" 양쪽에 등장. 사용자가 인지 후 처리. doctor 의 INFO 1 줄로 알림.

## 관련 파일 범위

- **변경**: `pilot/skills/learn/SKILL.md`
  - Phase 2 본문에 "외부 도메인 클래스 reference 추출" 단계 추가
  - Phase 5 본문에 "MANIFEST 의 '외부 도메인 reference' 섹션 자동 작성" 단계 추가 (`#10` 과 함께)
- **변경**: `pilot/skills/create-feature/SKILL.md`
  - "산출물에서 답할 수 없는 영역 발견 시 MANIFEST '외부 도메인' lookup → 가이드" 절차 추가
- **변경**: `pilot/skills/analyze/SKILL.md`
  - 5-2 단계의 cross-domain detect 절차 추가
- **변경**: `pilot/skills/context/MANIFEST.md.template` (또는 `init` skill 의 MANIFEST 생성 부분)
  - "외부 도메인 reference (learn 미완료)" 섹션 헤더 추가 (빈 표)
- **변경**: `pilot/tools/doctor/integrity.py`
  - "외부 도메인 reference" 섹션 schema 검증 (3 컬럼: 추정 도메인 / 클래스 / 추천 후속 학습)
  - 순환 의존성 detect 시 INFO 1 줄
- **단위 테스트 (신규)**: `pilot/tests/tools/test_doctor_cross_domain.py` — "외부 도메인" 섹션 schema 검증 케이스
- **회귀 픽스처**: `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/` 에 cross-module import 추가 (예: 새 폴더 `_input/secondary-domain/`) → cross-domain detect 검증
- **사용자 영향**: V1 검증으로 입증된 진짜 gap 처리. 큰 레거시 cross-domain feature 작성 가능성 회복.
