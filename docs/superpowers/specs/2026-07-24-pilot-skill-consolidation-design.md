# Pilot 스킬 정비 (skill consolidation) 설계

- 날짜: 2026-07-24
- 상태: 설계 승인 대기
- 배경: 에이전트(모델) 능력 향상으로 세부 절차 지시가 과잉이 됨. 지시 축약과
  컨텍스트·토큰 비용 절감이 목적. 인터뷰로 확정한 방향:
  - 동기: 지시 과잉 해소 + 컨텍스트 비용 절감
  - 대상 선정: 전수 감사 후 후보 제안·승인
  - 축약 강도: 원칙 중심 재작성 (각 SKILL.md 100줄 이하)
  - Python: 미사용 삭제 + 모델 판단 이관 + 거대 파일 슬림화 모두
  - 범위: pilot 플러그인 전체 (skills 17개, skills/context/, tools/, agents/,
    hooks/, docs·docs-site)

## 1. 목표와 성공 기준

현황 (2026-07-24 기준):

| 영역 | 현재 |
|---|---|
| SKILL.md 17개 | 2,071줄 (최장 learn 207 · analyze 202 · autopilot 198) |
| skills/context/ 19개 문서 | 1,726줄 |
| agents/ 5개 | 492줄 |
| 지시 문서 합계 | 4,289줄 |
| tools/ Python (테스트 제외) | 약 6,600줄 (integrity.py 2,160 · confluence.py 865 · orchestrate-load.py 762) |
| hooks/ 셸 | 490줄 |

성공 기준:

1. 각 SKILL.md 100줄 이하 — 절차 나열 대신 원칙·불변 조건·게이트 중심 서술
2. 지시 문서 총량(스킬+context+agents) 40% 이상 감축 → 약 2,500줄 이하
3. tools/ Python 30% 이상 감축 (감사 결과로 최종 목표 확정)
4. 동작 보존: pytest 전체 통과, `/pilot:doctor` 클린, 정비 완료 후 파이프라인
   1사이클 실완주(dogfooding)로 검증

## 2. 감사 방법론 (이 세션에서 선행)

서브에이전트 병렬 fan-out으로 4개 축을 감사하고
`docs/audits/2026-07-24-pilot-consolidation-audit.md` 로 통합한다.

1. **참조 그래프**: 스킬·훅·에이전트·hooks.json 이 실제 로드/실행하는 파일을
   추적해, 어디서도 참조되지 않는 스킬·context 문서·스크립트·훅을 검출
2. **중복 지시**: SKILL.md ↔ context/shared ↔ agents/ 간 반복 지시 검출
   (SSOT 위반). 정본 위치를 지정하고 나머지는 참조로 대체할 후보 목록화
3. **지시 과잉**: 모델 판단으로 대체 가능한 단계별 절차·방어적 서술·자명한
   설명을 스킬별로 식별
4. **Python**: 미사용 스크립트, 결정적 검증이 불필요해 모델 판단으로 이관
   가능한 로직, 과대 파일(integrity.py 등)의 축소·분할 후보 분석

보고서 형식: 후보별 **근거 · 예상 절감량 · 위험도(상/중/하)**. 사용자 승인을
받은 후보만 feature spec에 반영한다.

## 3. Feature 구성과 실행 순서

감사 승인 후 build-plugin 프로젝트에 3개 feature를 등록하고 각각 pilot
파이프라인(@pilot-planner → @pilot-generator → @pilot-evaluator, 필요 시
@pilot-planner-critic)으로 순차 실행한다.

| 순서 | Feature | 내용 | 선행 이유 |
|---|---|---|---|
| 1 | #18 prune | 감사 승인된 미사용 스킬·context 문서·스크립트·훅 삭제 + 참조 정리 | 삭제 확정이 먼저여야 #19 재작성이 죽은 참조를 만들지 않음 |
| 2 | #19 rewrite | #18 이후 잔존 SKILL.md 전체 + agents 원칙 중심 재작성(각 100줄 이하), context/ 재편 | 스킬별 불변 조건 체크리스트를 spec에 선추출 → evaluator 가 보존 검증 |
| 3 | #20 slim | 거대 스크립트 축소·분할, 모델 이관 항목의 스크립트·테스트 삭제 | #19 확정 후 스킬 지시문에 이관 원칙 반영 여부를 diff 로 확인 가능 |

각 feature는 독립 커밋·독립 사이클로 진행해 사이클별 롤백이 가능하다.

## 4. 검증·안전장치

- **사이클 공통 게이트**: pytest 전체 통과 + `/pilot:doctor` 클린 +
  `docs_build.py` 재빌드로 문서 링크 정합 확인
- **#19 안전장치**: 스킬별 불변 조건 체크리스트(게이트·SSOT 경로·상태 전이)를
  spec 요구사항으로 명문화 — 축약 중 동작 누락이 evaluator 게이트에서 걸림
- **#20 안전장치**: 스크립트 삭제·이관 항목은 해당 스킬 지시문에 원칙이 실제
  반영됐는지 diff 확인 후 삭제
- **최종 검증**: 정비 완료 후 파이프라인 1사이클 실완주(dogfooding)
- docs-site 는 각 feature 의 변경분 반영만 수행. 문서 사이트 자체의 대규모
  재작성은 이번 범위 외

## 5. 범위 외 (Out of scope)

- 새 기능 추가 (정비 전용)
- docs-site 구조·테마 개편
- workspace/ 하위 프로젝트 산출물 정리 (build-plugin 기록은 이력이므로 보존)
