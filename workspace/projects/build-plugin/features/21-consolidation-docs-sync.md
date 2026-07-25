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
  - **(범위 추가 — 사용자 승인 2026-07-25, S1)** `pilot/docs/tutorial/getting-started.md` Troubleshooting 3곳 정정 — `:277` 삭제된 `OH-1` ID · `:293` 삭제된 config 표 스키마 검증 · `:311-314` 삭제된 MANIFEST 헤더 정합성 검사. 절차를 따라도 아무 오류가 보고되지 않아 사용자가 막히는 상태
  - docs 빌드·링크 게이트 통과 (`docs_build.py --check`). **주의 — `test_doc_links` 는 `SCAN_DIRS = ("skills", "agents")` 로 `pilot/docs/` 를 스캔하지 않는다** (`pilot/tests/tools/test_doc_links.py:31`). docs 링크 검증은 동일 로직을 `pilot/docs/` 에 적용하는 별도 게이트로 대체 (plan § 게이트 G4)

## 상태 전환

_(없음)_

## 비즈니스 규칙

- 문서(md)만 수정 — Python·SKILL.md 변경 금지
- `pilot/docs/PLAN-manual.md` 는 mkdocs 제외 메타 산출물 — 범위 외
- 생성물 디렉터리 (`docs/reference/{agents,skills,tools}/`) 는 직접 수정 금지 (docs_build 재생성 대상)

## 예외 케이스

- doctor-migration.md 를 삭제·개명하면 인바운드 링크 5곳이 깨진다 — 파일명 유지가 안전 경로
- `mkdocs.yml:98` nav 라벨이 `Doctor 진단·마이그레이션` 인데 yml 은 md-only 범위 밖 — 페이지 H1 에서 "마이그레이션" 을 빼면 nav ↔ 제목이 어긋난다. schema 마이그레이션(`v1`→`v1.2`)은 현행 기능이므로 제목 유지가 사실에도 부합
- **본 사이클은 설치 캐시(실경로)를 검증하지 않는다** — wrapper 가 로드하는 것은 캐시 `0.4.0`, 저장소는 `0.9.0` (마켓플레이스가 GitHub 클론이라 갱신에 머지·배포 선행 필요). 따라서 #20 dogfooding 게이트 판정은 **저장소 사본 기준으로 축소** 확정(D-1 (b), 2026-07-25). "#21 완주 = #20 실사용 검증" 으로 읽으면 안 되며, 배포 후 실경로 1회 재확인이 **후속 확인 필요** 로 남는다

## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- (없음)

### (d) 비즈니스 결정 영역
- (없음 — dogfooding 소재는 D3 에서 사용자 승인 완료)
- [x] `getting-started.md` Troubleshooting 3곳을 본 feature 범위에 포함할 것인가 (planner 실측 발견) → **포함** (2026-07-25 승인, S1)
- [x] 설치 캐시 0.4.0 ↔ 저장소 0.9.0 격차로 실경로 미검증 — 게이트를 어떻게 처리할 것인가 → **저장소 사본 기준으로 축소 + 한계 명시 기록, 배포 후 재확인은 후속 과제** (2026-07-25 승인, D-1 (b))
- [x] planner 가 발견한 나머지 드리프트 2건(`context/pilot/index.md:43` P0 라벨 · `config.md:32-33` conventions 오탐) 처리 → **본 범위 제외, 별도 feature 로 분리** (2026-07-25 승인, D-2·D-3)
