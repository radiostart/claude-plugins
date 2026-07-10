#!/usr/bin/env python3
"""
hooks/protect-managed.sh 동작 테스트 — bash 훅을 서브프로세스로 호출.

검증 대상 (감사 발견 F24 권고 기준):
  1. workspace/projects/{P}/ 하위 *기존 파일* Write 차단 (exit 2)
  2. Bash destructive 명령 (리다이렉트 `>`/`>>`, mv, rm, sed -i, tee, cp,
     python open(..,'w')) 이 managed 파일을 겨냥할 때 차단
  3. 통과 케이스: 신규 파일 Write, Edit 도구, 백업 경로(.prompts.bak/),
     workspace/projects/ 외부 경로, 읽기 전용 명령
  4. PILOT_PROTECT_BYPASS=1 명시 우회
  5. 따옴표 unbalanced 명령의 보수적 fallback (workspace 토큰 전수 검사)

실행:
    python3 pilot/tests/tools/test_protect_managed.py
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "protect-managed.sh"


def _make_root(td: str) -> Path:
    """managed 파일(workspace/projects/P/ 하위 기존 파일)을 갖춘 프로젝트 루트 생성.

    protect-managed.sh 의 보호 대상 정의:
      - rel_path 가 ^workspace/projects/[^/]+/ 에 매칭되고
      - 대상 경로가 이미 존재(-e)하는 경우.
    """
    root = Path(td)
    proj = root / "workspace" / "projects" / "P"
    (proj / "features").mkdir(parents=True)
    (proj / "plan.md").write_text("# plan\n", encoding="utf-8")
    (proj / "features" / "01-a.md").write_text("# feature\n", encoding="utf-8")
    # 백업 경로 (통과 대상)
    bak = proj / ".prompts.bak" / "20260101-000000"
    bak.mkdir(parents=True)
    (bak / "planner.md").write_text("backup\n", encoding="utf-8")
    # workspace 이지만 projects/ 외부
    (root / "workspace" / "context").mkdir(parents=True)
    (root / "workspace" / "context" / "config.md").write_text("# config\n", encoding="utf-8")
    # workspace 외부
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("print('x')\n", encoding="utf-8")
    return root


def _run_hook(root: Path, payload: dict, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.pop("PILOT_PROTECT_BYPASS", None)  # 외부 환경 오염 차단
    env["CLAUDE_PROJECT_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        cwd=str(root),
    )


def _write(root: Path, rel: str) -> dict:
    return {"tool_name": "Write", "tool_input": {"file_path": str(root / rel)}}


def _edit(root: Path, rel: str) -> dict:
    return {"tool_name": "Edit", "tool_input": {"file_path": str(root / rel)}}


def _bash(cmd: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": cmd}}


class WriteProtection(unittest.TestCase):
    """Write 도구 — 기존 managed 파일만 차단."""

    def test_write_existing_managed_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _write(root, "workspace/projects/P/plan.md"))
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertIn("차단", proc.stderr)

    def test_write_new_file_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _write(root, "workspace/projects/P/new-file.md"))
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_edit_existing_managed_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _edit(root, "workspace/projects/P/plan.md"))
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_write_backup_path_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(
                root,
                _write(root, "workspace/projects/P/.prompts.bak/20260101-000000/planner.md"),
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_write_workspace_non_projects_passes(self):
        """workspace/ 이지만 projects/ 외부 (기존 파일) — 통과."""
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _write(root, "workspace/context/config.md"))
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_write_outside_workspace_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _write(root, "src/main.py"))
            self.assertEqual(proc.returncode, 0, proc.stderr)


class BashDestructiveTargets(unittest.TestCase):
    """Bash 도구 — 임베디드 파서의 destructive target 추론."""

    def test_redirect_overwrite_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash("echo x > workspace/projects/P/plan.md"))
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertIn("차단", proc.stderr)

    def test_redirect_append_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash("echo x >> workspace/projects/P/plan.md"))
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_redirect_glued_blocked(self):
        """`>file` 붙여쓴 리다이렉트도 감지."""
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash("echo x >workspace/projects/P/plan.md"))
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_redirect_new_file_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash("echo x > workspace/projects/P/new-file.md"))
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_mv_source_managed_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash("mv workspace/projects/P/plan.md /tmp/out.md"))
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_mv_target_managed_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash("mv notes.md workspace/projects/P/plan.md"))
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_rm_managed_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash("rm workspace/projects/P/features/01-a.md"))
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_rm_absolute_path_blocked(self):
        """절대 경로 target 도 CLAUDE_PROJECT_DIR 기준으로 정규화되어 차단."""
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash(f"rm {root}/workspace/projects/P/plan.md"))
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_rm_rf_project_dir_trailing_slash_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash("rm -rf workspace/projects/P/"))
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_rm_rf_project_dir_without_trailing_slash_blocked(self):
        """`rm -rf workspace/projects/P` (trailing slash 없음) 도 차단 —
        프로젝트 폴더 자체 삭제가 훅의 핵심 보호 대상 (감사 F24 에서 갭 발견 후 수정)."""
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash("rm -rf workspace/projects/P"))
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_sed_inplace_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash("sed -i 's/a/b/' workspace/projects/P/plan.md"))
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_sed_without_inplace_passes(self):
        """-i 없는 sed 는 읽기 전용 — 통과."""
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash("sed 's/a/b/' workspace/projects/P/plan.md"))
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_tee_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash("echo x | tee workspace/projects/P/plan.md"))
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_cp_target_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash("cp notes.md workspace/projects/P/plan.md"))
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_python_open_write_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            cmd = "python3 -c \"open('workspace/projects/P/plan.md', 'w').write('x')\""
            proc = _run_hook(root, _bash(cmd))
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_readonly_command_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash("grep -r plan workspace/projects/P/plan.md"))
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_bash_backup_path_passes(self):
        """Bash destructive 라도 .prompts.bak/ 백업 경로는 통과."""
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(
                root,
                _bash("rm workspace/projects/P/.prompts.bak/20260101-000000/planner.md"),
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)


class BypassEnv(unittest.TestCase):
    """PILOT_PROTECT_BYPASS 명시 우회."""

    def test_bypass_allows_write(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(
                root,
                _write(root, "workspace/projects/P/plan.md"),
                extra_env={"PILOT_PROTECT_BYPASS": "1"},
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_bypass_allows_bash(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(
                root,
                _bash("rm workspace/projects/P/plan.md"),
                extra_env={"PILOT_PROTECT_BYPASS": "1"},
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_bypass_other_value_still_blocks(self):
        """PILOT_PROTECT_BYPASS=0 등 '1' 이외 값은 우회 아님."""
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(
                root,
                _write(root, "workspace/projects/P/plan.md"),
                extra_env={"PILOT_PROTECT_BYPASS": "0"},
            )
            self.assertEqual(proc.returncode, 2, proc.stderr)


class UnbalancedQuoteFallback(unittest.TestCase):
    """shlex ValueError 시 보수적 fallback — 모든 workspace 토큰 검사."""

    def test_unbalanced_quote_existing_target_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash('echo "oops > workspace/projects/P/plan.md'))
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_unbalanced_quote_readonly_mention_still_blocked(self):
        """보수적 동작: 파괴적 문맥이 아니어도 기존 managed 경로 언급만으로 차단."""
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash('cat "workspace/projects/P/plan.md'))
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_unbalanced_quote_new_target_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash('echo "oops > workspace/projects/P/none.md'))
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_unbalanced_quote_no_workspace_token_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, _bash('echo "unbalanced quote'))
            self.assertEqual(proc.returncode, 0, proc.stderr)


class OtherTools(unittest.TestCase):
    def test_unknown_tool_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, {"tool_name": "Glob", "tool_input": {"pattern": "**/*.md"}})
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_write_without_file_path_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_root(td)
            proc = _run_hook(root, {"tool_name": "Write", "tool_input": {}})
            self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
