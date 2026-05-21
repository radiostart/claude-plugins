# 코드 리뷰 — Java

> **참고용 예시**. 플러그인은 본 파일을 로드하지 않는다. `workspace/context/review/java.md` 로 복사 후 편집.
> Spring 룰은 본 파일의 `## Spring 특화` 섹션 — Spring 미사용 프로젝트는 복사 시 해당 섹션 삭제.

## 적용 범위

확장자: `.java`. 변경된 hunk 에만 적용.

## Grep-friendly 위반 룰

- `[major][grep:System\.out\.print(ln)?\(]` `System.out` 출력 — `Logger` (SLF4J / Log4j) 권장.
- `[major][grep:catch\s*\(\s*Exception\s+\w+\s*\)\s*\{\s*\}]` 예외 swallow — 최소 로그 또는 재발생.
- `[major][grep:catch\s*\(\s*Throwable\s+]` `Throwable` catch — `Error` 흡수 위험, `Exception` 권장.
- `[major][grep:\.printStackTrace\s*\(\)]` `e.printStackTrace()` — logger 사용.
- `[minor][grep:@SuppressWarnings\(["'][^"']+["']\)\s*$]` `@SuppressWarnings` 사유 누락 — 주석 첨부.
- `[minor][grep:new\s+(Integer|Long|Double|Float|Boolean)\s*\(]` Boxed 생성자 — `valueOf` 또는 autoboxing 권장 (Java 9+ deprecated).
- `[nit][grep:\bnew\s+Date\s*\(\)]` `java.util.Date` — `java.time` (LocalDateTime / Instant) 권장.

## Judgment-based 룰

- `[critical][judgment]` 동시성: shared mutable state 에 `synchronized` / `Lock` / `Atomic*` 누락.
- `[major][judgment]` resource 누수: `InputStream` / `Connection` / `Statement` 에 try-with-resources 누락.
- `[major][judgment]` `null` 반환 vs `Optional<T>` 혼용 — 시그니처 일관성.
- `[major][judgment]` `equals` / `hashCode` 한쪽만 override — contract 위반.
- `[minor][judgment]` `Collections.unmodifiableList` 누락한 getter — defensive copy 검토.
- `[minor][judgment]` `Stream` 종단 연산 누락 (`collect` / `forEach`) — lazy 평가 미실행.

## Spring 특화 (프레임워크 감지 시)

- `[critical][judgment]` `@Transactional` 메서드의 self-invocation — proxy bypass, 별도 빈 분리.
- `[major][judgment]` `@Autowired` 필드 주입 — 생성자 주입 권장 (테스트·불변성).
- `[major][grep:@RequestMapping\s*\([^)]*\)\s*$]` `@RequestMapping` 의 HTTP method 누락 — `@GetMapping` / `@PostMapping` 등 명시.
- `[major][judgment]` `@Transactional(readOnly=false)` 광범위 적용 — read-only 메서드 분리.
- `[major][judgment]` JPA N+1 — `@EntityGraph` 또는 `JOIN FETCH` 누락.

## 누락 마무리 (축 5)

- 새 의존성 → `pom.xml` `<dependencies>` 또는 `build.gradle` `dependencies` 등재.
- 새 public class → 패키지 경로·접근 제한자 일관성.
- 새 entity·table 변경 → Flyway / Liquibase 마이그레이션 (`db/migration/V*.sql`) 존재.
- 새 controller endpoint → API 문서 (OpenAPI / Swagger) 또는 `@Operation` 어노테이션 (팀 컨벤션).

## Do-NOT (Java 특화)

- `var` (Java 10+) vs 명시 타입 취향 지적 금지.
- lambda vs method reference 취향 지적 금지.
- `final` 변수 강제 지적 금지 (rules.md 명시 시만).
- Checkstyle 자동화 영역 (들여쓰기·임포트 순서) 지적 금지.
