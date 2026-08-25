"""
tools/jira.py 단위 테스트.

커버리지:
  - 키 형식 검증 (invalid key format)
  - 화이트리스트 분기 (env / config.md 표·리스트 / 미설정 / TTY 유무)
  - 환경변수 부재 (JIRA_*) → exit 1 + stderr 안내
  - HTTP 동작 (urlopen mock):
      * fetch 200 → stdout summary/status/reporter
      * fetch 404 → exit 1
      * comment 201 → stdout `OK`
      * comment HTTPError 401 / URLError → stderr 첫 줄 `[ERROR] COMMENT FAILED for {KEY}`

실행:
    python3 pilot/tests/tools/test_jira.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "jira.py"


def _load_jira(workspace_root: Path | None = None):
    """jira.py 를 신선한 모듈로 로드. CLAUDE_PROJECT_DIR 을 일시 변경해 _load_dotenv 가
    테스트 디렉토리만 보도록 한다."""
    saved = os.environ.get("CLAUDE_PROJECT_DIR")
    if workspace_root is not None:
        os.environ["CLAUDE_PROJECT_DIR"] = str(workspace_root)
    else:
        # 호출자가 workspace_root 를 안 줬으면 빈 임시 dir 로 격리. CLAUDE_PROJECT_DIR
        # 미설정 시에도 필수 — jira.py 의 WORKSPACE_ROOT 가 CWD 로 폴백해, 저장소
        # 루트에서 실행하면 로컬 .env (git-ignored 인증 파일) 를 로드할 수 있다.
        td = tempfile.mkdtemp(prefix="jira_test_root_")
        os.environ["CLAUDE_PROJECT_DIR"] = td
    try:
        spec = importlib.util.spec_from_file_location("jira_mod_under_test", TOOL_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        if saved is None:
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
        else:
            os.environ["CLAUDE_PROJECT_DIR"] = saved
    return module


# 외부 환경 영향 차단 — JIRA_* / ATLASSIAN_* / JIRA_QA_PROJECT_KEY 를 clean state 로 시작.
_ENV_KEYS_TO_RESET = (
    "JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_TOKEN",
    "ATLASSIAN_BASE_URL", "ATLASSIAN_EMAIL", "ATLASSIAN_TOKEN",
    "JIRA_QA_PROJECT_KEY",
)


@contextlib.contextmanager
def clean_env(**overrides: str):
    """JIRA_* / ATLASSIAN_* 환경변수만 격리. 다른 키는 그대로 둔다."""
    saved = {k: os.environ.get(k) for k in _ENV_KEYS_TO_RESET}
    for k in _ENV_KEYS_TO_RESET:
        os.environ.pop(k, None)
    for k, v in overrides.items():
        os.environ[k] = v
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


@contextlib.contextmanager
def capture_io(stdin: str | None = None):
    """stdout/stderr 캡처 + 선택적 stdin 주입."""
    out = io.StringIO()
    err = io.StringIO()
    saved_stdin = sys.stdin
    if stdin is not None:
        sys.stdin = io.StringIO(stdin)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            yield out, err
    finally:
        sys.stdin = saved_stdin


def _fresh_module():
    """매 테스트마다 신선한 모듈 (모듈 레벨 캐시 회피)."""
    return _load_jira()


# ---------------------------------------------------------------------------
# Key format validation
# ---------------------------------------------------------------------------

class KeyFormatValidation(unittest.TestCase):
    def test_lowercase_rejected(self):
        with clean_env():
            mod = _fresh_module()
            with capture_io() as (_, err):
                with self.assertRaises(SystemExit) as ctx:
                    mod.validate_key_format("shop1234")
            self.assertEqual(ctx.exception.code, 1)
            self.assertIn("invalid key format", err.getvalue())

    def test_mixed_case_prefix_rejected(self):
        with clean_env():
            mod = _fresh_module()
            with capture_io() as (_, err):
                with self.assertRaises(SystemExit):
                    mod.validate_key_format("qaprj-1")
            self.assertIn("invalid key format", err.getvalue())

    def test_empty_rejected(self):
        with clean_env():
            mod = _fresh_module()
            with capture_io() as (_, err):
                with self.assertRaises(SystemExit):
                    mod.validate_key_format("")
            self.assertIn("invalid key format", err.getvalue())

    def test_valid_passes_silently(self):
        with clean_env():
            mod = _fresh_module()
            with capture_io() as (out, err):
                mod.validate_key_format("SHOP-1234")  # no exit
            self.assertEqual(out.getvalue(), "")
            self.assertEqual(err.getvalue(), "")


# ---------------------------------------------------------------------------
# Whitelist behavior
# ---------------------------------------------------------------------------

class WhitelistBehavior(unittest.TestCase):
    def test_no_env_no_config_passes(self):
        with clean_env():
            with tempfile.TemporaryDirectory() as td:
                mod = _load_jira(Path(td))
                with capture_io() as (_, err):
                    mod.validate_key_whitelist("ANYTHING-99")  # no exit, no output
                self.assertEqual(err.getvalue(), "")

    def test_env_matches_silently(self):
        with clean_env(JIRA_QA_PROJECT_KEY="QAPRJ"):
            with tempfile.TemporaryDirectory() as td:
                mod = _load_jira(Path(td))
                with capture_io() as (_, err):
                    mod.validate_key_whitelist("QAPRJ-1")
                self.assertEqual(err.getvalue(), "")

    def test_env_mismatch_no_tty_refuses(self):
        with clean_env(JIRA_QA_PROJECT_KEY="QAPRJ"):
            with tempfile.TemporaryDirectory() as td:
                mod = _load_jira(Path(td))
                # 기본 sys.stdin 은 test runner 환경에서 보통 non-TTY (isatty False).
                with capture_io() as (_, err):
                    with self.assertRaises(SystemExit) as ctx:
                        mod.validate_key_whitelist("SHOP-1")
                self.assertEqual(ctx.exception.code, 1)
                self.assertIn("[WARN]", err.getvalue())
                self.assertIn("QAPRJ", err.getvalue())
                self.assertIn("SHOP", err.getvalue())
                self.assertIn("non-interactive", err.getvalue())

    def test_env_mismatch_tty_y_proceeds(self):
        with clean_env(JIRA_QA_PROJECT_KEY="QAPRJ"):
            with tempfile.TemporaryDirectory() as td:
                mod = _load_jira(Path(td))
                fake_stdin = io.StringIO("y\n")
                fake_stdin.isatty = lambda: True  # type: ignore[attr-defined]
                saved = sys.stdin
                sys.stdin = fake_stdin
                try:
                    err = io.StringIO()
                    with contextlib.redirect_stderr(err):
                        mod.validate_key_whitelist("SHOP-1")  # no exit
                    self.assertIn("[WARN]", err.getvalue())
                    self.assertIn("Proceed anyway", err.getvalue())
                finally:
                    sys.stdin = saved

    def test_env_mismatch_tty_n_refuses(self):
        with clean_env(JIRA_QA_PROJECT_KEY="QAPRJ"):
            with tempfile.TemporaryDirectory() as td:
                mod = _load_jira(Path(td))
                fake_stdin = io.StringIO("n\n")
                fake_stdin.isatty = lambda: True  # type: ignore[attr-defined]
                saved = sys.stdin
                sys.stdin = fake_stdin
                try:
                    err = io.StringIO()
                    with contextlib.redirect_stderr(err):
                        with self.assertRaises(SystemExit) as ctx:
                            mod.validate_key_whitelist("SHOP-1")
                    self.assertEqual(ctx.exception.code, 1)
                    self.assertIn("aborted", err.getvalue())
                finally:
                    sys.stdin = saved

    def test_config_md_table_row_takes_precedence_over_env(self):
        # workspace/context/config.md 의 jira_qa_project_key (표 행) 가 env 보다 우선.
        with clean_env(JIRA_QA_PROJECT_KEY="ENVKEY"):
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                cfg = root / "workspace" / "context" / "config.md"
                cfg.parent.mkdir(parents=True)
                cfg.write_text(
                    "## 설정\n\n"
                    "| 키 | 값 | 용도 |\n| --- | --- | --- |\n"
                    "| `jira_qa_project_key` | `CONFIGKEY` | QA 키 화이트리스트 |\n",
                    encoding="utf-8",
                )
                mod = _load_jira(root)
                # CONFIGKEY 매칭 → 통과
                with capture_io() as (_, err):
                    mod.validate_key_whitelist("CONFIGKEY-7")
                self.assertEqual(err.getvalue(), "")
                # ENVKEY 매칭이지만 config 가 우선이라 mismatch → non-TTY refuse
                with capture_io() as (_, err):
                    with self.assertRaises(SystemExit):
                        mod.validate_key_whitelist("ENVKEY-1")
                self.assertIn("CONFIGKEY", err.getvalue())

    def test_config_md_list_form_recognized(self):
        # `- jira_qa_project_key: KEY` 리스트 표기도 인식한다.
        with clean_env():
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                cfg = root / "workspace" / "context" / "config.md"
                cfg.parent.mkdir(parents=True)
                cfg.write_text("- jira_qa_project_key: LISTKEY\n", encoding="utf-8")
                mod = _load_jira(root)
                with capture_io() as (_, err):
                    mod.validate_key_whitelist("LISTKEY-3")
                self.assertEqual(err.getvalue(), "")


# ---------------------------------------------------------------------------
# Env presence
# ---------------------------------------------------------------------------

class EnvPresence(unittest.TestCase):
    def test_missing_base_url_exits(self):
        with clean_env(JIRA_EMAIL="a@b.com", JIRA_TOKEN="tok"):
            mod = _fresh_module()
            with capture_io() as (_, err):
                with self.assertRaises(SystemExit) as ctx:
                    mod.get_credentials()
            self.assertEqual(ctx.exception.code, 1)
            self.assertIn("ATLASSIAN_BASE_URL", err.getvalue())
            self.assertIn("env not set", err.getvalue())

    def test_all_present_returns_tuple(self):
        with clean_env(
            JIRA_BASE_URL="https://example.atlassian.net",
            JIRA_EMAIL="a@b.com",
            JIRA_TOKEN="tok",
        ):
            mod = _fresh_module()
            base, email, token = mod.get_credentials()
            self.assertEqual(base, "https://example.atlassian.net")
            self.assertEqual(email, "a@b.com")
            self.assertEqual(token, "tok")

    def test_atlassian_fallback_all_three(self):
        """JIRA_* 없을 때 ATLASSIAN_* 가 fallback 으로 사용된다."""
        with clean_env(
            ATLASSIAN_BASE_URL="https://example.atlassian.net",
            ATLASSIAN_EMAIL="a@b.com",
            ATLASSIAN_TOKEN="tok",
        ):
            mod = _fresh_module()
            base, email, token = mod.get_credentials()
            self.assertEqual(base, "https://example.atlassian.net")
            self.assertEqual(email, "a@b.com")
            self.assertEqual(token, "tok")

    def test_tool_specific_takes_priority(self):
        """JIRA_* 와 ATLASSIAN_* 가 동시에 있으면 JIRA_* 우선."""
        with clean_env(
            JIRA_BASE_URL="https://jira-priority.atlassian.net",
            JIRA_EMAIL="jira@b.com",
            JIRA_TOKEN="jira-tok",
            ATLASSIAN_BASE_URL="https://atl-fallback.atlassian.net",
            ATLASSIAN_EMAIL="atl@b.com",
            ATLASSIAN_TOKEN="atl-tok",
        ):
            mod = _fresh_module()
            base, email, token = mod.get_credentials()
            self.assertEqual(base, "https://jira-priority.atlassian.net")
            self.assertEqual(email, "jira@b.com")
            self.assertEqual(token, "jira-tok")

    def test_mixed_jira_and_atlassian(self):
        """JIRA_BASE_URL 만 있고 이메일·토큰은 ATLASSIAN_* — 항목별 독립 fallback."""
        with clean_env(
            JIRA_BASE_URL="https://example.atlassian.net",
            ATLASSIAN_EMAIL="a@b.com",
            ATLASSIAN_TOKEN="tok",
        ):
            mod = _fresh_module()
            base, email, token = mod.get_credentials()
            self.assertEqual(base, "https://example.atlassian.net")
            self.assertEqual(email, "a@b.com")
            self.assertEqual(token, "tok")

    def test_missing_recommends_atlassian(self):
        """둘 다 부재 시 에러 메시지가 ATLASSIAN_* 을 권장 (canonical 이름) 한다."""
        with clean_env():
            mod = _fresh_module()
            with capture_io() as (_, err):
                with self.assertRaises(SystemExit):
                    mod.get_credentials()
            msg = err.getvalue()
            # 메시지가 ATLASSIAN_* 권장 + JIRA_* 도 인식한다는 점 모두 안내
            self.assertIn("ATLASSIAN_", msg)
            self.assertIn("JIRA_", msg)


# ---------------------------------------------------------------------------
# HTTP behavior — urlopen mock
# ---------------------------------------------------------------------------

class _FakeResp:
    """`with urllib.request.urlopen(...) as resp:` 형태 호환 가짜 응답."""

    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._payload


def _fake_issue_json() -> bytes:
    return json.dumps({
        "key": "SHOP-1",
        "fields": {
            "summary": "장바구니 합산 오류",
            "status": {"name": "Open"},
            "reporter": {"displayName": "홍길동", "emailAddress": "hong@example.com"},
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "장바구니에서 합계가 1원 모자란다"}],
                    }
                ],
            },
            "attachment": [
                {"filename": "screenshot.png"},
                {"filename": "trace.log"},
            ],
        },
    }).encode("utf-8")


class FetchHttpBehavior(unittest.TestCase):
    def test_fetch_happy_path(self):
        with clean_env(
            JIRA_BASE_URL="https://example.atlassian.net",
            JIRA_EMAIL="a@b.com",
            JIRA_TOKEN="tok",
        ):
            mod = _fresh_module()
            with mock.patch.object(
                mod.urllib.request, "urlopen",
                return_value=_FakeResp(_fake_issue_json()),
            ):
                with capture_io() as (out, _):
                    mod.cmd_fetch("SHOP-1")
                output = out.getvalue()
        self.assertIn("장바구니 합산 오류", output)
        self.assertIn("Open", output)
        self.assertIn("홍길동", output)
        self.assertIn("장바구니에서 합계가 1원 모자란다", output)
        self.assertIn("screenshot.png", output)
        self.assertIn("trace.log", output)

    def test_fetch_404_exits(self):
        with clean_env(
            JIRA_BASE_URL="https://example.atlassian.net",
            JIRA_EMAIL="a@b.com",
            JIRA_TOKEN="tok",
        ):
            mod = _fresh_module()
            http_err = urllib.error.HTTPError(
                url="x", code=404, msg="Not Found", hdrs=None, fp=None,
            )
            with mock.patch.object(mod.urllib.request, "urlopen", side_effect=http_err):
                with capture_io() as (_, err):
                    rc = mod.cmd_fetch("SHOP-1")
            self.assertEqual(rc, 1)
            self.assertIn("fetch failed", err.getvalue())
            self.assertIn("404", err.getvalue())


class CommentHttpBehavior(unittest.TestCase):
    def test_comment_happy_path(self):
        with clean_env(
            JIRA_BASE_URL="https://example.atlassian.net",
            JIRA_EMAIL="a@b.com",
            JIRA_TOKEN="tok",
        ):
            mod = _fresh_module()
            with mock.patch.object(
                mod.urllib.request, "urlopen",
                return_value=_FakeResp(b'{"id":"10000"}'),
            ):
                with capture_io() as (out, _):
                    mod.cmd_comment("SHOP-1", "fix landed in abc1234")
                output = out.getvalue().strip()
        self.assertEqual(output, "OK")

    def test_comment_http_401_failure_header(self):
        with clean_env(
            JIRA_BASE_URL="https://example.atlassian.net",
            JIRA_EMAIL="a@b.com",
            JIRA_TOKEN="tok",
        ):
            mod = _fresh_module()
            http_err = urllib.error.HTTPError(
                url="x", code=401, msg="Unauthorized", hdrs=None, fp=None,
            )
            with mock.patch.object(mod.urllib.request, "urlopen", side_effect=http_err):
                with capture_io() as (_, err):
                    rc = mod.cmd_comment("SHOP-1", "msg")
            self.assertEqual(rc, 1)
            lines = err.getvalue().splitlines()
            self.assertGreaterEqual(len(lines), 2)
            self.assertEqual(lines[0], "[ERROR] COMMENT FAILED for SHOP-1")
            self.assertIn("401", lines[1])

    def test_comment_urlerror_failure_header(self):
        with clean_env(
            JIRA_BASE_URL="https://example.atlassian.net",
            JIRA_EMAIL="a@b.com",
            JIRA_TOKEN="tok",
        ):
            mod = _fresh_module()
            url_err = urllib.error.URLError("Name or service not known")
            with mock.patch.object(mod.urllib.request, "urlopen", side_effect=url_err):
                with capture_io() as (_, err):
                    rc = mod.cmd_comment("SHOP-1", "msg")
            self.assertEqual(rc, 1)
            lines = err.getvalue().splitlines()
            self.assertEqual(lines[0], "[ERROR] COMMENT FAILED for SHOP-1")
            self.assertIn("Name or service not known", lines[1])

    def test_comment_missing_env_still_has_header(self):
        # COMMENT FAILED 는 env 누락 시에도 stderr 첫 줄이어야 한다.
        with clean_env():  # JIRA_* / ATLASSIAN_* 모두 비어있음
            mod = _fresh_module()
            with capture_io() as (_, err):
                rc = mod.cmd_comment("SHOP-1", "msg")
            self.assertEqual(rc, 1)
            lines = err.getvalue().splitlines()
            self.assertGreaterEqual(len(lines), 1)
            self.assertEqual(lines[0], "[ERROR] COMMENT FAILED for SHOP-1")
            # 두 번째 줄부터 env 미설정 안내가 따라와야 한다 (canonical ATLASSIAN_* 권장).
            self.assertTrue(
                any("ATLASSIAN_" in ln for ln in lines[1:]),
                f"expected ATLASSIAN_* env hint after header, got: {lines!r}",
            )

    def test_comment_with_atlassian_fallback_proceeds(self):
        """JIRA_* 만 없고 ATLASSIAN_* 다 있으면 cmd_comment 가 정상 진행 (COMMENT FAILED 안 남)."""
        with clean_env(
            ATLASSIAN_BASE_URL="https://example.atlassian.net",
            ATLASSIAN_EMAIL="a@b.com",
            ATLASSIAN_TOKEN="tok",
        ):
            mod = _fresh_module()
            with mock.patch.object(
                mod.urllib.request, "urlopen",
                return_value=_FakeResp(b'{"id":"10000"}'),
            ):
                with capture_io() as (out, err):
                    mod.cmd_comment("SHOP-1", "msg")
            self.assertNotIn("COMMENT FAILED", err.getvalue())
            self.assertIn("OK", out.getvalue())


# ---------------------------------------------------------------------------
# ADF parsing smoke
# ---------------------------------------------------------------------------

class AdfParsing(unittest.TestCase):
    def test_paragraph_and_marks(self):
        with clean_env():
            mod = _fresh_module()
        adf = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "hello "},
                        {"type": "text", "text": "world", "marks": [{"type": "strong"}]},
                    ],
                },
            ],
        }
        out = mod.adf_to_text(adf)
        self.assertIn("hello", out)
        self.assertIn("**world**", out)

    def test_bullet_list(self):
        with clean_env():
            mod = _fresh_module()
        adf = {
            "type": "doc",
            "content": [
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [{
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "first"}],
                            }],
                        },
                        {
                            "type": "listItem",
                            "content": [{
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "second"}],
                            }],
                        },
                    ],
                },
            ],
        }
        out = mod.adf_to_text(adf)
        self.assertIn("- first", out)
        self.assertIn("- second", out)


# ---------------------------------------------------------------------------
# Steps-to-reproduce extraction
# ---------------------------------------------------------------------------

class ExtractStepsToReproduce(unittest.TestCase):
    def test_korean_heading(self):
        with clean_env():
            mod = _fresh_module()
        body = mod._extract_steps_to_reproduce(
            "## 재현 경로\n- step1\n- step2\n## 다른\nnoise\n",
            fields={},
        )
        self.assertEqual(body, "- step1\n- step2")

    def test_no_heading_returns_none(self):
        with clean_env():
            mod = _fresh_module()
        body = mod._extract_steps_to_reproduce(
            "그냥 설명만 있고 헤딩 없음\n장바구니가 깨졌어요\n",
            fields={},
        )
        self.assertIsNone(body)

    def test_heading_variants(self):
        with clean_env():
            mod = _fresh_module()
        # 재현 방법
        body = mod._extract_steps_to_reproduce(
            "## 재현 방법\n1. A\n2. B\n", fields={},
        )
        self.assertIn("1. A", body)
        self.assertIn("2. B", body)
        # Steps to reproduce (영문, 대소문자 무시)
        body = mod._extract_steps_to_reproduce(
            "### Steps to Reproduce\n- click X\n", fields={},
        )
        self.assertEqual(body.strip(), "- click X")
        # repro steps
        body = mod._extract_steps_to_reproduce(
            "# Repro Steps\nopen page\n", fields={},
        )
        self.assertEqual(body.strip(), "open page")


# ---------------------------------------------------------------------------
# _load_dotenv
# ---------------------------------------------------------------------------

class LoadDotenv(unittest.TestCase):
    def test_loads_jira_vars_and_emits_info(self):
        # UNRELATED_KEY 가 다른 테스트에 누수되지 않도록 명시적으로 cleanup.
        self.addCleanup(lambda: os.environ.pop("UNRELATED_KEY", None))
        with clean_env():
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                (root / ".env").write_text(
                    "JIRA_BASE_URL=https://example.atlassian.net\n"
                    "JIRA_EMAIL=u@example.com\n"
                    "# comment line\n"
                    "UNRELATED_KEY=ignore-me\n",
                    encoding="utf-8",
                )
                # _load_jira 가 모듈을 import 하면서 _load_dotenv() 를 실행한다.
                # 이때 stderr 를 캡처해 [INFO] 라인 출현 여부를 검증.
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    mod = _load_jira(root)
                # env 가 채워졌는지 확인
                self.assertEqual(
                    os.environ.get("JIRA_BASE_URL"),
                    "https://example.atlassian.net",
                )
                self.assertEqual(os.environ.get("JIRA_EMAIL"), "u@example.com")
                # 비-JIRA 키도 .env 에 있으면 env 에는 들어가지만 INFO 알림 대상은 아님.
                self.assertEqual(os.environ.get("UNRELATED_KEY"), "ignore-me")
                # [INFO] 라인 존재 + 로드된 키 이름이 포함
                err_text = err.getvalue()
                self.assertIn("[INFO] Loaded credentials", err_text)
                self.assertIn("JIRA_BASE_URL", err_text)
                self.assertIn("JIRA_EMAIL", err_text)
                # UNRELATED_KEY 는 credential prefix 가 아니므로 INFO 라인에 들어가면 안 됨.
                self.assertNotIn("UNRELATED_KEY", err_text)
                # mod 가 정상 로드되었는지도 한 번 더 확인
                self.assertTrue(hasattr(mod, "_load_dotenv"))


if __name__ == "__main__":
    unittest.main()
