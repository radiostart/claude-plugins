# RESUME — pilot 정비 프로젝트 (2026-07-26 갱신)

컨텍스트 한계로 세션을 새로 시작할 때 이 문서만 읽으면 이어받을 수 있다.

## 지금까지

에이전트 진화에 따른 pilot 플러그인 정비 — 지시 과잉 해소 + 컨텍스트 비용 절감.
전수 감사 → feature 순차 사이클로 진행. **PR #9 머지 완료 · v0.10.0 릴리스 완료.**

| feature | 상태 | 결과 |
|---|---|---|
| #18 prune | ✅ READY | 미사용 46파일 삭제 · 모순 드리프트 B-1~B-9 정정 |
| #19 rewrite | ✅ READY | 스킬 17개 ≤100줄 (learn 109) · 불변 조건 195항 전수 보존 · 지시 문서 4,808 → 3,635줄 |
| #20 slim | ⏳ **NOT_READY — 게이트 1건만 남음** | Python 7,138 → 4,997 (절감 2,141줄, 30.1%) · 이관 3종 삭제 · MANIFEST 파서 실버그 수정 · validate.yml CI. **7기준 중 6 통과, dogfooding 1건 미충족** |
| #21 docs-sync | ✅ READY | reference/index.md · doctor-migration.md · getting-started.md 정합. 정정 대장 15행을 소스로 재검증 |
| #22 relearn | 📋 등록만 됨 | `/pilot:learn` 재실행으로 context 드리프트 3건 해소 |
| #23 파서 오탐 | 📋 등록만 됨 | doctor 파서 오탐 2건 (conventions 플레이스홀더 · features 카운트) |
| #24 update 도구 | ⚠️ **NOT_READY (저장소 내 전건 통과)** | D1 = **(iii) 폐기** 실행 — `pilot-update.sh` 삭제 + README·getting-started·release-and-upgrade 안내 정정. `README.md:35` 설치 명령 id 오류(신규 설치 실패)도 함께 해소. **잔여 1건 = v0.10.0 릴리스 노트 `## 업그레이드` 블록** (저장소 밖·`immutable:false`). 커밋 `b4e73e3`+`f0f01d5` |
| #25 스키마 중복 | ✅ **READY (코드 변경 0)** | 결론 **(ii) 현행 유지**. `--strict` 로 명세의 유지 근거 하나는 죽었으나 어느 쪽도 상위 집합 아님 — CLI 미탐 2종(description 바이트 상한·version↔tag)이 `schema.py` 존치 근거. CLI 는 릴리스 전 로컬 보조 검사로 문서화. 대조표 = `features/25-*.md` § 재실측 |

