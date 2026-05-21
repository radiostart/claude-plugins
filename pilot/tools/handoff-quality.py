#!/usr/bin/env python3
"""
pilot handoff-quality — planner ↔ generator 인계 콘텐츠 품질 측정 (Phase β).

plan-validate 가 검증하지 않는 영역 — **콘텐츠 품질** 정량 측정:

- **변경 파일 구체성** (`### 변경 파일`): 각 항목이 실제 파일 경로 vs 모호 표현
- **변경 사유 명시도**: 각 항목에 "왜" 가 있는가
- **Red 계약 구체성** (TDD plan): 라벨 값이 placeholder vs 구체 텍스트

Usage:
    # 단일 plan 파일
    python3 tools/handoff-quality.py path/to/03-foo.plan.md
    python3 tools/handoff-quality.py path/to/03-foo.plan.md --mode tdd

    # 디렉터리 일괄 (features/*.plan.md 모두)
    python3 tools/handoff-quality.py workspace/projects/proj1/features/

    # JSON
    python3 tools/handoff-quality.py path/to/plan.md --json

Exit:
    0 — 평가 정상 종료 (점수 무관)
    1 — 입력 오류 (파일 없음 등)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

# plan-validate 의 helper 재사용 — 동일 plan 파서 로직 공유
_TOOLS_DIR = Path(__file__).resolve().parent
_PLAN_VAL_PATH = _TOOLS_DIR / "plan-validate.py"
_spec = importlib.util.spec_from_file_location("plan_validate_mod", _PLAN_VAL_PATH)
_pv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pv)

# ---------------------------------------------------------------------------
# 변경 파일 구체성 평가
# ---------------------------------------------------------------------------

# placeholder 패턴 — 값이 이걸 포함하면 vague 로 분류.
# 룰: "미정의" / "미정확" 같은 정상 단어가 false positive 되지 않도록
# 명시적 placeholder 표현만 매칭 (괄호·접미사 포함 또는 완결된 phrase).
PLACEHOLDER_PATTERNS = [
    r"\bTBD\b",
    r"\bTODO\b",
    r"\(미정\)",
    r"_\(미정\)_",
    r"\(추후 결정\)",
    r"추후 결정한다",
    r"추후 결정\b",
    r"추후 결정$",
    r"추후 정한다",
    r"추후 보강",
    r"별도 협의",
    r"별도 정의",
    r"placeholder",
    r"Generator 실행 예정",
    r"_\(추가 예정\)_",
    r"_\(미작성\)_",
]
PLACEHOLDER_RE = re.compile("|".join(PLACEHOLDER_PATTERNS), re.IGNORECASE)

# 변경 파일 항목 — 형식: `- [ ] path/to/file.ext — reason` 또는 `- [x]` 또는 단순 `- path`
CHANGE_ITEM_RE = re.compile(
    r"^\s{0,4}-\s*(?:\[[ x]\]\s+)?(.+?)(?:\s+(?:—|-)\s+(.+))?$"
)
PATH_WITH_EXT_RE = re.compile(r"[\w./-]+\.[a-zA-Z0-9]{1,8}(?::\d+)?$")
DIR_PATH_RE = re.compile(r"[\w./-]+/$")
PATH_LIKE_RE = re.compile(r"[\w][\w./-]+/[\w./-]+")  # slash 포함 일반 path


def classify_change_item(raw: str) -> str:
    """change item 의 첫 번째 토큰을 분류.

    Returns:
        "concrete" — 정확한 파일 경로 (확장자 포함 또는 명확한 path:line)
        "directory" — 디렉터리 path (slash 끝)
        "vague" — 그 외 (placeholder, 자유 산문, 키워드만)
    """
    text = raw.strip().rstrip(",").strip()
    if not text:
        return "vague"
    # backtick code block 안 vs 밖 모두 체크
    if "`" in text:
        m = re.search(r"`([^`]+)`", text)
        if m:
            text = m.group(1)
    # placeholder 우선
    if PLACEHOLDER_RE.search(text):
        return "vague"
    # 명확한 파일 경로 (확장자 + slash 또는 path-like)
    if PATH_WITH_EXT_RE.search(text) and "/" in text:
        return "concrete"
    if DIR_PATH_RE.match(text.split()[0]):
        return "directory"
    # 단일 토큰이지만 확장자 없음 + slash 있음 → directory 추정
    first_token = text.split()[0]
    if "/" in first_token and "." not in first_token.split("/")[-1]:
        return "directory"
    return "vague"


def parse_change_files(plan_text: str) -> list[dict]:
    """`### 변경 파일` 섹션 파싱.

    Returns:
        [{"raw": str, "path": str, "reason": str|None, "type": str, "has_reason": bool}, ...]
    """
    body = _pv.extract_section_body(plan_text, "### 변경 파일")
    if body is None:
        return []
    items: list[dict] = []
    for line in body.splitlines():
        if not line.strip():
            continue
        m = CHANGE_ITEM_RE.match(line)
        if not m:
            continue
        path_part = (m.group(1) or "").strip()
        reason_part = (m.group(2) or "").strip() or None
        if not path_part:
            continue
        # 헤더성 라인 제외 (`- [예시]` 같은 안내 라인)
        if path_part.startswith("[") and "예시" in path_part:
            continue
        items.append({
            "raw": line.strip(),
            "path": path_part,
            "reason": reason_part,
            "type": classify_change_item(path_part),
            "has_reason": reason_part is not None and bool(reason_part.strip()),
        })
    return items


def evaluate_change_files(items: list[dict]) -> dict:
    total = len(items)
    if total == 0:
        return {
            "total": 0,
            "concrete": 0,
            "directory": 0,
            "vague": 0,
            "with_reason": 0,
            "specificity_score": None,
            "reason_coverage": None,
        }
    concrete = sum(1 for i in items if i["type"] == "concrete")
    directory = sum(1 for i in items if i["type"] == "directory")
    vague = sum(1 for i in items if i["type"] == "vague")
    with_reason = sum(1 for i in items if i["has_reason"])
    return {
        "total": total,
        "concrete": concrete,
        "directory": directory,
        "vague": vague,
        "with_reason": with_reason,
        "specificity_score": round(concrete / total, 3),
        "reason_coverage": round(with_reason / total, 3),
    }


# ---------------------------------------------------------------------------
# Red 계약 구체성 평가 (TDD 모드)
# ---------------------------------------------------------------------------

# 각 스텝에서 검증할 라벨 (label 의 첫 alt 사용)
TDD_STEP_LABELS = [
    ("테스트 대상", ["테스트 대상", "spec 대상"]),
    ("검증할 행동", ["검증할 행동"]),
    ("기대 실패 유형", ["기대 실패 유형"]),
]


def extract_label_value(step_body: str, label: str) -> str | None:
    """스텝 본문에서 `label: ...` 의 value 추출. 없으면 None."""
    word = label.rstrip(":").strip()
    pattern = re.compile(
        rf"^\s{{0,4}}[->*]?\s*{re.escape(word)}\b[^\n:]*:\s*(.+?)$",
        re.MULTILINE,
    )
    m = pattern.search(step_body)
    if not m:
        return None
    return m.group(1).strip()


def is_value_concrete(value: str | None) -> bool:
    if not value:
        return False
    text = value.strip()
    if not text:
        return False
    if PLACEHOLDER_RE.search(text):
        return False
    # 너무 짧은 값 (한 단어 미만) 도 vague 로 — 단 5 자 이상이면 통과
    if len(text) < 5:
        return False
    return True


def evaluate_red_contracts(plan_text: str) -> dict:
    """TDD plan 의 `### 스텝 목록` 안 각 스텝의 라벨 값 구체성 평가."""
    body = _pv.extract_section_body(plan_text, "### 스텝 목록")
    if body is None:
        return {
            "applicable": False,
            "reason": "no_step_section",
            "steps": 0,
        }
    steps = _pv.split_steps(body)
    if not steps:
        return {
            "applicable": False,
            "reason": "no_steps_parsed",
            "steps": 0,
        }
    total_labels = 0
    concrete_labels = 0
    per_step = []
    for step_num, step_body in steps:
        if _pv.is_meta_step(step_body):
            continue
        step_concrete = 0
        step_total = 0
        missing = []
        for label_key, alts in TDD_STEP_LABELS:
            value = None
            for alt in alts:
                value = extract_label_value(step_body, alt)
                if value is not None:
                    break
            step_total += 1
            if value is None:
                missing.append(label_key)
                continue
            if is_value_concrete(value):
                step_concrete += 1
        total_labels += step_total
        concrete_labels += step_concrete
        per_step.append({
            "step": step_num,
            "concrete": step_concrete,
            "total": step_total,
            "missing_labels": missing,
        })
    if total_labels == 0:
        return {
            "applicable": False,
            "reason": "all_meta_steps",
            "steps": len(steps),
        }
    return {
        "applicable": True,
        "steps": len(per_step),
        "total_labels": total_labels,
        "concrete_labels": concrete_labels,
        "specificity_score": round(concrete_labels / total_labels, 3),
        "per_step": per_step,
    }


# ---------------------------------------------------------------------------
# 단일 plan 평가 / 디렉터리 일괄
# ---------------------------------------------------------------------------

def evaluate_plan(path: Path, mode: str | None = None) -> dict:
    text = path.read_text(encoding="utf-8")
    items = parse_change_files(text)
    cf = evaluate_change_files(items)
    rc = evaluate_red_contracts(text) if (mode is None or mode == "tdd") else {
        "applicable": False, "reason": f"mode={mode}", "steps": 0
    }
    return {
        "path": str(path),
        "mode": mode,
        "change_files": cf,
        "red_contracts": rc,
    }


def evaluate_directory(d: Path) -> list[dict]:
    plans = sorted(d.glob("*.plan.md"))
    return [evaluate_plan(p) for p in plans]


# ---------------------------------------------------------------------------
# 출력
# ---------------------------------------------------------------------------

def render_text(reports: list[dict]) -> str:
    out = ["# Handoff Quality 측정\n"]
    if not reports:
        out.append("(plan 파일 없음)")
        return "\n".join(out) + "\n"
    out.append("| Plan | 변경파일 (concrete/dir/vague) | Specificity | Reason% | Red contracts | Red specificity |")
    out.append("|---|---|---|---|---|---|")
    for r in reports:
        cf = r["change_files"]
        rc = r["red_contracts"]
        path_label = Path(r["path"]).name
        cf_summary = f"{cf['concrete']}/{cf['directory']}/{cf['vague']} (n={cf['total']})"
        cf_spec = "—" if cf["specificity_score"] is None else f"{cf['specificity_score']:.0%}"
        cf_reason = "—" if cf["reason_coverage"] is None else f"{cf['reason_coverage']:.0%}"
        rc_summary = "n/a" if not rc.get("applicable") else f"{rc['concrete_labels']}/{rc['total_labels']}"
        rc_spec = "n/a" if not rc.get("applicable") else f"{rc['specificity_score']:.0%}"
        out.append(f"| {path_label} | {cf_summary} | {cf_spec} | {cf_reason} | {rc_summary} | {rc_spec} |")
    # 매크로 평균
    cf_scores = [r["change_files"]["specificity_score"] for r in reports if r["change_files"]["specificity_score"] is not None]
    rc_scores = [r["red_contracts"]["specificity_score"] for r in reports if r["red_contracts"].get("applicable")]
    out.append("")
    if cf_scores:
        out.append(f"**매크로 변경파일 specificity**: {sum(cf_scores)/len(cf_scores):.1%} (n={len(cf_scores)})")
    if rc_scores:
        out.append(f"**매크로 Red contract specificity**: {sum(rc_scores)/len(rc_scores):.1%} (n={len(rc_scores)})")
    return "\n".join(out) + "\n"


def render_json(reports: list[dict]) -> str:
    cf_scores = [r["change_files"]["specificity_score"] for r in reports if r["change_files"]["specificity_score"] is not None]
    rc_scores = [r["red_contracts"]["specificity_score"] for r in reports if r["red_contracts"].get("applicable")]
    summary = {
        "total_plans": len(reports),
        "macro_change_files_specificity": round(sum(cf_scores)/len(cf_scores), 3) if cf_scores else None,
        "macro_red_contract_specificity": round(sum(rc_scores)/len(rc_scores), 3) if rc_scores else None,
    }
    return json.dumps({"summary": summary, "plans": reports}, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="pilot handoff-quality")
    parser.add_argument("path", help="plan 파일 또는 features/ 디렉터리")
    parser.add_argument("--mode", choices=["standard", "tdd", "characterize"], default=None,
                        help="단일 파일 평가 시 mode 명시 (기본 자동 — TDD 가정)")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    args = parser.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"error: not found: {p}", file=sys.stderr)
        return 1

    if p.is_dir():
        reports = evaluate_directory(p)
    else:
        reports = [evaluate_plan(p, args.mode)]

    if args.json:
        print(render_json(reports))
    else:
        print(render_text(reports), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
