# Plan Critic — #21 정비 후속 — 문서 정합 (#20 반영)

> 입력 plan: `features/21-consolidation-docs-sync.plan.md` (검토 시각 2026-07-25T01:55:21Z)
> 입력 feature: `features/21-consolidation-docs-sync.md`
> 페르소나: `personas.planner-critic` (red-team)
> focus 반영: 없음 (`orchestrate-load --phase planner-critic` → `focus: null`)
> 검산 기준: HEAD `e1aa755` · 게이트 G1~G7 전건 실행 · 정정 대장 12행 + S1 3행 소스 대조

## 챌린지

### C1 — G7 은 축소 후 "게이트" 로서 남는 게 없다. 그런데 #20 완료 귀속이 정의돼 있지 않다
- **severity**: blocking
- **category**: premise
- **plan 인용**: 단계 3 / § 게이트 G7 (`21-*.plan.md:123-133`) · § 교차 의존 (`:287`) · `20-consolidation-slim.plan.md:74-82` (planner 가 이미 반영한 diff)
- **챌린지**: D-1 (b) 축소 후 G7 에 남는 증거는 두 조각뿐인데 **둘 다 새 정보가 없다.**
  - (a) 는 plan 자신이 `:133` 에서 "증거력이 없다" 고 명시한다 → 사실상 skip.
  - (b) 는 저장소 사본 `pilot/tools/orchestrate-load.py` 1회 호출이다. 그런데 이 검증은 **#20 세션에서 이미 수행됐다** — `20-*.plan.md:78` 이 "본 세션에서 저장소 사본 기준 선행 실측 확인 완료" 라고 적고 있다. #21 이 하는 일은 동일 스크립트 재실행이다.
  - 재실측: `python3 pilot/tools/orchestrate-load.py --phase planner --workspace workspace` → `wrapper-protocol.md`·`workspace/context/pilot/index.md` 실재, 미등록 힌트 부재 (기대값 성립). 그러나 이건 **단위 호출 1건**이지 "파이프라인 1사이클 실완주" 가 아니다. #20 이 바꾼 preamble P0 신문안·doctor 슬림 출력의 evaluator 게이트 소비·plan-validate·wrapper-protocol 전달은 이 사이클에서 **한 번도 실행되지 않는다** (본 세션 wrapper 가 로드한 것은 캐시 0.4.0 — 실측 확인).

  즉 축소된 G7 은 "저장소 파일을 직접 실행해 봤다" 이상이 아니며, 그마저도 #20 이 이미 한 것의 반복이다. plan 은 R-1 에서 한계를 정직하게 적었지만, § 교차 의존 `:287` 은 여전히 "본 feature 는 #20 최종 게이트(dogfooding 1사이클 완주)의 소재다" 로 서술하고, `project.md:40` 은 `[dogfooding]` 라벨을 유지한다. **가장 위험한 공백은 따로 있다 — #21 이 완주하면 `project.md:39` 의 #20 체크박스를 `[x]` 로 찍어도 되는가에 대해 plan 이 한 줄도 말하지 않는다.** evaluator 는 "#21 READY = #20 게이트 통과" 로 읽을 여지가 크고, 그러면 실경로 미검증인 채로 #20 이 완료 처리된다.
- **제안**: 다음 3 가지를 plan 에 명시한다. ① G7 (a) 를 `skip — 증거 없음` 으로 라벨 고정 (pass 로 적지 않는다). ② G7 (b) 를 "완주 판정" 이 아니라 **"#20 스텝 6 회귀 재확인 (중복 실행)"** 으로 격하하고, 이 사이클이 #20 에 대해 신규로 보증하는 것이 **0 건**임을 R-1 에 한 줄로 적는다. ③ **#20 `## 목표` 체크박스의 처리 방침** — "#21 READY 만으로 #20 을 `[x]` 처리하지 않는다 (배포 후 실경로 재확인 시점까지 `[ ]` 유지)" 또는 그 반대를 evaluator 가 오해할 수 없게 단정한다. § 교차 의존 `:287` 의 "최종 게이트의 소재" 문구도 축소 후 실태에 맞게 고친다.

---

