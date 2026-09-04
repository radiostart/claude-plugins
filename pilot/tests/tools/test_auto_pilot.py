"""
tools/auto_pilot.py 단위 테스트.

실행:
    python3 tests/tools/test_auto_pilot.py
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "auto_pilot.py"


def _load_mod():
    spec = importlib.util.spec_from_file_location("auto_pilot_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    # Python 3.13: register in sys.modules before exec so @dataclass can resolve __module__
    sys.modules["auto_pilot_mod"] = module
    spec.loader.exec_module(module)
    return module


m = _load_mod()


CRITIC_WITH_BLOCKING = """# Plan Critic — #3 사용자 삭제

> 입력 plan: `features/03-user-deletion.plan.md`

## 챌린지

### C1 — soft-delete 누락

- **severity**: blocking
- **category**: risk
- **plan 인용**: 단계 #2
- **챌린지**: soft-delete 누락
- **제안**: archived_at 추가

### C2 — 과한 단계

- **severity**: suggestion
- **category**: scope
- **plan 인용**: 단계 #4
- **챌린지**: 과한 단계
- **제안**: 병합
"""

CRITIC_SUGGESTION_NIT = """# Plan Critic — #3 사용자 삭제

## 챌린지

### C1 — 대안 제안

- **severity**: suggestion
- **category**: alternative

### C2 — 사소한 정확성

- **severity**: nit
- **category**: scope
"""

CRITIC_NO_CHALLENGES = """# Plan Critic — #3 사용자 삭제

> 입력 plan: `features/03-user-deletion.plan.md`

## 챌린지

검출된 결함 없음. plan 통과.
"""

CRITIC_MALFORMED = """# 잘못된 파일

제목만 있고 챌린지 섹션도 severity 라벨도 통과 문구도 없는 내용.
"""

EVAL_READY = """## VERIFICATION REPORT

- status: READY
- feature: #3 사용자 삭제
- mode: standard
- gates:
  - requirements: pass
  - tdd_evidence: skip
  - capture_lockdown: skip
  - test_run: skip
  - scope: pass
  - drift: none
- metrics:
  - files_changed: 4
- issues_to_fix:
  - none
- next: PR 준비
"""

EVAL_NOT_READY = """## VERIFICATION REPORT

- status: NOT_READY
- feature: #3 사용자 삭제
- mode: standard
- gates:
  - requirements: fail
  - tdd_evidence: skip
  - capture_lockdown: skip
  - test_run: skip
  - scope: pass
  - drift: none
- metrics:
  - files_changed: 4
- issues_to_fix:
  - [blocking] soft-delete 누락 — order_service.rb
