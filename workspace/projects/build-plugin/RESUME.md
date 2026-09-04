# RESUME — pilot 정비 프로젝트 (2026-07-26 갱신)

컨텍스트 한계로 세션을 새로 시작할 때 이 문서만 읽으면 이어받을 수 있다.

## 지금까지

에이전트 진화에 따른 pilot 플러그인 정비 — 지시 과잉 해소 + 컨텍스트 비용 절감.
전수 감사 → feature 순차 사이클로 진행. **PR #9 머지 완료 · v0.10.0 릴리스 완료.**

| feature | 상태 | 결과 |
|---|---|---|
| #18 prune | ✅ READY | 미사용 46파일 삭제 · 모순 드리프트 B-1~B-9 정정 |
| #19 rewrite | ✅ READY | 스킬 17개 ≤100줄 (learn 109) · 불변 조건 195항 전수 보존 · 지시 문서 4,808 → 3,635줄 |
| #20 slim | ✅ **READY (2026-07-26 게이트 마감)** | Python 7,138 → 4,997 (절감 2,141줄, 30.1%) · 이관 3종 삭제 · MANIFEST 파서 실버그 수정 · validate.yml CI. **7기준 전건 통과** — 마지막 dogfooding 게이트는 #23 사이클이 실경로 0.10.0 에서 완주하며 충족 |
| #21 docs-sync | ✅ READY | reference/index.md · doctor-migration.md · getting-started.md 정합. 정정 대장 15행을 소스로 재검증 |
| #22 relearn | 📋 등록만 됨 | `/pilot:learn` 재실행으로 context 드리프트 3건 해소 |
| #23 파서 오탐 | ✅ **READY · PR #11 머지 완료** | 오탐 2건 소멸 — doctor `10 PASS · 1 WARN · 0 ERROR` · `features=24` 복구. `_common.py:is_feature_spec_file` (파생 판정 SSOT) + `integrity.py:_extract_declared_path` (구조 기반 4단 판정) 신설. 테스트 292건 OK (신규 8) |
| #24 update 도구 | ✅ **READY** | D1 = **(iii) 폐기** 이행 — `pilot-update.sh` 삭제 + README·getting-started·release-and-upgrade 안내 정정. `README.md:35` 설치 명령 id 오류(**신규 설치가 그대로 실패**하던 실사용자 버그)도 해소. v0.10.0 릴리스 노트 `## 업그레이드` 블록도 사용자 승인 후 정정 (백업→교체→diff 검증 이행) |
| #25 스키마 중복 | ✅ **READY (코드 변경 0)** | 결론 **(ii) 현행 유지**. `--strict` 로 명세의 유지 근거 하나는 죽었으나 **어느 쪽도 상위 집합이 아님** — CLI 미탐 2종(SKILL description 바이트 상한·version↔git tag)이 `schema.py` 존치 근거. CLI 는 릴리스 전 로컬 보조 검사로 `README.md` 에 문서화. 대조표 = `features/25-*.md` § 재실측 |
| #27 context-search | ✅ **READY (2026-09-04, PR #29)** | 섹션 단위 결정적 검색 도구. `features/27-context-search-tool.plan.md` validate 통과 · D1~D8 사용자 승인 · critic 진행. 설계 SSOT `docs/superpowers/plans/2026-09-04-context-retrieval-feature-plan.md` § F-A |
| #28 freshness | 📋 등록 (2026-09-04) | 로드 시 신선도 힌트(file:line 인용 vs git/mtime) + GUIDE·state-schema analyzed 서술 정정(F-E). #27 다음 |
| #29 frontmatter manifest | 📋 등록 (2026-09-04) | learn 산출 frontmatter 5키 + orchestrate-load `context_manifest`. #27 머지 후 |
| #30 path trigger | 📋 등록 (2026-09-04) | `.claude/rules` paths(C1) 또는 PostToolUse 훅(C2). **서브에이전트 발화 실측 선행** 후 확정 |

