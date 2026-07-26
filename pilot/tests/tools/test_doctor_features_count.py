"""
pilot/tools/doctor/_common.py 의 count_real_features / is_feature_spec_file 단위 테스트.

features/ 디렉터리는 spec (`NN-slug.md`) 외에 파생 산출물(`NN-slug.plan.md`·
`NN-slug.plan.critic.md` 등 다중 확장자)을 함께 담는다. count_real_features 는
spec 만 세야 하고, 파생 산출물 접미사가 늘어도 (`is_feature_spec_file` 의
"stem 에 `.` 이 있으면 파생" 규칙으로) 자동으로 제외돼야 한다 (#23).

    - test_mixed_spec_and_derived_counts_spec_only : spec 3 + .plan.md 2 + .plan.critic.md 2 → 3
    - test_derived_only_counts_zero                : 파생 산출물만 존재 → 0 (analyzed=true WARN 이 살아나는 참 케이스)
    - test_future_suffix_auto_excluded              : 미래 접미사(.plan.review.md) 도 자동 제외
    - test_subdirs_and_non_md_ignored               : 하위 디렉터리·.txt·.yml 무시 (기존 거동 유지)
    - test_dotted_spec_stem_not_counted             : [잔여 리스크 고정] spec 파일명 stem 자체에 `.` 이 있으면
      "stem 에 `.` 이 있으면 파생" 규칙 때문에 spec 임에도 미카운트된다 — 현재 규칙의 판정 결과를 문서화하는 테스트
      (버그 수정이 아니라 경계 고정. 회귀 시 이 테스트가 실패로 알려준다).

실행:
    python3 pilot/tests/tools/test_doctor_features_count.py
"""

import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent

# tools/ 를 sys.path 에 추가하여 doctor 패키지를 직접 import (doctor.py 는 더 이상
# backward-compat re-export 를 제공하지 않음 — #20 스텝 3).
_TOOLS_DIR = str(PLUGIN_ROOT / "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

import doctor._common as common  # noqa: E402


def _touch(features_dir: Path, name: str) -> None:
    (features_dir / name).write_text("# stub\n", encoding="utf-8")


class MixedSpecAndDerived(unittest.TestCase):
    def test_mixed_spec_and_derived_counts_spec_only(self):
        with tempfile.TemporaryDirectory() as td:
            features_dir = Path(td) / "features"
            features_dir.mkdir()
            for name in ("01-a.md", "02-b.md", "03-c.md"):
                _touch(features_dir, name)
            for name in ("01-a.plan.md", "02-b.plan.md"):
                _touch(features_dir, name)
            for name in ("01-a.plan.critic.md", "02-b.plan.critic.md"):
                _touch(features_dir, name)
            self.assertEqual(common.count_real_features(features_dir), 3)


class DerivedOnlyCountsZero(unittest.TestCase):
    def test_derived_only_counts_zero(self):
        with tempfile.TemporaryDirectory() as td:
            features_dir = Path(td) / "features"
            features_dir.mkdir()
            _touch(features_dir, "01-a.plan.md")
            _touch(features_dir, "01-a.plan.critic.md")
            self.assertEqual(common.count_real_features(features_dir), 0)


class FutureSuffixAutoExcluded(unittest.TestCase):
    def test_future_suffix_auto_excluded(self):
        with tempfile.TemporaryDirectory() as td:
            features_dir = Path(td) / "features"
            features_dir.mkdir()
            _touch(features_dir, "01-a.md")
            _touch(features_dir, "07-x.plan.review.md")
            self.assertEqual(common.count_real_features(features_dir), 1)


class SubdirsAndNonMdIgnored(unittest.TestCase):
    def test_subdirs_and_non_md_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            features_dir = Path(td) / "features"
            features_dir.mkdir()
            _touch(features_dir, "01-a.md")
            (features_dir / "subdir").mkdir()
            _touch(features_dir / "subdir", "02-b.md")
            (features_dir / "notes.txt").write_text("x", encoding="utf-8")
            (features_dir / "config.yml").write_text("x", encoding="utf-8")
            self.assertEqual(common.count_real_features(features_dir), 1)


class DottedSpecStemNotCounted(unittest.TestCase):
    def test_dotted_spec_stem_not_counted(self):
        """[잔여 리스크 고정] spec 파일명 자체가 stem 에 `.` 을 포함하면 (예: 버전 표기
        `05-v1.0-release.md`) "stem 에 `.` 이 있으면 파생 산출물" 규칙에 걸려 spec 임에도
        카운트되지 않는다.

        이는 planner 승인 시점에 인지된 알려진 경계다 (plan.md § 채택할 판정 규칙 각주).
        버그를 고치는 테스트가 아니라 **현재 규칙이 이 입력을 어떻게 판정하는지 고정**하는
        문서화 테스트 — 향후 판정 규칙이 바뀌면 이 테스트가 먼저 실패해 알려준다.
        """
        with tempfile.TemporaryDirectory() as td:
            features_dir = Path(td) / "features"
            features_dir.mkdir()
            _touch(features_dir, "01-a.md")
            _touch(features_dir, "05-v1.0-release.md")  # 실제 spec 이지만 stem 에 "." 포함
            # is_feature_spec_file() 단독 판정: 점 있는 stem은 False (파생 취급).
            self.assertFalse(
                common.is_feature_spec_file(features_dir / "05-v1.0-release.md"),
                "stem 에 '.' 이 있는 실제 spec 파일명도 파생으로 오판정되는 현재 규칙을 고정",
            )
            # count_real_features 도 동일 규칙을 따라 "01-a.md" 1건만 센다 (2건이 아님).
            self.assertEqual(
                common.count_real_features(features_dir),
                1,
                "dotted-stem spec 은 미카운트 — 현재 규칙의 알려진 경계",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
