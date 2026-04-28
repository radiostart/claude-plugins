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
        p = self._write("## 제한사항\n\n- **domain**: retail\n")
        self.assertEqual(m.determine_domain(p), "retail")

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
                domain=None, analyzed=False, tdd=False, phase="planner",
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
                domain=None, analyzed=False, tdd=False, phase="planner",
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
                domain=None, analyzed=False, tdd=False, phase="generator",
            )
            self.assertTrue(any("coding.md" in f for f in files))

    def test_tdd_true_loads_rgr_md(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / "projects" / "P").mkdir(parents=True)
            files, hints, _ = m.build_load_plan(
                workspace=ws, project="P",
                domain=None, analyzed=False, tdd=True, phase="planner",
            )
            self.assertTrue(any("rgr.md" in f for f in files))
            self.assertTrue(any("TDD" in h for h in hints))

    def test_characterize_mode_overrides_tdd(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / "projects" / "P").mkdir(parents=True)
            files, hints, _ = m.build_load_plan(
                workspace=ws, project="P",
                domain=None, analyzed=False, tdd=True, phase="planner",
                mode="characterize",
            )
            self.assertTrue(any("characterize.md" in f for f in files))
            # tdd=true 였지만 mode 가 우선이므로 경고 힌트 포함
            self.assertTrue(any("characterize" in h for h in hints))


if __name__ == "__main__":
    unittest.main()
