"""skills/*/SKILL.md description 예산·카나리 게이트.

스킬 목록 (name+description) 은 전 세션 상주 컨텍스트다. 하니스는 목록에
chars 기반 공유 예산을 두고 초과분을 무경고 강등하므로 (아래 "예산 메커니즘"),
description 비대는 조용히 라우팅 퇴화로 이어진다. 본 게이트는 두 드리프트를
기계 차단한다:

1. **byte 예산** — per-skill ≤ 650B, 전체 합계 ≤ 7,200B (UTF-8, 값 기준).
   예산 상향은 사유를 명기한 PR 로만 (조용한 비대 → 명시적 결정).
2. **anti-trigger 카나리** — autopilot·qa 의 오발동 방지 문구는 "모델 자발
   발동 차단" 목적으로 **문두에 의도 배치**된 것. 목록 잘림 시 앞부분만
   생존하므로 위치가 곧 안전장치다. 압축·리라이트가 이 문구를 지우거나
   뒤로 미는 편집을 차단한다.

description 계약 (5요소): 정체 1문장 · 트리거 (사용자 실발화 표면) ·
anti-trigger (문두 고정, 본문 이동 금지 — 본문은 호출 후에만 로드) ·
인접 스킬 구분 · 본문 위임 포인터. 그 외 운용 상세는 본문으로.

측정 정의 (canonical): frontmatter `description` 값 — 블록 스칼라 지시자
(`>-` 등) 는 제외, 연속행은 strip 후 단일 공백 join, UTF-8 bytes.

예산 메커니즘 (버전 종속 — 커뮤니티 역공학 기반, 공식 문서 아님): 하니스
예산은 토큰이 아니라 **chars 단위 전역 공유**다 — contextWindow tokens × 4
× skillListingBudgetFraction (기본 0.01) ≈ 200k 세션 8,000 chars 를 모든
플러그인·내장 스킬이 나눠 쓰고, 초과 시 fits→priority→truncate→names-only
로 무경고 강등된다 (per-skill 별도 상한 1,536 chars). 실측 1.83 B/char
(한글 3B=1char) 로 합계 7,200B ≈ 3,930 chars ≈ 기본 공유 예산의 ~49% —
게이트 상수는 이 몫 안에서 유지한다. 주의 — 본 게이트는 자체 비대만
막는다: 타 플러그인과의 합산 초과 (공유 예산 크라우딩) 는 게이트 밖이며
증상은 스킬 무경고 미발동이다.

주의: python 3.9 호환·stdlib 전용 유지 (다른 tests/tools/*.py 와 동일 컨트랙트).
"""

import tempfile
import unittest
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
SKILLS_DIR = PLUGIN_ROOT / "skills"

PER_SKILL_MAX = 650
TOTAL_MAX = 7200

# anti-trigger 카나리 — 값: (문두 prefix, 필수 부분 문자열들).
# 문구를 정당하게 리라이트할 때는 본 표를 함께 갱신한다 (2파일 결합은 의도 —
# 안전 조항 변경을 리뷰 가시권으로 끌어내는 장치).
CANARIES = {
    "qa": ("사용자가", ["명시적으로 호출했을 때만", "발동하지 않는다"]),
    "autopilot": ("사용자가", ["명시 요청했을 때만", "자발 발동하지 않는다"]),
}

BLOCK_SCALAR_INDICATORS = (">-", ">", ">+", "|", "|-", "|+")


