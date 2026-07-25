"""pilot doctor — 정합성·스키마 검사 패키지.

상위 `tools/doctor.py` 가 얇은 dispatcher 로 하위 모듈에 라우팅한다.

- `_common`     : Result, ANSI, parse helpers, summarize/run_auto_fixes
- `integrity`   : workspace/team/project 정합성 검사 + auto-fix
- `schema`      : 플러그인 구조 검사 (--schema)

패키지 함수를 직접 테스트하려면 `doctor.integrity`·`doctor._common` 을
sys.path 경유로 직접 import 한다 (`tools/doctor.py` 는 기능상 필요한
심볼만 노출 — wildcard-style backward-compat re-export 없음).
"""
