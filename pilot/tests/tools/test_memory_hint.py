"""
tools/memory-hint.py 의 인덱스 파싱 / 토큰화 / 점수 계산 단위 테스트.

실행:
    python3 tests/tools/test_memory_hint.py
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "memory-hint.py"


def _load_mod():
    spec = importlib.util.spec_from_file_location("memory_hint_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = _load_mod()


class SlugForCwd(unittest.TestCase):
    def test_slashes_become_dashes(self):
        self.assertEqual(m.slug_for_cwd(Path("/Users/jay/Projects/foo")), "-Users-jay-Projects-foo")


class Tokenize(unittest.TestCase):
    def test_korean_english_digits_extracted_lowercased(self):
        out = m.tokenize("관리자 ADMIN 영역 v0.2.5")
        # 영문은 소문자, 한글 그대로, 점은 분할 → "0", "2", "5"
        self.assertIn("관리자", out)
        self.assertIn("admin", out)
        self.assertIn("영역", out)
        self.assertIn("v0", out)

    def test_punctuation_drops(self):
        self.assertEqual(m.tokenize("a, b. c!"), ["a", "b", "c"])

    def test_empty_input_returns_empty(self):
        self.assertEqual(m.tokenize(""), [])


class ParseIndex(unittest.TestCase):
    def _write_index(self, content: str) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        tmp.write(content)
        tmp.close()
        return Path(tmp.name)

    def test_em_dash_separator(self):
        idx = self._write_index("- [Title A](file_a.md) — hook A\n- [Title B](file_b.md) — hook B\n")
        entries = m.parse_index(idx)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["title"], "Title A")
        self.assertEqual(entries[0]["filename"], "file_a.md")
        self.assertEqual(entries[0]["hook"], "hook A")

    def test_hyphen_and_colon_separators(self):
        idx = self._write_index("- [X](x.md) - hook X\n- [Y](y.md) : hook Y\n")
        entries = m.parse_index(idx)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[1]["hook"], "hook Y")

    def test_non_matching_lines_skipped(self):
        idx = self._write_index("# heading\n\n- [valid](v.md) — hook\nrandom text\n* not a dash\n")
        entries = m.parse_index(idx)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["filename"], "v.md")

    def test_missing_file_returns_empty(self):
        self.assertEqual(m.parse_index(Path("/nonexistent/MEMORY.md")), [])


class ReadDescription(unittest.TestCase):
    def test_extracts_description_field(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "f.md").write_text(
                '---\nname: test\ndescription: "관리자 화면 점검 결과"\ntype: project\n---\n\nbody\n',
                encoding="utf-8",
            )
            self.assertEqual(m.read_description(d, "f.md"), "관리자 화면 점검 결과")

    def test_no_frontmatter_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "f.md").write_text("plain body\n", encoding="utf-8")
            self.assertEqual(m.read_description(d, "f.md"), "")

    def test_missing_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(m.read_description(Path(td), "nope.md"), "")


class ScoreEntry(unittest.TestCase):
    def test_counts_keyword_hits_across_fields(self):
        entry = {"title": "관리자 점검", "hook": "ADMIN review", "filename": "admin_check.md"}
        # "관리자" 1회, "admin" 2회 (hook + filename) → 총 3
        self.assertEqual(m.score_entry(entry, "", ["관리자", "admin"]), 3)

    def test_no_keywords_zero_score(self):
        entry = {"title": "x", "hook": "y", "filename": "z.md"}
        self.assertEqual(m.score_entry(entry, "", []), 0)

    def test_empty_keyword_skipped(self):
        entry = {"title": "x", "hook": "y", "filename": "z.md"}
        self.assertEqual(m.score_entry(entry, "", ["", "x"]), 1)

    def test_includes_description_in_haystack(self):
        entry = {"title": "t", "hook": "h", "filename": "f.md"}
        self.assertEqual(m.score_entry(entry, "관리자 영역", ["관리자"]), 1)


class MemoryDirCandidates(unittest.TestCase):
    def test_primary_only_when_no_worktree_marker(self):
        cands = m.memory_dir_candidates(Path("/Users/x/Projects/foo"))
        self.assertEqual(len(cands), 1)
        self.assertTrue(str(cands[0]).endswith("/-Users-x-Projects-foo/memory"))

    def test_worktree_fallback_added(self):
        # worktree 슬롯 cwd 는 marker 이후 부분이 worktree 식별자
        wt = Path("/Users/x/Projects/foo--claude-worktrees-abc123")
        cands = m.memory_dir_candidates(wt)
        self.assertEqual(len(cands), 2)
        # 두 번째 후보는 marker 이전 경로 = 원본 프로젝트 memory
        self.assertTrue(str(cands[1]).endswith("/-Users-x-Projects-foo/memory"))


if __name__ == "__main__":
    unittest.main()
