#!/usr/bin/env python3
"""
pilot/tools/doctor/integrity.py 의 check_features_open_questions 단위 테스트.

    - test_pass_empty_oq       : Open Questions 4 카테고리 모두 빈 상태 ((없음)) → ERROR/WARN 없음
    - test_pass_valid          : Open Questions 에 실제 항목 포함 → ERROR/WARN 없음
    - test_info_missing_section: ## Open Questions 섹션 자체 부재 → INFO 1 줄 이상, ERROR 없음
    - test_info_missing_h3     : H3 카테고리 일부 누락 → INFO 1 줄 이상, ERROR 없음

실행:
    python3 pilot/tests/tools/test_doctor_open_questions.py
"""

import importlib.util
import sys
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "doctor.py"
FIXTURE_BASE = PLUGIN_ROOT / "tests" / "fixtures" / "v0.1.0-baseline" / "open-questions"


def _load_doctor():
    spec = importlib.util.spec_from_file_location("doctor_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doctor = _load_doctor()


class OpenQuestionsPassEmpty(unittest.TestCase):
    """## Open Questions 4 카테고리 모두 빈 상태 ((없음) 만) → ERROR/WARN 없음."""

    def test_pass_empty_oq(self):
        features_dir = FIXTURE_BASE / "pass-empty" / "features"
        self.assertTrue(features_dir.is_dir(), f"fixture 없음: {features_dir}")
        results = doctor.check_features_open_questions(features_dir)
        errors = [r for r in results if r.level in ("ERROR", "WARN")]
        self.assertEqual(
            len(errors), 0,
            f"ERROR/WARN 있으면 안 됨: {[r.message for r in errors]}"
        )


class OpenQuestionsPassValid(unittest.TestCase):
    """## Open Questions 에 실제 항목 포함 → ERROR/WARN 없음."""

    def test_pass_valid(self):
        features_dir = FIXTURE_BASE / "pass-valid" / "features"
        self.assertTrue(features_dir.is_dir(), f"fixture 없음: {features_dir}")
        results = doctor.check_features_open_questions(features_dir)
        errors = [r for r in results if r.level in ("ERROR", "WARN")]
        self.assertEqual(
            len(errors), 0,
            f"ERROR/WARN 있으면 안 됨: {[r.message for r in errors]}"
        )


class OpenQuestionsInfoMissingSection(unittest.TestCase):
    """## Open Questions 섹션 자체 부재 → INFO 1 줄 이상, ERROR 없음."""

    def test_info_missing_section(self):
        features_dir = FIXTURE_BASE / "info-missing-section" / "features"
        self.assertTrue(features_dir.is_dir(), f"fixture 없음: {features_dir}")
        results = doctor.check_features_open_questions(features_dir)
        errors = [r for r in results if r.level == "ERROR"]
        infos = [r for r in results if r.level == "INFO"]
        self.assertEqual(
            len(errors), 0,
            f"ERROR 있으면 안 됨 (backward-compat INFO 만): {[r.message for r in errors]}"
        )
        self.assertGreaterEqual(len(infos), 1, "INFO 1 줄 이상 기대 (섹션 부재 안내)")
        info_messages = " ".join(r.message for r in infos)
        self.assertIn(
            "Open Questions", info_messages,
            f"INFO 메시지에 'Open Questions' 없음: {info_messages}"
        )


class OpenQuestionsInfoMissingH3(unittest.TestCase):
    """H3 카테고리 일부 누락 → INFO 1 줄 이상, ERROR 없음."""

    def test_info_missing_h3(self):
        features_dir = FIXTURE_BASE / "info-missing-h3" / "features"
        self.assertTrue(features_dir.is_dir(), f"fixture 없음: {features_dir}")
        results = doctor.check_features_open_questions(features_dir)
        errors = [r for r in results if r.level == "ERROR"]
        infos = [r for r in results if r.level == "INFO"]
        self.assertEqual(
            len(errors), 0,
            f"H3 누락은 ERROR 아님: {[r.message for r in errors]}"
        )
        self.assertGreaterEqual(len(infos), 1, "INFO 1 줄 이상 기대 (H3 누락 안내)")
        info_messages = " ".join(r.message for r in infos)
        self.assertIn(
            "카테고리", info_messages,
            f"INFO 메시지에 '카테고리' 없음: {info_messages}"
        )


if __name__ == "__main__":
    unittest.main()
