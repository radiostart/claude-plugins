# 코드 리뷰 — PHP

> **참고용 예시**. 플러그인은 본 파일을 로드하지 않는다. `workspace/context/review/php.md` 로 복사 후 편집.
> Laravel/Symfony 룰은 본 파일의 `## Laravel / Symfony 특화` 섹션 — 사용 안 하는 프레임워크 섹션은 복사 시 삭제.

## 적용 범위

확장자: `.php`, `.phtml`. 변경된 hunk 에만 적용.

## Grep-friendly 위반 룰

- `[critical][grep:\beval\s*\(|\bassert\s*\(\s*\$]` `eval()` / 동적 `assert()` — RCE 위험.
- `[critical][grep:mysql_(query|connect|fetch)\(]` `mysql_*` 함수 — PHP 7+ 제거, PDO / mysqli prepared statement 사용.
- `[critical][grep:\$_(GET|POST|REQUEST|COOKIE)\[[^\]]+\][^=]*(query|exec|shell_exec|passthru|system)]` 사용자 입력 직접 실행 — SQLi / RCE.
- `[major][grep:var_dump\s*\(|print_r\s*\([^)]+\)\s*;]` 디버그 출력 잔존 — 제거 또는 logger.
- `[major][grep:@\w+\s*\(]` `@` 에러 억제 — 예외 처리 권장.
- `[major][grep:\bdie\s*\(|\bexit\s*\(]` `die`/`exit` 사용 (프레임워크 외부) — 예외 발생 권장.
- `[minor][grep:[^=!<>]==[^=]|[^=!]!=[^=]]` 느슨한 비교 — `===` / `!==` 권장 (타입 강제).
- `[minor][grep:\bextract\s*\(]` `extract()` — 변수 스코프 오염, 명시 할당.

## Judgment-based 룰

- `[critical][judgment]` SQL 문자열 보간 (`"SELECT ... $var"`) — prepared statement / bind 사용.
- `[major][judgment]` `try/catch` 후 swallow (`catch (\Exception $e) {}`) — 최소 로그 또는 재발생.
- `[major][judgment]` superglobal (`$_GET`, `$_POST`) 직접 사용 — request 객체·validator 레이어 통과.
- `[minor][judgment]` `null` 반환 vs 예외 혼용 — 함수 시그니처 일관성 (return type `?T` 명시).
- `[minor][judgment]` `array_*` 함수 인자 순서 헷갈림 (`needle, haystack` vs `haystack, needle`) — 검증.

## Laravel / Symfony 특화 (프레임워크 감지 시)

- `[critical][judgment]` Laravel: Eloquent N+1 — `with()` eager loading 누락.
- `[major][judgment]` Laravel: mass assignment — `$fillable` / `$guarded` 정의 확인.
- `[major][grep:\{!!\s*\$]` Laravel Blade: `{!! $var !!}` raw 출력 — XSS 위험, `{{ $var }}` escape 우선.
- `[major][judgment]` Symfony: 의존성 주입 누락 — `new Service()` 직접 호출, container 통과.

## 누락 마무리 (축 5)

- 새 의존성 → `composer.json` 등재 + `composer.lock` 동기.
- 새 모델 변경 동반 가능 패턴 → Laravel `database/migrations/` · Doctrine `migrations/` 파일 확인.
- 새 환경변수 (`env('X')` / `getenv('X')`) → `.env.example` 갱신.
- 새 route → `routes/web.php` / `routes/api.php` 또는 컨트롤러 어노테이션 등재.

## Do-NOT (PHP 특화)

- single-quote vs double-quote 취향 지적 금지.
- PSR-12 들여쓰기·줄바꿈 취향 지적 금지 — `phpcs` 자동화 영역.
- short echo (`<?=`) 취향 지적 금지.
- `array()` vs `[]` 취향 지적 금지 (rules.md 명시 시만).