### C2 — 정정 대장의 근거 file:line 이 틀렸다 — 정정 문서가 새 오류를 얻는다
- **severity**: blocking
- **category**: premise
- **plan 인용**: § 정정 대장 행 #5·#7·#10 (`21-*.plan.md:150,:152,:155`)
- **챌린지**: 대장의 **주장(claim) 자체는 전건 참**임을 소스로 확인했다 — `.bak` 백업 부재(`integrity.py:272` in-place `write_text`, 백업 코드 없음) · MANIFEST 표 보정·prompts 재생성 auto-fix 부재(`fix=` 는 정확히 `:380`·`:507`·`:802` 3곳) · "모든 수정 전 사용자 확인" 불성립(`_common.py:281-298` `run_auto_fixes` 는 확인 프롬프트 없음) · "Read-only" 제목 오류(`integrity.py:84-141` `check_gitignore_required_patterns` 가 `--fix` 없이 `.gitignore` 를 `write_text`). **문제는 근거 인용이다.**

  | 행 | plan 이 적은 근거 | 실측 |
  | --- | --- | --- |
  | #10 | `integrity.py:711,:749,:763` | `--regen-agents` 힌트 실제 위치는 **`:680`·`:714`·`:752`·`:801` 4곳**. 인용한 3개는 각 `Result.WARN,` 줄이고, 특히 **`:763` 은 `--regen-agents` 가 아니라 `/pilot:analyze --force` 힌트 블록** — 무관한 줄이다 |
  | #5 | `_common.py:34-37` | `PASS`/`INFO`/`WARN`/`ERROR` 는 **`:35-38`** (off-by-one). `:49` 는 `def render`, 레벨 렌더는 `:50` |
  | #7 | `integrity.py:271-272` | `write_text` 는 **`:272`** |

  plan 은 스텝 2 에서 "재작성한 `doctor-migration.md` 의 **모든 거동 주장**에 file:line 근거를 붙여" 라고 지시한다(`:118`). 이 대로면 새 문서가 잘못된 좌표를 싣고, G6 은 "12행 반영 여부" 만 보므로 **틀린 인용이 게이트를 그대로 통과한다.** R-2 가 막으려던 바로 그 재발 경로다.
- **제안**: ① 행 #5·#7·#10 의 근거를 위 실측값으로 교정한다 (#10 은 4곳 전부 나열하고, `:801` 은 `fix=` 가 붙은 유일한 사례이므로 "이 힌트만 auto-fixable 이나 그 fix 는 prompts 재생성이 아니라 레거시 섹션 제거" 로 구분 서술). ② 라인 번호를 **문서 본문에 넣지 않는 안**을 명시 선택지로 올린다 — `doctor-migration.md` 는 docs 사이트에 배포되는 사용자 문서이고, 좌표는 다음 슬림화에서 즉시 썩는다. 근거표는 **커밋 메시지/REPORT 에만** 남기고 문서 본문은 함수명·플래그명 수준으로 서술하는 편이 정합 유지 비용이 낮다. 스텝 2 `:118` 의 "문서에 붙인다 / REPORT 에 붙인다" 이중 해석 여지를 하나로 확정한다.

---

### C3 — G6 은 완전성만 검사한다 — 재작성으로 **신설되는 3개 절**의 사실성은 무게이트다
- **severity**: blocking
- **category**: edge-case
- **plan 인용**: § 게이트 G6 (`21-*.plan.md:116-121`) · 스텝 2 권장 골격 (`:200-201`) · § 리스크 R-2 (`:256`)
- **챌린지**: G6 의 판정 기준 2축은 둘 다 **"대장 N행 전부 반영"** 이라는 커버리지 검사다. 그런데 스텝 2 의 권장 골격은 대장 12행에 없는 내용을 **새로 3개 절이나 만든다** — `4. 실패 진단(--diagnose)` (4패턴·`## DIAGNOSIS` 5필드·호출 시점) · `5. 플러그인 구조 검사(--schema)` (`validate.yml` CI 연동) · `Onboarding Health` 1문단. 이 신규 서술이 코드·SKILL.md 와 어긋나도 **G1~G5·G7 은 문자열/링크/생성물만 보고, G6 은 "12행 반영" 만 보므로 어느 게이트도 걸러내지 못한다.**

  실제로 이 영역은 오독하기 쉽다 — `--diagnose` 는 `doctor.py` argparse 에 **없고**(`tools/doctor.py:42-61` 은 `workspace`·`--project`·`--fix`·`--schema` 뿐), `SKILL.md:42-66` 의 모델 지시문 모드로만 존재한다. Onboarding Health 도 `doctor.py` 출력이 아니라 **스킬 경유 한정**이며 발동 조건이 있다(`SKILL.md:68-74`). plan 은 주의사항 `:216` 에서 `--diagnose` 두 경로 구분을 경고했지만, 그 경고를 **검증하는 축이 G6 에 없다.**
