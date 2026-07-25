# RESUME — pilot 정비 프로젝트 (2026-07-25 갱신)

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
| #24 update 도구 | 📋 등록만 됨 | `pilot-update.sh` 경로 stale + 설계 한계 + 잘못된 안내. **존치 여부 결정이 선행** |

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
   통과 시 `project.md:39` 의 #20 목표를 `[x]` 로 (evaluator 단독 권한) + 부기된 미체크 사유 제거.
4. **#23 사이클** — `@pilot-planner` → (critic) → `@pilot-generator` → `@pilot-evaluator`.
   브랜치는 이미 `skills/23-doctor-parser-false-positives` 로 생성돼 있다.
5. **#22 사이클** — `/pilot:learn` 재실행. **반드시 세션 재시작 이후에** — 구버전 스킬로 재학습하면 옛 서술을 다시 학습한다.
6. **#24 사이클** — `pilot-update.sh` 존치 여부 결정이 선행. 브랜치 `skills/24-pilot-update-tool` 에 등록분이 있다.

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