- next: generator 재진입
"""

EVAL_NO_REPORT = """구현은 끝났습니다. 보고서 블록을 빼먹었습니다.
"""


class TestDecideNext(unittest.TestCase):
    def test_planner_signal_error_stops_agent_error(self):
        # None = 검증 자체가 실행 불능 — invalid plan(plan-validate)과 처방이 다르다.
        action = m.decide_next("planner", {"plan_valid": None})
        self.assertEqual(action.kind, "stop")
        self.assertEqual(action.reason, "agent-error")

    def test_plan_validate_fail_stops(self):
        action = m.decide_next("planner", {"plan_valid": False})
        self.assertEqual(action.kind, "stop")
        self.assertEqual(action.reason, "plan-validate")

    def test_plan_validate_pass_proceeds(self):
        action = m.decide_next("planner", {"plan_valid": True})
        self.assertEqual(action.kind, "proceed")

    def test_critic_blocking_stops(self):
        action = m.decide_next("critic", {"severities": ["suggestion", "blocking"]})
        self.assertEqual(action.kind, "stop")
        self.assertEqual(action.reason, "critic-blocking")

    def test_critic_suggestion_nit_only_reflects(self):
        action = m.decide_next("critic", {"severities": ["suggestion", "nit"]})
        self.assertEqual(action.kind, "reflect")

    def test_critic_empty_proceeds(self):
        action = m.decide_next("critic", {"severities": []})
        self.assertEqual(action.kind, "proceed")

    def test_critic_unparseable_stops(self):
        action = m.decide_next("critic", {"severities": None})
        self.assertEqual(action.kind, "stop")
        self.assertEqual(action.reason, "signal-parse")

    def test_evaluator_ready_done(self):
        action = m.decide_next("evaluator", {"status": "READY", "retries_used": 0})
        self.assertEqual(action.kind, "done")

    def test_evaluator_not_ready_first_retries(self):
        action = m.decide_next("evaluator", {"status": "NOT_READY", "retries_used": 0})
        self.assertEqual(action.kind, "retry")

    def test_evaluator_not_ready_exhausted_stops(self):
        action = m.decide_next("evaluator", {"status": "NOT_READY", "retries_used": 1})
        self.assertEqual(action.kind, "stop")
        self.assertEqual(action.reason, "retry-exhausted")

    def test_evaluator_unparseable_stops(self):
        action = m.decide_next("evaluator", {"status": None, "retries_used": 0})
        self.assertEqual(action.kind, "stop")
        self.assertEqual(action.reason, "signal-parse")


class TestParseCriticSeverities(unittest.TestCase):
    def test_extracts_blocking_and_suggestion(self):
        result = m.parse_critic_severities(CRITIC_WITH_BLOCKING)
        self.assertEqual(sorted(result), ["blocking", "suggestion"])

    def test_suggestion_nit_only(self):
        result = m.parse_critic_severities(CRITIC_SUGGESTION_NIT)
        self.assertEqual(sorted(result), ["nit", "suggestion"])

    def test_no_challenges_returns_empty_list(self):
        result = m.parse_critic_severities(CRITIC_NO_CHALLENGES)
        self.assertEqual(result, [])

    def test_malformed_returns_none(self):
        result = m.parse_critic_severities(CRITIC_MALFORMED)
        self.assertIsNone(result)

    def test_pass_marker_does_not_mask_real_severities(self):
        # 통과 문구가 본문에 끼어 있어도 severity 라벨이 있으면 0건 처리하지 않는다.
        text = (
            "## 챌린지\n\n"
            "- **severity**: blocking\n"
            "- **제안**: 이대로면 plan 통과 못 함\n"
        )
        result = m.parse_critic_severities(text)
        self.assertEqual(result, ["blocking"])

    # ── 파싱 완전성 불변식 (적대적 검토 반영) ────────────────────────────
    # known limitation: 같은 챌린지에서 헤더·severity 가 함께 깨지거나
    # (`#### C2` 오기 + `- **severity**: **blocking**` 볼드 값) decoy 라벨이
    # 수를 재균형하면 불변식을 통과한다 — 파서로 자유형 일탈 전부는 못 잡는다.

    def test_partial_severity_loss_returns_none(self):
        # 챌린지 3건 중 1건의 severity 만 비표준 — 탈락분이 blocking 이면
        # 나머지로 reflect 통과되던 fail-open. 이제 형식 불신으로 stop.
        text = (
            "## 챌린지\n"
            "### C1 — a\n- **severity**: suggestion\n"
            "### C2 — b\n- **severity**: nit\n"
            "### C3 — c\n- **severity**: 차단\n"
        )
        self.assertIsNone(m.parse_critic_severities(text))

    def test_invalid_value_without_headers_returns_none(self):
        # 헤더 0 + 비표준 값만 → 기존엔 [] 로 proceed 되던 fail-open.
        text = "## 챌린지\n- **severity**: major\n"
        self.assertIsNone(m.parse_critic_severities(text))

    def test_negated_pass_phrase_returns_none(self):
        # 행 시작이 통과 문구로 시작하는 부정문 — 전체-행 매치라 비매치.
        text = "## 챌린지\n\n검출된 결함 없음이라고 단정하기 어렵다. 추가 검토를 권한다.\n"
        self.assertIsNone(m.parse_critic_severities(text))

    def test_freeform_pass_prose_returns_none(self):
        # 자유서술 속 'plan 통과' 서브스트링 — 기존엔 [] 로 proceed 되던 fail-open.
        text = "## 챌린지\n형식을 갖추지 못했다. 이 plan 통과 여부는 추가 검토가 필요하다.\n"
        self.assertIsNone(m.parse_critic_severities(text))

    def test_uppercase_severity_label_recognized(self):
        # 대소문자 변형은 형식 결함이 아니다 — signal-parse 대신
        # critic-blocking 으로 정지해 처방이 실제 원인을 가리키게 된다.
        text = "## 챌린지\n### C1 — a\n- **Severity**: blocking\n"
        self.assertEqual(m.parse_critic_severities(text), ["blocking"])

    def test_quoted_severity_bullet_in_proposal_stops(self):
        # 계약 준수 파일이지만 제안 본문에 severity 인용 불릿이 있으면 stop —
        # 의도된 조임 (저빈도, 처방표 signal-parse 행이 커버).
        text = (
            "## 챌린지\n"
            "### C1 — severity 표기 정리\n"
            "- **severity**: suggestion\n"
            "- **category**: scope\n"
            "- **제안**: 아래처럼 명시할 것\n"
            "  - severity: high 로 명시\n"
        )
        self.assertIsNone(m.parse_critic_severities(text))


class TestParseEvaluatorStatus(unittest.TestCase):
    def test_ready(self):
        self.assertEqual(m.parse_evaluator_status(EVAL_READY), "READY")

    def test_not_ready(self):
        self.assertEqual(m.parse_evaluator_status(EVAL_NOT_READY), "NOT_READY")

    def test_no_report_block_returns_none(self):
        self.assertIsNone(m.parse_evaluator_status(EVAL_NO_REPORT))

    # ── status 정확 매치 (적대적 검토 반영) ──────────────────────────────

    def test_template_echo_returns_none(self):
        # 템플릿 줄을 그대로 복사한 흔한 실패 모드 — 첫-토큰 절삭이
        # READY 로 오독해 무검증 done 이 되던 fail-open.
        text = "## VERIFICATION REPORT\n- status: READY | NOT_READY\n"
        self.assertIsNone(m.parse_evaluator_status(text))

    def test_annotated_ready_returns_none(self):
        # 유보 붙은 READY — 평가자의 유보 의도를 절삭하지 않는다.
        text = "## VERIFICATION REPORT\n- status: READY (조건부 — 테스트 미실행)\n"
        self.assertIsNone(m.parse_evaluator_status(text))

    def test_duplicate_status_key_returns_none(self):
        # 블록 내 status 재기입 — 라인 루프의 마지막-값-승 규칙이
        # NOT_READY 를 READY 로 뒤집던 fail-open (F9).
        text = (
            "## VERIFICATION REPORT\n"
            "- status: NOT_READY\n"
            "- issues_to_fix:\n"
            "  - [blocking] 미해결\n"
            "- status: READY\n"
        )
        self.assertIsNone(m.parse_evaluator_status(text))


class TestExtractAndParseReport(unittest.TestCase):
    """extract_report_block · parse_report 단위 테스트 (구 test_verify_report_lint.py 이식, #20 스텝 5)."""

    def test_no_block_returns_none(self):
        self.assertIsNone(m.extract_report_block("# 다른 헤더\n본문"))

    def test_block_extracted(self):
        text = "전문\n## VERIFICATION REPORT\n- status: READY\n## 다음 섹션\n끝"
        block = m.extract_report_block(text)
        self.assertIn("status: READY", block)
        self.assertNotIn("다음 섹션", block)

    def test_two_exact_headers_returns_none(self):
        # 복수 블록 = evaluator 계약(전체 재생성) 위반 — 추정하지 않고 멈춘다 (F7).
        text = (
            "## VERIFICATION REPORT\n- status: NOT_READY\n\n"
            "## VERIFICATION REPORT\n- status: READY\n"
        )
        self.assertIsNone(m.extract_report_block(text))

    def test_decorated_second_header_returns_none(self):
        # 장식 헤더는 정확-매치 카운트를 피해 stale READY 첫 블록만 남기던
        # 우회 (F10) — 유일성은 접두 매치로 센다.
        text = (
            "## VERIFICATION REPORT\n- status: READY\n\n"
            "## VERIFICATION REPORT — 재평가 (2차)\n- status: NOT_READY\n"
        )
        self.assertIsNone(m.extract_report_block(text))

    def test_status_value_preserved_verbatim(self):
        # status 는 절삭 없이 원문 보존 — 정확-매치 판정의 전제.
        r = m.parse_report("- status: READY | NOT_READY\n")
        self.assertEqual(r["status"], "READY | NOT_READY")

    def test_parse_top_level_keys(self):
        block = (
            "- status: READY\n"
            "- feature: #03 결제\n"
            "- mode: red_contract\n"
            "- next: #04 환불\n"
        )
        r = m.parse_report(block)
        self.assertEqual(r["status"], "READY")
        self.assertEqual(r["feature"], "#03 결제")
        self.assertEqual(r["mode"], "red_contract")
        self.assertEqual(r["next"], "#04 환불")

    def test_parse_gates(self):
        block = (
            "- gates:\n"
            "  - requirements: pass — features/03.md\n"
            "  - tdd_evidence: skip — mode 미사용\n"
            "  - drift: detected — workspace/...\n"
        )
        r = m.parse_report(block)
        self.assertEqual(r["gates"]["requirements"]["value"], "pass")
        self.assertEqual(r["gates"]["requirements"]["evidence"], "features/03.md")
        self.assertEqual(r["gates"]["tdd_evidence"]["value"], "skip")
        self.assertEqual(r["gates"]["drift"]["value"], "detected")

    def test_parse_issues(self):
        block = (
            "- issues_to_fix:\n"
            "  - [Major] foo 누락 — features/03.md:14\n"
            "  - [Minor] bar — files/x.md\n"
        )
        r = m.parse_report(block)
        self.assertEqual(len(r["issues_to_fix"]), 2)
        self.assertEqual(r["issues_to_fix"][0]["severity"], "Major")
        self.assertEqual(r["issues_to_fix"][0]["summary"], "foo 누락")
        self.assertEqual(r["issues_to_fix"][0]["location"], "features/03.md:14")

    def test_parse_issues_none(self):
        block = "- issues_to_fix:\n  - none\n"
        r = m.parse_report(block)
        self.assertEqual(len(r["issues_to_fix"]), 1)
        self.assertEqual(r["issues_to_fix"][0]["summary"], "none")


class TestModeFromState(unittest.TestCase):
    """_mode_from_state — .agent-state.yml 에서의 mode 직접 도출 (P2-1)."""

    def _state(self, content):
        f = tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False)
        f.write(content)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_characterize_wins_over_tdd(self):
        path = self._state("schema: v1.3\ntdd: true\nmode: characterize\n")
        self.assertEqual(m._mode_from_state(path), "characterize")

    def test_quoted_characterize(self):
        path = self._state('tdd: false\nmode: "characterize"\n')
        self.assertEqual(m._mode_from_state(path), "characterize")

    def test_tdd_true(self):
        path = self._state("tdd: true\nmode: null\n")
        self.assertEqual(m._mode_from_state(path), "tdd")

    def test_tdd_false_standard(self):
        path = self._state("tdd: false\nmode: null\n")
        self.assertEqual(m._mode_from_state(path), "standard")

    def test_inline_comment_stripped(self):
        # 스키마 문서 예시 형식 — 인라인 주석이 값을 오염시키지 않는다.
        path = self._state("tdd: false   # TDD 모드 활성 여부\nmode: null\n")
        self.assertEqual(m._mode_from_state(path), "standard")

    def test_missing_tdd_key_returns_none(self):
        # 필수 필드 부재 = 형식 불신 — standard 폴백은 검증 공집합 우회가 된다.
        path = self._state("schema: v1.3\ndomain: null\n")
        self.assertIsNone(m._mode_from_state(path))

    def test_missing_file_returns_none(self):
        self.assertIsNone(m._mode_from_state("/no/such/state.yml"))

    def test_none_path_returns_none(self):
        self.assertIsNone(m._mode_from_state(None))


