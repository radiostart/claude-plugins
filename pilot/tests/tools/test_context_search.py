"""
tools/context-search.py 의 토큰화 / 섹션 분할 / 채점 / 순위 / CLI 단위 테스트
+ `pilot/tests/fixtures/context-search/` 스냅샷 기반 골든 hit@3 테스트 (6질의).

실행:
    python3 tests/tools/test_context_search.py
"""

import importlib.util
import io
import json
import os
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "context-search.py"
FIXTURE_ROOT = PLUGIN_ROOT / "tests" / "fixtures" / "context-search" / "workspace"


def _load_mod():
    spec = importlib.util.spec_from_file_location("context_search_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    # Python 3.13: exec 전에 sys.modules 등록 — @dataclass 의 __module__ 해석에 필요
    # (test_auto_pilot.py 선례).
    sys.modules["context_search_mod"] = module
    spec.loader.exec_module(module)
    return module


m = _load_mod()


# ---------------------------------------------------------------------------
# 토큰화
# ---------------------------------------------------------------------------
class Tokenize(unittest.TestCase):
    def test_camelcase_splits_into_parts_and_original(self):
        self.assertEqual(
            m.tokenize("CyberBongoRegister"),
            ["cyber", "bongo", "register", "cyberbongoregister"],
        )

    def test_korean_splits_on_whitespace_only_no_morpheme_split(self):
        # "배송취소 서비스" 는 공백 기준 정확히 2토큰 — 형태소 분리 없음
        self.assertEqual(m.tokenize("배송취소 서비스"), ["배송취소", "서비스"])

    def test_single_char_and_stopwords_removed(self):
        toks = m.tokenize("a the x 것 quick")
        self.assertNotIn("a", toks)
        self.assertNotIn("the", toks)
        self.assertNotIn("x", toks)
        self.assertNotIn("것", toks)
        self.assertIn("quick", toks)

    def test_lowercase_and_order_preserving_dedupe(self):
        self.assertEqual(m.tokenize("Load load LOAD data"), ["load", "data"])

    def test_separators_split_tokens(self):
        self.assertEqual(m.tokenize("orchestrate-load.py:463"), ["orchestrate", "load", "py", "463"])

    def test_empty_text_returns_empty(self):
        self.assertEqual(m.tokenize(""), [])


class PathTokens(unittest.TestCase):
    def test_strips_extension_of_last_segment_only(self):
        self.assertEqual(m.path_tokens("pilot/index.md"), ["pilot", "index"])

    def test_no_extension_pollution_for_py(self):
        toks = m.path_tokens("pilot/tools/orchestrate-load.py")
        self.assertNotIn("py", toks)
        self.assertIn("orchestrate", toks)
        self.assertIn("load", toks)

    def test_single_segment_no_slash(self):
        self.assertEqual(m.path_tokens("config.md"), ["config"])


# ---------------------------------------------------------------------------
# 질의 파싱
# ---------------------------------------------------------------------------
class ParseQueryTest(unittest.TestCase):
    def test_select_with_heading(self):
        q = m.parse_query("select:pilot/index.md#Cluster")
        self.assertEqual(q.kind, "select")
        self.assertEqual(q.select_path, "pilot/index.md")
        self.assertEqual(q.select_heading, "Cluster")

    def test_select_without_heading(self):
        q = m.parse_query("select:pilot/index.md")
        self.assertEqual(q.kind, "select")
        self.assertIsNone(q.select_heading)

    def test_required_prefix_tokenized_into_required(self):
        q = m.parse_query("+orchestrate-load domain")
        self.assertIn("orchestrate", q.required)
        self.assertIn("load", q.required)
        self.assertIn("domain", q.optional)

    def test_path_like_word_recorded_in_raw_paths(self):
        q = m.parse_query("app/services/x.rb")
        self.assertIn("app/services/x.rb", q.raw_paths)
        self.assertIn("app", q.optional)
        self.assertIn("services", q.optional)

    def test_empty_or_stopword_only_yields_zero_tokens(self):
        q = m.parse_query("the a")
        self.assertEqual(q.optional, [])
        self.assertEqual(q.required, [])


# ---------------------------------------------------------------------------
# 섹션 분할
# ---------------------------------------------------------------------------
class SplitSectionsTest(unittest.TestCase):
    def test_h2_h3_line_ranges_1_based_inclusive(self):
        text = "# Title\n\n## A\nbody a\n\n## B\nbody b\n"
        secs = m.split_sections(text, "f.md")
        by_heading = {s.heading: s for s in secs}
        # "# Title" 은 line 1, "## A" 는 line 3
        self.assertEqual(by_heading["A"].line_start, 3)
        self.assertEqual(by_heading["A"].line_end, 5)  # "## B" 직전(빈 줄 포함)
        self.assertEqual(by_heading["B"].line_start, 6)
        self.assertEqual(by_heading["B"].line_end, 7)

    def test_h2_body_includes_nested_h3(self):
        text = "## Parent\nintro\n### Child\nchild body\n## Next\nx\n"
        secs = m.split_sections(text, "f.md")
        parent = next(s for s in secs if s.heading == "Parent")
        self.assertIn("### Child", parent.body_lines)
        self.assertIn("child body", parent.body_lines)
        child = next(s for s in secs if s.heading == "Child")
        self.assertEqual(child.level, 3)

    def test_hash_inside_fence_is_not_a_heading(self):
        text = "## Real\n```python\n# not a heading\n```\nbody\n"
        secs = m.split_sections(text, "f.md")
        self.assertEqual([s.heading for s in secs], ["Real"])

    def test_indented_fence_also_hides_hash(self):
        text = "## Real\n  ```\n  # also not a heading\n  ```\nbody\n"
        secs = m.split_sections(text, "f.md")
        self.assertEqual([s.heading for s in secs], ["Real"])

    def test_frontmatter_excluded_and_description_kept(self):
        text = '---\ndescription: "설명입니다"\n---\n## A\nbody\n'
        secs = m.split_sections(text, "f.md")
        self.assertEqual(len(secs), 1)
        self.assertEqual(secs[0].description, "설명입니다")
        self.assertNotIn("description:", "\n".join(secs[0].body_lines))

    def test_no_frontmatter_description_is_none(self):
        secs = m.split_sections("## A\nbody\n", "f.md")
        self.assertIsNone(secs[0].description)

    def test_h1_only_file_is_single_section(self):
        secs = m.split_sections("# Only Title\n\nbody text.\n", "f.md")
        self.assertEqual(len(secs), 1)
        self.assertEqual(secs[0].heading, "Only Title")
        self.assertEqual(secs[0].level, 1)
        self.assertNotIn("# Only Title", secs[0].body_lines)

    def test_no_heading_file_is_whole_file_section(self):
        secs = m.split_sections("just text\nmore text\n", "f.md")
        self.assertEqual(len(secs), 1)
        self.assertEqual(secs[0].heading, "(파일 전체)")
        self.assertEqual(secs[0].level, 1)

    def test_preface_before_first_h2_indexed_as_level_1(self):
        text = "# Title\n\npreface body text.\n\n## A\nbody\n"
        secs = m.split_sections(text, "f.md")
        preface = next(s for s in secs if s.level == 1)
        self.assertEqual(preface.heading, "Title")
        self.assertIn("preface body text.", preface.body_lines)

    def test_preface_omitted_when_empty(self):
        text = "# Title\n## A\nbody\n"
        secs = m.split_sections(text, "f.md")
        self.assertEqual([s.level for s in secs], [2])

    def test_no_h1_preface_labeled_seomun(self):
        text = "some intro without h1\n\n## A\nbody\n"
        secs = m.split_sections(text, "f.md")
        preface = next(s for s in secs if s.level == 1)
        self.assertEqual(preface.heading, "(서문)")


# ---------------------------------------------------------------------------
# 인용 경로 추출
# ---------------------------------------------------------------------------
class ExtractCitationsTest(unittest.TestCase):
    def test_extracts_path_and_strips_line_suffix(self):
        tokens, paths = m.extract_citations("참조: pilot/tools/doctor.py:36 확인")
        self.assertIn("pilot/tools/doctor.py", paths)
        self.assertIn("doctor", tokens)

    def test_extracts_line_range_suffix(self):
        _tokens, paths = m.extract_citations("app/services/x.rb:12-20 범위")
        self.assertIn("app/services/x.rb", paths)

    def test_no_citation_returns_empty(self):
        tokens, paths = m.extract_citations("그냥 본문 텍스트")
        self.assertEqual(tokens, set())
        self.assertEqual(paths, [])

    def test_memo_presence_does_not_change_result(self):
        body = "cite pilot/tools/doctor.py:1 twice pilot/tools/doctor.py:2"
        t1, p1 = m.extract_citations(body, memo=None)
        t2, p2 = m.extract_citations(body, memo={})
        self.assertEqual(t1, t2)
        self.assertEqual(p1, p2)


# ---------------------------------------------------------------------------
# 점수
# ---------------------------------------------------------------------------
class ScoreTextTest(unittest.TestCase):
    def _q(self, raw):
        return m.parse_query(raw)

    def test_heading_exact_match(self):
        score, matched = m.score_text(self._q("doctor"), heading="doctor", body="")
        self.assertEqual(score, m.SCORE["heading_exact"])
        self.assertEqual(matched, ["doctor"])

    def test_heading_exact_suppresses_partial(self):
        # heading 이 정확히 "doctor" 이면 부분 일치(+5) 는 가산되지 않는다.
        score, _ = m.score_text(self._q("doctor"), heading="doctor", body="")
        self.assertEqual(score, 10)

    def test_heading_partial_only(self):
        score, matched = m.score_text(self._q("doc"), heading="doctor tool", body="")
        # "doc" 이 1글자 초과이므로 유지되고, "doctor" 헤딩 토큰과 정확 일치는 아님
        self.assertEqual(score, m.SCORE["heading_partial"])
        self.assertEqual(matched, ["doc"])

    def test_path_signal(self):
        score, _ = m.score_text(self._q("pilot"), heading="", body="", path_tokens={"pilot", "index"})
        self.assertEqual(score, m.SCORE["path"])

    def test_citation_signal(self):
        score, _ = m.score_text(self._q("doctor"), heading="", body="", citation_tokens={"doctor"})
        self.assertEqual(score, m.SCORE["citation"])

    def test_description_signal_boundary(self):
        score, _ = m.score_text(self._q("검색"), heading="", body="", description="검색 도구입니다")
        self.assertEqual(score, m.SCORE["description"])

    def test_body_signal_boundary(self):
        score, _ = m.score_text(self._q("검색"), heading="", body="검색 도구입니다")
        self.assertEqual(score, m.SCORE["body"])

    def test_frequency_not_counted(self):
        score, _ = m.score_text(self._q("load"), heading="", body="load load load")
        self.assertEqual(score, m.SCORE["body"])  # 3회 등장해도 2점

    def test_ascii_requires_both_boundaries(self):
        score, _ = m.score_text(self._q("load"), heading="", body="payload here")
        self.assertEqual(score, 0)  # "load" 는 "payload" 의 부분이라 매칭 안 됨

    def test_korean_left_boundary_allows_trailing_particle(self):
        score, matched = m.score_text(self._q("섹션"), heading="", body="이 섹션을 확인한다")
        self.assertEqual(score, m.SCORE["body"])
        self.assertEqual(matched, ["섹션"])

    def test_korean_left_boundary_blocks_prefix_attachment(self):
        score, _ = m.score_text(self._q("섹션"), heading="", body="가섹션 텍스트")
        self.assertEqual(score, 0)

    def test_raw_path_suffix_match_bonus(self):
        query = self._q("+services/x.rb")
        # 실전에서는 citation_tokens/citation_paths 가 extract_citations() 로 함께
        # 나온다 — required 게이트(D6)를 만족시키려면 constituent 토큰("services")
        # 도 신호를 받아야 하므로 citation_tokens 를 함께 전달한다.
        score, matched = m.score_text(
            query, heading="", body="",
            citation_tokens={"app", "services"},
            citation_paths=["app/services/x.rb"],
        )
        self.assertIn("services/x.rb", matched)
        # citation(+6, "services" 토큰) + raw-path suffix 보너스(+6) = 12
        self.assertGreaterEqual(score, m.SCORE["citation"] * 2)

    def test_required_token_gates_whole_score_to_zero(self):
        query = self._q("+missing present")
        score, matched = m.score_text(query, heading="", body="present here")
        self.assertEqual(score, 0)
        # 진단용 matched 는 개별 신호가 있던 토큰(present)을 그대로 보존
        self.assertIn("present", matched)

    def test_required_only_query_still_scores_when_satisfied(self):
        query = self._q("+doctor")
        score, _ = m.score_text(query, heading="doctor", body="")
        self.assertEqual(score, m.SCORE["heading_exact"])

    def test_level1_section_gets_no_heading_signal_via_score_section(self):
        sec = m.Section(
            file="f.md", heading="pilot skills", level=1,
            line_start=1, line_end=3, body_lines=["intro text"], description=None,
        )
        query = self._q("pilot")
        score, _ = m.score_section(sec, query)
        # heading="pilot skills" 였다면 부분 일치(+5)를 받았겠지만 level 1 은 0
        self.assertEqual(score, 0)

    def test_level23_section_gets_heading_signal_via_score_section(self):
        sec = m.Section(
            file="f.md", heading="pilot skills", level=2,
            line_start=1, line_end=3, body_lines=["intro text"], description=None,
        )
        query = self._q("pilot")
        score, _ = m.score_section(sec, query)
        self.assertGreaterEqual(score, m.SCORE["heading_partial"])


# ---------------------------------------------------------------------------
# 순위
# ---------------------------------------------------------------------------
class RankTest(unittest.TestCase):
    def _sec(self, file, heading, level, line_start=1):
        return m.Section(
            file=file, heading=heading, level=level,
            line_start=line_start, line_end=line_start + 1,
            body_lines=[], description=None,
        )

    def test_tie_break_h2_before_h3_before_level1_before_index_before_path(self):
        h3 = self._sec("b.md", "H3", 3)
        h2 = self._sec("c.md", "H2", 2)
        l1 = self._sec("a.md", "L1", 1)
        idx = self._sec("index.md", "Idx", 1)
        scored = [(h3, 5, []), (h2, 5, []), (l1, 5, []), (idx, 5, [])]
        ordered = m.rank(scored, limit=10)
        self.assertEqual([s.heading for s, _, _ in ordered], ["H2", "H3", "Idx", "L1"])

    def test_path_ascending_tiebreak(self):
        b = self._sec("b.md", "H", 2)
        a = self._sec("a.md", "H", 2)
        ordered = m.rank([(b, 5, []), (a, 5, [])], limit=10)
        self.assertEqual([s.file for s, _, _ in ordered], ["a.md", "b.md"])

    def test_entry_rel_counts_as_entry(self):
        entry = self._sec("orders/index.md", "E", 2)
        other = self._sec("orders/other.md", "O", 2)
        ordered = m.rank(
            [(other, 5, []), (entry, 5, [])], limit=10, entry_rel={"orders/index.md"}
        )
        # is_entry 는 동점자 사이 우선순위만 바꾸므로 file 정렬보다 먼저 적용됨을 확인
        self.assertEqual(ordered[0][0].file, "orders/index.md")

    def test_limit_applied(self):
        secs = [self._sec(f"{i}.md", "H", 2) for i in range(5)]
        scored = [(s, 10 - i, []) for i, s in enumerate(secs)]
        ordered = m.rank(scored, limit=2)
        self.assertEqual(len(ordered), 2)


# ---------------------------------------------------------------------------
# 스니펫 · read_hint
# ---------------------------------------------------------------------------
class SnippetReadHintTest(unittest.TestCase):
    def test_snippet_capped_at_240_and_contains_matched_token(self):
        body = "x" * 300 + " keyword " + "y" * 300
        sec = m.Section(
            file="f.md", heading="H", level=2, line_start=1, line_end=2,
            body_lines=[body], description=None,
        )
        snippet = m.build_snippet(sec, ["keyword"])
        self.assertLessEqual(len(snippet), m.SNIPPET_CHARS + 2)  # 좌우 … 여유
        self.assertIn("keyword", snippet)

    def test_snippet_falls_back_to_prefix_when_no_body_match(self):
        sec = m.Section(
            file="f.md", heading="H", level=2, line_start=1, line_end=2,
            body_lines=["only heading or path matched, no body hit here"], description=None,
        )
        snippet = m.build_snippet(sec, ["nonexistent"])
        self.assertTrue(body_starts := snippet.startswith("only heading"))

    def test_read_hint_format(self):
        sec = m.Section(
            file="f.md", heading="H", level=2, line_start=10, line_end=15,
            body_lines=[], description=None,
        )
        self.assertEqual(m.build_read_hint(sec, "f.md"), "Read f.md offset=10 limit=6")

    def test_large_section_hint(self):
        sec = m.Section(
            file="f.md", heading="H", level=2, line_start=1, line_end=401,
            body_lines=[], description=None,
        )
        hint = m.build_read_hint(sec, "f.md")
        self.assertIn("섹션이 크다(401줄)", hint)
        self.assertIn("limit=80", hint)


# ---------------------------------------------------------------------------
# collect_files — traversal / scope / include / symlink / dedupe
# ---------------------------------------------------------------------------
class CollectFilesTest(unittest.TestCase):
    def _ws(self, td):
        ws = Path(td)
        (ws / "context").mkdir(parents=True)
        return ws

    def test_missing_corpus_root_raises(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)  # context/ 없음
            with self.assertRaises(m.SearchError) as cm:
                m.collect_files(ws, None, None, None)
            self.assertEqual(cm.exception.exit_code, 2)

    def test_scope_traversal_dotdot_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td)
            with self.assertRaises(m.SearchError) as cm:
                m.collect_files(ws, "../projects", None, None)
            self.assertEqual(cm.exception.exit_code, 2)
            self.assertIn("../projects", cm.exception.message)

    def test_scope_traversal_absolute_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td)
            with self.assertRaises(m.SearchError):
                m.collect_files(ws, "/etc", None, None)

    def test_project_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td)
            with self.assertRaises(m.SearchError):
                m.collect_files(ws, None, None, "../x")

    def test_traversal_rejected_even_when_orchestrate_load_unavailable(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td)
            orig = m._load_orchestrate_load
            m._load_orchestrate_load = lambda: None
            try:
                with self.assertRaises(m.SearchError):
                    m.collect_files(ws, "../x", None, None)
            finally:
                m._load_orchestrate_load = orig

    def test_include_absolute_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td)
            with self.assertRaises(m.SearchError):
                m.collect_files(ws, None, ["/etc"], None)

    def test_include_dotdot_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td)
            with self.assertRaises(m.SearchError):
                m.collect_files(ws, None, ["../../x"], None)

    def test_scope_folder_and_entry_and_boundaries_both_directions(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td)
            (ws / "context" / "alpha").mkdir()
            (ws / "context" / "alpha" / "index.md").write_text("## A\nx\n", encoding="utf-8")
            (ws / "context" / "beta").mkdir()
            (ws / "context" / "beta" / "index.md").write_text("## B\nx\n", encoding="utf-8")
            (ws / "context" / "boundaries").mkdir()
            (ws / "context" / "boundaries" / "alpha--beta.md").write_text("x", encoding="utf-8")
            (ws / "context" / "boundaries" / "gamma--alpha.md").write_text("x", encoding="utf-8")
            (ws / "context" / "boundaries" / "gamma--beta.md").write_text("x", encoding="utf-8")

            files, _info, _entries = m.collect_files(ws, "alpha", None, None)
            names = {str(p.relative_to(ws)) for p in files}
            self.assertIn(os.path.join("context", "alpha", "index.md"), names)
            self.assertIn(os.path.join("context", "boundaries", "alpha--beta.md"), names)
            self.assertIn(os.path.join("context", "boundaries", "gamma--alpha.md"), names)
            self.assertNotIn(os.path.join("context", "beta", "index.md"), names)
            self.assertNotIn(os.path.join("context", "boundaries", "gamma--beta.md"), names)

    def test_unregistered_scope_falls_back_to_whole_corpus_with_info(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td)
            (ws / "context" / "somefile.md").write_text("## X\nx\n", encoding="utf-8")
            files, info, _entries = m.collect_files(ws, "unregistered", None, None)
            self.assertTrue(any("MANIFEST/폴더에 없음" in i for i in info))
            self.assertTrue(any(p.name == "somefile.md" for p in files))

    def test_scope_dedupes_entry_inside_scope_folder(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td)
            (ws / "context" / "alpha").mkdir()
            (ws / "context" / "alpha" / "index.md").write_text("## A\nx\n", encoding="utf-8")
            (ws / "context" / "MANIFEST.md").write_text(
                "## 도메인 분류\n\n| 도메인 | 진입 파일 | 설명 |\n| --- | --- | --- |\n"
                "| alpha | `alpha/index.md` | a |\n",
                encoding="utf-8",
            )
            files, _info, entries = m.collect_files(ws, "alpha", None, None)
            # alpha/index.md 는 폴더 스캔과 MANIFEST 진입 파일 양쪽에서 잡히지만 1회만
            matches = [p for p in files if p.name == "index.md"]
            self.assertEqual(len(matches), 1)
            self.assertEqual(len(entries), 1)

    def test_include_resolves_under_project_features(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td)
            (ws / "projects" / "P" / "features").mkdir(parents=True)
            (ws / "projects" / "P" / "features" / "01-x.md").write_text("## F\nx\n", encoding="utf-8")
            files, _info, _entries = m.collect_files(ws, None, ["features"], "P")
            self.assertTrue(any(p.name == "01-x.md" for p in files))

    def test_include_missing_target_produces_info_skip(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td)
            _files, info, _entries = m.collect_files(ws, None, ["nope"], None)
            self.assertTrue(any("nope" in i and "skip" in i for i in info))

    def test_symlinked_directory_escape_excluded_with_info(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as ext:
            ws = self._ws(td)
            (ws / "context" / "legit.md").write_text("## L\nx\n", encoding="utf-8")
            ext_path = Path(ext)
            (ext_path / "x.md").write_text("## Evil\nx\n", encoding="utf-8")
            os.symlink(ext_path, ws / "context" / "evil")

            files, info, _entries = m.collect_files(ws, None, None, None)
            names = {p.name for p in files}
            self.assertNotIn("x.md", names)
            self.assertIn("legit.md", names)
            self.assertTrue(any("코퍼스 밖 링크 1건 제외" in i for i in info))


# ---------------------------------------------------------------------------
# search() — select / zero-hit / limit / determinism
# ---------------------------------------------------------------------------
class SearchTest(unittest.TestCase):
    def _corpus(self, td):
        ws = Path(td)
        ctx = ws / "context"
        ctx.mkdir(parents=True)
        (ctx / "a.md").write_text("## Alpha keyword\n\nbody alpha keyword text.\n", encoding="utf-8")
        (ctx / "b.md").write_text("## Beta other\n\nbody beta other text.\n", encoding="utf-8")
        return ws

    def test_empty_query_raises_with_usage_flag(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._corpus(td)
            with self.assertRaises(m.SearchError) as cm:
                m.search(workspace=ws, project=None, scope=None, includes=None, query_raw="the a", limit=5)
            self.assertEqual(cm.exception.exit_code, 2)
            self.assertTrue(cm.exception.show_usage)

    def test_limit_below_one_raises(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._corpus(td)
            with self.assertRaises(m.SearchError):
                m.search(workspace=ws, project=None, scope=None, includes=None, query_raw="keyword", limit=0)

    def test_limit_above_max_clamped_with_info(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._corpus(td)
            result = m.search(
                workspace=ws, project=None, scope=None, includes=None,
                query_raw="keyword", limit=25,
            )
            self.assertTrue(any("최대값" in i for i in result["info"]))

    def test_zero_hit_reports_token_hits_and_guidance(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._corpus(td)
            result = m.search(
                workspace=ws, project=None, scope="pilot", includes=None,
                query_raw="totallyabsentword", limit=5,
            )
            self.assertEqual(result["returned"], 0)
            self.assertIsNotNone(result["zero_hit"])
            self.assertIn("totallyabsentword", result["zero_hit"]["token_hits"])
            self.assertTrue(any("scope" in g for g in result["zero_hit"]["guidance"]))

    def test_zero_hit_josa_guidance_never_doubles_particle(self):
        # C8 안내 예시 — 토큰이 조사로 끝나면 그 토큰을, 아니면 고정 예시를 쓴다 (`섹션을을` 이중 조사 회귀 방지)
        q = m.parse_query("zzqq 섹션을")
        guidance = m.build_zero_hit("zzqq 섹션을", q, {"zzqq": 0, "섹션을": 0}, None, False)["guidance"]
        josa_line = next(g for g in guidance if "조사" in g)
        self.assertIn("`섹션을` → `섹션`", josa_line)
        self.assertNotIn("을을", josa_line)
        q2 = m.parse_query("zzqq 섹션")
        guidance2 = m.build_zero_hit("zzqq 섹션", q2, {"zzqq": 0, "섹션": 0}, None, False)["guidance"]
        self.assertIn("`섹션을` → `섹션`", next(g for g in guidance2 if "조사" in g))

    def test_select_returns_all_sections_of_file(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._corpus(td)
            result = m.search(
                workspace=ws, project=None, scope=None, includes=None,
                query_raw="select:a.md", limit=5,
            )
            self.assertEqual(result["returned"], 1)
            self.assertIsNone(result["results"][0]["score"])

    def test_select_missing_file_returns_suggestions(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._corpus(td)
            result = m.search(
                workspace=ws, project=None, scope=None, includes=None,
                query_raw="select:aa.md", limit=5,
            )
            self.assertEqual(result["returned"], 0)
            self.assertLessEqual(len(result["zero_hit"]["suggestions"]), 3)

    def test_select_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._corpus(td)
            with self.assertRaises(m.SearchError):
                # workspace 밖으로 나가는 대상만 거부 — `../x` 는 workspace/x 라 include 후보와 같은 층위 (C4)
                m.search(workspace=ws, project=None, scope=None, includes=None, query_raw="select:../../x", limit=5)

    def test_determinism_same_directory_reversed_creation_order(self):
        import shutil

        files = {
            "a.md": "## Alpha keyword\n\nbody alpha keyword text.\n",
            "b.md": "## Beta keyword\n\nbody beta keyword text.\n",
            "pilot/c.md": "## Gamma keyword\n\nbody gamma keyword text.\n",
        }
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            ctx = ws / "context"

            def write(order):
                if ctx.exists():
                    shutil.rmtree(ctx)
                ctx.mkdir()
                (ctx / "pilot").mkdir()
                for name in order:
                    (ctx / name).write_text(files[name], encoding="utf-8")

            write(["a.md", "b.md", "pilot/c.md"])
            r1 = m.search(workspace=ws, project=None, scope=None, includes=None, query_raw="keyword", limit=5)
            write(["pilot/c.md", "b.md", "a.md"])
            r2 = m.search(workspace=ws, project=None, scope=None, includes=None, query_raw="keyword", limit=5)
            self.assertEqual(
                json.dumps(r1, ensure_ascii=False), json.dumps(r2, ensure_ascii=False)
            )


class PerformanceTest(unittest.TestCase):
    def test_1000_sections_korean_joined_query_under_one_second(self):
        # C6 — G3 게이트가 ASCII 질의만 재던 빈틈: 붙여 쓴 4자+ 한글 5토큰(E2·E4 경로)도 같은 상한.
        words = "선발송 접수 상태 확인 규칙과 도메인 진입 파일 로드 순서를 정합성 검사 이후에 반영한다".split()
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            ctx = ws / "context"
            ctx.mkdir(parents=True)
            for i in range(200):
                lines = [f"# 파일 {i}", ""]
                for s in range(5):
                    lines.append(f"## 섹션 {i}-{s} keyword{s}")
                    lines.append(" ".join(words[(i + s + k) % len(words)] for k in range(160)))
                    lines.append(" ".join(f"app/services/mod{i}_{s}_{c}.rb:{c + 1}" for c in range(6)))
                    lines.append("")
                (ctx / f"file{i}.md").write_text("\n".join(lines), encoding="utf-8")
            start = time.time()
            result = m.search(
                workspace=ws, project=None, scope=None, includes=None,
                query_raw="선발송접수 상태확인 도메인로드 진입파일 정합성검사", limit=5,
            )
            elapsed = time.time() - start
            self.assertGreater(result["candidates"], 0)
            self.assertLess(elapsed, 1.0)


    def test_1000_sections_high_citation_density_under_one_second(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            ctx = ws / "context"
            ctx.mkdir(parents=True)
            for i in range(200):
                lines = [f"# File {i}", ""]
                for s in range(5):
                    lines.append(f"## Section {i}-{s} keyword{s}")
                    lines.append("")
                    lines.append(
                        " ".join(f"app/services/mod{i}_{s}_{c}.rb:{c + 1}" for c in range(6))
                    )
                    lines.append("")
                (ctx / f"file{i}.md").write_text("\n".join(lines), encoding="utf-8")

            start = time.time()
            result = m.search(
                workspace=ws, project=None, scope=None, includes=None,
                query_raw="keyword2", limit=5,
            )
            elapsed = time.time() - start
            self.assertEqual(result["candidates"], 200)
            self.assertLess(elapsed, 1.0)


# ---------------------------------------------------------------------------
# CLI (main) — exit codes / --format
# ---------------------------------------------------------------------------
class MainCliTest(unittest.TestCase):
    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = m.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_missing_query_arg_returns_2(self):
        code, _out, _err = self._run([])
        self.assertEqual(code, 2)

    def test_bad_format_choice_returns_2(self):
        code, _out, err = self._run(["doctor", "--format", "xml"])
        self.assertEqual(code, 2)
        self.assertIn("--format", err)

    def test_empty_query_returns_2_with_usage(self):
        code, _out, err = self._run(["the a"])
        self.assertEqual(code, 2)
        self.assertIn("usage", err.lower())

    def test_traversal_scope_returns_2_with_stderr_message(self):
        code, _out, err = self._run(["doctor", "--scope", "../projects"])
        self.assertEqual(code, 2)
        self.assertIn("../projects", err)

    def test_traversal_absolute_scope_returns_2(self):
        code, _out, _err = self._run(["doctor", "--scope", "/etc"])
        self.assertEqual(code, 2)

    def test_traversal_project_returns_2(self):
        code, _out, _err = self._run(["doctor", "--project", "../x"])
        self.assertEqual(code, 2)

    def test_json_format_is_valid_json(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / "context").mkdir(parents=True)
            (ws / "context" / "a.md").write_text("## Keyword\nbody keyword text\n", encoding="utf-8")
            code, out, _err = self._run(["keyword", "--workspace", str(ws), "--format", "json"])
            self.assertEqual(code, 0)
            data = json.loads(out)
            self.assertIn("results", data)


# ---------------------------------------------------------------------------
# select: 다중 대상 (E8)
# ---------------------------------------------------------------------------
class SelectMultiTest(unittest.TestCase):
    def _corpus(self, td):
        ws = Path(td)
        ctx = ws / "context"
        ctx.mkdir(parents=True)
        (ctx / "a.md").write_text("## Alpha\nbody a\n", encoding="utf-8")
        (ctx / "b.md").write_text("## Beta\nbody b\n", encoding="utf-8")
        return ws

    def _search(self, ws, q, **kw):
        return m.search(workspace=ws, project=None, scope=None, includes=None, query_raw=q, limit=5, **kw)

    def test_parse_multi_targets_and_first_target_compat(self):
        q = m.parse_query("select:a.md#H1, b.md#H2,c.md")
        self.assertEqual(q.kind, "select")
        self.assertEqual(q.select_targets, [("a.md", "H1"), ("b.md", "H2"), ("c.md", None)])
        self.assertEqual((q.select_path, q.select_heading), ("a.md", "H1"))

    def test_multi_select_returns_targets_in_order(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._corpus(td)
            r = self._search(ws, "select:b.md,a.md")
            self.assertEqual([x["heading"] for x in r["results"]], ["Beta", "Alpha"])
            self.assertEqual(r["candidates"], 2)
            self.assertIsNone(r["zero_hit"])
            self.assertEqual(r["query"], "select:b.md,a.md")

    def test_multi_select_partial_missing_gives_info_not_zero_hit(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._corpus(td)
            r = self._search(ws, "select:a.md,zzz.md")
            self.assertEqual(r["returned"], 1)
            self.assertIsNone(r["zero_hit"])
            self.assertTrue(any("select 대상 없음: 'zzz.md'" in i for i in r["info"]), r["info"])

    def test_multi_select_all_missing_keeps_suggestions_shape(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._corpus(td)
            r = self._search(ws, "select:aa.md,bb.md")
            self.assertEqual(r["returned"], 0)
            self.assertIn("suggestions", r["zero_hit"])
            self.assertLessEqual(len(r["zero_hit"]["suggestions"]), 3)

    def test_single_select_heading_miss_keeps_guidance_shape(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._corpus(td)
            r = self._search(ws, "select:a.md#Nope")
            self.assertEqual(list(r["zero_hit"].keys()), ["guidance"])

    def test_multi_select_dedupes_same_section(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._corpus(td)
            r = self._search(ws, "select:a.md#Alpha,a.md")
            self.assertEqual(r["returned"], 1)

    def test_multi_select_traversal_in_any_target_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._corpus(td)
            with self.assertRaises(m.SearchError):
                self._search(ws, "select:a.md,../../x")

    def test_select_include_candidate_roundtrip(self):
        # C4 — --include 후보는 루트 기준으로 `../projects/...` 라 표시 경로·루트 기준 표기 양쪽으로 도달해야 한다.
        with tempfile.TemporaryDirectory() as td:
            ws = self._corpus(td)
            (ws / "projects" / "P" / "features").mkdir(parents=True)
            feat = ws / "projects" / "P" / "features" / "01-x.md"
            feat.write_text("## Feat\nfeature body\n", encoding="utf-8")
            kw = dict(workspace=ws, project="P", scope=None, includes=["features"], limit=5)
            shown = m._display_path(feat)
            r1 = m.search(query_raw=f"select:{shown}#Feat", **kw)
            self.assertEqual(r1["returned"], 1)
            self.assertEqual(r1["results"][0]["heading"], "Feat")
            r2 = m.search(query_raw="select:../projects/P/features/01-x.md", **kw)
            self.assertEqual(r2["returned"], 1)
            with self.assertRaises(m.SearchError):
                m.search(query_raw="select:../../etc/x.md", **kw)

    def test_select_empty_heading_after_hash_gives_info(self):
        # C1 — 쉘이 백틱을 치환해 `select:a.md#` 로 들어오면 파일 전체를 돌려주되 무음이 아니어야 한다.
        with tempfile.TemporaryDirectory() as td:
            ws = self._corpus(td)
            r = self._search(ws, "select:a.md#")
            self.assertEqual(r["returned"], 1)
            self.assertTrue(any("헤딩이 비어" in i and "작은따옴표" in i for i in r["info"]), r["info"])
            self.assertFalse(any("헤딩이 비어" in i for i in self._search(ws, "select:a.md")["info"]))

    def test_select_heading_match_ignores_backticks_and_emphasis(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / "context").mkdir(parents=True)
            (ws / "context" / "l.md").write_text(
                "## `/pilot:doctor`\nx\n## **Bold** _plan_\ny\n", encoding="utf-8"
            )
            for q in ("select:l.md#/pilot:doctor", "select:l.md#pilot:doctor", "select:l.md#`/pilot:doctor`"):
                r = self._search(ws, q)
                self.assertEqual([x["heading"] for x in r["results"]], ["`/pilot:doctor`"], q)
            r = self._search(ws, "select:l.md#bold plan")
            self.assertEqual(r["returned"], 1)

    def test_select_accepts_displayed_cwd_relative_path(self):
        # manifest/md 가 표시하는 CWD 기준 경로를 그대로 붙여 넣어도 코퍼스 루트 기준으로 정규화된다.
        with tempfile.TemporaryDirectory() as td:
            ws = self._corpus(td)
            shown = m._display_path(ws / "context" / "a.md")
            r = self._search(ws, f"select:{shown}#Alpha")
            self.assertEqual(r["returned"], 1)
            self.assertEqual(r["query"], "select:a.md#Alpha")
            with self.assertRaises(m.SearchError):
                self._search(ws, f"select:{m._display_path(ws / 'context')}/../../etc/x.md")


# ---------------------------------------------------------------------------
# --inject (E9)
# ---------------------------------------------------------------------------
class InjectTest(unittest.TestCase):
    def _ws(self, td, files):
        ws = Path(td)
        ctx = ws / "context"
        ctx.mkdir(parents=True)
        for name, text in files.items():
            (ctx / name).write_text(text, encoding="utf-8")
        return ws

    def _search(self, ws, q, **kw):
        return m.search(workspace=ws, project=None, scope=None, includes=None, query_raw=q, limit=5, **kw)

    def test_inject_adds_text_and_wrapper_block(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, {"a.md": "## Alpha\nbody a\n"})
            r = self._search(ws, "select:a.md#Alpha", inject=True)
            self.assertEqual(r["results"][0]["text"], "## Alpha\nbody a")
            self.assertFalse(r["results"][0]["truncated"])
            md = m.render_md(r)
            self.assertIn('<context-snippet file="', md)
            self.assertIn('heading="Alpha" lines="1-2">', md)
            self.assertIn("</context-snippet>", md)
            self.assertNotIn("1. >", md)

    def test_without_inject_output_has_no_text_key(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, {"a.md": "## Alpha\nbody a\n"})
            r = self._search(ws, "select:a.md#Alpha")
            self.assertNotIn("text", r["results"][0])
            self.assertNotIn("<context-snippet", m.render_md(r))

    def test_budget_truncates_with_rest_hint(self):
        with tempfile.TemporaryDirectory() as td:
            body = "\n".join("x" * 20 for _ in range(50))
            ws = self._ws(td, {"a.md": "## Alpha\n" + body + "\n"})
            r = self._search(ws, "select:a.md", inject=True, max_bytes=1200)
            res = r["results"][0]
            self.assertTrue(res["truncated"])
            self.assertLessEqual(len(m.render_md(r).encode("utf-8")), 1200)  # C8 — 렌더 총량이 상한 안
            self.assertTrue(res["inject_rest"].startswith("Read "))
            self.assertIn("offset=", res["inject_rest"])
            self.assertIn("[잘림 — 나머지: Read ", m.render_md(r))

    def test_budget_exhausted_skips_later_sections_with_info(self):
        with tempfile.TemporaryDirectory() as td:
            # 결과별 렌더 오버헤드(표/manifest 줄·래퍼·잘림/생략 줄)와 예비 600B 를 뗀 뒤 본문에 쓴다 —
            # 4,000B 면 오버헤드 ≈1,500B, 본문 예산 ≈2,500B: Alpha(1,500B) 는 들어가고 Beta 는 못 들어간다.
            ws = self._ws(td, {"a.md": "## Alpha\n" + "a" * 1500 + "\n## Beta\n" + "b" * 1500 + "\n"})
            r = self._search(ws, "select:a.md", inject=True, max_bytes=4000)
            self.assertNotEqual(r["results"][0]["text"], "")
            self.assertIn("inject_skip", r["results"][1])
            self.assertTrue(any("예산" in i for i in r["info"]), r["info"])
            self.assertIn("[2] ", m.render_md(r))
            self.assertLessEqual(len(m.render_md(r).encode("utf-8")), 4000)

    def test_rendered_md_and_manifest_within_max_bytes(self):
        # C8 — 상한은 본문 합이 아니라 md/manifest 렌더 총량(헤더·후보 줄·래퍼 포함)을 묶는다.
        with tempfile.TemporaryDirectory() as td:
            body = "\n".join("keyword 본문 line" for _ in range(60))  # 섹션당 ≈1.3KB, 여러 줄이라 부분 주입 가능
            files = {f"f{i}.md": f"## Keyword {i}\n" + body + "\n" for i in range(8)}
            ws = self._ws(td, files)
            r = m.search(workspace=ws, project=None, scope=None, includes=None, query_raw="keyword", limit=8,
                         inject=True, max_bytes=8000)
            self.assertLessEqual(len(m.render_md(r).encode("utf-8")), 8000)
            self.assertLessEqual(len(m.render_manifest(r, now=0).encode("utf-8")), 8000)
            self.assertTrue(any(x["text"] for x in r["results"]))
            self.assertTrue(any(x.get("inject_skip") for x in r["results"]))

    def test_section_capped_at_400_lines(self):
        with tempfile.TemporaryDirectory() as td:
            body = "\n".join(f"line {i}" for i in range(500))
            ws = self._ws(td, {"a.md": "## Alpha\n" + body + "\n"})
            r = self._search(ws, "select:a.md", inject=True, max_bytes=24000)
            res = r["results"][0]
            self.assertEqual(len(res["text"].splitlines()), m.LARGE_SECTION_LINES)
            self.assertTrue(res["truncated"])

    def test_child_h3_skipped_when_parent_h2_injected_first(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, {"a.md": "## Parent\nintro\n### Child\nchild body\n"})
            r = self._search(ws, "select:a.md", inject=True)
            parent, child = r["results"]
            self.assertIn("### Child", parent["text"])
            self.assertIn("중복", child["inject_skip"])
            self.assertEqual(child["text"], "")

    def test_child_first_then_parent_folds_child_range(self):
        # C5 — 키워드 질의에서는 H3 정확 일치(+10)가 H2(본문 +2)보다 앞선다. 뒤에 오는 부모는
        # 이미 주입된 자식 범위를 1줄 표지로 접어 본문 중복을 없앤다.
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, {"a.md": "## Parent zeta\nintro alpha child\n### Child alpha\nchild body\n"})
            r = m.search(workspace=ws, project=None, scope=None, includes=None,
                         query_raw="alpha child", limit=5, inject=True)
            child, parent = r["results"]
            self.assertEqual(child["heading"], "Child alpha")
            self.assertEqual(child["text"], "### Child alpha\nchild body")
            self.assertNotIn("child body", parent["text"])
            self.assertIn("[L3-4 는 [#1] 에 주입됨 — 생략]", parent["text"])
            self.assertIn("intro alpha child", parent["text"])
            self.assertFalse(parent["truncated"])
            self.assertEqual(m.render_md(r).count("child body"), 1)

    def test_select_reverse_order_folds_child(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, {"a.md": "## Parent\nintro\n### Child\nchild body\n"})
            r = self._search(ws, "select:a.md#Child,a.md#Parent", inject=True)
            child, parent = r["results"]
            self.assertEqual(child["text"], "### Child\nchild body")
            self.assertNotIn("child body", parent["text"])
            self.assertIn("에 주입됨", parent["text"])

    def test_folded_parent_truncation_rest_hint_uses_file_lines(self):
        # 접힌 표지 뒤에서 잘려도 inject_rest 의 offset 은 파일 라인 기준이어야 한다.
        with tempfile.TemporaryDirectory() as td:
            # 자식(L3-4) 뒤에 선택되지 않은 H3(L5~) 가 이어져 부모 본문 안에 남는다 — 표지(1줄)가 2줄을 대신하므로
            # 텍스트 k 줄을 실으면 마지막 파일 라인은 k + 1, 나머지 Read 는 k + 2 부터.
            tail = "\n".join("t" * 40 for _ in range(30))
            ws = self._ws(td, {"a.md": "## Parent\nintro\n### Child\nchild body\n### Other\n" + tail + "\n"})
            big = self._search(ws, "select:a.md#Child,a.md#Parent", inject=True)
            self.assertFalse(big["results"][1]["truncated"])
            self.assertIn("[L3-4 는 [#1] 에 주입됨 — 생략]", big["results"][1]["text"])
            r = self._search(ws, "select:a.md#Child,a.md#Parent", inject=True, max_bytes=1800)
            child, parent = r["results"]
            self.assertTrue(parent["truncated"], parent)
            kept_lines = parent["text"].count("\n") + 1
            self.assertGreaterEqual(kept_lines, 4)
            self.assertIn(f"offset={kept_lines + 2} ", parent["inject_rest"])

    def test_child_kept_when_parent_truncated_before_child(self):
        # 부모가 400줄 캡으로 잘려 자식 범위를 덮지 못하면 자식은 중복이 아니다 — 그대로 주입.
        with tempfile.TemporaryDirectory() as td:
            filler = "\n".join("p" for _ in range(450))
            ws = self._ws(td, {"a.md": "## Parent\n" + filler + "\n### Child\nchild body\n"})
            r = self._search(ws, "select:a.md", inject=True)
            parent, child = r["results"]
            self.assertTrue(parent["truncated"])
            self.assertNotIn("inject_skip", child)
            self.assertEqual(child["text"], "### Child\nchild body")

    def test_max_bytes_clamped_and_zero_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, {"a.md": "## Alpha\nbody\n"})
            r = self._search(ws, "select:a.md", inject=True, max_bytes=99_999)
            self.assertTrue(any(str(m.INJECT_MAX_BYTES_CAP) in i for i in r["info"]))
            with self.assertRaises(m.SearchError):
                self._search(ws, "select:a.md", inject=True, max_bytes=0)

    def test_wrapper_attribute_escaping(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, {"a.md": '## Say "hi" <b>\nbody\n'})
            r = self._search(ws, "select:a.md", inject=True)
            self.assertIn('heading="Say &quot;hi&quot; &lt;b&gt;"', m.render_md(r))

    def test_level1_preface_text_restores_h1(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, {"a.md": "# Title\n\npreface.\n\n## A\nx\n"})
            r = self._search(ws, "select:a.md#Title", inject=True)
            self.assertTrue(r["results"][0]["text"].startswith("# Title"))

    def test_keyword_query_inject_cli_default_limit_3(self):
        with tempfile.TemporaryDirectory() as td:
            files = {f"f{i}.md": f"## Keyword {i}\nkeyword body {i}\n" for i in range(5)}
            ws = self._ws(td, files)
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = m.main(["keyword", "--workspace", str(ws), "--inject", "--format", "json"])
            self.assertEqual(code, 0)
            data = json.loads(out.getvalue())
            self.assertEqual(data["returned"], m.INJECT_DEFAULT_LIMIT)
            self.assertTrue(all("text" in r for r in data["results"]))
            out2 = io.StringIO()
            with redirect_stdout(out2), redirect_stderr(io.StringIO()):
                m.main(["keyword", "--workspace", str(ws), "--format", "json"])
            self.assertEqual(json.loads(out2.getvalue())["returned"], m.DEFAULT_LIMIT)


# ---------------------------------------------------------------------------
# --format manifest (E10)
# ---------------------------------------------------------------------------
class ManifestTest(unittest.TestCase):
    def _ws(self, td, files):
        ws = Path(td)
        ctx = ws / "context"
        ctx.mkdir(parents=True)
        for name, text in files.items():
            (ctx / name).write_text(text, encoding="utf-8")
        return ws

    def _search(self, ws, q, **kw):
        return m.search(workspace=ws, project=None, scope=None, includes=None, query_raw=q, limit=5, **kw)

    def test_manifest_line_format(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, {"a.md": "## Keyword here\nkeyword body text\n"})
            r = self._search(ws, "keyword")
            out = m.render_manifest(r, now=time.time())
            lines = out.splitlines()
            self.assertTrue(lines[0].startswith("검색: `keyword`"))
            line = lines[2]
            self.assertTrue(line.startswith(f"[#1] {m.SCORE['heading_exact'] + m.SCORE['body']} | "), line)
            self.assertIn(" :: Keyword here | L1-2 | 0d | matched: keyword | ", line)
            self.assertNotIn("| #", out)  # md 표 골격 없음

    def test_manifest_select_score_dash(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, {"a.md": "## Alpha\nbody\n"})
            out = m.render_manifest(self._search(ws, "select:a.md"))
            self.assertIn("[#1] - | ", out)

    def test_manifest_snippet_capped_at_80(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, {"a.md": "## Alpha\n" + "keyword " + "y" * 300 + "\n"})
            out = m.render_manifest(self._search(ws, "keyword"))
            tail = out.splitlines()[2].rsplit(" | ", 1)[1]
            self.assertLessEqual(len(tail), m.MANIFEST_SNIPPET_CHARS + 1)
            self.assertTrue(tail.endswith("…"))

    def test_manifest_age_days_from_mtime(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, {"a.md": "## Alpha\nkeyword body\n"})
            now = time.time()
            os.utime(ws / "context" / "a.md", (now - 3 * 86400 - 10, now - 3 * 86400 - 10))
            out = m.render_manifest(self._search(ws, "keyword"), now=now)
            self.assertIn("| 3d |", out)

    def test_manifest_zero_hit_and_info_rendered(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, {"a.md": "## Alpha\nbody\n"})
            out = m.render_manifest(self._search(ws, "totallyabsent"))
            self.assertIn("0건", out)
            self.assertIn("토큰별 일치 섹션 수: totallyabsent=0", out)

    def test_manifest_heading_without_backticks(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, {"a.md": "## `/pilot:doctor` keyword\nbody\n"})
            out = m.render_manifest(self._search(ws, "keyword"))
            self.assertIn(" :: /pilot:doctor keyword | ", out)
            self.assertNotIn("`", out.splitlines()[2].split(" | ")[1])

    def test_manifest_with_inject_appends_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, {"a.md": "## Alpha\nbody\n"})
            out = m.render_manifest(self._search(ws, "select:a.md", inject=True))
            self.assertIn("[#1] - | ", out)
            self.assertIn("<context-snippet ", out)

    def test_cli_format_manifest_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, {"a.md": "## Keyword\nbody keyword text\n"})
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = m.main(["keyword", "--workspace", str(ws), "--format", "manifest"])
            self.assertEqual(code, 0)
            self.assertIn("[#1] ", out.getvalue())


# ---------------------------------------------------------------------------
# 한글 결합어 양방향 (E2~E5)
# ---------------------------------------------------------------------------
class CompoundTest(unittest.TestCase):
    def _q(self, raw):
        return m.parse_query(raw)

    def test_compounds_from_adjacent_hangul_words_in_query_order(self):
        q = self._q("선발송 접수 상태")
        self.assertEqual(q.compounds, [("선발송", "접수"), ("접수", "상태")])
        self.assertEqual(self._q("접수 선발송").compounds, [("접수", "선발송")])  # 순서 민감

    def test_compounds_broken_by_stopword_ascii_path_single_char(self):
        self.assertEqual(self._q("선발송 및 접수").compounds, [])
        self.assertEqual(self._q("선발송 API 접수").compounds, [])
        self.assertEqual(self._q("선발송 app/x.rb 접수").compounds, [])
        self.assertEqual(self._q("선발송 값 접수").compounds, [])
        self.assertEqual(self._q("select:a.md").compounds, [])

    def test_required_prefix_still_pairs(self):
        self.assertEqual(self._q("+선발송 접수").compounds, [("선발송", "접수")])

    def test_joined_body_scores_equal_to_spaced_body(self):
        q = self._q("선발송 접수")
        joined, mj = m.score_text(q, heading="", body="선발송접수 확인")
        spaced, ms = m.score_text(q, heading="", body="선발송 접수 확인")
        self.assertEqual(joined, spaced)
        self.assertEqual(joined, 2 * m.SCORE["body"])
        self.assertEqual(mj, ["선발송", "접수"])
        self.assertEqual(ms, ["선발송", "접수"])

    def test_compound_in_description(self):
        q = self._q("선발송 접수")
        score, matched = m.score_text(q, heading="", body="", description="선발송접수 규칙")
        self.assertEqual(score, 2 * m.SCORE["description"])
        self.assertEqual(matched, ["선발송", "접수"])

    def test_compound_not_double_counted_when_both_forms_present(self):
        q = self._q("선발송 접수")
        score, _ = m.score_text(q, heading="", body="선발송 접수 그리고 선발송접수")
        self.assertEqual(score, 2 * m.SCORE["body"])

    def test_compound_requires_left_boundary(self):
        q = self._q("선발송 접수")
        score, _ = m.score_text(q, heading="", body="가선발송접수")
        self.assertEqual(score, 0)

    def test_heading_compound_already_handled_by_partial_match(self):
        q = self._q("선발송 접수")
        score, _ = m.score_text(q, heading="선발송접수 상태값", body="")
        self.assertEqual(score, 2 * m.SCORE["heading_partial"])

    def test_reverse_joined_query_matches_spaced_body(self):
        score, matched = m.score_text(self._q("진입파일"), heading="", body="도메인 진입 파일 로드")
        self.assertEqual(score, m.SCORE["body"])
        self.assertEqual(matched, ["진입파일"])

    def test_reverse_joined_query_matches_spaced_description(self):
        score, _ = m.score_text(self._q("진입파일"), heading="", body="", description="진입 파일 규칙")
        self.assertEqual(score, m.SCORE["description"])

    def test_reverse_joined_query_matches_spaced_heading_as_partial(self):
        score, _ = m.score_text(self._q("진입파일"), heading="도메인 진입 파일", body="")
        self.assertEqual(score, m.SCORE["heading_partial"])

    def test_reverse_heading_hangul_token_contained_in_query_token(self):
        score, _ = m.score_text(self._q("진입파일"), heading="Cluster 진입", body="")
        self.assertEqual(score, m.SCORE["heading_partial"])

    def test_reverse_not_applied_below_min_chars(self):
        score, _ = m.score_text(self._q("파일들"), heading="파일", body="파 일 들")
        self.assertEqual(score, 0)

    def test_reverse_not_applied_to_ascii(self):
        score, _ = m.score_text(self._q("payload"), heading="pay load", body="pay load")
        self.assertEqual(score, 0)

    def test_reverse_does_not_stack_on_direct_hit(self):
        score, _ = m.score_text(self._q("진입파일"), heading="", body="진입파일 그리고 진입 파일")
        self.assertEqual(score, m.SCORE["body"])

    def test_required_gate_satisfied_via_compound(self):
        q = self._q("선발송 +접수")
        score, matched = m.score_text(q, heading="", body="선발송접수 확인")
        self.assertEqual(score, 2 * m.SCORE["body"])
        self.assertIn("접수", matched)

    def test_required_gate_satisfied_via_reverse(self):
        score, _ = m.score_text(self._q("+진입파일"), heading="", body="진입 파일")
        self.assertEqual(score, m.SCORE["body"])

    def test_snippet_positions_on_reverse_match(self):
        sec = m.Section(
            file="f.md", heading="H", level=2, line_start=1, line_end=2,
            body_lines=["x" * 300 + " 진입 파일 " + "y" * 300], description=None,
        )
        self.assertIn("진입 파일", m.build_snippet(sec, ["진입파일"]))

    def test_existing_signals_unchanged(self):
        # 결합어 도입 후에도 기존 6신호 값은 그대로다 (G2 — Q1~Q4 출력 바이트 동일의 단위 근거)
        q = self._q("doctor")
        self.assertEqual(m.score_text(q, heading="doctor", body="")[0], m.SCORE["heading_exact"])
        self.assertEqual(m.score_text(q, heading="", body="doctor here")[0], m.SCORE["body"])
        self.assertEqual(m.score_text(q, heading="", body="", path_tokens={"doctor"})[0], m.SCORE["path"])

    def test_zero_hit_guidance_mentions_compound_auto_match(self):
        q = self._q("zzqq 진입파일")
        guidance = m.build_zero_hit("zzqq 진입파일", q, {"zzqq": 0, "진입파일": 0}, None, False)["guidance"]
        self.assertTrue(any("붙여쓰기·띄어쓰기" in g for g in guidance), guidance)
        q2 = self._q("zzqq 섹션")
        guidance2 = m.build_zero_hit("zzqq 섹션", q2, {"zzqq": 0, "섹션": 0}, None, False)["guidance"]
        self.assertFalse(any("붙여쓰기" in g for g in guidance2))


# ---------------------------------------------------------------------------
# frontmatter 파서 (E6) · sources glob 보너스 (E7)
# ---------------------------------------------------------------------------
class FrontmatterTest(unittest.TestCase):
    def test_scalar_trailing_comment_stripped(self):
        # #29 예시 그대로 — 주석의 enum 8단어가 type 값으로 번지면 모든 파일이 모든 type 에 매칭된다.
        meta = m.parse_frontmatter(
            ["type: services            # index | routes | models | services | rules | enums | boundary | free"]
        )
        self.assertEqual(meta, {"type": "services"})

    def test_quoted_values_keep_hash_and_strip_quotes(self):
        meta = m.parse_frontmatter(['description: "이슈 #12 처리 규칙"', "domain: 'wms'"])
        self.assertEqual(meta, {"description": "이슈 #12 처리 규칙", "domain": "wms"})

    def test_block_list_with_comments(self):
        meta = m.parse_frontmatter(
            [
                "sources:                  # 이 문서가 다루는 소스 범위",
                "  - app/services/wms/**",
                "  - app/models/wms/shipment.rb  # 모델",
                "type: rules",
            ]
        )
        self.assertEqual(meta["sources"], ["app/services/wms/**", "app/models/wms/shipment.rb"])
        self.assertEqual(meta["type"], "rules")

    def test_inline_list_and_scalar_sources(self):
        self.assertEqual(
            m.parse_frontmatter(["sources: [app/a/**, 'app/b.rb']"])["sources"], ["app/a/**", "app/b.rb"]
        )
        self.assertEqual(m.parse_frontmatter(["sources: app/x/**"])["sources"], ["app/x/**"])

    def test_folded_scalar_takes_first_continuation_line_only(self):
        meta = m.parse_frontmatter(["description: >-", "  첫 줄 설명", "  둘째 줄", "domain: x"])
        self.assertEqual(meta, {"description": "첫 줄 설명", "domain": "x"})

    def test_unknown_keys_ignored_and_empty_values_absent(self):
        self.assertEqual(m.parse_frontmatter(["name: skill", "learned_at: 2026-09-04"]), {})
        self.assertEqual(m.parse_frontmatter(["sources:", "type:", "# 주석만"]), {})

    def test_split_sections_populates_meta_and_description(self):
        text = "---\ndescription: 설명\ndomain: wms\ntype: rules\nsources:\n  - app/x/**\n---\n## A\nbody\n"
        secs = m.split_sections(text, "f.md")
        self.assertEqual(secs[0].description, "설명")
        self.assertEqual(
            secs[0].meta, {"description": "설명", "domain": "wms", "type": "rules", "sources": ["app/x/**"]}
        )

    def test_no_frontmatter_meta_empty(self):
        self.assertEqual(m.split_sections("## A\nbody\n", "f.md")[0].meta, {})


class SourcesBonusTest(unittest.TestCase):
    def _q(self):
        return m.parse_query("app/services/wms/cancel.rb")

    def test_glob_covers_raw_path_query(self):
        score, matched = m.score_text(self._q(), heading="", body="", sources=["app/services/wms/**"])
        self.assertEqual(score, m.SCORE["citation"])
        self.assertEqual(matched, ["app/services/wms/cancel.rb"])

    def test_gitignore_semantics_of_sources_glob(self):
        # C7 — #30 `.claude/rules paths:` 와 같은 집합: `*`·`?` 는 `/` 를 넘지 않고 `**` 만 가로지른다.
        hit = ("app/services/**", "app/services/wms", "app/services/wms/", "**/wms/**", "wms", "services", "*.rb",
               "app/services/wms/*.rb", "app/*/wms/**", "/app/services/**")  # 슬래시 없는 이름은 어느 깊이의 디렉토리와도
        miss = ("wms/**", "app/services/*.rb", "app/*/cancel.rb", "*.py", "app/services/wm?/x.rb", "models")
        for g in hit:
            self.assertEqual(m.score_text(self._q(), heading="", body="", sources=[g])[0], m.SCORE["citation"], g)
        for g in miss:
            self.assertEqual(m.score_text(self._q(), heading="", body="", sources=[g])[0], 0, g)
        self.assertTrue(m._source_glob_match("app/services/wms/x/y.rb", "app/services/wms/**"))
        self.assertFalse(m._source_glob_match("app/services/wms/x/y.rb", "app/services/wms/*.rb"))

    def test_mismatch_and_empty_no_bonus(self):
        self.assertEqual(m.score_text(self._q(), heading="", body="", sources=["app/models/**"])[0], 0)
        self.assertEqual(m.score_text(self._q(), heading="", body="", sources=[""])[0], 0)

    def test_bonus_once_per_query_path_and_stacks_with_citation(self):
        score, matched = m.score_text(
            self._q(), heading="", body="",
            citation_paths=["app/services/wms/cancel.rb"],
            sources=["app/services/wms/**", "app/services/**"],
        )
        self.assertEqual(score, 2 * m.SCORE["citation"])
        self.assertEqual(matched.count("app/services/wms/cancel.rb"), 1)

    def test_no_segment_token_scoring_from_sources(self):
        # `wms` 키워드 질의는 sources 로 점수를 받지 않는다 — type·domain 도 마찬가지 (E7)
        q = m.parse_query("wms services rules")
        sec = m.Section(
            file="f.md", heading="", level=2, line_start=1, line_end=1, body_lines=[],
            description=None, meta={"type": "rules", "domain": "wms", "sources": ["app/services/wms/**"]},
        )
        self.assertEqual(m.score_section(sec, q)[0], 0)

    def test_score_section_passes_meta_sources(self):
        sec = m.Section(
            file="f.md", heading="", level=2, line_start=1, line_end=1, body_lines=[],
            description=None, meta={"sources": ["app/services/wms/**"]},
        )
        self.assertEqual(m.score_section(sec, self._q())[0], m.SCORE["citation"])

    def test_json_type_domain_only_when_present(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / "context").mkdir()
            (ws / "context" / "a.md").write_text(
                "---\ntype: rules\ndomain: wms\n---\n## Keyword A\nkeyword body\n", encoding="utf-8"
            )
            (ws / "context" / "b.md").write_text("## Keyword B\nkeyword body\n", encoding="utf-8")
            r = m.search(workspace=ws, project=None, scope=None, includes=None, query_raw="keyword", limit=5)
            a, b = r["results"]
            self.assertEqual(list(a.keys())[-3:], ["read_hint", "type", "domain"])
            self.assertEqual((a["type"], a["domain"]), ("rules", "wms"))
            self.assertNotIn("type", b)
            self.assertNotIn("domain", b)
            self.assertIn("[#1] 12 [rules] | ", m.render_manifest(r))


# ---------------------------------------------------------------------------
# 골든 — pilot/tests/fixtures/context-search/ 스냅샷, --scope pilot, hit@3
# ---------------------------------------------------------------------------
@unittest.skipUnless(FIXTURE_ROOT.is_dir(), "context-search 골든 fixture 없음")
class GoldenHitAtThree(unittest.TestCase):
    """D2 — 고정 스냅샷 fixture 로 검증(라이브 코퍼스 hit@3 는 evaluator 가 별도 실측)."""

    def _top3(self, query):
        result = m.search(
            workspace=FIXTURE_ROOT, project=None, scope="pilot", includes=None,
            query_raw=query, limit=3,
        )
        return [(r["file"], r["heading"]) for r in result["results"]]

    def test_q1_doctor_consistency_check(self):
        top3 = self._top3("doctor 정합성 검사")
        self.assertTrue(
            any("lifecycle.md" in f and "doctor" in h for f, h in top3), top3
        )

    def test_q2_slack_webhook_notification(self):
        top3 = self._top3("slack webhook 알림")
        self.assertTrue(
            any("delivery.md" in f and "slack" in h for f, h in top3), top3
        )

    def test_q3_reverse_path_query(self):
        top3 = self._top3("pilot/skills/learn/SKILL.md")
        self.assertTrue(
            any("spec.md" in f and "learn" in h for f, h in top3), top3
        )

    def test_q4_korean_only_query(self):
        top3 = self._top3("도메인 진입 파일 자동 로드")
        self.assertTrue(
            any("index.md" in f and "Cluster" in h for f, h in top3), top3
        )

    def test_q5_korean_joined_compound_query(self):
        # E4 — `진입파일` 처럼 붙여 쓴 질의가 `진입 파일` 로 띄어 쓴 본문·헤딩 토큰과 대조된다.
        # 도입 전 실측(2026-09-08): 정답 top-3 이탈(`진입파일` 히트 0) → 도입 후 1위 7점.
        top3 = self._top3("도메인 진입파일 자동 로드")
        self.assertTrue(
            any("index.md" in f and "Cluster" in h for f, h in top3), top3
        )

    def test_q6_korean_joined_compound_with_ascii_anchor(self):
        # 회귀 감시 — ASCII 헤딩 정확 일치(doctor)가 있는 질의에 붙여 쓴 한글이 섞여도 1위 불변.
        top3 = self._top3("doctor 정합성검사")
        self.assertTrue(
            any("lifecycle.md" in f and "doctor" in h for f, h in top3), top3
        )


if __name__ == "__main__":
    unittest.main()
