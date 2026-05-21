"""
tools/regen-verify.py 단위 테스트.

실행:
    python3 tests/tools/test_regen_verify.py
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "regen-verify.py"
FIXTURES = PLUGIN_ROOT / "tests" / "fixtures" / "regen-verify"


def _load_mod():
    spec = importlib.util.spec_from_file_location("regen_verify_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = _load_mod()


class ParseSections(unittest.TestCase):
    def test_managed_marker_recognized(self):
        text = (
            "# Title\n\n"
            "<!-- [analyze-managed] -->\n"
            "## A\n본문 A\n\n"
            "## B\n본문 B\n"
        )
        sections = m.parse_sections(text)
        # B 는 managed 아님
        a = next(s for s in sections if s["title"] == "## A")
        b = next(s for s in sections if s["title"] == "## B")
        self.assertTrue(a["managed"])
        self.assertFalse(b["managed"])

    def test_marker_with_blank_lines_above_section(self):
        text = (
            "<!-- [analyze-managed] -->\n\n\n"
            "## A\n본문\n"
        )
        sections = m.parse_sections(text)
        a = next(s for s in sections if s["title"] == "## A")
        self.assertTrue(a["managed"])

    def test_no_h2_returns_only_preface(self):
        """H2 없으면 preface 단일 섹션 (title=None) 만 반환."""
        sections = m.parse_sections("# 제목\n본문\n")
        h2_sections = [s for s in sections if s["title"] is not None]
        self.assertEqual(h2_sections, [])


class CompareFiles(unittest.TestCase):
    def _write(self, td: Path, name: str, content: str) -> Path:
        p = td / name
        p.write_text(content, encoding="utf-8")
        return p

    def test_identical_files_no_violation(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            content = "<!-- [analyze-managed] -->\n## A\n본문\n\n## B\n본문\n"
            b = self._write(tdp, "b.md", content)
            a = self._write(tdp, "a.md", content)
            r = m.compare_files(b, a)
            self.assertEqual(r["preserved_violations"], [])
            self.assertEqual(r["managed_changed"], [])

    def test_managed_section_changed_is_info_not_violation(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            before = "<!-- [analyze-managed] -->\n## A\n구\n\n## B\n동일\n"
            after = "<!-- [analyze-managed] -->\n## A\n신\n\n## B\n동일\n"
            b = self._write(tdp, "b.md", before)
            a = self._write(tdp, "a.md", after)
            r = m.compare_files(b, a)
            self.assertEqual(r["preserved_violations"], [])
            self.assertIn("## A", r["managed_changed"])

    def test_preserved_section_changed_is_violation(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            before = "<!-- [analyze-managed] -->\n## A\n동일\n\n## B\n구\n"
            after = "<!-- [analyze-managed] -->\n## A\n동일\n\n## B\n신\n"
            b = self._write(tdp, "b.md", before)
            a = self._write(tdp, "a.md", after)
            r = m.compare_files(b, a)
            self.assertEqual(len(r["preserved_violations"]), 1)
            self.assertEqual(r["preserved_violations"][0]["section"], "## B")

    def test_added_unmanaged_section_is_violation(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            before = "<!-- [analyze-managed] -->\n## A\n본문\n"
            after = "<!-- [analyze-managed] -->\n## A\n본문\n\n## C\n새 항목\n"
            b = self._write(tdp, "b.md", before)
            a = self._write(tdp, "a.md", after)
            r = m.compare_files(b, a)
            self.assertEqual(len(r["preserved_violations"]), 1)
            self.assertEqual(r["preserved_violations"][0]["section"], "## C")

    def test_removed_unmanaged_section_is_violation(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            before = "<!-- [analyze-managed] -->\n## A\n본문\n\n## B\n수동 영역\n"
            after = "<!-- [analyze-managed] -->\n## A\n본문\n"
            b = self._write(tdp, "b.md", before)
            a = self._write(tdp, "a.md", after)
            r = m.compare_files(b, a)
            self.assertEqual(len(r["preserved_violations"]), 1)
            self.assertEqual(r["preserved_violations"][0]["section"], "## B")


class FixtureIntegration(unittest.TestCase):
    def test_safe_passes(self):
        reports = m.verify_dirs(FIXTURES / "before", FIXTURES / "after_safe")
        violations = [r for r in reports if r["preserved_violations"]]
        self.assertEqual(violations, [])

    def test_violation_fails(self):
        reports = m.verify_dirs(FIXTURES / "before", FIXTURES / "after_violation")
        violations = [r for r in reports if r["preserved_violations"]]
        self.assertEqual(len(violations), 1)  # planner.md 1 개
        sections = [v["section"] for v in violations[0]["preserved_violations"]]
        self.assertIn("## 플래닝 프로세스", sections)
        self.assertIn("## 주의사항", sections)


class CLIRender(unittest.TestCase):
    def test_text_render_pass(self):
        reports = m.verify_dirs(FIXTURES / "before", FIXTURES / "after_safe")
        out = m.render_text(reports)
        self.assertIn("PASS", out)
        self.assertNotIn("⚠️", out)

    def test_text_render_fail(self):
        reports = m.verify_dirs(FIXTURES / "before", FIXTURES / "after_violation")
        out = m.render_text(reports)
        self.assertIn("FAIL", out)
        self.assertIn("⚠️", out)

    def test_json_structure(self):
        import json as _json
        reports = m.verify_dirs(FIXTURES / "before", FIXTURES / "after_safe")
        out = m.render_json(reports)
        data = _json.loads(out)
        self.assertTrue(data["passed"])
        self.assertIn("files", data)


if __name__ == "__main__":
    unittest.main()
