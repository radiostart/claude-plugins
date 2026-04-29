#!/usr/bin/env python3
"""
pilot/tools/doctor/integrity.py 의 check_workspace_config_sections 단위 테스트.

    - test_pass_empty         : 신규 섹션 모두 부재 → INFO, ERROR 없음
    - test_pass_valid         : 신규 섹션 정상 정의 → ERROR 없음
    - test_error_column_mismatch_scope : scope 카테고리 2 컬럼 → ERROR + "표 컬럼 수"
    - test_error_bad_header_char       : project.md 대상 H3 에 슬래시 → ERROR + "차단 문자" 또는 "슬래시"
    - test_error_no_prefix             : scope 헤더 ## prefix 누락 → ERROR + "## prefix"
    - test_error_role_column           : 역할 분류 표 wide-form (4 컬럼) → ERROR + "표 컬럼 수"

실행:
    python3 pilot/tests/tools/test_doctor_integrity.py
"""

import importlib.util
import sys
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "doctor.py"
FIXTURE_BASE = PLUGIN_ROOT / "tests" / "fixtures" / "v0.1.0-baseline" / "config"


def _load_doctor():
    spec = importlib.util.spec_from_file_location("doctor_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doctor = _load_doctor()


class ConfigSectionPassEmpty(unittest.TestCase):
    """신규 섹션 모두 부재 → INFO 1~2 줄, ERROR 없음."""

    def test_pass_empty(self):
        fixture = FIXTURE_BASE / "pass-empty" / "config.md"
        self.assertTrue(fixture.is_file(), f"fixture 없음: {fixture}")
        results = doctor.check_workspace_config_sections(fixture)
        errors = [r for r in results if r.level == "ERROR"]
        infos = [r for r in results if r.level == "INFO"]
        self.assertEqual(len(errors), 0, f"ERROR 있으면 안 됨: {[r.message for r in errors]}")
        # 각 섹션 부재 시 INFO 1 줄씩 — 최소 1 줄 이상
        self.assertGreaterEqual(len(infos), 1, "INFO 1 줄 이상 기대")


class ConfigSectionPassValid(unittest.TestCase):
    """신규 섹션 정상 정의 → ERROR 없음 (PASS 또는 INFO)."""

    def test_pass_valid(self):
        fixture = FIXTURE_BASE / "pass-valid" / "config.md"
        self.assertTrue(fixture.is_file(), f"fixture 없음: {fixture}")
        results = doctor.check_workspace_config_sections(fixture)
        errors = [r for r in results if r.level == "ERROR"]
        self.assertEqual(len(errors), 0, f"ERROR 있으면 안 됨: {[r.message for r in errors]}")


class ConfigSectionErrorColumnMismatch(unittest.TestCase):
    """scope 카테고리 2 컬럼 → ERROR + "표 컬럼 수" 메시지."""

    def test_error_column_mismatch_scope(self):
        fixture = FIXTURE_BASE / "error-column-mismatch" / "config.md"
        self.assertTrue(fixture.is_file(), f"fixture 없음: {fixture}")
        results = doctor.check_workspace_config_sections(fixture)
        errors = [r for r in results if r.level == "ERROR"]
        self.assertGreaterEqual(len(errors), 1, "ERROR 1 건 이상 기대")
        messages = " ".join(r.message for r in errors)
        self.assertIn("표 컬럼 수", messages, f"'표 컬럼 수' 가 메시지에 없음: {messages}")


class ConfigSectionErrorBadHeaderChar(unittest.TestCase):
    """project.md 대상 H3 에 슬래시 포함 → ERROR + "차단 문자" 또는 "슬래시" 메시지."""

    def test_error_bad_header_char(self):
        fixture = FIXTURE_BASE / "error-bad-header-char" / "config.md"
        self.assertTrue(fixture.is_file(), f"fixture 없음: {fixture}")
        results = doctor.check_workspace_config_sections(fixture)
        errors = [r for r in results if r.level == "ERROR"]
        self.assertGreaterEqual(len(errors), 1, "ERROR 1 건 이상 기대")
        messages = " ".join(r.message for r in errors)
        has_keyword = "차단 문자" in messages or "슬래시" in messages
        self.assertTrue(has_keyword, f"'차단 문자' 또는 '슬래시' 가 메시지에 없음: {messages}")


class ConfigSectionErrorNoPrefix(unittest.TestCase):
    """scope 헤더 ## prefix 누락 → ERROR + "## prefix" 메시지."""

    def test_error_no_prefix(self):
        fixture = FIXTURE_BASE / "error-no-prefix" / "config.md"
        self.assertTrue(fixture.is_file(), f"fixture 없음: {fixture}")
        results = doctor.check_workspace_config_sections(fixture)
        errors = [r for r in results if r.level == "ERROR"]
        self.assertGreaterEqual(len(errors), 1, "ERROR 1 건 이상 기대")
        messages = " ".join(r.message for r in errors)
        self.assertIn("## prefix", messages, f"'## prefix' 가 메시지에 없음: {messages}")


class ConfigSectionErrorRoleColumn(unittest.TestCase):
    """역할 분류 표 wide-form (4 컬럼) → ERROR + "표 컬럼 수" 메시지."""

    def test_error_role_column(self):
        fixture = FIXTURE_BASE / "error-role-column" / "config.md"
        self.assertTrue(fixture.is_file(), f"fixture 없음: {fixture}")
        results = doctor.check_workspace_config_sections(fixture)
        errors = [r for r in results if r.level == "ERROR"]
        self.assertGreaterEqual(len(errors), 1, "ERROR 1 건 이상 기대")
        messages = " ".join(r.message for r in errors)
        self.assertIn("표 컬럼 수", messages, f"'표 컬럼 수' 가 메시지에 없음: {messages}")


class ConfigSectionPassEmptyTable(unittest.TestCase):
    """## learn 언어 패턴 두 표 모두 헤더만 있고 행 0 → PASS (ERROR 없음, INFO 포함).

    D10 결정: 빈 표는 정상. 폴더 인접성 fallback 안내 INFO 가 출력되어야 함.
    """

    def test_pass_empty_table(self):
        fixture = FIXTURE_BASE / "pass-valid" / "config.md"
        self.assertTrue(fixture.is_file(), f"fixture 없음: {fixture}")
        results = doctor.check_workspace_config_sections(fixture)
        errors = [r for r in results if r.level == "ERROR"]
        infos = [r for r in results if r.level == "INFO"]
        self.assertEqual(len(errors), 0, f"ERROR 있으면 안 됨 (빈 표는 정상): {[r.message for r in errors]}")
        # 빈 표 2 개에 대한 INFO 가 각각 출력되어야 함
        self.assertGreaterEqual(len(infos), 2, f"INFO 2 줄 이상 기대 (빈 표 각 1 줄): {[r.message for r in infos]}")
        info_messages = " ".join(r.message for r in infos)
        self.assertIn("비어있음", info_messages, f"'비어있음' 이 INFO 메시지에 없음: {info_messages}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
