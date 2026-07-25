# #21 정비 후속 — 문서 정합 (#20 반영)

> source: prompt
> created: 2026-07-25T01:21:31Z
> user_prompt: "#20 slim 의 삭제·이관 결과를 docs/ 에 반영 — 삭제 도구 목록 정정, doctor-migration how-to 개편. dogfooding 사이클 소재 (D3 결정)"

## 요구사항

- **조건**: #20 완료 상태 (커밋 bb4f222~adf85db — 이관 3종·verify-report-lint 삭제, 마이그레이션 제거, doctor --diagnose 지시문화).
- **트리거**: #20 최종 게이트인 dogfooding 1사이클의 소재 (planner → generator → evaluator 완주).
- **기대결과**:
  - `pilot/docs/reference/index.md:25` 의 도구 목록에서 삭제된 3종 (`init_detect`·`verify-report-lint`·`memory-hint`) 제거 (`diagnose` 언급 여부도 확인)
  - `pilot/docs/how-to/doctor-migration.md` 를 #20 현실에 맞게 개편 — v0.1→v0.2 마이그레이션 절차 서술 제거, `--fix`(상태 보정)·`--diagnose`(지시문 기반 진단) 현행 거동 반영. 인바운드 링크 5곳 (getting-started·drift-protocol·release-and-upgrade·modes·how-to/index) 은 유지되도록 파일명·앵커 보존
  - docs 빌드·링크 게이트 통과 (`docs_build.py --check`·`test_doc_links`)

## 상태 전환

_(없음)_

## 비즈니스 규칙

- 문서(md)만 수정 — Python·SKILL.md 변경 금지
- `pilot/docs/PLAN-manual.md` 는 mkdocs 제외 메타 산출물 — 범위 외
- 생성물 디렉터리 (`docs/reference/{agents,skills,tools}/`) 는 직접 수정 금지 (docs_build 재생성 대상)

## 예외 케이스

- doctor-migration.md 를 삭제·개명하면 인바운드 링크 5곳이 깨진다 — 파일명 유지가 안전 경로

## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- (없음)

### (d) 비즈니스 결정 영역
- (없음 — dogfooding 소재는 D3 에서 사용자 승인 완료)