def parse_description(text):
    """SKILL.md 전문에서 frontmatter description 값을 canonical 규칙으로 추출.

    반환: 값 문자열 (없으면 None). yaml 미사용 — 측정 정의 자체가 본 파서다.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    parts = None
    for i in range(1, len(lines)):
        line = lines[i]
        if line.strip() == "---":
            break
        if line.startswith("description:"):
            head = line[len("description:"):].strip()
            parts = [] if head in BLOCK_SCALAR_INDICATORS else ([head] if head else [])
            j = i + 1
            while j < len(lines) and (lines[j].startswith("  ") or lines[j].startswith("\t")):
                stripped = lines[j].strip()
                if stripped == "---":
                    break
                parts.append(stripped)
                j += 1
            break
    if parts is None:
        return None
    return " ".join(parts)


def check_skills_dir(skills_dir):
    """skills_dir 하위 전 스킬 검사. 반환: 위반 메시지 리스트 (통과 시 빈 리스트)."""
    violations = []
    sized = []
    skill_files = sorted(Path(skills_dir).glob("*/SKILL.md"))
    if not skill_files:
        return ["skills 디렉터리에 SKILL.md 가 없음: %s" % skills_dir]
    for f in skill_files:
        name = f.parent.name
        desc = parse_description(f.read_text(encoding="utf-8"))
        if not desc:
            violations.append("%s: description 부재 또는 빈 값" % name)
            continue
        nbytes = len(desc.encode("utf-8"))
        sized.append((nbytes, name))
        if nbytes > PER_SKILL_MAX:
            violations.append(
                "%s: description %dB > 예산 %dB — 운용 상세를 본문으로 위임할 것"
                % (name, nbytes, PER_SKILL_MAX)
            )
        if name in CANARIES:
            prefix, needles = CANARIES[name]
            if not desc.startswith(prefix):
                violations.append(
                    "%s: anti-trigger 가 문두가 아님 (문두 고정 배치 — "
                    "목록 잘림 시 앞부분만 생존)" % name
                )
            for needle in needles:
                if needle not in desc:
                    violations.append(
                        "%s: anti-trigger 카나리 문구 소실 — %r" % (name, needle)
                    )
    total = sum(b for b, _ in sized)
    if total > TOTAL_MAX:
        top = ", ".join("%s=%dB" % (n, b) for b, n in sorted(sized, reverse=True)[:3])
        violations.append(
            "합계 %dB > 예산 %dB — 최대 항목: %s. 기존 항목 압축 또는 사유 명기 "
            "예산 상향 PR 필요" % (total, TOTAL_MAX, top)
        )
    return violations


# ---------------------------------------------------------------------------
# fixture 기반 자기검증 — 실파일 변조 없이 red 경로 재현 (재현 가능·원복 불요)
# ---------------------------------------------------------------------------

def _fixture_tree(tmpdir, skills):
    root = Path(tmpdir) / "skills"
    for name, desc_block in skills.items():
        d = root / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            "---\nname: %s\n%s---\n\n본문.\n" % (name, desc_block), encoding="utf-8"
        )
    return root


class ParserCases(unittest.TestCase):
    def test_folded_scalar_joined_with_single_space(self):
        text = "---\nname: x\ndescription: >-\n  줄 하나\n  줄 둘\n---\n"
        self.assertEqual(parse_description(text), "줄 하나 줄 둘")

    def test_plain_scalar_multiline(self):
        text = "---\nname: x\ndescription: 첫 조각\n  이어짐\n---\n"
        self.assertEqual(parse_description(text), "첫 조각 이어짐")

    def test_missing_description_returns_none(self):
        self.assertIsNone(parse_description("---\nname: x\n---\n"))


class BudgetGuard(unittest.TestCase):
    def test_over_per_skill_budget_fails(self):
        long_desc = "description: >-\n  %s\n" % ("가" * (PER_SKILL_MAX // 3 + 10))
        with tempfile.TemporaryDirectory() as td:
            root = _fixture_tree(td, {"fat": long_desc})
            violations = check_skills_dir(root)
        self.assertTrue(any("fat" in v and "예산" in v for v in violations))

    def test_empty_description_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = _fixture_tree(td, {"blank": "description: >-\n"})
            violations = check_skills_dir(root)
        self.assertTrue(any("blank" in v and "부재" in v for v in violations))

    def test_lean_skill_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _fixture_tree(td, {"lean": "description: 짧고 명확한 설명.\n"})
            self.assertEqual(check_skills_dir(root), [])


class CanaryGuard(unittest.TestCase):
    def test_demoted_anti_trigger_fails(self):
        # 문구는 있으나 문두가 아님 — 압축 리라이트가 범하기 쉬운 편집을 재현
        desc = (
            "description: >-\n"
            "  Jira QA 결함 처리 모드 진입. 사용자가 명시적으로 호출했을 때만\n"
            "  사용한다 — 발동하지 않는다.\n"
        )
        with tempfile.TemporaryDirectory() as td:
            root = _fixture_tree(td, {"qa": desc})
            violations = check_skills_dir(root)
        self.assertTrue(any("문두" in v for v in violations))

    def test_deleted_canary_phrase_fails(self):
        desc = "description: >-\n  사용자가 부르면 자동 순차 진행한다.\n"
        with tempfile.TemporaryDirectory() as td:
            root = _fixture_tree(td, {"autopilot": desc})
            violations = check_skills_dir(root)
        self.assertTrue(any("카나리" in v for v in violations))


class RealRepoGate(unittest.TestCase):
    """실제 skills/ 전수 — 본 게이트의 주 목적."""

    def test_repo_skills_within_budget_and_canaries(self):
        violations = check_skills_dir(SKILLS_DIR)
        self.assertEqual(violations, [], "\n".join(violations))


if __name__ == "__main__":
    unittest.main(verbosity=1)
