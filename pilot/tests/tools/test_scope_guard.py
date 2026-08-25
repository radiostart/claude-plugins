#!/usr/bin/env python3
"""
hooks/scope-guard.sh 동작 테스트 — bash 훅을 서브프로세스로 호출.

검증 대상:
  1. Ignore 패턴 차단 (기존 동작 회귀)
  2. characterize 모드에서 {source_root} 하위 Edit/Write 사전 차단
  3. characterize 모드에서도 테스트 계층 (test_path_convention) 은 허용
  4. 표준 모드 (mode 미설정) 에서는 source_root 수정 허용
  5. characterize 인데 source_root 미설정이면 통과 (graceful)
  6. 경로 판정 — 프로젝트 밖 경로 통과, 심링크·비정규 표기·상대
     CLAUDE_PROJECT_DIR 에서도 프로젝트 안 파일은 판정 (무음 해제 방지)
  7. 패턴 해석 gitignore 규약 — 루트 앵커 vs `**/` 임의 깊이 구분,
     파일 패턴 substring 오차단 해소

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


def _run_hook_abs(project_dir: str, file_path: str) -> subprocess.CompletedProcess:
    """CLAUDE_PROJECT_DIR·file_path 를 문자열 그대로 전달 (표기 변형 테스트용)."""
    payload = json.dumps({"tool_input": {"file_path": file_path}})
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = project_dir
    return subprocess.run(
        ["bash", str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
    )


def _run_hook(root: Path, rel_file: str) -> subprocess.CompletedProcess:
    return _run_hook_abs(str(root), str(root / rel_file))


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


class OutsideProjectPaths(unittest.TestCase):
    """프로젝트 밖 경로는 Ignore 판정 대상이 아니다 — 오차단 방지."""

    def _root(self, td: str) -> Path:
        root = _make_project(td)
        (root / "workspace" / "context" / "config.md").write_text(
            "## Ignore\n\n"
            "| 패턴 | 사유 |\n"
            "| ---- | ---- |\n"
            "| `tmp/**` | 임시 산출물 |\n"
            "| `log/**` | 로그 |\n",
            encoding="utf-8",
        )
        return root

    def test_scratchpad_absolute_path_passes(self):
        # `/private/tmp/...` 가 `tmp/` 패턴에 걸리지 않아야 한다
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            proc = _run_hook_abs(str(root), "/private/tmp/claude-x/scratchpad/note.md")
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_other_repo_absolute_path_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            proc = _run_hook_abs(str(root), "/Users/other/another-repo/log/output.md")
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_relative_path_escaping_project_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            proc = _run_hook_abs(str(root), "../other-repo/tmp/foo.md")
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_relative_path_inside_project_blocked(self):
        # 상대 경로 입력은 종전대로 프로젝트 루트 상대로 취급
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            proc = _run_hook_abs(str(root), "tmp/foo.md")
            self.assertEqual(proc.returncode, 2, proc.stderr)


class PathNormalization(unittest.TestCase):
    """표기가 달라도 프로젝트 안이면 판정한다 — 가드 무음 해제 방지."""

    def _root(self, td: str) -> Path:
        root = _make_project(td)
        (root / "workspace" / "context" / "config.md").write_text(
            "## Ignore\n\n| 패턴 | 사유 |\n| ---- | ---- |\n| `tmp/**` | 임시 |\n",
            encoding="utf-8",
        )
        (root / "tmp").mkdir()
        return root

    def test_symlinked_project_dir_still_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            alias = Path(td).parent / f"alias-{Path(td).name}"
            os.symlink(root, alias)
            try:
                proc = _run_hook_abs(str(alias), str(root / "tmp/cache.md"))
                self.assertEqual(proc.returncode, 2, proc.stderr)
                proc = _run_hook_abs(str(root), str(alias / "tmp/cache.md"))
                self.assertEqual(proc.returncode, 2, proc.stderr)
            finally:
                os.unlink(alias)

    def test_non_canonical_absolute_path_still_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            noncanon = str(root.parent / "." / root.name / "tmp/cache.md")
            proc = _run_hook_abs(str(root), noncanon)
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_relative_project_dir_still_blocks(self):
        # 상대 CLAUDE_PROJECT_DIR — realpath 분기가 없으면 통째로 통과한다
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            payload = json.dumps({"tool_input": {"file_path": str(root / "tmp/cache.md")}})
            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = "."
            proc = subprocess.run(
                ["bash", str(HOOK)],
                input=payload,
                capture_output=True,
                text=True,
                env=env,
                cwd=str(root),
            )
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_trailing_slash_project_dir_still_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            proc = _run_hook_abs(str(root) + "/", str(root / "tmp/cache.md"))
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_glob_metachar_in_project_dir(self):
        # 경로에 glob 메타문자가 있어도 정상 파일 오차단·차단 누락이 없어야 한다
        with tempfile.TemporaryDirectory() as td:
            meta = Path(td) / "pr[oj]"
            meta.mkdir()
            root = _make_project(str(meta))
            (root / "workspace" / "context" / "config.md").write_text(
                "## Ignore\n\n| 패턴 | 사유 |\n| ---- | ---- |\n| `tmp/**` | 임시 |\n",
                encoding="utf-8",
            )
            proc = _run_hook_abs(str(root), str(root / "app/models/order.rb"))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            proc = _run_hook_abs(str(root), str(root / "tmp/cache.md"))
            self.assertEqual(proc.returncode, 2, proc.stderr)


class GitignoreSemantics(unittest.TestCase):
    """패턴 해석 gitignore 규약 — 앵커/임의 깊이 구분·glob 전체 대응."""

    def _root(self, td: str) -> Path:
        root = _make_project(td)
        (root / "workspace" / "context" / "config.md").write_text(
            "## Ignore\n\n"
            "| 패턴 | 사유 |\n"
            "| ---- | ---- |\n"
            "| `tmp/**` | 임시 산출물 |\n"
            "| `log/` | 로그 |\n"
            "| `public/**` | 정적 자산 |\n"
            "| `**/*.http` | HTTP 스크래치 |\n"
            "| `**/node_modules/**` | 의존성 |\n"
            "| `.env` | 시크릿 |\n",
            encoding="utf-8",
        )
        return root

    def test_root_anchored_blocks_top_level(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            proc = _run_hook(root, "tmp/cache.md")
            self.assertEqual(proc.returncode, 2, proc.stderr)
            proc = _run_hook(root, "public/index.html")
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_root_anchored_does_not_match_nested(self):
        # `tmp/**`·`public/**` 는 루트 앵커 — 하위 동명 폴더는 잡지 않는다
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            proc = _run_hook(root, "app/services/tmp/helper.rb")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            proc = _run_hook(root, "app/views/public/index.html")
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_trailing_slash_only_matches_any_depth(self):
        # `log/` (경로 중간 `/` 없음) 는 gitignore 규약상 임의 깊이
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            proc = _run_hook(root, "log/development.md")
            self.assertEqual(proc.returncode, 2, proc.stderr)
            proc = _run_hook(root, "app/log/app.rb")
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_directory_pattern_does_not_match_substring(self):
        # `log/` 가 `dialog/` 를 substring 으로 오매칭하지 않는다
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            proc = _run_hook(root, "dialog/foo.rb")
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_doublestar_prefix_matches_at_depth(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            proc = _run_hook(root, "packages/web/node_modules/pkg/index.js")
            self.assertEqual(proc.returncode, 2, proc.stderr)
            proc = _run_hook(root, "app/api/orders.http")
            self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_file_pattern_is_not_substring(self):
        # `*.http` 가 `api.httpie.md`·`response.http.json` 을 잡지 않는다
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            proc = _run_hook(root, "docs/api.httpie.md")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            proc = _run_hook(root, "spec/fixtures/response.http.json")
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_bare_filename_pattern_exact_match_any_depth(self):
        # `.env` 는 임의 깊이의 정확한 파일명만 — `.env.production` 은 미매칭
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            proc = _run_hook(root, "config/.env")
            self.assertEqual(proc.returncode, 2, proc.stderr)
            proc = _run_hook(root, "config/.env.production")
            self.assertEqual(proc.returncode, 0, proc.stderr)


class FailOpenStates(unittest.TestCase):
    def test_no_config_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "tmp").mkdir()
            proc = _run_hook_abs(str(root), str(root / "tmp/foo.md"))
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_empty_ignore_section_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_project(td)
            (root / "workspace" / "context" / "config.md").write_text(
                "## Ignore\n\n(없음)\n", encoding="utf-8"
            )
            proc = _run_hook(root, "tmp/foo.md")
            self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
