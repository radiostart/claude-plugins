"""switch-scan.py 테스트.

- 파생 규칙: 진행 (목표 체크박스·placeholder 제외)·요약 (개요→목표→폴더명 fallback)·상태 부기
- degraded: corrupt STATE WARN + 목록 계속·활성 폴더 부재 WARN·STATE/issues/ 부재 정상
- 출력 계약: 최근순 정렬·cap 10 + `외 N건`·`|` 이스케이프·--json 스키마
- 실사용 관측 케이스: project.md 부재 (state 파일만 존재)·목표 전부
  placeholder·한/영 STATE 헤더
"""

from __future__ import annotations

import contextlib
import datetime
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
SCAN_PATH = PLUGIN_ROOT / "tools" / "switch-scan.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("switch_scan", SCAN_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = _load_module()

BASE_TS = 1_750_000_000  # 고정 기준 시각 (테스트 결정성)


def _run(args):
    """main() 을 stdout 캡처로 실행해 (exit_code, output) 반환."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = m.main(args)
    return code, buf.getvalue()


def _date_of(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def _make_ws(td):
    ws = Path(td) / "workspace"
    ws.mkdir()
    return ws


def _touch_tree(root, ts):
    for p in [root] + list(root.rglob("*")):
        os.utime(p, (ts, ts))


def _pmd(overview="한 줄 개요", goals=("- [x] 목표 A", "- [ ] 목표 B")):
    return "# X\n\n## 개요\n\n{}\n\n## 목표\n\n{}\n".format(overview, "\n".join(goals))


def _make_project(ws, name, project_md=None, state=None, ts=BASE_TS):
    d = ws / "projects" / name
    d.mkdir(parents=True)
    if project_md is not None:
        (d / "project.md").write_text(project_md, encoding="utf-8")
    if state is not None:
        (d / ".agent-state.yml").write_text(state, encoding="utf-8")
    _touch_tree(d, ts)
    return d


def _make_issue(ws, name, issue_md=None, ts=BASE_TS):
    d = ws / "issues" / name
    d.mkdir(parents=True)
    if issue_md is not None:
        (d / "issue.md").write_text(issue_md, encoding="utf-8")
    _touch_tree(d, ts)
    return d


def _write_state(ws, rows, header="| 모드 | 이름/이슈명 | 상태 |"):
    body = header + "\n| --- | --- | --- |\n" + "\n".join(rows) + "\n"
    (ws / "STATE.md").write_text(body, encoding="utf-8")


def _json_items(out):
    return json.loads(out)["items"]


class BasicTable(unittest.TestCase):
    def test_projects_and_issues_combined_sorted_desc(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(ws, "old", project_md=_pmd(), ts=BASE_TS - 1000)
            _make_project(ws, "new", project_md=_pmd(), ts=BASE_TS)
            _make_issue(ws, "boom", issue_md="# 결제 오류 대응\n", ts=BASE_TS - 500)
            code, out = _run([str(ws), "--json"])
            self.assertEqual(code, 0)
            items = _json_items(out)
            self.assertEqual([it["name"] for it in items], ["new", "boom", "old"])
            self.assertEqual([it["mode"] for it in items], ["project", "issue", "project"])
            self.assertEqual(items[1]["summary"], "결제 오류 대응")
            self.assertEqual(items[0]["date"], _date_of(BASE_TS))

    def test_active_marker_and_progress(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(ws, "alpha", project_md=_pmd(), state="analyzed: true\n")
            _write_state(ws, ["| project | alpha | 진행중 |"])
            code, out = _run([str(ws)])
            self.assertEqual(code, 0)
            self.assertIn("alpha ◀ 활성", out)
            self.assertIn("| 1/2 |", out)
            self.assertNotIn("WARN", out)

    def test_mtime_tie_breaks_by_name(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(ws, "bbb", project_md=_pmd(), ts=BASE_TS)
            _make_project(ws, "aaa", project_md=_pmd(), ts=BASE_TS)
            _, out = _run([str(ws), "--json"])
            self.assertEqual([it["name"] for it in _json_items(out)], ["aaa", "bbb"])

    def test_bak_artifacts_excluded_from_mtime(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            d = _make_project(ws, "p", project_md=_pmd(), ts=BASE_TS - 5000)
            bak = d / "project.md.bak"
            bak.write_text("x", encoding="utf-8")
            bak_dir = d / ".prompts.bak"
            bak_dir.mkdir()
            (bak_dir / "planner.md").write_text("x", encoding="utf-8")
            os.utime(bak, (BASE_TS, BASE_TS))
            os.utime(bak_dir / "planner.md", (BASE_TS, BASE_TS))
            os.utime(bak_dir, (BASE_TS, BASE_TS))
            os.utime(d, (BASE_TS - 5000, BASE_TS - 5000))
            _, out = _run([str(ws), "--json"])
            self.assertEqual(_json_items(out)[0]["date"], _date_of(BASE_TS - 5000))


class DerivationFallbacks(unittest.TestCase):
    def test_overview_placeholder_falls_back_to_goal(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(
                ws,
                "p",
                project_md=_pmd(
                    overview="{프로젝트 목적과 배경을 1~2문장으로}",
                    goals=("- [x] 미사입 구조 개선 -> [상세](features/01-x.md)", "- [ ] 후속"),
                ),
            )
            _, out = _run([str(ws), "--json"])
            item = _json_items(out)[0]
            self.assertEqual(item["summary"], "미사입 구조 개선")  # 링크 suffix 제거
            self.assertEqual(item["progress"], "1/2")

    def test_all_placeholder_goals_dash_progress_and_folder_summary(self):
        # 스캐폴딩 직후 미기입 프로젝트 — 목표가 전부 placeholder
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(
                ws,
                "test",
                project_md=_pmd(
                    overview="{프로젝트 목적}",
                    goals=("- [ ] {완료 조건 1}", "- [ ] {완료 조건 2}"),
                ),
            )
            _, out = _run([str(ws), "--json"])
            item = _json_items(out)[0]
            self.assertEqual(item["progress"], "-")
            self.assertEqual(item["summary"], "test")

    def test_missing_project_md(self):
        # project.md 부재 — .agent-state.yml 만 존재하는 폴더
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(ws, "TICKET-528", state="---\nanalyzed: true\ntdd: true\n---\n")
            _, out = _run([str(ws), "--json"])
            item = _json_items(out)[0]
            self.assertEqual(item["summary"], "TICKET-528")
            self.assertEqual(item["progress"], "-")
            self.assertEqual(item["state"], "분석완·tdd")

    def test_missing_state_yml_legacy(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(ws, "legacy", project_md=_pmd())
            _, out = _run([str(ws), "--json"])
            self.assertEqual(_json_items(out)[0]["state"], "-")

    def test_state_suffixes_tdd_and_characterize(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(
                ws,
                "p",
                project_md=_pmd(),
                state='analyzed: true\ntdd: true\nmode: characterize\nplugin_version: "0.15.0"\n',
            )
            _, out = _run([str(ws), "--json"])
            self.assertEqual(_json_items(out)[0]["state"], "분석완·tdd·chr")

    def test_state_flags_without_analyzed(self):
        # 미분석 + tdd — 선행 `-` 없이 플래그만 표기
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(ws, "p", project_md=_pmd(), state="analyzed: false\ntdd: true\n")
            _, out = _run([str(ws), "--json"])
            self.assertEqual(_json_items(out)[0]["state"], "tdd")

    def test_state_qa_phase_marker(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(
                ws, "p", project_md=_pmd(),
                state="analyzed: true\nphase: qa\n",
            )
            _, out = _run([str(ws), "--json"])
            self.assertEqual(_json_items(out)[0]["state"], "분석완·qa")

    def test_issue_without_h1_uses_folder_name(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_issue(ws, "legacy-issue", issue_md="현상만 적힘\n")
            _, out = _run([str(ws), "--json"])
            item = _json_items(out)[0]
            self.assertEqual(item["summary"], "legacy-issue")
            self.assertEqual(item["progress"], "-")


class IssueActionProgress(unittest.TestCase):
    # issue `## 조치` 프록시 3값 판정 — 조치 기입이 완료 신호라는 GUIDE 계약.

    def _progress(self, issue_md):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_issue(ws, "i", issue_md=issue_md)
            _, out = _run([str(ws), "--json"])
            return _json_items(out)[0]["progress"]

    def test_filled_action_is_resolved(self):
        md = "# 결제 오류\n\n## 조치\n\n- refund 재시도 가드 추가 (PR #12)\n"
        self.assertEqual(self._progress(md), "조치완")

    def test_template_placeholder_is_unresolved(self):
        # 조치 절이 템플릿 그대로 남은 미완 이슈
        md = "# t\n\n## 현상\n\n- 증상\n\n## 조치\n\n_(수정 완료 후 자동 기입)_\n"
        self.assertEqual(self._progress(md), "미완")

    def test_italic_variant_counts_as_resolved(self):
        # 정확 일치 규칙 — 정당한 한 줄 italic 조치는 실내용 (접두/접미 패턴이면 오인)
        md = "# t\n\n## 조치\n\n_(핫픽스로 종결 — PR #12)_\n"
        self.assertEqual(self._progress(md), "조치완")

    def test_brace_placeholder_only_is_unresolved(self):
        md = "# t\n\n## 조치\n\n{소스 변경 내용}\n"
        self.assertEqual(self._progress(md), "미완")

    def test_section_missing_is_dash(self):
        md = "# t\n\n## 현상\n\n- 증상만 있는 비템플릿 legacy\n"
        self.assertEqual(self._progress(md), "-")

    def test_fenced_heading_not_recognized_current_behavior(self):
        # 한계 고정 (의도적 상속): 파서는 펜스를 인식하지 않아 펜스 안
        # `## 조치` 도 섹션 전환으로 본다 → 이 fixture 는 조치완 오판이 현행
        # 동작임을 고정한다. 파서가 펜스 인식을 얻으면 의식적으로 갱신할 것.
        md = (
            "# t\n\n## 현상\n\n```log\n## 조치\n적용 로그 내용\n```\n\n"
            "## 조치\n\n_(수정 완료 후 자동 기입)_\n"
        )
        self.assertEqual(self._progress(md), "조치완")

    def test_action_placeholder_constant_matches_guide_template(self):
        # 판정 상수 ↔ issues/GUIDE.md 템플릿 문자열 drift 감지
        guide_path = PLUGIN_ROOT / "skills" / "context" / "lifecycle" / "issues" / "GUIDE.md"
        guide = guide_path.read_text(encoding="utf-8")
        self.assertIn(m.ACTION_PLACEHOLDER, guide)


class CapAndRendering(unittest.TestCase):
    def test_cap_10_with_rest_line_and_all_flag(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            for i in range(12):
                _make_project(ws, "p{:02d}".format(i), project_md=_pmd(), ts=BASE_TS - i)
            code, out = _run([str(ws)])
            self.assertEqual(code, 0)
            self.assertIn("외 2건 — `--all` 로 전체 표시", out)
            self.assertEqual(out.count("| project |"), 10)
            _, out_all = _run([str(ws), "--all"])
            self.assertNotIn("외 2건", out_all)
            self.assertEqual(out_all.count("| project |"), 12)
            _, out_json = _run([str(ws), "--json"])
            self.assertEqual(json.loads(out_json)["count"], 12)
            self.assertEqual(len(_json_items(out_json)), 12)  # JSON 은 cap 비적용

    def test_cap_footer_counts_hidden_unresolved_issues(self):
        # cap 밖으로 밀린 미완 이슈의 침묵 절단 방지
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            for i in range(11):
                _make_project(ws, "p{:02d}".format(i), project_md=_pmd(), ts=BASE_TS - i)
            _make_issue(
                ws,
                "stale",
                issue_md="# 미완 이슈\n\n## 조치\n\n_(수정 완료 후 자동 기입)_\n",
                ts=BASE_TS - 999,
            )
            _, out = _run([str(ws)])
            self.assertIn("외 2건 (미완 이슈 1건 포함) — `--all` 로 전체 표시", out)
            self.assertEqual(out.count("| issue |"), 0)  # 실제로 cap 밖으로 밀림

    def test_pipe_in_summary_escaped_in_markdown_only(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(ws, "p", project_md=_pmd(overview="A|B 파이프 요약"))
            _, md = _run([str(ws)])
            self.assertIn("A\\|B 파이프 요약", md)
            _, js = _run([str(ws), "--json"])
            self.assertEqual(_json_items(js)[0]["summary"], "A|B 파이프 요약")

    def test_summary_truncated_to_40(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(ws, "p", project_md=_pmd(overview="가" * 60))
            _, out = _run([str(ws), "--json"])
            summary = _json_items(out)[0]["summary"]
            self.assertEqual(len(summary), 40)
            self.assertTrue(summary.endswith("…"))

    def test_empty_workspace_message(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            code, out = _run([str(ws)])
            self.assertEqual(code, 0)
            self.assertIn("작업 폴더가 없습니다", out)


class StateVariantsAndDegraded(unittest.TestCase):
    def test_english_header_state(self):
        # 영문 헤더 + 안내문 프리앰블 변형
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(ws, "non-root", project_md=_pmd())
            (ws / "STATE.md").write_text(
                "# STATE\n\n활성 작업 1행만 유지.\n\n"
                "| mode | name | status |\n| --- | --- | --- |\n"
                "| project | non-root | 진행중 |\n",
                encoding="utf-8",
            )
            _, out = _run([str(ws)])
            self.assertIn("non-root ◀ 활성", out)

    def test_same_name_project_and_issue_marks_mode_match_only(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(ws, "dup", project_md=_pmd(), ts=BASE_TS)
            _make_issue(ws, "dup", issue_md="# dup 이슈\n", ts=BASE_TS - 10)
            _write_state(ws, ["| issue | dup | 진행중 |"])
            _, out = _run([str(ws), "--json"])
            items = {(it["mode"], it["name"]): it["active"] for it in _json_items(out)}
            self.assertFalse(items[("project", "dup")])
            self.assertTrue(items[("issue", "dup")])

    def test_corrupt_state_warns_but_lists(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(ws, "a", project_md=_pmd())
            _make_project(ws, "b", project_md=_pmd())
            _write_state(ws, ["| project | a | 진행중 |", "| project | b | 진행중 |"])
            code, out = _run([str(ws)])
            self.assertEqual(code, 0)
            self.assertIn("WARN: STATE.md 에 진행중 행이 2개", out)
            self.assertIn("pilot-doctor", out)
            self.assertIn("| mode |", out)  # 목록은 계속 출력

    def test_active_folder_missing_warns_with_mode_path(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(ws, "real", project_md=_pmd())
            _write_state(ws, ["| issue | ghost | 진행중 |"])
            code, out = _run([str(ws)])
            self.assertEqual(code, 0)
            self.assertIn("활성 issue 'ghost' 의 폴더가 issues/ 에 없습니다", out)

    def test_bare_issue_active_row_no_folder_warn(self):
        # `| issue | - | 진행중 |` (bare 진입) 은 폴더 부재 WARN 비대상
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(ws, "p", project_md=_pmd())
            _write_state(ws, ["| issue | - | 진행중 |"])
            code, out = _run([str(ws)])
            self.assertEqual(code, 0)
            self.assertNotIn("WARN", out)

    def test_state_absent_lists_without_marker(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(ws, "p", project_md=_pmd())
            code, out = _run([str(ws)])
            self.assertEqual(code, 0)
            self.assertNotIn("◀ 활성", out)
            self.assertNotIn("WARN", out)

    def test_no_issues_dir_ok(self):
        # issues/ 디렉토리 자체 부재도 정상
        with tempfile.TemporaryDirectory() as td:
            ws = _make_ws(td)
            _make_project(ws, "p", project_md=_pmd())
            code, out = _run([str(ws), "--json"])
            self.assertEqual(code, 0)
            self.assertEqual(len(_json_items(out)), 1)

    def test_workspace_missing_exit_1(self):
        with tempfile.TemporaryDirectory() as td:
            code, out = _run([str(Path(td) / "workspace")])
            self.assertEqual(code, 1)
            self.assertIn("workspace/ 가 없습니다", out)


if __name__ == "__main__":
    unittest.main()
