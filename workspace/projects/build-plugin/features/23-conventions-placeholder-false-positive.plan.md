# 구현 계획: #23 doctor 파서 오탐 2건 (conventions 플레이스홀더 · features 카운트)

> mode: standard (tdd=false) · 작성: 2026-07-26 planner
> 대상 spec: [23-conventions-placeholder-false-positive.md](23-conventions-placeholder-false-positive.md)

## 실측 baseline (2026-07-26, `python3 pilot/tools/doctor.py workspace`)

```
요약: 10 PASS · 4 WARN · 0 ERROR
[WARN] conventions: conventions_doc=예: `context/conventions.md 로 선언됐으나 파일 없음 …      ← 오탐 (A)
[WARN] conventions: conventions_evals=예: `context/evals/conventions.json 로 선언됐으나 파일 없음 … ← 오탐 (A)
[WARN] build-plugin plugin_version: 0.1.0 → 0.10.0 업그레이드됨 (wrapper 계약 변경 가능)        ← 정상 (건드리지 않음)
[WARN] build-plugin drift: features 24 → 30 (증가 6)                                          ← 오탐 (B)
[PASS] build-plugin analyzed: analyzed=True, features=30                                       ← 값 자체가 오계산
```

- spec 이 기록한 "29" 는 `.plan.critic.md` 5개 시점 값. 실측 시점에는 6개(#17·#18·#19·#20·#21·#24)라 **30**. 오탐 성격·원인 동일.
- features/ 실측: 총 44 파일 = spec `NN-slug.md` 24 + `.plan.md` 14 + `.plan.critic.md` 6. `.agent-state.yml` 의 `last_analyzed_features: 24` 가 정확한 값.
- 오탐 2종 모두 **현행 재현 확인**.

## 채택할 판정 규칙 (spec Open Questions (d)) — ✅ **사용자 승인 완료 (2026-07-26)**

> 아래 3건 전부 권고안 그대로 **확정**. `@pilot-planner-critic` 은 건너뛰기로 결정.
> 단 (B) 의 "stem 에 `.` 이 있으면 파생" 규칙은 **spec 파일명에 점을 쓰는 사용자에서 미카운트 리스크**가 있음이
> 승인 시점에 인지된 잔여 리스크다 — generator 는 이 경계를 테스트로 고정할 것.


| Open Q | 권고 | 근거 |
| --- | --- | --- |
| (A) 플레이스홀더 판정 규칙 | **(i) 구조 기반 확장안** — 값 셀이 "코드 스팬 단독" 또는 "공백 없는 평문" 일 때만 선언 인정. 그 외(설명문+코드 스팬 혼재, 코드 스팬 복수, 공백 포함 산문)는 미선언 + INFO 1줄 | spec 비즈니스 규칙이 "한국어 `예:` 하드코딩 의존 금지" 를 명시 → (ii) 단독 배제. (iii) 는 파서가 문서 규약에 의존해 **기존 사용자 workspace 오탐이 남음** (spec 이 반대한 접근). config.md 작성 규칙 "값은 백틱/평문 둘 다 허용" 을 보존해야 하므로 코드 스팬 단독만 인정하는 협의의 (i) 도 불가 |
| (A) `--fix` 포함 여부 | **미포함** — 진단 정확화까지 | 사용자 workspace 파일 자동 편집 범위 확대. spec 예외 케이스가 "신중" 명시. 오탐이 사라지면 자동 조치 대상 자체가 없다 |
| (B) 파생 산출물 판정 | **(iv) 다중 확장자 규칙** — `*.md` 중 **stem 에 `.` 이 있으면 파생 산출물**(`23-x.plan` · `23-x.plan.critic`), 없으면 spec. 판정을 `_common.py` 한 곳에 함수로 고정 | (i) 블랙리스트는 "접미사가 또 늘면 재발" 이라 spec 이 금지. (ii) 화이트리스트 정규식 `^\d+-[a-z0-9-]+\.md$` 은 파서는 단순해지지만 **명명 규약을 강제** → 한글 slug·대문자 spec 을 쓰는 사용자 프로젝트에서 count 0 → `analyzed=true` WARN 오탐이라는 새 참(true) 판정 훼손. (iv) 는 접미사가 늘어도 자동 대응하면서 명명 규약을 강제하지 않는다. (iii) 디렉터리 이동은 기존 산출물 이관 비용 + plan-schema 경로 계약 변경이라 과함 |

## 변경 파일

- [x] `pilot/tools/doctor/_common.py` — (B) `is_feature_spec_file(p)` 신설 + `count_real_features` 가 이를 사용 (파생 판정 SSOT 1곳)
- [x] `pilot/tools/doctor/integrity.py` — (A) `_extract_declared_path(cell)` 신설 + `check_conventions_paths` 의 config 표 파싱·project.md override 양쪽에 적용 + 예시 표기 INFO 1줄
- [x] `pilot/tests/tools/test_doctor_conventions.py` — (A) 케이스 3건 추가 (기존 5 케이스 무변경)
- [x] `pilot/tests/tools/test_doctor_features_count.py` — (B) 신규 회귀 테스트 4 케이스 + 잔여 리스크 고정 테스트 1건(dotted-stem spec 미카운트 경계 문서화)
- [x] `pilot/skills/context/lifecycle/setup/templates/config.md.template` — conventions 2행 값 셀을 미선언 표기(`—`)로 + 작성 규칙 1줄 (재발 방지. 파서는 이 규약에 **의존하지 않음**)

무변경 확정 (의도적):

- `workspace/context/config.md` — **살아있는 오탐 픽스처로 보존**. 파서 단독 효과를 doctor 실측으로 증명하기 위해 이번 사이클에서 고치지 않는다.
- `workspace/projects/build-plugin/.agent-state.yml` — `last_analyzed_features: 24` 가 정확값. 수정 후 파서가 24 를 반환하며 자동 정합.
- `pilot/tools/orchestrate-load.py` — 같은 계열 placeholder leak 존재하나 본 범위 밖 (§ 교차 의존).

## 구현 순서

1. **(B) 파생 산출물 판정 SSOT 신설** — `_common.py:197` 부근.

   ```python
   def is_feature_spec_file(p: Path) -> bool:
       """features/ 의 spec 파일 판정. 파생 산출물(`*.plan.md`·`*.plan.critic.md` 등
       다중 확장자)은 spec 이 아니다 — 접미사가 늘어도 이 규칙 하나로 커버된다."""
       return p.is_file() and p.suffix == ".md" and "." not in p.stem
   ```

   `count_real_features` 는 `sum(1 for p in features_dir.iterdir() if is_feature_spec_file(p))` 로 축약. 하드코딩된 `.plan.md` 문자열 제거.

   > 참(true positive) 보존 근거 — `count_real_features` 의 호출처는 실측 grep 결과 `integrity.py:517` **단 1곳**이고 거기서 두 판정에 쓰인다.
   > - `analyzed=true && count==0` WARN (`integrity.py:518`): 파생물만 있고 spec 이 0인 features/ 에서 **여전히 발화**한다. 오히려 정확해진다 — 종전에는 `.plan.critic.md` 만 있어도 count>0 이라 이 WARN 이 침묵했다.
   > - `analyzed=false && count>0` WARN (`integrity.py:527`): spec 이 1개라도 있으면 발화 유지.
   > - features 증가 drift WARN (`integrity.py:707`): spec 이 실제 늘면 `count > last+1` 로 계속 감지. `last_analyzed_features` 가 spec 기준 기록이라 파서를 spec 기준으로 맞추는 방향이 정합 (spec 예외 케이스 마지막 항목).

2. **(A) 값 셀 판정 헬퍼 신설** — `integrity.py` 의 `CONVENTION_KEYS`(869행) 인접에 배치.

   ```python
   _UNDECLARED_MARKERS = {"", "-", "—", "–", "값", "n/a", "N/A", "(없음)", "(미설정)"}

   def _extract_declared_path(cell: str) -> str | None:
       """config 값 셀에서 실제 선언 경로만 추출. 예시·플레이스홀더면 None."""
   ```

   판정 순서 (모두 **구조 기반** — 한국어 문자열 의존 없음):

   1. `cell.strip()` 이 `_UNDECLARED_MARKERS` 에 속하면 → `None` (미선언, 조용히 skip).
   2. 백틱 코드 스팬이 **정확히 1개**이고 그것이 셀 전체(양끝 공백 제외)면 → 내부 텍스트를 선언 값으로 반환. (예: `` `context/conventions.md` ``)
   3. 코드 스팬이 **0개**이고 셀에 공백이 없으면 → 셀 텍스트 그대로 반환. (config.md 작성 규칙 "평문도 허용" 보존)
   4. 그 외(설명문 + 코드 스팬 혼재 / 코드 스팬 복수 / 공백 포함 산문) → `None` + **예시 표기 INFO 1줄**.

   `예: \`context/conventions.md\`` 는 4번 → 미선언 + INFO. 현행 오탐 WARN 2건 소멸.

3. **(A) `check_conventions_paths` 배선** — `integrity.py:897-921`.
   - config 표 루프(`:901-904`): `value = row[1].strip().strip("\`").strip()` + `value != "값"` 조건을 `_extract_declared_path(row[1])` 호출로 교체. `None` 이면 declared 에 넣지 않고, 4번 사유일 때만 INFO Result 1건 append.
   - project.md override 루프(`:915-921`): 추출된 값도 동일 헬퍼를 통과시켜 일관성 확보 (기존 테스트 `ProjectOverrideChecked` 의 `` `context/kotlin-conventions.md` `` 은 규칙 2 로 통과).
   - INFO 문구(안): `{key} 값 셀이 예시 표기로 보임 — 미선언 취급 ('{원문 셀}'). 실제 경로는 백틱 코드 스팬 단독 또는 공백 없는 평문으로 기입`

   > 참 보존 근거 — `Result.INFO` 는 `summarize`(`_common.py:301-313`)가 PASS/WARN/ERROR 만 세므로 **요약 카운트·exit code 에 영향 없다**. 오탐 WARN 만 사라지고, "선언했는데 파일 없음" 은 규칙 2·3 경로로 그대로 WARN 이다.

4. **테스트 보강** (기존 파일 패턴 답습 — `unittest` + `tempfile`, `sys.path` 에 `pilot/tools` 삽입).
   - `test_doctor_conventions.py` 추가 3건:
     - `test_placeholder_cell_not_declared` — `| \`conventions_doc\` | 예: \`context/conventions.md\` | … |` → WARN 0건, INFO 1건 (**본 feature 의 회귀 잠금**).
     - `test_plain_text_path_still_declared` — 백틱 없는 `context/conventions.md` + 파일 부재 → WARN 1건 (평문 선언 참 보존).
     - `test_dash_marker_silent` — 값 셀 `—` → 결과 0건.
     - 기존 5 케이스는 **한 줄도 수정하지 않는다** (무손 게이트의 증거).
   - `test_doctor_features_count.py` 신규 4건:
     - spec 3 + `.plan.md` 2 + `.plan.critic.md` 2 → **3**.
     - 파생 산출물만 존재 → **0** (`analyzed=true` WARN 이 살아나는 참 케이스).
     - 미래 접미사 `07-x.plan.review.md` 도 자동 제외 → 재발 방지 증명.
     - 하위 디렉터리·`.txt`·`.yml` 무시 (기존 거동 유지).

5. **템플릿 표기 규약** — `config.md.template:52-53` 의 `conventions_doc`·`conventions_evals` 값 셀을 `—` 로, 예시는 "용도" 컬럼으로 이동. `**작성 규칙:**`(64행)에 1줄 추가: "값 셀에는 실제 값만 적는다. 예시는 용도 컬럼에, 미선언은 `—`." 나머지 `예:` 행 6개(`test_command_fail_fast`·`coverage_command`·`lint_command`·`test_path_convention`·`test_framework_hints`·`pr_default_base`)는 **이번 범위 밖** — doctor 검사 대상이 아니고, 손대면 orchestrate-load 반환 config 내용이 바뀌어 wrapper hints 출력이 변한다 (§ 교차 의존).

6. **게이트 실측** (순서 고정 — 파서 단독 효과 증명).
   - G1: 스텝 1~3 적용 직후, `workspace/context/config.md` **무변경 상태**로 `python3 pilot/tools/doctor.py workspace` → 기대 `10 PASS · 1 WARN · 0 ERROR` + `features=24` + WARN 이 `plugin_version` 1건뿐 + conventions INFO 2줄.
   - G2: `python3 pilot/tests/tools/test_doctor_conventions.py` · `test_doctor_features_count.py` 전부 통과.
   - G3: 기존 doctor 인접 테스트 무손 — `test_orchestrate_load.py`·`test_doc_links.py`·`test_docs_build.py` 등 `pilot/tests/tools/` 일괄 실행 후 실패 0.
   - G4: `.agent-state.yml` diff 0 (`last_analyzed_features: 24` 유지).

## 주의사항

- **정상 감지 3종은 반드시 살려둔다**: (a) 실선언 + 파일 부재 → WARN 유지, (b) spec 실제 증가 → drift WARN 유지, (c) `analyzed=true` + spec 0 → WARN 유지. G1·G2 가 각각의 증거.
- `plugin_version` WARN(0.1.0 → 0.10.0)은 **정상 동작**이라 본 feature 에서 손대지 않는다. G1 기대값의 남는 1건이 이것이다.
- `Result.INFO` 는 요약 카운트에 안 잡히지만 화면에는 출력된다. 새 workspace 는 템플릿이 `—` 라 INFO 0줄, 기존 workspace 만 2줄 — 의도된 안내다.
- 이번 사이클은 `--fix` 를 확장하지 않는다. doctor `--fix` 범위에 관한 문서 모순(project.md 인수인계 R-3)은 **여전히 미해소** — 별건 유지.
- 삭제된 스크립트(`diagnose.py`·`memory-hint.py`·`init_detect.py`·`verify-report-lint.py`)를 호출하지 않는다 (#20 게이트 (a) 판정 대상).
- 계획 확정 후 generator/critic 자동 호출 금지 (guardrails § A16).

## 교차 의존 (다른 feature 영향)

- **orchestrate-load placeholder leak** — `parse_lang_config`(`orchestrate-load.py:141-172`)가 같은 표를 파싱하며 `test_framework_hints=자유 텍스트` 같은 **플레이스홀더를 실값으로 반환**한다 (본 세션 step 1 반환 JSON 에서 실측). conventions 2행은 정규식이 백틱 혼재 셀을 못 물어 우연히 빠져나간다. 성격은 (A) 와 동일하나 wrapper hints 출력 변화를 유발하므로 **후속 feature 로 분리 권고**.
- **project.md 인수인계 R-3** (`doctor/SKILL.md:34` `--fix` 설명 ↔ `docs/reference/skills/doctor.md:71-72` 비파괴 서술 모순) — `--fix` 를 확장하지 않기로 했으므로 본 feature 로는 해소되지 않는다. **사용자 결정 (2026-07-26): 다음으로 이월** — 별도 feature 대상. 체크박스 `[ ]` 유지, 이번 사이클에서 건드리지 않는다.
- **나머지 미처리 전달사항 18건** — #23 과 무관 판단, **일괄 이월 확정** (RESUME.md "미처리 전달사항은 v0.4.0 이월로 사용자 승인됨 — unchecked 유지가 정상"). generator·evaluator 모두 체크박스를 건드리지 않는다.
- **#22 (context 드리프트 재학습)** — 본 변경은 `pilot/tools/` 코드라 `workspace/context/pilot/` 서술과 무관. 영향 없음.
