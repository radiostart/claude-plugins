"""preamble.md § 스킬별 P 절차 적용표 ↔ skills/ 폴더 집합 일치 게이트.

`preamble.md` 는 그 표를 "P 절차 적용 대상의 **유일 SSOT**" 로 선언하고, 각
SKILL.md 는 절차 본문을 복제하지 않고 참조만 하도록 규정한다. 그런데 표에서
빠진 스킬은 그 규정의 사각지대가 된다 — 참조할 행이 없으니 자기 문구로 절차를
인라인 복제하게 되고, 그러면 preamble 이 애초에 막으려던 이중 관리 드리프트가
그대로 재발한다 (표 밖 스킬이 P1 상당 절차를 자체 문구로 복제하는 형태로
실제 발생하는 경로다).

사람 눈으로는 "표에 없는 스킬" 이 보이지 않는다 — 있는 행을 읽지 없는 행을
찾지는 않기 때문이다. 그래서 기계로 막는다.

의도적으로 P 절차를 하나도 쓰지 않는 스킬 (`pilot-init` — workspace 를 처음
만드는 스킬이라 P1 조차 성립하지 않는다) 도 **행 자체는 존재해야 한다**.
빈 행은 "검토했고 해당 없음" 이라는 기록이고, 행 부재는 "아무도 안 봤다" 다.

python 3.9 호환·stdlib 전용 유지 (다른 tests/tools/*.py 와 동일 컨트랙트).
"""

import re
import unittest
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
SKILLS_DIR = PLUGIN_ROOT / "skills"
PREAMBLE = PLUGIN_ROOT / "skills" / "context" / "shared" / "preamble.md"

# skills/ 하위지만 스킬이 아닌 폴더 (SKILL.md 미보유 공유 컨텍스트).
NON_SKILL_DIRS = {"context"}


def skill_names(skills_dir):
    """SKILL.md 를 가진 폴더 이름 집합."""
    return {
        p.name
        for p in sorted(skills_dir.iterdir())
        if p.is_dir() and p.name not in NON_SKILL_DIRS and (p / "SKILL.md").is_file()
    }


def table_rows(preamble_text):
    """적용표의 첫 컬럼 (백틱으로 감싼 스킬명) 집합."""
    names = set()
    in_table = False
    for line in preamble_text.splitlines():
        s = line.strip()
        if s.startswith("| 스킬"):
            in_table = True
            continue
        if in_table:
            if not s.startswith("|"):
                break
            first = s.strip("|").split("|")[0].strip()
            m = re.fullmatch(r"`([^`]+)`", first)
            if m:
                names.add(m.group(1))
    return names


class PreambleCoverage(unittest.TestCase):
    def test_every_skill_has_a_row(self):
        skills = skill_names(SKILLS_DIR)
        rows = table_rows(PREAMBLE.read_text(encoding="utf-8"))

        missing = sorted(skills - rows)
        self.assertEqual(
            missing, [],
            "P 절차 적용표에 행이 없는 스킬: {}. preamble.md 의 표에 행을 추가하세요 "
            "— P 절차를 하나도 쓰지 않더라도 빈 행 + 각주로 그 사실을 기록합니다 "
            "(행 부재는 검토 누락과 구분되지 않습니다).".format(", ".join(missing)),
        )

    def test_no_stale_rows(self):
        skills = skill_names(SKILLS_DIR)
        rows = table_rows(PREAMBLE.read_text(encoding="utf-8"))

        stale = sorted(rows - skills)
        self.assertEqual(
            stale, [],
            "적용표에 있으나 실재하지 않는 스킬: {}. 스킬 rename·삭제 시 표도 "
            "함께 갱신하세요.".format(", ".join(stale)),
        )


if __name__ == "__main__":
    unittest.main()
