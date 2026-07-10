#!/usr/bin/env python3
"""
hooks/commit-format.sh 동작 테스트 — bash 훅을 서브프로세스로 호출.

이 훅은 advisory (항상 exit 0) — 차단 축이 아니라 '파싱 회귀 시 scope 검증이
조용히 무력화되는' 축을 커버한다 (감사 발견 F24). 따라서 단언은 exit code 가
아니라 stderr 경고의 유무로 한다.

검증 대상:
  1. config.md `## 설정` 표의 commit_scopes 추출 로직 (섹션 한정, 백틱 유무)
  2. `git commit -m "..."` / `-m '...'` 메시지 추출 로직
  3. --amend 검증 제외
  4. 50자 초과 제목 경고
  5. scope 없는 형식 (한국어 설명, [티켓]) 무경고 통과

주의: 기본 scope 목록의 구체 값은 shared/commit.md 와의 정렬 작업으로 바뀔 수
있어 스냅샷 단언하지 않는다 — scope 검증 로직은 항상 tempdir config.md 에 정의한
목록 기준으로 검증한다. (훅은 config.md 를 CLAUDE_PROJECT_DIR 이 아닌 CWD 상대로
읽으므로 cwd=tempdir 로 실행한다.)

실행:
    python3 pilot/tests/tools/test_commit_format.py
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "commit-format.sh"


def _write_config(root: Path, scopes_cell: str, section: str = "## 설정") -> None:
    """`{section}` 아래 commit_scopes 행을 가진 config.md 생성."""
    ctx = root / "workspace" / "context"
    ctx.mkdir(parents=True, exist_ok=True)
    (ctx / "config.md").write_text(
        f"{section}\n\n"
        "| 키 | 값 | 용도 |\n"
        "| --- | --- | --- |\n"
        f"| commit_scopes | {scopes_cell} | 커밋 scope 목록 |\n\n"
        "## 다음 섹션\n\n내용 없음\n",
        encoding="utf-8",
    )


def _run_hook(cwd: Path, command: str) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    return subprocess.run(
        ["bash", str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        cwd=str(cwd),
    )


class NonCommitAndAmend(unittest.TestCase):
    def test_non_commit_command_silent(self):
        with tempfile.TemporaryDirectory() as td:
            proc = _run_hook(Path(td), "ls -la")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stderr, "")

    def test_amend_excluded(self):
        """--amend 는 목록 밖 scope 라도 검증 제외 (무경고)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_config(root, "`alpha,beta`")
            proc = _run_hook(root, 'git commit --amend -m "gamma: 수정"')
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stderr, "")


class ConfigScopeExtraction(unittest.TestCase):
    """config.md `## 설정` 표에서 commit_scopes 추출."""

    def test_config_scope_passes_silently(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_config(root, "`alpha,beta`")
            proc = _run_hook(root, 'git commit -m "alpha: 기능 추가"')
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stderr, "")

    def test_unknown_scope_warns_but_exit_zero(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_config(root, "`alpha,beta`")
            proc = _run_hook(root, 'git commit -m "gamma: 기능 추가"')
            self.assertEqual(proc.returncode, 0, proc.stderr)  # advisory — 차단 없음
            self.assertIn("알 수 없는 scope", proc.stderr)
            self.assertIn("gamma", proc.stderr)

    def test_scopes_cell_without_backticks(self):
        """값 셀에 백틱이 없어도 추출된다."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_config(root, "alpha,beta")
            proc = _run_hook(root, 'git commit -m "beta: 정리"')
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stderr, "")

    def test_row_outside_settings_section_ignored(self):
        """`## 설정` 밖의 commit_scopes 행은 추출되지 않는다 — 섹션 한정 확인.

        기본 목록 값 자체는 단언하지 않는다: 잘못 추출됐다면 alpha 가 통과했을
        것이므로, '## 기타' 의 alpha 목록이 무시되어 경고가 나는지만 본다.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_config(root, "`alpha`", section="## 기타")
            proc = _run_hook(root, 'git commit -m "alpha: 기능"')
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("알 수 없는 scope", proc.stderr)

    def test_missing_config_does_not_crash(self):
        """config.md 부재 — fallback 기본값으로 동작하며 scope 형식이 아니면 무경고."""
        with tempfile.TemporaryDirectory() as td:
            proc = _run_hook(Path(td), 'git commit -m "임시 저장 커밋"')
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stderr, "")


class MessageExtraction(unittest.TestCase):
    """-m "..." / -m '...' 추출 로직."""

    def test_single_quote_message_extracted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_config(root, "`alpha`")
            proc = _run_hook(root, "git commit -m 'gamma: 작업'")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("gamma", proc.stderr)  # 추출됐어야 경고 가능

    def test_double_quote_with_extra_flags_extracted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_config(root, "`alpha`")
            proc = _run_hook(root, 'git commit -a --no-verify -m "gamma: 작업"')
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("gamma", proc.stderr)

    def test_heredoc_message_passes_silently(self):
        """heredoc 방식은 메시지 추출 불가 — 통과 (문서화된 한계)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_config(root, "`alpha`")
            cmd = 'git commit -m "$(cat <<\'EOF\'\ngamma: 작업\nEOF\n)"'
            proc = _run_hook(root, cmd)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stderr, "")

    def test_no_message_flag_passes_silently(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_config(root, "`alpha`")
            proc = _run_hook(root, "git commit -F /tmp/msg.txt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stderr, "")


class TitleRules(unittest.TestCase):
    def test_title_over_50_chars_warns(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_config(root, "`alpha`")
            long_title = "alpha: " + "x" * 60  # 67자
            proc = _run_hook(root, f'git commit -m "{long_title}"')
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("50자", proc.stderr)

    def test_korean_only_title_passes(self):
        """scope 없는 한국어 설명 (허용 형식 3) — 무경고."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_config(root, "`alpha`")
            proc = _run_hook(root, 'git commit -m "한국어 설명만 있는 커밋"')
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stderr, "")

    def test_ticket_format_passes(self):
        """[티켓번호] 형식 (허용 형식 2) — 무경고."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_config(root, "`alpha`")
            proc = _run_hook(root, 'git commit -m "[TICKET-123] 티켓 작업"')
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stderr, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
