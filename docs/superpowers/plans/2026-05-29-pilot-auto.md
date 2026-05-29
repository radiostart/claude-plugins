# `/pilot:auto` 감독형 자율 오케스트레이터 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** feature 명세가 이미 존재하는 상태에서 planner→critic→generator→evaluator 를 자동 순차 진행하되, hard-stop 신호에 걸리면 즉시 사람에게 제어를 반환하는 감독형 자율 모드를 pilot 플러그인에 추가한다.

**Architecture:** 두 부분으로 나뉜다. (1) `tools/auto_pilot.py` — 각 에이전트 산출 신호(plan-validate exit code, `.plan.critic.md` severity, evaluator REPORT status)를 읽어 다음 액션(`proceed|reflect|retry|done|stop`)을 결정하는 **순수 함수** + 신호 파서. 실제 에이전트 호출은 하지 않는다. (2) `skills/auto/SKILL.md` — 그 결정 함수를 호출하며 기존 4개 에이전트를 순차 호출하고 `NN.auto.md` 감사 로그를 남기는 얇은 오케스트레이터 스킬. 에이전트 내부와 기존 도구는 변경하지 않는다.

**Tech Stack:** Python 3 (stdlib only — `argparse`, `json`, `re`, `pathlib`), `unittest`. 기존 `tools/verify-report-lint.py` 의 REPORT 파서를 재사용한다. 스킬은 Claude Code 슬래시 커맨드 마크다운.

설계 출처: `docs/superpowers/specs/2026-05-29-pilot-auto-design.md`

---

## File Structure

신규 파일:
- `pilot/tools/auto_pilot.py` — 신호 파서 + 전이 결정 순수 함수 + CLI. 하나의 책임: "신호 → 다음 액션".
- `pilot/tests/tools/test_auto_pilot.py` — 전이 결정·파서 단위 테스트.
- `pilot/skills/auto/SKILL.md` — `/pilot:auto` 오케스트레이터 스킬.

수정 파일:
- `pilot/.claude-plugin/plugin.json` — description 에 auto 모드 언급 (선택, Task 7).
- `pilot/agents/pilot-planner.md` 또는 README — "수동이 기본, auto 는 opt-in 예외" 문서화 (Task 7).

**핵심 경계:** `auto_pilot.py` 는 도메인 판단을 절대 하지 않는다. "이 챌린지가 타당한가"는 critic/planner 가, "요구사항 충족했나"는 evaluator 가 판단한다. `auto_pilot.py` 는 그들이 내놓은 신호의 enum 값만 읽고 전이한다. 모든 전이 결정이 이 한 파일의 순수 함수에 모이므로 에이전트 호출 없이 전수 테스트가 가능하다.

---

## Task 1: 전이 결정 핵심 함수 — `decide_next`

신호 dict 를 받아 다음 액션을 반환하는 순수 함수를 TDD 로 만든다. 이것이 오케스트레이터의 두뇌다.

**Files:**
- Create: `pilot/tools/auto_pilot.py`
- Test: `pilot/tests/tools/test_auto_pilot.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`pilot/tests/tools/test_auto_pilot.py` 생성:

```python
"""
tools/auto_pilot.py 단위 테스트.

실행:
    python3 tests/tools/test_auto_pilot.py
"""

import importlib.util
import unittest
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "auto_pilot.py"


