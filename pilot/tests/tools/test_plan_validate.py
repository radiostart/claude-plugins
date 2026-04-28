"""
tools/plan-validate.py 단위 테스트.

실행:
    python3 tests/tools/test_plan_validate.py
"""

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = THIS_DIR.parent.parent
TOOL_PATH = PLUGIN_ROOT / "tools" / "plan-validate.py"


def _load_mod():
    spec = importlib.util.spec_from_file_location("plan_validate_mod", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = _load_mod()


VALID_STANDARD = """## 구현 계획: #1 주문 검증 추가

### 변경 파일

- [ ] `app/services/order_service.rb` — validate 추가

### 구현 순서

1. validator 모듈 추가
2. service 에 호출 삽입

### 주의사항

- 기존 호출자 영향 없음 확인
"""

VALID_STANDARD_MINIMAL = """# #1 간단한 계획

본문만 있고 별도 섹션 없음. doc-level 형식은 자유 — 검증 대상 아님.
"""

VALID_CHARACTERIZE_REAL_PATTERN = """# #26 APP PUSH 자동 발송 — Characterization Contract

> source: features/26-app-push.md
> mode: characterize

## 포착 대상 요약

7 종 PUSH 발송 분기를 spec 으로 고정.

### PUSH 별 진입점

| push_type | 진입 메서드 |
|---|---|
| A | foo |

### 스텝 목록 (Characterization Contract)

1. **[스텝 1]** create_presend — 분기 grid

   - 테스트 대상: `spec/services/presend_service_spec.rb`
   - 입력: 어드민 접수 (price > 0)
   - 현재 출력: Generator 실행 예정
   - 관찰된 사이드 이펙트: send_push 1 회 호출
"""

VALID_TDD = """## 구현 계획: #2 환불 정책 적용

### 변경 파일

- [ ] `app/services/refund_service.rb`

### 스텝 목록

1. **[스텝 1]** RefundService#process — 정책 적용
   - 테스트 대상: `spec/services/refund_service_spec.rb`
   - 검증할 행동: 환불 요청 시 → process 호출 → 정책 검증 통과
   - 기대 실패 유형: `NoMethodError: undefined method 'apply_policy'`

2. **[스텝 2]** RefundPolicy#valid? — 가드
   - 테스트 대상: `spec/policies/refund_policy_spec.rb`
   - 검증할 행동: 7일 초과 → valid? 호출 → false
   - 기대 실패 유형: `NameError: uninitialized constant RefundPolicy`

### 주의사항

- 기간 계산은 KST 기준
"""

VALID_CHARACTERIZE = """## 구현 계획: #3 레거시 결제 포착

### 변경 파일

- [ ] `spec/services/legacy_payment_spec.rb` (신규)

### 스텝 목록 (Characterization Contract)

1. **[스텝 1]** LegacyPayment#charge — 현재 동작 포착
   - 테스트 대상: `spec/services/legacy_payment_spec.rb`
   - 입력: amount=1000, currency='KRW'
   - 현재 출력: Generator 실행 예정
   - 관찰된 사이드 이펙트: payments 테이블 INSERT, audit_log 기록

### 주의사항

- app/ 수정 금지
"""

INVALID_TDD_MISSING_FIELD = """## 구현 계획: #4 누락 필드

### 변경 파일

- [ ] `app/foo.rb`

### 스텝 목록

1. **[스텝 1]** Foo#bar
   - 테스트 대상: `spec/foo_spec.rb`
   - 검증할 행동: 호출 시 결과 반환

### 주의사항

- (없음)
"""

INVALID_NO_TITLE = """본문만 있고 헤딩이 전혀 없는 파일.

이런 형식은 plan 으로 인식되지 않는다.
"""

INVALID_TDD_NO_STEPS = """## 구현 계획: #5

### 변경 파일

- [ ] `app/foo.rb`

### 스텝 목록

(아직 작성 전)

### 주의사항

- 없음
"""


class HasPlanTitle(unittest.TestCase):
    def test_h1_present(self):
        self.assertTrue(m.has_plan_title("# 제목\n본문"))

    def test_h2_present(self):
        self.assertTrue(m.has_plan_title("## 구현 계획: foo"))

    def test_h3_also_counts(self):
        # 임의의 H3 도 마크다운 헤딩으로 인정 (실 plan 에 H1 없는 케이스 대비)
        self.assertTrue(m.has_plan_title("### 변경 파일\n본문"))

    def test_h6_present(self):
        self.assertTrue(m.has_plan_title("###### 매우 작은 제목"))

    def test_no_heading(self):
        self.assertFalse(m.has_plan_title("본문만 있음. 헤딩 없음."))

    def test_hash_without_space(self):
        # "#태그" 같은 라인은 헤딩 아님 (공백 필요)
        self.assertFalse(m.has_plan_title("#태그 본문"))


class FindMissingSections(unittest.TestCase):
    def test_standard_has_no_required_sections(self):
        # standard 모드는 doc-level 섹션을 강제하지 않음 — 빈 본문도 통과
        self.assertEqual(m.find_missing_sections("본문\n", "standard"), [])

    def test_tdd_requires_step_section(self):
        self.assertEqual(m.find_missing_sections(VALID_TDD, "tdd"), [])

    def test_characterize_requires_exact_heading(self):
        self.assertEqual(
            m.find_missing_sections(VALID_CHARACTERIZE, "characterize"), []
        )

    def test_tdd_section_does_not_satisfy_characterize(self):
        # tdd 의 "### 스텝 목록" 만 있으면 characterize 에선 missing
        missing = m.find_missing_sections(VALID_TDD, "characterize")
        self.assertIn("### 스텝 목록 (Characterization Contract)", missing)


class SplitSteps(unittest.TestCase):
    def test_extract_two_steps(self):
        body = m.extract_section_body(VALID_TDD, "### 스텝 목록")
        self.assertIsNotNone(body)
        steps = m.split_steps(body)
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0][0], 1)
        self.assertEqual(steps[1][0], 2)

    def test_no_steps(self):
        body = "(아직 작성 전)\n"
        self.assertEqual(m.split_steps(body), [])


