# #19 정비 rewrite — 원칙 중심 재작성

> source: prompt
> created: 2026-07-24T13:31:10Z
> user_prompt: "rewrite — SKILL.md 전체·agents 를 원칙 중심으로 재작성 (스킬 각 100줄 이하), context/ SSOT 재편. 근거: docs/audits/2026-07-24-pilot-consolidation-audit.md § 3 (#19 범위) + 축2·축3 부록"

## 요구사항

- **조건**: #18 prune 완료 후 (삭제·드리프트 정정이 확정된 베이스에서 시작).
- **트리거**: 정비 3-feature 사이클의 2번.
- **기대결과**:
  - 잔존 SKILL.md 17개를 원칙·불변 조건·게이트 중심으로 재작성 — 각 100줄 이하. 축약 후보와 스킬별 불변 조건 체크리스트는 감사 축 3 (`docs/audits/2026-07-24-audit-3-instruction-excess.md`) 이 SSOT — 체크리스트 전 항목이 재작성 후에도 보존되어야 한다
  - agents/ 5개는 **계약 보존 우선** (100줄 비강제 — 감사 § 4 결정 4). 축약은 축 3 의 에이전트별 축약 후보 한도 내에서만
  - context/ SSOT 재편 (감사 축 2 § A 16 클러스터): `shared/wrapper-protocol.md` 신설 (A-2), `guardrails.md` 에 A2 fallback 정의 신설 (A-15), preamble P1 에 workspace_missing 보강 (B-6 부수), 나머지 클러스터는 제안 정본으로 통합하고 소비처는 참조로 대체
  - 지시 문서 총량 (스킬+context+agents) 30~35% 감축

## 상태 전환

_(없음)_

## 비즈니스 규칙

- **문자열 원문 계약 불변**: preamble P-단계 참조, messages.md 키, CLI 호출 시그니처, TDD Detect literal 4종, config 표 헤더 리터럴, evaluator VERIFICATION REPORT 블록 — 한 글자도 변경 금지
- **analyze 단계 번호 앵커**: project·create-feature 가 "분석 프로세스 5~6단계"·"6-5" 로 인용 — 번호 체계 변경 시 인용부 3개 스킬을 동일 커밋에서 수정
- learn 의 실측 기반 규칙 (Read rejection 1/2 vs analyze 1/3, 폴더-suffix 미strip, ≤10 자동 skip 등) 은 "자명해 보여도" 보존 — 과거 실패의 교정치
- frontmatter description 은 트리거 판단용 — 축약 대상 아님
- pytest + doctor + docs 빌드 게이트 (공통)

## 예외 케이스

- 재작성 후 100줄 초과가 불변 조건 보존과 충돌하는 스킬 — (d) 참조
- prompts-scaffold-notes 등 context 문서가 재작성된 스킬의 옛 줄번호를 인용하는 경우 — 인용 재고정 필요

## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- (없음)

### (d) 비즈니스 결정 영역
- [x] learn 처럼 불변 조건 밀도가 최고인 스킬이 100줄과 계약 보존이 충돌할 때 — 소폭 초과 (~120줄) 허용 vs references/ 분리로 100줄 사수 중 어느 쪽을 우선하나? (감사 축 3 총괄: learn 은 100줄 경계선) → 소폭 초과 ~120줄 허용 (2026-07-24 사용자 결정)
