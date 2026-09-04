# #22 정비 후속 — context 드리프트 재학습 (D-2)

> source: prompt
> created: 2026-07-25T00:00:00Z
> user_prompt: "#21 planner 가 발견한 `workspace/context/pilot/` 잔존 드리프트 3건 — 본 범위 제외하고 별도 feature 로 분리 (D-2 결정)"
> scope_extended: 2026-09-04 — #24 planner 가 발견한 `lifecycle.md:79` `--fix` 마이그레이션 서술(4번째 건) 을 사용자 결정으로 편입

## 요구사항

- **조건**: #20 완료 (이관 3종 `diagnose.py`·`memory-hint.py`·`init_detect.py` 삭제) + #21 PR 머지.
- **트리거**: `workspace/context/pilot/` 산출물이 삭제된 스크립트를 현행 구현으로 서술 중. #21 planner 실측 → critic C6 로 1건 → **3건** 정정된 인벤토리 + 2026-09-04 #24 planner 보고 1건(4번째 행) 이 스코프 근거다.
- **기대결과**: 아래 4건이 현행 구현과 일치하도록 재학습으로 해소된다.

  | # | 위치 | 현행 서술 | 실측 |
  | --- | --- | --- | --- |
  | 1 | `workspace/context/pilot/index.md:43` | P-N 매트릭스 헤더 `P0 (memory-hint)` | `memory-hint.py` 는 #20 스텝 4b 삭제. P0 은 "MEMORY.md 색인 직접 선별 Read" (`preamble.md`) |
  | 2 | `workspace/context/pilot/lifecycle.md:22` | "`tools/init_detect.py` `detect_languages()` → … default 패턴 주입" | `init_detect.py` 는 #20 스텝 4c 삭제 — `ls pilot/tools` 8종에 부재. init SKILL 의 Glob 직접 판단으로 이관 |
  | 3 | `workspace/context/pilot/lifecycle.md:69` | "(진단 모드는 `tools/doctor/diagnose.py`)" | `diagnose.py` 는 #20 스텝 4a 삭제 — `pilot/tools/doctor/` = `__init__`·`_common`·`integrity`·`schema` 뿐 |
  | 4 | `workspace/context/pilot/lifecycle.md:79` | "`--fix` = v0.1.0→v0.2.0 마이그레이션 질의 (`references/migration.md`)" | 실제 `pilot/skills/doctor/SKILL.md:34` 의 `--fix` 는 gitignore 주입·STATE 정리·schema 업그레이드. `doctor/references/` 는 #20 에서 삭제되어 부재 (2026-09-04 #24 planner 드리프트 보고로 편입) |

  - 함께 흡수되는 이월분: `project.md:157` (#19) 의 `spec.md`·`index.md` SKILL.md 라인 인용 stale. **단 그 항목은 `lifecycle.md` 2건을 커버하지 못하므로** 본 feature 가 상위 집합이다.

## 상태 전환

_(없음)_

## 비즈니스 규칙

- **`workspace/context/` 산출물 직접 Edit 금지** (drift-protocol § A). 해소 경로는 `/pilot:learn` 재실행 단일 수단이다.
- 재학습 결과가 위 3건을 실제로 덮었는지 **재학습 후 grep 으로 확인**한다 — learn 이 해당 문단을 재생성하지 않으면 드리프트가 남는다.
- 라인 번호는 재학습 시점에 이동한다. 위 표의 `:NN` 은 등록 시점 좌표이며, 검증은 **문자열 기준**(`memory-hint`·`init_detect`·`diagnose.py`·`references/migration.md`)으로 한다.

## 예외 케이스

- `/pilot:learn` 재실행이 3건 중 일부만 갱신할 수 있다 — learn 이 읽는 소스가 해당 서술의 출처와 다를 경우. 그때는 drift-protocol § B (승인 하 정정) 경로로 전환할지 판단이 필요하다.
- `workspace/context/scope/pilot.md`·`rules/pilot.md` 는 사용자 커스텀 layer 로 미작성 — 재학습 대상 아님.

## Open Questions

### (a) 같은 도메인 추가 read 필요
- (없음)

### (b) cross-domain 산출물 부재
- (없음)

### (c) 외부 시스템 spec 부재
- (없음)

### (d) 비즈니스 결정 영역
- [ ] `/pilot:learn` 재실행이 3건을 전부 덮지 못할 경우 — drift-protocol § B 로 전환해 승인 하 직접 정정할 것인가, 아니면 learn 스킬 자체의 커버리지 결함으로 보고 별도 처리할 것인가
