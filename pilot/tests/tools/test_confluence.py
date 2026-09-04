"""
tools/confluence.py 의 HTML → Markdown 변환 로직 단위 테스트.

    - parse_html / Element 셰임 (stdlib html.parser 기반, bs4 대체)
    - _table_to_md (rowspan / colspan / nested table 평탄화)
    - _inline_md (bold / italic / link / mention)
    - _cell_md (pipe escape, <br> 보존)
    - split_sections (빈 H1 그룹 헤딩 보존)
    - extract_page_id (URL 파싱)
    - html_to_md 통합
    - search_docs (context-search 랭커 공유 · substring 폴백 · match_pos, #24)

실행:
    python3 tests/tools/test_confluence.py
"""

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "confluence.py"


def _load_confluence():
    spec = importlib.util.spec_from_file_location("confluence_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


c = _load_confluence()


def _table(html: str):
    return c.parse_html(html).find("table")


class HtmlParserShim(unittest.TestCase):
    """parse_html / Element 셰임의 기본 동작."""

    def test_text_nodes_are_plain_str(self):
        # bs4 NavigableString 처럼 텍스트 노드는 str 이어야 isinstance 검사가 호환된다.
        root = c.parse_html("<p>hello</p>")
        p = root.find("p")
        self.assertTrue(all(isinstance(ch, str) for ch in p.children))

    def test_void_tag_not_pushed_to_stack(self):
        # <br> 같은 void 태그는 닫는 태그가 없어도 후속 형제를 자식으로 빨아들이면 안 된다.
        root = c.parse_html("<div>a<br>b</div>")
        div = root.find("div")
        names = [ch.name for ch in div.children if not isinstance(ch, str)]
        self.assertEqual(names, ["br"])

    def test_class_attr_returns_list(self):
        root = c.parse_html('<a class="x y">t</a>')
        self.assertEqual(root.find("a").get("class"), ["x", "y"])

    def test_find_all_recursive_flag(self):
        root = c.parse_html("<table><tr><td><table><tr><td>n</td></tr></table></td></tr></table>")
        outer = root.find("table")
        self.assertEqual(len(outer.find_all("tr", recursive=False)), 1)
        self.assertEqual(len(outer.find_all("tr", recursive=True)), 2)


class TableRowspanFlatten(unittest.TestCase):
    def test_rowspan_duplicates_into_subsequent_rows(self):
        html = """
        <table>
          <tr><td rowspan="3">Screen-1</td><td>case-1</td></tr>
          <tr><td>case-2</td></tr>
          <tr><td>case-3</td></tr>
        </table>
        """
        out = c._table_to_md(_table(html))
        self.assertIn("| Screen-1 | case-1 |", out)
        self.assertIn("| Screen-1 | case-2 |", out)
        self.assertIn("| Screen-1 | case-3 |", out)

    def test_nested_rowspan_screen_and_component(self):
        html = """
        <table>
          <tr><td rowspan="3">Screen</td><td rowspan="2">Btn-X</td><td>case-1</td></tr>
          <tr><td>case-2</td></tr>
          <tr><td>Btn-Y</td><td>case-3</td></tr>
        </table>
        """
        out = c._table_to_md(_table(html))
        # Screen 은 3행 모두, Btn-X 는 2행, Btn-Y 는 마지막 1행
        self.assertIn("| Screen | Btn-X | case-1 |", out)
        self.assertIn("| Screen | Btn-X | case-2 |", out)
        self.assertIn("| Screen | Btn-Y | case-3 |", out)


class TableColspan(unittest.TestCase):
    def test_colspan_keeps_text_in_first_column(self):
        html = """
        <table>
          <tr><th colspan="2">Header A-B</th><th>Header C</th></tr>
          <tr><td>a1</td><td>b1</td><td>c1</td></tr>
        </table>
        """
        out = c._table_to_md(_table(html))
        # colspan=2 인 헤더는 첫 칼럼에만 텍스트, 두 번째 칼럼은 빈 셀
        self.assertIn("| Header A-B |  | Header C |", out)
        self.assertIn("| a1 | b1 | c1 |", out)


class TableNestedFlatten(unittest.TestCase):
    """중첩 표는 외부 표 컬럼 폭주 방지를 위해 ` / ` 평탄화."""

    def test_nested_table_does_not_explode_columns(self):
        html = """
        <table>
          <tr><th>A</th><th>B</th></tr>
          <tr>
            <td>cell</td>
            <td><table><tr><td>x</td><td>y</td></tr></table></td>
          </tr>
        </table>
        """
        out = c._table_to_md(_table(html))
        # 외부 표는 2 컬럼 유지 (중첩 표가 컬럼을 부풀리면 안 됨)
        for line in out.strip().splitlines():
            self.assertEqual(line.count("|"), 3, f"외부 표가 2 컬럼이 아님: {line!r}")
        # 중첩 셀은 ` / ` 로 평탄화
        self.assertIn("x / y", out)


class TableCellEscape(unittest.TestCase):
    def test_pipe_in_cell_is_escaped(self):
        html = "<table><tr><td>a|b</td><td>c</td></tr></table>"
        out = c._table_to_md(_table(html))
        self.assertIn(r"a\|b", out)

    def test_br_in_cell_preserved_as_br_tag(self):
        html = "<table><tr><td><p>line1</p><p>line2</p></td><td>x</td></tr></table>"
        out = c._table_to_md(_table(html))
        self.assertIn("line1<br>line2", out)


class InlineMarkup(unittest.TestCase):
    def test_bold_italic_preserved(self):
        root = c.parse_html("<p>hello <strong>bold</strong> and <em>em</em>.</p>")
        out = c._inline_md(root.find("p"))
        self.assertIn("**bold**", out)
        self.assertIn("_em_", out)

    def test_link_preserved(self):
        root = c.parse_html('<p>see <a href="https://x">link</a></p>')
        out = c._inline_md(root.find("p"))
        self.assertIn("[link](https://x)", out)

    def test_user_mention_renders_as_text_only(self):
        # confluence 멘션 링크는 class="user-mention" 로 표시됨 → 링크 텍스트만 남기고 URL 제거
        root = c.parse_html('<p>cc <a class="user-mention" href="/people/123">홍길동</a></p>')
        out = c._inline_md(root.find("p"))
        self.assertIn("홍길동", out)
        self.assertNotIn("/people/123", out)


class SplitSections(unittest.TestCase):
    def test_empty_h1_group_heading_preserved(self):
        # "1. 배경 및 목적" 같은 H1 라벨은 본문 없이 H2 섹션을 묶기만 함 → 보존되어야 함
        html = """
        <h1>그룹헤딩</h1>
        <h2>하위1</h2>
        <p>내용1</p>
        """
        soup = c.parse_html(html)
        sections = c.split_sections(soup)
        headings = [s["heading"] for s in sections]
        self.assertIn("그룹헤딩", headings)
        self.assertIn("하위1", headings)


class ExtractPageId(unittest.TestCase):
    def test_numeric_id(self):
        self.assertEqual(c.extract_page_id("5426020353"), "5426020353")

    def test_full_url(self):
        url = "https://example.atlassian.net/wiki/spaces/~xxx/pages/5426020353/title-slug"
        self.assertEqual(c.extract_page_id(url), "5426020353")

    def test_invalid_input_raises(self):
        with self.assertRaises(ValueError):
            c.extract_page_id("not-a-page")


class HtmlToMdIntegration(unittest.TestCase):
    def test_style_block_is_stripped(self):
        # _node_to_md 가 style 태그를 무시하는지 (cmd_fetch 의 사전 strip 과는 별개의 안전망)
        soup = c.parse_html("<div><style>.x{}</style><p>text</p></div>")
        out = c.html_to_md(soup)
        self.assertNotIn(".x{}", out)
        self.assertIn("text", out)


# ---------------------------------------------------------------------------
# search_docs — context-search 랭커 공유 (D4/C4, #24)
# ---------------------------------------------------------------------------
def _write_md(tmp_dir: str, name: str, text: str) -> None:
    (Path(tmp_dir) / name).write_text(text, encoding="utf-8")


class SearchDocsRanked(unittest.TestCase):
    """랭커 로드 성공 경로 — 점수순 정렬·상한·match_pos."""

    @classmethod
    def setUpClass(cls):
        cls.ranker = c._load_context_search()
        assert cls.ranker is not None, "context-search.py 랭커 로드 실패 — 테스트 전제 조건"

    def test_heading_match_ranks_before_body_only_match(self):
        tmp = tempfile.mkdtemp()
        _write_md(
            tmp, "a.md",
            "# A\n\n"
            "## Heading keyword\n\nbody without the term.\n\n"
            "## Other section\n\nbody mentions keyword only here.\n",
        )
        md_files = sorted(Path(tmp).glob("*.md"))
        results, total = c.search_docs(md_files, "keyword", limit=5, ranker=self.ranker)
        self.assertEqual(total, 2)
        self.assertEqual(results[0]["heading"], "## Heading keyword")

    def test_limit_caps_results_but_total_reflects_all_matches(self):
        tmp = tempfile.mkdtemp()
        body = "\n".join(f"## Section {i} keyword\n\nbody keyword text {i}.\n" for i in range(7))
        _write_md(tmp, "many.md", body)
        md_files = sorted(Path(tmp).glob("*.md"))
        results, total = c.search_docs(md_files, "keyword", limit=5, ranker=self.ranker)
        self.assertEqual(total, 7)
        self.assertEqual(len(results), 5)

    def test_match_pos_zero_when_signal_is_not_literal_text(self):
        # 점수는 파일명(path_tokens="doctor")에서만 나오고 헤딩·본문 텍스트에는
        # "doctor" 가 literal 하게 없음 — match_pos 는 0 으로 폴백(C4-2).
        tmp = tempfile.mkdtemp()
        _write_md(tmp, "doctor.md", "## Other Title\n\nno mention of that word here either.\n")
        md_files = sorted(Path(tmp).glob("*.md"))
        results, total = c.search_docs(md_files, "doctor", limit=5, ranker=self.ranker)
        self.assertEqual(total, 1)
        self.assertEqual(results[0]["match_pos"], 0)

    def test_match_pos_finds_first_boundary_match_in_body(self):
        tmp = tempfile.mkdtemp()
        _write_md(tmp, "h.md", "## Something\n\nintro noise keyword appears here in body.\n")
        md_files = sorted(Path(tmp).glob("*.md"))
        results, total = c.search_docs(md_files, "keyword", limit=5, ranker=self.ranker)
        self.assertEqual(total, 1)
        pos = results[0]["match_pos"]
        self.assertTrue(results[0]["content"].lower()[pos:].startswith("keyword"))


class SearchDocsFallback(unittest.TestCase):
    """substring 폴백 경로 (C4-1) — 로드 실패는 WARN 1줄, 토큰 0개는 무음."""

    def test_ranker_none_falls_back_to_substring_with_warn(self):
        tmp = tempfile.mkdtemp()
        _write_md(tmp, "a.md", "## Heading\n\nbody keyword text.\n")
        md_files = sorted(Path(tmp).glob("*.md"))
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            results, total = c.search_docs(md_files, "keyword", limit=5, ranker=None)
        self.assertEqual(total, 1)
        self.assertIn("[WARN]", err.getvalue())
        self.assertIn("context-search", err.getvalue())

    def test_single_char_query_falls_back_silently(self):
        tmp = tempfile.mkdtemp()
        _write_md(tmp, "a.md", "## Heading\n\nbody keyword text.\n")
        md_files = sorted(Path(tmp).glob("*.md"))
        ranker = c._load_context_search()
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            results, total = c.search_docs(md_files, "k", limit=5, ranker=ranker)
        self.assertEqual(err.getvalue(), "")  # 로드는 성공했으므로 WARN 없음
        self.assertEqual(total, 1)  # "k" 는 "keyword" 의 substring


if __name__ == "__main__":
    unittest.main()
