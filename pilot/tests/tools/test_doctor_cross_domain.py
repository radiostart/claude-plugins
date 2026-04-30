#!/usr/bin/env python3
"""
#09 cross-domain 처리 가이드 — doctor 검증 단위 테스트.

    - test_info_stale_row_bidirectional : 두 도메인 모두 외부 도메인 표 양쪽 등장
                                          (A 가 B 를 외부 도메인으로, B 가 A 를 외부 도메인으로 표기)
                                          → INFO 발화 (순환 의존 감지)
    - test_no_error_on_valid_manifest   : 정상 MANIFEST → ERROR 없음

Note: #09 의 외부 reference 추출 알고리즘 자체는 SKILL.md 가이드라 단위 테스트 대상 아님.
      doctor 의 schema 검증 함수 (check_workspace_external_domain_section) 범위만 테스트.

실행:
    python3 pilot/tests/tools/test_doctor_cross_domain.py
"""

import importlib.util
import tempfile
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


class CrossDomainInfoStaleRowBidirectional(unittest.TestCase):
    """두 도메인 모두 외부 도메인 표에 등장 (순환 의존 유사 패턴) → INFO 발화, ERROR 없음."""

    def test_info_stale_row_bidirectional(self):
        # foo 와 bar 가 서로를 외부 도메인으로 표기하는 MANIFEST (예시 도메인)
        manifest_content = """\
# Domain Manifest

## 도메인 분류

| 도메인 | 진입 파일 | 설명 |
| --- | --- | --- |
| foo | `foo/index.md` | (예시 도메인) |
| bar | `bar/index.md` | (예시 도메인) |

## 외부 도메인 reference (learn 미완료)

| 추정 도메인 | 클래스 (개수) | 추천 후속 학습 |
| --- | --- | --- |
| foo | FooClassA (1) | `/pilot:learn app/services/foo/` (auto) |
| bar | BarClassA (1) | `/pilot:learn app/models/bar/` (auto) |
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", encoding="utf-8", delete=False
        ) as f:
            f.write(manifest_content)
            tmp_path = Path(f.name)

        try:
            results = doctor.check_workspace_external_domain_section(tmp_path)
            errors = [r for r in results if r.level == "ERROR"]
            infos = [r for r in results if r.level == "INFO"]
            # 순환 의존 (stale row) 은 ERROR 아님
            self.assertEqual(
                len(errors), 0,
                f"순환 의존 패턴은 ERROR 아님: {[r.message for r in errors]}"
            )
            # 두 도메인 모두 도메인 분류 표에 있으므로 stale row INFO 2 건
            self.assertGreaterEqual(
                len(infos), 2,
                f"stale row INFO 2 건 이상 기대 (양방향): {[r.message for r in infos]}"
            )
        finally:
            tmp_path.unlink(missing_ok=True)


class CrossDomainNoErrorOnValidManifest(unittest.TestCase):
    """정상 MANIFEST → ERROR 없음."""

    def test_no_error_on_valid_manifest(self):
        fixture = FIXTURE_BASE / "pass-valid" / "MANIFEST.md"
        self.assertTrue(fixture.is_file(), f"fixture 없음: {fixture}")
        results = doctor.check_workspace_external_domain_section(fixture)
        errors = [r for r in results if r.level == "ERROR"]
        self.assertEqual(len(errors), 0, f"ERROR 있으면 안 됨: {[r.message for r in errors]}")


if __name__ == "__main__":
    unittest.main()
