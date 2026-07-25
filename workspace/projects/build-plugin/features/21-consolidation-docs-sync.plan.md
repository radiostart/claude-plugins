# 구현 계획: #21 정비 후속 — 문서 정합 (#20 반영)

> 모드: standard (tdd: false, mode: null) · 작성: 2026-07-25 planner
> 대상 spec: `features/21-consolidation-docs-sync.md` · 선행: #18(prune) → #19(rewrite) → #20(slim, adf85db 완료)
> 제약: **md 만 수정** · 파일명 보존 (`doctor-migration.md` 인바운드 링크 5곳) · 생성물 디렉터리 (`docs/reference/{agents,skills,tools}/`) 직접 수정 금지 · Python·SKILL.md 무변경
> **사용자 결정 (2026-07-25, 확정)**: D-1 → (b) 저장소 사본 기준으로 게이트 축소 + 실경로 미검증 한계 명시 · S1 → `getting-started.md` 3곳 **이번 범위 포함** · D-2·D-3 → **범위 제외**, 별도 feature 로 분리(등록은 메인 대화가 처리). 상세: § 사용자 결정 (확정).
> **critic 합의 반영 (2026-07-25, `.plan.critic.md` C1~C11 전건 accepted)**: C1 #20 목표 체크박스 **unchecked 유지** 확정(사용자) + G7 격하 · C2 근거 좌표 3행 재실측 교정 + **문서 본문 라인번호 금지** 확정 · C3 대장 12→**15행** + G6 3축 · C4 무효화 항목 **대체 제안 없이 삭제**(사용자) · C5 무효 게이트 삭제 · C6 D-2 인벤토리 3건 정정 · C7 `reference/skills/doctor.md` 잔존 모순 기록 · C8 스텝 2 를 2-a/2-b 두 커밋 분리 · C9 D-1 기각 근거 정정(결정 유지) · C10 G3 등식 완화 · C11 G1 추출 범위 한정.

## 실측 baseline (2026-07-25, HEAD e1aa755)

계획 수립 중 직접 실행해 확인한 현행 상태. 게이트 설계의 근거다.

| 항목 | 실측값 | 근거 |
| --- | --- | --- |
| `pilot/tools/*.py` 실재 | 8개 — auto_pilot·confluence·docs_build·doctor·orchestrate-load·plan-validate·regen-verify·slack-notify | `ls pilot/tools` |
| `reference/index.md:25` 나열 | 11개 (위 8개 + `init_detect`·`verify-report-lint`·`memory-hint` 3 stale) | 파일 실독 |
| `reference/index.md:13`(agents 5) · `:19`(skills 17) | **정확 — 무변경** | `ls pilot/agents`=5, `ls -d pilot/skills/*/`(context 제외)=17 |
| `diagnose` 문자열 in `reference/index.md` | **0건** (spec 의 "확인" 항목 — 정정 불요) | grep |
| `doctor-migration.md` 인바운드 링크 | 정확히 5건, **앵커 사용 0건** | grep (아래 § 인바운드 링크 대장) |
| `mkdocs.yml:98` nav 항목 | `Doctor 진단·마이그레이션: how-to/doctor-migration.md` — yml 이라 **수정 불가(범위 외)** | 파일 실독 |
| `docs_build.py --check` | exit 0 | 실행 |
| `python3 -m unittest discover -s tests/tools` (pilot CWD) | 284 tests, OK | 실행 |
| `pilot/docs` 내부 md 링크 | 194건 검사 / **broken 0** | 인라인 해석 스크립트 (§ 게이트 G4) |
| `python3 pilot/tools/doctor.py workspace` | 9 PASS · 4 WARN · 0 ERROR | 실행 |
| `OH-[1-5]` 문자열 (docs+skills+agents 전체) | **정확히 1건** — `getting-started.md:277` | grep |
| 설치 캐시 ↔ 저장소 버전 | 캐시 `0.1.0`·`0.4.0` / 저장소 `0.9.0` — **실경로는 0.4.0** | `ls ~/.claude/plugins/cache/.../pilot`, `plugin.json` |
| `docs/reference/{agents,skills,tools}/` git 추적 | **gitignore 대상** (`pilot/.gitignore:10`) — `git diff` 에 절대 안 나타난다 (critic C5) | `git check-ignore -v pilot/docs/reference/tools/index.md` |
| `getting-started.md` 로 향하는 **앵커** 링크 | **0건** — Troubleshooting 본문 삭제가 링크를 깨지 않는다 (critic C4 안전성 근거) | `grep -rn "getting-started.md#"` |
| `workspace/context/pilot/` 잔존 드리프트 | **3건** — `index.md:43` · `lifecycle.md:22` · `lifecycle.md:69` (critic C6) | 실독 |

## 게이트 설계 — spec 문구의 실측 정정

spec 의 `게이트: docs_build.py --check · test_doc_links` 를 **그대로 쓰면 본 feature 를 검증하지 못한다.** 실측 근거:

- **`test_doc_links.py` 는 `pilot/docs/` 를 스캔하지 않는다.** `SCAN_DIRS = ("skills", "agents")` (`pilot/tests/tools/test_doc_links.py:31`). 즉 이 테스트를 통과시켜도 본 feature 가 만지는 파일의 링크는 한 줄도 검증되지 않는다 → **무관 게이트**. 대체: 동일 로직을 `pilot/docs/` 에 적용하는 인라인 스크립트(G4, baseline 실측 완료).
- **`docs_build.py --check` 는 생성물만 검증한다.** `build()` 산출 집합(`agents/`·`skills/`·`tools/`·`identity.md`) 만 디스크와 대조하며, `docs/reference/index.md` 는 커밋본이라 대상 밖 — 코드 주석이 명시한다: *"`docs/reference/index.md`(커밋본)·`identity.md` 는 이 목록 밖이라 대상이 아니다"* (`pilot/tools/docs_build.py:359-361`). 따라서 `--check` 통과는 **"생성물을 오염시키지 않았다"** 는 회귀 방지 증거일 뿐, 본체 검증이 아니다 → 보조 게이트로 유지(G5).
- **`mkdocs build --strict` 는 로컬 실행 불가** — `mkdocs` 미설치(`which mkdocs` → not found). CI(`.github/workflows/docs.yml`) 의 PR 잡에서만 돈다. 로컬 게이트로 약속하지 않는다.

### 검증 게이트 (전부 로컬 실행 가능 · 기대값 확정)

**G1 — 도구 목록 = `tools/*.py` 집합 완전 일치** (누락·잔존 양방향 검출)

