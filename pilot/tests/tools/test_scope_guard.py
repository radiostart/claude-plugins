#!/usr/bin/env python3
"""
hooks/scope-guard.sh 동작 테스트 — bash 훅을 서브프로세스로 호출.

검증 대상:
  1. Ignore 패턴 차단 (기존 동작 회귀)
  2. characterize 모드에서 {source_root} 하위 Edit/Write 사전 차단
  3. characterize 모드에서도 테스트 계층 (test_path_convention) 은 허용
  4. 표준 모드 (mode 미설정) 에서는 source_root 수정 허용
  5. characterize 인데 source_root 미설정이면 통과 (graceful)

실행:
    python3 pilot/tests/tools/test_scope_guard.py
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "scope-guard.sh"


CONFIG_WITH_LANG = (
    "## Ignore\n\n"
    "| 패턴 | 사유 |\n"
    "| ---- | ---- |\n"
    "| `vendor/` | 생성 코드 |\n\n"
    "## 언어·도구 기본값\n\n"
    "| 키 | 값 | 용도 |\n"
    "| --- | --- | --- |\n"
    "| `source_root` | `app/` | 소스 루트 |\n"
    "| `test_path_convention` | `spec/**/*_spec.rb` | 테스트 경로 |\n"
)


def _make_project(td: str, state_yml_extra: str = "") -> Path:
    """STATE.md 활성 프로젝트 P + config.md + .agent-state.yml 을 갖춘 루트 생성."""
    root = Path(td)
    (root / "workspace" / "context").mkdir(parents=True)
    (root / "workspace" / "STATE.md").write_text(
        "| 모드    | 이름/이슈명 | 상태   |\n"
        "| ------- | ----------- | ------ |\n"
        "| project | P | 진행중 |\n",
        encoding="utf-8",
    )
    (root / "workspace" / "context" / "config.md").write_text(
        CONFIG_WITH_LANG, encoding="utf-8"
    )
    (root / "workspace" / "projects" / "P").mkdir(parents=True)
    (root / "workspace" / "projects" / "P" / ".agent-state.yml").write_text(
        "schema: v1.2\nanalyzed: true\ntdd: false\ndomain: orders\n" + state_yml_extra,
        encoding="utf-8",
    )
    return root


def _run_hook(root: Path, rel_file: str) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_input": {"file_path": str(root / rel_file)}})
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(root)
    return subprocess.run(
        ["bash", str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
    )


class IgnorePatternRegression(unittest.TestCase):
    def test_ignore_pattern_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_project(td)
            proc = _run_hook(root, "vendor/gen.rb")
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertIn("Ignore", proc.stderr)


class CharacterizeLockdown(unittest.TestCase):
    def test_characterize_blocks_source_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_project(td, state_yml_extra="mode: characterize\n")
            proc = _run_hook(root, "app/models/user.rb")
            self.assertEqual(proc.returncode, 2, f"차단 기대: {proc.stderr}")
            self.assertIn("characterize", proc.stderr)

    def test_characterize_allows_test_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_project(td, state_yml_extra="mode: characterize\n")
            proc = _run_hook(root, "spec/models/user_spec.rb")
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_characterize_allows_workspace_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_project(td, state_yml_extra="mode: characterize\n")
            proc = _run_hook(root, "workspace/projects/P/features/01-a.plan.md")
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_standard_mode_source_root_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_project(td)  # mode 미설정
            proc = _run_hook(root, "app/models/user.rb")
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_characterize_without_source_root_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_project(td, state_yml_extra="mode: characterize\n")
            # source_root 행 제거한 config 로 교체
            (root / "workspace" / "context" / "config.md").write_text(
                "## Ignore\n\n| 패턴 | 사유 |\n| ---- | ---- |\n| `vendor/` | 생성 코드 |\n",
                encoding="utf-8",
            )
            proc = _run_hook(root, "app/models/user.rb")
            self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