class TestCli(unittest.TestCase):
    def _run(self, args, stdin_text=None):
        proc = subprocess.run(
            ["python3", str(TOOL_PATH)] + args,
            input=stdin_text,
            capture_output=True,
            text=True,
        )
        return proc

    def _tmpdir(self):
        d = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        return Path(d)

    def _planner_env(self, state_content, plan_content):
        """features/ 규약 경로에 plan + state 파일을 만든 뒤 (plan, state) 경로 반환."""
        d = self._tmpdir()
        features = d / "features"
        features.mkdir()
        plan = features / "03-sample.plan.md"
        plan.write_text(plan_content, encoding="utf-8")
        state = d / ".agent-state.yml"
        state.write_text(state_content, encoding="utf-8")
        return str(plan), str(state)

    def test_planner_valid_standard_proceeds(self):
        # standard 는 필수 섹션이 없다 — 최소 plan 이 valid (plan-validate 계약).
        plan, state = self._planner_env(
            "schema: v1.3\ntdd: false\nmode: null\n",
            "# plan\n\n## 구현 계획\n\n- 스텝 1\n",
        )
        proc = self._run(["--phase", "planner", "--plan-file", plan, "--state-file", state])
        self.assertEqual(proc.returncode, 0)
        out = json.loads(proc.stdout)
        self.assertEqual(out["kind"], "proceed")

    def test_planner_invalid_tdd_plan_stops_plan_validate(self):
        # tdd 모드 필수 섹션(### 스텝 목록) 부재 → invalid. stderr 에 누락 요약,
        # stdout 은 결정 JSON 단독 (plan-validate 의 JSON 은 폐기됨).
        plan, state = self._planner_env(
            "schema: v1.3\ntdd: true\nmode: null\n",
            "# plan\n\n본문뿐 — 스텝 목록 없음\n",
        )
        proc = self._run(["--phase", "planner", "--plan-file", plan, "--state-file", state])
        out = json.loads(proc.stdout)  # 이중 JSON 이면 여기서 실패한다
        self.assertEqual(out["kind"], "stop")
        self.assertEqual(out["reason"], "plan-validate")
        self.assertTrue(proc.stderr.strip(), "누락 항목 stderr 가 비어 있다")

    def test_planner_missing_plan_file_stops_agent_error(self):
        _, state = self._planner_env("schema: v1.3\ntdd: false\n", "# unused\n")
        proc = self._run(
            ["--phase", "planner", "--plan-file", "/no/such/plan.md", "--state-file", state]
        )
        out = json.loads(proc.stdout)
        self.assertEqual(out["kind"], "stop")
        self.assertEqual(out["reason"], "agent-error")

    def test_planner_missing_state_file_stops_agent_error(self):
        plan, _ = self._planner_env("unused: true\n", "# plan\n")
        proc = self._run(
            ["--phase", "planner", "--plan-file", plan, "--state-file", "/no/such/state.yml"]
        )
        out = json.loads(proc.stdout)
        self.assertEqual(out["kind"], "stop")
        self.assertEqual(out["reason"], "agent-error")

    def test_critic_phase_reads_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(CRITIC_WITH_BLOCKING)
            path = f.name
        try:
            proc = self._run(["--phase", "critic", "--critic-file", path])
            out = json.loads(proc.stdout)
            self.assertEqual(out["kind"], "stop")
            self.assertEqual(out["reason"], "critic-blocking")
        finally:
            os.unlink(path)

    def test_evaluator_phase_reads_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(EVAL_NOT_READY)
            path = f.name
        try:
            proc = self._run(
                ["--phase", "evaluator", "--report-file", path, "--retries-used", "0"]
            )
            out = json.loads(proc.stdout)
            self.assertEqual(out["kind"], "retry")
        finally:
            os.unlink(path)

    def test_evaluator_missing_file_stops_signal_parse(self):
        proc = self._run(
            ["--phase", "evaluator", "--report-file", "/no/such/file.md",
             "--retries-used", "0"]
        )
        out = json.loads(proc.stdout)
        self.assertEqual(out["kind"], "stop")
        self.assertEqual(out["reason"], "signal-parse")


if __name__ == "__main__":
    unittest.main()