- **제안**: G6 을 2축 → 3축으로 확장한다. 3번째 축 = **"신규 서술 무근거 0건"** — 재작성 후 문서의 각 거동 문장을 나열하고 (a) 대장 12행 중 하나에 대응하거나 (b) `tools/doctor/*.py` 또는 `skills/doctor/SKILL.md` 인용이 붙어 있거나 둘 중 하나임을 evaluator 가 체크리스트로 확인하게 한다. 최소한 `--diagnose`·`--schema`·Onboarding Health 3절에 대해서는 "스크립트 플래그가 아님 / workspace 인자 없음 / 스킬 경유 한정 + 발동 조건" 세 문장을 **필수 포함 항목으로 대장에 행 추가**해 커버리지 검사 대상으로 끌어들인다.

---

### C4 — S1-3 의 대체 진단 경로가 캐시 버전에 의존한다 — 튜토리얼 독자에게 항상 위양성이 나온다
- **severity**: blocking
- **category**: edge-case
- **plan 인용**: § S1 정정 대장 S1-3 (`21-*.plan.md:191`) · G7 주의 (`:208`)
- **챌린지**: S1-3 의 정정 방향은 "자동 로드 성공 여부는 `orchestrate-load.py` 힌트(`\"진입 파일이 MANIFEST 에 등록되지 않음\"` 부재)로 확인" 이다. 그런데 plan 자신이 `:208` 에서 **"캐시 경로로 실행하면 D-1 의 미등록 힌트가 그대로 나와 오판한다"** 고 적었다. `getting-started.md` 는 **플러그인 사용자용 튜토리얼**이고, 사용자에게 있는 것은 저장소가 아니라 설치 캐시다. 실제로 이 문서는 이미 `:15-16` 에서 `${CLAUDE_PLUGIN_ROOT}` 경로로 명령을 안내하는 관례를 갖고 있다.

  결과: 독자가 `${CLAUDE_PLUGIN_ROOT}/tools/orchestrate-load.py` 를 실행하면 — 본 세션에서 실측한 것처럼 (캐시 0.4.0 반환 JSON 에 `"도메인 'pilot' 의 진입 파일이 MANIFEST 에 등록되지 않음"` 힌트 존재) — **MANIFEST 헤더를 올바르게 고쳐도 힌트가 그대로 나온다.** #20 의 anchored H2 매칭이 배포되기 전 버전을 쓰는 모든 사용자에게 해당한다. S1-3 이 고치려던 증상("절차를 따라도 아무 오류가 보고되지 않아 사용자가 막힌다")을, **"절차를 따라도 계속 실패로 보고돼 사용자가 막힌다"** 로 바꿔놓는 것뿐이다. 덧붙여 `orchestrate-load.py` 는 wrapper 내부 헬퍼이지 사용자 대면 CLI 가 아니라, 튜토리얼 Troubleshooting 의 추상 수준과도 맞지 않는다.
