#!/usr/bin/env python3
"""
pilot auto_pilot — 감독형 자율 오케스트레이터의 전이 결정 로직.

`/pilot:auto` 스킬이 각 에이전트(planner / critic / generator / evaluator)를
순차 호출하는 사이, 각 에이전트가 남긴 머신리더블 신호를 읽어 다음 액션을
결정한다. 이 모듈은 *판단하지 않는다* — 신호의 enum 값만 보고 전이한다.

신호 출처:
  - planner   : plan-validate.py exit code → plan_valid (bool)
  - critic    : .plan.critic.md 의 챌린지 severity 목록 → severities (list|None)
  - evaluator : VERIFICATION REPORT 의 status → status ("READY"|"NOT_READY"|None)

액션 종류:
  proceed | reflect | retry | done | stop

스펙: docs/superpowers/specs/2026-05-29-pilot-auto-design.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

MAX_RETRIES = 1  # NOT_READY 시 generator 재진입 횟수 상한


@dataclass
class Action:
    kind: str            # proceed | reflect | retry | done | stop
    reason: str = ""     # stop 일 때 사유 (plan-validate | critic-blocking | retry-exhausted | signal-parse | agent-error)


_SEVERITY_LINE_RE = re.compile(
    r"^\s*[-*]?\s*\*{0,2}severity\*{0,2}\s*:\s*([a-zA-Z_]+)", re.MULTILINE
)
_CHALLENGE_HEADER_RE = re.compile(r"^###\s+C\d+", re.MULTILINE)
# critic 의 명시적 "결함 없음" 통과 문구 (agents/pilot-planner-critic.md step 5).
# 0건일 때 critic 은 `## 챌린지` 아래에 이 문구 한 줄만 남긴다.
_PASS_MARKER_RE = re.compile(r"검출된 결함 없음|plan 통과")

VALID_SEVERITIES = {"blocking", "suggestion", "nit"}


def parse_critic_severities(text: str):
    """`.plan.critic.md` 본문에서 severity 목록을 추출한다.

    Returns:
        list[str]  — 정상 파싱 (0건이면 빈 리스트)
        None       — 형식이 깨져 신뢰할 수 없음 (상위에서 hard-stop)
    """
    headers = _CHALLENGE_HEADER_RE.findall(text)
    sev_matches = _SEVERITY_LINE_RE.findall(text)

    # 명시적 "결함 없음" 통과 문구가 있고 챌린지 헤더도 severity 라벨도 없으면
    # 0건으로 인정. severity 라벨이 존재하면 통과 문구가 본문 어딘가에 끼어
    # 있더라도 0건 처리하지 않고 아래 정상 파싱 경로로 흘려보낸다 (오탐 방지).
    if _PASS_MARKER_RE.search(text) and not headers and not sev_matches:
        return []

    # 챌린지 헤더도 severity 라벨도 통과 문구도 없으면 형식 미상 → None
    if not headers and not sev_matches:
        return None

    severities = [s.lower() for s in sev_matches if s.lower() in VALID_SEVERITIES]

    # 챌린지 헤더가 있는데 유효 severity 를 하나도 못 읽었으면 형식 깨짐 → None
    if headers and not severities:
        return None

    return severities


_THIS_DIR = Path(__file__).resolve().parent


def _load_report_lint():
    """tools/verify-report-lint.py 를 동적 로드 (하이픈 파일명)."""
    import importlib.util

    path = _THIS_DIR / "verify-report-lint.py"
    spec = importlib.util.spec_from_file_location("verify_report_lint_mod", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["verify_report_lint_mod"] = module
    spec.loader.exec_module(module)
    return module


def parse_evaluator_status(text: str):
    """evaluator 출력 텍스트에서 VERIFICATION REPORT status 를 추출한다.

    기존 verify-report-lint.py 의 검증된 파서를 재사용한다 (REPORT 파싱 중복 금지).

    Returns:
        "READY" | "NOT_READY"  — 정상 파싱
        None                   — REPORT 블록 부재 또는 status 부재/이상 (상위에서 hard-stop)
    """
    lint = _load_report_lint()
    block = lint.extract_report_block(text)
    if block is None:
        return None
    parsed = lint.parse_report(block)
    status = parsed.get("status")
    if status not in ("READY", "NOT_READY"):
        return None
    return status


def decide_next(phase: str, signal: dict) -> Action:
    """phase 의 산출 신호를 받아 다음 액션을 결정한다 (순수 함수)."""
    if phase == "planner":
        if signal.get("plan_valid") is True:
            return Action("proceed")
        return Action("stop", "plan-validate")

    if phase == "critic":
        severities = signal.get("severities")
        if severities is None:
            return Action("stop", "signal-parse")
        if "blocking" in severities:
            return Action("stop", "critic-blocking")
        if len(severities) == 0:
            return Action("proceed")
        return Action("reflect")

    if phase == "evaluator":
        status = signal.get("status")
        if status == "READY":
            return Action("done")
        if status == "NOT_READY":
            if signal.get("retries_used", 0) < MAX_RETRIES:
                return Action("retry")
            return Action("stop", "retry-exhausted")
        return Action("stop", "signal-parse")

    return Action("stop", "signal-parse")


def _read_file_or_none(path_str):
    """파일을 읽어 텍스트 반환. 없거나 못 읽으면 None."""
    if not path_str:
        return None
    p = Path(path_str)
    if not p.is_file():
        return None
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return None


def _build_signal(args) -> dict:
    """CLI 인자 → decide_next 가 받는 signal dict."""
    if args.phase == "planner":
        return {"plan_valid": args.plan_valid == "true"}

    if args.phase == "critic":
        text = _read_file_or_none(args.critic_file)
        if text is None:
            return {"severities": None}
        return {"severities": parse_critic_severities(text)}

    if args.phase == "evaluator":
        text = _read_file_or_none(args.report_file)
        status = parse_evaluator_status(text) if text is not None else None
        return {"status": status, "retries_used": args.retries_used}

    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="pilot auto-pilot 전이 결정")
    ap.add_argument(
        "--phase", required=True, choices=["planner", "critic", "evaluator"]
    )
    ap.add_argument("--plan-valid", choices=["true", "false"], dest="plan_valid")
    ap.add_argument("--critic-file", dest="critic_file")
    ap.add_argument("--report-file", dest="report_file")
    ap.add_argument("--retries-used", type=int, default=0, dest="retries_used")
    args = ap.parse_args()

    signal = _build_signal(args)
    action = decide_next(args.phase, signal)
    print(json.dumps({"kind": action.kind, "reason": action.reason}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
