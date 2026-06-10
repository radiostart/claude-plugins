"""
tools/orchestrate-load.py 의 파싱 / 비교 / 도메인 추출 단위 테스트.

실행:
    python3 tests/tools/test_orchestrate_load.py
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "orchestrate-load.py"


def _load_mod():
    spec = importlib.util.spec_from_file_location("orchestrate_load_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = _load_mod()


class ParseSemver(unittest.TestCase):
    def test_three_part(self):
        self.assertEqual(m.parse_semver("0.2.5"), (0, 2, 5))

    def test_two_part_pads_patch(self):
        self.assertEqual(m.parse_semver("1.0"), (1, 0, 0))

    def test_invalid_returns_none(self):
        self.assertIsNone(m.parse_semver("not.a.version"))
        self.assertIsNone(m.parse_semver(None))
        self.assertIsNone(m.parse_semver(""))


class ComparePluginVersion(unittest.TestCase):
    def test_patch_diff_silent(self):
        self.assertIsNone(m.compare_plugin_version("0.2.4", "0.2.5"))

    def test_minor_upgrade_warns(self):
        result = m.compare_plugin_version("0.1.5", "0.2.0")
        self.assertIsNotNone(result)
        level, msg = result
        self.assertEqual(level, "WARN")
        self.assertIn("0.1.5", msg)
        self.assertIn("0.2.0", msg)

    def test_state_higher_than_plugin_warns(self):
        result = m.compare_plugin_version("0.3.0", "0.2.0")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "WARN")

    def test_missing_state_version_returns_info(self):
        result = m.compare_plugin_version(None, "0.2.5")
        self.assertEqual(result[0], "INFO")
        self.assertIn("0.2.5", result[1])

    def test_missing_current_returns_none(self):
        self.assertIsNone(m.compare_plugin_version("0.2.0", None))


class ParseStateMdActive(unittest.TestCase):
    def test_extracts_active_project_names(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(
                "| 순번 | 이름  | 상태   | 비고 |\n"
                "| --- | ----- | ------ | --- |\n"
                "| 1   | ProjA | 진행중 | x   |\n"
                "| 2   | ProjB | 완료   | y   |\n"
                "| 3   | ProjC | 진행중 | z   |\n"
            )
            p = Path(f.name)
        active = m.parse_state_md_active(p)
        self.assertEqual(active, ["ProjA", "ProjC"])

    def test_no_state_md_returns_empty(self):
        self.assertEqual(m.parse_state_md_active(Path("/nonexistent")), [])


class ParseStateYml(unittest.TestCase):
    def _write(self, content: str) -> Path:
        f = tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False, encoding="utf-8")
        f.write(content)
        f.close()
        return Path(f.name)

    def test_type_coercion_bool_null_int_string(self):
        p = self._write(
            "schema: v1.2\n"
            "analyzed: true\n"
            "tdd: false\n"
            "domain: null\n"
            "count: 42\n"
            'plugin_version: "0.2.5"\n'
        )
        d = m.parse_state_yml(p)
        self.assertEqual(d["schema"], "v1.2")
        self.assertIs(d["analyzed"], True)
        self.assertIs(d["tdd"], False)
        self.assertIsNone(d["domain"])
        self.assertEqual(d["count"], 42)
        self.assertEqual(d["plugin_version"], "0.2.5")  # 따옴표 strip 됨

    def test_missing_file_returns_none(self):
        self.assertIsNone(m.parse_state_yml(Path("/nonexistent.yml")))


class ParseLangTools(unittest.TestCase):
    def _write_manifest(self, body: str) -> Path:
        f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        f.write(body)
        f.close()
        return Path(f.name)

    def test_extracts_language_keys_only(self):
        manifest = self._write_manifest(
            "# foo\n\n"
            "## 언어·도구 기본값\n\n"
            "| 키 | 값 | 설명 |\n"
            "| --- | --- | --- |\n"
            "| `language` | `ruby` | 주 언어 |\n"
            "| `test_command` | `bundle exec rspec` | 테스트 |\n"
            "| `unknown_key` | `xxx` | 무시되어야 함 |\n"
            "\n## 다른 섹션\n"
        )
        d = m.parse_lang_tools(manifest)
        self.assertEqual(d.get("language"), "ruby")
        self.assertEqual(d.get("test_command"), "bundle exec rspec")
        self.assertNotIn("unknown_key", d)

    def test_no_section_returns_empty(self):
        manifest = self._write_manifest("# foo\n\n## 다른 섹션\n\n내용\n")
        self.assertEqual(m.parse_lang_tools(manifest), {})

    def test_missing_file_returns_none(self):
        """파일 부재·읽기 실패는 None — 호출부가 '손상' 으로 구분해 경고."""
        self.assertIsNone(m.parse_lang_tools(Path("/nonexistent/config.md")))


class ParseLangOverride(unittest.TestCase):
    def _write(self, body: str) -> Path:
        f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        f.write(body)
        f.close()
        return Path(f.name)

    def test_extracts_override_from_제한사항(self):
        p = self._write(
            "# 프로젝트\n\n"
            "## 제한사항\n\n"
            "- **language**: `python`\n"
            "- **test_command**: `pytest`\n"
            "- ignored_key: ignored\n"
            "\n## 다음 섹션\n"
        )
        d = m.parse_lang_override(p)
        self.assertEqual(d.get("language"), "python")
        self.assertEqual(d.get("test_command"), "pytest")
        self.assertNotIn("ignored_key", d)


class DetermineDomain(unittest.TestCase):
    def _write(self, body: str) -> Path:
        f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        f.write(body)
        f.close()
        return Path(f.name)

    def test_domain_extracted(self):
        p = self._write("## 제한사항\n\n- **domain**: orders\n")
        self.assertEqual(m.determine_domain(p), "orders")

    def test_domain_with_backticks(self):
        p = self._write("- domain: `admin`\n")
        self.assertEqual(m.determine_domain(p), "admin")

    def test_no_domain_returns_none(self):
        p = self._write("# foo\n\n내용\n")
        self.assertIsNone(m.determine_domain(p))


class ReadFocus(unittest.TestCase):
    def _write(self, body: str) -> Path:
        f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        f.write(body)
        f.close()
        return Path(f.name)

    def test_drops_first_heading(self):
        p = self._write("# Focus\n\n실제 내용\n")
        self.assertEqual(m.read_focus(p), "실제 내용")

    def test_no_heading_returns_full_text(self):
        p = self._write("그냥 본문\n")
        self.assertEqual(m.read_focus(p), "그냥 본문")

    def test_empty_file_returns_none(self):
        p = self._write("")
        self.assertIsNone(m.read_focus(p))

    def test_missing_file_returns_none(self):
        self.assertIsNone(m.read_focus(Path("/nonexistent")))

    def test_heading_only_returns_heading_text(self):
        """본문 없이 heading 만 있는 focus 파일은 heading 텍스트를 지시로 반환."""
        p = self._write("# 소프트 딜리트 빼줘\n")
        self.assertEqual(m.read_focus(p), "소프트 딜리트 빼줘")


class ParseManifestDomainFiles(unittest.TestCase):
    def _write(self, body: str) -> Path:
        f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        f.write(body)
        f.close()
        return Path(f.name)

    def test_single_row_entry(self):
        p = self._write(
            "## 도메인 분류\n\n"
            "| 도메인 | 진입 파일 | 설명 |\n"
            "| --- | --- | --- |\n"
            "| orders | `orders.md` | 주문 |\n"
        )
        self.assertEqual(m.parse_manifest_domain_files(p, "orders"), ["orders.md"])

    def test_multiple_rows_all_returned(self):
        """같은 도메인의 행이 여러 개면 표 순서대로 전부 반환."""
        p = self._write(
            "## 도메인 분류\n\n"
            "| 도메인 | 진입 파일 | 설명 |\n"
            "| --- | --- | --- |\n"
            "| orders | `orders/index.md` | 개요 |\n"
            "| orders | `orders/states.md` | 상태 전이 |\n"
            "| payments | `payments.md` | 결제 |\n"
        )
        self.assertEqual(
            m.parse_manifest_domain_files(p, "orders"),
            ["orders/index.md", "orders/states.md"],
        )

    def test_duplicate_entries_deduped(self):
        p = self._write(
            "## 도메인 분류\n\n"
            "| orders | `orders.md` | a |\n"
            "| orders | `orders.md` | b |\n"
        )
        self.assertEqual(m.parse_manifest_domain_files(p, "orders"), ["orders.md"])

    def test_workspace_context_prefix_stripped(self):
        p = self._write(
            "## 도메인 분류\n\n"
            "| orders | `workspace/context/orders.md` | 주문 |\n"
        )
        self.assertEqual(m.parse_manifest_domain_files(p, "orders"), ["orders.md"])

    def test_no_match_returns_empty(self):
        p = self._write("## 도메인 분류\n\n| payments | `payments.md` | 결제 |\n")
        self.assertEqual(m.parse_manifest_domain_files(p, "orders"), [])


class ParseManifestExternalRefs(unittest.TestCase):
    def _write(self, body: str) -> Path:
        f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        f.write(body)
        f.close()
        return Path(f.name)

    def test_extracts_rows(self):
        p = self._write(
            "## 외부 도메인 reference (learn 미완료)\n\n"
            "| 추정 도메인 | 클래스 (개수) | 추천 후속 학습 |\n"
            "| --- | --- | --- |\n"
            "| schoice | Schoice::Order, Schoice::Box (2) | `/pilot:learn app/models/schoice/` (auto) |\n"
            "| billing | Billing::Invoice (1) | `/pilot:learn app/services/billing/` (auto) |\n"
        )
        refs = m.parse_manifest_external_refs(p)
        self.assertEqual([r[0] for r in refs], ["schoice", "billing"])
        self.assertIn("Schoice::Order", refs[0][1])

    def test_no_section_returns_empty(self):
        p = self._write("## 도메인 분류\n\n| orders | `orders.md` | x |\n")
        self.assertEqual(m.parse_manifest_external_refs(p), [])

    def test_header_row_skipped(self):
        p = self._write(
            "## 외부 도메인 reference\n\n"
            "| 추정 도메인 | 클래스 (개수) | 추천 후속 학습 |\n"
            "| --- | --- | --- |\n"
        )
        self.assertEqual(m.parse_manifest_external_refs(p), [])


class BuildLoadPlanIntegration(unittest.TestCase):
    """build_load_plan 통합 — 실제 workspace 디렉토리 트리 만들고 호출."""

    def test_planner_phase_loads_manifest_and_project(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            project = "P"
            (ws / "context").mkdir(parents=True)
            (ws / "context" / "MANIFEST.md").write_text("# manifest\n", encoding="utf-8")
            (ws / "context" / "config.md").write_text(
                "## 언어·도구 기본값\n\n| `language` | `python` | x |\n", encoding="utf-8"
            )
            (ws / "projects" / project).mkdir(parents=True)
            (ws / "projects" / project / "project.md").write_text("# proj\n", encoding="utf-8")

            files, hints, config = m.build_load_plan(
                workspace=ws, project=project,
                domain=None, tdd=False, phase="planner",
            )
            self.assertIn("workspace/context/MANIFEST.md", files)
            self.assertIn(f"workspace/projects/{project}/project.md", files)
            self.assertEqual(config.get("language"), "python")
            # 도메인 미지정 → 힌트 포함
            self.assertTrue(any("도메인 판정 실패" in h for h in hints))

    def test_project_md_overrides_config(self):
        """project.md 제한사항이 context/config.md 값을 override."""
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            project = "P"
            (ws / "context").mkdir(parents=True)
            (ws / "context" / "config.md").write_text(
                "## 언어·도구 기본값\n\n"
                "| `language` | `ruby` | x |\n"
                "| `test_command` | `bundle exec rspec` | x |\n",
                encoding="utf-8",
            )
            (ws / "projects" / project).mkdir(parents=True)
            (ws / "projects" / project / "project.md").write_text(
                "## 제한사항\n\n- **test_command**: `bundle exec rspec --format documentation`\n",
                encoding="utf-8",
            )

            _, _, config = m.build_load_plan(
                workspace=ws, project=project,
                domain=None, tdd=False, phase="planner",
            )
            # 프로젝트 override 적용
            self.assertEqual(config.get("test_command"), "bundle exec rspec --format documentation")
            # 프로젝트가 override 안 한 키는 context 값 유지
            self.assertEqual(config.get("language"), "ruby")

    def test_generator_phase_includes_coding_md(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / "projects" / "P").mkdir(parents=True)
            files, _, _ = m.build_load_plan(
                workspace=ws, project="P",
                domain=None, tdd=False, phase="generator",
            )
            self.assertTrue(any("coding.md" in f for f in files))

    def _ws_with_conventions(self, td: str) -> Path:
        """conventions_doc/evals 가 선언되고 실제 파일도 존재하는 workspace."""
        ws = Path(td)
        (ws / "context" / "evals").mkdir(parents=True)
        (ws / "context" / "config.md").write_text(
            "## 언어·도구 기본값\n\n"
            "| `conventions_doc` | `context/conventions.md` | x |\n"
            "| `conventions_evals` | `context/evals/conventions.json` | x |\n",
            encoding="utf-8",
        )
        (ws / "context" / "conventions.md").write_text("# 관행\n", encoding="utf-8")
        (ws / "context" / "evals" / "conventions.json").write_text("{}", encoding="utf-8")
        (ws / "projects" / "P").mkdir(parents=True)
        return ws

    def test_generator_phase_loads_conventions_files(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws_with_conventions(td)
            files, _, _ = m.build_load_plan(
                workspace=ws, project="P",
                domain=None, tdd=False, phase="generator",
            )
            self.assertIn("workspace/context/conventions.md", files)
            self.assertIn("workspace/context/evals/conventions.json", files)

    def test_evaluator_phase_loads_conventions_files(self):
        """evaluator 도 generator 와 같은 conventions 파일로 독립 검증한다."""
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws_with_conventions(td)
            files, _, _ = m.build_load_plan(
                workspace=ws, project="P",
                domain=None, tdd=False, phase="evaluator",
            )
            self.assertIn("workspace/context/conventions.md", files)
            self.assertIn("workspace/context/evals/conventions.json", files)

    def test_evaluator_declared_but_missing_conventions_hints(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / "context").mkdir(parents=True)
            (ws / "context" / "config.md").write_text(
                "## 언어·도구 기본값\n\n"
                "| `conventions_doc` | `context/conventions.md` | x |\n",
                encoding="utf-8",
            )
            (ws / "projects" / "P").mkdir(parents=True)
            files, hints, _ = m.build_load_plan(
                workspace=ws, project="P",
                domain=None, tdd=False, phase="evaluator",
            )
            self.assertNotIn("workspace/context/conventions.md", files)
            self.assertTrue(any("conventions_doc" in h and "파일 없음" in h for h in hints))

    def test_planner_phase_skips_conventions_files(self):
        """planner 는 conventions 자동 로드 대상이 아니다 (generator·evaluator 전용)."""
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws_with_conventions(td)
            files, _, _ = m.build_load_plan(
                workspace=ws, project="P",
                domain=None, tdd=False, phase="planner",
            )
            self.assertNotIn("workspace/context/conventions.md", files)
            self.assertNotIn("workspace/context/evals/conventions.json", files)

    def _ws_with_boundaries(self, td: str) -> Path:
        """boundaries/ 경계 계약 문서가 있는 workspace (활성 도메인 orders)."""
        ws = Path(td)
        (ws / "context" / "boundaries").mkdir(parents=True)
        (ws / "context" / "boundaries" / "orders--payments.md").write_text(
            "# 경계: orders → payments\n", encoding="utf-8"
        )
        (ws / "context" / "boundaries" / "shipping--orders.md").write_text(
            "# 경계: shipping → orders\n", encoding="utf-8"
        )
        (ws / "context" / "boundaries" / "shipping--billing.md").write_text(
            "# 경계: shipping → billing\n", encoding="utf-8"
        )
        (ws / "projects" / "P").mkdir(parents=True)
        return ws

    def test_boundary_docs_loaded_both_directions(self):
        """domain=orders 면 orders--*.md (정방향) 와 *--orders.md (역방향) 만 로드."""
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws_with_boundaries(td)
            files, hints, _ = m.build_load_plan(
                workspace=ws, project="P",
                domain="orders", tdd=False, phase="planner",
            )
            self.assertIn("workspace/context/boundaries/orders--payments.md", files)
            self.assertIn("workspace/context/boundaries/shipping--orders.md", files)
            self.assertNotIn("workspace/context/boundaries/shipping--billing.md", files)
            self.assertTrue(any("경계 계약" in h for h in hints))

    def test_no_boundaries_dir_silent(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / "projects" / "P").mkdir(parents=True)
            files, _, _ = m.build_load_plan(
                workspace=ws, project="P",
                domain="orders", tdd=False, phase="planner",
            )
            self.assertFalse(any("boundaries" in f for f in files))

    def test_external_refs_hint_with_boundary_prescription(self):
        """MANIFEST 외부 도메인 reference 행 → 미학습 안내 + boundary learn 처방 hint."""
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / "context").mkdir(parents=True)
            (ws / "context" / "MANIFEST.md").write_text(
                "## 도메인 분류\n\n"
                "| orders | `orders.md` | 주문 |\n\n"
                "## 외부 도메인 reference (learn 미완료)\n\n"
                "| 추정 도메인 | 클래스 (개수) | 추천 후속 학습 |\n"
                "| --- | --- | --- |\n"
                "| schoice | Schoice::Order (1) | `/pilot:learn app/models/schoice/` (auto) |\n",
                encoding="utf-8",
            )
            (ws / "context" / "orders.md").write_text("# orders\n", encoding="utf-8")
            (ws / "projects" / "P").mkdir(parents=True)
            _, hints, _ = m.build_load_plan(
                workspace=ws, project="P",
                domain="orders", tdd=False, phase="planner",
            )
            joined = " ".join(hints)
            self.assertIn("schoice", joined)
            self.assertIn("--boundary", joined)

    def test_tdd_true_loads_rgr_md(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / "projects" / "P").mkdir(parents=True)
            files, hints, _ = m.build_load_plan(
                workspace=ws, project="P",
                domain=None, tdd=True, phase="planner",
            )
            self.assertTrue(any("rgr.md" in f for f in files))
            self.assertTrue(any("TDD" in h for h in hints))

    def test_characterize_mode_overrides_tdd(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / "projects" / "P").mkdir(parents=True)
            files, hints, _ = m.build_load_plan(
                workspace=ws, project="P",
                domain=None, tdd=True, phase="planner",
                mode="characterize",
            )
            self.assertTrue(any("characterize.md" in f for f in files))
            # tdd=true 였지만 mode 가 우선이므로 경고 힌트 포함
            self.assertTrue(any("characterize" in h for h in hints))


class HasPathTraversal(unittest.TestCase):
    def test_plain_identifier_is_safe(self):
        self.assertFalse(m.has_path_traversal("MyProject"))
        self.assertFalse(m.has_path_traversal("proj-1"))
        self.assertFalse(m.has_path_traversal("retail_v2"))

    def test_path_separator_flagged(self):
        self.assertTrue(m.has_path_traversal("a/b"))
        self.assertTrue(m.has_path_traversal("a\\b"))

    def test_dotdot_flagged(self):
        self.assertTrue(m.has_path_traversal(".."))
        self.assertTrue(m.has_path_traversal("../etc"))


class MainStateErrors(unittest.TestCase):
    """main() 의 .agent-state.yml 진단 메시지 — 누락 / 빈 파일 / 손상 구분."""

    def _run(self, workspace: Path) -> tuple[int, dict]:
        import json
        import subprocess

        proc = subprocess.run(
            ["python3", str(TOOL_PATH), "--phase", "planner",
             "--workspace", str(workspace)],
            capture_output=True, text=True,
        )
        return proc.returncode, json.loads(proc.stdout)

    def _scaffold(self, td: str) -> Path:
        """STATE.md(1 개 진행중) + projects/P/ 까지 구성. state.yml 은 미생성."""
        ws = Path(td)
        (ws / "projects" / "P").mkdir(parents=True)
        (ws / "STATE.md").write_text(
            "| 순번 | 이름 | 상태 | 비고 |\n"
            "| --- | --- | --- | --- |\n"
            "| 1 | P | 진행중 | x |\n",
            encoding="utf-8",
        )
        return ws

    def test_missing_state_reports_누락(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._scaffold(td)
            rc, out = self._run(ws)
            self.assertEqual(rc, 1)
            self.assertIn("누락", out["error"])

    def test_empty_state_reports_비어있음(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._scaffold(td)
            (ws / "projects" / "P" / ".agent-state.yml").write_text(
                "", encoding="utf-8"
            )
            rc, out = self._run(ws)
            self.assertEqual(rc, 1)
            self.assertIn("비어", out["error"])
            self.assertNotIn("누락", out["error"])

    def test_comments_only_state_reports_비어있음(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._scaffold(td)
            (ws / "projects" / "P" / ".agent-state.yml").write_text(
                "# 주석만 있는 파일\n# key 없음\n", encoding="utf-8"
            )
            rc, out = self._run(ws)
            self.assertEqual(rc, 1)
            self.assertIn("비어", out["error"])

    def test_traversal_in_project_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / "projects").mkdir(parents=True)
            (ws / "STATE.md").write_text(
                "| 순번 | 이름 | 상태 | 비고 |\n"
                "| --- | --- | --- | --- |\n"
                "| 1 | ../evil | 진행중 | x |\n",
                encoding="utf-8",
            )
            rc, out = self._run(ws)
            self.assertEqual(rc, 1)
            self.assertIn("허용되지 않는 문자", out["error"])


if __name__ == "__main__":
    unittest.main()
