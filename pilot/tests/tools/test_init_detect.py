"""
pilot/tools/init_detect.py 단위 테스트.

실행:
    python3 -m unittest pilot.tests.tools.test_init_detect
    python3 -m unittest discover pilot/tests/tools -p "test_init_detect.py"

의존성: Python 표준 라이브러리만 (pip install 불필요).
"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "init_detect.py"


def _load_init_detect():
    """init_detect.py 를 importlib 로 로드 (doctor.py 패턴 답습)."""
    spec = importlib.util.spec_from_file_location("init_detect_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load_init_detect()
detect_languages = _mod.detect_languages
detect_scope_candidates = _mod.detect_scope_candidates
IGNORE_BASELINE = _mod.IGNORE_BASELINE
LANG_EXT_MAP = _mod.LANG_EXT_MAP
SCOPE_FOLDER_MAP = _mod.SCOPE_FOLDER_MAP


class TestDetectLanguagesPythonOnly(unittest.TestCase):
    """케이스 1: .py 파일만 있으면 ["python"] 반환."""

    def test_detect_languages_python_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i in range(5):
                (root / f"file{i}.py").write_text("# py", encoding="utf-8")
            langs, info = detect_languages(root)
            self.assertEqual(langs, ["python"])
            # INFO 메시지 없음 (비매핑 확장자 없음)
            unmapped_infos = [m for m in info if "매핑되지 않은 확장자" in m]
            self.assertEqual(len(unmapped_infos), 0)


class TestDetectLanguagesTop3Truncation(unittest.TestCase):
    """케이스 2: 상위 3개 언어만 반환 (4개 있어도 3개로 잘림)."""

    def test_detect_languages_top3_truncation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # .py 10개, .ts 8개, .go 5개, .java 3개
            for i in range(10):
                (root / f"a{i}.py").write_text("", encoding="utf-8")
            for i in range(8):
                (root / f"b{i}.ts").write_text("", encoding="utf-8")
            for i in range(5):
                (root / f"c{i}.go").write_text("", encoding="utf-8")
            for i in range(3):
                (root / f"d{i}.java").write_text("", encoding="utf-8")

            langs, _ = detect_languages(root)
            self.assertEqual(langs, ["python", "typescript", "go"])
            self.assertNotIn("java", langs)


class TestDetectLanguagesZeroMatchReturnsEmpty(unittest.TestCase):
    """케이스 3: 매핑 안 되는 확장자만 있으면 [] + info 메시지."""

    def test_detect_languages_zero_match_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i in range(5):
                (root / f"file{i}.rs").write_text("", encoding="utf-8")  # rust — 미매핑
            for i in range(3):
                (root / f"doc{i}.md").write_text("", encoding="utf-8")   # md — 미매핑

            langs, info = detect_languages(root)
            self.assertEqual(langs, [])
            # INFO 메시지에 비매핑 확장자 언급
            unmapped_infos = [m for m in info if "매핑되지 않은 확장자" in m]
            self.assertGreater(len(unmapped_infos), 0)
            self.assertIn(".rs", unmapped_infos[0])


class TestDetectLanguagesRespectsIgnoreBaseline(unittest.TestCase):
    """케이스 4: node_modules/ 하위 .py 100개는 집계 제외."""

    def test_detect_languages_respects_ignore_baseline(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # node_modules 안에 .py 100개
            nm = root / "node_modules" / "some_pkg"
            nm.mkdir(parents=True)
            for i in range(100):
                (nm / f"dep{i}.py").write_text("", encoding="utf-8")
            # 실제 소스에 .ts 2개
            for i in range(2):
                (root / f"src{i}.ts").write_text("", encoding="utf-8")

            langs, _ = detect_languages(root)
            # python 이 집계되면 안 됨 (node_modules 제외)
            self.assertNotIn("python", langs)
            self.assertIn("typescript", langs)


class TestDetectScopeCandidatesSingleFolder(unittest.TestCase):
    """케이스 5: models/ 단일 폴더 → {"models": "Models"} (빈도 ≥ 1, Q1)."""

    def test_detect_scope_candidates_single_folder(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "models").mkdir()
            scope_map, _ = detect_scope_candidates(root)
            self.assertIn("models", scope_map)
            self.assertEqual(scope_map["models"], "Models")


class TestDetectScopeCandidatesUnmappedFolderExcluded(unittest.TestCase):
    """케이스 6: 매핑 안 되는 폴더(lib/, utils/)는 결과 dict 미포함 + info."""

    def test_detect_scope_candidates_unmapped_folder_excluded(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "lib").mkdir()
            (root / "utils").mkdir()
            scope_map, info = detect_scope_candidates(root)
            self.assertNotIn("lib", scope_map)
            self.assertNotIn("utils", scope_map)
            # INFO 메시지에 미매핑 폴더 언급
            unmapped_infos = [m for m in info if "매핑되지 않은 폴더" in m]
            self.assertGreater(len(unmapped_infos), 0)


class TestDetectLanguagesSamplingMaxFiles(unittest.TestCase):
    """케이스 7: max_files=10 으로 잘라도 예외 없이 종료 + INFO 메시지."""

    def test_detect_languages_sampling_max_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # 50개 .py 파일 생성
            for i in range(50):
                (root / f"file{i}.py").write_text("", encoding="utf-8")

            # 예외 없이 종료해야 함
            try:
                langs, info = detect_languages(root, max_files=10)
            except Exception as e:
                self.fail(f"detect_languages raised {e} with max_files=10")

            # INFO 메시지에 샘플링 안내 포함
            sampling_infos = [m for m in info if "샘플링" in m]
            self.assertGreater(len(sampling_infos), 0)


class TestIgnoreBaselineConstantHasRequiredPatterns(unittest.TestCase):
    """케이스 8: IGNORE_BASELINE 에 spec line 28 의 10 패턴 전부 포함."""

    def test_ignore_baseline_constant_has_required_patterns(self):
        # spec #13 line 28 에 명시된 10 패턴
        required = [
            ".git/",
            "node_modules/",
            "__pycache__/",
            "vendor/",
            "dist/",
            "build/",
            ".next/",
            "target/",
            "*.pyc",
            "*.lock",
        ]
        for pattern in required:
            self.assertIn(
                pattern,
                IGNORE_BASELINE,
                msg=f"IGNORE_BASELINE 에 '{pattern}' 이 없음",
            )
        # 정확히 10개 이상 (추가 항목 허용)
        self.assertGreaterEqual(len(IGNORE_BASELINE), 10)


if __name__ == "__main__":
    unittest.main()