- **제안**: S1-3 의 대체 경로에서 `orchestrate-load.py` 를 **뺀다.** 이미 `:305` 에 있는 `grep "^##" workspace/context/MANIFEST.md` 로 헤더 형식을 확인하고, 판정 기준을 "`## 도메인 분류` 가 **정확히 그 문자열 단독 라인**이어야 하며 suffix(`## 도메인 분류 (수동 관리)`)는 매칭되지 않는다" 로 서술하는 것으로 충분하다 (#20 스텝 6 anchored 계약과 정합 — plan `:193` 이 이미 그 계약을 인용하고 있다). 굳이 `orchestrate-load` 를 남긴다면 **"플러그인 v0.9.0 이상에서만 유효" 라는 버전 단서**를 필수로 붙이고, 그 단서 자체가 튜토리얼에 적합한지 재판단한다.

---

### C5 — G5 의 세 번째 명령은 아무것도 강제하지 않는다 (gitignore 대상)
- **severity**: suggestion
- **category**: risk
- **plan 인용**: § 게이트 G5 (`21-*.plan.md:113`) · § 주의사항 (`:218` "G5 세 번째 명령이 이를 강제한다")
- **챌린지**: `git diff --name-only | grep -c "^pilot/docs/reference/\(agents\|skills\|tools\)/"` 가 0 이어야 한다는 게이트인데, 그 세 디렉터리는 **전부 `pilot/.gitignore:8-10` 대상**이다 (`git check-ignore -v` 로 확인). 즉 generator 가 생성물을 손으로 뜯어고쳐도 `git diff --name-only` 에 **애초에 나타나지 않으므로** 이 명령은 항상 0 을 반환한다. 게이트가 아니라 장식이며, 주의사항 `:218` 의 "강제한다" 는 거짓 안심이다. 실제로 손편집을 잡아내는 것은 G5 첫 번째 명령(`docs_build.py --check`, 빌드 결과와 디스크 대조) 하나뿐이다.
- **제안**: 세 번째 명령을 삭제하거나 `git status --porcelain --ignored pilot/docs/reference/` 처럼 무시 파일까지 보는 형태로 교체한다. 주의사항 `:218` 은 "생성물 손편집 검출은 `docs_build.py --check` 가 단독으로 담당한다" 로 정정한다.

---

### C6 — D-2 의 드리프트 인벤토리가 누락돼 있다 — 분리 feature 가 과소 스코프로 등록된다
- **severity**: suggestion
- **category**: premise
- **plan 인용**: § 사용자 결정 D-2 (`21-*.plan.md:242`) · § 후속 인수인계 (`:283`) · 누적 임계 주석 (`:245`)
- **챌린지**: plan 은 `workspace/context/` 잔존 드리프트를 `pilot/index.md:43` (P0 memory-hint) **1건**으로 특정하고, 그 전제 위에서 "드리프트 3건(D-1·D-2·D-3)" 이라는 누적 임계 판단과 분리 feature 스코프를 세운다. 실측하면 최소 **3건**이다:

  - `workspace/context/pilot/index.md:43` — `P0 (memory-hint)` (plan 이 잡은 것)
  - `workspace/context/pilot/lifecycle.md:22` — `` `tools/init_detect.py` `detect_languages()` `` (#20 스텝 4c 삭제 — `ls pilot/tools` 8개에 부재)
  - `workspace/context/pilot/lifecycle.md:69` — `` (진단 모드는 `tools/doctor/diagnose.py`) `` (#20 삭제 — `ls pilot/tools/doctor/` = `__init__`·`_common`·`integrity`·`schema` 뿐)

  #21 본체에는 영향이 없다 (`workspace/context/` 무변경 원칙 준수). 문제는 **인수인계 기록의 사실성**이다 — 메인 대화가 이 plan 을 근거로 분리 feature 를 등록하면 `lifecycle.md` 2건이 누락된 채 spec 이 만들어지고, 다음 `/pilot:learn` 재실행 범위 판단도 어긋난다. 전달사항 `:157` (spec.md·index.md 라인 인용 stale) 과 같은 계열이지만 그 항목만으로는 `lifecycle.md` 가 커버되지 않는다.
- **제안**: D-2 항목과 § 후속 인수인계에 `lifecycle.md:22`·`:69` 2건을 **추가 기재**한다 (직접 Edit 은 여전히 금지 — drift-protocol § A). 누적 임계 서술(`:245`)의 "3건" 도 실측 건수에 맞게 조정하거나 "결정이 필요한 건 3건, 사후 정리 대상 라인은 별도" 로 구분한다.

---

### C7 — 정정된 문서가 같은 docs 사이트의 다른 페이지와 정면 충돌한다 (범위 제외의 부작용)
- **severity**: suggestion
- **category**: risk
- **plan 인용**: § 정정 대장 행 #2·#11 (`21-*.plan.md:147,:156`) · § 후속 인수인계 (`:280`)
- **챌린지**: 대장 행 #2·#11 의 결론은 "doctor 는 완전한 read-only 가 아니다(`--fix` 없이 `.gitignore` 를 쓴다)" + "`--fix` 는 확인 없이 즉시 적용한다" 이고, 이건 실측상 참이다. 그런데 **같은 docs 사이트에 배포되는** `pilot/docs/reference/skills/doctor.md:71-72` 는 정반대로 적혀 있다:

  - `:71` — "검사는 **비파괴** — 읽기만 함, 파일 수정 안 함 (`--fix` 제외)"
  - `:72` — "실패 시 fix 제안은 출력하되 자동 적용 안 함. 사용자가 해당 스킬을 재실행."

  이 페이지는 `skills/doctor/SKILL.md:79-80` 에서 `docs_build.py` 가 생성하는 파생물이고, SKILL.md 는 spec 비즈니스 규칙상 **본 범위 밖**이다. plan 은 후속 인수인계에 `SKILL.md:34` 만 올렸고 **`:79-80` 은 놓쳤다** — `:34` 보다 `:79-80` 쪽이 신규 문서와 더 직접적으로 충돌한다. 결과적으로 #21 머지 직후 사이트에는 "doctor 는 파일을 수정한다"(how-to) 와 "doctor 는 파일을 수정하지 않는다"(reference) 가 공존한다.
- **제안**: ① § 후속 인수인계에 `skills/doctor/SKILL.md:79-80` 을 추가하고, `:34` 와 묶어 한 건으로 처리하도록 명시한다. ② R-2 에 "본 사이클 종료 시점에 `reference/skills/doctor.md` 와의 모순이 남는다 (SKILL.md 범위 밖)" 를 **알려진 잔존 모순**으로 기록해 evaluator 가 이를 결함으로 오판하거나 반대로 조용히 넘기지 않게 한다. ③ 신규 `doctor-migration.md` 본문에 "`--fix` 무관 자동 조치 1건" 을 서술할 때 reference 페이지와 충돌한다는 사실을 감춘 채 단정하지 않는다.

---

### C8 — 스텝 2 가 성격이 다른 두 변경을 한 스텝·한 커밋에 묶었다 (S1 편입 후유증)
- **severity**: suggestion
- **category**: scope
- **plan 인용**: 스텝 2 / 2-b (`21-*.plan.md:200-204`) · § 주의사항 커밋 단위 (`:222`)
- **챌린지**: 스텝 2 는 (i) `doctor-migration.md` **전면 재작성** (골격 7절 신설, 대장 12행, 게이트는 G6 인스펙션 하나) 과 (ii) `getting-started.md` **3곳 외과적 치환** (게이트는 G2b 라는 결정적 grep) 을 한 스텝에 담고, 주의사항 `:222` 는 스텝 1 까지 묶어 단일 커밋을 지시한다. 두 변경은 변동성·검증 방식·되돌림 조건이 전부 다르다.
  - 되돌림 단위: 재작성본이 리뷰에서 반려되면 이미 검증된 S1 3곳 정정까지 함께 되돌아간다.
  - 게이트 귀속: G3 은 "인바운드 링크 정확히 5건" 을 요구하는데, 그 5건 중 #1 이 **스텝 2-b 가 편집하는 바로 그 파일**(`getting-started.md:256`) 이다. 한 커밋이면 G3 실패 시 원인 파일이 두 개 중 어디인지 diff 를 다시 갈라야 한다.
  - 게다가 `:222` 는 "한 커밋으로 묶는다" 라고 단정한 직후 스텝 3 산출물에 대해서는 "같은 커밋 또는 `skills:` 분리 — generator 판단" 이라고 위임한다. 원자성을 이유로 묶으라면서 일부는 재량으로 남기는 것은 지시로서 일관되지 않다.
- **제안**: 스텝 2 를 `2-a`(`doctor-migration.md` 재작성) / `2-b`(`getting-started.md` 3곳) **두 커밋**으로 나눈다 (PR 은 하나 유지 — "문서 정합의 원자성" 은 PR 단위로 충족된다). 각 커밋 직후 귀속 게이트를 고정한다 — 2-a → G3·G4·G6-축1, 2-b → G2b·G3·G6-축2. 스텝 3 의 `20-*.plan.md` diff 커밋 귀속도 generator 재량이 아니라 plan 에서 하나로 확정한다.

---

### C9 — D-1 의 기각 사유("이 세션 내 불가능")는 사실과 다르다 — 결정은 유지하되 근거는 정정 필요
- **severity**: suggestion
- **category**: premise
- **plan 인용**: § 사용자 결정 D-1 "(a) 안 기각 사유" (`21-*.plan.md:235`) · § 리스크 R-1 (`:249-254`)
- **챌린지**: 기록된 기각 사유는 "마켓플레이스가 GitHub `radiostart/claude-plugins` 클론이라 캐시 갱신은 **머지·배포 선행**이 필요 — 이 세션 내 불가능" 이다. 결정(축소)에는 이의 없지만 이 **전제는 부정확**하다. 실측:
  - 설치 위치는 `~/.claude/plugins/installed_plugins.json` 의 `pilot@radiostart-plugins → installPath: .../cache/radiostart-plugins/pilot/0.4.0` 로, **로컬 디렉터리 + 로컬 JSON 레지스트리**다. 마켓플레이스 원본(`known_marketplaces.json` → git URL)과는 별개 계층이다.
  - 따라서 캐시 트리를 저장소 사본으로 로컬 갱신하는 경로(디렉터리 교체 또는 `installPath` 재지정)는 **기술적으로 존재**한다. 막는 것은 "GitHub 머지 필요" 가 아니라 **"사용자 전역 플러그인 설치본을 검증 목적으로 변조하는 것이 부적절"** 이라는 판단, 그리고 **세션 중 플러그인 리로드가 되지 않아 wrapper 실경로 재현이 여전히 불완전하다**는 점이다.

  근거가 틀린 채로 남으면 후속(배포 후 재확인) 담당자가 "배포만 되면 자동 해소" 로 오해하고, 실제 필요한 절차(`pilot/tools/pilot-update.sh` 실행 + 세션 재시작)를 빠뜨린다 — plan `:282` 이 이미 그 필요를 감지하고 있으면서 D-1 근거와 연결하지 않았다.
- **제안**: D-1 의 기각 사유를 "GitHub 머지 선행 필요" → **"로컬 캐시 변조는 사용자 전역 설치본을 건드리는 부작용이 있고, 세션 중 플러그인 리로드가 불가해 실경로 재현이 성립하지 않음"** 으로 정정한다. R-1 의 "후속 확인 필요" 항목에는 재확인 절차를 명시한다 — 머지 → 배포 → `pilot-update.sh` → **세션 재시작** → G7 기대값 재측정.

---

### C10 — G3 의 `== 5` 등식은 정상적인 링크 추가에도 실패한다
- **severity**: nit
- **category**: alternative
- **plan 인용**: § 게이트 G3 (`21-*.plan.md:73-80`) · 스텝 2 새 링크 지침 (`:202`)
- **챌린지**: G3 의 두 번째 명령은 `pilot/docs` 전체에서 `doctor-migration.md` 링크 **총 개수 == 5** 를 요구한다. 검산 결과 현재 정확히 5건·앵커 0건으로 baseline 은 맞다 (`PLAN-manual.md:46,168,264` 는 링크 문법이 아니라 카운트에서 제외됨 — 확인). 그러나 진짜 요구사항은 "**대장 5곳이 모두 살아 있고 resolve 된다**" 이지 "총량이 5 를 넘지 않는다" 가 아니다. 스텝 2 는 generator 에게 새 상대 링크 추가를 허용하므로, 어떤 페이지가 doctor-migration 을 정당하게 참조하기 시작하면 **아무것도 깨지지 않았는데 G3 이 실패**한다.
- **제안**: `== 5` 를 "대장 5개 위치(파일:줄 아님, 파일 단위)가 각각 1건 이상 존재 + 전체 doctor-migration 링크가 전부 resolve" 로 바꾼다. 총량 상한이 필요하다면 `>= 5` 로 두고 초과분은 REPORT 에 열거만 시킨다.

---

### C11 — G1 의 백틱 파싱은 문장 재작성 한 번에 깨진다 + 정렬 함정
- **severity**: nit
- **category**: risk
- **plan 인용**: § 게이트 G1 (`21-*.plan.md:39-52`)
- **챌린지**: 실행 확인 결과 G1 은 현행 파일에서 정상 동작한다(listed 11 vs actual 8 → 기대대로 불일치). 다만 두 가지 취약점이 있다. ① `re.findall(r'`([^`]+)`', line)` 이 **해당 줄의 모든 백틱 토큰**을 도구명으로 간주하고 `pilot/tools/*.py` 하나만 제외한다 — generator 가 카드 문구를 다듬으며 백틱 토큰(예: `` `--check` ``, 버전 표기)을 하나라도 추가하면 게이트가 실패한다. ② 기대 순서가 ASCII 정렬이라 **`docs_build` 가 `doctor` 보다 앞**이다(`docs_build` < `doctor`). "알파벳순" 이라는 지시만 보고 사람이 자연스럽게 `doctor, docs_build` 로 쓰면 실패한다. plan `:51` 이 기대 출력을 그대로 적어둔 것은 좋은 방어지만, 스텝 1 본문(`:197`)에는 이 함정이 언급돼 있지 않다.
- **제안**: 스텝 1 본문에 "나열은 `sorted()` ASCII 순 — `docs_build` 가 `doctor` 앞" 을 한 줄 덧붙이고, "해당 줄에 도구명 외 백틱 토큰을 추가하지 않는다" 는 제약도 함께 적는다. 또는 G1 의 추출 대상을 `` `pilot/tools/*.py` `` 뒤 구간으로 한정한다.

---

## 참고 — 검산해서 **문제없음**을 확인한 항목 (재검토 불요)

| 항목 | 실측 결과 |
| --- | --- |
| G1 baseline (listed 11 vs actual 8) | 일치 — `ls pilot/tools/*.py` = 8종, `index.md:25` = 11종 |
| G2 (grep + reference 제외 필터) | 정상 동작 — `index.md:25` 1건만 남고 `reference/agents/pilot-evaluator.md:46` 은 필터로 제외됨 |
| G2b (`OH-[1-5]`) | **정확히 1건** (`getting-started.md:277`) — 0건 목표 달성 가능. 게이트 유효 |
| G3 (링크 5건·앵커 0건·nav 1건) | 5건 / 0건 / `mkdocs.yml:98` 1건 — plan 대장 5행 위치 전건 일치 |
| G4 (docs 내부 링크) | `checked 194 broken 0` — plan baseline 과 일치 |
| G5-1·G5-2 | `docs_build.py --check` exit 0 · `284 tests OK` |
| G7 (b) 기대값 | 저장소 사본 실행 시 `wrapper-protocol.md`·`pilot/index.md` 실재 + 미등록 힌트 부재 — 성립 (증거력 논점은 C1) |
| doctor 실행 baseline | 저장소 루트 CWD 기준 `9 PASS · 4 WARN · 0 ERROR` — plan 과 일치 (`pilot/` CWD 로 돌리면 8 PASS 로 달라진다 — evaluator 는 CWD 를 저장소 루트로 고정할 것) |
| 정정 대장 claim 진위 12행 | **주장은 전건 참** (근거 좌표만 C2) |
| S1 대장 3행 | `:277`·`:293`·`:311-314` 위치·현행 문구 전건 일치. `check_workspace_config_sections`·MANIFEST 헤더 검증 삭제 확인 (`integrity.py:393-417` 은 `is_file()` 존재 검사만) |
| 주의사항 `how-to/index.md:99` 무변경 판단 | 정확 — 카드 설명은 현행 거동과 일치 |

## 합의 (planner 가 재호출되어 채움 — 처음에는 비워둠)

| C# | 처리 | 메모 |
|----|------|------|
| C1 | accepted | **사용자 확정** — #20 목표 체크박스는 **unchecked 유지**. #21 완주가 `[x]` 근거가 아님을 plan § #20 체크박스 처리 방침에 명문화 + evaluator 반영용 사유 문안 준비 (체크박스·목표 줄 편집은 evaluator 단독 권한이라 planner 는 문안만 제공). 제안 ①②③ 전부 반영 — G7 (a) `skip — 증거 없음` 라벨 고정, (b) 를 "완주 판정" → "#20 스텝 6 회귀 재확인 (중복 실행)" 으로 격하, R-1 에 "본 사이클이 #20 에 신규로 보증하는 것 0건" 명시, § 교차 의존 "최종 게이트의 소재" 문구 정정 |
| C2 | accepted | 좌표 3행 재실측 후 교정 — #10 `:711,:749,:763` → **`:680`·`:714`·`:752`·`:801`** (`:763` 은 `--regen-agents` 가 아니라 `/pilot:analyze --force` 힌트(`:766`)의 WARN 줄로, 무관 인용 확인). `:801` 만 `fix=`(`:802`) 동반이나 그 fix 는 prompts 재생성이 아니라 `_fix_remove_legacy_planning_section` 임을 구분 서술. #5 `_common.py:34-37` → **`:35-38`**(레벨 상수), 렌더 색상 매핑은 `:50`. #7 `:271-272` → **`:272`**. 제안 ② 도 채택 — **문서 본문에는 라인 번호를 넣지 않는다**(함수명·플래그명 수준), 근거 좌표는 plan 대장·커밋·REPORT 에만. 스텝 2 의 이중 해석 여지 제거 |
| C3 | accepted | 정정 대장을 12행 → **15행**으로 확장 (#13 `--diagnose` · #14 `--schema` · #15 Onboarding Health). 신설 3개 절이 커버리지 검사 대상에 포함됨. G6 을 2축 → **3축**으로 확장 (3축 = 신규 서술 무근거 0건) |
| C4 | accepted | **사용자 확정 — 대체 절차 제안 없이 삭제.** 버전 분기 서술("0.4.0 에서는 X, 0.9.0 에서는 Y")도 금지. S1 대장 3행의 정정 방향을 전부 **삭제**로 변경 (S1-3 의 `orchestrate-load.py` 대체 경로는 제안 자체를 철회 — critic 지적대로 캐시 사용자에게 항상 위양성). 삭제 후 §번호·`:281` 앵커·인바운드 링크 무영향 실측 확인 (getting-started.md 로 향하는 앵커 링크 0건) |
| C5 | accepted | `pilot/docs/reference/tools/` 등 3개 디렉터리가 `pilot/.gitignore:10` 대상임을 `git check-ignore -v` 로 재확인 — G5 세 번째 명령은 항상 0 반환. **명령 삭제**하고 주의사항의 "G5 세 번째 명령이 이를 강제한다" → "생성물 손편집 검출은 `docs_build.py --check` 단독 담당" 으로 정정 |
| C6 | accepted | `lifecycle.md:22`(`init_detect.py detect_languages()`) · `:69`(`doctor/diagnose.py`) 2건 실측 확인. D-2 인벤토리를 **3건**으로 정정하고 § 후속 인수인계에도 기재 — 메인 대화가 이 인벤토리를 근거로 분리 feature 를 등록. 누적 임계 서술도 "결정 3건 / 사후 정리 라인 3건" 으로 구분 |
| C7 | accepted | `reference/skills/doctor.md:71-72` ↔ 신규 `doctor-migration.md` 정면 충돌 확인. § 후속 인수인계에 `SKILL.md:79-80` 추가(`:34` 와 **한 건으로 묶어** 처리), R-2 에 **알려진 잔존 모순**으로 기록해 evaluator 오판 방지. 신규 문서에서 "`--fix` 무관 자동 조치" 서술 시 충돌을 감춘 채 단정하지 않도록 스텝 2-a 에 제약 명시 |
| C8 | accepted | 스텝 2 를 **2-a(재작성) / 2-b(외과적 치환) 두 커밋**으로 분리 (PR 은 1개 유지). 게이트 귀속 고정 — 2-a → G3·G4·G6-축1·축3, 2-b → G2b·G3·G6-축2. 스텝 3 의 `20-*.plan.md` diff 는 planner 가 이미 반영했으므로 **커밋 3 에 귀속** 으로 확정(generator 재량 아님). 주의사항의 일관되지 않던 "묶는다/재량" 서술 정리 |
| C9 | accepted | **결정(축소)은 유지, 근거만 정정.** `installed_plugins.json` 이 로컬 디렉터리 + 로컬 레지스트리라 캐시 교체 경로가 기술적으로 존재함을 인정하고, 기각 사유를 "GitHub 머지 선행 필요" → **"사용자 전역 설치본 변조가 부적절 + 세션 중 플러그인 리로드 불가로 실경로 재현 자체가 불성립"** 으로 교체. R-1 의 후속 절차를 머지 → 배포 → `pilot-update.sh` → **세션 재시작** → G7 재측정 5단계로 명시 |
| C10 | accepted | `== 5` 총량 등식 → **"대장 5개 파일이 각각 1건 이상 + 전체 doctor-migration 링크 전부 resolve"** 로 교체. 총량은 `>= 5` 로 두고 초과분은 REPORT 에 열거만. 정당한 신규 참조가 게이트를 깨지 않게 됨 |
| C11 | accepted | G1 추출 대상을 `` `pilot/tools/*.py` `` **뒤 구간으로 한정**해 백틱 토큰 오염 차단. 스텝 1 본문에 ① "`sorted()` ASCII 순 — **`docs_build` 가 `doctor` 앞**" ② "해당 줄에 도구명 외 백틱 토큰 추가 금지" 2줄 명시 |
