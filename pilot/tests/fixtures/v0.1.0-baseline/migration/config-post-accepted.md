# Workspace Config

## learn 언어 패턴

`/pilot:learn` 의 Phase 2 (Inventory) 가 진입 파일 확장자에서 언어를 추론한 뒤 본 섹션의 두 표를 lookup. 비어있으면 폴더 인접성 fallback. 사용자가 자기 프로젝트의 패턴을 정의.

### 의존성 추적

| 언어 | 의존성 추출 패턴 |
| ---- | ---------------- |
| Ruby | `require_relative` · 클래스 참조 (`OrderService`) → `app/**/order_service.rb` Glob |
| Kotlin | `import com.example.X` · `@Autowired`·`val foo: FooService` |
| TypeScript | `import { X } from "../foo"` · 상대 경로 추적 |
| Python | `from foo import X` · `import foo.bar` |
| Go | 동일 패키지 + `import "foo/bar"` |

### 역할 분류

| 역할 | 식별 패턴 |
| --- | --------- |
| routes | `config/routes.rb` 도메인 라인·`@RestController` `@RequestMapping`·`*.routes.ts` `router.use` |
| controllers | `*_controller.rb`·`< ApplicationController`·`@RestController` `@Controller`·`*.controller.ts` |
| services | `*_service.rb`·`app/services/**`·`@Service`·`*.service.ts` |
| models | `app/models/**`·`< ApplicationRecord`·`@Entity`·`*.model.ts` `*.entity.ts` |
| helpers | `app/helpers/**`·util/lib 폴더·`*Util.kt` `*Helper.kt`·`*.util.ts` `*.helper.ts` |
| other | 위 어느 것도 아님 |

## scope 카테고리

| scope 헤더 | project.md 대상 H3 | 표 헤더 |
| --- | --- | --- |
| ## Routes | Endpoints | 엔드포인트, Method, 목적 |
| ## Models | Models | Class, DB, 목적 |
| ## Services | Services | Class, 파일, 목적 |
