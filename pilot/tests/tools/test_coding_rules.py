#!/usr/bin/env python3
"""
hooks/coding-rules.sh 회귀 테스트 — bash 훅을 서브프로세스로 호출 (plan r2 Phase 0, critic C1·C8).

현행 거동을 고정한다 (경로 트리거 규칙 #30 C1 배선 전 기준선):
  1. file_path 부재 → 무음
  2. 프로젝트 밖 파일 → 무음
  3. workspace/ 내부 파일 → 무음
  4. source_root 선언 + 실재 디렉토리 → 그 밖 파일 무음 · 안 파일 발화
  5. 스켈레톤 source_root 셀(`app/` · `src/main/` 등) → sed 미매칭 → fail-open (제한 없이 발화)
  6. 규칙 없음(rules/ 부재 + conventions_doc 미해석) → 무음
  7. conventions_doc `예:` 접두 벗기기 + 3후보 해석
  8. 세션당 1회 마커 — 같은 session_id 두 번째 호출 무음
  9. session_id 부재 → 마커 없이 매 호출 발화 (현행 — 보완 훅은 이 경우 무음으로 설계)
 10. CLAUDE_PLUGIN_ROOT 미설정 시 리터럴 `$CLAUDE_PLUGIN_ROOT`, 설정 시 경로 · JSON 출력 형식

실행:
    python3 pilot/tests/tools/test_coding_rules.py
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "coding-rules.sh"

CONFIG_REAL_ROOT = (
    "## 언어·도구 기본값\n\n"
    "| 키 | 값 | 용도 |\n"
    "| --- | --- | --- |\n"
    "| `source_root` | `app/` | 소스 루트 |\n"
)
CONFIG_SKELETON = (
    "## 언어·도구 기본값\n\n"
    "| 키 | 값 | 용도 |\n"
    "| --- | --- | --- |\n"
    "| `source_root` | `app/` · `src/main/` 등 | 소스 루트 |\n"
    "| `conventions_doc` | 예: `context/conventions.md` | 관행 문서 |\n"
)


def _make_project(td: str, config: str = "", rules: bool = True, conventions: str | None = None) -> Path:
    root = Path(td) / "proj"
    ctx = root / "workspace" / "context"
    ctx.mkdir(parents=True)
    if config:
        (ctx / "config.md").write_text(config, encoding="utf-8")
    if rules:
        (ctx / "rules").mkdir()
        (ctx / "rules" / "orders.md").write_text("# rules\n", encoding="utf-8")
    if conventions:
        p = root / conventions
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# conventions\n", encoding="utf-8")
    (root / "app").mkdir()
    (root / "app" / "order.rb").write_text("class Order; end\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "note.md").write_text("x\n", encoding="utf-8")
    (root / "tmp").mkdir()
    return root


def _run(root: Path, file_path: str, session: str | None = "s1", plugin_root: str | None = "/plug") -> dict | None:
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_PLUGIN_ROOT", "TMPDIR")}
    env["CLAUDE_PROJECT_DIR"] = str(root)
    env["TMPDIR"] = str(root / "tmp")
    if plugin_root is not None:
        env["CLAUDE_PLUGIN_ROOT"] = plugin_root
    payload: dict = {"tool_input": {"file_path": file_path}}
    if session is not None:
        payload["session_id"] = session
    proc = subprocess.run(
        ["bash", str(HOOK)], input=json.dumps(payload), capture_output=True, text=True, env=env, cwd=str(root)
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout.strip()
    return json.loads(out) if out else None


class CodingRulesHookTest(unittest.TestCase):
    def test_no_file_path_silent(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_project(td, CONFIG_REAL_ROOT)
            self.assertIsNone(_run(root, ""))

    def test_outside_project_silent(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_project(td, CONFIG_REAL_ROOT)
            self.assertIsNone(_run(root, "/etc/hosts"))

    def test_workspace_internal_silent(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_project(td, CONFIG_REAL_ROOT)
            self.assertIsNone(_run(root, str(root / "workspace" / "context" / "rules" / "orders.md")))

    def test_source_root_declared_restricts(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_project(td, CONFIG_REAL_ROOT)
            self.assertIsNone(_run(root, str(root / "docs" / "note.md")))
            out = _run(root, str(root / "app" / "order.rb"))
            self.assertIsNotNone(out)
            self.assertIn("app/order.rb", out["hookSpecificOutput"]["additionalContext"])

    def test_skeleton_source_root_fails_open(self):
        # `app/` · `src/main/` 등 — sed 가 값 셀을 못 잡아 source_root 미선언과 같이 동작한다 (critic C8).
        with tempfile.TemporaryDirectory() as td:
            root = _make_project(td, CONFIG_SKELETON)
            out = _run(root, str(root / "docs" / "note.md"))
            self.assertIsNotNone(out)
            self.assertIn("docs/note.md", out["hookSpecificOutput"]["additionalContext"])

    def test_no_rules_silent(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_project(td, CONFIG_SKELETON, rules=False)  # conventions 파일 없음 → 미해석
            self.assertIsNone(_run(root, str(root / "app" / "order.rb")))

    def test_conventions_doc_example_prefix_and_resolution(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_project(td, CONFIG_SKELETON, rules=False, conventions="workspace/context/conventions.md")
            out = _run(root, str(root / "app" / "order.rb"))
            self.assertIsNotNone(out)
            self.assertIn("context/conventions.md (conventions_doc)", out["hookSpecificOutput"]["additionalContext"])
            self.assertNotIn("예:", out["hookSpecificOutput"]["additionalContext"])

    def test_session_marker_once_per_session(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_project(td, CONFIG_REAL_ROOT)
            self.assertIsNotNone(_run(root, str(root / "app" / "order.rb"), session="same"))
            self.assertIsNone(_run(root, str(root / "app" / "order.rb"), session="same"))
            self.assertIsNotNone(_run(root, str(root / "app" / "order.rb"), session="other"))
            self.assertTrue((root / "tmp" / "pilot-coding-rules.same").exists())

    def test_missing_session_id_fires_every_call(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_project(td, CONFIG_REAL_ROOT)
            self.assertIsNotNone(_run(root, str(root / "app" / "order.rb"), session=None))
            self.assertIsNotNone(_run(root, str(root / "app" / "order.rb"), session=None))

    def test_plugin_root_literal_and_json_shape(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_project(td, CONFIG_REAL_ROOT)
            out = _run(root, str(root / "app" / "order.rb"), session="a", plugin_root=None)
            ctx = out["hookSpecificOutput"]["additionalContext"]
            self.assertIn("$CLAUDE_PLUGIN_ROOT/skills/context/shared/coding.md", ctx)
            out2 = _run(root, str(root / "app" / "order.rb"), session="b", plugin_root="/plug")
            self.assertEqual(out2["hookSpecificOutput"]["hookEventName"], "PostToolUse")
            self.assertIn("/plug/skills/context/shared/coding.md", out2["hookSpecificOutput"]["additionalContext"])
            self.assertIn("workspace/context/rules/ (도메인 규칙)", out2["hookSpecificOutput"]["additionalContext"])
            self.assertEqual(set(out2.keys()), {"hookSpecificOutput"})


if __name__ == "__main__":
    unittest.main()
