"""
tools/docs_build.py 의 변환 단위·통합 테스트.

실행:
    python3 -m unittest pilot.tests.tools.test_docs_build
"""

from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PILOT_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PILOT_ROOT / "tools" / "docs_build.py"
FIXTURE_DIR = THIS_DIR.parent / "fixtures" / "docs_build"
FIXTURE_SOURCES = FIXTURE_DIR / "sources"
FIXTURE_EXPECTED = FIXTURE_DIR / "expected"


def _load_mod():
    spec = importlib.util.spec_from_file_location("docs_build_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


m = _load_mod()


class ParseFrontmatter(unittest.TestCase):
    def test_extracts_yaml_block(self):
        text = "---\nname: x\ndescription: y\n---\nbody here\n"
        meta, body = m.parse_frontmatter(text)
        self.assertEqual(meta, {"name": "x", "description": "y"})
        self.assertEqual(body, "body here\n")

    def test_no_frontmatter_returns_empty_meta(self):
        text = "# heading\nbody\n"
        meta, body = m.parse_frontmatter(text)
        self.assertEqual(meta, {})
        self.assertEqual(body, text)

    def test_malformed_yaml_returns_empty_meta(self):
        # 진짜로 yaml-invalid (탭+불균형 흐름 시퀀스)
        text = "---\n- [unclosed\n  key: value\n---\nbody\n"
        meta, _ = m.parse_frontmatter(text)
        self.assertEqual(meta, {})

    def test_non_dict_yaml_returns_empty_meta(self):
        # frontmatter 가 dict 가 아닌 list 면 reference 메타로 부적격 → empty
        text = "---\n- a\n- b\n---\nbody\n"
        meta, _ = m.parse_frontmatter(text)
        self.assertEqual(meta, {})


class StripWrapperQuote(unittest.TestCase):
    def test_removes_leading_quote_block(self):
        body = "\n> wrapper 안내\n> 추가 줄\n\n실제 본문\n"
        out = m.strip_wrapper_quote(body)
        self.assertEqual(out, "실제 본문\n")

    def test_keeps_body_without_quote(self):
        body = "## 책임\n본문\n"
        out = m.strip_wrapper_quote(body)
        self.assertEqual(out, body)


class TransformAgent(unittest.TestCase):
    def test_matches_expected_golden(self):
        src = FIXTURE_SOURCES / "agents" / "sample-agent.md"
        expected = (FIXTURE_EXPECTED / "agents" / "sample-agent.md").read_text(encoding="utf-8")
        self.assertEqual(m.transform_agent(src), expected)


class TransformSkill(unittest.TestCase):
    def test_matches_expected_golden(self):
        src = FIXTURE_SOURCES / "skills" / "sample-skill"
        expected = (FIXTURE_EXPECTED / "skills" / "sample-skill.md").read_text(encoding="utf-8")
        self.assertEqual(m.transform_skill(src), expected)

    def test_returns_none_when_skill_md_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "noskill"
            empty.mkdir()
            self.assertIsNone(m.transform_skill(empty))


class TransformTool(unittest.TestCase):
    def test_matches_expected_golden(self):
        src = FIXTURE_SOURCES / "tools" / "sample_tool.py"
        expected = (FIXTURE_EXPECTED / "tools" / "sample_tool.md").read_text(encoding="utf-8")
        self.assertEqual(m.transform_tool(src), expected)

    def test_excludes_private_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "_internal.py"
            f.write_text('"""docstring"""\n', encoding="utf-8")
            self.assertIsNone(m.transform_tool(f))

    def test_skips_when_no_docstring(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "nodoc.py"
            f.write_text("x = 1\n", encoding="utf-8")
            self.assertIsNone(m.transform_tool(f))


class TransformIdentity(unittest.TestCase):
    def test_matches_expected_golden(self):
        src = FIXTURE_SOURCES / "skills" / "context" / "shared" / "identity.yml"
        expected = (FIXTURE_EXPECTED / "identity.md").read_text(encoding="utf-8")
        self.assertEqual(m.transform_identity(src), expected)


class BuildIntegration(unittest.TestCase):
    """전체 fixture 디렉토리에 build() 를 돌려 expected 와 비교."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        # fixture sources 를 tmp/{root} 로 복사 (build 가 cwd-안전하게 동작하는지 검증)
        shutil.copytree(FIXTURE_SOURCES, self.tmp / "root")
        self.root = self.tmp / "root"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _expected_map(self) -> dict[Path, str]:
        em: dict[Path, str] = {}
        for f in sorted(FIXTURE_EXPECTED.rglob("*.md")):
            rel = f.relative_to(FIXTURE_EXPECTED)
            em[self.root / "docs" / "reference" / rel] = f.read_text(encoding="utf-8")
        return em

    def test_build_matches_expected(self):
        files = m.build(self.root)
        expected = self._expected_map()
        self.assertEqual(set(files.keys()), set(expected.keys()))
        for p, content in files.items():
            self.assertEqual(content, expected[p], f"diff at {p.relative_to(self.root)}")

    def test_write_then_check_passes(self):
        files = m.build(self.root)
        m.write_files(files)
        self.assertEqual(m.check_files(files), [])

    def test_check_reports_drift(self):
        files = m.build(self.root)
        m.write_files(files)
        # 임의로 한 파일 내용 변형
        sample = next(iter(files.keys()))
        sample.write_text("drifted\n", encoding="utf-8")
        diffs = m.check_files(files)
        self.assertIn(sample, diffs)

    def test_check_reports_missing(self):
        files = m.build(self.root)
        # write 하지 않음 → 모두 missing
        diffs = m.check_files(files)
        self.assertEqual(set(diffs), set(files.keys()))


class MainExitCodes(unittest.TestCase):
    def test_check_exits_1_on_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            shutil.copytree(FIXTURE_SOURCES, tmp_path / "root")
            exit_code = m.main(["--check", "--root", str(tmp_path / "root")])
            self.assertEqual(exit_code, 1)

    def test_generate_then_check_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            shutil.copytree(FIXTURE_SOURCES, tmp_path / "root")
            self.assertEqual(m.main(["--root", str(tmp_path / "root")]), 0)
            self.assertEqual(m.main(["--check", "--root", str(tmp_path / "root")]), 0)

    def test_missing_root_exits_1(self):
        exit_code = m.main(["--root", "/nonexistent/path/xxxx"])
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
