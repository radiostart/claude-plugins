# #10 MANIFEST.md 외부 도메인 섹션 자동 추가

> source: V1-Full Step D 시나리오 C 제안 A — `/pilot:learn` 종료 시 inventory 의 외부 클래스 reference 를 분석해 MANIFEST 에 자동 추가하는 메커니즘

## 요구사항

- **조건**: `/pilot:learn {domain}` 호출 후 inventory.md 에 외부 클래스 reference (예: `Schoice::SsmSPackageSheet`, `Sinsang::PackageStockReduceAndRefundService`) 가 식별됨. 단 사용자가 외부 도메인을 별도로 인지하고 후속 learn 호출하기 어려움.
- **트리거**: `/pilot:learn` Phase 5 (MANIFEST 갱신) 단계.
- **기대결과**: MANIFEST.md 에 "외부 도메인 reference (learn 미완료)" 섹션 자동 작성 (3 컬럼 표). 사용자가 한 곳에서 미학습 도메인 목록 + 추천 후속 learn 명령 확인.

## 비즈니스 규칙

- **표 스키마**: `| 추정 도메인 | 클래스 (개수) | 추천 후속 학습 |` (3 컬럼)
  - 추정 도메인: 클래스의 module/namespace 에서 추출 (예: `Schoice::SsmSPackageSheet` → `schoice`)
  - 클래스 (개수): 해당 도메인의 외부 reference 클래스 목록 + 갯수 (예: `SsmSPackageSheet, SsmSOrderSheetPackageInvoice... (15)`)
  - 추천 후속 학습: `/pilot:learn {추정 경로}` 명령 (예: `/pilot:learn app/models/schoice/`)
- **추정 도메인 알고리즘**:
  - 1순위: Ruby `Module::Class` namespace 의 첫 segment 소문자화 (예: `Schoice::SsmSPackageSheet` → `schoice`)
  - 2순위: 클래스 prefix 의 snake_case 변환 (예: `SsmSPackageSheet` → `ssm_s_package_sheet` → 첫 prefix `ssm_s` ?)
  - 3순위: 매칭 실패 시 "unclassified" 카테고리로 묶음
- **추천 경로 알고리즘**:
  - 사용자 코드베이스 root 에서 `app/{models,services,controllers}/{추정 도메인}/` 패턴 탐색 → 존재하면 그 경로 추천
  - 없으면 "(경로 자동 추정 실패 — 사용자 직접 지정)" 메시지
- **idempotency**: 두 번째 `/pilot:learn {외부 도메인}` 호출 시 MANIFEST 의 "외부 도메인 reference" 표 행 제거 (이미 학습됨 표시).
- **사용자 ignore**: 일부 외부 reference 는 절대 learn 불가능 (예: `ActiveRecord::Base` 같은 framework 클래스). 사용자가 표 행을 직접 삭제 또는 config 의 ignore 패턴 추가.
- **A2 runtime fallback**: 알고리즘 실패 시 (예: 추정 도메인 추출 불가) → "외부 도메인" 섹션 추가 자체 skip + WARN 1 줄 (`[WARN] 외부 도메인 reference 추출 실패 — 수동 관리 권장`). abort 안 함.

## 예외 케이스

- **외부 클래스가 standard library**: ignore 패턴으로 자동 제외 (예: `ActiveRecord::Base`, `ApplicationRecord`, `String`, `Hash`). config 에 hardcoded 기본 ignore 목록 + 사용자 추가 가능.
- **MANIFEST.md 의 기존 "외부 도메인" 섹션 사용자 편집**: 자동 갱신 시 사용자 편집 보존 (idempotency 룰). 자동 추가 행과 사용자 추가 행을 구분하기 위해 자동 추가 행 끝에 ` (auto)` 마커 (선택).
- **추정 도메인이 이미 학습된 도메인 (MANIFEST 의 "도메인 분류" 표 등록 도메인)**: "외부 도메인" 섹션에서 자동 제외 — 이미 학습됨.
- **외부 reference 가 0**: "외부 도메인" 섹션 자체 추가 안 함 (헤더 + 빈 표만 두지 않음).

## 관련 파일 범위

- **변경**: `pilot/skills/learn/SKILL.md`
  - Phase 5 본문에 "외부 도메인 reference 분석 + MANIFEST 갱신" 단계 추가 (`#09` 와 함께)
- **변경**: `pilot/skills/init/SKILL.md` 의 MANIFEST template
  - "외부 도메인 reference (learn 미완료)" 섹션 placeholder 추가 — 첫 learn 후 자동 채워짐
- **변경**: `pilot/tools/doctor/integrity.py`
  - "외부 도메인 reference" 섹션 schema 검증 (3 컬럼: 추정 도메인·클래스·추천 후속)
  - "외부 도메인" 섹션의 도메인이 이미 "도메인 분류" 표에 있으면 stale row → INFO 1 줄
- **단위 테스트**: `pilot/tests/tools/test_doctor_external_domain.py` — schema 검증 + idempotency 케이스
- **회귀 픽스처**: `pilot/tests/fixtures/v0.1.0-baseline/_input/python-sample/` 에 cross-module import 추가
- **사용자 영향**: cross-domain feature 작성 시 어떤 도메인 추가 학습 필요한지 한 곳 (MANIFEST) 에서 확인 가능. 학습 우선순위 결정 명료.
