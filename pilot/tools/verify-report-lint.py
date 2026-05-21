#!/usr/bin/env python3
"""
pilot verify-report-lint — evaluator VERIFICATION REPORT 형식·일관성 검증.

evaluator wrapper step 7 이 출력하는 `## VERIFICATION REPORT` 블록을
결정론적으로 파싱해 다음을 검증:

- 필수 섹션 / gate 존재
- 각 gate 값 enum (pass/fail/skip/none/detected)
- status (READY|NOT_READY) ↔ gates 일관성
- mode (red_contract|characterize|standard) ↔ gate skip 매핑
- status: NOT_READY ↔ issues_to_fix 비어있지 않음
- drift: detected → issues_to_fix 에 언급

Usage:
    cat report.md | python3 tools/verify-report-lint.py
    python3 tools/verify-report-lint.py path/to/report.md
    python3 tools/verify-report-lint.py path/to/report.md --json

Exit:
    0 — 위반 없음 (PASS)
    1 — 위반 있음 (FAIL) 또는 REPORT 블록 부재
    2 — 입력 오류
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 스키마 정의
# ---------------------------------------------------------------------------

REPORT_HEADER_RE = re.compile(r"^##\s+VERIFICATION REPORT\s*$", re.M)
NEXT_H2_RE = re.compile(r"^## ", re.M)

VALID_STATUS = {"READY", "NOT_READY"}
VALID_MODE = {"red_contract", "characterize", "standard"}

# gate name → 허용 값 set
GATE_ENUMS: dict[str, set[str]] = {
    "requirements": {"pass", "fail"},
    "tdd_evidence": {"pass", "fail", "skip"},
    "capture_lockdown": {"pass", "fail", "skip"},
    "test_run": {"pass", "fail", "skip"},
    "scope": {"pass", "fail"},
    "drift": {"none", "detected"},
}
REQUIRED_GATES = list(GATE_ENUMS.keys())

# mode 별 gate 의 강제 skip 여부 (skip 이면 must be skip, none/detected 도 OK)
# True = must be skip, False = must NOT be skip
MODE_GATE_SKIP_RULES: dict[str, dict[str, bool]] = {
    "characterize": {
        "tdd_evidence": False,     # [Captured] 검증으로 pass|fail
        "capture_lockdown": False, # core gate — pass|fail
        "test_run": False,         # 실행 필수
    },
    "red_contract": {
        "tdd_evidence": False,     # Red+Green 검증
        "capture_lockdown": True,  # standard 와 동일 — skip
        "test_run": False,         # 실행 필수
    },
    "standard": {
        "tdd_evidence": True,      # skip
        "capture_lockdown": True,  # skip
        "test_run": True,          # skip (수기 시나리오로 대체)
    },
}

REQUIRED_TOP_KEYS = ["status", "feature", "mode", "gates", "metrics", "issues_to_fix", "next"]

# ---------------------------------------------------------------------------
# 파서
# ---------------------------------------------------------------------------

def extract_report_block(text: str) -> str | None:
    """`## VERIFICATION REPORT` 블록 추출. 없으면 None."""
    m = REPORT_HEADER_RE.search(text)
    if not m:
        return None
    rest = text[m.end():]
    next_h2 = NEXT_H2_RE.search(rest)
    return (rest[: next_h2.start()] if next_h2 else rest).strip()


_TOP_KEY_RE = re.compile(r"^- ([a-z_]+):\s*(.*)$")
# 비정규 top-level 키 회수용 — 불릿이 `*` 이거나 누락됐거나 공백이 다른 경우.
# 정규(_TOP_KEY_RE) 매칭 실패 시 REQUIRED_TOP_KEYS 에 한해 이 패턴으로 회수한다.
_LOOSE_TOP_KEY_RE = re.compile(r"^[-*]?[ \t]*([a-z_]+):\s*(.*)$")
_NESTED_KEY_RE = re.compile(r"^\s+- ([a-z_]+):\s*(.+?)(?:\s+—\s+(.*))?$")
_ISSUE_LINE_RE = re.compile(r"^\s+-\s+(.+)$")


def parse_report(block: str) -> dict:
    """REPORT 블록 → 구조화된 dict.

    Returns:
        {
          "status": str | None,
          "feature": str | None,
          "mode": str | None,
          "gates": {gate_name: {"value": str, "evidence": str}},
          "metrics": {metric_name: str},
          "issues_to_fix": [{"severity": str, "summary": str, "location": str}] or ["none"],
          "next": str | None,
          "_raw_top_keys": [str, ...],  # 등장 순서
        }
    """
    out: dict = {
        "status": None,
        "feature": None,
        "mode": None,
        "gates": {},
        "metrics": {},
        "issues_to_fix": [],
        "next": None,
        "_raw_top_keys": [],
        "_malformed_top_keys": [],
    }

    lines = block.splitlines()
    current_section: str | None = None  # "gates" | "metrics" | "issues_to_fix" | None

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue

        # top-level key
        if not line.startswith(" "):
            m = _TOP_KEY_RE.match(line)
            if m:
                key, rest = m.group(1), m.group(2).strip()
            else:
                # 정규 형식(`- key: value`) 이 아니지만 필수 키를 의도한 것으로
                # 보이면 (불릿 누락·`*` 사용 등) 조용히 버리지 않는다 — 키는 인식하되
                # 형식 위반으로 기록한다. 그래야 "필수 섹션 부재" 오탐이 안 난다.
                loose = _LOOSE_TOP_KEY_RE.match(line)
                if loose and loose.group(1) in REQUIRED_TOP_KEYS:
                    key, rest = loose.group(1), loose.group(2).strip()
                    out["_malformed_top_keys"].append(key)
                else:
                    continue
            out["_raw_top_keys"].append(key)
            if key in ("status", "mode"):
                # value 의 첫 토큰만 (예: "READY", "tdd | NOT_READY" 같은 enum 표기 제외)
                out[key] = rest.split()[0] if rest else None
            elif key in ("feature", "next"):
                out[key] = rest if rest else None
            elif key == "gates":
                current_section = "gates"
            elif key == "metrics":
                current_section = "metrics"
            elif key == "issues_to_fix":
                current_section = "issues_to_fix"
            continue

        # nested (들여쓰기)
        if current_section == "gates":
            m = _NESTED_KEY_RE.match(line)
            if m:
                gate_name, value, evidence = m.group(1), m.group(2).strip(), (m.group(3) or "").strip()
                # value 가 "pass | fail | skip" 같은 enum 표기면 첫 토큰 사용
                first = value.split()[0] if value else ""
                out["gates"][gate_name] = {"value": first, "evidence": evidence}
        elif current_section == "metrics":
            m = _NESTED_KEY_RE.match(line)
            if m:
                metric_name, value, _ = m.group(1), m.group(2).strip(), m.group(3)
                out["metrics"][metric_name] = value
        elif current_section == "issues_to_fix":
            m = _ISSUE_LINE_RE.match(line)
            if not m:
                continue
            content = m.group(1).strip()
            if content.lower() == "none":
                out["issues_to_fix"].append({"severity": None, "summary": "none", "location": None})
                continue
            # `[severity] summary — location` 형식
            sev_m = re.match(r"\[(\w+)\]\s+(.+?)(?:\s+—\s+(.+))?$", content)
            if sev_m:
                out["issues_to_fix"].append({
                    "severity": sev_m.group(1),
                    "summary": sev_m.group(2).strip(),
                    "location": (sev_m.group(3) or "").strip() or None,
                })
            else:
                # 형식 안 맞아도 raw 로 보존 (validate 에서 검증)
                out["issues_to_fix"].append({"severity": None, "summary": content, "location": None})

    return out


# ---------------------------------------------------------------------------
# 검증
# ---------------------------------------------------------------------------

class Violation:
    """단일 위반 사항."""
    SEVERITY_ERROR = "error"
    SEVERITY_WARN = "warn"

    def __init__(self, code: str, message: str, severity: str = SEVERITY_ERROR):
        self.code = code
        self.message = message
        self.severity = severity

    def __repr__(self) -> str:
        return f"[{self.severity}] {self.code}: {self.message}"

    def to_dict(self) -> dict:
        return {"code": self.code, "severity": self.severity, "message": self.message}


def validate(report: dict) -> list[Violation]:
    """REPORT dict → 위반 사항 리스트."""
    v: list[Violation] = []

    # 1. 필수 top-level 섹션 존재
    raw_keys = set(report.get("_raw_top_keys", []))
    for key in REQUIRED_TOP_KEYS:
        if key not in raw_keys:
            v.append(Violation("missing_section", f"필수 섹션 부재: {key}"))

    # 2. status enum
    status = report.get("status")
    if status is None:
        v.append(Violation("missing_status", "status 값 없음"))
    elif status not in VALID_STATUS:
        v.append(Violation("invalid_status", f"status 값이 enum 외: {status} (허용: {sorted(VALID_STATUS)})"))

    # 3. mode enum
    mode = report.get("mode")
    if mode is None:
        v.append(Violation("missing_mode", "mode 값 없음"))
    elif mode not in VALID_MODE:
        v.append(Violation("invalid_mode", f"mode 값이 enum 외: {mode} (허용: {sorted(VALID_MODE)})"))

    # 4. gate 항목 존재 + enum
    gates = report.get("gates", {})
    for gate_name, allowed in GATE_ENUMS.items():
        if gate_name not in gates:
            v.append(Violation("missing_gate", f"gate 항목 부재: {gate_name}"))
            continue
        gate_val = gates[gate_name]["value"]
        if gate_val not in allowed:
            v.append(Violation(
                "invalid_gate_value",
                f"gate {gate_name} 값이 enum 외: {gate_val} (허용: {sorted(allowed)})"
            ))

    # 5. status ↔ gates 일관성
    if status == "READY":
        for gate_name, info in gates.items():
            val = info["value"]
            if val == "fail":
                v.append(Violation(
                    "status_gate_inconsistency",
                    f"status: READY 인데 {gate_name}: fail",
                ))
            if gate_name == "drift" and val == "detected":
                v.append(Violation(
                    "status_gate_inconsistency",
                    f"status: READY 인데 drift: detected",
                ))

    # 6. status: NOT_READY → 적어도 1 개 gate fail 이거나 drift detected
    # NOTE: issues_to_fix 관련 룰 (not_ready_no_issues / ready_with_issues / drift_not_in_issues)
    # 은 issue 기능 정립 전까지 비활성. 향후 결정 후 재활성화.
    if status == "NOT_READY":
        any_fail = any(g["value"] == "fail" for g in gates.values()) or \
                   gates.get("drift", {}).get("value") == "detected"
        if not any_fail:
            v.append(Violation(
                "status_no_failure_evidence",
                "status: NOT_READY 인데 어떤 gate 도 fail/detected 가 아님",
            ))

    # 7. mode ↔ gate skip 매핑
    if mode in MODE_GATE_SKIP_RULES:
        for gate_name, must_skip in MODE_GATE_SKIP_RULES[mode].items():
            if gate_name not in gates:
                continue
            actual = gates[gate_name]["value"]
            if must_skip and actual != "skip":
                v.append(Violation(
                    "mode_gate_mismatch",
                    f"mode: {mode} 에서 {gate_name} 는 skip 이어야 하지만 {actual} 로 기록됨",
                ))
            if not must_skip and actual == "skip":
                v.append(Violation(
                    "mode_gate_mismatch",
                    f"mode: {mode} 에서 {gate_name} 는 pass|fail 이어야 하지만 skip 으로 기록됨",
                ))

    # 8. (제거) drift_not_in_issues — issues 기능 정립 전까지 비활성

    return v


# ---------------------------------------------------------------------------
# 출력 / CLI
# ---------------------------------------------------------------------------

def render_text(violations: list[Violation], block_present: bool) -> str:
    if not block_present:
        return "FAIL: VERIFICATION REPORT 블록 부재 (`## VERIFICATION REPORT` 헤더 없음)\n"
    if not violations:
        return "PASS: 위반 없음\n"
    errs = [v for v in violations if v.severity == Violation.SEVERITY_ERROR]
    warns = [v for v in violations if v.severity == Violation.SEVERITY_WARN]
    label = "FAIL" if errs else "WARN"
    out = []
    out.append(f"{label}: error {len(errs)} / warn {len(warns)}\n")
    for v in errs:
        out.append(f"  [error] {v.code}: {v.message}")
    for v in warns:
        out.append(f"  [warn]  {v.code}: {v.message}")
    return "\n".join(out) + "\n"


def render_json(violations: list[Violation], block_present: bool) -> str:
    return json.dumps({
        "block_present": block_present,
        "passed": block_present and not [v for v in violations if v.severity == Violation.SEVERITY_ERROR],
        "violations": [v.to_dict() for v in violations],
    }, ensure_ascii=False, indent=2)


def lint(text: str) -> tuple[list[Violation], bool]:
    """text → (violations, block_present)."""
    block = extract_report_block(text)
    if block is None:
        return ([], False)
    parsed = parse_report(block)
    return (validate(parsed), True)


def main() -> int:
    parser = argparse.ArgumentParser(description="pilot verify-report-lint")
    parser.add_argument("path", nargs="?", help="REPORT 파일 경로 (생략 시 stdin)")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    args = parser.parse_args()

    if args.path:
        p = Path(args.path)
        if not p.is_file():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 2
        text = p.read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    violations, block_present = lint(text)
    if args.json:
        print(render_json(violations, block_present))
    else:
        print(render_text(violations, block_present), end="")

    if not block_present:
        return 1
    has_error = any(v.severity == Violation.SEVERITY_ERROR for v in violations)
    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main())
