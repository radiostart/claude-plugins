# 코드 리뷰 — Kotlin

> **참고용 예시**. 플러그인은 본 파일을 로드하지 않는다. `workspace/context/review/kotlin.md` 로 복사 후 편집.
> Android 룰은 본 파일의 `## Android 특화` 섹션 — 서버사이드 프로젝트는 복사 시 해당 섹션 삭제.

## 적용 범위

확장자: `.kt`, `.kts`. 변경된 hunk 에만 적용.

## Grep-friendly 위반 룰

- `[major][grep:\bprintln\s*\(]` 프로덕션 코드의 `println` — `Logger` / `kotlin-logging` 권장.
- `[major][grep:!!\s*[.\[]|!!\s*$]` non-null assertion (`!!`) — `?.` / `?:` / `requireNotNull` 권장.
- `[major][grep:\bAny\?\s*[=,)]]` `Any?` 타입 — 구체 타입 또는 generic.
- `[minor][grep:@Suppress\(["'][^"']+["']\)\s*$]` `@Suppress` 사유 누락 — 주석으로 이유 첨부.
- `[minor][grep:\bTODO\(\)]` `TODO()` 호출 잔존 — 구현 또는 명시 예외.
- `[nit][grep:^\s*var\s+\w+\s*=]` 지역 `var` — `val` 우선 검토 (가변 필요한지).

## Judgment-based 룰

- `[critical][judgment]` `runBlocking` 프로덕션 사용 — coroutine scope 통합, `suspend` 함수.
- `[major][judgment]` `GlobalScope.launch` — structured concurrency 위반, `viewModelScope` / `lifecycleScope` 사용.
- `[major][judgment]` `lateinit` 미초기화 위험 — `Delegates.notNull` 또는 nullable 검토.
- `[major][judgment]` `Exception` 광범위 catch — 구체 예외, `CancellationException` 재발생 필수.
- `[minor][judgment]` `let`/`also`/`apply`/`run`/`with` 의도 안 맞는 선택 — 가독성 영향.
- `[minor][judgment]` data class 가 너무 많은 프로퍼티 (>7) — value object 분리 검토.

## Android 특화 (감지 시)

- `[major][judgment]` Activity·Fragment lifecycle 외부에서 `findViewById` 호출 — view binding 권장.
- `[major][judgment]` Context leak — Activity Context 를 long-living 객체에 보유.
- `[major][judgment]` `runOnUiThread` / `Handler(Looper.getMainLooper())` 남용 — coroutine `Dispatchers.Main`.

## 누락 마무리 (축 5)

- 새 의존성 → `build.gradle.kts` / `build.gradle` 의 `dependencies` 블록 + 버전 카탈로그 (`libs.versions.toml`) 동기.
- 새 public API (`fun`, `class`, `object`) → KDoc 권장 (팀 컨벤션 시).
- 새 sealed class 분기 추가 → 기존 `when` exhaustive 확인 (`Grep` 으로 호출 위치 검사).
- 새 Android `Activity` / `Fragment` → `AndroidManifest.xml` 등재.

## Do-NOT (Kotlin 특화)

- expression body (`fun f() = ...`) vs block body 취향 지적 금지.
- trailing comma 유무 취향 지적 금지.
- import alias 사용 취향 지적 금지.
- ktlint·detekt 자동화 영역 (라인 길이·들여쓰기) 지적 금지.
