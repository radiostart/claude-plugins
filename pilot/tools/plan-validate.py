#!/usr/bin/env python3
"""
plan-validate — Planner 가 작성한 `features/NN-{slug}.plan.md` 의 형식 계약을
모드별로 검증한다.

스펙: skills/context/lifecycle/plan-schema.md
Open Questions 게이트 스펙: skills/context/shared/open-questions.md § 판정 매트릭스

작동 흐름:
  1. plan 파일 Read
  2. 최상단 H2(`## 구현 계획: ...`) 존재 확인
  3. 모드별 필수 H3 섹션 존재 확인
  4. tdd/characterize: `### 스텝 목록[...]` 안의 각 스텝 항목별 필수 라벨 확인
  5. Open Questions 게이트 — plan 경로에서 feature 파일을 유도해
     미해결 OQ 카테고리별 plan 처리 마커(`추정 구현`/`범위 제외`) 존재 검증.
     feature 파일·OQ 섹션 부재 시 skip (oq.checked=false)
  6. 결과를 JSON 으로 stdout 출력 + 누락 요약을 stderr (exit 1 인 경우)

Usage:
    python3 plan-validate.py <plan_file> --mode {standard|tdd|characterize}

Exit:
    0 = valid
    1 = invalid (검증 실패)
    2 = 사용 오류 (파일 없음 / 인자 오류 등)
"""

import argparse
import json
import re
import sys
from pathlib import Path

MODES = ("standard", "tdd", "characterize")

# 분량 가드 (WARN, 비차단) — 스펙: skills/context/lifecycle/plan-schema.md § 분량 가드
# 근거: 정상 plan 20~27k자. 초과분은 대부분 회차 이력 잔재
# (실사례: 이력 누적 plan 135k자 ≈ 토큰 65k — 후속 에이전트가 매 라운드 전문 재로딩).
SIZE_WARN_CHARS = 30_000
LINE_WARN_CHARS = 1_500  # Read 툴 라인 절단(2,000자) 안전 마진


def size_warnings(text: str) -> list[str]:
    """분량 가드 — 임계 초과를 WARN 메시지 리스트로 반환 (빈 리스트 = 통과).

    exit code 에 영향을 주지 않는다. planner 는 WARN 시 회차 이력 잔재
    (`N차 갱신` 헤더·`1회차 대비 정정` 주석·기각 사유 장문)를 정리하고
    최신 확정 상태만 남긴다 — 이력 SSOT 는 critic 합의 표.
    """
    warnings: list[str] = []
    total = len(text)
    if total > SIZE_WARN_CHARS:
        warnings.append(
            f"plan 분량 {total:,}자 — 상한 {SIZE_WARN_CHARS:,}자 초과. "
            "회차 이력 잔재를 정리하고 최신 확정 상태만 남길 것 "
            "(스펙: plan-schema.md § 분량 가드)"
        )
    longest = max((len(ln) for ln in text.splitlines()), default=0)
    if longest > LINE_WARN_CHARS:
        warnings.append(
            f"최장 라인 {longest:,}자 — {LINE_WARN_CHARS:,}자 초과. "
            "Read 툴 라인 절단(2,000자) 위험 — 표·문단 분리 필요"
        )
    return warnings


# 모드별 필수 H3 섹션 — doc-level 형식은 느슨하게, step section 만 강제
# (실 운영 plan 들이 자유로운 doc 구성을 사용 — `포착 대상 요약`·인라인 경계 노트 등)
REQUIRED_SECTIONS = {
    "standard": [],
    "tdd": ["### 스텝 목록"],
    "characterize": ["### 스텝 목록 (Characterization Contract)"],
}

# 스텝 단위 필수 라벨 (모드별) — 검증의 핵심 가치.
# 각 항목은 동의어 alternatives 리스트 — 그룹 내 라벨 중 하나라도 등장하면 통과.
# 예: 운영 plan 들은 `테스트 대상:` 보다 `spec 대상:` 을 더 자주 사용.
STEP_REQUIRED_LABELS = {
    "tdd": [
        ["테스트 대상:", "spec 대상:"],
        ["검증할 행동:"],
        ["기대 실패 유형:"],
    ],
    "characterize": [
        ["테스트 대상:", "spec 대상:"],
        ["입력:"],
        ["현재 출력:"],
        ["관찰된 사이드 이펙트:"],
    ],
}

# 스텝 목록 섹션 헤딩 (모드별)
STEP_SECTION_HEADING = {
    "tdd": "### 스텝 목록",
    "characterize": "### 스텝 목록 (Characterization Contract)",
}

