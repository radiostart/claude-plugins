"""
tools/auto_pilot.py 단위 테스트.

실행:
    python3 tests/tools/test_auto_pilot.py
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "auto_pilot.py"


def _load_mod():
    spec = importlib.util.spec_from_file_location("auto_pilot_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    # Python 3.13: register in sys.modules before exec so @dataclass can resolve __module__
    sys.modules["auto_pilot_mod"] = module
    spec.loader.exec_module(module)
    return module


m = _load_mod()


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

    def test_pass_marker_does_not_mask_real_severities(self):
        # 통과 문구가 본문에 끼어 있어도 severity 라벨이 있으면 0건 처리하지 않는다.
        text = (
            "## 챌린지\n\n"
            "- **severity**: blocking\n"
            "- **제안**: 이대로면 plan 통과 못 함\n"
        )
        result = m.parse_critic_severities(text)
        self.assertEqual(result, ["blocking"])


class TestParseEvaluatorStatus(unittest.TestCase):
    def test_ready(self):
        self.assertEqual(m.parse_evaluator_status(EVAL_READY), "READY")

    def test_not_ready(self):
        self.assertEqual(m.parse_evaluator_status(EVAL_NOT_READY), "NOT_READY")

    def test_no_report_block_returns_none(self):
        self.assertIsNone(m.parse_evaluator_status(EVAL_NO_REPORT))


class TestExtractAndParseReport(unittest.TestCase):
    """extract_report_block · parse_report 단위 테스트 (구 test_verify_report_lint.py 이식, #20 스텝 5)."""

    def test_no_block_returns_none(self):
        self.assertIsNone(m.extract_report_block("# 다른 헤더\n본문"))

    def test_block_extracted(self):
        text = "전문\n## VERIFICATION REPORT\n- status: READY\n## 다음 섹션\n끝"
        block = m.extract_report_block(text)
        self.assertIn("status: READY", block)
        self.assertNotIn("다음 섹션", block)

    def test_parse_top_level_keys(self):
        block = (
            "- status: READY\n"
            "- feature: #03 결제\n"
            "- mode: red_contract\n"
            "- next: #04 환불\n"
        )
        r = m.parse_report(block)
        self.assertEqual(r["status"], "READY")
        self.assertEqual(r["feature"], "#03 결제")
        self.assertEqual(r["mode"], "red_contract")
        self.assertEqual(r["next"], "#04 환불")

    def test_parse_gates(self):
        block = (
            "- gates:\n"
            "  - requirements: pass — features/03.md\n"
            "  - tdd_evidence: skip — mode 미사용\n"
            "  - drift: detected — workspace/...\n"
        )
        r = m.parse_report(block)
        self.assertEqual(r["gates"]["requirements"]["value"], "pass")
        self.assertEqual(r["gates"]["requirements"]["evidence"], "features/03.md")
        self.assertEqual(r["gates"]["tdd_evidence"]["value"], "skip")
        self.assertEqual(r["gates"]["drift"]["value"], "detected")

    def test_parse_issues(self):
        block = (
            "- issues_to_fix:\n"
            "  - [Major] foo 누락 — features/03.md:14\n"
            "  - [Minor] bar — files/x.md\n"
        )
        r = m.parse_report(block)
        self.assertEqual(len(r["issues_to_fix"]), 2)
        self.assertEqual(r["issues_to_fix"][0]["severity"], "Major")
        self.assertEqual(r["issues_to_fix"][0]["summary"], "foo 누락")
        self.assertEqual(r["issues_to_fix"][0]["location"], "features/03.md:14")

    def test_parse_issues_none(self):
        block = "- issues_to_fix:\n  - none\n"
        r = m.parse_report(block)
        self.assertEqual(len(r["issues_to_fix"]), 1)
        self.assertEqual(r["issues_to_fix"][0]["summary"], "none")


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


if __name__ == "__main__":
    unittest.main()
