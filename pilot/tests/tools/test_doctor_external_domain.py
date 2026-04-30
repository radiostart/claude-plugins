#!/usr/bin/env python3
"""
pilot/tools/doctor/integrity.py 의 check_workspace_external_domain_section 단위 테스트.

    - test_pass_empty          : ## 외부 도메인 reference 섹션 부재 → INFO, ERROR 없음
    - test_pass_valid          : 3 컬럼 + 헤더 정확 → ERROR 없음
    - test_error_column_mismatch : 2 컬럼 → ERROR + "컬럼 수"
    - test_error_header_mismatch : 헤더 wording 변경 → ERROR + "헤더"
    - test_info_stale_row      : 추정 도메인이 도메인 분류 표에도 등록 → INFO + "이미"

실행:
    python3 pilot/tests/tools/test_doctor_external_domain.py
"""

import importlib.util
import sys
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "doctor.py"
FIXTURE_BASE = PLUGIN_ROOT / "tests" / "fixtures" / "v0.1.0-baseline" / "external-domain"


def _load_doctor():
    spec = importlib.util.spec_from_file_location("doctor_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doctor = _load_doctor()


class ExternalDomainPassEmpty(unittest.TestCase):
    """## 외부 도메인 reference 섹션 부재 → INFO 1 줄, ERROR 없음."""

    def test_pass_empty(self):
        fixture = FIXTURE_BASE / "pass-empty" / "MANIFEST.md"
        self.assertTrue(fixture.is_file(), f"fixture 없음: {fixture}")
        results = doctor.check_workspace_external_domain_section(fixture)
        errors = [r for r in results if r.level == "ERROR"]
        infos = [r for r in results if r.level == "INFO"]
        self.assertEqual(len(errors), 0, f"ERROR 있으면 안 됨: {[r.message for r in errors]}")
        self.assertGreaterEqual(len(infos), 1, "INFO 1 줄 이상 기대 (섹션 부재 안내)")


class ExternalDomainPassValid(unittest.TestCase):
    """3 컬럼 + 헤더 정확 일치 → ERROR 없음."""

    def test_pass_valid(self):
        fixture = FIXTURE_BASE / "pass-valid" / "MANIFEST.md"
        self.assertTrue(fixture.is_file(), f"fixture 없음: {fixture}")
        results = doctor.check_workspace_external_domain_section(fixture)
        errors = [r for r in results if r.level == "ERROR"]
        self.assertEqual(len(errors), 0, f"ERROR 있으면 안 됨: {[r.message for r in errors]}")


class ExternalDomainErrorColumnMismatch(unittest.TestCase):
    """2 컬럼 → ERROR + "컬럼 수" 메시지."""

    def test_error_column_mismatch(self):
        fixture = FIXTURE_BASE / "error-column-mismatch" / "MANIFEST.md"
        self.assertTrue(fixture.is_file(), f"fixture 없음: {fixture}")
        results = doctor.check_workspace_external_domain_section(fixture)
        errors = [r for r in results if r.level == "ERROR"]
        self.assertGreaterEqual(len(errors), 1, "ERROR 1 건 이상 기대")
        messages = " ".join(r.message for r in errors)
        self.assertIn("컬럼", messages, f"'컬럼' 이 메시지에 없음: {messages}")


class ExternalDomainErrorHeaderMismatch(unittest.TestCase):
    """헤더 wording 변경 → ERROR + "헤더" 메시지."""

    def test_error_header_mismatch(self):
        fixture = FIXTURE_BASE / "error-header-mismatch" / "MANIFEST.md"
        self.assertTrue(fixture.is_file(), f"fixture 없음: {fixture}")
        results = doctor.check_workspace_external_domain_section(fixture)
        errors = [r for r in results if r.level == "ERROR"]
        self.assertGreaterEqual(len(errors), 1, "ERROR 1 건 이상 기대")
        messages = " ".join(r.message for r in errors)
        self.assertIn("헤더", messages, f"'헤더' 가 메시지에 없음: {messages}")


class ExternalDomainInfoStaleRow(unittest.TestCase):
    """추정 도메인이 도메인 분류 표에도 등록 → INFO + "이미" 메시지."""

    def test_info_stale_row(self):
        fixture = FIXTURE_BASE / "info-stale-row" / "MANIFEST.md"
        self.assertTrue(fixture.is_file(), f"fixture 없음: {fixture}")
        results = doctor.check_workspace_external_domain_section(fixture)
        errors = [r for r in results if r.level == "ERROR"]
        infos = [r for r in results if r.level == "INFO"]
        # stale row는 ERROR 아님
        self.assertEqual(len(errors), 0, f"stale row 는 ERROR 아님: {[r.message for r in errors]}")
        # INFO 에 "이미" 또는 "등록됨" 또는 "학습됨" 중 하나
        info_messages = " ".join(r.message for r in infos)
        has_keyword = any(kw in info_messages for kw in ["이미", "등록됨", "학습됨"])
        self.assertTrue(has_keyword, f"stale row INFO 메시지에 관련 키워드 없음: {info_messages}")


if __name__ == "__main__":
    unittest.main()