**릴리스 상태**: `main` = `677fe7c` (PR #9 머지). 태그 `pilot-v0.10.0`. 릴리스 노트 게시됨.
문서 사이트 배포 완료 (`Deployed 677fe7c`).

근거 문서 (모두 커밋됨):
- 설계: `docs/superpowers/specs/2026-07-24-pilot-skill-consolidation-design.md`
- 감사: `docs/audits/2026-07-24-pilot-consolidation-audit.md` + 축별 부록 4개
- 각 feature: `workspace/projects/build-plugin/features/{18..23}-*.md` (+ `.plan.md`·`.plan.critic.md`)

## 남은 작업 (순서대로)

1. ~~버전 표기 3곳 동기화~~ — **완료** (PR #10 머지, `main` = `229b2a8`). 사이트 랜딩 v0.10.0 표기 확인됨.
2. ~~플러그인 설치본 갱신~~ — **완료** (사용자가 `/plugin` 으로 업데이트).
   `installed_plugins.json` → `pilot@radiostart-plugins 0.10.0`, `cache/.../pilot/0.10.0/` 에 tools 8종 · doctor/ 4개 · wrapper-protocol.md 실재 확인.
   ⚠️ **세션 재시작 필요** — 세션 시작 시 로드된 경로가 고정이라, 재시작 전에는 구버전(0.4.0)이 계속 쓰인다.
3. **#20 dogfooding 게이트 마감** — 재시작 후 실경로에서 1사이클 완주.
   판정 기준: (a) 사이클 중 삭제 스크립트 4종 호출 시도 0건 (b) orchestrate-load JSON 에 도메인 진입 파일 실재.
   통과 시 `project.md` 의 #20 목표를 `[x]` 로 (evaluator 단독 권한) + 부기된 미체크 사유 제거.

   > **버전 확인과 게이트 증거는 별개다.**
   > - **로드 버전 확인 (즉시·무비용)** — 아무 `/pilot:` 스킬을 부르면 헤더에 `Base directory for this skill: .../pilot/{version}/skills/{name}` 이 찍힌다. `0.10.0` 이면 실경로 진입 완료.
   > - **orchestrate-load 증거** — 세션을 여는 것만으로는 실행되지 않는다. `orchestrate-load.py` 는 **서브에이전트 wrapper 가 호출 시 최우선 실행**하므로, 다음 사이클의 `@pilot-planner` 호출이 곧 판정 (b) 의 증거가 된다. 판정 (a) 는 사이클 전체를 봐야 한다.
4. **#23 사이클** — `@pilot-planner` → (critic) → `@pilot-generator` → `@pilot-evaluator`.
   브랜치는 이미 `skills/23-doctor-parser-false-positives` 로 생성돼 있다.
5. **#22 사이클** — `/pilot:learn` 재실행. **반드시 세션 재시작 이후에** — 구버전 스킬로 재학습하면 옛 서술을 다시 학습한다.
6. ~~**#24 사이클**~~ — **저장소 내 전건 완료** (2026-07-26, 브랜치 `skills/24-pilot-update-tool`). `pilot-update.sh` 는 **삭제됐다 — 되살리지 말 것**. 잔여는 배포된 v0.10.0 릴리스 노트 `## 업그레이드` 블록 1건뿐이고, 절차는 `features/24-pilot-update-tool.plan.md` 스텝 2 (백업 → 취득 → 교체 → diff 검증). 사용자가 범위 제외를 명시 승인하면 그 기록으로 대체한다.
7. ~~**#25 사이클**~~ — **완료 (코드 변경 0)**. 결론 (ii) 현행 유지 — `schema.py`·`validate.yml` 무변경. 재개 불필요.

## 이어받을 때 주의

- 사이클 규약: 에이전트 자동 체인 금지 — 각 단계는 사용자 명시 호출.
- generator 는 코드만 커밋 (workspace/ 는 별도 커밋), `project.md` `## 목표` 체크박스는 evaluator 단독 권한.
- `main` 직접 커밋·푸시 금지 (한 번 실수해 브랜치로 옮긴 전례 있음).
- `workspace/context/` 산출물 직접 Edit 금지 — `/pilot:learn` 재실행 몫 (drift-protocol § A).
- **#20 은 "실경로 미검증" 이 유일한 미충족 사유다.** #21 READY 를 #20 게이트 통과로 읽지 말 것.
- 미처리 전달사항은 v0.4.0 이월로 사용자 승인됨 (unchecked 유지가 정상).

## 알려진 잔존 결함 (문서화됨, 미수정)

- `skills/doctor/SKILL.md:34`·`:79-80` — "검사는 비파괴, 파일 수정 안 함" 이 실측과 반대 (`.gitignore` secret 주입은 `--fix` 없이도 실행). 파생물 `reference/skills/doctor.md:71-72` 를 통해 사이트에도 배포됨. 후속 feature 대상 (R-3).
- `pilot/docs/PLAN-manual.md` 4곳 (`:19`·`:46`·`:168`·`:264`) — 구 `doctor-migration.md` 구조 기술. mkdocs 제외 메타 산출물.
- doctor WARN 4건 중 3건이 오탐 — #23 대상 (conventions 2 + features 카운트 1). 나머지 1건은 `plugin_version` 정상 감지.
