# 2026-08-03 감사 잔여 결함 정비 (audit-remediation) Implementation Plan — Rev.2

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Rev.2 (v0.14.0 재베이스)**: 초판은 v0.10.0 체크아웃 기준이었다. 업스트림 v0.14.0(커밋 1914428)이 초판 항목 중 focus 훅 예외(+테스트)·doctor feature 오계상("stem 에 `.` 있으면 파생" 규칙)을 이미 해결했고, 이슈 모드 evaluator REPORT 저장(`issue.eval[.r{N}].md`) 컨벤션을 신설했다. 본 개정판은 v0.14.0 에서 실측 재확정한 잔여 결함만 다루며, REPORT 영속화 명명을 업스트림 컨벤션(`.eval.md`)에 맞춘다. Slack pr 기본값 변경은 HANDOFF 백로그의 "제품 판단 필요" 항목 — **사용자가 "기본값에 pr 포함"으로 확정**(2026-08-03).

**Goal:** v0.14.0 에서 실측 확정된 잔여 결함 7건 — critic `.plan.critic.md` 덮어쓰기 훅 차단(rc=2 실측) · autopilot `.auto.md` append 훅 차단(rc=2) · 프로젝트 모드 REPORT 비영속 · 사장된 감사 인용 · GUIDE B-2 잔여 · 스킬 description 과잉 · Slack pr 기본값 누락 — 을 수정한다.

**Architecture:** 훅 충돌은 "재생성이 설계 의도인 evaluator REPORT 산출물(`.eval[.r{N}].md`)만 훅 예외 + 나머지(critic 갱신·auto 로그 append)는 문서를 Edit 기반 절차로 개정" 하는 하이브리드. 프로젝트 모드 REPORT 영속화는 이슈 모드의 기존 `issue.eval.md` 컨벤션을 `features/NN-{slug}.eval.md` 로 대칭 확장한다 (이슈 모드 동일-라운드 재평가 덮어쓰기가 훅에 막히는 잠재 결함도 같은 예외로 함께 해소).

**Tech Stack:** Bash 훅(`hooks/protect-managed.sh`), Python unittest(`tests/tools/*.py` — 단독 실행 또는 `python3 -m unittest discover`), Markdown 스킬/에이전트 문서, mkdocs 매뉴얼.

**Repo:** `/Users/jay-p/.claude/plugins/marketplaces/radiostart-plugins` — 브랜치 `fix/2026-08-03-audit-remediation` (base 1914428). 이하 상대 경로는 **`pilot/` 기준**.

## Global Constraints

