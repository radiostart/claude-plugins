"""pilot doctor — 정합성·진단·스키마 검사 패키지.

상위 `tools/doctor.py` 가 얇은 dispatcher 로 4 모듈에 라우팅한다.

- `_common`     : Result, ANSI, parse helpers, summarize/run_auto_fixes
- `integrity`   : workspace/team/project 정합성 검사 + auto-fix
- `schema`      : 플러그인 구조 검사 (--schema)
- `diagnose`    : 런타임 실패 패턴 진단 (--diagnose)

backward compat: `from doctor._common import *` 로 모든 공개 심볼을
`tools/doctor.py` 가 re-export 한다 (test 가 importlib 로 로드하는 경로 보존).
"""