class IsMetaStep(unittest.TestCase):
    def test_jaepocheok_skip(self):
        body = "1. **[스텝 1]** Foo\n   - [Captured] 재포착 생략 — 사유 ...\n"
        self.assertTrue(m.is_meta_step(body))

    def test_record_only(self):
        body = "1. **[스텝 1]** Foo\n   - 기록만 남김: ...\n"
        self.assertTrue(m.is_meta_step(body))

    def test_normal_step_not_meta(self):
        body = "1. **[스텝 1]** Foo\n   - 테스트 대상: x\n"
        self.assertFalse(m.is_meta_step(body))


class LabelVariants(unittest.TestCase):
    def test_label_with_inline_qualifier(self):
        # `입력 (3축 조합):` 같은 변형도 인정
        body = (
            "1. **[스텝 1]** Foo\n"
            "   - 테스트 대상: x\n"
            "   - 입력 (reason × new_count 3축 조합):\n"
            "     - Row A: ...\n"
            "   - 현재 출력: y\n"
            "   - 관찰된 사이드 이펙트: z\n"
        )
        miss = m.step_missing_labels(body, m.STEP_REQUIRED_LABELS["characterize"])
        self.assertEqual(miss, [])

    def test_label_inside_word_not_matched(self):
        # 다른 단어 내부의 부분 매칭은 인정 안 함 (`재입력:` 은 `입력:` 아님)
        body = (
            "1. **[스텝 1]** Foo\n"
            "   - 테스트 대상: x\n"
            "   - 재입력:\n"  # 라벨 아님 — `입력:` 매칭 금지
            "   - 현재 출력: y\n"
            "   - 관찰된 사이드 이펙트: z\n"
        )
        miss = m.step_missing_labels(body, m.STEP_REQUIRED_LABELS["characterize"])
        self.assertIn("입력:", miss)


