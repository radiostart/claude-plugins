"""
skills/·agents/ 마크다운 인라인 링크 존재 검증 (감사 F20 재발 방지).

'agents→prompts' 리네임 미전파 같은 참조 드리프트를 CI 에서 잡는다.
docs_build.py 는 링크를 재작성만 할 뿐 존재 검증이 없으므로 중복 아님.

검증 대상 (두 종류만):
  1. `${CLAUDE_PLUGIN_ROOT}/...` 링크 → 플러그인 루트(pilot/) 기준 실존 검증
  2. 상대 경로 링크 (`./`·`../` 시작, 또는 경로 문자로 시작하고 검사 대상
     확장자로 끝나는 것) → 해당 md 파일 위치 기준 실존 검증

제외:
  - http(s):// 등 스킴 링크, mailto:
  - 앵커만 있는 링크 (#...)
  - `workspace/` 시작 — 소비 프로젝트 CWD 의존 경로
  - `{`·`}` 또는 `<`·`>` 플레이스홀더 포함 (예: features/NN-{slug}.md)
  - 앵커가 붙은 파일 링크는 앵커를 떼고 파일만 검증

실행:
    python3 tests/tools/test_doc_links.py
"""

import re
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent

SCAN_DIRS = ("skills", "agents")

# 상대 링크 중 확장자 기반으로 검사할 대상 (`./`·`../` 시작 링크는 확장자 무관 검사)
CHECKED_SUFFIXES = (".md", ".py", ".sh", ".yml", ".yaml", ".json", ".template")

PLUGIN_ROOT_PREFIX = "${CLAUDE_PLUGIN_ROOT}/"

# 인라인 링크 [text](target). 이미지 ![alt](target) 도 [alt](target) 부분이 매칭됨.
LINK_RE = re.compile(r"\[[^][]*\]\(([^()\s]+)\)")


def iter_markdown_files():
    for d in SCAN_DIRS:
        yield from sorted((PLUGIN_ROOT / d).rglob("*.md"))


def extract_targets(line: str):
    """한 줄에서 인라인 링크 target 목록을 추출한다."""
    return LINK_RE.findall(line)


def is_excluded(target: str) -> bool:
    if "://" in target or target.startswith("mailto:"):
        return True
    if target.startswith("#"):
        return True  # 같은 문서 내 앵커
    if target.startswith("workspace/"):
        return True  # 소비 프로젝트 CWD 의존 — 플러그인 저장소에 실존하지 않음
    if any(ch in target for ch in "{}<>"):
        return True  # 플레이스홀더 경로 (예: features/NN-{slug}.md)
    return False


def strip_anchor(target: str) -> str:
    return target.split("#", 1)[0]


def resolve(md_file: Path, target: str):
    """
    검증 대상이면 해석된 절대 경로를, 대상이 아니면 None 을 반환한다.
    """
    # ${CLAUDE_PLUGIN_ROOT} 자체가 {}·$ 를 포함하므로 제외 규칙보다 먼저 처리
    if target.startswith(PLUGIN_ROOT_PREFIX):
        rest = target[len(PLUGIN_ROOT_PREFIX):]
        if is_excluded(rest):
            return None
        rest = strip_anchor(rest)
        if not rest:
            return None
        return PLUGIN_ROOT / rest

    if is_excluded(target):
        return None
    target = strip_anchor(target)
    if not target:
        return None  # 앵커만 있던 링크

    if target.startswith(("./", "../")):
        return (md_file.parent / target).resolve()

    # 경로 문자로 시작하는 상대 링크 — 검사 대상 확장자로 끝나는 것만
    if target.endswith(CHECKED_SUFFIXES):
        return (md_file.parent / target).resolve()

    return None  # 디렉터리 표기 등 — 검증 대상 아님


def find_broken_links():
    """[(표시용 상대경로:라인, target, 해석 경로)] 목록을 반환한다."""
    broken = []
    for md_file in iter_markdown_files():
        rel = md_file.relative_to(PLUGIN_ROOT)
        text = md_file.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for target in extract_targets(line):
                resolved = resolve(md_file, target)
                if resolved is not None and not resolved.exists():
                    broken.append((f"{rel}:{lineno}", target, resolved))
    return broken


class ExtractTargets(unittest.TestCase):
    def test_basic_inline_link(self):
        self.assertEqual(
            extract_targets("본문 [문서](references/foo.md) 참조."),
            ["references/foo.md"],
        )

    def test_multiple_links_per_line(self):
        self.assertEqual(
            extract_targets("[a](x.md) 와 [b](../y.md)"),
            ["x.md", "../y.md"],
        )

    def test_no_link(self):
        self.assertEqual(extract_targets("일반 텍스트 (괄호) 포함"), [])


class ResolveRules(unittest.TestCase):
    MD = PLUGIN_ROOT / "skills" / "analyze" / "SKILL.md"

    def test_plugin_root_link_resolves_from_pilot_root(self):
        p = resolve(self.MD, "${CLAUDE_PLUGIN_ROOT}/skills/context/INDEX.md")
        self.assertEqual(p, PLUGIN_ROOT / "skills/context/INDEX.md")

    def test_dotdot_relative_resolves_from_md_dir(self):
        p = resolve(self.MD, "../commit/SKILL.md")
        self.assertEqual(p, PLUGIN_ROOT / "skills/commit/SKILL.md")

    def test_bare_relative_with_checked_suffix(self):
        p = resolve(self.MD, "references/scope-sync.md")
        self.assertEqual(p, self.MD.parent / "references/scope-sync.md")

    def test_http_excluded(self):
        self.assertIsNone(resolve(self.MD, "https://example.com/a.md"))

    def test_anchor_only_excluded(self):
        self.assertIsNone(resolve(self.MD, "#섹션-제목"))

    def test_anchor_stripped_from_file_link(self):
        p = resolve(self.MD, "references/scope-sync.md#모드")
        self.assertEqual(p, self.MD.parent / "references/scope-sync.md")

    def test_workspace_prefix_excluded(self):
        self.assertIsNone(resolve(self.MD, "workspace/projects/foo/plan.md"))

    def test_placeholder_braces_excluded(self):
        self.assertIsNone(resolve(self.MD, "features/NN-{slug}.md"))

    def test_placeholder_angle_brackets_excluded(self):
        self.assertIsNone(resolve(self.MD, "features/01-<feature-slug-a>.md"))

    def test_mailto_excluded(self):
        self.assertIsNone(resolve(self.MD, "mailto:dev@example.com"))

    def test_directory_notation_without_suffix_skipped(self):
        # `shared/` 같은 폴더 표기는 확장자 규칙에 안 걸리므로 검증 대상 아님
        self.assertIsNone(resolve(self.MD, "shared/"))


class DocLinksExist(unittest.TestCase):
    def test_scan_targets_exist(self):
        # 스캔 대상 자체가 사라지면 조용히 0건 통과하는 것을 방지
        for d in SCAN_DIRS:
            self.assertTrue((PLUGIN_ROOT / d).is_dir(), d)

    def test_no_broken_links(self):
        broken = find_broken_links()
        if broken:
            lines = [
                f"  {loc} → {target} (해석: {resolved})"
                for loc, target, resolved in broken
            ]
            self.fail(
                "깨진 링크 %d건:\n%s" % (len(broken), "\n".join(lines))
            )


if __name__ == "__main__":
    unittest.main()
