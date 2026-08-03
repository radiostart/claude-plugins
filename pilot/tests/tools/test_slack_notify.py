"""
tools/slack-notify.py 단위 테스트.

실행:
    python3 -m unittest tests.tools.test_slack_notify -v

    또는 (프로젝트 루트에서):
    python3 tests/tools/test_slack_notify.py
"""

import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "slack-notify.py"


def _load_tool_module():
    """하이픈 파일명 → importlib.util 로 동적 로드."""
    spec = importlib.util.spec_from_file_location("slack_notify_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


slack_notify = _load_tool_module()


def make_workspace(root: Path, project: str, *,
                   slack_env_content: str | None = None,
                   with_state_active: bool = True) -> Path:
    """테스트용 workspace 구조 생성. 프로젝트 경로 반환."""
    workspace = root / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    state_content = (
        "| mode | name | status |\n"
        "| --- | --- | --- |\n"
    )
    if with_state_active:
        state_content += f"| project | {project} | 진행중 |\n"
    (workspace / "STATE.md").write_text(state_content, encoding="utf-8")

    proj_dir = workspace / "projects" / project
    proj_dir.mkdir(parents=True, exist_ok=True)
    if slack_env_content is not None:
        (proj_dir / ".slack.env").write_text(slack_env_content, encoding="utf-8")
    return proj_dir


class NoopCases(unittest.TestCase):
    """설정 부재 · 필터링 등 no-op 경로."""

    def test_no_slack_env_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_workspace(root, "X", slack_env_content=None)
            stderr = io.StringIO()
            with mock.patch.object(slack_notify, "post_to_slack") as m_post, \
                    redirect_stderr(stderr):
                rc = slack_notify.main([
                    "--event", "complete",
                    "--workspace", str(root / "workspace"),
                ])
            self.assertEqual(rc, 0)
            m_post.assert_not_called()
            self.assertEqual(stderr.getvalue(), "")

    def test_webhook_empty_prints_one_stderr(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_workspace(
                root, "X",
                slack_env_content="SLACK_WEBHOOK_URL=\nSLACK_CHANNEL=#x\n",
            )
            stderr = io.StringIO()
            with mock.patch.object(slack_notify, "post_to_slack") as m_post, \
                    redirect_stderr(stderr):
                rc = slack_notify.main([
                    "--event", "complete",
                    "--workspace", str(root / "workspace"),
                ])
            self.assertEqual(rc, 0)
            m_post.assert_not_called()
            self.assertIn("SLACK_WEBHOOK_URL", stderr.getvalue())
            self.assertEqual(len(stderr.getvalue().strip().splitlines()), 1)

    def test_event_filtered_out(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_workspace(
                root, "X",
                slack_env_content=(
                    "SLACK_WEBHOOK_URL=https://hooks.slack.test/abc\n"
                    "SLACK_EVENTS=complete\n"
                ),
            )
            with mock.patch.object(slack_notify, "post_to_slack") as m_post:
                rc = slack_notify.main([
                    "--event", "approval",
                    "--workspace", str(root / "workspace"),
                ])
            self.assertEqual(rc, 0)
            m_post.assert_not_called()

    def test_no_active_project(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_workspace(
                root, "X",
                slack_env_content="SLACK_WEBHOOK_URL=https://x\n",
                with_state_active=False,
            )
            with mock.patch.object(slack_notify, "post_to_slack") as m_post:
                rc = slack_notify.main([
                    "--event", "complete",
                    "--workspace", str(root / "workspace"),
                ])
            self.assertEqual(rc, 0)
            m_post.assert_not_called()


class PostCases(unittest.TestCase):
    """정상 POST 및 네트워크 실패 경로."""

    # 제품 기본값(complete,approval,pr)이 아니라 명시 필터링 검증용 고정값.
    def _env_content(self, events: str = "complete,approval") -> str:
        return (
            "SLACK_WEBHOOK_URL=https://hooks.slack.test/abc\n"
            "SLACK_CHANNEL=#x\n"
            f"SLACK_EVENTS={events}\n"
        )

    def test_complete_success_invokes_post(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_workspace(root, "MyProject", slack_env_content=self._env_content())
            with mock.patch.object(slack_notify, "post_to_slack",
                                   return_value=(True, "ok")) as m_post, \
                    mock.patch.object(slack_notify, "is_tracked_by_git",
                                      return_value=False):
                rc = slack_notify.main([
                    "--event", "complete",
                    "--workspace", str(root / "workspace"),
                    "--feature-id", "10",
                ])
            self.assertEqual(rc, 0)
            m_post.assert_called_once()
            url, text = m_post.call_args.args
            self.assertEqual(url, "https://hooks.slack.test/abc")
            self.assertIn("MyProject", text)
            self.assertIn("#10", text)
            self.assertIn("✅", text)

    def test_approval_uses_message(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_workspace(root, "X", slack_env_content=self._env_content())
            with mock.patch.object(slack_notify, "post_to_slack",
                                   return_value=(True, "ok")) as m_post, \
                    mock.patch.object(slack_notify, "is_tracked_by_git",
                                      return_value=False):
                rc = slack_notify.main([
                    "--event", "approval",
                    "--workspace", str(root / "workspace"),
                    "--message", "DB 마이그레이션 승인",
                ])
            self.assertEqual(rc, 0)
            _, text = m_post.call_args.args
            self.assertIn("⏸", text)
            self.assertIn("DB 마이그레이션", text)

    def test_network_failure_returns_zero_with_stderr(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_workspace(root, "X", slack_env_content=self._env_content())
            stderr = io.StringIO()
            with mock.patch.object(slack_notify, "post_to_slack",
                                   return_value=(False, "HTTP 500: down")), \
                    mock.patch.object(slack_notify, "is_tracked_by_git",
                                      return_value=False), \
                    redirect_stderr(stderr):
                rc = slack_notify.main([
                    "--event", "complete",
                    "--workspace", str(root / "workspace"),
                ])
            self.assertEqual(rc, 0)
            self.assertIn("전송 실패", stderr.getvalue())


class TrackedFileGuard(unittest.TestCase):
    """.slack.env 가 git tracked 상태일 때 전송 차단."""

    def test_tracked_file_blocks_post(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_workspace(
                root, "X",
                slack_env_content="SLACK_WEBHOOK_URL=https://hooks.slack.test/abc\n",
            )
            stderr = io.StringIO()
            with mock.patch.object(slack_notify, "post_to_slack") as m_post, \
                    mock.patch.object(slack_notify, "is_tracked_by_git",
                                      return_value=True), \
                    redirect_stderr(stderr):
                rc = slack_notify.main([
                    "--event", "complete",
                    "--workspace", str(root / "workspace"),
                ])
            self.assertEqual(rc, 0)
            m_post.assert_not_called()
            self.assertIn("[CRITICAL]", stderr.getvalue())
            self.assertIn("git rm --cached", stderr.getvalue())


class IsTrackedIntegration(unittest.TestCase):
    """is_tracked_by_git: 실제 git 리포에서 동작 확인 (smoke)."""

    def test_untracked_file_returns_false(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            f = root / ".slack.env"
            f.write_text("SLACK_WEBHOOK_URL=x\n", encoding="utf-8")
            self.assertFalse(slack_notify.is_tracked_by_git(f))

    def test_tracked_file_returns_true(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "t@t"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "t"], check=True)
            f = root / ".slack.env"
            f.write_text("SLACK_WEBHOOK_URL=x\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", ".slack.env"], check=True)
            subprocess.run(
                ["git", "-C", str(root), "commit", "-q", "-m", "tracked"],
                check=True,
            )
            self.assertTrue(slack_notify.is_tracked_by_git(f))

    def test_non_git_dir_returns_false(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f = root / ".slack.env"
            f.write_text("x=y\n", encoding="utf-8")
            self.assertFalse(slack_notify.is_tracked_by_git(f))


if __name__ == "__main__":
    unittest.main(verbosity=2)