ANY_HEADING = re.compile(r"^#{1,6}\s+\S")
H3_LINE = re.compile(r"^###\s+.+$")
STEP_HEADER_LINE = re.compile(r"^\d+\.\s+\*\*\[스텝\s+\d+\]")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def has_plan_title(text: str) -> bool:
    """Plan 파일에 최소 1개 마크다운 제목 라인이 있는지 확인."""
    for line in text.splitlines():
        if ANY_HEADING.match(line):
            return True
    return False


def find_missing_sections(text: str, mode: str) -> list[str]:
    required = REQUIRED_SECTIONS[mode]
    lines = text.splitlines()
    # tdd 의 "### 스텝 목록" 은 characterize 의 "### 스텝 목록 (Characterization Contract)" 와
    # prefix 가 동일하므로, 정확 일치 매칭 사용. tdd 모드에서는 정확히 "### 스텝 목록" 라인을 찾는다.
    missing = []
    for sec in required:
        if not any(line.strip() == sec for line in lines):
            missing.append(sec)
    return missing


def extract_section_body(text: str, heading: str) -> str | None:
    """주어진 H3 헤딩 라인 다음부터 다음 H2/H3 직전까지의 본문을 반환. 없으면 None."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == heading:
            start = i + 1
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start, len(lines)):
        s = lines[j].strip()
        if s.startswith("## ") or H3_LINE.match(s):
            end = j
            break
    return "\n".join(lines[start:end])


def split_steps(section_body: str) -> list[tuple[int, str]]:
    """`1. **[스텝 N]** ...` 형식 항목들을 (스텝번호, 본문) 리스트로 분할."""
    if not section_body:
        return []
    lines = section_body.splitlines()
    steps: list[tuple[int, list[str]]] = []
    current: list[str] | None = None
    current_num: int | None = None
    for line in lines:
        m = re.match(r"^(\d+)\.\s+\*\*\[스텝\s+(\d+)\]", line)
        if m:
            if current is not None and current_num is not None:
                steps.append((current_num, "\n".join(current)))
            current_num = int(m.group(2))
            current = [line]
        else:
            if current is not None:
                current.append(line)
    if current is not None and current_num is not None:
        steps.append((current_num, "\n".join(current)))
    return [(num, body) for num, body in steps]


def is_meta_step(step_body: str) -> bool:
    """
    `재포착 생략` / `기록만 남김` 등 의도적 빈 스텝(Planner 가 spec 작성을
    명시적으로 건너뛰는 경우) 은 라벨 검증을 면제한다.
    """
    markers = (
        "재포착 생략",
        "기록만 남김",
        "**신규 파일 없음**",
        "재포착하지 않음",
    )
    return any(m in step_body for m in markers)


def _label_present(step_body: str, label: str) -> bool:
    """
    라벨 매칭 — 라인 시작(들여쓰기·`-`/`*` 허용) 다음에 라벨 단어가 등장하면 인정.
    라벨 끝 콜론은 같은 라인에 있으면 OK (`입력:` / `입력 (3축 조합):` 모두 매칭).
    label 인자는 끝에 `:` 포함된 형태 (`테스트 대상:`).
    """
    # 콜론 앞 단어만 추출
    word = label.rstrip(":").strip()
    # 라인 시작 prefix: 0~3 공백, 선택적 `-`/`*`/`>`, 공백
    pattern = re.compile(
        rf"^\s{{0,4}}[->*]?\s*{re.escape(word)}\b[^\n:]*:",
        re.MULTILINE,
    )
    return bool(pattern.search(step_body))


def step_missing_labels(
    step_body: str, required_labels: list[list[str]]
) -> list[str]:
    """
    각 필수 라벨 그룹에서 alternatives 중 하나라도 등장하면 통과.
    메타 스텝(`재포착 생략` 등) 은 검증 면제.
    누락된 그룹의 *대표 라벨* (첫 번째 alternative) 을 반환.
    """
    if is_meta_step(step_body):
        return []
    missing = []
    for group in required_labels:
        if not any(_label_present(step_body, alt) for alt in group):
            missing.append(group[0])
    return missing


# ---------------------------------------------------------------------------
# Open Questions 게이트 — 스펙: skills/context/shared/open-questions.md § 판정 매트릭스
# ---------------------------------------------------------------------------

# feature 파일 `## Open Questions` 파서 — doctor 슬림화(#20)로 공유 파서 모듈이
# 없어졌으므로 본 도구가 자체 보유한다.
OQ_CATEGORY_KEYS = ["(a)", "(b)", "(c)", "(d)"]
_OQ_H3_RE = re.compile(r"^### (\([abcd]\)) ", re.M)
_OQ_H2_RE = re.compile(r"^## Open Questions\s*$", re.M)
_OQ_NEXT_H2_RE = re.compile(r"^## ", re.M)
_OQ_ITEM_OPEN_RE = re.compile(r"^- \[ \] (.+)$")
_OQ_ITEM_RESOLVED_RE = re.compile(r"^- \[x\] (.+)$", re.IGNORECASE)

PLAN_SUFFIX_RE = re.compile(r"^(?P<stem>.+)\.plan(?:\.r\d+)?\.md$")
OQ_MARKER_ASSUME = "추정 구현"
OQ_MARKER_EXCLUDE_RE = re.compile(r"범위(?:에서)?\s*제외")
OQ_LEGACY_BLANKET = "산출물 부재 상태에서 추정 구현"


def _fenced_mask(lines: list[str]) -> list[bool]:
    """각 라인이 fenced 코드블록(``` 또는 ~~~) 내부면 True (펜스 구분선 포함).

    OQ 마커 매칭이 코드블록 안의 예시 라인을 진짜 처리 마커로 오인하는 것을 막는다."""
    mask = [False] * len(lines)
    in_code = False
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            mask[i] = True  # 펜스 구분선 자체도 내부로 취급
            in_code = not in_code
            continue
        mask[i] = in_code
    return mask


def _extract_oq_section(text: str) -> str | None:
    """`## Open Questions` 섹션 본문만 추출. 없으면 None."""
    m = _OQ_H2_RE.search(text)
    if not m:
        return None
    start = m.end()
    rest = text[start:]
    next_h2 = _OQ_NEXT_H2_RE.search(rest)
    return rest[: next_h2.start()] if next_h2 else rest


def _parse_oq_categories(section: str) -> dict:
    """OQ 섹션 본문 → 카테고리별 open/resolved 항목 리스트.

    Returns:
        {"(a)": {"open": [str, ...], "resolved": [str, ...]}, "(b)": {...}, ...}
    누락된 카테고리는 빈 list 로 채움.
    """
    out = {k: {"open": [], "resolved": []} for k in OQ_CATEGORY_KEYS}
    current: str | None = None
    for raw in section.splitlines():
        line = raw.rstrip()
        h3 = _OQ_H3_RE.match(line)
        if h3:
            current = h3.group(1)
            continue
        if current is None:
            continue
        m_open = _OQ_ITEM_OPEN_RE.match(line)
        if m_open:
            out[current]["open"].append(m_open.group(1).strip())
            continue
        m_done = _OQ_ITEM_RESOLVED_RE.match(line)
        if m_done:
            out[current]["resolved"].append(m_done.group(1).strip())
    return out


def derive_feature_path(plan_path: Path) -> Path | None:
    """plan 경로 → 대응 feature 파일 경로. plan 명명 규약 외 파일이면 None.

    `NN-{slug}.plan.md` → `NN-{slug}.md` (`.plan.r{N}.md` 도 동일 stem — 회차 plan 대비).
    """
    m_ = PLAN_SUFFIX_RE.match(plan_path.name)
    if not m_:
        return None
    return plan_path.with_name(m_.group("stem") + ".md")


def _empty_oq_result() -> dict:
    return {"checked": False, "feature_file": None, "unresolved": {}, "errors": []}


def check_open_questions(plan_text: str, feature_path: Path | None) -> dict:
    """미해결 OQ ↔ plan 처리 마커 대조. 스펙: open-questions.md § 마커 어휘.

    feature 파일·OQ 섹션 부재 시 checked=False (skip — 사이클 밖 plan 호환).
    미해결 카테고리마다 plan 본문(fenced 코드블록 제외)에 카테고리 키 +
    마커(`추정 구현`/`범위 제외`) 동일 라인 등장을 요구한다. 포괄 문구
    "산출물 부재 상태에서 추정 구현" 은 (d) 외 카테고리를 커버(하위 호환).
    (d) 비즈니스 결정 영역은 `범위 제외` 키 동반만 인정 — 임의 결정 금지.
    """
    out = _empty_oq_result()
    if feature_path is None or not feature_path.is_file():
        return out
    out["feature_file"] = str(feature_path)
    try:
        feature_text = feature_path.read_text(encoding="utf-8")
    except Exception:
        return out
    section = _extract_oq_section(feature_text)
    if section is None:
        return out

    out["checked"] = True
    parsed = _parse_oq_categories(section)
    unresolved = {
        cat: parsed[cat]["open"]
        for cat in OQ_CATEGORY_KEYS
        if parsed[cat]["open"]
    }
    out["unresolved"] = unresolved
    if not unresolved:
        return out

    lines = plan_text.splitlines()
    mask = _fenced_mask(lines)
    body_lines = [ln for i, ln in enumerate(lines) if not mask[i]]
    has_blanket = any(OQ_LEGACY_BLANKET in ln for ln in body_lines)

    def keyed_marker(cat: str, allow_assume: bool) -> bool:
        for ln in body_lines:
            if cat not in ln:
                continue
            if OQ_MARKER_EXCLUDE_RE.search(ln):
                return True
            if allow_assume and OQ_MARKER_ASSUME in ln:
                return True
        return False

    for cat, items in unresolved.items():
        if cat == "(d)":
            if not keyed_marker(cat, allow_assume=False):
                out["errors"].append(
                    f"(d) 미해결 {len(items)}건 — 사용자 결정 필요. "
                    "plan 진행은 `(d) ...: 범위 제외` 마커(사용자 결정 보류 "
                    "명시)로만 가능 (스펙: open-questions.md § 판정 매트릭스)"
                )
        else:
            if not keyed_marker(cat, allow_assume=True) and not has_blanket:
                out["errors"].append(
                    f"{cat} 미해결 {len(items)}건 — plan 에 처리 마커 없음. "
                    f"`{cat} ...: 추정 구현` 또는 `{cat} ...: 범위 제외` "
                    "라인 필요 (스펙: open-questions.md § 마커 어휘)"
                )
    return out


def validate(plan_path: Path, mode: str) -> dict:
    if mode not in MODES:
        return {
            "valid": False,
            "mode": mode,
            "errors": [f"unknown mode: {mode}. Allowed: {', '.join(MODES)}"],
        }

    if not plan_path.exists():
        return {
            "valid": False,
            "mode": mode,
            "errors": [f"file not found: {plan_path}"],
        }

    text = read_text(plan_path)

    result: dict = {
        "valid": True,
        "mode": mode,
        "missing_sections": [],
        "step_errors": [],
        "errors": [],
        "warnings": [],
        "oq": _empty_oq_result(),
    }

    if not text.strip():
        result["valid"] = False
        result["errors"].append("file is empty")
        return result

    result["warnings"] = size_warnings(text)

    if not has_plan_title(text):
        result["valid"] = False
        result["errors"].append("missing markdown heading (any of '#'..'######')")

    missing = find_missing_sections(text, mode)
    if missing:
        result["valid"] = False
        result["missing_sections"] = missing

    if mode in ("tdd", "characterize"):
        heading = STEP_SECTION_HEADING[mode]
        body = extract_section_body(text, heading)
        if body is None:
            # 이미 missing_sections 에 잡혔을 것이므로 추가 진단만 생략
            pass
        else:
            steps = split_steps(body)
            if not steps:
                result["valid"] = False
                result["errors"].append(
                    f"'{heading}' contains no step items "
                    "(expected '1. **[스텝 1]** ...')"
                )
            else:
                required_labels = STEP_REQUIRED_LABELS[mode]
                for num, sbody in steps:
                    miss = step_missing_labels(sbody, required_labels)
                    if miss:
                        result["valid"] = False
                        result["step_errors"].append(
                            {"step": num, "missing_fields": miss}
                        )

    oq = check_open_questions(text, derive_feature_path(plan_path))
    result["oq"] = oq
    if oq["errors"]:
        result["valid"] = False

    return result


def format_human_summary(result: dict, plan_path: Path) -> str:
    lines = [f"plan-validate: {plan_path} — mode={result['mode']} → INVALID"]
    for err in result.get("errors", []):
        lines.append(f"  - error: {err}")
    for sec in result.get("missing_sections", []):
        lines.append(f"  - missing section: {sec}")
    for serr in result.get("step_errors", []):
        fields = ", ".join(serr["missing_fields"])
        lines.append(f"  - step {serr['step']} missing: {fields}")
    for oerr in result.get("oq", {}).get("errors", []):
        lines.append(f"  - open questions: {oerr}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate plan file format.")
    ap.add_argument("plan_file", help="path to features/NN-{slug}.plan.md")
    ap.add_argument(
        "--mode",
        required=True,
        choices=MODES,
        help="plan mode (resolved from .agent-state.yml by caller)",
    )
    args = ap.parse_args()

    path = Path(args.plan_file)
    result = validate(path, args.mode)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    for warn in result.get("warnings", []):
        print(f"[WARN] {warn}", file=sys.stderr)

    if not result["valid"]:
        print(format_human_summary(result, path), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
