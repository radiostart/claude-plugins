# RESUME — pilot 정비 프로젝트 (2026-07-25 세션 인수인계)

컨텍스트 한계로 세션을 새로 시작할 때 이 문서만 읽으면 이어받을 수 있다.

## 지금까지 (브랜치 `docs/pilot-skill-consolidation-spec`)

에이전트 진화에 따른 pilot 플러그인 정비 — 지시 과잉 해소 + 컨텍스트 비용 절감.
전수 감사 → 3-feature 순차 사이클로 진행했고 **#18·#19·#20 구현 완료**.

| feature | 상태 | 결과 |
|---|---|---|
| #18 prune | ✅ evaluator READY | 미사용 46파일 삭제 · 모순 드리프트 B-1~B-9 정정 · docs_build stale 정리 |
| #19 rewrite | ✅ evaluator READY | 스킬 17개 ≤100줄 (learn 109) · 에이전트 계약 보존 재작성 · context SSOT 재편. 지시 문서 4,808 → 3,635줄 |
| #20 slim | ⏳ **구현 완료, evaluator 미실행** | tools/ Python 절감 **2,141줄** (7,138 → 4,997, 감사 분모 대비 30.1%) · 이관 3종 삭제 · MANIFEST 파서 실버그 수정 · validate.yml CI 신설 |
| #21 docs-sync | 📋 등록만 됨 | #20 의 dogfooding 게이트 소재 (D3 사용자 승인) |

근거 문서 (모두 커밋됨):
- 설계: `docs/superpowers/specs/2026-07-24-pilot-skill-consolidation-design.md`
- 감사: `docs/audits/2026-07-24-pilot-consolidation-audit.md` + 축별 부록 4개
- 각 feature: `workspace/projects/build-plugin/features/{18,19,20,21}-*.md` (+ `.plan.md`·`.plan.critic.md`)

## 남은 작업 (순서대로)

1. **#21 dogfooding 사이클 완주** — `@pilot-planner` → (critic 선택) → `@pilot-generator` → `@pilot-evaluator`.
   대상: `features/21-consolidation-docs-sync.md` (reference/index.md 도구 목록 정정 + how-to/doctor-migration.md 현행화, md 만 수정).
   이 사이클 자체가 #20 의 최종 게이트다.
2. **#20 evaluator 호출** — dogfooding 완주 후. 판정 기준 (critic C8 합의):
   - (a) 사이클 중 삭제 스크립트 4종 (`diagnose.py`·`memory-hint.py`·`init_detect.py`·`verify-report-lint.py`) 호출 시도 grep **0건**
   - (b) orchestrate-load JSON 에 도메인 진입 파일 실재 — #20 generator 가 선행 실측 확인 완료
   - `.plan.md` 의 dogfooding 체크 항목이 미체크로 남아 있으니 evaluator 가 판정 후 처리
3. **PR 생성** — `/pilot:pr` (base 는 config 기준 자동 결정). 커밋 20여 개가 이미 브랜치에 쌓여 있다.
4. **(PR 머지 후) `/pilot:learn` 재실행** — `workspace/context/pilot/*.md` 의 라인 인용이 #19·#20 재작성으로 stale. drift-protocol 에 따라 직접 Edit 금지, learn 재실행 몫.

## 이어받을 때 주의

- 사이클 규약: 에이전트 자동 체인 금지 — 각 단계는 사용자 명시 호출.
- generator 는 코드만 커밋 (workspace/ 는 별도 커밋), project.md `## 목표` 체크박스는 evaluator 단독 권한.
- 미처리 전달사항 19건은 v0.4.0 이월로 사용자 승인됨 (unchecked 유지가 정상).
- spec 의 "지시 문서 30~35% 감축" 은 #19 단독 24.4% + #20 합산으로 판정하기로 사용자와 합의됨.
