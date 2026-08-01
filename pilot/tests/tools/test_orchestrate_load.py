"""
tools/orchestrate-load.py 의 파싱 / 비교 / 도메인 추출 단위 테스트.

실행:
    python3 tests/tools/test_orchestrate_load.py
"""

import importlib.util
import os
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
    def test_extracts_active_mode_name_pairs(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(
                "| 모드 | 이름 | 상태 |\n"
                "| --- | ----- | ------ |\n"
                "| project | ProjA | 진행중 |\n"
                "| issue | hotfix-1 | 진행중 |\n"
                "| project | ProjB | 완료 |\n"
            )
            p = Path(f.name)
        active = m.parse_state_md_active(p)
        self.assertEqual(active, [("project", "ProjA"), ("issue", "hotfix-1")])

    def test_legacy_numeric_mode_column_passthrough(self):
        """legacy 표 (| 순번 | 이름 | 상태 | 비고 |) — 첫 칸 순번이 mode 로
        그대로 전달되고, 소비부 (main) 가 `issue` 외 값을 project 로 폴백한다."""
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
        self.assertEqual(active, [("1", "ProjA"), ("3", "ProjC")])

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

    def test_regression_command_key_accepted(self):
        """regression_command 는 LANG_KEYS 화이트리스트 등록 키 — drop 되지 않는다."""
        manifest = self._write_manifest(
            "## 언어·도구 기본값\n\n"
            "| `regression_command` | `bundle exec rspec spec/` | 광역 회귀 |\n"
        )
        d = m.parse_lang_tools(manifest)
        self.assertEqual(d.get("regression_command"), "bundle exec rspec spec/")

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

    def test_korean_domain_label(self):
        """issue.md 상단의 `도메인: {값}` 라인도 파싱한다 (work_mode 계약)."""
        p = self._write("# 이슈 제목\n\n도메인: orders\n\n## 현상\n")
        self.assertEqual(m.determine_domain(p), "orders")

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

    def test_prose_prefixed_header_does_not_shadow_real_section(self):
        """실버그 재현 (#20 스텝 6-①, D1) — 실제 workspace/context/MANIFEST.md 형상.

        본문 안내 blockquote 가 `## 도메인 분류` 리터럴을 인용해도(단독 H2 라인이
        아님) anchored 매칭이 이를 건너뛰고 실제 표를 정상 파싱해야 한다. 구
        un-anchored 정규식(`re.search`)은 이 prose 를 먼저 매칭해 빈 리스트를
        반환했다(재현 대상 실버그).
        """
        p = self._write(
            "# Domain Manifest\n\n"
            "> **자동 로드 — 도메인 진입 파일** (선택)\n"
            ">\n"
            "> `## 도메인 분류` H2 + 3 컬럼 표로 작성하면 플러그인이 자동으로 로드한다.\n\n"
            "## 도메인 분류\n\n"
            "| 도메인 | 진입 파일 | 설명 |\n"
            "| --- | --- | --- |\n"
            "| orders | `orders.md` | 주문 |\n"
        )
        self.assertEqual(m.parse_manifest_domain_files(p, "orders"), ["orders.md"])

    def test_fenced_example_header_ignored(self):
        """펜스 코드블록 안의 예시 H2 는 무시하고 실제 섹션만 파싱 (critic C4)."""
        p = self._write(
            "# Domain Manifest\n\n"
            "예시:\n\n"
            "```markdown\n"
            "## 도메인 분류\n\n"
            "| 도메인 | 진입 파일 | 설명 |\n"
            "| --- | --- | --- |\n"
            "| example | `example.md` | 예시 |\n"
            "```\n\n"
            "## 도메인 분류\n\n"
            "| 도메인 | 진입 파일 | 설명 |\n"
            "| --- | --- | --- |\n"
            "| orders | `orders.md` | 주문 |\n"
        )
        self.assertEqual(m.parse_manifest_domain_files(p, "orders"), ["orders.md"])

    def test_suffix_variant_header_intentionally_not_matched(self):
        """suffix 붙은 H2 변형은 의도적으로 미매칭 (critic C5 — 회귀 성격 수용, 문서화).

        anchored 정규식은 `## 도메인 분류` 가 단독 라인일 때만 매칭한다.
        `## 도메인 분류 (수동 관리)` 같은 suffix 변형은 구 계약에서는 동작했으나
        (learn SKILL.md:80 의 "코드블록·prose 인용 무시" 계약 완전 구현을 위해)
        이 케이스는 의도적으로 non-match 로 남긴다.
        """
        p = self._write(
            "## 도메인 분류 (수동 관리)\n\n"
            "| 도메인 | 진입 파일 | 설명 |\n"
            "| --- | --- | --- |\n"
            "| orders | `orders.md` | 주문 |\n"
        )
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


class MainIssueMode(unittest.TestCase):
    """main() 의 issue 모드 (STATE.md `| issue | {이슈명} | 진행중 |`) 계약.

    상태 파일 없이 issues/{이슈명}/issue.md 가 단건 명세 (stateless).
    analyzed=false·tdd=false·mode=null 고정, project.md·prompts/ 미로드,
    focus 는 issues/ 경로. 계약 상세: docs/how-to/issue-cycle.md.
    """

    def _run(self, workspace: Path, *extra: str) -> tuple[int, dict]:
        import json
        import subprocess

        proc = subprocess.run(
            ["python3", str(TOOL_PATH), "--phase", "planner",
             "--workspace", str(workspace), *extra],
            capture_output=True, text=True,
        )
        return proc.returncode, json.loads(proc.stdout)

    def _scaffold(self, td: str, issue: str = "hotfix-1", state_row: str | None = None) -> Path:
        ws = Path(td)
        (ws / "context").mkdir(parents=True)
        (ws / "context" / "MANIFEST.md").write_text(
            "## 도메인 분류\n\n"
            "| 도메인 | 진입 파일 | 설명 |\n"
            "| --- | --- | --- |\n"
            "| orders | `orders.md` | 주문 |\n",
            encoding="utf-8",
        )
        (ws / "context" / "orders.md").write_text("# orders\n", encoding="utf-8")
        row = state_row if state_row is not None else f"| issue | {issue} | 진행중 |"
        (ws / "STATE.md").write_text(
            "| 모드 | 이름 | 상태 |\n| --- | --- | --- |\n" + row + "\n",
            encoding="utf-8",
        )
        issue_dir = ws / "issues" / issue
        issue_dir.mkdir(parents=True)
        (issue_dir / "issue.md").write_text(
            "# 제목\n\n도메인: orders\n\n## 현상\n\n- 증상\n", encoding="utf-8"
        )
        return ws

    def test_issue_mode_contract_fields_and_files(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._scaffold(td)
            rc, out = self._run(ws)
            self.assertEqual(rc, 0, out.get("error"))
            self.assertEqual(out["work_mode"], "issue")
            self.assertEqual(out["project"], "hotfix-1")
            self.assertIs(out["analyzed"], False)
            self.assertIs(out["tdd"], False)
            self.assertIsNone(out["mode"])
            self.assertEqual(out["domain"], "orders")  # issue.md `도메인:` 라인
            self.assertIn("workspace/issues/hotfix-1/issue.md", out["files_to_read"])
            self.assertIn("workspace/context/orders.md", out["files_to_read"])
            # project 전제 항목 억제 — project.md·prompts/ 미로드, 부재 힌트도 없음
            self.assertFalse(any("project.md" in f for f in out["files_to_read"]))
            self.assertFalse(any("prompts/" in f for f in out["files_to_read"]))
            self.assertFalse(any("project.md 없음" in h for h in out["hints"]))
            self.assertFalse(any("prompts/" in h for h in out["hints"]))
            self.assertTrue(any("[work_mode] issue" in h for h in out["hints"]))

    def test_issue_mode_all_phases_exit_zero(self):
        """4 phase 전부 issue 모드 계약으로 exit 0 (spec smoke 게이트의 자동화)."""
        import json
        import subprocess

        with tempfile.TemporaryDirectory() as td:
            ws = self._scaffold(td)
            for phase in ("planner", "planner-critic", "generator", "evaluator"):
                proc = subprocess.run(
                    ["python3", str(TOOL_PATH), "--phase", phase,
                     "--workspace", str(ws)],
                    capture_output=True, text=True,
                )
                out = json.loads(proc.stdout)
                self.assertEqual(proc.returncode, 0, (phase, out.get("error")))
                self.assertEqual(out["work_mode"], "issue", phase)

    def test_issue_focus_read_from_issues_dir(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self._scaffold(td)
            (ws / "issues" / "hotfix-1" / ".focus.md").write_text(
                "# Focus\n\n롤백 스크립트 먼저\n", encoding="utf-8"
            )
            rc, out = self._run(ws)
            self.assertEqual(rc, 0, out.get("error"))
            self.assertEqual(out["focus"], "롤백 스크립트 먼저")

    def test_missing_issue_md_reports_issue_context_error(self):
        """이슈 폴더 부재 → issue 맥락 에러. 오도성 처방 (.agent-state·projects/) 금지."""
        with tempfile.TemporaryDirectory() as td:
            ws = self._scaffold(td, state_row="| issue | ghost | 진행중 |")
            rc, out = self._run(ws)
            self.assertEqual(rc, 1)
            self.assertIn("issues/ghost/issue.md 없음", out["error"])
            self.assertNotIn(".agent-state", out["error"])
            self.assertNotIn("projects/", out["error"])

    def test_bare_issue_row_unsupported(self):
        """`| issue | - |` (이슈명 없는 bare 진입) 는 사이클 비지원 안내."""
        with tempfile.TemporaryDirectory() as td:
            ws = self._scaffold(td, state_row="| issue | - | 진행중 |")
            rc, out = self._run(ws)
            self.assertEqual(rc, 1)
            self.assertIn("사이클 비지원", out["error"])

    def test_explicit_project_flag_forces_project_mode(self):
        """issue 활성 중에도 --project 명시는 STATE 우회 project 강제
        (corrupt-state 탈출구 보존)."""
        with tempfile.TemporaryDirectory() as td:
            ws = self._scaffold(td)
            rc, out = self._run(ws, "--project", "SomeProj")
            self.assertEqual(rc, 1)  # 프로젝트 state 부재 에러 (project 경로로 감)
            self.assertEqual(out["work_mode"], "project")
            self.assertIn(".agent-state.yml", out["error"])


class SsotLoad(unittest.TestCase):
    """SSOT 강제 로드 — identity.yml·guardrails.md·wrapper-protocol.md 3종
    (instincts.yaml 은 제거됨, 감사 F17). wrapper-protocol.md 는 #20 스텝 6-③(D2)
    에서 배선 — agents/pilot-*.md 상단 "Read 지시 1줄"과 이중화."""

    def _plan_files(self, plugin_root_env: str | None) -> tuple[list, list]:
        saved = os.environ.get(m.PLUGIN_ROOT_ENV)
        try:
            if plugin_root_env is None:
                os.environ.pop(m.PLUGIN_ROOT_ENV, None)
            else:
                os.environ[m.PLUGIN_ROOT_ENV] = plugin_root_env
            with tempfile.TemporaryDirectory() as td:
                ws = Path(td)
                (ws / "projects" / "P").mkdir(parents=True)
                files, hints, _ = m.build_load_plan(
                    workspace=ws, project="P",
                    domain=None, tdd=False, phase="planner",
                )
            return files, hints
        finally:
            if saved is None:
                os.environ.pop(m.PLUGIN_ROOT_ENV, None)
            else:
                os.environ[m.PLUGIN_ROOT_ENV] = saved

    def test_loads_identity_and_guardrails_not_instincts(self):
        files, _ = self._plan_files(str(PLUGIN_ROOT))
        self.assertTrue(any(f.endswith("shared/identity.yml") for f in files))
        self.assertTrue(any(f.endswith("shared/guardrails.md") for f in files))
        self.assertFalse(any("instincts" in f for f in files))

    def test_loads_wrapper_protocol(self):
        """wrapper-protocol.md 가 files_to_read 에 배선됨 (D2, #19 전달사항 :157 소비)."""
        files, _ = self._plan_files(str(PLUGIN_ROOT))
        self.assertTrue(any(f.endswith("shared/wrapper-protocol.md") for f in files))

    def test_unresolvable_root_appends_without_check(self):
        """CLAUDE_PLUGIN_ROOT 미설정 시 리터럴 placeholder 로 무조건 포함 (기존 동작 유지)."""
        files, _ = self._plan_files(None)
        self.assertTrue(any("identity.yml" in f for f in files))
        self.assertTrue(any("guardrails.md" in f for f in files))
        self.assertTrue(any("wrapper-protocol.md" in f for f in files))

    def test_missing_ssot_file_skipped_with_warn(self):
        """SSOT 파일 부재 시 존재하지 않는 Read 지시 대신 WARN 힌트 + 생략 (감사 G3)."""
        with tempfile.TemporaryDirectory() as fake_root:
            files, hints = self._plan_files(fake_root)
            self.assertFalse(any("identity.yml" in f for f in files))
            self.assertFalse(any("guardrails.md" in f for f in files))
            self.assertFalse(any("wrapper-protocol.md" in f for f in files))
            self.assertTrue(any("SSOT 파일 없음" in h for h in hints))


class BuildInstructions(unittest.TestCase):
    """instructions 필드 — wrapper 공통 JSON 처리 지시의 정본 (감사 F29)."""

    def test_all_phases_have_five_directives(self):
        for phase in ("planner", "planner-critic", "generator", "evaluator"):
            ins = m.build_instructions(phase)
            self.assertEqual(len(ins), 5, phase)
            self.assertIn("error 필드", ins[0])
            self.assertIn("files_to_read", ins[1])
            self.assertIn("focus", ins[2])

    def test_focus_directive_is_phase_specific(self):
        directives = {
            phase: m.build_instructions(phase)[2]
            for phase in ("planner", "planner-critic", "generator", "evaluator")
        }
        self.assertEqual(len(set(directives.values())), 4)
        self.assertIn("계획", directives["planner"])
        self.assertIn("챌린지", directives["planner-critic"])
        self.assertIn("구현", directives["generator"])
        self.assertIn("검토", directives["evaluator"])


if __name__ == "__main__":
    unittest.main()
