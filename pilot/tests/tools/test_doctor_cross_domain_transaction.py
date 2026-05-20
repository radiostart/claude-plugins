#!/usr/bin/env python3
"""
pilot/tools/doctor/integrity.py 의 check_domain_transaction_contracts 단위 테스트.

    - test_pass_no_subsection    : Cross-domain Transaction Contracts 섹션 부재 → INFO 1 줄, ERROR/WARN 없음
    - test_pass_inline           : 4 컬럼 + 헤더 정확 + 변경 type 화이트리스트 → ERROR/WARN 없음
    - test_pass_separated        : 분리 파일 시나리오 (index 에 섹션 없음) → INFO 만, ERROR 없음
    - test_pass_empty            : placeholder 행 포함 표 → ERROR/WARN 없음
    - test_error_column_mismatch : 3 컬럼 표 → ERROR + "컬럼 수"
    - test_error_header_mismatch : 헤더 wording 변경 → ERROR + "헤더"
    - test_error_bad_type        : 변경 type "delete" 등 화이트리스트 외 → ERROR + "변경 type"

실행:
    python3 pilot/tests/tools/test_doctor_cross_domain_transaction.py
"""

import importlib.util
import sys
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "doctor.py"
FIXTURE_BASE = PLUGIN_ROOT / "tests" / "fixtures" / "v0.1.0-baseline" / "transaction-contracts"


def _load_doctor():
    spec = importlib.util.spec_from_file_location("doctor_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doctor = _load_doctor()


class TxContractsPassNoSubsection(unittest.TestCase):
    """### Cross-domain Transaction Contracts 섹션 부재 → INFO 1 줄, ERROR/WARN 없음.

    단일 DB 도메인 정상 시나리오.
    """

    def test_pass_no_subsection(self):
        workspace = FIXTURE_BASE / "pass-no-subsection"
        self.assertTrue(workspace.is_dir(), f"fixture 없음: {workspace}")
        results = doctor.check_domain_transaction_contracts(workspace)
        errors = [r for r in results if r.level in ("ERROR", "WARN")]
        infos = [r for r in results if r.level == "INFO"]
        self.assertEqual(
            len(errors), 0,
            f"ERROR/WARN 있으면 안 됨 (단일 DB 정상): {[r.message for r in errors]}"
        )
        self.assertGreaterEqual(len(infos), 1, "INFO 1 줄 이상 기대 (섹션 부재 안내)")
        info_messages = " ".join(r.message for r in infos)
        self.assertIn(
            "Cross-domain Transaction Contracts", info_messages,
            f"INFO 메시지에 'Cross-domain Transaction Contracts' 없음: {info_messages}"
        )


class TxContractsPassInline(unittest.TestCase):
    """4 컬럼 + 헤더 정확 + 변경 type 화이트리스트 → ERROR/WARN 없음."""

    def test_pass_inline(self):
        workspace = FIXTURE_BASE / "pass-inline"
        self.assertTrue(workspace.is_dir(), f"fixture 없음: {workspace}")
        results = doctor.check_domain_transaction_contracts(workspace)
        errors = [r for r in results if r.level in ("ERROR", "WARN")]
        self.assertEqual(
            len(errors), 0,
            f"ERROR/WARN 있으면 안 됨 (valid inline 표): {[r.message for r in errors]}"
        )


class TxContractsPassSeparated(unittest.TestCase):
    """분리 파일 시나리오: index 에 섹션 없음 → INFO 만, ERROR 없음."""

    def test_pass_separated(self):
        workspace = FIXTURE_BASE / "pass-separated"
        self.assertTrue(workspace.is_dir(), f"fixture 없음: {workspace}")
        results = doctor.check_domain_transaction_contracts(workspace)
        errors = [r for r in results if r.level == "ERROR"]
        self.assertEqual(
            len(errors), 0,
            f"ERROR 있으면 안 됨 (분리 파일 — index 에 섹션 없음 = INFO 만): {[r.message for r in errors]}"
        )


class TxContractsPassEmpty(unittest.TestCase):
    """placeholder 행 포함 표 → ERROR/WARN 없음."""

    def test_pass_empty(self):
        workspace = FIXTURE_BASE / "pass-empty"
        self.assertTrue(workspace.is_dir(), f"fixture 없음: {workspace}")
        results = doctor.check_domain_transaction_contracts(workspace)
        errors = [r for r in results if r.level in ("ERROR", "WARN")]
        self.assertEqual(
            len(errors), 0,
            f"ERROR/WARN 있으면 안 됨 (placeholder 행은 검증 skip): {[r.message for r in errors]}"
        )


class TxContractsErrorColumnMismatch(unittest.TestCase):
    """3 컬럼 표 → ERROR + "컬럼 수" 포함."""

    def test_error_column_mismatch(self):
        workspace = FIXTURE_BASE / "error-column-mismatch"
        self.assertTrue(workspace.is_dir(), f"fixture 없음: {workspace}")
        results = doctor.check_domain_transaction_contracts(workspace)
        errors = [r for r in results if r.level == "ERROR"]
        self.assertGreaterEqual(len(errors), 1, "ERROR 1 건 이상 기대 (컬럼 수 불일치)")
        error_messages = " ".join(r.message for r in errors)
        self.assertIn(
            "컬럼 수", error_messages,
            f"ERROR 메시지에 '컬럼 수' 없음: {error_messages}"
        )


class TxContractsErrorHeaderMismatch(unittest.TestCase):
    """헤더 wording 변경 → ERROR + "헤더" 포함."""

    def test_error_header_mismatch(self):
        workspace = FIXTURE_BASE / "error-header-mismatch"
        self.assertTrue(workspace.is_dir(), f"fixture 없음: {workspace}")
        results = doctor.check_domain_transaction_contracts(workspace)
        errors = [r for r in results if r.level == "ERROR"]
        self.assertGreaterEqual(len(errors), 1, "ERROR 1 건 이상 기대 (헤더 불일치)")
        error_messages = " ".join(r.message for r in errors)
        self.assertIn(
            "헤더", error_messages,
            f"ERROR 메시지에 '헤더' 없음: {error_messages}"
        )


class TxContractsErrorBadType(unittest.TestCase):
    """변경 type 화이트리스트 외 → ERROR + "변경 type" 포함."""

    def test_error_bad_type(self):
        workspace = FIXTURE_BASE / "error-bad-type"
        self.assertTrue(workspace.is_dir(), f"fixture 없음: {workspace}")
        results = doctor.check_domain_transaction_contracts(workspace)
        errors = [r for r in results if r.level == "ERROR"]
        self.assertGreaterEqual(len(errors), 1, "ERROR 1 건 이상 기대 (변경 type 화이트리스트 위반)")
        error_messages = " ".join(r.message for r in errors)
        self.assertIn(
            "변경 type", error_messages,
            f"ERROR 메시지에 '변경 type' 없음: {error_messages}"
        )


if __name__ == "__main__":
    unittest.main()