- **문자열 계약 불변**: VERIFICATION REPORT 의 `status` 값(`READY`|`NOT_READY`)·`gates` **7개 키**(`requirements`·`tdd_evidence`·`capture_lockdown`·`test_run`·`scope`·`open_questions`·`drift`)와 enum·`metrics.domain_impact` 형식, preamble P-단계 번호, `messages.md` 키, `auto_pilot.py` 신호 파싱 형식(`### C\d+` 헤더·`severity:` 줄·`^## VERIFICATION REPORT$`), `.plan.critic.md` severity/category enum·`## 합의` 표 헤더, 이슈 모드 `issue.eval[.r{N}].md` 규약 — **한 글자도 바꾸지 않는다.**
- **테스트 실행**: 개별 `python3 tests/tools/test_<name>.py`, 전체 `python3 -m unittest discover -s tests/tools` (pilot/ 에서, pytest 미설치). 베이스라인 345 tests.
- **커밋 형식** (`skills/context/shared/commit.md`): `{scope}: {한국어 설명}` — 등록 scope 는 `feat`/`fix`/`refactor`/`skills` (`docs` 미등록 — 문서 커밋은 scope 없이 한국어 설명만). `chore(release):` 는 선례 유지. 요약 50자 이내. commit-format 훅은 advisory.
- **버전 3곳 동기**: `.claude-plugin/plugin.json` `version` · `mkdocs.yml:125` `extra.version` · `docs/index.md:11` highlights 블록.
- **실행하지 않는 것**: `release.sh` 태깅·PR 생성 (사용자 결정 대기). `workspace/context/pilot/*` 도메인 문서 직접 Edit 금지 (HANDOFF #22 — drift-protocol § A, `/pilot:learn` 재실행 영역).

## 범위 제외 (명시)

- 런타임 최적화(SSOT 트리오 직렬화·rgr.md 분할): 별도 스펙 감, 감사 판정 "과하지 않음".
- code-review REPORT 영속화: read-only 에이전트 유지.
- HANDOFF 백로그의 다른 항목(#22 재학습, placeholder leak, 영어 README 등): 이번 범위 밖.

---

### Task 1: protect-managed 훅 — eval REPORT 산출물 예외 (TDD)

`features/*.eval[.r{N}].md`(신설)와 `issues/*/issue.eval[.r{N}].md`(기존 이슈 규약)를 훅 예외에 추가한다. `.plan.critic.md`·`.auto.md` 는 **계속 차단**(Task 2 에서 문서를 Edit 기반으로 개정). 근거: eval REPORT 는 재평가마다 전체 재생성되는 기계 산출물(이력은 git 보존)이고, 이슈 모드는 동일-라운드 재평가 덮어쓰기가 현행 훅에 막히는 잠재 결함이 있다(실측 rc=2).

**Files:**
- Modify: `hooks/protect-managed.sh` (check_path 예외 블록 — 현행 42-46행의 focus 예외 아래), 헤더 주석 예외 목록
- Test: `tests/tools/test_protect_managed.py`

**Interfaces:**
- Produces: check_path 예외 2종 — `*/features/*.eval*.md`, `*/issues/*/issue.eval*.md` (Task 3 의 evaluator 저장 계약이 의존)

- [ ] **Step 1: 실패하는 테스트 추가**

`tests/tools/test_protect_managed.py` 끝(`if __name__` 위)에 새 클래스 추가. 기존 헬퍼(`_make_root`·`_run_hook`·`_write`·`_bash`)를 그대로 사용하고, 파일 픽스처는 각 테스트 안에서 자체 생성한다 (기존 `_make_root` 수정 없음). 추가 전에 `grep -n "eval" tests/tools/test_protect_managed.py` 로 기존 eval 관련 케이스와 충돌 없는지 확인:

```python
class EvalReportExceptions(unittest.TestCase):
    """evaluator REPORT 산출물(.eval[.rN].md) — 재평가 전체 재생성 허용."""

    def test_write_existing_feature_eval_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            p = root / "workspace" / "projects" / "P" / "features" / "01-a.eval.md"
            p.write_text("## VERIFICATION REPORT\n", encoding="utf-8")
            proc = _run_hook(root, _write(root, "workspace/projects/P/features/01-a.eval.md"))
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_bash_redirect_existing_feature_eval_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            p = root / "workspace" / "projects" / "P" / "features" / "01-a.eval.md"
            p.write_text("old\n", encoding="utf-8")
            proc = _run_hook(root, _bash("cat > workspace/projects/P/features/01-a.eval.md"))
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_write_existing_issue_eval_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            d = root / "workspace" / "issues" / "login-bug"
            d.mkdir(parents=True)
            (d / "issue.eval.md").write_text("old\n", encoding="utf-8")
            proc = _run_hook(root, _write(root, "workspace/issues/login-bug/issue.eval.md"))
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_write_existing_issue_eval_rn_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            d = root / "workspace" / "issues" / "login-bug"
            d.mkdir(parents=True)
            (d / "issue.eval.r2.md").write_text("old\n", encoding="utf-8")
            proc = _run_hook(root, _write(root, "workspace/issues/login-bug/issue.eval.r2.md"))
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_plan_critic_write_existing_still_blocked(self):
        """critic 은 기존 파일이면 Edit 사용 (Task 2 개정 계약) — 훅 차단 유지."""
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            p = root / "workspace" / "projects" / "P" / "features" / "01-a.plan.critic.md"
            p.write_text("# c\n", encoding="utf-8")
            proc = _run_hook(root, _write(root, "workspace/projects/P/features/01-a.plan.critic.md"))
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_auto_md_shell_append_still_blocked(self):
        """autopilot 로그 append 는 Edit 사용 (Task 2 개정 계약) — 훅 차단 유지."""
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            p = root / "workspace" / "projects" / "P" / "features" / "01-a.auto.md"
            p.write_text("## Run 1\n", encoding="utf-8")
            proc = _run_hook(root, _bash("echo done >> workspace/projects/P/features/01-a.auto.md"))
            self.assertEqual(proc.returncode, 2, proc.stderr)
```

주의: `_make_root` 가 만드는 픽스처 구조는 버전에 따라 다를 수 있다 — `workspace/projects/P/features/` 가 없으면 테스트 안에서 `mkdir(parents=True, exist_ok=True)` 로 보강한다.

- [ ] **Step 2: 실패 확인**

```bash
cd /Users/jay-p/.claude/plugins/marketplaces/radiostart-plugins/pilot
python3 tests/tools/test_protect_managed.py 2>&1 | tail -5
```

Expected: FAIL — eval 계열 4건 실패(rc 2 ≠ 0), still_blocked 2건 통과.

- [ ] **Step 3: 훅 예외 구현**

`hooks/protect-managed.sh` 의 focus 예외 블록(현행 44-46행) 바로 아래에 추가:

```bash
  # evaluator REPORT 산출물은 통과 — 재평가마다 전체 재생성 (agents/pilot-evaluator step 7,
  # 이슈 규약 issues/GUIDE.md). 이력은 git 이 보존. 접미 고정 매치 — `.evaluate.md` 류
  # 서브스트링 오매치 방지 (Task 1 리뷰 finding 반영).
  [[ "$rel_path" == */features/*.eval.md || "$rel_path" == */features/*.eval.r*.md ]] && return 0
  [[ "$rel_path" == */issues/*/issue.eval.md || "$rel_path" == */issues/*/issue.eval.r*.md ]] && return 0
```

헤더 주석의 예외 목록(현행 18행 부근 `.prompts.bak/` 줄 아래)에 한 줄 추가:

```bash
#   - features/*.eval[.rN].md · issues/*/issue.eval[.rN].md (evaluator REPORT — 재생성 산출물)
```

- [ ] **Step 4: 전체 테스트 통과 확인**

```bash
python3 tests/tools/test_protect_managed.py
```

Expected: `OK` — 신규 6건 + 기존 전 케이스 (기존 차단 케이스 판정 뒤집힘 없음).

- [ ] **Step 5: 커밋**

```bash
cd /Users/jay-p/.claude/plugins/marketplaces/radiostart-plugins
git add pilot/hooks/protect-managed.sh pilot/tests/tools/test_protect_managed.py
git commit -m "fix: protect-managed 에 eval REPORT 재생성 예외 추가"
```

---

### Task 2: 훅과 양립하는 문서 절차 개정 (critic·autopilot·focus)

**Files:**
- Modify: `agents/pilot-planner-critic.md:50` (Write→조건부 Edit), `:75` (0챌린지 규칙)
- Modify: `skills/autopilot/SKILL.md:74` (append 수단 명시)
- Modify: `skills/focus/SKILL.md:53` (모호 문구)

- [ ] **Step 1: critic step 5 개정**

`agents/pilot-planner-critic.md:50` 의 현재 문구:

```
5. **[출력]** `features/NN-{slug}.plan.critic.md` 를 다음 형식으로 Write (기존 파일 있으면 덮어쓴다 — 누적은 합의 표, 본문 챌린지는 최신 상태만). work_mode=issue 면 출력은 `issues/{이슈명}/issue.plan.critic[.r{N}].md` (r 은 대상 plan 과 동일):
```

를 다음으로 교체:

```
5. **[출력]** `features/NN-{slug}.plan.critic.md` 를 다음 형식으로 작성한다 — **신규면 Write, 기존 파일이 있으면 Edit** 로 `## 챌린지` 섹션 본문만 교체하고 헤더의 검토 시각을 갱신한다. `## 합의` 표는 보존한다 (기존 파일 Write 는 protect-managed 훅이 차단하며, 합의 이력은 잃지 않는다. 본문 챌린지는 최신 상태만 유지). **Edit 후 자기 점검**: 파일에 이번 라운드의 `### C` 항목·severity 줄만 남았는지 확인 — 이전 라운드 잔존 시 autopilot 신호 파서가 해소된 blocking 을 다시 읽는다. work_mode=issue 면 출력은 `issues/{이슈명}/issue.plan.critic[.r{N}].md` (r 은 대상 plan 과 동일):
```

같은 파일 `:75` 의 현재 문구:

```
   챌린지 0개면 `## 챌린지` 아래 "검출된 결함 없음. plan 통과." 한 줄만 적고 `## 합의` 표는 생략.
```

를 다음으로 교체 (0챌린지 재검토 ↔ "합의 표 보존" 충돌 해소):

```
   챌린지 0개면 `## 챌린지` 아래 "검출된 결함 없음. plan 통과." 한 줄만 적는다. `## 합의` 표는 신규 파일이면 생략, 기존 파일에 이미 표가 있으면 보존.
```

- [ ] **Step 2: autopilot 감사 로그 수단 명시**

`skills/autopilot/SKILL.md:74` 의 `` `{AUTO_LOG}` 에 매 전이마다 한 줄 append(단계 종료 즉시 — 중단돼도 흔적이 남도록). `` 를 다음으로 교체 (뒤 문장 유지):

```
`{AUTO_LOG}` 에 매 전이마다 한 줄 append(단계 종료 즉시 — 중단돼도 흔적이 남도록). **append 는 Edit 도구로 수행** — 셸 `>>` 와 기존 파일 Write 는 protect-managed 훅이 차단한다(신규 `{AUTO_LOG}` 생성만 Write).
```

- [ ] **Step 3: focus 모호 문구 정정**

`skills/focus/SKILL.md:53` 의 `있으면 \`.focus.history/{timestamp}.md\` 로 이동 후 삭제` 를 `있으면 \`.focus.history/{timestamp}.md\` 로 이동(mv — 이동이 곧 제거, 별도 rm 불필요)` 로 교체.

- [ ] **Step 4: 매뉴얼 동기화 확인 + 링크 테스트 + 커밋**

```bash
cd /Users/jay-p/.claude/plugins/marketplaces/radiostart-plugins/pilot
grep -rn "덮어쓴다\|이동 후 삭제" docs/how-to/ docs/explanation/ | grep -i "critic\|focus\|auto" || echo "no-manual-drift"
python3 tests/tools/test_doc_links.py
cd /Users/jay-p/.claude/plugins/marketplaces/radiostart-plugins
git add pilot/agents/pilot-planner-critic.md pilot/skills/autopilot/SKILL.md pilot/skills/focus/SKILL.md
git commit -m "critic·autopilot·focus 갱신 절차를 훅과 양립하게 개정"
```

매뉴얼 grep 에 출력이 있으면 각 위치를 동일 의미로 정정 후 `git add` 에 포함.

---

### Task 3: 프로젝트 모드 REPORT 영속화 — `features/NN-{slug}.eval.md`

이슈 모드의 기존 `issue.eval.md` 규약(agents/pilot-evaluator.md:27)을 프로젝트 모드로 대칭 확장. guardrails "SSOT 는 파일" 원칙과의 모순 + autopilot `{REPORT_PATH}` 미명세 해소.

**Files:**
- Modify: `agents/pilot-evaluator.md:49` (step 7 도입부에 저장 지시)
- Modify: `skills/autopilot/SKILL.md` (`### 4. evaluator` 절 첫 줄 + `:27` `{FEAT}` 제외 목록)
- Modify: `docs/explanation/workspace-layout.md` (`:37` 다이어그램 라벨, `:91` 영구 파일 표)
- Modify: `skills/context/shared/guardrails.md` (`:57` § SSOT — 기록은 Edit 으로, 예외 1줄)

**Interfaces:**
- Consumes: Task 1 의 `*/features/*.eval*.md` 훅 예외
- Produces: `workspace/projects/{PROJECT}/features/{NN}-{slug}.eval.md` — 최신 REPORT 1개만 담는 tracked 파일. `auto_pilot.py --report-file` 이 `^## VERIFICATION REPORT$` 블록을 그대로 파싱 (단일 블록 보장)

- [ ] **Step 1: evaluator step 7 저장 지시**

`agents/pilot-evaluator.md:49` 의 현재 문구:

```
7. **[필수] VERIFICATION REPORT 출력** — 메시지 끝에 아래 블록을 그대로 붙인다. 체크박스(step 4)는 상세 기록, REPORT 는 요약이며 `status: READY` 는 전 gate pass + project.md `[x]` 완료와 동치.
```

를 다음으로 교체 (이후 REPORT 블록·자기 점검 문단 무변경):

```
7. **[필수] VERIFICATION REPORT 출력 + 저장** — 메시지 끝에 아래 블록을 그대로 붙이고, 동일 블록을 `workspace/projects/{PROJECT}/features/{NN}-{slug}.eval.md` 에 저장한다 (재평가 시 전체 재생성 — 최신 상태만 유지, 이력은 git 이 보존. work_mode=issue 의 저장 경로는 위 issue 모드 절의 규약을 따른다). 체크박스(step 4)는 상세 기록, REPORT 는 요약이며 `status: READY` 는 전 gate pass + project.md `[x]` 완료와 동치.
```

- [ ] **Step 2: autopilot `{REPORT_PATH}` 확정 + `{FEAT}` 제외**

`skills/autopilot/SKILL.md` 의 `### 4. evaluator` 절 첫 줄 (백틱 포함 원문):

```
`@pilot-evaluator` 호출 → VERIFICATION REPORT 를 파일로 저장 후:
```

를 다음으로 교체:

```
`@pilot-evaluator` 호출 — evaluator 가 REPORT 를 `features/{NN}-{slug}.eval.md` 로 저장한다(에이전트 계약 step 7). `{REPORT_PATH}` = 그 경로:
```

같은 파일 `:27` 의 `{FEAT}` 제외 목록 `` (`.plan.md`·`.plan.critic.md`·`.auto.md` 제외) `` 를 `` (`.plan.md`·`.plan.critic.md`·`.auto.md`·`.eval.md` 제외) `` 로 교체 — 신설 파일이 feature 글롭에 오인 매치되면 재개 플로우의 slug 도출이 깨진다.

- [ ] **Step 3: workspace-layout 갱신**

`docs/explanation/workspace-layout.md:37` 다이어그램 라벨 `(NN-*.md · NN-*.plan.md · NN-*.plan.critic.md)` → `(NN-*.md · NN-*.plan.md · NN-*.plan.critic.md · NN-*.eval.md)`.

`:91` 행 `| \`features/NN-*.plan.md\` · \`.plan.critic.md\` | 영구 파일 (작업 이력 기록) | tracked |` 아래에 새 행 추가:

```markdown
| `features/NN-*.eval.md` | 영구 파일 (evaluator 최종 REPORT — 재평가 시 최신으로 교체) | tracked |
```

- [ ] **Step 4: guardrails 예외 1줄**

`skills/context/shared/guardrails.md:57` 문장 끝에 추가:

```markdown
예외: evaluator REPORT 산출물(`features/NN-*.eval.md` · `issues/*/issue.eval[.r{N}].md`)은 재평가마다 전체 재생성 — Write/Bash 재작성이 정본이며 이력은 git 이 보존한다.
```

- [ ] **Step 5: 정합 확인 + 커밋**

```bash
cd /Users/jay-p/.claude/plugins/marketplaces/radiostart-plugins/pilot
grep -rln "eval.md" agents/pilot-evaluator.md skills/autopilot/SKILL.md skills/context/shared/guardrails.md docs/explanation/workspace-layout.md
python3 tests/tools/test_doc_links.py && python3 tests/tools/test_auto_pilot.py
cd /Users/jay-p/.claude/plugins/marketplaces/radiostart-plugins
git add pilot/agents/pilot-evaluator.md pilot/skills/autopilot/SKILL.md pilot/docs/explanation/workspace-layout.md pilot/skills/context/shared/guardrails.md
git commit -m "feat: 프로젝트 모드 evaluator REPORT 를 features/NN-*.eval.md 로 영속화"
```

Expected: grep 4파일 전부 매치, 테스트 2건 `OK`.

---

### Task 4: 컨벤션 검증 축 이중화 — 층위 관계 선언

**Files:**
- Modify: `skills/context/shared/coding.md` (§ 검증 Merge 규칙 문단 뒤)
- Modify: `skills/context/shared/review-rules-template.md` (`- 없는 언어 → baseline 만 적용.` 아래)
- Modify: `skills/code-review-init/SKILL.md` (§ 사전 확인 3번 아래 4번 신설)
- Modify: `agents/pilot-evaluator.md:35` (gate 반영 경계)

- [ ] **Step 1: coding.md 층위 선언**

§ 검증 의 `**Merge 규칙:** ...` 문단 뒤에 추가:

```markdown
**리뷰 룰과의 층위 분리:** `conventions_doc`/`conventions_evals` 는 **구현·기계 검증 축**(Generator 자기 검사·Evaluator 독립 검증)이고, `workspace/context/review/{lang}.md` 는 **리뷰 룰 축**(`pilot-code-review` 전용, 사람 판단 기준)이다. 같은 언어 지식이라도 소비 주체가 다르다 — 조항이 겹치면 리뷰 룰 쪽에서 conventions 문서를 참조로 대체한다 (이중 유지 금지).
```

- [ ] **Step 2: review-rules-template 헤더 안내**

`- 없는 언어 → baseline 만 적용.` 줄 아래에 추가:

```markdown
- `config.md` 의 `conventions_doc` 가 이미 다루는 조항(명명·관용구·금지 패턴)은 여기 중복 기재하지 말고 해당 문서를 참조로 링크한다 — 층위 정의: `coding.md` § 검증.
```

- [ ] **Step 3: code-review-init § 사전 확인 4번 신설**

`3. 대상 경로 ... 질의.` 항목 바로 아래에 추가:

```markdown
4. `workspace/context/config.md` 의 `conventions_doc` 선언 여부를 확인한다 — 선언되어 있으면 그 문서가 이미 다루는 조항(명명·관용구·금지 패턴)은 룰 파일에 중복 기재하지 말고 참조로 대체하도록 안내한다 (층위 정의: [`coding.md`](../context/shared/coding.md) § 검증).
```

- [ ] **Step 4: evaluator gate 반영 경계**

`agents/pilot-evaluator.md:35` 끝의 `위반은 \`issues_to_fix\` 에 기록하고 \`requirements\` gate 판정 근거에 반영한다.` 를 다음으로 교체:

```
위반은 `issues_to_fix` 에 기록한다. **gate 반영 경계**: `conventions_evals` 의 기계 검증 케이스 위반만 `requirements` gate 판정 근거에 반영하고, `conventions_doc` 의 스타일·관용구 위반은 `issues_to_fix` 참고 항목으로만 남긴다 (gate 오염 방지 — 층위: [`coding.md`](${CLAUDE_PLUGIN_ROOT}/skills/context/shared/coding.md) § 검증).
```

- [ ] **Step 5: 검증 + 커밋**

```bash
cd /Users/jay-p/.claude/plugins/marketplaces/radiostart-plugins/pilot
python3 tests/tools/test_doc_links.py
cd /Users/jay-p/.claude/plugins/marketplaces/radiostart-plugins
git add pilot/skills/context/shared/coding.md pilot/skills/context/shared/review-rules-template.md pilot/skills/code-review-init/SKILL.md pilot/agents/pilot-evaluator.md
git commit -m "컨벤션 검증 축 층위 분리 선언 — conventions vs review 룰"
```

---

### Task 5: 위생 일괄 — Slack pr 기본값 · 사장 인용 · GUIDE B-2 · self-verify

**Files:**
- Modify: `skills/slack/SKILL.md:36`, `docs/how-to/slack-notify.md` (기본값 경고 절), repo 루트 `HANDOFF.md` (백로그 항목)
- Modify: `agents/pilot-evaluator.md:78`, `skills/pilot-doctor/SKILL.md:18,70` (인용 제거)
- Modify: `tools/auto_pilot.py:17,87`, `tools/doctor.py:13`, `tools/orchestrate-load.py:56`, `tests/fixtures/v0.1.0-baseline/README.md:8,15` ("repo 루트 " 접두)
- Modify: `skills/context/lifecycle/projects/GUIDE.md:225`, `skills/analyze/references/self-verify.md:19,30`

- [ ] **Step 1: Slack 활성화 기본 이벤트에 pr 포함** (사용자 확정 사항)

`skills/slack/SKILL.md:36` 의 `이벤트(기본 \`complete,approval\`, 쉼표 구분)` → `이벤트(기본 \`complete,approval,pr\`, 쉼표 구분)`.

`docs/how-to/slack-notify.md` 에서 "기본값에 pr 미포함" 취지의 경고·안내를 grep(`grep -n "pr" docs/how-to/slack-notify.md`)으로 찾아 새 기본값과 정합하게 정정. `grep -n "default 포함\|기본" skills/pr/SKILL.md` 로 pr 스킬 서술도 정합 확인(불일치 시 정정).

repo 루트 `HANDOFF.md` 백로그의 "Slack `pr` 이벤트가 기본값에서 누락" 항목을 삭제하고, 그 자리에 한 줄: `- ~~Slack pr 기본값~~ — 해소 (2026-08-03, 기본값 complete,approval,pr 로 통일 — 사용자 제품 판단).`

- [ ] **Step 2: 사장된 감사 인용 정리**

모델 로드 문서 3곳 — 인용 경로 제거, 짧은 사유 유지:
- `agents/pilot-evaluator.md:78`: `(구 \`verify-report-lint.py\` 스키마 검증 이관, 근거: \`docs/audits/2026-07-24-audit-4-python.md\` § C-5)` → `(구 \`verify-report-lint.py\` 스키마 검증 이관)`
- `skills/pilot-doctor/SKILL.md:18`: `(모델이 더 잘 판단하는 휴리스틱 패턴 매칭 — 근거: \`docs/audits/2026-07-24-audit-4-python.md\` § C-6)` → `(모델이 더 잘 판단하는 휴리스틱 패턴 매칭)`
- `skills/pilot-doctor/SKILL.md:70`: `(v0.9.0+ 구조 정합성 검사로 축소 — 근거: \`docs/audits/2026-07-24-audit-4-python.md\` § B)` → `(v0.9.0+ 구조 정합성 검사로 축소)`

사람만 읽는 파일 — `docs/audits/...`·`docs/superpowers/...` 경로 앞에 "repo 루트 " 표기 추가 (경로는 배포 `pilot/` 밖, repo 루트에 실존):
- `tools/auto_pilot.py:17` (스펙 인용), `tools/auto_pilot.py:87`, `tools/doctor.py:13`, `tools/orchestrate-load.py:56`, `tests/fixtures/v0.1.0-baseline/README.md:8,15`

- [ ] **Step 3: GUIDE.md B-2 잔여 정정**

`skills/context/lifecycle/projects/GUIDE.md:225` 의:

```markdown
> **TDD 모드**일 때: `/pilot:tdd` 가 파일 최상단에 경고 앵커를 추가한다 — Planner 실패 테스트를 통과시키는 방향으로 구현.
```

를 다음으로 교체 (정본 `tdd-activation.md` § 3 "Red 작성·실패 확인 → Green (최소 구현) → Refactor 를 한 컨텍스트에서 순환" 과 의미 일치 — Refactor 누락 금지):

```markdown
> **TDD 모드**일 때: `/pilot:tdd` 가 파일 최상단에 경고 앵커를 추가한다 — Red(실패 테스트 작성·실패 확인) → Green(최소 구현) → Refactor 를 순환. 앵커 문구 정본: [`tdd-activation.md`](../../modes/tdd-activation.md) § 3.
```

- [ ] **Step 4: self-verify 파생 산출물 제외 확장**

`skills/analyze/references/self-verify.md:19` 의 `` 각 features/*.md (`.plan.md` 제외) 에 아래 섹션이 존재해야 한다: `` 와 `:30` 의 `` `features/*.md` 개수 (`.plan.md` 제외) `` 에서 제외 목록을 `` (`.plan.md`·`.plan.critic.md`·`.auto.md`·`.eval.md` 제외) `` 로 확장 (2곳).

- [ ] **Step 5: 검증 + 커밋**

```bash
cd /Users/jay-p/.claude/plugins/marketplaces/radiostart-plugins/pilot
grep -rn "docs/audits/2026\|docs/superpowers/specs" agents/ skills/ tools/ tests/fixtures/ | grep -v "repo 루트"; echo "grep-exit=$?"
python3 tests/tools/test_doc_links.py && python3 tests/tools/test_slack_notify.py && python3 tests/tools/test_doctor_slack.py && python3 tests/tools/test_auto_pilot.py
cd /Users/jay-p/.claude/plugins/marketplaces/radiostart-plugins
git add pilot/ HANDOFF.md
git commit -m "fix: Slack pr 기본값 통일·사장 인용 정리·GUIDE B-2·self-verify 제외 확장"
```

Expected: 첫 grep 매치 0건(`grep-exit=1`), 테스트 4건 `OK`. (`git add pilot/` 는 이 시점의 변경이 본 Task 것뿐임을 `git status` 로 먼저 확인.)

---

### Task 6: 스킬 description 감량 — 상시 토큰 절감

상위 7종(learn 816B·autopilot 780B·create-feature 487B·issue 446B·project 420B·pilot-doctor 419B·analyze 409B, 합계 3,777B)을 「기능 1~2문장 + 인접 스킬 라우팅 구분」으로 축소. 라우팅 구분 문구와 autopilot 의 **자발 발동 금지 게이트 조항은 유지** (트리거 계약). 에이전트 5개는 적정 — 무변경.

**Files:**
- Modify: 7개 `skills/{learn,autopilot,create-feature,issue,project,pilot-doctor,analyze}/SKILL.md` frontmatter description 만 (name·본문 무변경)

- [ ] **Step 1: 7개 description 교체**

`skills/learn/SKILL.md`:
```yaml
description: >-
  기존 소스 코드의 진입점(컨트롤러·서비스 파일 또는 폴더)을 받아 의존성을
  따라 읽고 `workspace/context/` 도메인 문서를 부트스트랩한다 — 추측 금지,
  file:line 인용만. `--boundary B --from A` 는 A 가 호출하는 표면만
  `boundaries/{A}--{B}.md` 로 포착한다. docs/ 기획서 가공은 `/pilot:analyze`.
```

`skills/autopilot/SKILL.md`:
```yaml
description: >-
  사용자가 자동 진행을 명시 요청했을 때만 사용한다 — "계속 진행해줘" 류
  발화만으로 자발 발동하지 않는다. 이미 생성된 단일 feature 를
  planner→critic→generator→evaluator 로 자동 순차 진행하는 감독형 자율
  모드로, hard-stop 신호에 걸리면 즉시 사람에게 제어를 반환한다. feature
  생성·명세는 `/pilot:create-feature`·`/pilot:analyze` 담당.
```

`skills/create-feature/SKILL.md`:
```yaml
description: >-
  활성 프로젝트에 프롬프트 한 줄로 단일 feature 명세(features/NN-{slug}.md)를
  추가하고 project.md·prompts/* 를 동기화한다. 기획서(docs/) 기반 다건 분할은
  `/pilot:analyze`. 실행은 @pilot-planner 호출로 시작 — 자동 파이프라인 아님.
```

`skills/issue/SKILL.md`:
```yaml
description: >-
  운영 이슈 처리 모드 — `workspace/issues/{이슈명}/` 를 생성·로드해 버그
  대응·장애 분석·핫픽스 등 단발성 문제 1건을 해결한다. 필요 시 project 와
  동일한 4-에이전트 사이클을 issue 단위로 사용. 지속 기능 개발은 `/pilot:project`.
```

`skills/project/SKILL.md`:
```yaml
description: >-
  새 프로젝트를 시작하거나 기존 프로젝트를 재개한다. 프로젝트 폴더 생성·로드,
  STATE.md 갱신, 도메인 컨텍스트 적재. Confluence URL 인자는 confl·analyze
  위임, `--tdd` 는 TDD 모드. 단발 이슈는 `/pilot:issue`.
```

`skills/pilot-doctor/SKILL.md`:
```yaml
description: >-
  pilot 워크스페이스·프로젝트의 정합성을 검사한다. 상태 이상·드리프트·부분
  설정이 의심될 때, 또는 정기 점검·진단을 원할 때 사용한다. STATE corrupt
  같은 조용한 문제를 조기 감지한다.
```

`skills/analyze/SKILL.md`:
```yaml
description: >-
  저장된 docs/ 기획서를 features/ 기능 명세로 분할·구조화하고 project.md
  목표·prompts/*(planner·generator·evaluator)를 자동 갱신한다. 기획서 fetch 는
  `/pilot:confl`, 프롬프트 기반 단일 기능 추가는 `/pilot:create-feature`.
```

- [ ] **Step 2: 절감 실측**

```bash
cd /Users/jay-p/.claude/plugins/marketplaces/radiostart-plugins/pilot
for s in learn autopilot create-feature issue project pilot-doctor analyze; do
  printf "%s: " "$s"
  python3 -c "
import re
t=open('skills/$s/SKILL.md',encoding='utf-8').read()
m=re.search(r'description: >-\n((?:  .*\n)+)',t)
print(len(m.group(1).encode()) if m else 'PARSE-FAIL')"
done
```

Expected: 합계가 기존 3,777B 대비 **1,500B 이상 감소**, PARSE-FAIL 0건 (있으면 YAML 2칸 들여쓰기 복구).

- [ ] **Step 3: 커밋**

```bash
cd /Users/jay-p/.claude/plugins/marketplaces/radiostart-plugins
git add pilot/skills/*/SKILL.md
git commit -m "refactor: 스킬 description 7종 감량 — 상시 프롬프트 비용 절감"
```

---

### Task 7: 전체 검증 + 버전 동기 (0.14.0 → 0.15.0)

**Files:**
- Modify: `.claude-plugin/plugin.json`, `mkdocs.yml:125`, `docs/index.md:11`

- [ ] **Step 1: 전체 테스트**

```bash
cd /Users/jay-p/.claude/plugins/marketplaces/radiostart-plugins/pilot
python3 -m unittest discover -s tests/tools -v 2>&1 | tail -3
```

Expected: `OK` — 베이스라인 345 + Task 1 신규 6 = **351 tests**.

- [ ] **Step 2: 버전 3곳 동기**

- `.claude-plugin/plugin.json`: `"version": "0.14.0"` → `"0.15.0"`
- `mkdocs.yml:125`: `version: "0.14.0"` → `version: "0.15.0"` (뒤 주석 유지)
- `docs/index.md:11`: 기존 `!!! tip "v0.14.0 highlights"` 블록 **위에** 동일 형식으로 `!!! tip "v0.15.0 highlights"` 블록 신설 — 내용 4줄: 프로젝트 모드 evaluator REPORT 영속화(`features/NN-*.eval.md`) + 훅 재생성 예외, critic·autopilot 갱신 절차 훅 정합(Edit 기반), Slack 기본 이벤트에 `pr` 포함, 스킬 description 7종 감량.

- [ ] **Step 3: 최종 확인 + 커밋**

```bash
cd /Users/jay-p/.claude/plugins/marketplaces/radiostart-plugins/pilot
grep -rn "0.15.0" .claude-plugin/plugin.json mkdocs.yml docs/index.md
python3 tests/tools/test_docs_build.py
cd /Users/jay-p/.claude/plugins/marketplaces/radiostart-plugins
git add pilot/.claude-plugin/plugin.json pilot/mkdocs.yml pilot/docs/index.md
git commit -m "chore(release): v0.15.0 버전 표기 동기화"
git log --oneline main..HEAD
```

Expected: 3파일 매치, docs build `OK`, 커밋 7개. 이후 PR·`release.sh` 는 사용자 결정 대기.