class StepMissingLabels(unittest.TestCase):
    def test_all_present(self):
        body = (
            "1. **[스텝 1]** Foo\n"
            "   - 테스트 대상: `x`\n"
            "   - 검증할 행동: y\n"
            "   - 기대 실패 유형: z\n"
        )
        self.assertEqual(
            m.step_missing_labels(body, m.STEP_REQUIRED_LABELS["tdd"]),
            [],
        )

    def test_alternative_label_accepted(self):
        # `spec 대상:` 도 `테스트 대상:` 동의어로 인정
        body = (
            "1. **[스텝 1]** Foo\n"
            "   - spec 대상: `x`\n"
            "   - 검증할 행동: y\n"
            "   - 기대 실패 유형: z\n"
        )
        self.assertEqual(
            m.step_missing_labels(body, m.STEP_REQUIRED_LABELS["tdd"]),
            [],
        )

    def test_one_missing(self):
        body = (
            "1. **[스텝 1]** Foo\n"
            "   - 테스트 대상: `x`\n"
            "   - 검증할 행동: y\n"
        )
        miss = m.step_missing_labels(body, m.STEP_REQUIRED_LABELS["tdd"])
        self.assertEqual(miss, ["기대 실패 유형:"])


class ValidateIntegration(unittest.TestCase):
    def _write(self, content: str) -> Path:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".plan.md", delete=False, encoding="utf-8"
        )
        tmp.write(content)
        tmp.close()
        return Path(tmp.name)

    def test_valid_standard(self):
        p = self._write(VALID_STANDARD)
        r = m.validate(p, "standard")
        self.assertTrue(r["valid"], r)

    def test_valid_standard_minimal(self):
        # 섹션 없는 자유 형식도 standard 모드에선 통과
        p = self._write(VALID_STANDARD_MINIMAL)
        r = m.validate(p, "standard")
        self.assertTrue(r["valid"], r)

    def test_valid_tdd(self):
        p = self._write(VALID_TDD)
        r = m.validate(p, "tdd")
        self.assertTrue(r["valid"], r)

    def test_valid_characterize(self):
        p = self._write(VALID_CHARACTERIZE)
        r = m.validate(p, "characterize")
        self.assertTrue(r["valid"], r)

    def test_valid_characterize_real_pattern(self):
        # 실 운영 plan 패턴 — H1, 포착 대상 요약, 자유 H3 들 + 스텝 목록
        p = self._write(VALID_CHARACTERIZE_REAL_PATTERN)
        r = m.validate(p, "characterize")
        self.assertTrue(r["valid"], r)

    def test_invalid_no_title(self):
        p = self._write(INVALID_NO_TITLE)
        r = m.validate(p, "standard")
        self.assertFalse(r["valid"])
        self.assertTrue(any("missing markdown heading" in e for e in r["errors"]))

    def test_invalid_tdd_missing_field(self):
        p = self._write(INVALID_TDD_MISSING_FIELD)
        r = m.validate(p, "tdd")
        self.assertFalse(r["valid"])
        self.assertEqual(len(r["step_errors"]), 1)
        self.assertEqual(r["step_errors"][0]["step"], 1)
        self.assertIn("기대 실패 유형:", r["step_errors"][0]["missing_fields"])

    def test_invalid_tdd_no_steps(self):
        p = self._write(INVALID_TDD_NO_STEPS)
        r = m.validate(p, "tdd")
        self.assertFalse(r["valid"])
        self.assertTrue(any("no step items" in e for e in r["errors"]))

    def test_file_not_found(self):
        r = m.validate(Path("/tmp/nonexistent-plan-xyz.md"), "standard")
        self.assertFalse(r["valid"])
        self.assertTrue(any("not found" in e for e in r["errors"]))

    def test_unknown_mode(self):
        p = self._write(VALID_STANDARD)
        r = m.validate(p, "unknown")
        self.assertFalse(r["valid"])


class CliExit(unittest.TestCase):
    def _run(self, content: str, mode: str) -> subprocess.CompletedProcess:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".plan.md", delete=False, encoding="utf-8"
        )
        tmp.write(content)
        tmp.close()
        return subprocess.run(
            ["python3", str(TOOL_PATH), tmp.name, "--mode", mode],
            capture_output=True,
            text=True,
        )

    def test_exit_0_on_valid(self):
        r = self._run(VALID_STANDARD, "standard")
        self.assertEqual(r.returncode, 0, r.stderr)
        payload = json.loads(r.stdout)
        self.assertTrue(payload["valid"])

    def test_exit_1_on_invalid(self):
        r = self._run(INVALID_TDD_MISSING_FIELD, "tdd")
        self.assertEqual(r.returncode, 1)
        payload = json.loads(r.stdout)
        self.assertFalse(payload["valid"])
        self.assertIn("plan-validate", r.stderr)


if __name__ == "__main__":
    unittest.main()
