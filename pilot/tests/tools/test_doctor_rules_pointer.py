#!/usr/bin/env python3
"""
doctor `check_rules_pointer` + hooks/domain-pointer.sh 테스트 (plan r2 Phase 2, #30 C1).

    - 규칙 디렉토리 부재 → 결과 없음 · 정합 → PASS
    - 관리 마커 없는 파일 INFO 만 · 미등록 도메인 WARN · 포인터 경로 부재 WARN · 재생성 불일치 INFO
    - 규칙 파일 간 동일 glob INFO · claudeMdExcludes INFO · check_workspace 배선
    - domain-pointer.sh: 매칭 시 JSON 출력, 비매칭·규칙 없음 무음, hooks.json 등록

실행:
    python3 pilot/tests/tools/test_doctor_rules_pointer.py
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
_TOOLS_DIR = str(PLUGIN_ROOT / "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from doctor import rules_pointer as rp  # noqa: E402
from doctor import integrity  # noqa: E402
from doctor._common import Result  # noqa: E402

sys.path.insert(0, str(THIS_DIR))
from test_rules_pointer import _make_repo  # noqa: E402

HOOK = PLUGIN_ROOT / "hooks" / "domain-pointer.sh"


def _levels(results):
    return [(r.level, r.label) for r in results]


class CheckRulesPointerTest(unittest.TestCase):
    def test_no_dir_and_pass(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_repo(td) / "workspace"
            self.assertEqual(rp.check_rules_pointer(ws), [])
            rp.write_rules_files(ws)
            res = rp.check_rules_pointer(ws)
            self.assertEqual([r.level for r in res], [Result.PASS])
            self.assertIn("2개", res[0].message)

    def test_unmanaged_info_only(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_repo(td) / "workspace"
            rdir = rp.rules_dir(ws)
            rdir.mkdir(parents=True)
            (rdir / "pilot-ghost.md").write_text("# 내 규칙 (마커 없음)\n", encoding="utf-8")
            res = rp.check_rules_pointer(ws)
            self.assertEqual([r.level for r in res], [Result.INFO])
            self.assertIn("관리 마커 없음", res[0].message)

    def test_stale_domain_warn(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_repo(td) / "workspace"
            rp.write_rules_files(ws)
            (rp.rules_dir(ws) / "pilot-ghost.md").write_text(
                f"---\npaths:\n  - lib/**\n---\n{rp.MARKER_LINE}\n이 경로는 `ghost` 도메인이다.\n", encoding="utf-8"
            )
            res = rp.check_rules_pointer(ws)
            warns = [r for r in res if r.level == Result.WARN]
            self.assertEqual(len(warns), 1)
            self.assertIn("MANIFEST 에 없음", warns[0].message)
            self.assertFalse(any(r.level == Result.PASS for r in res))

    def test_missing_pointer_warn_and_differs_info(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_repo(td) / "workspace"
            rp.write_rules_files(ws)
            (ws / "context" / "rules" / "wms.md").unlink()  # 포인터가 가리키던 규칙 파일 삭제
            res = rp.check_rules_pointer(ws)
            self.assertTrue(any(r.level == Result.WARN and "포인터 경로 부재" in r.message for r in res), _levels(res))
            self.assertTrue(any(r.level == Result.INFO and "재생성 결과와 다름" in r.message for r in res), _levels(res))

    def test_overlap_and_claude_md_excludes_info(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _make_repo(td)
            ws = repo / "workspace"
            rp.write_rules_files(ws)
            rdir = rp.rules_dir(ws)
            for d in ("wms", "billing"):
                p = rdir / f"pilot-{d}.md"
                p.write_text(p.read_text(encoding="utf-8").replace("paths:\n", "paths:\n  - lib/shared/**\n", 1), encoding="utf-8")
            (repo / ".claude" / "settings.json").write_text(json.dumps({"claudeMdExcludes": [".claude/rules/**"]}), encoding="utf-8")
            res = rp.check_rules_pointer(ws)
            msgs = [r.message for r in res]
            self.assertTrue(any("`lib/shared/**` 가" in m for m in msgs), msgs)
            self.assertTrue(any("claudeMdExcludes" in m for m in msgs), msgs)

    def test_check_workspace_includes_rules_pointer(self):
        with tempfile.TemporaryDirectory() as td:
            ws = _make_repo(td) / "workspace"
            rp.write_rules_files(ws)
            labels = [r.label for r in integrity.check_workspace(ws)]
            self.assertIn("규칙 포인터", labels)


class DomainPointerHookTest(unittest.TestCase):
    def _run(self, repo: Path, file_path: str, session: str = "s1") -> str:
        env = dict(os.environ)
        env.update({"CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT), "CLAUDE_PROJECT_DIR": str(repo), "TMPDIR": str(repo / "tmp")})
        payload = {"tool_input": {"file_path": file_path}, "session_id": session}
        proc = subprocess.run(["bash", str(HOOK)], input=json.dumps(payload), capture_output=True, text=True, env=env, cwd=str(repo))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.strip()

    def test_hook_fires_once_and_is_silent_otherwise(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _make_repo(td)
            self.assertEqual(self._run(repo, str(repo / "app" / "services" / "wms" / "a.rb")), "")  # 규칙 파일 없음
            rp.write_rules_files(repo / "workspace")
            out = json.loads(self._run(repo, str(repo / "app" / "services" / "wms" / "a.rb")))
            ctx = out["hookSpecificOutput"]["additionalContext"]
            self.assertTrue(ctx.startswith("[도메인 포인터] 이 경로는 `wms` 도메인이다."))
            self.assertIn("- 진입: workspace/context/wms/index.md", ctx)
            self.assertNotIn("<!--", ctx)
            self.assertEqual(self._run(repo, str(repo / "app" / "services" / "wms" / "b.rb")), "")  # 같은 세션 2회
            self.assertEqual(self._run(repo, str(repo / "spec" / "wms_spec.rb"), "s2"), "")            # 비매칭

    def test_registered_in_hooks_json(self):
        data = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        post = [h for entry in data["hooks"]["PostToolUse"] for h in entry["hooks"]]
        cmds = [h["command"] for h in post]
        self.assertIn("bash ${CLAUDE_PLUGIN_ROOT}/hooks/domain-pointer.sh", cmds)
        self.assertEqual(cmds.index("bash ${CLAUDE_PLUGIN_ROOT}/hooks/coding-rules.sh") + 1,
                         cmds.index("bash ${CLAUDE_PLUGIN_ROOT}/hooks/domain-pointer.sh"))
        self.assertTrue(all(h.get("timeout", 0) <= 5 for h in post))


if __name__ == "__main__":
    unittest.main()