def _load_mod():
    spec = importlib.util.spec_from_file_location("auto_pilot_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = _load_mod()


class TestDecideNext(unittest.TestCase):
    def test_plan_validate_fail_stops(self):
        action = m.decide_next("planner", {"plan_valid": False})
        self.assertEqual(action.kind, "stop")
        self.assertEqual(action.reason, "plan-validate")

    def test_plan_validate_pass_proceeds(self):
        action = m.decide_next("planner", {"plan_valid": True})
        self.assertEqual(action.kind, "proceed")

    def test_critic_blocking_stops(self):
        action = m.decide_next("critic", {"severities": ["suggestion", "blocking"]})
        self.assertEqual(action.kind, "stop")
        self.assertEqual(action.reason, "critic-blocking")

    def test_critic_suggestion_nit_only_reflects(self):
        action = m.decide_next("critic", {"severities": ["suggestion", "nit"]})
        self.assertEqual(action.kind, "reflect")

    def test_critic_empty_proceeds(self):
        action = m.decide_next("critic", {"severities": []})
        self.assertEqual(action.kind, "proceed")

    def test_critic_unparseable_stops(self):
        action = m.decide_next("critic", {"severities": None})
        self.assertEqual(action.kind, "stop")
        self.assertEqual(action.reason, "signal-parse")

    def test_evaluator_ready_done(self):
        action = m.decide_next("evaluator", {"status": "READY", "retries_used": 0})
        self.assertEqual(action.kind, "done")

    def test_evaluator_not_ready_first_retries(self):
        action = m.decide_next("evaluator", {"status": "NOT_READY", "retries_used": 0})
        self.assertEqual(action.kind, "retry")

    def test_evaluator_not_ready_exhausted_stops(self):
        action = m.decide_next("evaluator", {"status": "NOT_READY", "retries_used": 1})
        self.assertEqual(action.kind, "stop")
        self.assertEqual(action.reason, "retry-exhausted")

    def test_evaluator_unparseable_stops(self):
        action = m.decide_next("evaluator", {"status": None, "retries_used": 0})
        self.assertEqual(action.kind, "stop")
        self.assertEqual(action.reason, "signal-parse")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd pilot && python3 tests/tools/test_auto_pilot.py`
Expected: FAIL — `auto_pilot.py` 가 없어 `spec.loader.exec_module` 에서 `FileNotFoundError`

- [ ] **Step 3: 최소 구현 작성**

`pilot/tools/auto_pilot.py` 생성:

```python
#!/usr/bin/env python3
"""
pilot auto_pilot — 감독형 자율 오케스트레이터의 전이 결정 로직.

`/pilot:auto` 스킬이 각 에이전트(planner / critic / generator / evaluator)를
순차 호출하는 사이, 각 에이전트가 남긴 머신리더블 신호를 읽어 다음 액션을
결정한다. 이 모듈은 *판단하지 않는다* — 신호의 enum 값만 보고 전이한다.

신호 출처:
  - planner   : plan-validate.py exit code → plan_valid (bool)
  - critic    : .plan.critic.md 의 챌린지 severity 목록 → severities (list|None)
  - evaluator : VERIFICATION REPORT 의 status → status ("READY"|"NOT_READY"|None)

액션 종류:
  proceed | reflect | retry | done | stop

스펙: docs/superpowers/specs/2026-05-29-pilot-auto-design.md
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

MAX_RETRIES = 1  # NOT_READY 시 generator 재진입 횟수 상한


@dataclass
class Action:
    kind: str            # proceed | reflect | retry | done | stop
    reason: str = ""     # stop 일 때 사유 (plan-validate | critic-blocking | retry-exhausted | signal-parse | agent-error)


def decide_next(phase: str, signal: dict) -> Action:
    """phase 의 산출 신호를 받아 다음 액션을 결정한다 (순수 함수)."""
    if phase == "planner":
        if signal.get("plan_valid") is True:
            return Action("proceed")
        return Action("stop", "plan-validate")

    if phase == "critic":
        severities = signal.get("severities")
        if severities is None:
            return Action("stop", "signal-parse")
        if "blocking" in severities:
            return Action("stop", "critic-blocking")
        if len(severities) == 0:
            return Action("proceed")
        return Action("reflect")

    if phase == "evaluator":
        status = signal.get("status")
        if status == "READY":
            return Action("done")
        if status == "NOT_READY":
            if signal.get("retries_used", 0) < MAX_RETRIES:
                return Action("retry")
            return Action("stop", "retry-exhausted")
        return Action("stop", "signal-parse")

    return Action("stop", "signal-parse")
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd pilot && python3 tests/tools/test_auto_pilot.py`
Expected: PASS — `Ran 10 tests ... OK`

- [ ] **Step 5: 커밋**

```bash
cd pilot && git add tools/auto_pilot.py tests/tools/test_auto_pilot.py
git commit -m "feat(pilot): auto_pilot decide_next 전이 결정 함수 추가"
```

---

## Task 2: critic severity 파서 — `parse_critic_severities`

`.plan.critic.md` 에서 챌린지 severity 목록을 추출한다. 실제 critic 출력 형식(`agents/pilot-planner-critic.md` step 5 기준)은 각 챌린지가 `### C1 — {제목}` 헤더 + `- **severity**: blocking` 형태이며, **챌린지가 0개면** `## 챌린지` 아래에 `"검출된 결함 없음. plan 통과."` 한 줄만 적고 `## 합의` 표는 생략한다. 파싱 실패(형식 깨짐)는 `None` 을 반환해 상위에서 hard-stop 시킨다.

**Files:**
- Modify: `pilot/tools/auto_pilot.py`
- Test: `pilot/tests/tools/test_auto_pilot.py`

- [ ] **Step 1: 실패하는 테스트 추가**

`test_auto_pilot.py` 에 클래스 추가:

```python
CRITIC_WITH_BLOCKING = """# Plan Critic — #3 사용자 삭제

> 입력 plan: `features/03-user-deletion.plan.md`

## 챌린지

### C1 — soft-delete 누락

- **severity**: blocking
- **category**: risk
- **plan 인용**: 단계 #2
- **챌린지**: soft-delete 누락
- **제안**: archived_at 추가

### C2 — 과한 단계

- **severity**: suggestion
- **category**: scope
- **plan 인용**: 단계 #4
- **챌린지**: 과한 단계
- **제안**: 병합
"""

CRITIC_SUGGESTION_NIT = """# Plan Critic — #3 사용자 삭제

## 챌린지

### C1 — 대안 제안

- **severity**: suggestion
- **category**: alternative

### C2 — 사소한 정확성

- **severity**: nit
- **category**: scope
"""

CRITIC_NO_CHALLENGES = """# Plan Critic — #3 사용자 삭제

> 입력 plan: `features/03-user-deletion.plan.md`

## 챌린지

검출된 결함 없음. plan 통과.
"""

CRITIC_MALFORMED = """# 잘못된 파일

제목만 있고 챌린지 섹션도 severity 라벨도 통과 문구도 없는 내용.
"""


class TestParseCriticSeverities(unittest.TestCase):
    def test_extracts_blocking_and_suggestion(self):
        result = m.parse_critic_severities(CRITIC_WITH_BLOCKING)
        self.assertEqual(sorted(result), ["blocking", "suggestion"])

    def test_suggestion_nit_only(self):
        result = m.parse_critic_severities(CRITIC_SUGGESTION_NIT)
        self.assertEqual(sorted(result), ["nit", "suggestion"])

    def test_no_challenges_returns_empty_list(self):
        result = m.parse_critic_severities(CRITIC_NO_CHALLENGES)
        self.assertEqual(result, [])

    def test_malformed_returns_none(self):
        result = m.parse_critic_severities(CRITIC_MALFORMED)
        self.assertIsNone(result)
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd pilot && python3 tests/tools/test_auto_pilot.py`
Expected: FAIL — `AttributeError: module ... has no attribute 'parse_critic_severities'`

- [ ] **Step 3: 최소 구현 작성**

`auto_pilot.py` 의 `import` 아래에 `re` 추가하고, `decide_next` 위에 함수 추가:

```python
import re

_SEVERITY_LINE_RE = re.compile(
    r"^\s*[-*]?\s*\*{0,2}severity\*{0,2}\s*:\s*([a-zA-Z_]+)", re.MULTILINE
)
_CHALLENGE_HEADER_RE = re.compile(r"^###\s+C\d+", re.MULTILINE)
# critic 의 명시적 "결함 없음" 통과 문구 (agents/pilot-planner-critic.md step 5).
# 0건일 때 critic 은 `## 챌린지` 아래에 이 문구 한 줄만 남긴다.
_PASS_MARKER_RE = re.compile(r"검출된 결함 없음|plan 통과")

VALID_SEVERITIES = {"blocking", "suggestion", "nit"}


def parse_critic_severities(text: str):
    """`.plan.critic.md` 본문에서 severity 목록을 추출한다.

    Returns:
        list[str]  — 정상 파싱 (0건이면 빈 리스트)
        None       — 형식이 깨져 신뢰할 수 없음 (상위에서 hard-stop)
    """
    headers = _CHALLENGE_HEADER_RE.findall(text)
    sev_matches = _SEVERITY_LINE_RE.findall(text)

    # 명시적 "결함 없음" 통과 문구가 있고 챌린지 헤더가 없으면 0건으로 인정.
    if _PASS_MARKER_RE.search(text) and not headers:
        return []

    # 챌린지 헤더도 severity 라벨도 통과 문구도 없으면 형식 미상 → None
    if not headers and not sev_matches:
        return None

    severities = [s.lower() for s in sev_matches if s.lower() in VALID_SEVERITIES]

    # 챌린지 헤더가 있는데 유효 severity 를 하나도 못 읽었으면 형식 깨짐 → None
    if headers and not severities:
        return None

    return severities
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd pilot && python3 tests/tools/test_auto_pilot.py`
Expected: PASS — `Ran 14 tests ... OK`

- [ ] **Step 5: 커밋**

```bash
cd pilot && git add tools/auto_pilot.py tests/tools/test_auto_pilot.py
git commit -m "feat(pilot): auto_pilot critic severity 파서 추가"
```

---

## Task 3: evaluator status 파서 재사용 래퍼 — `parse_evaluator_status`

evaluator REPORT 파싱은 기존 `verify-report-lint.py` 에 검증된 `extract_report_block` + `parse_report` 가 있다. 이를 동적 로드해 `status` 만 뽑는 얇은 래퍼를 만든다. 중복 구현하지 않는다 (DRY).

**Files:**
- Modify: `pilot/tools/auto_pilot.py`
- Test: `pilot/tests/tools/test_auto_pilot.py`

- [ ] **Step 1: 실패하는 테스트 추가**

`test_auto_pilot.py` 에 추가:

```python
EVAL_READY = """## VERIFICATION REPORT

- status: READY
- feature: #3 사용자 삭제
- mode: standard
- gates:
  - requirements: pass
  - tdd_evidence: skip
  - capture_lockdown: skip
  - test_run: skip
  - scope: pass
  - drift: none
- metrics:
  - files_changed: 4
- issues_to_fix:
  - none
- next: PR 준비
"""

EVAL_NOT_READY = """## VERIFICATION REPORT

- status: NOT_READY
- feature: #3 사용자 삭제
- mode: standard
- gates:
  - requirements: fail
  - tdd_evidence: skip
  - capture_lockdown: skip
  - test_run: skip
  - scope: pass
  - drift: none
- metrics:
  - files_changed: 4
- issues_to_fix:
  - [blocking] soft-delete 누락 — order_service.rb
- next: generator 재진입
"""

EVAL_NO_REPORT = """구현은 끝났습니다. 보고서 블록을 빼먹었습니다.
"""


class TestParseEvaluatorStatus(unittest.TestCase):
    def test_ready(self):
        self.assertEqual(m.parse_evaluator_status(EVAL_READY), "READY")

    def test_not_ready(self):
        self.assertEqual(m.parse_evaluator_status(EVAL_NOT_READY), "NOT_READY")

    def test_no_report_block_returns_none(self):
        self.assertIsNone(m.parse_evaluator_status(EVAL_NO_REPORT))
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd pilot && python3 tests/tools/test_auto_pilot.py`
Expected: FAIL — `AttributeError: ... 'parse_evaluator_status'`

- [ ] **Step 3: 최소 구현 작성**

`auto_pilot.py` 에 추가 (`import` 부 + 함수). 하이픈 포함 파일명이라 `importlib.util` 로 로드:

```python
import importlib.util

_THIS_DIR = Path(__file__).resolve().parent


def _load_report_lint():
    """tools/verify-report-lint.py 를 동적 로드 (하이픈 파일명)."""
    path = _THIS_DIR / "verify-report-lint.py"
    spec = importlib.util.spec_from_file_location("verify_report_lint_mod", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_evaluator_status(text: str):
    """evaluator 출력 텍스트에서 VERIFICATION REPORT status 를 추출한다.

    Returns:
        "READY" | "NOT_READY"  — 정상 파싱
        None                   — REPORT 블록 부재 또는 status 부재/이상 (상위에서 hard-stop)
    """
    lint = _load_report_lint()
    block = lint.extract_report_block(text)
    if block is None:
        return None
    parsed = lint.parse_report(block)
    status = parsed.get("status")
    if status not in ("READY", "NOT_READY"):
        return None
    return status
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd pilot && python3 tests/tools/test_auto_pilot.py`
Expected: PASS — `Ran 17 tests ... OK`

- [ ] **Step 5: 커밋**

```bash
cd pilot && git add tools/auto_pilot.py tests/tools/test_auto_pilot.py
git commit -m "feat(pilot): auto_pilot evaluator status 파서 (report-lint 재사용)"
```

---

## Task 4: CLI 진입점 — 신호 파일을 받아 액션 JSON 출력

스킬(SKILL.md)이 호출할 CLI 를 만든다. 스킬은 각 phase 후 산출물 경로를 넘기고, CLI 는 적절한 파서를 돌려 `decide_next` 결과를 JSON 으로 출력한다. 스킬이 직접 파싱 로직을 갖지 않도록 한다 (결정론 보장).

**Files:**
- Modify: `pilot/tools/auto_pilot.py`
- Test: `pilot/tests/tools/test_auto_pilot.py`

- [ ] **Step 1: 실패하는 테스트 추가 (subprocess 로 CLI 검증)**

`test_auto_pilot.py` 상단 import 에 `subprocess`, `tempfile`, `json`, `os` 추가하고 클래스 추가:

```python
import subprocess
import tempfile
import json
import os


class TestCli(unittest.TestCase):
    def _run(self, args, stdin_text=None):
        proc = subprocess.run(
            ["python3", str(TOOL_PATH)] + args,
            input=stdin_text,
            capture_output=True,
            text=True,
        )
        return proc

    def test_planner_phase_pass(self):
        proc = self._run(["--phase", "planner", "--plan-valid", "true"])
        self.assertEqual(proc.returncode, 0)
        out = json.loads(proc.stdout)
        self.assertEqual(out["kind"], "proceed")

    def test_planner_phase_fail(self):
        proc = self._run(["--phase", "planner", "--plan-valid", "false"])
        out = json.loads(proc.stdout)
        self.assertEqual(out["kind"], "stop")
        self.assertEqual(out["reason"], "plan-validate")

    def test_critic_phase_reads_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(CRITIC_WITH_BLOCKING)
            path = f.name
        try:
            proc = self._run(["--phase", "critic", "--critic-file", path])
            out = json.loads(proc.stdout)
            self.assertEqual(out["kind"], "stop")
            self.assertEqual(out["reason"], "critic-blocking")
        finally:
            os.unlink(path)

    def test_evaluator_phase_reads_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(EVAL_NOT_READY)
            path = f.name
        try:
            proc = self._run(
                ["--phase", "evaluator", "--report-file", path, "--retries-used", "0"]
            )
            out = json.loads(proc.stdout)
            self.assertEqual(out["kind"], "retry")
        finally:
            os.unlink(path)

    def test_evaluator_missing_file_stops_signal_parse(self):
        proc = self._run(
            ["--phase", "evaluator", "--report-file", "/no/such/file.md",
             "--retries-used", "0"]
        )
        out = json.loads(proc.stdout)
        self.assertEqual(out["kind"], "stop")
        self.assertEqual(out["reason"], "signal-parse")
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd pilot && python3 tests/tools/test_auto_pilot.py`
Expected: FAIL — CLI 미구현이라 `--phase` 인자 처리 없음 → JSON 파싱 에러 또는 비정상 종료

- [ ] **Step 3: 최소 구현 작성**

`auto_pilot.py` 끝에 추가:

```python
def _read_file_or_none(path_str):
    """파일을 읽어 텍스트 반환. 없거나 못 읽으면 None."""
    if not path_str:
        return None
    p = Path(path_str)
    if not p.is_file():
        return None
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return None


def _build_signal(args) -> dict:
    """CLI 인자 → decide_next 가 받는 signal dict."""
    if args.phase == "planner":
        return {"plan_valid": args.plan_valid == "true"}

    if args.phase == "critic":
        text = _read_file_or_none(args.critic_file)
        if text is None:
            return {"severities": None}
        return {"severities": parse_critic_severities(text)}

    if args.phase == "evaluator":
        text = _read_file_or_none(args.report_file)
        status = parse_evaluator_status(text) if text is not None else None
        return {"status": status, "retries_used": args.retries_used}

    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="pilot auto-pilot 전이 결정")
    ap.add_argument(
        "--phase", required=True, choices=["planner", "critic", "evaluator"]
    )
    ap.add_argument("--plan-valid", choices=["true", "false"], dest="plan_valid")
    ap.add_argument("--critic-file", dest="critic_file")
    ap.add_argument("--report-file", dest="report_file")
    ap.add_argument("--retries-used", type=int, default=0, dest="retries_used")
    args = ap.parse_args()

    signal = _build_signal(args)
    action = decide_next(args.phase, signal)
    print(json.dumps({"kind": action.kind, "reason": action.reason}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd pilot && python3 tests/tools/test_auto_pilot.py`
Expected: PASS — `Ran 22 tests ... OK`

- [ ] **Step 5: 커밋**

```bash
cd pilot && git add tools/auto_pilot.py tests/tools/test_auto_pilot.py
git commit -m "feat(pilot): auto_pilot CLI 진입점 추가"
```

---

## Task 5: 오케스트레이터 스킬 — `skills/auto/SKILL.md`

기존 4개 에이전트를 순차 호출하며 각 전이마다 `auto_pilot.py` CLI 로 다음 액션을 결정하고, `NN.auto.md` 에 로그를 남기는 스킬을 작성한다. 이 스킬 자체는 판단하지 않고 CLI 결정에 따라 다음 에이전트를 호출하거나 멈춘다.

이 Task 는 코드가 아니라 마크다운 절차 문서이므로 테스트 대신 구조 검증으로 진행한다.

**Files:**
- Create: `pilot/skills/auto/SKILL.md`

- [ ] **Step 1: SKILL.md 작성**

`pilot/skills/auto/SKILL.md` 생성. 아래 전체 내용을 그대로 Write:

````markdown
---
name: auto
description: >-
  이미 생성된 단일 feature 를 planner→critic→generator→evaluator 로
  자동 순차 진행하는 감독형 자율 모드. hard-stop 신호(plan-validate 실패·
  critic blocking·재시도 소진·신호 파싱 실패)에 걸리면 즉시 사람에게 제어를
  반환한다. 모든 자동 결정은 features/NN-{slug}.auto.md 에 기록한다. feature
  생성·명세 작업은 `/pilot:create-feature`·`/pilot:analyze` 가 담당한다.
---

# /pilot:auto

이미 명세가 존재하는 **단일 feature** 를 자동 순차 진행한다. 기본 흐름은
사용자가 각 에이전트를 명시 호출하는 것이고, 이 스킬은 그 마찰을 줄이는
**opt-in 예외 모드**다. 위험 신호에 걸리면 자동 진행을 멈추고 사람에게 넘긴다.

대상: $ARGUMENTS (feature 번호 — 예: `03` 또는 `3`)

**사용 예:**

```
/pilot:auto 03
/pilot:auto 3
```

---

## 사전 확인

[preamble.md](../context/shared/preamble.md) 의 **P1** 수행.

- P1: `{PROJECT}` 획득. 실패 시 [messages.md](../context/shared/messages.md) 의
  `workspace_missing` / `no_active_project` 출력 후 종료.

`$ARGUMENTS` 가 비어있으면 **"feature 번호를 입력하세요. 예: `/pilot:auto 03`"**
안내 후 종료.

`{NN}` = 입력 번호를 2자리 zero-pad (예: `3` → `03`).
`{FEAT}` = `workspace/projects/{PROJECT}/features/{NN}-*.md` (`.plan.md`·`.plan.critic.md`·`.auto.md` 제외).
`{FEAT}` 가 없으면 **"feature {NN} 없음. `/pilot:create-feature` 로 먼저 생성하세요."**
출력 후 종료 (hard-stop: feature 부재).

`{AUTO_LOG}` = `workspace/projects/{PROJECT}/features/{NN}-{slug}.auto.md`.

---

## 재개 확인

`{AUTO_LOG}` 이 이미 존재하면, 이전 실행이 중단됐거나 완료된 것이다.
파일 마지막 `## Run` 섹션의 마지막 줄(stop 사유 또는 ✅ DONE)을 읽고
사용자에게 **1회 확인**한다:

```
이 feature 는 이전에 auto-pilot 이 실행됐습니다.
마지막 상태: {마지막 줄}

어떻게 할까요?
  1. 여기서 재개 (마지막 멈춘 phase 다음부터)
  2. 처음부터 다시 (planner 부터)
  3. 취소
```

사용자 응답 전까지 진행하지 않는다. 이미 ✅ DONE 인 경우에도 동일하게
"이미 완료됨, 다시 할까요?" 로 확인한다. `{AUTO_LOG}` 이 없으면 처음부터
(planner) 시작하고 새 `## Run` 섹션을 연다.

---

## 자동 진행 절차

각 단계 후 반드시 `auto_pilot.py` 로 다음 액션을 결정한다. **스킬이 직접
신호를 해석하지 않는다** — CLI 가 반환한 `kind` 에 따라서만 분기한다.

### 1. planner

`@pilot-planner` 를 호출해 `{NN}-{slug}.plan.md` 를 작성하게 한다.
완료되면 plan 을 검증한다 (mode 는 `.agent-state.yml` 의 tdd/characterize 로 결정 —
tdd:true→`tdd`, mode:characterize→`characterize`, 그 외→`standard`):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/plan-validate.py \
  workspace/projects/{PROJECT}/features/{NN}-{slug}.plan.md --mode {MODE}
echo "exit=$?"
```

exit 0 이면 `--plan-valid true`, 아니면 `false`:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/auto_pilot.py --phase planner --plan-valid {true|false}
```

- `kind=proceed` → 2번으로
- `kind=stop` (reason=plan-validate) → **STOP**. 로그에 기록 후 사람에게 보고.

### 2. critic

`@pilot-planner-critic` 를 호출해 `{NN}-{slug}.plan.critic.md` 를 작성하게 한다.
완료되면:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/auto_pilot.py --phase critic \
  --critic-file workspace/projects/{PROJECT}/features/{NN}-{slug}.plan.critic.md
```

- `kind=proceed` (챌린지 0건) → 3번으로
- `kind=reflect` (suggestion/nit 만) → `@pilot-planner` 를 재호출해 챌린지를
  반영하고 `.plan.critic.md` 의 `## 합의` 표를 채우게 한 뒤 3번으로.
- `kind=stop` (reason=critic-blocking) → **STOP**. blocking 챌린지는 사람 판단.
- `kind=stop` (reason=signal-parse) → **STOP**. critic 파일 형식 이상.

### 3. generator

`@pilot-generator` 를 호출해 구현하게 한다. (재시도 시에도 이 단계로 재진입.)
generator 는 산출 신호가 없으므로 결정 호출 없이 4번으로 진행한다.
generator 호출이 예외/빈 출력으로 실패하면 **STOP** (reason=agent-error) 후
로그 기록.

### 4. evaluator

`@pilot-evaluator` 를 호출해 검증하게 한다. evaluator 의 VERIFICATION REPORT
출력을 파일로 저장한다 (`{NN}-{slug}.report.md` 임시 저장 또는 evaluator 가
남긴 산출물 경로). 그 파일로:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/auto_pilot.py --phase evaluator \
  --report-file {REPORT_PATH} --retries-used {R}
```

`{R}` = 지금까지 generator 재진입 횟수 (최초 0).

- `kind=done` (READY) → ✅ 완료. 로그에 기록 후 사람에게 보고.
- `kind=retry` (NOT_READY, 재시도 잔여) → `{R}` 을 1 증가시키고 3번(generator)
  으로 재진입.
- `kind=stop` (reason=retry-exhausted) → **STOP**. 재시도 소진, 사람 판단.
- `kind=stop` (reason=signal-parse) → **STOP**. REPORT 형식 이상.

---

## 감사 로그 (`{AUTO_LOG}`)

매 전이마다 `{AUTO_LOG}` 에 타임라인 한 줄을 append 한다. 새 실행은 새
`## Run N — {날짜}` 섹션으로 시작한다. 형식:

```markdown
# Auto-pilot Log: {NN}-{slug}

## Run 1 — {YYYY-MM-DD}
- [planner]  plan.md 작성 → plan-validate {PASS|FAIL}
- [critic]   챌린지 {N}건 (blocking a · suggestion b · nit c) → {proceed|reflect}
- [generator] diff 생성
- [evaluator] {READY|NOT_READY} ({실패 gate 요약})
- [retry 1/1] generator 재진입 → evaluator {결과}
- {✅ DONE | ❌ STOP: {사유} (hard-stop)}
  → {사람 판단 필요 항목 — stop 인 경우}
```

각 줄은 해당 단계가 끝나는 즉시 기록한다 (중단돼도 진행 흔적이 남도록).

---

## STOP 시 사람에게 보고

자동 진행이 멈추면 메인 대화에 다음을 출력하고 **종료**한다 (더 진행하지 않음):

```
auto-pilot 중단: {NN}-{slug}
사유: {stop 사유}
마지막 단계: {phase}
사람 판단 필요: {항목}

수정 후 `/pilot:auto {NN}` 으로 재개할 수 있습니다.
로그: features/{NN}-{slug}.auto.md
```

---

## 제약

- **opt-in 예외 모드.** pilot 의 기본은 사용자가 각 에이전트를 명시 호출하는
  것이다. 이 스킬은 저위험·소규모 feature 의 마찰을 줄이기 위한 것이며,
  위험 신호에 걸리면 항상 사람에게 제어를 반환한다.
- **스킬은 판단하지 않는다.** 모든 전이는 `auto_pilot.py` 가 신호 enum 을 보고
  내린 결정(`kind`)에 따른다. 도메인 판단은 각 에이전트의 책임이다.
- **신호를 못 읽으면 멈춘다.** critic/evaluator 산출물 파싱 실패는 추측 없이
  hard-stop(signal-parse) 한다.
- **재시도는 정확히 1회**, 항상 generator 재진입. plan 자체가 틀렸다면 2차
  NOT_READY 로 사람에게 넘어간다.
- **단일 feature 단위.** 다수 feature 연속 진행은 지원하지 않는다.

---

## 참고

- `/pilot:create-feature` — 단일 feature 명세 생성 (이 스킬의 선행 단계)
- `/pilot:focus` — 진행 중 사용자 결정을 에이전트에 전달
- `@pilot-planner` 외 — 수동으로 각 단계 호출 (auto 를 쓰지 않을 때)
````

- [ ] **Step 2: 스킬 구조 검증**

Run: `cd pilot && python3 -c "import pathlib,sys; t=pathlib.Path('skills/auto/SKILL.md').read_text(); assert t.startswith('---'); assert 'name: auto' in t; assert 'auto_pilot.py' in t; assert '재개 확인' in t; print('SKILL.md OK')"`
Expected: `SKILL.md OK`

- [ ] **Step 3: 커밋**

```bash
cd pilot && git add skills/auto/SKILL.md
git commit -m "feat(pilot): /pilot:auto 오케스트레이터 스킬 추가"
```

---

## Task 6: 전체 회귀 테스트 + auto_pilot 실행 권한

신규 도구가 기존 테스트를 깨지 않는지 확인하고, CLI 가 실행 가능한지 점검한다.

**Files:**
- Modify: `pilot/tools/auto_pilot.py` (실행 권한)

- [ ] **Step 1: auto_pilot 전체 테스트**

Run: `cd pilot && python3 tests/tools/test_auto_pilot.py`
Expected: PASS — `OK` (22 tests)

- [ ] **Step 2: 기존 도구 회귀 테스트 (인접 영향 확인)**

Run: `cd pilot && python3 tests/tools/test_verify_report_lint.py && python3 tests/tools/test_plan_validate.py`
Expected: 둘 다 `OK` — auto_pilot 이 verify-report-lint 를 import 만 할 뿐 수정하지 않았으므로 영향 없음

- [ ] **Step 3: CLI smoke test**

Run: `cd pilot && python3 tools/auto_pilot.py --phase planner --plan-valid true`
Expected: `{"kind": "proceed", "reason": ""}`

- [ ] **Step 4: 실행 권한 부여 (기존 tools 관례 일치)**

```bash
cd pilot && chmod +x tools/auto_pilot.py && ls -l tools/auto_pilot.py | cut -c1-10
```
Expected: `-rwxr-xr-x`

- [ ] **Step 5: 커밋**

```bash
cd pilot && git add tools/auto_pilot.py
git commit -m "chore(pilot): auto_pilot.py 실행 권한 부여"
```

---

## Task 7: 문서 정합성 — auto 모드를 예외로 명시

기존 문서가 "자동 파이프라인 아님"을 강조하므로, auto 가 그 원칙의 명시적 예외임을 문서화해 모순을 없앤다.

**Files:**
- Modify: `pilot/.claude-plugin/plugin.json`
- Modify: `pilot/agents/pilot-planner.md` (흐름 안내 부분)

- [ ] **Step 1: plugin.json description 갱신**

`pilot/.claude-plugin/plugin.json` 의 `description` 끝에 auto 언급을 추가한다. 현재 값:

```json
"description": "Domain-knowledge-driven agent workflow plugin for complex projects (pilot-planner → [pilot-planner-critic] → pilot-generator → pilot-evaluator) + pilot-code-review for pre-PR code review",
```

다음으로 교체:

```json
"description": "Domain-knowledge-driven agent workflow plugin for complex projects (pilot-planner → [pilot-planner-critic] → pilot-generator → pilot-evaluator) + pilot-code-review for pre-PR code review. /pilot:auto provides opt-in supervised autonomy for a single feature.",
```

- [ ] **Step 2: pilot-planner.md 에 auto 모드 한 줄 추가**

`pilot/agents/pilot-planner.md` 에서 흐름을 설명하는 부분(`사용자 선택 후 흐름은 ...` 문장이 있는 단락) 바로 뒤에 한 줄을 추가한다. 먼저 해당 위치를 찾는다:

Run: `cd pilot && grep -n "자동 호출하는 것은 금지" agents/pilot-planner.md`
Expected: 한 줄 매칭 (예: `85:...skip 은 항상 사용자 결정이다.`)

그 줄 다음에 빈 줄 + 아래 문장을 삽입:

```markdown

> 예외: `/pilot:auto` (감독형 자율 모드) 는 이 흐름을 자동 순차 진행하되, critic blocking·재시도 소진 등 hard-stop 신호에 걸리면 사람에게 제어를 반환한다. 자동 모드에서도 critic 은 항상 실행되며 blocking 챌린지는 auto-accept 하지 않는다.
```

- [ ] **Step 3: 정합성 확인**

Run: `cd pilot && python3 -c "import json; d=json.load(open('.claude-plugin/plugin.json')); assert 'pilot:auto' in d['description']; print('plugin.json OK')" && grep -q "pilot:auto" agents/pilot-planner.md && echo "planner doc OK"`
Expected:
```
plugin.json OK
planner doc OK
```

- [ ] **Step 4: 커밋**

```bash
cd pilot && git add .claude-plugin/plugin.json agents/pilot-planner.md
git commit -m "docs(pilot): /pilot:auto 를 수동 흐름의 opt-in 예외로 명시"
```

---

## 완료 기준

- `python3 tests/tools/test_auto_pilot.py` → OK (22 tests)
- `python3 tests/tools/test_verify_report_lint.py` → OK (회귀 없음)
- `python3 tests/tools/test_plan_validate.py` → OK (회귀 없음)
- `/pilot:auto` 스킬이 plugin 스킬 목록에 노출됨
- plugin.json·planner 문서가 auto 모드를 예외로 명시 (기존 "자동 아님" 원칙과 모순 없음)

## 추후 과제 (이번 범위 밖 — 설계 §8)

- 다수 feature / 프로젝트 전체 연속 진행 (`--all`)
- `/pilot:doctor` 의 `NN.auto.md` 정합성 점검 (중단 방치 감지)
- 위험도 기반 게이팅
- Slack 알림 연동 (`slack-notify.py` 재사용)