**릴리스 상태 (2026-07-26)**: `main` = `f73cc1c` (PR #11 머지 — #23 + #20 게이트 마감).
**v0.10.1 릴리스 진행 중** — 브랜치 `chore/release-v0.10.1` 에서 버전 표기 3곳(`plugin.json`·`mkdocs.yml`·`docs/index.md`) 동기화.
이전 릴리스: 태그 `pilot-v0.10.0` (PR #9 · `677fe7c`), 문서 사이트 배포 완료.

근거 문서 (모두 커밋됨):
- 설계: `docs/superpowers/specs/2026-07-24-pilot-skill-consolidation-design.md`
- 감사: `docs/audits/2026-07-24-pilot-consolidation-audit.md` + 축별 부록 4개
- 각 feature: `workspace/projects/build-plugin/features/{18..23}-*.md` (+ `.plan.md`·`.plan.critic.md`)

## 남은 작업 (순서대로)

1. ~~버전 표기 3곳 동기화~~ — **완료** (PR #10 머지, `main` = `229b2a8`). 사이트 랜딩 v0.10.0 표기 확인됨.
2. ~~플러그인 설치본 갱신~~ — **완료** (사용자가 `/plugin` 으로 업데이트).
   `installed_plugins.json` → `pilot@radiostart-plugins 0.10.0`, `cache/.../pilot/0.10.0/` 에 tools 8종 · doctor/ 4개 · wrapper-protocol.md 실재 확인.
   ⚠️ **세션 재시작 필요** — 세션 시작 시 로드된 경로가 고정이라, 재시작 전에는 구버전(0.4.0)이 계속 쓰인다.
3. ~~**#20 dogfooding 게이트 마감**~~ — **완료 (2026-07-26)**. `project.md` #20 목표 `[x]` 처리됨 (evaluator 단독 권한 행사), 부기된 미체크 사유 제거됨.
   - 판정 (a) 삭제 스크립트 4종 호출 시도 **0건** — planner·generator·evaluator 3구간 전건. evaluator 가 자기 보고 외 구조적 증거도 수집 (캐시 0.10.0 트리에 4종 전부 부재, 잔존 언급은 provenance 주석·릴리스 노트 3건뿐 = 호출 지시 0).
   - 판정 (b) `orchestrate-load` `files_to_read` 에 `wrapper-protocol.md`·`context/pilot/index.md` 실재 + "미등록" 힌트 부재 — planner·evaluator 두 구간에서 독립 재현.
   - 3구간 모두 로드 경로 `~/.claude/plugins/cache/radiostart-plugins/pilot/**0.10.0**`. 0.4.0 에서 보이던 MANIFEST 파서 오탐은 실경로에서 소멸.

   > **재판정 불필요.** 후속 사이클은 이 게이트를 다시 측정하지 않는다 (`project.md` 전달사항에도 동일 취지 기록됨).
4. ~~**#23 사이클**~~ — **완료, evaluator READY**. 브랜치 `skills/23-doctor-parser-false-positives` (main `229b2a8` 까지 ff).
   **미커밋 상태** — 커밋·PR 이 다음 액션이다.
   - 코드 4파일 + 신규 테스트 1파일: `_common.py`·`integrity.py`·`test_doctor_conventions.py`(+3)·`test_doctor_features_count.py`(신규 5)·`config.md.template`
   - workspace: `project.md`(#20·#23 목표 `[x]` + 전달사항 3건 신규) · `prompts/evaluator.md` · `RESUME.md` · `23-*.plan.md`
   - critic 은 사용자 판단으로 **건너뜀** (판정 규칙 3건 직접 승인).
5. **#22 사이클** — **새 세션에서 아래 명령으로 시작할 것** (2026-07-26 사용자 결정).

   ```
   /pilot:learn pilot/skills/ --domain pilot --force
   ```

   - **왜 새 세션인가** — 2026-07-26 세션에서 Phase 3 까지 진행하다 중단했다. `pilot/skills/` 는 `.md` 50 개 · 합계 **4,232 줄**이고 전부 300 줄 이하라 learn 규칙상 **전수 Read** 대상이다 (약 100k 토큰). learn 은 산출물 6 개를 재생성하려 50 개 내용을 동시에 들고 있어야 해서, 컨텍스트가 중간에 요약되면 뒤에 쓰이는 파일부터 얕아진다. **중단 시점에 쓴 파일은 없다** (abort cleanup 계약 준수).
   - **선행 조사 완료 — 재확인 불필요.** 드리프트 3 건의 소스가 모두 현행으로 갱신돼 있어 전수 해소가 예상된다:

     | # | 산출물 현행 서술 | 소스 실제 (2026-07-26 확인) |
     | --- | --- | --- |
     | 1 | `index.md` P-N 매트릭스 헤더 `P0 (memory-hint)` | `context/shared/preamble.md:19` = "P0. 관련 메모 선조회" |
     | 2 | `lifecycle.md` `tools/init_detect.py detect_languages()` | `init/SKILL.md:39` = "언어 감지 (Glob 직접 판단)" |
     | 3 | `lifecycle.md` `(진단 모드는 tools/doctor/diagnose.py)` | `doctor/SKILL.md:18` = "진단 모드(`--diagnose`)는 스크립트 없이 본 SKILL 지시문이 직접 수행" |

   - **인벤토리 실측** — 발견 50 (`SKILL.md` 17 + `context/` 27 + references 6), `config.md` `Ignore` 표가 비어 있어 제외 0 건, 테스트·벤더 해당 없음. 기존 산출물 6 개(`index`·`lifecycle`·`delivery`·`modes`·`review`·`spec`) 덮어쓰기라 `--force` 필수.
   - **Phase 2 확인 게이트는 이미 통과했다** — 새 세션에서 같은 통계가 나오면 그대로 진행하면 된다.
   - **검증** — 재학습 후 `grep -rn "memory-hint\|init_detect\|diagnose\.py" workspace/context/pilot/` 이 0 건이어야 한다 (명세가 라인 번호 아닌 **문자열 기준** 검증을 요구).
   - **미해소 Open Question (d)** — 재학습이 3 건을 전부 덮지 못하면 drift-protocol § B(승인 하 직접 정정)로 전환할지, learn 스킬 커버리지 결함으로 별도 처리할지 아직 결정 안 됨.
6. ~~**#24 사이클**~~ — **완료 (2026-07-26)**. 브랜치 `skills/24-pilot-update-tool`. D1~D4 전건 이행.
   - **`pilot/tools/pilot-update.sh` 는 삭제됐다 — 되살리지 말 것.** 지원 업그레이드 경로는 `/plugin marketplace update radiostart-plugins` → `/plugin update pilot@radiostart-plugins` → **세션 재시작** 하나뿐이고, `/plugin` 자체가 없는 환경은 **미지원**으로 문서에 명시했다.
   - D2 (게시된 v0.10.0 Release 본문) 도 사용자 명시 승인 후 정정 완료 — 백업 → `## 업그레이드` 블록만 교체 → `gh release edit --notes-file` → `--json body` 재취득 diff 로 해당 블록 외 불변 확인.
   - evaluator 는 최초에 D2 범위 분리를 **기각**했다 (plan D2 = "정정한다" 가 기록된 사용자 결정인데 유예를 뒷받침할 기록이 없었음). 구현 주체가 자기 커밋에서 요구사항을 완화하면 순환 논증이 된다는 지적 — 후속 사이클도 같은 기준으로 판정된다.
7. ~~**#25 사이클**~~ — **완료 (2026-07-26, 코드 변경 0)**. 결론 (ii) 현행 유지 — `schema.py`(410줄)·`validate.yml` 무변경. 재개 불필요.
   - code-review 가 blocking 1건을 잡았다: README 릴리스 절차에 "manifest JSON 문법 파손은 CLI 만 잡는다" 를 실측인 것처럼 적었으나 **양쪽 다 잡는다**. 2026-07-25 구표의 "(문법 파손은 미검증)" 을 "미탐" 으로 오독한 결과 — **미검증을 실측으로 승격시키지 말 것**. 정정 완료.

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
- ~~doctor WARN 4건 중 3건이 오탐~~ — **#23 로 해소 (2026-07-26)**. 현재 `10 PASS · 1 WARN · 0 ERROR`, 남은 1건은 `plugin_version` 정상 감지.
- **orchestrate-load placeholder leak (미등록 · 후속 feature 후보)** — `parse_lang_config` (`pilot/tools/orchestrate-load.py:141-172`) 가 config.md 같은 표를 파싱하며 `test_framework_hints=자유 텍스트` 같은 **플레이스홀더를 실값으로 반환**한다 (#23 evaluator step 1 반환 JSON 에서 실측). 성격은 #23 (A) 와 동일하나 wrapper hints 출력이 바뀌므로 별건. #23 이 만든 `integrity.py:_extract_declared_path` 를 재사용해 해소 가능.
- **features 명명 경계** — spec 파일명 stem 에 점을 쓰면 (`05-v1.0-release.md`) 파생 산출물로 오판정돼 미카운트된다. `test_doctor_features_count.py::DottedSpecStemNotCounted` 가 이 경계를 고정. 명명 규약을 바꾸는 후속 feature 는 이 테스트를 먼저 볼 것.
