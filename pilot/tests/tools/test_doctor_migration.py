#!/usr/bin/env python3
"""
pilot/tools/doctor/integrity.py 의 migrate_v0_1_to_v0_2 단위 테스트.

케이스:
    - test_skip_new_user         : plugin_version 0.2.0 → 마이그레이션 skip
    - test_skip_partial_defined  : config 에 이미 행 있으면 skip + INFO
    - test_detect_v010           : plugin_version 0.1.0, config 빈 표 → WARN (마이그레이션 대상)
    - test_accept_opt_in         : stdin 'a' → default 표 주입 + state 갱신 + plugin_version 0.2.0
    - test_decline_opt_out       : stdin 'b' → config 그대로 + migration_v0_2_0: declined
    - test_postpone_opt_c        : stdin 'c' → 변경 없음, 다음 호출 시 다시 묻기
    - test_non_interactive       : stdin isatty=False → 자동 미루기

실행:
    python3 pilot/tests/tools/test_doctor_migration.py
"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "doctor.py"
FIXTURE_BASE = PLUGIN_ROOT / "tests" / "fixtures" / "v0.1.0-baseline"
MIGRATION_FIXTURE = FIXTURE_BASE / "migration"

# tools/ 를 sys.path 에 추가하여 doctor 패키지 import 가능하게
_TOOLS_DIR = str(PLUGIN_ROOT / "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

# doctor.integrity 를 표준 방식으로 import (mock target 이 정확히 잡히도록)
import importlib as _importlib
import doctor.integrity as _integrity
import doctor._common as _common

# doctor.py 를 통한 facade 로드 (backward-compat 테스트 겸)
def _load_doctor():
    spec = importlib.util.spec_from_file_location("doctor_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# 테스트는 integrity 모듈 함수를 직접 호출 (mock 정확도 보장)
migrate_fn = _integrity.migrate_v0_1_to_v0_2
MOCK_READ_VERSION = "doctor.integrity.read_current_plugin_version"


def _make_workspace(tmp: Path, plugin_version=None, migration_v0_2_0=None,
                    config_content=None):
    """임시 workspace 구조 생성 헬퍼."""
    ws = tmp / "workspace"
    (ws / "context").mkdir(parents=True)
    (ws / "projects" / "TestProj").mkdir(parents=True)

    # STATE.md
    (ws / "STATE.md").write_text(
        "| 모드 | 프로젝트 | 상태 |\n| --- | --- | --- |\n| standard | TestProj | 진행중 |\n",
        encoding="utf-8",
    )

    # MANIFEST.md
    (ws / "context" / "MANIFEST.md").write_text(
        "# Domain Manifest\n\n## 도메인 분류\n\n| 도메인 | 진입 파일 | 설명 |\n| --- | --- | --- |\n",
        encoding="utf-8",
    )

    # config.md
    if config_content is None:
        # 기본: 헤더만 있는 빈 표 (D10 이후 상태)
        config_content = (
            "# Workspace Config\n\n"
            "## learn 언어 패턴\n\n"
            "### 의존성 추적\n\n"
            "| 언어 | 의존성 추출 패턴 |\n"
            "| ---- | ---------------- |\n\n"
            "### 역할 분류\n\n"
            "| 역할 | 식별 패턴 |\n"
            "| --- | --------- |\n"
        )
    (ws / "context" / "config.md").write_text(config_content, encoding="utf-8")

    # .agent-state.yml
    state_lines = ["schema: v1.2", "analyzed: true", "tdd: false", "domain: pilot"]
    if plugin_version is not None:
        state_lines.append(f"plugin_version: {plugin_version}")
    if migration_v0_2_0 is not None:
        state_lines.append(f"migration_v0_2_0: {migration_v0_2_0}")
    state_content = "\n".join(state_lines) + "\n"
    (ws / "projects" / "TestProj" / ".agent-state.yml").write_text(
        state_content, encoding="utf-8"
    )

    return ws


class MigrationSkipNewUser(unittest.TestCase):
    """plugin_version 이 0.2.0 이상이면 신규 사용자 — 마이그레이션 skip."""

    def test_skip_new_user(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = _make_workspace(Path(tmp), plugin_version="0.2.0")
            with mock.patch(MOCK_READ_VERSION, return_value="0.2.0"):
                results = migrate_fn(ws, "TestProj")
            self.assertEqual(results, [], f"신규 사용자는 결과 없어야 함: {results}")


class MigrationSkipPartialDefined(unittest.TestCase):
    """config 에 이미 행이 있는 경우 (부분 정의) → skip + INFO."""

    def test_skip_partial_defined(self):
        with tempfile.TemporaryDirectory() as tmp:
            # config 에 일부 행이 있는 상태
            partial_config = (
                "# Workspace Config\n\n"
                "## learn 언어 패턴\n\n"
                "### 의존성 추적\n\n"
                "| 언어 | 의존성 추출 패턴 |\n"
                "| ---- | ---------------- |\n"
                "| Ruby | `require_relative` |\n\n"
                "### 역할 분류\n\n"
                "| 역할 | 식별 패턴 |\n"
                "| --- | --------- |\n"
            )
            ws = _make_workspace(Path(tmp), plugin_version="0.1.0", config_content=partial_config)
            with mock.patch(MOCK_READ_VERSION, return_value="0.2.0"):
                results = migrate_fn(ws, "TestProj")
            levels = [r.level for r in results]
            self.assertIn("INFO", levels, f"부분 정의 → INFO 기대: {levels}")
            # WARN 없어야 함 (skip)
            self.assertNotIn("WARN", levels, f"부분 정의 시 WARN 없어야 함: {levels}")


class MigrationDetectV010(unittest.TestCase):
    """plugin_version 0.1.0 + config 빈 표 → WARN (마이그레이션 대상 감지)."""

    def test_detect_v010(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = _make_workspace(Path(tmp), plugin_version="0.1.0")
            with mock.patch(MOCK_READ_VERSION, return_value="0.2.0"):
                results = migrate_fn(ws, "TestProj")
            levels = [r.level for r in results]
            self.assertIn("WARN", levels, f"v0.1.0 감지 → WARN 기대: {levels}")


class MigrationAcceptOptIn(unittest.TestCase):
    """stdin 'a' (opt-in) → config 에 default 표 주입 + .agent-state.yml 갱신."""

    def test_accept_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = _make_workspace(Path(tmp), plugin_version="0.1.0")
            config_path = ws / "context" / "config.md"
            state_yml = ws / "projects" / "TestProj" / ".agent-state.yml"

            with mock.patch(MOCK_READ_VERSION, return_value="0.2.0"):
                results = migrate_fn(ws, "TestProj")

            # fix callable 실행 (stdin 'a' mock)
            warn_results = [r for r in results if r.level == "WARN" and r.fix is not None]
            self.assertEqual(len(warn_results), 1, f"WARN + fix callable 1 건 기대: {results}")

            with mock.patch("builtins.input", return_value="a"), \
                 mock.patch("sys.stdin") as mock_stdin:
                mock_stdin.isatty.return_value = True
                ok, msg = warn_results[0].fix()

            self.assertTrue(ok, f"fix 성공 기대: {msg}")

            # config.md 에 Ruby 행이 주입됐는지 확인
            config_text = config_path.read_text(encoding="utf-8")
            self.assertIn("Ruby", config_text, f"Ruby 행이 config 에 없음:\n{config_text}")
            self.assertIn("Kotlin", config_text, f"Kotlin 행이 config 에 없음")

            # .agent-state.yml 갱신 확인
            state_text = state_yml.read_text(encoding="utf-8")
            self.assertIn("migration_v0_2_0: accepted", state_text,
                          f"migration_v0_2_0: accepted 가 없음:\n{state_text}")
            self.assertIn("plugin_version: 0.2.0", state_text,
                          f"plugin_version: 0.2.0 이 없음:\n{state_text}")


class MigrationDeclineOptOut(unittest.TestCase):
    """stdin 'b' (opt-out) → config 그대로 + migration_v0_2_0: declined."""

    def test_decline_opt_out(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = _make_workspace(Path(tmp), plugin_version="0.1.0")
            config_path = ws / "context" / "config.md"
            state_yml = ws / "projects" / "TestProj" / ".agent-state.yml"

            with mock.patch(MOCK_READ_VERSION, return_value="0.2.0"):
                results = migrate_fn(ws, "TestProj")

            warn_results = [r for r in results if r.level == "WARN" and r.fix is not None]
            self.assertEqual(len(warn_results), 1)

            with mock.patch("builtins.input", return_value="b"), \
                 mock.patch("sys.stdin") as mock_stdin:
                mock_stdin.isatty.return_value = True
                ok, msg = warn_results[0].fix()

            self.assertTrue(ok, f"fix 성공 기대: {msg}")

            # config.md 가 변경되지 않아야 함 (Ruby 없음)
            config_after = config_path.read_text(encoding="utf-8")
            self.assertNotIn("Ruby", config_after,
                             "거부 시 config 에 Ruby 가 없어야 함")

            # .agent-state.yml 에 declined 기록
            state_text = state_yml.read_text(encoding="utf-8")
            self.assertIn("migration_v0_2_0: declined", state_text,
                          f"migration_v0_2_0: declined 가 없음:\n{state_text}")
            self.assertIn("plugin_version: 0.2.0", state_text)


class MigrationPostponeOptC(unittest.TestCase):
    """stdin 'c' (미루기) → 변경 없음, 다음 호출 시 다시 묻기."""

    def test_postpone_opt_c(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = _make_workspace(Path(tmp), plugin_version="0.1.0")
            config_path = ws / "context" / "config.md"
            config_before = config_path.read_text(encoding="utf-8")

            with mock.patch(MOCK_READ_VERSION, return_value="0.2.0"):
                results = migrate_fn(ws, "TestProj")

            warn_results = [r for r in results if r.level == "WARN" and r.fix is not None]
            self.assertEqual(len(warn_results), 1)

            with mock.patch("builtins.input", return_value="c"), \
                 mock.patch("sys.stdin") as mock_stdin:
                mock_stdin.isatty.return_value = True
                ok, msg = warn_results[0].fix()

            self.assertTrue(ok, f"미루기도 성공 기대: {msg}")
            self.assertIn("미루기", msg, f"미루기 메시지 기대: {msg}")

            # config 변경 없음
            config_after = config_path.read_text(encoding="utf-8")
            self.assertEqual(config_before, config_after, "미루기 시 config 변경 없어야 함")


class MigrationNonInteractive(unittest.TestCase):
    """non-interactive 환경 (stdin.isatty() = False) → 자동 미루기."""

    def test_non_interactive(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = _make_workspace(Path(tmp), plugin_version="0.1.0")
            config_path = ws / "context" / "config.md"
            config_before = config_path.read_text(encoding="utf-8")

            with mock.patch(MOCK_READ_VERSION, return_value="0.2.0"):
                results = migrate_fn(ws, "TestProj")

            warn_results = [r for r in results if r.level == "WARN" and r.fix is not None]
            self.assertEqual(len(warn_results), 1)

            # non-interactive: isatty() = False
            with mock.patch("sys.stdin") as mock_stdin:
                mock_stdin.isatty.return_value = False
                ok, msg = warn_results[0].fix()

            self.assertTrue(ok, f"non-interactive 미루기 성공 기대: {msg}")
            # config 변경 없음 (자동 미루기)
            config_after = config_path.read_text(encoding="utf-8")
            self.assertEqual(config_before, config_after,
                             "non-interactive 시 config 변경 없어야 함")


if __name__ == "__main__":
    unittest.main(verbosity=2)
