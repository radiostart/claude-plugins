# pilot 플러그인 정비 전수 감사 (통합 보고서)

- 일자: 2026-07-24
- 설계: [`docs/superpowers/specs/2026-07-24-pilot-skill-consolidation-design.md`](../superpowers/specs/2026-07-24-pilot-skill-consolidation-design.md)
- 방법: 4축 병렬 서브에이전트 감사. 축별 상세는 부록 참조 —
  - [축 1 참조 그래프](2026-07-24-audit-1-reference-graph.md)
  - [축 2 중복 지시](2026-07-24-audit-2-duplication.md)
  - [축 3 지시 과잉](2026-07-24-audit-3-instruction-excess.md)
  - [축 4 Python 도구](2026-07-24-audit-4-python.md)

## 1. 핵심 결론

1. **미사용 파일은 거의 없다.** 이전 감사(2026-07-10)가 고아 도구를 정리해 참조 위생이 좋다. 확실한 삭제 후보는 `tests/fixtures/handoff-quality/` 4파일(86줄)뿐이고, 나머지는 사람용 문서·수동 하네스로 의도된 약한 참조다. 깨진 참조 0건.
2. **감축 여력의 본체는 "지시 과잉"과 "Python 내부"다.** 스킬+에이전트 2,563줄 → 약 1,490줄(-42%) 재작성 가능. tools/ 는 삭제가 아니라 integrity.py 내부 슬림화(-1,100)와 소형 스크립트 4종의 모델 이관이 주 감축원이다.
3. **모순 드리프트 9건 발견** (축 2 § B). 특히 위험도 상 3건 — INDEX.md 의 STATE 갱신 구규칙(B-1), "planner 가 실패 테스트 작성" 구서술(B-2), tdd SKILL 의 Detect literal 하드코드(A-6) — 은 재작성 이전에 정정해야 한다.
4. **축약의 실제 위험은 문자열 계약이다.** preamble P-단계, messages.md 키, CLI 시그니처, Detect literal, 표 헤더, analyze 단계 번호 앵커(project·create-feature 가 번호로 인용) 등은 한 글자도 바꾸면 안 되는 축이며, 축 3 의 스킬별 불변 조건 체크리스트가 #19 의 검증 기준이 된다.

## 2. 절감 추정 통합

| 영역 | 현재 | 감사 기반 추정 | 비고 |
|---|---|---|---|
| SKILL.md 17 + agents 5 | 2,563줄 | → 약 1,490줄 (-42%) | 축 3. 단 evaluator 등 계약 밀도 높은 에이전트는 -15% 수준이 한계 |
| context/ 등 공유 문서 | 1,726줄 | 약 -150줄 + 재편 여지 | 축 2 중복 142줄 (일부는 위 재작성과 중복 계상) + wrapper-protocol 신설 효과 |
| **지시 문서 합계** | 4,289줄 | → **약 2,900~3,000줄 (-30~32%)** | **spec 의 40% 목표보다 실측이 낮음 — § 4 결정 3** |
| tools/ Python | 7,109줄 | -2,100~-2,500 (-30~35%) | spec 의 30% 목표 충족. schema.py 처분에 따라 변동 |
| tests/ Python | 4,767줄 | 약 -1,380 (-29%) | 삭제·이관과 연동 |

## 3. Feature 반영 매핑

- **#18 prune** — 확정 삭제·정정만 (동작 변경 없음):
  - `tests/fixtures/handoff-quality/` 4파일 삭제 (+ § 4 결정 1 의 승인 범위)
  - 모순 드리프트 9건 정정 (B-1~B-9 판정대로: INDEX.md·GUIDE.md 구서술, pr SKILL 자기순환 오문, 경로 표기 등)
  - stale 참조 정리: `skills/doctor/SKILL.md:46` 의 존재하지 않는 `validate.yml` 언급 (§ 4 결정 2 와 연동), `docs_build.py` stale 출력 정리 로직
- **#19 rewrite** — 원칙 중심 재작성:
  - 대상: 잔존 SKILL.md 전체 + agents 5 (각 100줄 이하 — 단 evaluator 등은 계약 보존 우선, § 4 결정 4)
  - context/ 재편: `wrapper-protocol.md` 신설(A-2), 중복 클러스터 16건 정본 통합, `A2 fallback` 정의 신설(A-15), preamble P1 에 workspace_missing 보강(B-6)
  - 검증 기준: 축 3 의 스킬별 불변 조건 체크리스트를 feature spec 요구사항으로 편입
  - 특별 주의: analyze 단계 번호 앵커(project·create-feature 와 동일 커밋 수정), learn 의 실측 기반 규칙(1/2 vs 1/3 등), autopilot 기계 계약
- **#20 slim** — Python 감축:
  - integrity.py: 마이그레이션 246줄 삭제, md 표 lint 4종 이관(-642), Onboarding Health 축소(-221)
  - 이관 후 삭제: diagnose.py, memory-hint.py, init_detect.py (+ schema.py — § 4 결정 2) — 각 호출처 문서 수정과 동일 커밋
  - 슬림화: verify-report-lint validate 이관(파서는 auto_pilot 흡수), doctor.py re-export 정리, orchestrate-load 중복 유틸 정리
  - 연동 테스트·픽스처 삭제 (~1,380줄)
  - 이관 부적합 판정 (유지): plan-validate.py(autopilot hard-stop 신호), regen-verify.py(모델 자기 인증 방지), auto_pilot.py(전이 결정성), confluence.py, slack-notify.py, docs_build.py

## 4. 승인 필요 결정

1. **삭제 범위** — 확실 후보(handoff-quality 4파일) 외에 다음을 삭제할지:
   (a) `v0.1.0-baseline/` 수동 회귀 하네스 37파일+diff.sh (~1,453줄 — 자동 테스트 미사용, 마이그레이션 삭제 시 존재 의의 대부분 소멸),
   (b) `examples/code-review/README.md` (53줄, 사람용),
   (c) 사람용 문서 3종 (`lifecycle/INDEX.md`·`setup/README.md`·`issues/example/issue.md`)
2. **doctor/schema.py 처분** — 모델 이관 후 삭제(-410줄) vs stale 된 CI(`validate.yml`)를 실제로 복원하고 유지(감사 권장)
3. **지시 문서 감축 목표** — spec 의 40% 를 실측 기반 30~35% 로 조정할지
4. **에이전트 100줄 규칙** — 스킬에만 적용하고 에이전트는 "계약 보존 우선"으로 예외 둘지 (감사 권장)
