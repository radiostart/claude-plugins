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
    - test_placeholder_cell_not_declared: 예시 표기 셀(설명문+코드 스팬 혼재) → WARN 0건, INFO 1건 (#23 회귀 잠금)
    - test_plain_text_path_still_declared: 백틱 없는 평문 경로 + 파일 부재 → WARN 1건 (참 보존)
    - test_dash_marker_silent           : 값 셀 `—` → 결과 0건

실행:
    python3 pilot/tests/tools/test_doctor_conventions.py
"""

import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent

# tools/ 를 sys.path 에 추가하여 doctor 패키지를 직접 import (doctor.py 는 더 이상
# backward-compat re-export 를 제공하지 않음 — #20 스텝 3).
_TOOLS_DIR = str(PLUGIN_ROOT / "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

import doctor.integrity as doctor  # noqa: E402


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


class PlaceholderCellNotDeclared(unittest.TestCase):
    def test_placeholder_cell_not_declared(self):
        r"""값 셀이 '설명문 + 코드 스팬' 혼재(예시 표기)면 미선언 취급 — WARN 오탐 소멸.

        #23 (A) 회귀 잠금: `예: \`context/conventions.md\`` 같은 예시 표기가
        실선언으로 오인돼 파일 부재 WARN 을 잘못 발화하던 버그.
        """
        config = (
            "## 언어·도구 기본값\n\n"
            "| 키 | 값 | 용도 |\n"
            "| --- | --- | --- |\n"
            "| `conventions_doc` | 예: `context/conventions.md` | 관행 문서 |\n"
        )
        with tempfile.TemporaryDirectory() as td:
            ws = _make_workspace(td, config)
            results = doctor.check_conventions_paths(ws, None)
            warns = [r for r in results if r.level == "WARN"]
            infos = [r for r in results if r.level == "INFO"]
            self.assertEqual(warns, [], f"예시 표기는 WARN 이면 안 됨: {[r.message for r in warns]}")
            self.assertEqual(len(infos), 1, f"예시 표기 INFO 1건 기대: {[r.message for r in infos]}")


class PlainTextPathStillDeclared(unittest.TestCase):
    def test_plain_text_path_still_declared(self):
        """백틱 없는 공백 없는 평문 경로도 여전히 실선언으로 인정(참 보존) → 파일 없으면 WARN."""
        config = (
            "## 언어·도구 기본값\n\n"
            "| 키 | 값 | 용도 |\n"
            "| --- | --- | --- |\n"
            "| `conventions_doc` | context/conventions.md | 관행 문서 |\n"
        )
        with tempfile.TemporaryDirectory() as td:
            ws = _make_workspace(td, config)
            results = doctor.check_conventions_paths(ws, None)
            warns = [r for r in results if r.level == "WARN"]
            self.assertEqual(len(warns), 1, f"평문 선언은 여전히 WARN 대상: {[r.message for r in warns]}")
            self.assertIn("conventions_doc", warns[0].message)


class DashMarkerSilent(unittest.TestCase):
    def test_dash_marker_silent(self):
        """값 셀이 미선언 마커(`—`)면 조용히 skip — WARN·INFO 모두 없음."""
        config = (
            "## 언어·도구 기본값\n\n"
            "| 키 | 값 | 용도 |\n"
            "| --- | --- | --- |\n"
            "| `conventions_doc` | — | 관행 문서 |\n"
        )
        with tempfile.TemporaryDirectory() as td:
            ws = _make_workspace(td, config)
            results = doctor.check_conventions_paths(ws, None)
            self.assertEqual(results, [], f"미선언 마커는 결과 없어야 함: {[r.message for r in results]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
