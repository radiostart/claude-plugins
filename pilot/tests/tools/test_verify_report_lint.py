"""
tools/verify-report-lint.py 단위 테스트.

실행:
    python3 tests/tools/test_verify_report_lint.py
"""

import importlib.util
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "verify-report-lint.py"
FIXTURES = PLUGIN_ROOT / "tests" / "fixtures" / "verify-reports"


def _load_mod():
    spec = importlib.util.spec_from_file_location("verify_lint_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = _load_mod()


class ExtractAndParse(unittest.TestCase):
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


class ValidateRules(unittest.TestCase):
    def _lint(self, text: str):
        return m.lint(text)

    def test_valid_ready_tdd(self):
        text = (FIXTURES / "valid" / "01-ready-tdd.md").read_text(encoding="utf-8")
        violations, present = self._lint(text)
        self.assertTrue(present)
        self.assertEqual([v for v in violations if v.severity == m.Violation.SEVERITY_ERROR], [])

    def test_valid_characterize(self):
        text = (FIXTURES / "valid" / "02-ready-characterize.md").read_text(encoding="utf-8")
        violations, present = self._lint(text)
        self.assertTrue(present)
        errs = [v for v in violations if v.severity == m.Violation.SEVERITY_ERROR]
        self.assertEqual(errs, [], msg=f"errors: {[v.message for v in errs]}")

    def test_valid_standard(self):
        text = (FIXTURES / "valid" / "03-ready-standard.md").read_text(encoding="utf-8")
        violations, present = self._lint(text)
        self.assertTrue(present)
        errs = [v for v in violations if v.severity == m.Violation.SEVERITY_ERROR]
        self.assertEqual(errs, [], msg=f"errors: {[v.message for v in errs]}")

    def test_valid_not_ready_with_issues(self):
        text = (FIXTURES / "valid" / "04-not-ready-with-issues.md").read_text(encoding="utf-8")
        violations, present = self._lint(text)
        self.assertTrue(present)
        errs = [v for v in violations if v.severity == m.Violation.SEVERITY_ERROR]
        self.assertEqual(errs, [], msg=f"errors: {[v.message for v in errs]}")

    def test_invalid_no_block(self):
        text = (FIXTURES / "invalid" / "01-no-block.md").read_text(encoding="utf-8")
        violations, present = self._lint(text)
        self.assertFalse(present)

    def test_invalid_status_gate_mismatch(self):
        text = (FIXTURES / "invalid" / "02-status-gate-mismatch.md").read_text(encoding="utf-8")
        violations, present = self._lint(text)
        self.assertTrue(present)
        codes = [v.code for v in violations]
        self.assertIn("status_gate_inconsistency", codes)

    def test_invalid_mode_characterize(self):
        text = (FIXTURES / "invalid" / "04-mode-gate-mismatch-characterize.md").read_text(encoding="utf-8")
        violations, _ = self._lint(text)
        codes = [v.code for v in violations]
        self.assertIn("mode_gate_mismatch", codes)

    def test_valid_standard_with_test_run(self):
        """standard 모드에서도 test_command 설정 시 test_run: pass 가 합법."""
        text = (FIXTURES / "valid" / "06-ready-standard-with-tests.md").read_text(encoding="utf-8")
        violations, present = self._lint(text)
        self.assertTrue(present)
        errs = [v for v in violations if v.severity == m.Violation.SEVERITY_ERROR]
        self.assertEqual(errs, [], msg=f"errors: {[v.message for v in errs]}")

    def test_invalid_mode_standard(self):
        text = (FIXTURES / "invalid" / "05-mode-gate-mismatch-standard.md").read_text(encoding="utf-8")
        violations, _ = self._lint(text)
        codes = [v.code for v in violations]
        # tdd_evidence: pass 만 위반 — test_run 은 standard 에서 무제약 (skip|pass|fail)
        self.assertEqual(codes.count("mode_gate_mismatch"), 1)

    def test_invalid_enum_values(self):
        text = (FIXTURES / "invalid" / "06-invalid-enum-values.md").read_text(encoding="utf-8")
        violations, _ = self._lint(text)
        codes = [v.code for v in violations]
        self.assertIn("invalid_status", codes)
        self.assertIn("invalid_mode", codes)
        self.assertIn("invalid_gate_value", codes)

    def test_invalid_missing_gates(self):
        text = (FIXTURES / "invalid" / "07-missing-gates.md").read_text(encoding="utf-8")
        violations, _ = self._lint(text)
        codes = [v.code for v in violations]
        # 누락 gate: capture_lockdown, drift (pilot 은 open_questions gate 없음)
        self.assertEqual(codes.count("missing_gate"), 2)

class CLIBehavior(unittest.TestCase):
    """exit code 와 출력 형식 검증."""

    def test_pass_returns_pass_label(self):
        text = (FIXTURES / "valid" / "01-ready-tdd.md").read_text(encoding="utf-8")
        violations, present = m.lint(text)
        out = m.render_text(violations, present)
        self.assertIn("PASS", out)

    def test_fail_returns_fail_label(self):
        text = (FIXTURES / "invalid" / "02-status-gate-mismatch.md").read_text(encoding="utf-8")
        violations, present = m.lint(text)
        out = m.render_text(violations, present)
        self.assertIn("FAIL", out)

    def test_no_block_returns_fail(self):
        text = (FIXTURES / "invalid" / "01-no-block.md").read_text(encoding="utf-8")
        violations, present = m.lint(text)
        out = m.render_text(violations, present)
        self.assertIn("FAIL", out)
        self.assertIn("부재", out)

    def test_json_output_structure(self):
        import json as _json
        text = (FIXTURES / "valid" / "01-ready-tdd.md").read_text(encoding="utf-8")
        violations, present = m.lint(text)
        out = m.render_json(violations, present)
        data = _json.loads(out)
        self.assertTrue(data["block_present"])
        self.assertTrue(data["passed"])
        self.assertEqual(data["violations"], [])


if __name__ == "__main__":
    unittest.main()
