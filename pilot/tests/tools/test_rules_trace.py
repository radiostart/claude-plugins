#!/usr/bin/env python3
"""
hooks/rules-trace.sh 테스트 — InstructionsLoaded 계측 훅 (#30 G4/G6 증거, opt-in).

    - 정상 입력 → 로그 1줄(JSON: ts·session·agent·reason·file·cwd), file_content 는 기록하지 않음
    - 서브에이전트 입력(agent_type) → agent 필드, 메인 → "main"
    - 잘못된 JSON → 로그 없음, exit 0 (무음 실패)
    - hooks.json 에는 등록되지 않음 (opt-in 계약)

실행:
    python3 pilot/tests/tools/test_rules_trace.py
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "rules-trace.sh"


def _run(payload: str, log: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PILOT_RULES_TRACE_LOG"] = str(log)
    return subprocess.run(["bash", str(HOOK)], input=payload, capture_output=True, text=True, env=env)


class RulesTraceTest(unittest.TestCase):
    def test_logs_one_json_line_without_content(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "trace.log"
            payload = json.dumps({
                "session_id": "s1", "hook_event_name": "InstructionsLoaded", "load_reason": "path_glob_match",
                "file_path": "/repo/.claude/rules/pilot-wms.md", "file_content": "SECRET-BODY", "cwd": "/repo",
            })
            proc = _run(payload, log)
            self.assertEqual((proc.returncode, proc.stdout), (0, ""))
            lines = log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            row = json.loads(lines[0])
            self.assertEqual((row["session"], row["agent"], row["reason"]), ("s1", "main", "path_glob_match"))
            self.assertEqual(row["file"], "/repo/.claude/rules/pilot-wms.md")
            self.assertNotIn("SECRET-BODY", lines[0])
            self.assertTrue(row["ts"])

    def test_subagent_type_and_append(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "trace.log"
            _run(json.dumps({"session_id": "s", "load_reason": "path_glob_match", "file_path": "a", "agent_type": "Explore"}), log)
            _run(json.dumps({"session_id": "s", "load_reason": "session_start", "file_path": "b"}), log)
            rows = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([(r["agent"], r["reason"]) for r in rows], [("Explore", "path_glob_match"), ("main", "session_start")])

    def test_invalid_json_silent(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "trace.log"
            proc = _run("not json", log)
            self.assertEqual((proc.returncode, proc.stdout), (0, ""))
            self.assertFalse(log.exists())

    def test_not_registered_in_plugin_hooks(self):
        data = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        self.assertNotIn("InstructionsLoaded", data["hooks"])
        self.assertNotIn("rules-trace.sh", json.dumps(data))


if __name__ == "__main__":
    unittest.main()
