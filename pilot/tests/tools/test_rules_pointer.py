#!/usr/bin/env python3
"""
doctor/rules_pointer.py · tools/rules-pointer.py 단위 테스트 (plan r2 Phase 1, #30 C1).

    - MANIFEST 도메인 표 파싱 · 도메인 문서 집합
    - paths 도출: sources 우선 · 인용 실파일 해석(제외 규칙) · 하위 트리 탐욕 분할 · 캡 · 도메인 간 배타
    - 포인터 순서·캡(8줄·500자)·"그 외 N개" · 파일 렌더·주입 본문·paths 파서
    - write(마커 보존·동일 무변경) · check · 결정성 · 훅(세션·도메인 1회, ≤2 도메인, 무음 조건)
    - CLI exit 코드

실행:
    python3 pilot/tests/tools/test_rules_pointer.py
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
_TOOLS_DIR = str(PLUGIN_ROOT / "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from doctor import rules_pointer as rp  # noqa: E402
from doctor._common import Result  # noqa: E402

CLI = PLUGIN_ROOT / "tools" / "rules-pointer.py"

MANIFEST = (
    "# MANIFEST\n\n> `## 도메인 분류` 표 안내 — 이 줄은 표가 아니다\n\n"
    "## 도메인 분류\n\n"
    "| 도메인 | 진입 파일 | 설명 |\n| --- | --- | --- |\n"
    "| wms | `wms/index.md` | 창고 |\n"
    "| billing | `billing.md` | 정산 |\n\n"
    "## 외부 도메인 reference\n\n(없음)\n"
)
CONFIG = (
    "## Ignore\n\n| 패턴 | 사유 |\n| --- | --- |\n| `vendor/` | 생성 코드 |\n\n"
    "## 언어·도구 기본값\n\n| 키 | 값 | 용도 |\n| --- | --- | --- |\n"
    "| `source_root` | `app/` | 소스 루트 |\n"
    "| `test_path_convention` | `spec/**/*_spec.rb` | 테스트 |\n"
)
WMS_INDEX = (
    "# wms\n\n서비스 `app/services/wms/a.rb#run` 와 (app/services/wms/b.rb:3) 가 `app/models/order.rb` 를 쓴다.\n"
    "테스트 `spec/wms_spec.rb` · 벤더 `vendor/lib.rb` · 내부 링크 `workspace/context/wms/services.md` · "
    "미해석 `app/services/wms/missing.rb`.\n"
)
BILLING = (
    "# billing\n\n`app/services/billing/c.rb` `app/services/billing/d.rb` 가 `app/models/order.rb` 와 "
    "`app/models/invoice.rb` 를 갱신한다.\n"
)


def _make_repo(td: str) -> Path:
    repo = Path(td) / "repo"
    ctx = repo / "workspace" / "context"
    (ctx / "wms").mkdir(parents=True)
    (ctx / "rules").mkdir()
    (ctx / "boundaries").mkdir()
    (ctx / "MANIFEST.md").write_text(MANIFEST, encoding="utf-8")
    (ctx / "config.md").write_text(CONFIG, encoding="utf-8")
    (ctx / "wms" / "index.md").write_text(WMS_INDEX, encoding="utf-8")
    (ctx / "wms" / "services.md").write_text("---\ntype: services\n---\n## S\n`app/services/wms/a.rb`\n", encoding="utf-8")
    (ctx / "wms" / "enums.md").write_text("## E\nstate\n", encoding="utf-8")
    (ctx / "wms" / "notes.md").write_text("## N\nmemo\n", encoding="utf-8")
    (ctx / "rules" / "wms.md").write_text("# rules\n", encoding="utf-8")
    (ctx / "boundaries" / "wms--billing.md").write_text("# b\n", encoding="utf-8")
    (ctx / "billing.md").write_text(BILLING, encoding="utf-8")
    for rel in (
        "app/services/wms/a.rb", "app/services/wms/b.rb", "app/models/order.rb", "app/models/invoice.rb",
        "app/services/billing/c.rb", "app/services/billing/d.rb", "spec/wms_spec.rb", "vendor/lib.rb",
    ):
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x\n", encoding="utf-8")
    (repo / "tmp").mkdir()
    return repo


class DomainsAndDocsTest(unittest.TestCase):
    def test_list_domains_from_anchored_table(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_repo(td) / "workspace"
            self.assertEqual(rp.list_domains(ws), [("wms", ["wms/index.md"]), ("billing", ["billing.md"])])

    def test_domain_docs_and_boundaries(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_repo(td) / "workspace"
            names = [p.name for p in rp.domain_docs(ws, "wms", ["wms/index.md"])]
            self.assertEqual(names, ["enums.md", "index.md", "notes.md", "services.md"])
            self.assertEqual([p.name for p in rp.boundary_docs(ws, "billing")], ["wms--billing.md"])


class DerivePathsTest(unittest.TestCase):
    def test_exclusions_and_resolution(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_repo(td) / "workspace"
            ex = [rp.glob_regex(g) for g in rp.exclusion_globs(ws)]
            files = rp.resolved_sources(ws, rp.domain_docs(ws, "wms", ["wms/index.md"]), ex)
            self.assertEqual(files, ["app/models/order.rb", "app/services/wms/a.rb", "app/services/wms/b.rb"])

    def test_greedy_split_yields_precise_globs(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_repo(td) / "workspace"
            d = rp.derive_paths(ws)
            self.assertEqual(d["wms"].globs, ["app/services/wms/**"])          # 단일 모델 파일은 잃어도 되는 1건
            self.assertEqual(d["billing"].globs, ["app/models/**", "app/services/billing/**"])
            self.assertTrue(d["wms"].estimated)
            self.assertTrue(any("인용 경로 추정" in m for m in d["wms"].info))

    def test_sources_frontmatter_takes_precedence(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_repo(td) / "workspace"
            (ws / "context" / "billing.md").write_text(
                "---\nsources:\n  - app/billing/\n  - lib/bill.rb\n---\n" + BILLING, encoding="utf-8"
            )
            dp = rp.derive_paths(ws, ["billing"])["billing"]
            self.assertEqual(dp.globs, ["app/billing/**", "lib/bill.rb"])
            self.assertFalse(dp.estimated)

    def test_exclusivity_tie_removes_and_winner_keeps(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _make_repo(td)
            ws = repo / "workspace"
            # 두 도메인이 같은 디렉토리(app/shared) 를 인용 — 동률이면 둘 다 제외
            for rel in ("app/shared/x.rb", "app/shared/y.rb", "app/shared/z.rb"):
                (repo / rel).parent.mkdir(parents=True, exist_ok=True)
                (repo / rel).write_text("x\n", encoding="utf-8")
            (ws / "context" / "wms" / "index.md").write_text("`app/shared/x.rb` `app/shared/y.rb`\n", encoding="utf-8")
            (ws / "context" / "billing.md").write_text("`app/shared/x.rb` `app/shared/y.rb`\n", encoding="utf-8")
            d = rp.derive_paths(ws)
            self.assertEqual(d["wms"].globs, [])
            self.assertEqual(d["billing"].globs, [])
            self.assertTrue(any("동률" in m for m in d["wms"].info))
            # billing 이 더 많이 인용하면 billing 만 유지
            (ws / "context" / "billing.md").write_text("`app/shared/x.rb` `app/shared/y.rb` `app/shared/z.rb`\n", encoding="utf-8")
            d = rp.derive_paths(ws)
            self.assertEqual(d["billing"].globs, ["app/shared/**"])
            self.assertEqual(d["wms"].globs, [])
            self.assertTrue(any("`billing` 우선" in m for m in d["wms"].info))

    def test_unknown_domain_raises(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_repo(td) / "workspace"
            with self.assertRaises(rp.RulesPointerError):
                rp.derive_paths(ws, ["ghost"])

    def test_too_few_citations_skips(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_repo(td) / "workspace"
            (ws / "context" / "billing.md").write_text("`app/models/order.rb` 만 인용\n", encoding="utf-8")
            dp = rp.derive_paths(ws, ["billing"])["billing"]
            self.assertEqual(dp.globs, [])
            self.assertTrue(any("skip" in m for m in dp.info))


class AggregateGlobsTest(unittest.TestCase):
    def test_empty_and_root_files(self):
        self.assertEqual(rp.aggregate_globs([]), [])
        self.assertEqual(rp.aggregate_globs(["README.md"]), [("README.md", 1)])  # 유일하면 유지

    def test_cap_eight_top_level_dirs_by_count(self):
        files = [f"d{i}/a.py" for i in range(9)] + [f"d{i}/b.py" for i in range(9)] + ["d0/c.py"]
        out = rp.aggregate_globs(files)
        self.assertEqual(len(out), rp.MAX_GLOBS)
        self.assertIn(("d0/**", 3), out)

    def test_split_rejected_when_dropping_too_many(self):
        # 부모 20파일 중 단일 파일 디렉토리 3개(3파일 손실 > max(1, 2)) → 분할 거부, 상위 glob 유지
        files = [f"app/big/f{i}.rb" for i in range(17)] + ["app/s1/x.rb", "app/s2/x.rb", "app/s3/x.rb"]
        self.assertEqual(rp.aggregate_globs(files), [("app/**", 20)])

    def test_depth_limit_three(self):
        files = [f"a/b/c/d/f{i}.rb" for i in range(4)]
        self.assertEqual(rp.aggregate_globs(files), [("a/b/c/**", 4)])

    def test_deterministic_regardless_of_input_order(self):
        files = ["app/x/1.rb", "app/x/2.rb", "lib/y/1.rb", "lib/y/2.rb", "app/z/1.rb", "app/z/2.rb"]
        self.assertEqual(rp.aggregate_globs(files), rp.aggregate_globs(list(reversed(files))))


class PointersAndRenderTest(unittest.TestCase):
    def test_pointer_order_and_extra(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_repo(td) / "workspace"
            lines, extra = rp.select_pointers(ws, "wms", ["wms/index.md"])
            self.assertEqual(lines, [
                "- 진입: workspace/context/wms/index.md",
                "- 규칙: workspace/context/rules/wms.md",
                "- 본문: workspace/context/wms/enums.md",
                "- 본문: workspace/context/wms/services.md",
                "- 경계: workspace/context/boundaries/wms--billing.md",
            ])
            self.assertEqual(extra, 0)
            (ws / "context" / "wms" / "rules.md").write_text("## R\n", encoding="utf-8")
            _lines, extra = rp.select_pointers(ws, "wms", ["wms/index.md"])
            self.assertEqual(extra, 1)

    def test_compose_body_caps_lines_and_chars(self):
        many = [f"- 본문: workspace/context/d/{'x' * 60}{i}.md" for i in range(6)] + [
            f"- 경계: workspace/context/boundaries/d--{i}.md" for i in range(3)
        ]
        body = rp.compose_body("d", many, 0)
        self.assertLessEqual(len(body.splitlines()), rp.MAX_LINES)
        self.assertLessEqual(len(body), rp.MAX_CHARS)
        self.assertIn("- 그 외 ", body)
        self.assertTrue(body.endswith(rp.DETAIL_LINE))
        self.assertNotIn("- 경계:", body)  # 경계부터 접힌다

    def test_render_and_injected_body_and_paths(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_repo(td) / "workspace"
            content, info = rp.build_rules_file(ws, "wms")
            self.assertTrue(content.startswith("---\npaths:\n  - app/services/wms/**\n---\n"))
            self.assertIn(rp.MARKER_PREFIX, content)
            self.assertIn(rp.ESTIMATE_COMMENT, content)
            body = rp.injected_body(content)
            self.assertTrue(body.startswith("이 경로는 `wms` 도메인이다."))
            self.assertNotIn("<!--", body)
            self.assertLessEqual(len(body), rp.MAX_CHARS)
            self.assertEqual(rp.parse_paths(content), ["app/services/wms/**"])
            self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", body)  # C4 — 주입 본문에 치환 변수 없음


class WriteCheckHookTest(unittest.TestCase):
    def test_write_created_unchanged_updated_and_marker_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _make_repo(td)
            ws = repo / "workspace"
            statuses, info = rp.write_rules_files(ws)
            self.assertEqual(dict(statuses), {"wms": "created", "billing": "created"})
            self.assertTrue(any("새 세션부터" in m for m in info))
            self.assertEqual(dict(rp.write_rules_files(ws)[0]), {"wms": "unchanged", "billing": "unchanged"})
            p = rp.rules_path(ws, "wms")
            p.write_text(p.read_text(encoding="utf-8") + "\n- 추가\n", encoding="utf-8")
            self.assertEqual(dict(rp.write_rules_files(ws, ["wms"])[0]), {"wms": "updated"})
            p.write_text("# 내 규칙\n", encoding="utf-8")  # 마커 없음 → 보존
            statuses, info = rp.write_rules_files(ws, ["wms"])
            self.assertEqual(dict(statuses), {"wms": "skipped-unmanaged"})
            self.assertEqual(p.read_text(encoding="utf-8"), "# 내 규칙\n")

    def test_check_rows(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_repo(td) / "workspace"
            self.assertEqual([r[1] for r in rp.check_rules_files(ws)], ["missing", "missing"])
            rp.write_rules_files(ws)
            self.assertEqual([r[1] for r in rp.check_rules_files(ws)], ["ok", "ok"])
            p = rp.rules_path(ws, "billing")
            p.write_text(p.read_text(encoding="utf-8").replace("정산", "x") + "\n", encoding="utf-8")
            self.assertEqual(dict((r[0], r[1]) for r in rp.check_rules_files(ws))["billing"], "differs")

    def test_deterministic_generation(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_repo(td) / "workspace"
            a = {d: rp.build_rules_file(ws, d)[0] for d in ("wms", "billing")}
            b = {d: rp.build_rules_file(ws, d)[0] for d in ("wms", "billing")}
            self.assertEqual(a, b)

    def test_hook_once_per_session_per_domain(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _make_repo(td)
            ws = repo / "workspace"
            rp.write_rules_files(ws)
            os.environ["TMPDIR"] = str(repo / "tmp")
            try:
                t = rp.match_hook(ws, str(repo / "app" / "services" / "wms" / "a.rb"), "s1")
                self.assertIsNotNone(t)
                self.assertTrue(t.startswith("[도메인 포인터] 이 경로는 `wms` 도메인이다."))
                self.assertIsNone(rp.match_hook(ws, str(repo / "app" / "services" / "wms" / "b.rb"), "s1"))
                self.assertIsNotNone(rp.match_hook(ws, str(repo / "app" / "services" / "wms" / "b.rb"), "s2"))
                self.assertIsNone(rp.match_hook(ws, str(repo / "spec" / "wms_spec.rb"), "s3"))          # 미매칭
                self.assertIsNone(rp.match_hook(ws, str(ws / "context" / "wms" / "index.md"), "s3"))    # workspace 내부
                self.assertIsNone(rp.match_hook(ws, str(repo / "app" / "services" / "wms" / "a.rb"), ""))  # session 부재
                self.assertIsNone(rp.match_hook(ws, "/etc/hosts", "s4"))
            finally:
                os.environ.pop("TMPDIR", None)

    def test_hook_caps_two_domains(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _make_repo(td)
            ws = repo / "workspace"
            rdir = rp.rules_dir(ws)
            rdir.mkdir(parents=True)
            for d in ("a", "b", "c"):
                (rdir / f"pilot-{d}.md").write_text(
                    f"---\npaths:\n  - app/**\n---\n{rp.MARKER_LINE}\n이 경로는 `{d}` 도메인이다.\n", encoding="utf-8"
                )
            os.environ["TMPDIR"] = str(repo / "tmp")
            try:
                t = rp.match_hook(ws, str(repo / "app" / "models" / "order.rb"), "s9")
            finally:
                os.environ.pop("TMPDIR", None)
            self.assertEqual(t.count("도메인이다."), 2)
            self.assertIn("그 외 1 도메인", t)


class CliTest(unittest.TestCase):
    def _run(self, args, cwd, stdin=None, env=None):
        e = dict(os.environ)
        e.update(env or {})
        return subprocess.run([sys.executable, str(CLI), *args], cwd=cwd, input=stdin, capture_output=True, text=True, env=e)

    def test_write_check_hook_exit_codes(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _make_repo(td)
            r = self._run(["--all", "--write"], repo)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("created", r.stdout)
            self.assertEqual(self._run(["--all", "--check"], repo).returncode, 0)
            p = rp.rules_path(repo / "workspace", "wms")
            p.write_text(p.read_text(encoding="utf-8") + "\nextra\n", encoding="utf-8")
            self.assertEqual(self._run(["--all", "--check"], repo).returncode, 1)
            self.assertEqual(self._run(["--domain", "ghost"], repo).returncode, 2)
            self.assertEqual(self._run([], repo).returncode, 2)
            hook_in = json.dumps({"tool_input": {"file_path": str(repo / "app" / "services" / "wms" / "a.rb")}, "session_id": "cli"})
            r = self._run(["--hook"], repo, stdin=hook_in, env={"TMPDIR": str(repo / "tmp")})
            self.assertEqual(r.returncode, 0)
            out = json.loads(r.stdout)
            self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PostToolUse")
            self.assertIn("`wms` 도메인", out["hookSpecificOutput"]["additionalContext"])
            r2 = self._run(["--hook"], repo, stdin="not json", env={"TMPDIR": str(repo / "tmp")})
            self.assertEqual((r2.returncode, r2.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
