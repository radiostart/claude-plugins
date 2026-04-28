"""
tools/doctor.py 의 Slack secret 보호 로직 단위 테스트.

    - check_gitignore_required_patterns
    - check_slack_env_not_tracked

실행:
    python3 tests/tools/test_doctor_slack.py
"""

import importlib.util
import subprocess
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


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "t"], check=True)


class GitignorePatterns(unittest.TestCase):

    def test_missing_patterns_are_auto_appended(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            workspace = repo / "workspace"
            workspace.mkdir()
            # .gitignore 가 아예 없음
            results = doctor.check_gitignore_required_patterns(workspace)
            gitignore = repo / ".gitignore"
            self.assertTrue(gitignore.is_file())
            content = gitignore.read_text(encoding="utf-8")
            self.assertIn(".slack.env", content)
            # 결과에 WARN (자동 주입) 존재
            self.assertTrue(any(r.level == "WARN" for r in results))

    def test_existing_pattern_passes(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            workspace = repo / "workspace"
            workspace.mkdir()
            (repo / ".gitignore").write_text(".slack.env\n", encoding="utf-8")
            results = doctor.check_gitignore_required_patterns(workspace)
            self.assertTrue(any(r.level == "PASS" for r in results))
            self.assertFalse(any(r.level in ("WARN", "ERROR") for r in results))

    def test_append_preserves_existing_content(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            workspace = repo / "workspace"
            workspace.mkdir()
            (repo / ".gitignore").write_text("node_modules/\n.env\n", encoding="utf-8")
            doctor.check_gitignore_required_patterns(workspace)
            content = (repo / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("node_modules/", content)
            self.assertIn(".env", content)
            self.assertIn(".slack.env", content)


class TrackedGuard(unittest.TestCase):

    def test_untracked_file_produces_no_error(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            proj = repo / "workspace" / "projects" / "X"
            proj.mkdir(parents=True)
            (proj / ".slack.env").write_text("SLACK_WEBHOOK_URL=x\n", encoding="utf-8")
            results = doctor.check_slack_env_not_tracked(repo / "workspace")
            self.assertEqual(results, [])

    def test_tracked_file_produces_critical_error(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            proj = repo / "workspace" / "projects" / "X"
            proj.mkdir(parents=True)
            slack_env = proj / ".slack.env"
            slack_env.write_text("SLACK_WEBHOOK_URL=x\n", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(repo), "add", "-f",
                 str(slack_env.relative_to(repo))],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(repo), "commit", "-q", "-m", "tracked"],
                check=True,
            )
            results = doctor.check_slack_env_not_tracked(repo / "workspace")
            self.assertEqual(len(results), 1)
            r = results[0]
            self.assertEqual(r.level, "ERROR")
            self.assertIn("[CRITICAL]", r.label)
            self.assertIn("git rm --cached", r.hint)

    def test_no_slack_env_files_produces_empty(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _init_git_repo(repo)
            proj = repo / "workspace" / "projects" / "X"
            proj.mkdir(parents=True)
            results = doctor.check_slack_env_not_tracked(repo / "workspace")
            self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