```bash
python3 - <<'PY'
import re, pathlib
line = next(l for l in pathlib.Path('pilot/docs/reference/index.md').read_text(encoding='utf-8').splitlines()
            if 'pilot/tools/*.py' in l)
tail = line.split('`pilot/tools/*.py`', 1)[1]          # C11: 마커 뒤 구간만 파싱
listed = re.findall(r'`([^`]+)`', tail)
actual = sorted(f.stem for f in pathlib.Path('pilot/tools').glob('*.py'))
assert listed == actual, ('listed', listed, 'actual', actual)
print('G1 OK', len(actual), actual)
PY
```

기대: `G1 OK 8 ['auto_pilot', 'confluence', 'docs_build', 'doctor', 'orchestrate-load', 'plan-validate', 'regen-verify', 'slack-notify']`
→ 이 등가를 성립시키려면 나열 순서를 **`sorted()` ASCII 순(= 생성 `reference/tools/index.md` 순서)** 으로 맞춘다. 순서 고정이 목적이 아니라, set 비교보다 강한 계약으로 향후 drift 를 자동 검출하기 위함.
→ **함정 2건 (critic C11)**: ① ASCII 순이라 **`docs_build` 가 `doctor` 보다 앞**이다 — "알파벳순" 만 보고 `doctor, docs_build` 로 쓰면 실패한다. ② 추출은 `` `pilot/tools/*.py` `` **마커 뒤 구간**만 대상으로 한정했으나, 그래도 그 뒤에 도구명 아닌 백틱 토큰을 추가하면 실패한다 — 해당 줄에는 도구명만 백틱으로 감싼다.

**G2 — 삭제 스크립트 4종 문자열 0건** (손으로 쓴 문서 한정)

```bash
grep -rn -E "init_detect|verify-report-lint|memory-hint|diagnose\.py" pilot/docs --include="*.md" \
  | grep -v "^pilot/docs/reference/\(agents\|skills\|tools\)/" ; echo "exit=$?"
```

기대: 매칭 0건(`exit=1`). 주의 — **`diagnose` 단독 문자열을 매칭하면 안 된다.** `--diagnose` 는 삭제된 게 아니라 스킬 지시문 모드로 살아 있다(`pilot/skills/doctor/SKILL.md:35,42-66`). 삭제된 것은 파일 `pilot/tools/doctor/diagnose.py` 뿐이므로 `diagnose\.py` 로만 매칭한다.

**G2b — 삭제된 Onboarding Health ID 0건** (S1 전용)

```bash
grep -rn "OH-[1-5]" pilot/docs pilot/skills pilot/agents --include="*.md"; echo "exit=$?"
```

기대: 매칭 0건(`exit=1`). baseline 은 정확히 1건(`getting-started.md:277`) — 이 1건이 사라지는 것이 S1 스텝의 직접 증거다. `OH-1`~`OH-5` 는 #20 스텝 3 에서 소멸했고 현행 `SKILL.md:68-74` 의 모델 점검 5항목에는 ID 표기가 없으므로, 저장소 전체에서 0건이 정상 상태다.

**G3 — 인바운드 링크 5곳 + nav 무손상** (critic C10 — 총량 등식 → 존재·resolve 검사)

```bash
python3 - <<'PY'
import re, pathlib
EXPECT = {'docs/tutorial/getting-started.md', 'docs/explanation/drift-protocol.md',
          'docs/explanation/release-and-upgrade.md', 'docs/explanation/modes.md',
          'docs/how-to/index.md'}
LINK = re.compile(r'\[[^][]*\]\(([^()\s]+)\)')
root = pathlib.Path('pilot')
found, unresolved, anchored, extra = set(), [], [], []
for md in sorted((root / 'docs').rglob('*.md')):
    rel = md.relative_to(root).as_posix()
    for i, l in enumerate(md.read_text(encoding='utf-8').splitlines(), 1):
        for t in LINK.findall(l):
            if 'doctor-migration.md' not in t:
                continue
            if '#' in t:
                anchored.append(f'{rel}:{i} {t}')
            if not (md.parent / t.split('#')[0]).resolve().exists():
                unresolved.append(f'{rel}:{i} {t}')
            if rel in EXPECT:
                found.add(rel)
            else:
                extra.append(f'{rel}:{i}')
assert found == EXPECT, ('missing', EXPECT - found)
assert not unresolved, unresolved
assert not anchored, anchored          # 앵커 도입 시 파일명 보존만으로는 부족 — 수동 검토 대상
print('G3 OK — 대장 5파일 전건 존재 · resolve OK · 앵커 0 · 초과 참조', extra)
PY
grep -n "how-to/doctor-migration.md" pilot/mkdocs.yml   # nav 1건 유지 (yml — 범위 밖이므로 무변경 확인용)
```

기대: 대장 **5개 파일이 각각 1건 이상** · 전체 링크 resolve · 앵커 0 · nav 1건. 초과 참조(`extra`)는 **실패가 아니라 REPORT 열거 대상** — 다른 페이지가 doctor-migration 을 정당하게 참조하기 시작해도 게이트가 깨지지 않는다.

**G4 — `pilot/docs/` 내부 md 링크 무결** (test_doc_links 미커버 영역 대체)

```bash
python3 - <<'PY'
import re, pathlib
LINK = re.compile(r'\[[^][]*\]\(([^()\s]+)\)')
bad, n = [], 0
for md in sorted(pathlib.Path('pilot/docs').rglob('*.md')):
    for i, l in enumerate(md.read_text(encoding='utf-8').splitlines(), 1):
        for t in LINK.findall(l):
            if '://' in t or t.startswith(('#', 'mailto:')):
                continue
            t0 = t.split('#')[0]
            if not t0 or not t0.endswith('.md'):
                continue
            n += 1
            if not (md.parent / t0).resolve().exists():
                bad.append(f'{md}:{i} -> {t}')
print('checked', n, 'broken', len(bad))
for b in bad: print(' ', b)
assert not bad
PY
```

기대: `broken 0` (baseline 194건/0 broken — 변경 후 검사 건수는 늘어도 broken 은 0 유지).

**G5 — 생성물 미오염 + 회귀**

```bash
python3 pilot/tools/docs_build.py --check                 # exit 0
cd pilot && python3 -m unittest discover -s tests/tools   # 284 tests OK
```

> **삭제됨 (critic C5)** — 기존 3번째 명령 `git diff --name-only | grep -c "^pilot/docs/reference/..."` 는 **무효 게이트**였다. 해당 3개 디렉터리가 `pilot/.gitignore:10` 대상이라 손편집을 해도 `git diff` 에 나타나지 않아 **항상 0** 을 반환한다(`git check-ignore -v` 로 확인). 생성물 손편집 검출은 `docs_build.py --check` 가 **단독으로** 담당한다 — 빌드 결과와 디스크를 직접 대조하므로 gitignore 와 무관하다.

**G6 — 사실 정확성 증거표** (grep 로는 검증 불가한 축 — 서술 대 코드 대조)

재작성한 `doctor-migration.md` 의 **모든 거동 주장**이 코드·SKILL.md 와 일치하는지 대조한다.

> **[확정 — critic C2 제안 ②] 근거 좌표는 문서 본문에 넣지 않는다.** `doctor-migration.md` 는 docs 사이트에 배포되는 **사용자 문서**이고 file:line 은 다음 슬림화에서 즉시 썩는다. 본문은 **함수명·플래그명·동작 수준**으로 서술하고(예: "`--fix` 는 확인 절차 없이 즉시 적용된다"), file:line 근거는 **본 plan 의 정정 대장 · 커밋 메시지 · VERIFICATION REPORT 에만** 남긴다. 스텝 2-a 의 "근거를 붙인다" 는 이 뜻으로 단일 해석한다.

판정 기준 **3축**:

- **축1 — `doctor-migration.md` : § 정정 대장 15행 전부 반영** (12행 + C3 로 추가된 #13~#15)
- **축2 — `getting-started.md` : § S1 정정 대장 3행 전부 반영** (`:277`·`:293`·`:311-314` — 전부 **삭제** 처리)
- **축3 — 신규 서술 무근거 0건** (critic C3): 재작성 후 문서의 각 거동 문장이 (a) 대장 15행 중 하나에 대응하거나 (b) `tools/doctor/*.py` 또는 `skills/doctor/SKILL.md` 근거가 REPORT 에 제시되거나 — **둘 중 하나**임을 evaluator 가 체크리스트로 확인한다. 어디에도 안 걸리는 문장이 1개라도 있으면 fail.
  - 축3 이 없으면 골격이 신설하는 `--diagnose`·`--schema`·Onboarding Health 3개 절이 **어떤 게이트에도 걸리지 않는다** (축1·2 는 커버리지 검사일 뿐). 이 3절은 오독하기 가장 쉬운 영역이라 대장 #13~#15 로도 이중 방어한다.

**G7 — #20 스텝 6 회귀 재확인 (중복 실행 · 완주 판정 아님)** — critic C1 로 격하

D-1 (b) 축소 후 이 항목은 **"게이트" 가 아니라 회귀 재확인**이다. 이름을 정직하게 바꾼다.

- **G7 (a) — `skip — 증거 없음`으로 라벨 고정.** pass 로 적지 않는다. 사이클 산출물 + Bash 오류에 삭제 4파일명 0건이라는 판정은, wrapper 가 자동 실행하는 캐시본이 애초에 그 4파일을 참조하지 않는 0.4.0 이라 **무증상 통과가 당연**하다. 증거력 0.
- **G7 (b) — `#20 스텝 6 회귀 재확인 (중복 실행)`.** 저장소 사본을 1회 호출해 회귀가 없음을 재확인할 뿐이며, 동일 검증은 **#20 세션에서 이미 수행됐다**(`20-*.plan.md:78`). 신규 정보가 아니다.

```bash
python3 pilot/tools/orchestrate-load.py --phase planner --workspace workspace
```

기대: `files_to_read` 에 `${CLAUDE_PLUGIN_ROOT}/skills/context/shared/wrapper-protocol.md` 와 `workspace/context/pilot/index.md` 가 실재 · `hints` 에 `"진입 파일이 MANIFEST 에 등록되지 않음"` 부재. 반드시 **저장소 사본 경로**로 실행한다 — 캐시 경로(`~/.claude/plugins/cache/...`)로 돌리면 D-1 의 미등록 힌트가 그대로 나와 오판한다.

> **이것은 "파이프라인 1사이클 실완주" 가 아니다.** 단위 호출 1건일 뿐이며, #20 이 바꾼 preamble P0 신문안·doctor 슬림 출력의 evaluator 소비·wrapper-protocol 전달은 본 사이클에서 **한 번도 실행되지 않는다**(wrapper 가 로드한 것은 캐시 0.4.0 — 실측). 귀결은 § 리스크 R-1 및 § #20 목표 체크박스 처리 방침.

## 변경 파일

- [x] `pilot/docs/reference/index.md` — `:25` tools 카드의 나열을 `pilot/tools/*.py` 실재 8종(알파벳순)과 일치시킨다. 삭제 3종(`init_detect`·`verify-report-lint`·`memory-hint`) 제거. **다른 줄 무변경** (agents 5 · skills 17 은 실측상 정확).
- [x] `pilot/docs/how-to/doctor-migration.md` — 전면 현행화. 파일명·H1 유지, 아래 § 정정 대장 **15행** 반영 (커밋 2).
- [x] `pilot/docs/tutorial/getting-started.md` — **S1 승인으로 범위 포함 확정.** Troubleshooting §1·§2·§3 의 #20 로 사라진 doctor 거동 3곳(`:277`·`:293`·`:311-314`)을 **삭제**한다 — 대체 절차·버전 분기 서술 금지(사용자 확정 + critic C4). 파일명·§번호·`:281` 앵커 보존, 증상/해결 구조 유지. 인바운드 링크·nav 영향 0(실측). § S1 정정 대장 참조 (커밋 3).
- [x] `workspace/projects/build-plugin/features/20-consolidation-slim.plan.md` — **D-1 (b) 확정에 따른 문구 정정 — Planner 가 본 세션에서 반영 완료** (drift-protocol § B, 수정 주체 = Planner). ① 완주 검증 절 상단에 "판정 범위 축소" blockquote 신설 (저장소 사본 한정 · 캐시 0.4.0 실경로 미검증 한계 · 배포 후 재확인 = 후속 확인 필요) ② 판정 (b) 문장에 "저장소 사본 기준" 명시 + 명령을 `pilot/tools/orchestrate-load.py` 로 정확화 ③ "이 사이클이 #20 변경분의 **실경로를 통과한다**" → 취소선 + "저장소 사본을 직접 호출한 명령에 한해 검증한다" 로 교체. `## 목표`·체크박스류는 무변경. **Generator 는 이 파일을 다시 수정하지 않는다.**

## 정정 대장 — `doctor-migration.md` (실측 대조 15행)

| # | 현행 서술 | 실측 | 근거 |
| --- | --- | --- | --- |
| 1 | `:4` "불일치 사안을 자동 마이그레이션합니다" | 기본 모드는 **검사만**. 수정은 `--fix` 한정 | `doctor.py:73`, `doctor/_common.py:281-283` |
| 2 | `:16` "### 1. 진단 실행 (Read-only)" | **완전한 read-only 가 아니다** — `.gitignore` 의 `.slack.env` 패턴은 `--fix` 없이도 즉시 append (secret 유출 리스크 우선) | `doctor/integrity.py:84-141` (특히 `:123` write_text) |
| 3 | `:22-29` 검사 6항목 | 실제는 workspace 8종 + conventions 2종 + project 9종. 아래 § 현행 검사 항목 | `integrity.py:320-425`, `:456-813`, `:872-937` |
| 4 | `:29` "의존하고 있는 기획서 문서(`docs/`) 파일의 누락 유무" | **그런 검사 없음.** 대신 `conventions_doc`·`conventions_evals` 선언-실존 검사 | `integrity.py:872-937` |
| 5 | `:31` "PASS, WARN, FAIL 로 구분" | 실제 레벨은 **PASS · INFO · WARN · ERROR** (FAIL 은 `--fix` 실패 라벨) | `_common.py:35-38` (레벨 상수) · `:50` (렌더 색상 매핑) · `:295` (FAIL) — *critic C2 로 off-by-one 교정* |
| 6 | `:43` "v1.0 → v1.1 → v1.2 업그레이드" | 라벨은 `v1`·`v1.1`·`v1.2`. 체인이 아니라 현재값(`SCHEMA_VERSION`)으로 **직접 bump** | `_common.py:18-19`, `integrity.py:229-276` |
| 7 | `:43` "`.agent-state.yml.bak-{version}` backup 을 남깁니다" | **거짓 — 백업을 만들지 않는다.** in-place write | `integrity.py:272` (`state_yml.write_text`. 백업 코드 부재, 저장소 전체 `.bak-` 검색 결과 doctor 경로 0건) — *critic C2 교정* |
| 8 | `:43` "필수 필드(`plugin_version`, `mode` 등) 누락 시 default 로 채움" | v1→v1.2 시 `domain: null` 주입만 | `integrity.py:246,:259-265` |
| 9 | `:44` "MANIFEST 테이블 보정 — 사용자 확인 후 수정" | **그런 auto-fix 없음.** `fix=` 는 정확히 3곳 | `integrity.py:380,:507,:802` |
| 10 | `:45` "prompts/ 재생성 (`--regen-agents` 와 동일)" | auto-fix 아님. drift 감지 시 `/pilot:analyze --regen-agents` **권장 hint** 출력만 | `integrity.py:680`·`:714`·`:752`·`:801` **4곳** — *critic C2 교정: 기존 `:711,:749,:763` 은 WARN 줄 인용이었고 특히 `:763` 은 `--regen-agents` 가 아니라 `/pilot:analyze --force` 힌트(`:766`) 블록으로 **무관***. **`:801` 만 `fix=` 동반(`:802`)** 이나 그 fix 는 prompts 재생성이 아니라 `_fix_remove_legacy_planning_section`(레거시 섹션 제거) — 문서에서 혼동 금지 |
| 11 | `:47` "모든 수정 액션 전에 사용자 확인을 요청합니다" | `run_auto_fixes` 는 **확인 없이 즉시 실행** | `_common.py:281-298` |
| 12 | (부재) `--schema` · `--diagnose` · Onboarding Health | 3종 모두 현행 기능인데 문서에 없음 → #13~#15 로 개별 전개 | `doctor.py:56-66`; SKILL `:35,:42-66`; SKILL `:68-74` |
| 13 | (신설 절 `--diagnose`) | **스크립트 플래그가 아니다.** `doctor.py` argparse 에는 `workspace`·`--project`·`--fix`·`--schema` 뿐 — `python3 doctor.py --diagnose` 는 `unrecognized arguments` 로 실패. `/pilot:doctor --diagnose` 슬래시 경유 **모델 지시문 모드**로만 존재하며 4패턴 판정 + `## DIAGNOSIS` 5필드 출력 | `doctor.py:42-61` (argparse), `doctor.py:11-13` (docstring), SKILL `:35`·`:42-66` |
| 14 | (신설 절 `--schema`) | **workspace 인자를 받지 않는다** (플러그인 구조 전용, `workspace` 인자 무시). `.github/workflows/validate.yml` 이 CI 로 실행 | `doctor.py:56-66`, SKILL `:36`, `.github/workflows/validate.yml` |
| 15 | (신설 절 Onboarding Health) | `doctor.py` 출력에 **OH 섹션이 없다**. `/pilot:doctor` **스킬 경유 한정**으로 모델이 점검하며 **발동 조건**이 있다(`## 도메인 분류` 표 0행 **또는** STATE.md 등록 프로젝트 0건). 임베디드 호출에서는 발화하지 않음 | SKILL `:68-74` |

> **#13~#15 는 critic C3 로 추가된 행이다.** 스텝 2-a 골격이 신설하는 3개 절을 커버리지 검사(G6 축1) 대상으로 끌어들여, 오독하기 쉬운 이 영역이 무게이트로 빠져나가지 않게 한다.

### 현행 auto-fix 실측 3종 (`--fix`)

1. **STATE.md 이력 행 정리** — `진행중` 이 아닌 행 제거. `진행중` 2건 이상이면 자동 정리 보류(사용자 판단) — `integrity.py:187-226,:375-382`
2. **`.agent-state.yml` schema 업그레이드** — `v1`/`v1.1` → `v1.2`. `v1` 은 `domain: null` 주입 동반 — `integrity.py:229-276,:503-508`
3. **`prompts/planner.md` 레거시 섹션 제거** — 래퍼로 이관된 `## 플래닝 프로세스` 삭제 — `integrity.py:279-313,:798-803`

`--fix` 무관 자동 조치 1건: `.gitignore` 에 `.slack.env` 패턴 즉시 주입 (`integrity.py:84-141`).

### 현행 검사 항목 (문서에 반영할 실측 목록)

- **Workspace** — `workspace/` 존재 · `.slack.env` git tracked 여부(CRITICAL) · `STATE.md` 진행중 개수(1개만 허용)·이력 행 · `context/MANIFEST.md` 존재 · `context/config.md` 존재 · `workspace/.env` credential drift · `.gitignore` secret 패턴 · auto-memory 감지 안내
- **Conventions** — `conventions_doc`·`conventions_evals` 선언-실존
- **Project** — `projects/{p}` 존재 · `.agent-state.yml` 존재·파싱·schema 지원범위 · `analyzed` ↔ `features/` 정합 · `tdd` 3-way 정합 · `domain` · `pr_base_branch` · `plugin_version` 업그레이드 감지 · features 증감 drift · `prompts/*.md` 중복 주입·레거시 섹션

### 인바운드 링크 대장 (5곳 — 전부 앵커 없음, 파일명 보존만으로 무손상)

| # | 위치 | 링크 텍스트 |
| --- | --- | --- |
| 1 | `pilot/docs/tutorial/getting-started.md:256` | Doctor 진단 및 마이그레이션 |
| 2 | `pilot/docs/explanation/drift-protocol.md:39` | Doctor 진단·마이그레이션 |
| 3 | `pilot/docs/explanation/release-and-upgrade.md:81` | Doctor 진단·마이그레이션 |
| 4 | `pilot/docs/explanation/modes.md:50` | Doctor 진단·마이그레이션 |
| 5 | `pilot/docs/how-to/index.md:95` | Doctor 마이그레이션 |

추가로 `pilot/mkdocs.yml:98` nav 1건(yml — 범위 외) · `pilot/docs/PLAN-manual.md:46,168,264` 3건(spec 상 범위 외).

## S1 정정 대장 — `getting-started.md` Troubleshooting (실측 3행)

> **[확정 방침 — 사용자 결정 + critic C4] 무효화된 항목은 대체 절차를 제안하지 않고 삭제한다.**
> 버전 분기 서술("0.4.0 에서는 X, 0.9.0 에서는 Y")도 쓰지 않는다 — 배포 후 다시 손대야 하기 때문이다. **존재하지 않는 검사를 전제한 안내는 틀린 안내보다 없는 편이 낫다.**
> 특히 S1-3 의 초안이었던 "`orchestrate-load.py` 힌트로 확인" 대체 경로는 **철회**한다 — 튜토리얼 독자가 가진 것은 저장소가 아니라 **설치 캐시**이고, 캐시 0.4.0 에서는 MANIFEST 를 올바르게 고쳐도 미등록 힌트가 그대로 나온다. 증상을 "아무 오류도 안 나온다" 에서 "계속 실패로 나온다" 로 바꿀 뿐이다. 게다가 `orchestrate-load.py` 는 wrapper 내부 헬퍼이지 사용자 대면 CLI 가 아니다.

| # | 위치 | 현행 | 실측 | 처리 |
| --- | --- | --- | --- | --- |
| S1-1 | `:277` (§1 config.md fallback) | "`/pilot:doctor` 명령어로 `OH-1` 진단 항목을 확인한 뒤" | `OH-1`~`OH-5` ID 는 #20 스텝 3 에서 삭제. `doctor.py` 출력에 OH 섹션 자체가 없다 (`SKILL.md:70` 이 명시) | **doctor 절만 삭제.** 같은 문장의 유효분(`config` 표가 비면 `/pilot:init` 재실행 · 기존 `config.md` 존재 시 wizard skip 주의)은 **보존**. `:274` 의 `cat config.md` 확인 블록도 보존 |
| S1-2 | `:293` (§2 wizard 매핑 정정) | "`/pilot:doctor` # schema 검증 수행 — 오류가 없으면 PASS" | `check_workspace_config_sections`(`## scope 카테고리`·`## Ignore` 표 검증)는 #20 스텝 2 에서 삭제. 현재는 `config.md` **존재 여부**만 검사 | **코드블록(`:292-294`) 통째로 삭제.** 앞의 수동 편집 지시 1·2 는 그대로 유효하므로 보존. 대체 검증 절차를 새로 제안하지 않는다 |
| S1-3 | `:311-314` (§3 learn H2 매칭 실패) | "`/pilot:doctor` # 헤더 정합성 검사 — 오류 보고 확인" → "doctor 진단 도구가 헤더 불일치를 보고하면 …" | 동일 — 헤더 정합성 검사 삭제됨. 절차를 따라도 **아무 오류가 보고되지 않아 사용자가 막힌다** | **코드블록(`:310-312`) + doctor 의존 조건절 삭제.** `:305` 의 `grep "^##" MANIFEST.md` 확인 블록과 "`## 도메인 분류` 헤더를 올바르게 수정한다" 는 수동 지시는 **보존** — 조건절만 걷어내 평서문으로 남긴다 |

**삭제 안전성 실측** (삭제가 문서 구조를 깨지 않음을 사전 확인):

- §번호(`### 1.`~`### 4.`)는 **헤딩을 건드리지 않으므로 불변** — 본문 일부만 제거한다.
- `:281` 의 명시 앵커 `{ #2-wizard-잘못-매핑-정정-경로 }` 는 §2 **헤딩에** 있어 무영향. 보존한다.
- **`getting-started.md` 로 향하는 앵커 링크는 저장소 전체에 0건** (`grep -rn "getting-started.md#"` → 무매칭). 본문 삭제로 깨질 인바운드 앵커가 없다.
- 인바운드 링크 대장 #1(`:256`)은 "다음 단계" 절이라 Troubleshooting 삭제 범위 밖 — G3 카운트 무영향.
- 삭제만 하므로 신규 링크가 생기지 않아 G4 도 무영향.

## 구현 순서

1. **`reference/index.md` 도구 목록 정정** (커밋 1) — `:25` 한 줄만 편집. 나열을 `pilot/tools/*.py` 실재 8종으로 교체(3종 제거). 편집 직후 **G1 즉시 실행**해 등가 확인. 다른 카드(agents·skills)·문단은 손대지 않는다.
   - **정렬은 `sorted()` ASCII 순 — `docs_build` 가 `doctor` 보다 앞이다** (critic C11). "알파벳순" 이라는 말만 보고 `doctor, docs_build` 로 쓰면 G1 이 실패한다.
   - **해당 줄에 도구명 외 백틱 토큰을 추가하지 않는다** — G1 은 `` `pilot/tools/*.py` `` 마커 뒤의 모든 백틱 토큰을 도구명으로 간주한다.
   - 영향 파일: `pilot/docs/reference/index.md`

2. **문서 본문 정정 — 성격이 다르므로 두 커밋으로 분리** (critic C8. PR 은 1개 유지 — "문서 정합의 원자성" 은 PR 단위로 충족된다)

   **2-a. `doctor-migration.md` 현행 재작성** (커밋 2) — 파일명·H1 유지(§ 주의사항 nav 제약). § 정정 대장 **15행** 전부 반영. 귀속 게이트: **G3 · G4 · G6-축1 · G6-축3**. 권장 골격:
   `한 줄 요약(정정)` → `전제 조건`(대체로 유지) → `1. 정합성 검사(기본)` — 검사 항목 + 판정 레벨 4종 + exit code(`SKILL.md:30`) → `2. 자동 수정(--fix)` — 실측 3종 표 + **백업 없음** + **확인 없이 즉시 적용** 명시 + `.gitignore` 예외 → `3. 재검증` → `4. 실패 진단(--diagnose)` — 스크립트 아님·4패턴·`## DIAGNOSIS` 5필드·호출 시점 → `5. 플러그인 구조 검사(--schema)` — `validate.yml` CI 연동 → `Onboarding Health` 1문단(스킬 경유 한정) → `다음 단계`(기존 링크 2건 보존).
   - 새 링크를 넣을 때는 상대 경로 실존만 사용(`../reference/skills/doctor.md`·`../explanation/release-and-upgrade.md`·`../tutorial/getting-started.md`). 플러그인 내부 파일(`skills/...`)은 기존 `:61` 패턴대로 GitHub blob 절대 URL 사용 — `${CLAUDE_PLUGIN_ROOT}` 표기 금지(docs 사이트에서 해석 불가).
   - **본문에 file:line 을 쓰지 않는다** (critic C2 확정) — 함수명·플래그명·동작 수준으로 서술. 좌표는 커밋 메시지·REPORT 에만.
   - **`--fix` 무관 자동 조치(`.gitignore` 주입) 서술 시 단정을 감추지 않는다** (critic C7) — 같은 사이트의 `reference/skills/doctor.md:71-72` 가 "비파괴 — 파일 수정 안 함" 이라 정면 충돌한다. 그 페이지는 `SKILL.md:79-80` 파생물이라 본 범위 밖이므로, 사실대로 쓰되 § 리스크 R-2 에 잔존 모순으로 기록된 상태임을 전제한다.
   - 영향 파일: `pilot/docs/how-to/doctor-migration.md`

   **2-b. `getting-started.md` Troubleshooting 3곳 삭제** (커밋 3) — § S1 정정 대장 3행을 **삭제**로 처리. 귀속 게이트: **G2b · G3 · G6-축2**.
   - §번호·증상/해결 구조·`:281` 앵커는 그대로 두고, 무효화된 doctor 절·코드블록만 제거한다. **대체 절차·버전 분기 서술 금지** (사용자 확정 + critic C4).
   - `:256` 의 doctor-migration 인바운드 링크(대장 #1)를 **건드리지 않는다** — Troubleshooting 밖 "다음 단계" 절이라 정상 작업 시 무영향이나, G3 이 이 파일의 링크 존재를 요구한다.
   - 2-a 와 분리하는 이유: 재작성본이 리뷰에서 반려돼도 이미 결정적 grep(G2b)으로 검증된 이 3곳 삭제가 함께 되돌아가지 않게 한다. G3 실패 시 원인 파일 판별도 쉬워진다.
   - 영향 파일: `pilot/docs/tutorial/getting-started.md`

3. **게이트 실행 + 증거 기록** (커밋 4) — G1~G7 순서대로 실행하고 출력을 그대로 캡처.
   - G6 은 정정 대장 **15행** + S1 대장 3행 + **축3(신규 서술 무근거 0건)** 을 체크리스트로 남긴다.
   - G7 은 **저장소 사본** `python3 pilot/tools/orchestrate-load.py` 로 실행한다 — 캐시 경로(`~/.claude/plugins/cache/...`)로 실행하면 D-1 의 미등록 힌트가 그대로 나와 오판한다(§ 리스크 R-1). **(a) 는 `skip — 증거 없음`, (b) 는 "회귀 재확인" 으로 기록** — pass 로 적지 않는다.
   - D-1 (b) 의 `20-*.plan.md` 문구 정정은 **Planner 가 이미 반영 완료** — Generator 는 재수정하지 않고 diff 존재만 확인한다. 이 diff 는 **커밋 4 에 귀속**한다 (generator 재량 아님 — critic C8).
   - 커밋 scope: 커밋 1~3 은 `docs:`, 커밋 4 는 `skills:` (`workspace/` 산출물 포함). `workspace/context/config.md` 의 `commit_scopes` 확인 대상.
   - **doctor baseline 재측정 시 CWD 를 저장소 루트로 고정** (critic 참고표) — `pilot/` 에서 돌리면 `8 PASS` 로 달라져 baseline `9 PASS · 4 WARN · 0 ERROR` 와 어긋난다.
   - 영향 파일: `workspace/projects/build-plugin/features/20-consolidation-slim.plan.md` (Planner 정정분 커밋 귀속) + 검증 대상 = 커밋 1~3 산출물 전체

## 주의사항

- **H1 wording 은 "마이그레이션" 을 유지한다.** `mkdocs.yml:98` nav 라벨이 `Doctor 진단·마이그레이션` 인데 yml 은 md 가 아니라 수정 범위 밖이다. 제목에서 "마이그레이션" 을 빼면 nav ↔ 페이지 제목이 어긋난다. 게다가 schema 마이그레이션(`v1`→`v1.2`)은 **여전히 살아 있는 기능**이라 제목은 사실에도 부합한다 — 개명 유혹을 차단한다.
- **`--diagnose` 를 "삭제됨" 으로 쓰지 않는다.** 삭제된 것은 `pilot/tools/doctor/diagnose.py` 이고, `--diagnose` 는 `/pilot:doctor` 슬래시 경유 **모델 지시문 모드**로 존재한다(`SKILL.md:42-66`). 반면 `python3 doctor.py --diagnose` 는 이제 `unrecognized arguments` 로 실패한다 — 두 경로를 구분해 서술한다.
- **`how-to/index.md:99` 카드 설명은 무변경.** "schema 버전 자동 migration(예: v1.1 → v1.2) 및 구조 정합성" 은 실측상 정확 — 불필요한 확장 금지.
- **생성물 디렉터리 직접 수정 금지** — `docs/reference/{agents,skills,tools}/` 는 `docs_build.py` 산출물이며 `pilot/.gitignore:10` 대상이다. **손편집 검출은 `docs_build.py --check` 가 단독으로 담당한다** (critic C5) — gitignore 대상이라 `git diff` 계열 명령으로는 절대 잡히지 않는다.
- **`PLAN-manual.md` 는 범위 외** (spec 비즈니스 규칙). `:46,:168,:264` 의 stale 서술은 손대지 않는다 — 손대면 spec 위반.
- **Python·SKILL.md 무변경** — 계획 중 `SKILL.md:34` 의 stale 문구(`--fix` 설명에 `.gitignore` secret 주입이 섞여 있으나 실제로는 `--fix` 무관 자동 조치)를 발견했다. **이번 범위 밖** — 아래 § 후속 인수인계로 넘긴다.
- **generator 는 `project.md` `## 목표` 체크박스를 수정하지 않는다** — evaluator 단독 권한 (#03 전달사항 정착 룰).
- **커밋 단위 — 4 커밋 / 1 PR 확정** (critic C8, generator 재량 없음): 커밋 1 = `reference/index.md` · 커밋 2 = `doctor-migration.md` 재작성 · 커밋 3 = `getting-started.md` 삭제 3곳 · 커밋 4 = `20-*.plan.md` diff + 게이트 증거. "문서 정합의 원자성" 은 **PR 단위**로 충족한다.
- **`workspace/context/` 무변경** — D-2·D-3 이 범위에서 빠졌으므로 `workspace/context/` 하위 파일은 이번 사이클에서 **한 줄도 수정하지 않는다.** `git diff --name-only | grep "^workspace/context/"` 가 0 건이어야 한다.
- **D-2·D-3 의 별도 feature 등록은 메인 대화 담당** — Planner·Generator 는 `features/` 에 새 spec 을 만들지 않는다.
- **#20 목표 체크박스는 건드리지 않는다** — 아래 § #20 목표 체크박스 처리 방침이 단독 SSOT. evaluator 도 이 방침을 따른다.

## #20 목표 체크박스 처리 방침 (critic C1 · 사용자 확정 2026-07-25)

> **결론: `project.md` 의 #20 항목은 `[ ]` unchecked 로 유지한다. #21 완주는 `[x]` 처리의 근거가 아니다.**

- **evaluator 에게** — `#21 status: READY` 를 "#20 dogfooding 게이트 통과" 로 해석하지 않는다. 본 사이클이 #20 에 대해 **신규로 보증하는 것은 0건**이다(§ 리스크 R-1). #20 항목을 `[x]` 로 바꾸지 말 것.
- **체크 조건** — "배포 후 **설치 캐시 실경로**로 1사이클 검증" 이 충족될 때만 `[x]`. 그때까지 `[ ]` 가 **정상 상태**이며 미완 누락이 아니다.
- **사유 문안 (evaluator 가 목표 항목에 반영할 문구 — planner 는 문안만 제공, 목표 줄 편집은 evaluator 단독 권한)**:

  ```
  - [ ] 정비 slim — Python 슬림화 -> [상세](features/20-consolidation-slim.md) `[consolidation 3/3]` (dogfooding 게이트 미충족 — #21 사이클은 저장소 사본만 검증, 설치 캐시 실경로는 배포 후 재확인 필요)
  ```

  괄호 주석만 덧붙이고 체크박스·링크·라벨은 원형 유지. 이 문안을 쓸지, 더 짧게 줄일지는 evaluator 재량이나 **"배포 후 실경로 재확인 필요" 라는 사실은 반드시 남긴다.**

## 사용자 결정 (확정 2026-07-25)

### S1 → **이번 #21 범위 포함** (승인)

`getting-started.md` Troubleshooting 3곳(`:277`·`:293`·`:311-314`) 정정을 스텝 2-b 로 편입. md-only·파일명 보존 제약 동일 적용. 변경 파일 목록·게이트(G2b·G6)·스텝 분할에 반영 완료. 상세 근거는 § S1 정정 대장.

### D-1 → **(b) 저장소 사본 기준으로 축소** (승인)

- **경위**: 본 planner 세션의 wrapper 가 실행한 것은 설치 캐시 `~/.claude/plugins/cache/radiostart-plugins/pilot/0.4.0/tools/orchestrate-load.py` 다. 반환 JSON 에 `pilot/index.md`·`wrapper-protocol.md` 가 없고 `"도메인 'pilot' 의 진입 파일이 MANIFEST 에 등록되지 않음"` 힌트가 그대로 나왔다. 저장소 사본(`pilot/tools/orchestrate-load.py`)은 정상 — 두 파일을 싣고 미등록 힌트가 없다. 캐시는 `0.1.0`·`0.4.0` 뿐, 저장소는 `plugin.json` 기준 `0.9.0`.
- **(a) 안 기각 사유** — *critic C9 로 근거 정정 (결정은 유지)*: 초안은 "마켓플레이스가 GitHub 클론이라 머지·배포 선행 필요" 라고 적었으나 **부정확**하다. 설치 위치는 `~/.claude/plugins/installed_plugins.json` 의 `pilot@radiostart-plugins → installPath` 로 **로컬 디렉터리 + 로컬 JSON 레지스트리**이며, 마켓플레이스 원본(git URL)과는 별개 계층이라 디렉터리 교체·`installPath` 재지정 경로가 **기술적으로는 존재**한다. 실제 기각 사유는 둘이다 — ① **사용자 전역 플러그인 설치본을 검증 목적으로 변조하는 것이 부적절** ② **세션 중 플러그인 리로드가 되지 않아 wrapper 실경로 재현이 어차피 성립하지 않는다**. 근거를 바로잡아 두지 않으면 후속 담당자가 "배포만 되면 자동 해소" 로 오해해 `pilot-update.sh` 실행·세션 재시작을 빠뜨린다.
- **확정 처리**: ① #20 dogfooding 게이트 판정 근거를 **"저장소 사본 기준 검증"** 으로 명시 축소 (G7) ② `20-consolidation-slim.plan.md:77-80` 에서 "실경로 통과" 를 함의하는 표현을 정정 (스텝 3) ③ 실경로 미검증을 한계로 명시 기록 (§ 리스크 R-1) ④ 배포 후 실경로 재확인은 **후속 확인 필요** 로만 표기 — feature 등록은 메인 대화가 별도 처리.

### D-2 · D-3 → **이번 사이클 범위 제외** (별도 feature 로 분리)

두 건 모두 본 feature 의 md-only 범위 밖이며, 별도 feature 로 분리 등록하기로 확정됐다(등록은 메인 대화가 처리 — Planner·Generator 는 **건드리지 않는다**). 번호는 미확정이므로 단정 참조하지 않는다.

- **D-2 (§ A) `workspace/context/pilot/` 잔존 드리프트 — 실측 3건** (critic C6 로 1건 → 3건 정정. 메인 대화가 **이 인벤토리를 근거로** 분리 feature 를 등록한다):

  | # | 위치 | 현행 서술 | 실측 |
  | --- | --- | --- | --- |
  | 1 | `index.md:43` | P-N 매트릭스 헤더 `P0 (memory-hint)` | `memory-hint.py` 는 #20 스텝 4b 삭제. P0 은 "MEMORY.md 색인 직접 선별 Read"(`preamble.md`) |
  | 2 | `lifecycle.md:22` | "`tools/init_detect.py` `detect_languages()` → … default 패턴 주입" | `init_detect.py` 는 #20 스텝 4c 삭제 — `ls pilot/tools` 8종에 부재. init SKILL 의 Glob 직접 판단으로 이관 |
  | 3 | `lifecycle.md:69` | "(진단 모드는 `tools/doctor/diagnose.py`)" | `diagnose.py` 는 #20 스텝 4a 삭제 — `pilot/tools/doctor/` = `__init__`·`_common`·`integrity`·`schema` 뿐 |

  처리 경로는 3건 모두 `/pilot:learn` 재실행 — **직접 Edit 금지**(drift-protocol § A). 기존 이월 항목 `project.md:157` 은 `spec.md`·`index.md` 만 언급해 **`lifecycle.md` 2건을 커버하지 못한다**.
- **D-3 (§ A) `workspace/context/config.md:32-33`** — `conventions_doc`/`conventions_evals` 행의 값 셀 `` 예: `context/conventions.md` `` 가 설명용 플레이스홀더인데 `check_conventions_paths`(`integrity.py:872-937`)가 실선언으로 파싱해 매 실행 WARN 2건 발화(현행 doctor WARN 4건 중 2건). 실측: `conventions: conventions_doc=예: \`context/conventions.md 로 선언됐으나 파일 없음`. 근본 원인이 파서라 문서만 고치면 다른 사용자 workspace 의 동일 오탐이 남는다.

> **누적 임계 정리 (critic C6 반영)** — **결정이 필요한 건은 3건**(D-1·D-2·D-3)이고, 그와 별개로 **사후 정리 대상 라인은 3건**(D-2 인벤토리 표)이다. drift-protocol § 누적 임계(3건 이상)에 도달했으나 일괄 정리 명령(`--regen-agents`·`doctor --fix`)으로 해소되는 항목은 **하나도 없었다** — 경로가 각각 배포·`/pilot:learn` 재실행·코드 수정이라 개별 결정으로 처리했고 위와 같이 전건 확정됐다.

## 리스크

**R-1. 본 사이클은 설치 캐시(실경로)를 검증하지 않는다 — 명시적 한계**

- 이 #21 사이클이 통과시키는 것은 **저장소 사본(0.9.0)** 의 거동뿐이다. wrapper 가 실제로 로드하는 것은 설치 캐시 **0.4.0** 이므로, #20 이 바꾼 `orchestrate-load.py`(anchored H2 매칭·`_common.py` dedup·`wrapper-protocol.md` 배선)·`preamble.md` P0 신문안·doctor 슬림 출력은 **본 사이클에서 실경로로 실행되지 않았다.**
- 따라서 "#21 사이클 완주 = #20 실사용 검증 완료" 로 읽으면 안 된다. G7 의 판정은 저장소 사본 직접 호출 결과로 한정한다.
- 반대로, 본 사이클이 캐시 0.4.0 으로 무사히 돌았다는 사실은 **하위호환 신호로도 쓸 수 없다** — 0.4.0 은 애초에 #20 삭제 대상 4파일을 참조하지 않는 구버전이라 무증상 통과가 당연하다.
- **본 사이클이 #20 에 대해 신규로 보증하는 것은 0건이다** (critic C1). G7 (a) 는 증거력 없음(skip), (b) 는 #20 세션이 이미 수행한 동일 검증의 재실행이다. 이 사실이 § #20 목표 체크박스 처리 방침의 근거다.
- **후속 확인 필요 — 5단계** (critic C9): ① PR 머지 → ② 배포 → ③ `pilot/tools/pilot-update.sh` 실행(캐시 갱신) → ④ **세션 재시작**(세션 중 플러그인 리로드 불가) → ⑤ 실경로에서 G7 기대값 재측정. 배포만으로는 자동 해소되지 않는다. 본 plan 은 이 항목을 **미완**으로 남긴다.

**R-2. 문서 정확성은 자동 게이트로 완전 보증되지 않는다** — G1~G5·G7 은 기계 검증이지만, `doctor-migration.md`·`getting-started.md` 의 *서술이 코드와 일치하는가* 는 G6 의 3축 인스펙션(대장 15행 + S1 3행 + 신규 서술 무근거 0건)에 의존한다. 축3 을 형식적으로 통과시키면 다음 슬림화 때 같은 drift 가 재발한다.

**R-3. [알려진 잔존 모순] 같은 docs 사이트 안에서 doctor 서술이 충돌한 채 머지된다** (critic C7)

- 신규 `how-to/doctor-migration.md` — "doctor 는 `--fix` 없이도 `.gitignore` 를 수정한다 / `--fix` 는 확인 없이 즉시 적용한다" (실측 참)
- `reference/skills/doctor.md:71-72` — "검사는 **비파괴** — 읽기만 함, 파일 수정 안 함(`--fix` 제외)" · "fix 제안은 출력하되 자동 적용 안 함"

두 페이지가 같은 사이트에 공존한다. 후자는 `skills/doctor/SKILL.md:79-80` 의 `docs_build.py` 파생물이고 **SKILL.md 는 spec 비즈니스 규칙상 본 범위 밖**이라 이번에 고칠 수 없다. **evaluator 는 이 모순을 (a) 본 feature 의 결함으로 오판하지도, (b) 조용히 넘기지도 말고** — 알려진 잔존 모순으로 REPORT 에 명시하고 § 후속 인수인계 1번 항목과 연결한다.

## 전달사항 소비 (project.md `## 에이전트 간 전달사항`)

> **체크박스 권한** — 본 절은 처리 **방침만** 기술한다. `[x]` 표기는 evaluator wrapper 단독 권한이며 planner·generator 는 찍지 않는다 (사용자 지시 2026-07-25 + #03 정착 룰).

**본 feature 가 소비 — 구현 완료 후 evaluator 가 `[x]` 처리할 대상 3건**

- `:133` (#14) "가이드 본문의 명령 출력 캡처는 v0.3.0 시점 SKILL.md 형식 … 수동 갱신" → **S1 승인으로 소비 확정.** #20 이 무효화한 `getting-started.md` Troubleshooting 3곳을 스텝 2-b 에서 정정한다. 소비 사유 부기 예: "#21 S1 로 doctor 관련 3곳 정정 (OH-1·config 표 검증·헤더 정합성 검사)".
- `:146` (#07) "`getting-started.md` analyze 출력 코드블록 drift 점검" → **무변경 확인으로 소비.** #20 은 analyze 출력을 바꾸지 않았고, 실측상 analyze 코드블록에 stale 서술이 없다. 문제는 doctor 관련 3곳뿐이며 S1 이 흡수.
- `:150` (#08) "`getting-started.md` project 출력 코드블록 drift 점검" → **무변경 확인으로 소비.** `:104` 의 `doctor: all checks passed` 한 줄은 현행 임베디드 출력 규칙(`SKILL.md:40`)과 여전히 일치.

**이월 유지 (unchecked) 1건**

- `:157` (#19) "`spec.md`·`index.md` 의 SKILL.md 라인 인용 전면 stale → PR 머지 후 `/pilot:learn` 재실행" → D-2 와 동일 계열. 본 feature 는 `workspace/context/` 를 건드리지 않으므로 **이월 유지** (직접 Edit 금지, drift-protocol § A).

**무관 15건 — 이월 유지 (unchecked)**

`:106` · `:116` · `:118` · `:122` · `:125` · `:126` · `:129` · `:132` · `:135` · `:143` · `:144` · `:145` · `:147` · `:149` · `:152`

전부 v0.4.0 이월 노트 또는 재사용 패턴 메모로 #20 삭제·#21 문서 정합과 접점이 없다. #20 planner 의 D4 승인(전건 이월)과 동일 성격 — 이번에도 이월 유지.

## 후속 인수인계 (본 feature 범위 밖 발견)

- **`pilot/skills/doctor/SKILL.md` 2곳 — 한 건으로 묶어 처리** (critic C7 로 `:79-80` 추가). SKILL.md 는 #21 범위 밖(spec 비즈니스 규칙)이라 후속 feature 대상:
  - `:34` — `--fix` 설명이 "`.gitignore` secret 패턴 주입·STATE.md 이력 정리·schema 업그레이드 등" 인데 `.gitignore` 주입은 실측상 **`--fix` 무관 무조건 실행**(`integrity.py:84-141`).
  - `:79-80` — "검사는 **비파괴** — 읽기만 함, 파일 수정 안 함(`--fix` 제외)" · "fix 제안은 출력하되 자동 적용 안 함" 두 줄이 실측과 정반대. **`:34` 보다 이쪽이 신규 `doctor-migration.md` 와 더 직접 충돌**하며, `docs_build.py` 파생물인 `reference/skills/doctor.md:71-72` 를 통해 같은 사이트에 배포된다(§ 리스크 R-3).
- `pilot/docs/PLAN-manual.md:264` — `schema 버전 감지 → migration 경로 (v1.0→v1.1→v1.2)` 표기가 실제 라벨(`v1`·`v1.1`·`v1.2`)과 불일치. spec 상 범위 외 — 메타 산출물 갱신 시 함께 처리.
- 설치 캐시(0.4.0) ↔ 저장소(0.9.0) 버전 격차 — R-1 참조. 사용자 환경 업데이트 절차(`pilot/tools/pilot-update.sh`)의 실행 시점을 릴리스 문서(`explanation/release-and-upgrade.md`)에 명문화할 필요. **후속 확인 필요** 항목.
- D-2 (`context/pilot/` 드리프트 **3건** — `index.md:43` · `lifecycle.md:22` · `lifecycle.md:69`) · D-3 (`config.md:32-33` conventions 오탐) — 별도 feature 로 분리 확정, 등록은 메인 대화 담당. **D-2 는 위 인벤토리 표가 스코프 근거** — 1건으로 등록하면 `lifecycle.md` 2건이 누락된다.

## 교차 의존

- **#20** — 본 feature 는 #20 최종 게이트의 소재로 **기획됐으나, D-1 (b) 축소 후 그 역할을 실질적으로 수행하지 못한다** (critic C1). 남은 검증은 저장소 사본 단위 호출 1건(= #20 세션이 이미 수행한 것의 재실행)뿐이며 **신규 보증 0건**이다. 따라서 **#20 목표 체크박스는 unchecked 유지**한다 — § #20 목표 체크박스 처리 방침이 단독 SSOT. 실경로 재확인은 배포 후 5단계 절차로 남는다(§ 리스크 R-1). Planner 가 `20-consolidation-slim.plan.md:74-82` 문구를 이미 정정했다.
- **#19** — `context/pilot/index.md`·`spec.md` 재학습 이월(전달사항 `:157`, D-2 와 동일 계열)은 본 PR 머지 후 `/pilot:learn` 재실행에서 일괄 흡수된다. 본 feature 는 `workspace/context/` 를 **건드리지 않는다.**
- **분리된 별도 feature 2건** — D-2·D-3. 번호 미확정이라 단정 참조하지 않는다. 본 feature 와 파일 충돌 없음 (대상이 `workspace/context/` 및 `pilot/tools/doctor/integrity.py` 로 본 범위 밖).

## 게이트 실행 결과 (Generator, 2026-07-25 · HEAD 4c0f027)

커밋 1~3 (`reference/index.md`·`doctor-migration.md`·`getting-started.md`) 완료 후 저장소 루트 CWD 기준 실행.

- **G1** — `listed == actual` 성립. `G1 OK 8 ['auto_pilot', 'confluence', 'docs_build', 'doctor', 'orchestrate-load', 'plan-validate', 'regen-verify', 'slack-notify']` → **pass**
- **G2** — `grep -rn -E "init_detect|verify-report-lint|memory-hint|diagnose\.py" pilot/docs --include="*.md" | grep -v "^pilot/docs/reference/..."` → 매칭 0건(`exit=1`) → **pass**
- **G2b** — `grep -rn "OH-[1-5]" pilot/docs pilot/skills pilot/agents --include="*.md"` → 매칭 0건(`exit=1`) → **pass**
- **G3** — `G3 OK — 대장 5파일 전건 존재 · resolve OK · 앵커 0 · 초과 참조 []` + `pilot/mkdocs.yml:98` nav 1건 유지 확인 → **pass**
- **G4** — `checked 194 broken 0` → **pass**
- **G5** — `python3 pilot/tools/docs_build.py --check` exit 0 · `python3 -m unittest discover -s tests/tools`(pilot CWD) `Ran 284 tests ... OK` → **pass**
- **G6 (축1 — 정정 대장 15행)** — 재작성한 `doctor-migration.md` 본문 대조: #1 "기본 검사=검사 전용, 수정은 --fix 한정"(:4) · #2 ".gitignore .slack.env 즉시 주입"(§2 하단 무관 조치 문단) · #3 workspace 8종+conventions 2종+project 9종 3카테고리 나열(§1) · #4 conventions_doc/evals 선언-실존 검사로 대체(§1, docs/ 누락 검사 서술 제거) · #5 PASS·INFO·WARN·ERROR 4단계(§1) · #6 v1/v1.1/v1.2 라벨 직접 bump(§2 표) · #7 백업 없음 명시(§2 "주의할 점") · #8 domain: null 만 주입(§2 표) · #9 MANIFEST 표 보정 auto-fix 아님 명시(§2 하단) · #10 prompts 재생성=권장 안내만·레거시 섹션 제거만 fix(§2 표+하단) · #11 확인 없이 즉시 적용(§2 "주의할 점") · #12~#15 신설 절 3개(§4 --diagnose·§5 --schema·Onboarding Health) 전건 반영 → **15/15 반영, pass**
- **G6 (축2 — S1 대장 3행)** — `getting-started.md` §1(:277 OH-1 문구 삭제, fallback 지시 보존) · §2(:292-294 코드블록 삭제, 1·2번 지시 보존) · §3(:310-312 코드블록+조건절 삭제, grep 확인 블록·헤더 수정 지시 보존) 3행 전건 삭제 처리 확인, 대체 절차·버전 분기 서술 0건 → **pass**
- **G6 (축3 — 신규 서술 무근거 0건)** — `doctor-migration.md` §4(--diagnose)·§5(--schema)·Onboarding Health 각 문장이 대장 #13~#15 대응 확인. §4: "스크립트 플래그 아님·`python3 doctor.py --diagnose` unrecognized arguments 실패·슬래시 경유 모델 지시문·4패턴·5필드 DIAGNOSIS" = `doctor.py` argparse(`workspace`·`--project`·`--fix`·`--schema` 뿐) + `skills/doctor/SKILL.md` § 진단 모드 근거. §5: "workspace 인자 없음·validate.yml CI" = `doctor.py` argparse(`--schema` 시 `workspace` 미참조) + `skills/doctor/SKILL.md:36`·`.github/workflows/validate.yml` 근거. Onboarding Health: "doctor.py 출력에 OH 섹션 없음·스킬 경유 한정·발동 조건 2가지" = `skills/doctor/SKILL.md` § Onboarding Health 근거. 무근거 문장 0건 → **pass**
- **G7** — `python3 pilot/tools/orchestrate-load.py --phase planner --workspace workspace` (저장소 사본) 실행 결과 `files_to_read` 에 `wrapper-protocol.md`·`workspace/context/pilot/index.md` 실재, `hints` 에 미등록 힌트 부재 확인. **(a) `skip — 증거 없음`** (증거력 없음, plan 판정대로) · **(b) "#20 스텝 6 회귀 재확인 (중복 실행)"** — #20 세션이 이미 수행한 동일 검증의 재실행이며 본 사이클의 신규 보증은 0건. **pass 로 기재하지 않음.**
- **`workspace/context/` 무변경 확인** — `git diff --name-only | grep "^workspace/context/"` → 0건 → **pass**
- **`20-consolidation-slim.plan.md` 재확인** — D-1 (b) 정정문(`:74-82` 판정 범위 축소 blockquote·취소선)이 HEAD 에 이미 반영돼 있음을 확인 (Planner 선반영분, 본 세션 재수정 없음).

**커밋 대장** — 1: `pilot/docs/reference/index.md`(065b716) · 2: `pilot/docs/how-to/doctor-migration.md`(13bbb8a) · 3: `pilot/docs/tutorial/getting-started.md`(4c0f027) · 4: 본 게이트 증거 + 체크박스 갱신(본 커밋, `skills:` scope).
