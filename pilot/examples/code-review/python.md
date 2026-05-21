# 코드 리뷰 — Python

> **참고용 예시**. 플러그인은 본 파일을 로드하지 않는다. `@pilot-code-review` 는 워크스페이스의 `{lang}.md` 만 읽는다.
> 사용법: 본 파일을 `workspace/context/review/python.md` 로 복사한 뒤 팀 컨벤션에 맞춰 편집·삭제.
> 진짜 시작 형식은 `${CLAUDE_PLUGIN_ROOT}/skills/context/lifecycle/setup/templates/code-review.lang.md.template` — 본 예시는 이미 채워진 참고 자료.

## 적용 범위

확장자: `.py`, `.pyi`. 본 룰은 변경된 hunk 에만 적용 (변경 외 코드 무시).

## Grep-friendly 위반 룰

각 룰은 `severity` + `detection` + `violation` + `fix-hint` 4요소.

- `[major][grep:^\s*print\(]` 프로덕션 코드의 `print` — 로깅 권장 → `logging` 또는 팀 표준 logger.
- `[major][grep:except\s*:\s*$]` bare `except:` — 구체 예외 타입 또는 `except Exception` + 로깅.
- `[major][grep:except\s+Exception\s*:\s*\n\s*pass]` 예외 swallow — 최소한 로그 또는 재발생 (`raise`).
- `[minor][grep:^\s*import\s+\*]` wildcard import — 명시 import.
- `[minor][grep:#\s*type:\s*ignore\s*$]` `type: ignore` 사유 누락 → `# type: ignore[error-code]  # 이유` 권장.
- `[minor][grep:^\s*from\s+\S+\s+import\s+\S+\s*$]` 미사용 import 의심 시 → 자율 탐색으로 호출 여부 확인.
- `[nit][grep:lambda\s+\w+\s*:\s*\w+\(\w+\)]` 단순 wrapper lambda — `operator` 또는 함수 참조 권장.

## Judgment-based 룰

- `[major][judgment]` mutable default arg (`def f(x=[]):`, `def f(x={}):`) — `None` sentinel + 함수 내부 초기화.
- `[major][judgment]` async 함수의 동기 블로킹 호출 (`time.sleep`, `requests.get` 등) — async 대체 (`asyncio.sleep`, `httpx.AsyncClient`).
- `[major][judgment]` 파일·네트워크 자원에 `with` 컨텍스트 매니저 누락 — 명시적 close 또는 with.
- `[minor][judgment]` `Optional[T]` 와 `T | None` 혼용 — PEP 604 (`T | None`) 단일 표기 우선.
- `[minor][judgment]` `in list` 대규모 (수십~수백 항목) 멤버십 검사 — `set` 으로 전환.

## 누락 마무리 (축 5)

- 새 public 함수·클래스 추가 → 대응 테스트 파일 (`tests/test_{module}.py` 또는 `{module}_test.py`) 존재 확인.
- 새 의존성 import → `requirements.txt` / `pyproject.toml` 의 `dependencies` 또는 `[project.dependencies]` 등재.
- 새 모듈 도입 → 상위 패키지 `__init__.py` 재노출 컨벤션 (팀이 운영 시).

## Do-NOT (Python 특화)

- 타입 어노테이션 누락 자체를 지적 금지 — 팀 rules.md 에 강제 명시된 경우만.
- f-string vs `.format()` vs `%` 취향 지적 금지.
- 함수 길이 ≤ 30 라인 같은 임의 임계 지적 금지 — rules.md 에 임계 명시된 경우만.
