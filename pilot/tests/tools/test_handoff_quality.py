"""
tools/handoff-quality.py 단위 테스트.

실행:
    python3 tests/tools/test_handoff_quality.py
"""

import importlib.util
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "handoff-quality.py"
FIXTURES = PLUGIN_ROOT / "tests" / "fixtures" / "handoff-quality"


def _load_mod():
    import sys
    tools_dir = str(PLUGIN_ROOT / "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    spec = importlib.util.spec_from_file_location("handoff_quality_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = _load_mod()


class ClassifyChangeItem(unittest.TestCase):
    def test_concrete_with_extension(self):
        self.assertEqual(m.classify_change_item("`app/services/foo.rb`"), "concrete")
        self.assertEqual(m.classify_change_item("app/services/foo.rb"), "concrete")
        self.assertEqual(m.classify_change_item("spec/models/order_spec.rb"), "concrete")

    def test_directory(self):
        self.assertEqual(m.classify_change_item("app/services/"), "directory")
        # path-like 이지만 확장자 없음 — directory 추정
        self.assertEqual(m.classify_change_item("app/services/payment"), "directory")

    def test_vague_placeholder(self):
        self.assertEqual(m.classify_change_item("TBD"), "vague")
        self.assertEqual(m.classify_change_item("추후 결정"), "vague")
        self.assertEqual(m.classify_change_item("결제 관련 파일들"), "vague")

    def test_vague_no_path(self):
        self.assertEqual(m.classify_change_item("서비스 레이어"), "vague")
        self.assertEqual(m.classify_change_item("모델"), "vague")


class ParseChangeFiles(unittest.TestCase):
    def test_parses_basic_items(self):
        text = (
            "## 구현 계획\n"
            "### 변경 파일\n"
            "- [ ] `app/services/foo.rb` — 신규 메서드 추가\n"
            "- [x] `app/models/bar.rb`\n"
            "- 추후 결정\n"
        )
        items = m.parse_change_files(text)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["type"], "concrete")
        self.assertTrue(items[0]["has_reason"])
        self.assertEqual(items[1]["type"], "concrete")
        self.assertFalse(items[1]["has_reason"])
        self.assertEqual(items[2]["type"], "vague")

    def test_no_section_returns_empty(self):
        text = "## 다른 섹션\n- foo\n"
        self.assertEqual(m.parse_change_files(text), [])


class EvaluateChangeFiles(unittest.TestCase):
    def test_empty_returns_none_scores(self):
        r = m.evaluate_change_files([])
        self.assertEqual(r["total"], 0)
        self.assertIsNone(r["specificity_score"])

    def test_all_concrete(self):
        items = [
            {"type": "concrete", "has_reason": True},
            {"type": "concrete", "has_reason": True},
        ]
        r = m.evaluate_change_files(items)
        self.assertEqual(r["specificity_score"], 1.0)
        self.assertEqual(r["reason_coverage"], 1.0)

    def test_mixed(self):
        items = [
            {"type": "concrete", "has_reason": True},
            {"type": "vague", "has_reason": False},
            {"type": "directory", "has_reason": True},
            {"type": "concrete", "has_reason": False},
        ]
        r = m.evaluate_change_files(items)
        self.assertEqual(r["concrete"], 2)
        self.assertEqual(r["vague"], 1)
        self.assertEqual(r["directory"], 1)
        self.assertEqual(r["specificity_score"], 0.5)
        self.assertEqual(r["reason_coverage"], 0.5)


class ValueConcreteness(unittest.TestCase):
    def test_concrete_values(self):
        self.assertTrue(m.is_value_concrete("결제 요청이 PG client 에 전달된다"))
        self.assertTrue(m.is_value_concrete("NoMethodError (charge 미구현)"))

    def test_placeholder_values(self):
        self.assertFalse(m.is_value_concrete("TBD"))
        self.assertFalse(m.is_value_concrete("추후 결정"))
        self.assertFalse(m.is_value_concrete("미정"))
        self.assertFalse(m.is_value_concrete(""))
        self.assertFalse(m.is_value_concrete(None))

    def test_too_short_value(self):
        self.assertFalse(m.is_value_concrete("X"))
        self.assertFalse(m.is_value_concrete("OK"))


class EvaluateRedContracts(unittest.TestCase):
    def test_no_step_section_not_applicable(self):
        text = "# 제목\n## 본문\n"
        r = m.evaluate_red_contracts(text)
        self.assertFalse(r["applicable"])

    def test_concrete_step_full_score(self):
        text = (
            "### 스텝 목록\n"
            "1. **[스텝 1]** 결제 호출 검증\n"
            "   - 테스트 대상: PaymentService#charge\n"
            "   - 검증할 행동: PG client 의 charge 가 호출되고 응답이 매핑된다\n"
            "   - 기대 실패 유형: NoMethodError (charge 미구현)\n"
        )
        r = m.evaluate_red_contracts(text)
        self.assertTrue(r["applicable"])
        self.assertEqual(r["specificity_score"], 1.0)

    def test_placeholder_step_low_score(self):
        text = (
            "### 스텝 목록\n"
            "1. **[스텝 1]** 알림 검증\n"
            "   - 테스트 대상: TBD\n"
            "   - 검증할 행동: 추후 결정\n"
            "   - 기대 실패 유형: TODO\n"
        )
        r = m.evaluate_red_contracts(text)
        self.assertTrue(r["applicable"])
        self.assertEqual(r["specificity_score"], 0.0)


class FixtureIntegration(unittest.TestCase):
    """fixture 디렉터리 일괄 평가 검증."""

    def test_good_fixtures_high_score(self):
        reports = m.evaluate_directory(FIXTURES / "good")
        self.assertEqual(len(reports), 2)
        # good plan 들은 specificity 100%
        for r in reports:
            cf = r["change_files"]
            if cf["specificity_score"] is not None:
                self.assertGreaterEqual(cf["specificity_score"], 0.9)

    def test_bad_fixtures_low_score(self):
        reports = m.evaluate_directory(FIXTURES / "bad")
        self.assertEqual(len(reports), 2)
        # bad plan 들은 specificity 낮음 또는 변경파일 없음
        bad_05 = next(r for r in reports if "05" in r["path"])
        self.assertLess(bad_05["change_files"]["specificity_score"], 0.5)
        self.assertLess(bad_05["red_contracts"]["specificity_score"], 0.5)


class CLIRender(unittest.TestCase):
    def test_text_render_includes_table(self):
        reports = m.evaluate_directory(FIXTURES / "good")
        out = m.render_text(reports)
        self.assertIn("| Plan |", out)
        self.assertIn("매크로", out)

    def test_json_render_structure(self):
        import json as _json
        reports = m.evaluate_directory(FIXTURES / "good")
        out = m.render_json(reports)
        data = _json.loads(out)
        self.assertIn("summary", data)
        self.assertIn("plans", data)
        self.assertEqual(len(data["plans"]), 2)


if __name__ == "__main__":
    unittest.main()
