#!/usr/bin/env python3
"""
pilot/tools/doctor/integrity.py 의 check_conventions_paths 단위 테스트.

config.md `## 언어·도구 기본값` 에 선언된 conventions_doc / conventions_evals 가
실제 파일로 존재하는지 검사한다 — 선언-실존 불일치는 generator/evaluator 호출
시점에야 발견되는 silent 갭이므로 doctor 가 조기 경고한다.

    - test_declared_and_missing_warns   : 선언됐는데 파일 없음 → 키별 WARN
    - test_declared_and_present_no_warn : 선언 + 파일 존재 → WARN 없음
    - test_undeclared_silent            : 미선언 → 결과 없음 (graceful)
    - test_workspace_prefix_normalized  : `workspace/` 접두 선언도 정상 해석
    - test_project_override_checked     : project.md 제한사항 override 경로도 검사

실행:
    python3 pilot/tests/tools/test_doctor_conventions.py
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "doctor.py"


def _load_doctor():
    spec = importlib.util.spec_from_file_location("doctor_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doctor = _load_doctor()


def _make_workspace(td: str, config_body: str, project_body: str | None = None) -> Path:
    ws = Path(td)
    (ws / "context").mkdir(parents=True, exist_ok=True)
    (ws / "context" / "config.md").write_text(config_body, encoding="utf-8")
    if project_body is not None:
        (ws / "projects" / "P").mkdir(parents=True, exist_ok=True)
        (ws / "projects" / "P" / "project.md").write_text(project_body, encoding="utf-8")
    return ws


CONFIG_DECLARED = (
    "## 언어·도구 기본값\n\n"
    "| 키 | 값 | 용도 |\n"
    "| --- | --- | --- |\n"
    "| `conventions_doc` | `context/conventions.md` | 관행 문서 |\n"
    "| `conventions_evals` | `context/evals/conventions.json` | 검증 케이스 |\n"
)


class DeclaredAndMissing(unittest.TestCase):
    def test_declared_and_missing_warns(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_workspace(td, CONFIG_DECLARED)
            results = doctor.check_conventions_paths(ws, None)
            warns = [r for r in results if r.level == "WARN"]
            messages = " ".join(r.message for r in warns)
            self.assertEqual(len(warns), 2, f"키별 WARN 2 건 기대: {messages}")
            self.assertIn("conventions_doc", messages)
            self.assertIn("conventions_evals", messages)


class DeclaredAndPresent(unittest.TestCase):
    def test_declared_and_present_no_warn(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_workspace(td, CONFIG_DECLARED)
            (ws / "context" / "conventions.md").write_text("# 관행\n", encoding="utf-8")
            (ws / "context" / "evals").mkdir(parents=True)
            (ws / "context" / "evals" / "conventions.json").write_text("{}", encoding="utf-8")
            results = doctor.check_conventions_paths(ws, None)
            warns = [r for r in results if r.level == "WARN"]
            self.assertEqual(warns, [], f"WARN 있으면 안 됨: {[r.message for r in warns]}")


class Undeclared(unittest.TestCase):
    def test_undeclared_silent(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_workspace(td, "## Ignore\n\n| 패턴 | 사유 |\n| --- | --- |\n")
            results = doctor.check_conventions_paths(ws, None)
            self.assertEqual(results, [], "미선언이면 결과 없음 (해당 기능 미사용)")


class WorkspacePrefixNormalized(unittest.TestCase):
    def test_workspace_prefix_normalized(self):
        config = (
            "## 언어·도구 기본값\n\n"
            "| 키 | 값 | 용도 |\n"
            "| --- | --- | --- |\n"
            "| `conventions_doc` | `workspace/context/conventions.md` | 관행 문서 |\n"
        )
        with tempfile.TemporaryDirectory() as td:
            ws = _make_workspace(td, config)
            (ws / "context" / "conventions.md").write_text("# 관행\n", encoding="utf-8")
            results = doctor.check_conventions_paths(ws, None)
            warns = [r for r in results if r.level == "WARN"]
            self.assertEqual(warns, [], f"접두 정규화 후 존재 — WARN 없어야 함: {[r.message for r in warns]}")


class ProjectOverrideChecked(unittest.TestCase):
    def test_project_override_checked(self):
        """project.md 제한사항이 다른 (없는) 경로로 override 하면 그 경로를 검사."""
        project_md = (
            "# P\n\n## 제한사항\n\n"
            "- **conventions_doc**: `context/kotlin-conventions.md`\n"
        )
        with tempfile.TemporaryDirectory() as td:
            ws = _make_workspace(td, CONFIG_DECLARED, project_body=project_md)
            # workspace 기본 경로 파일은 존재하지만 override 경로는 없음
            (ws / "context" / "conventions.md").write_text("# 관행\n", encoding="utf-8")
            (ws / "context" / "evals").mkdir(parents=True)
            (ws / "context" / "evals" / "conventions.json").write_text("{}", encoding="utf-8")
            results = doctor.check_conventions_paths(ws, "P")
            warns = [r for r in results if r.level == "WARN"]
            messages = " ".join(r.message for r in warns)
            self.assertEqual(len(warns), 1, f"override 경로 WARN 1 건 기대: {messages}")
            self.assertIn("kotlin-conventions.md", messages)


if __name__ == "__main__":
    unittest.main(verbosity=2)
