# doctor — 실패 진단 모드 (`--diagnose`)

`/pilot:doctor --diagnose` 는 정합성 검사와 독립적으로 런타임 실패 패턴을 4-phase (capture → diagnose → reduce → report) 로 진단한다.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace --diagnose
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py workspace --diagnose --project MyProject
```

---

## 검출 패턴

| 패턴 | 의미 | 판정 근거 |
|---|---|---|
| `loop` | 에이전트 루프 의심 | `.plan.md` 에 동일 설명 3회+ 반복 |
| `red-miss` | TDD Red 증거 누락 | `tdd: true` 인데 스텝 대비 `[Red]` 마크 부족 |
| `repeat-not-ready` | 동일 feature 2회+ 반려 | `.plan.md` / `project.md` 에 `NOT_READY` · `반려` 누적 |
| `scope-violation` | `.focus.md` scope 외 편집 | git diff 파일과 scope 불일치 |
| `none` | 정상 | 감지된 패턴 없음 |

---

## 출력 형식

```
## DIAGNOSIS
- project: MyProject
- pattern: red-miss | repeat-not-ready | loop | scope-violation | none
- evidence: {근거 요약}
- recommended_action: {권장 액션}
- confidence: high | medium
```

---

## Exit code & 우선순위

- exit code: `0` (pattern=none) · `1` (패턴 감지).
- 복수 패턴 동시 감지 시 우선순위: `red-miss > repeat-not-ready > scope-violation > loop`. 이 때 `confidence: medium`.

---

## 언제 호출

- evaluator 가 같은 feature 에 `status: NOT_READY` 를 2회 출력했을 때.
- 에이전트가 동일 도구·명령을 반복하는 것으로 의심될 때.
- 체크리스트·REPORT 기록이 비어있는데 완료 선언된 경우 (Red 증거 누락 의심).
