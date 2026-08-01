"""
pilot/tools/doctor/integrity.py 의 context mtime drift 검사 단위 테스트.

`check_project` 는 `context/` 하위 도메인 지식 문서의 mtime 이 state 의
`analyzed_at` 보다 최근이면 "재학습됨 → --regen-agents 권장" WARN 을 낸다.
`analyzed_at` 은 **UTC 기록**이므로 mtime 도 UTC 로 읽어야 한다 — 로컬 시각으로
읽으면 UTC 를 앞서는 표준시대(예: UTC+9)에서 analyze 직후에도 항상 drift 로
오판했다 (analyze 를 다시 돌려도 WARN 이 사라지지 않는 무한 루프).

    - test_analyze_after_change_no_warn : mtime < analyzed_at → WARN 없음
      (UTC+9 등 UTC 를 앞서는 tz 에서 회귀하던 케이스)
    - test_change_after_analyze_warns   : mtime > analyzed_at → WARN 발화 (정상 탐지 보존)
    - test_meta_files_excluded          : MANIFEST.md·config.md 는 도메인 지식이 아니라 제외

실행:
    python3 pilot/tests/tools/test_doctor_context_drift.py
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent

_TOOLS_DIR = str(PLUGIN_ROOT / "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

import doctor.integrity as integrity  # noqa: E402


def _build_workspace(td: str, analyzed_at: str) -> Path:
    """검사에 필요한 최소 워크스페이스. 반환값은 workspace 경로."""
    ws = Path(td) / "workspace"
    (ws / "context").mkdir(parents=True)
    proj = ws / "projects" / "P"
    (proj / "features").mkdir(parents=True)
    (proj / "prompts").mkdir()

    (proj / ".agent-state.yml").write_text(
        "schema: v1.2\n"
        "analyzed: true\n"
        f'analyzed_at: "{analyzed_at}"\n'
        "last_analyzed_features: 1\n"
        "tdd: false\n"
        "domain: d\n",
        encoding="utf-8",
    )
    (proj / "project.md").write_text("# P\n", encoding="utf-8")
    (proj / "features" / "01-a.md").write_text("# a\n", encoding="utf-8")
    return ws


def _set_mtime_utc(path: Path, dt_utc: datetime) -> None:
    ts = dt_utc.replace(tzinfo=timezone.utc).timestamp()
    os.utime(path, (ts, ts))


def _drift_warns(results) -> list:
    return [
        r
        for r in results
        if r.level == integrity.Result.WARN and "도메인 파일 변경됨" in r.message
    ]


class ContextMtimeDrift(unittest.TestCase):
    def test_analyze_after_change_no_warn(self):
        """mtime 이 analyzed_at 보다 과거면 WARN 없음.

        로컬 시각으로 mtime 을 읽던 시절 UTC+9 에서는 같은 상황도 9 시간
        미래로 보여 WARN 이 떴다.
        """
        analyzed = datetime(2026, 8, 1, 5, 0, 0)
        with tempfile.TemporaryDirectory() as td:
            ws = _build_workspace(td, analyzed.isoformat() + "Z")
            doc = ws / "context" / "d.md"
            doc.write_text("# d\n", encoding="utf-8")
            # analyze 1 시간 전에 학습된 문서
            _set_mtime_utc(doc, analyzed - timedelta(hours=1))

            self.assertEqual(_drift_warns(integrity.check_project(ws, "P")), [])

    def test_change_after_analyze_warns(self):
        """mtime 이 analyzed_at 보다 최근이면 WARN — 정상 탐지는 보존."""
        analyzed = datetime(2026, 8, 1, 5, 0, 0)
        with tempfile.TemporaryDirectory() as td:
            ws = _build_workspace(td, analyzed.isoformat() + "Z")
            doc = ws / "context" / "d.md"
            doc.write_text("# d\n", encoding="utf-8")
            _set_mtime_utc(doc, analyzed + timedelta(hours=1))

            warns = _drift_warns(integrity.check_project(ws, "P"))
            self.assertEqual(len(warns), 1)
            self.assertIn("d.md", warns[0].message)

    def test_meta_files_excluded(self):
        """MANIFEST.md·config.md 는 도메인 지식이 아니라 drift 대상 아님."""
        analyzed = datetime(2026, 8, 1, 5, 0, 0)
        with tempfile.TemporaryDirectory() as td:
            ws = _build_workspace(td, analyzed.isoformat() + "Z")
            for name in ("MANIFEST.md", "config.md"):
                p = ws / "context" / name
                p.write_text("# meta\n", encoding="utf-8")
                _set_mtime_utc(p, analyzed + timedelta(hours=1))

            self.assertEqual(_drift_warns(integrity.check_project(ws, "P")), [])


if __name__ == "__main__":
    unittest.main()
