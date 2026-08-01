"""Doctor 의 STATE.md issue 모드 인식 테스트.

- determine_active_project: 활성 행 mode=issue 면 None (프로젝트 오진 제거)
- determine_active_issue: 활성 행 mode=issue 면 이슈명 (스킵 안내용)
- legacy 표 (첫 칸 순번 숫자) 는 project 로 폴백 (하위호환)
- run_integrity_check: issue 활성 시 프로젝트 검사 섹션 미진입 + issue 스킵
  안내 출력 (종전에는 이슈명을 프로젝트로 오인해 `/pilot:project {이슈명}`
  실행을 처방 — 따르면 이슈명으로 프로젝트가 생성되고 STATE 가 뒤집혔다)
- _fix_state_md_prune_history: issue 진행중 행을 훼손하지 않는다 (mode-blind
  상태 열 판정 — 보존 회귀 테스트)

실행:
    python3 pilot/tests/tools/test_doctor_issue_mode.py
"""

import contextlib
import io
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


def _ws(td: str, state_row: str) -> Path:
    """context/MANIFEST.md + STATE.md(인자 행) 최소 workspace."""
    ws = Path(td)
    (ws / "context").mkdir(parents=True)
    (ws / "context" / "MANIFEST.md").write_text("# manifest\n", encoding="utf-8")
    (ws / "STATE.md").write_text(
        "| 모드 | 이름 | 상태 |\n| --- | --- | --- |\n" + state_row + "\n",
        encoding="utf-8",
    )
    return ws


class DetermineActiveProjectModeAware(unittest.TestCase):
    def test_issue_row_returns_none(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _ws(td, "| issue | hotfix-1 | 진행중 |")
            self.assertIsNone(doctor.determine_active_project(ws))

    def test_project_row_returns_name(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _ws(td, "| project | MyProj | 진행중 |")
            self.assertEqual(doctor.determine_active_project(ws), "MyProj")

    def test_legacy_numeric_mode_falls_back_to_project(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / "STATE.md").write_text(
                "| 순번 | 이름 | 상태 | 비고 |\n"
                "| --- | --- | --- | --- |\n"
                "| 1 | LegacyProj | 진행중 | x |\n",
                encoding="utf-8",
            )
            self.assertEqual(doctor.determine_active_project(ws), "LegacyProj")


class DetermineActiveIssue(unittest.TestCase):
    def test_issue_row_returns_name(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _ws(td, "| issue | hotfix-1 | 진행중 |")
            self.assertEqual(doctor.determine_active_issue(ws), "hotfix-1")

    def test_project_row_returns_none(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _ws(td, "| project | MyProj | 진행중 |")
            self.assertIsNone(doctor.determine_active_issue(ws))


class IntegrityCheckSkipsProjectOnActiveIssue(unittest.TestCase):
    def test_no_project_missing_error_and_issue_skip_notice(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _ws(td, "| issue | hotfix-1 | 진행중 |")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                doctor.run_integrity_check(ws, project=None, fix=False)
            out = buf.getvalue()
            # 오진 제거 — 이슈명을 프로젝트로 오인한 검사·처방이 없어야 한다.
            self.assertNotIn("Project (hotfix-1):", out)
            self.assertNotIn("/pilot:project hotfix-1", out)
            self.assertIn("활성 issue (hotfix-1)", out)


class PruneHistoryKeepsIssueRow(unittest.TestCase):
    def test_fixer_preserves_active_issue_row(self):
        """이력 정리 fixer 는 상태 열만 보고 행을 남긴다 — issue 진행중 행 보존."""
        with tempfile.TemporaryDirectory() as td:
            state_md = Path(td) / "STATE.md"
            state_md.write_text(
                "| 모드 | 이름 | 상태 |\n"
                "| --- | --- | --- |\n"
                "| issue | hotfix-1 | 진행중 |\n"
                "| project | OldProj | 완료 |\n"
                "| issue | old-issue | 보류 |\n",
                encoding="utf-8",
            )
            fixer = doctor._fix_state_md_prune_history(state_md)
            ok, _msg = fixer()
            self.assertTrue(ok)
            content = state_md.read_text(encoding="utf-8")
            self.assertIn("| issue | hotfix-1 | 진행중 |", content)
            self.assertNotIn("OldProj", content)
            self.assertNotIn("old-issue", content)


if __name__ == "__main__":
    unittest.main()
