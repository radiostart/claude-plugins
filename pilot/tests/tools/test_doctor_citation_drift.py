"""
pilot/tools/doctor/integrity.py 의 context 인용 drift 검사 단위 테스트.

`check_context_citations_stale` 은 context/**/*.md 의 `file:line`·`file#symbol`
인용이 가리키는 소스 파일이 문서보다 최신이면 stale 가능성 WARN 을 낸다
(learn SKILL § 추출 항목의 "pilot-doctor 의 mtime drift 감지 입력" 실물).

    - 인용 0건 파일은 조용히 빠지지 않고 "인용 부재" WARN
    - 앵커는 선택 — 괄호·백틱, 라인·범위·심볼·다중 앵커 모두 인용
    - .md 인용도 소스 인용 (플러그인 리포 학습) — 단 workspace 내부 상호 링크 제외
    - 미해석 인용은 stale 판정 제외 + 건수 병기 (커버리지 착시 방지)
    - source_root(context/config.md) 접두어 폴백 — 스켈레톤 예시 셀은 미선언 취급

실행:
    python3 pilot/tests/tools/test_doctor_citation_drift.py
"""

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent

_TOOLS_DIR = str(PLUGIN_ROOT / "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

import doctor.integrity as integrity  # noqa: E402


def _make_workspace(base: Path) -> tuple[Path, Path, Path]:
    """(workspace, context_domain_dir, service_repo) — 검사에 필요한 최소 구조."""
    service_repo = base / "service"
    workspace = service_repo / "workspace"
    domain_dir = workspace / "context" / "d"
    domain_dir.mkdir(parents=True)
    return workspace, domain_dir, service_repo


def _age(path: Path, seconds: int = 60) -> None:
    """path 의 mtime 을 과거로 밀어 '문서가 소스보다 먼저 작성됨' 을 결정적으로 만든다."""
    past = time.time() - seconds
    os.utime(path, (past, past))


def _write_src(service_repo: Path, rel: str, body: str = "x\n") -> Path:
    src = service_repo.joinpath(*rel.split("/"))
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text(body, encoding="utf-8")
    return src


def _stale_warns(results) -> list:
    return [r for r in results if "변경 감지" in r.message]


class NoCitations(unittest.TestCase):
    """인용 없는 파일은 검사에서 빠진다는 사실 자체를 WARN 으로 남긴다."""

    def test_no_citations_warns_instead_of_silent_skip(self):
        with tempfile.TemporaryDirectory() as td:
            ws, ddir, _ = _make_workspace(Path(td))
            (ddir / "a.md").write_text("설명만 있고 인용 없음.\n", encoding="utf-8")
            results = integrity.check_context_citations_stale(ws)
            warn = next(r for r in results if r.level == integrity.Result.WARN)
            self.assertIn("인용 부재", warn.label)
            self.assertIn("검사 대상에서 제외", warn.message)

    def test_no_citations_suppresses_pass(self):
        with tempfile.TemporaryDirectory() as td:
            ws, ddir, _ = _make_workspace(Path(td))
            (ddir / "a.md").write_text("인용 없음\n", encoding="utf-8")
            results = integrity.check_context_citations_stale(ws)
            self.assertFalse(
                any(r.level == integrity.Result.PASS for r in results)
            )

    def test_missing_context_dir_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "service" / "workspace"
            ws.mkdir(parents=True)
            self.assertEqual(integrity.check_context_citations_stale(ws), [])


class FreshCitations(unittest.TestCase):
    """문서가 소스보다 최신이면 PASS."""

    def test_source_older_than_doc_passes(self):
        with tempfile.TemporaryDirectory() as td:
            ws, ddir, repo = _make_workspace(Path(td))
            src = _write_src(repo, "app/s.rb")
            _age(src)
            (ddir / "a.md").write_text("전환 규칙 (app/s.rb:42)\n", encoding="utf-8")
            results = integrity.check_context_citations_stale(ws)
            self.assertEqual(_stale_warns(results), [])
            passed = next(r for r in results if r.level == integrity.Result.PASS)
            self.assertIn("1개 파일", passed.message)
            self.assertIn("인용 1건", passed.message)

    def test_pass_message_reports_unresolved_count(self):
        """미해석 인용 건수를 병기 — 커버리지 착시 방지."""
        with tempfile.TemporaryDirectory() as td:
            ws, ddir, repo = _make_workspace(Path(td))
            src = _write_src(repo, "app/s.rb")
            _age(src)
            (ddir / "a.md").write_text(
                "`app/s.rb` · `app/ghost.rb#missing`\n", encoding="utf-8"
            )
            results = integrity.check_context_citations_stale(ws)
            passed = next(r for r in results if r.level == integrity.Result.PASS)
            self.assertIn("인용 1건", passed.message)
            self.assertIn("미해석 1건", passed.message)

    def test_pass_survives_alongside_missing_citation_warn(self):
        """인용 부재 WARN 이 있어도 '인용 있는 파일은 최신' 정보는 유지."""
        with tempfile.TemporaryDirectory() as td:
            ws, ddir, repo = _make_workspace(Path(td))
            src = _write_src(repo, "app/s.rb")
            _age(src)
            (ddir / "a.md").write_text("`app/s.rb`\n", encoding="utf-8")
            (ddir / "bare.md").write_text("인용 없음\n", encoding="utf-8")
            results = integrity.check_context_citations_stale(ws)
            self.assertTrue(any("인용 부재" in r.label for r in results))
            passed = next(r for r in results if r.level == integrity.Result.PASS)
            self.assertIn("1개 파일", passed.message)


class StaleCitations(unittest.TestCase):
    """소스가 문서보다 최신이면 WARN."""

    def test_stale_source_triggers_warn_with_learn_hint(self):
        with tempfile.TemporaryDirectory() as td:
            ws, ddir, repo = _make_workspace(Path(td))
            doc = ddir / "a.md"
            doc.write_text("(app/s.rb:42)\n", encoding="utf-8")
            _age(doc)
            _write_src(repo, "app/s.rb")
            results = integrity.check_context_citations_stale(ws)
            warns = _stale_warns(results)
            self.assertEqual(len(warns), 1)
            self.assertEqual(warns[0].label, "context/d/a.md")
            self.assertIn("s.rb", warns[0].message)
            self.assertIn("/pilot:learn", warns[0].hint)
            self.assertIn("app/s.rb", warns[0].hint)

    def test_multiple_stale_grouped_with_sample(self):
        with tempfile.TemporaryDirectory() as td:
            ws, ddir, repo = _make_workspace(Path(td))
            names = ["a.rb", "b.rb", "c.rb", "e.rb"]
            doc = ddir / "a.md"
            doc.write_text(
                "\n".join(f"(app/{n}:{i + 1})" for i, n in enumerate(names)) + "\n",
                encoding="utf-8",
            )
            _age(doc)
            for n in names:
                _write_src(repo, f"app/{n}")
            warn = _stale_warns(integrity.check_context_citations_stale(ws))[0]
            self.assertIn("4개", warn.message)
            self.assertIn("외 1건", warn.message)

    def test_duplicate_citations_counted_once(self):
        with tempfile.TemporaryDirectory() as td:
            ws, ddir, repo = _make_workspace(Path(td))
            doc = ddir / "a.md"
            doc.write_text(
                "(app/s.rb:1)\n(app/s.rb:42)\n(app/s.rb:99)\n", encoding="utf-8"
            )
            _age(doc)
            _write_src(repo, "app/s.rb")
            warn = _stale_warns(integrity.check_context_citations_stale(ws))[0]
            self.assertIn("1개", warn.message)

    def test_unresolved_only_file_reports_absence_not_stale(self):
        with tempfile.TemporaryDirectory() as td:
            ws, ddir, _ = _make_workspace(Path(td))
            (ddir / "a.md").write_text(
                "(app/ghost.rb:99) — 존재하지 않는 파일\n", encoding="utf-8"
            )
            results = integrity.check_context_citations_stale(ws)
            warn = next(r for r in results if r.level == integrity.Result.WARN)
            self.assertIn("인용 부재", warn.label)
            self.assertIn("미해석", warn.message)
            self.assertEqual(_stale_warns(results), [])


class CitationFormats(unittest.TestCase):
    """앵커는 선택 — 실사용 인용 형식 전부를 인용으로 센다.

    회귀 방지: 앵커를 `:숫자` 필수로 조이면 심볼 앵커·백틱 표기 워크스페이스에서
    검사가 통째로 0 건이 된다 (조용한 무력화 — 리포트에도 안 남는다).
    """

    def _stale(self, td, citation: str) -> list:
        ws, ddir, repo = _make_workspace(Path(td))
        doc = ddir / "a.md"
        doc.write_text(f"{citation}\n", encoding="utf-8")
        _age(doc)
        _write_src(repo, "app/s.rb")
        return _stale_warns(integrity.check_context_citations_stale(ws))

    def test_paren_line_anchor(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(len(self._stale(td, "(app/s.rb:42)")), 1)

    def test_backtick_symbol_anchor(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(len(self._stale(td, "`app/s.rb#cancel!` 취소")), 1)

    def test_backtick_without_anchor(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(len(self._stale(td, "정의: `app/s.rb`")), 1)

    def test_line_range_anchor(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(len(self._stale(td, "`app/s.rb:379-381`")), 1)

    def test_middle_dot_multi_anchor(self):
        """실사용 형식 — `tools/plan-validate.py:34·461-466` 류."""
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(len(self._stale(td, "`app/s.rb:34·461-466`")), 1)

    def test_non_path_backtick_span_is_not_a_citation(self):
        with tempfile.TemporaryDirectory() as td:
            ws, ddir, _ = _make_workspace(Path(td))
            (ddir / "a.md").write_text(
                "`has_many :items, foreign_key: :ogiId`\n", encoding="utf-8"
            )
            results = integrity.check_context_citations_stale(ws)
            warn = next(r for r in results if r.level == integrity.Result.WARN)
            self.assertIn("인용 0건", warn.message)


class ScanScope(unittest.TestCase):
    """스캔 범위 — .md 소스 인용 포함, 상호 링크·메타 파일 제외."""

    def test_md_source_citation_is_checked(self):
        """.md 도 소스다 — 플러그인·문서 리포 학습 시 SKILL.md 인용이 대부분.

        `.md` 를 일괄 제외하면 문서 리포 워크스페이스의 stale 대부분을 놓치고,
        .md 인용만 있는 문서가 인용 부재로 오탐된다.
        """
        with tempfile.TemporaryDirectory() as td:
            ws, ddir, repo = _make_workspace(Path(td))
            doc = ddir / "a.md"
            doc.write_text("`pilot/skills/tdd/SKILL.md:12`\n", encoding="utf-8")
            _age(doc)
            _write_src(repo, "pilot/skills/tdd/SKILL.md", "# tdd\n")
            warns = _stale_warns(integrity.check_context_citations_stale(ws))
            self.assertEqual(len(warns), 1)

    def test_workspace_internal_link_is_not_a_citation(self):
        """workspace 내부로 해석되는 인용 = context 상호 링크 — 세지 않는다."""
        with tempfile.TemporaryDirectory() as td:
            ws, ddir, _ = _make_workspace(Path(td))
            neighbor = ddir / "b.md"
            neighbor.write_text("# b\n", encoding="utf-8")
            doc = ddir / "a.md"
            doc.write_text("`workspace/context/d/b.md` 참조\n", encoding="utf-8")
            _age(doc)
            os.utime(neighbor)  # 이웃 문서가 더 최신이어도 stale 오탐 금지
            results = integrity.check_context_citations_stale(ws)
            self.assertEqual(_stale_warns(results), [])
            # 상호 링크는 인용으로도 안 세므로 a.md 는 인용 부재로 분류된다
            self.assertTrue(
                any("a.md 인용 부재" in r.label for r in results)
            )

    def test_meta_files_excluded(self):
        with tempfile.TemporaryDirectory() as td:
            ws, ddir, repo = _make_workspace(Path(td))
            src = _write_src(repo, "app/s.rb")
            _age(src)
            (ddir / "a.md").write_text("`app/s.rb`\n", encoding="utf-8")
            for name in ("MANIFEST.md", "config.md", "pr.md", "coding.md"):
                (ws / "context" / name).write_text("메타 — 인용 없음\n", encoding="utf-8")
            results = integrity.check_context_citations_stale(ws)
            self.assertFalse(any("인용 부재" in r.label for r in results))


class SourceRootFallback(unittest.TestCase):
    """repo 루트 해석 실패 시 context/config.md 의 source_root 접두어로 재시도."""

    def _write_config(self, ws: Path, value_cell: str):
        (ws / "context" / "config.md").write_text(
            "## 언어·도구 기본값\n\n"
            "| 키 | 값 | 용도 |\n| --- | --- | --- |\n"
            f"| `source_root` | {value_cell} | 소스 루트 |\n",
            encoding="utf-8",
        )

    def test_subroot_relative_citation_resolves(self):
        with tempfile.TemporaryDirectory() as td:
            ws, ddir, repo = _make_workspace(Path(td))
            self._write_config(ws, "`sub/src`")
            doc = ddir / "a.md"
            doc.write_text("`svc/a.ts#login`\n", encoding="utf-8")
            _age(doc)
            _write_src(repo, "sub/src/svc/a.ts")
            warns = _stale_warns(integrity.check_context_citations_stale(ws))
            self.assertEqual(len(warns), 1)

    def test_repo_root_takes_precedence(self):
        with tempfile.TemporaryDirectory() as td:
            ws, ddir, repo = _make_workspace(Path(td))
            self._write_config(ws, "`app`")
            doc = ddir / "a.md"
            doc.write_text("`app/s.rb`\n", encoding="utf-8")
            _age(doc)
            _write_src(repo, "app/s.rb")
            warns = _stale_warns(integrity.check_context_citations_stale(ws))
            self.assertEqual(len(warns), 1)

    def test_missing_config_is_tolerated(self):
        with tempfile.TemporaryDirectory() as td:
            ws, ddir, repo = _make_workspace(Path(td))
            src = _write_src(repo, "app/s.rb")
            _age(src)
            (ddir / "a.md").write_text("`app/s.rb`\n", encoding="utf-8")
            results = integrity.check_context_citations_stale(ws)
            self.assertTrue(any(r.level == integrity.Result.PASS for r in results))


class ReadSourceRoot(unittest.TestCase):
    """_read_source_root 단위 — pilot-init 스켈레톤 config 와의 공존."""

    def _ws(self, td, row: str) -> Path:
        ws = Path(td) / "workspace"
        (ws / "context").mkdir(parents=True)
        (ws / "context" / "config.md").write_text(
            "## 언어·도구 기본값\n\n| 키 | 값 | 용도 |\n| --- | --- | --- |\n"
            f"{row}\n",
            encoding="utf-8",
        )
        return ws

    def test_reads_backticked_value(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, "| `source_root` | `app/` | 소스 루트 |")
            self.assertEqual(integrity._read_source_root(ws), "app/")

    def test_reads_bare_value(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, "| source_root | app/ | 소스 루트 |")
            self.assertEqual(integrity._read_source_root(ws), "app/")

    def test_skeleton_example_cell_is_not_a_declaration(self):
        """pilot-init 스켈레톤의 예시 산문 셀에서 `app/` 를 오추출하면 안 된다."""
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, "| `source_root` | `app/` · `src/main/` 등 | 소스 루트 |")
            self.assertIsNone(integrity._read_source_root(ws))

    def test_undeclared_marker_is_none(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(td, "| `source_root` | — | 소스 루트 |")
            self.assertIsNone(integrity._read_source_root(ws))

    def test_missing_config_is_none(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "workspace"
            (ws / "context").mkdir(parents=True)
            self.assertIsNone(integrity._read_source_root(ws))


if __name__ == "__main__":
    unittest.main()
