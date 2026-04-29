# Workspace Config

## learn 언어 패턴

의존성 추출 패턴 (표 1):

| 언어 | 의존성 추출 패턴 |
| ---- | -------------- |
| Ruby | `require_relative` · 클래스 참조 |

역할 분류 패턴 (표 2):

<!-- ERROR: wide-form 4 컬럼 — 2 컬럼 (역할, 식별 패턴) 필요 -->

| 역할 | Ruby | Kotlin | TypeScript |
| ---- | ---- | ------ | ---------- |
| routes | `config/routes.rb` | `@RestController` | `*.routes.ts` |
| controllers | `*_controller.rb` | `@Controller` | `*.controller.ts` |
