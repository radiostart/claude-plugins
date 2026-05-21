# 코드 리뷰 — TypeScript

> **참고용 예시**. 플러그인은 본 파일을 로드하지 않는다. `workspace/context/review/typescript.md` 로 복사 후 편집.
> JS 전용 룰은 `examples/code-review/javascript.md` 분리. 본 파일은 TS 타입 시스템 룰 + JS·TS 공유 런타임 룰 모두 포함.

## 적용 범위

확장자: `.ts`, `.tsx`. 변경된 hunk 에만 적용.

## Grep-friendly 위반 룰

- `[major][grep:console\.(log|debug|info)\(]` 프로덕션 코드의 console 출력 — 제거 또는 logger.
- `[major][grep://\s*@ts-ignore\s*$]` `@ts-ignore` 사유 누락 → `// @ts-expect-error: 이유` 권장.
- `[minor][grep::\s*any\b]` `any` 타입 — `unknown` 또는 구체 타입.
- `[minor][grep:as\s+any\b]` `as any` 캐스팅 — 타입 가드 또는 구체 타입.
- `[nit][grep:\bas\s+\w+\b]` 일반 type assertion — type guard 권장.
- `[minor][grep:^\s*debugger\s*;?\s*$]` `debugger` 잔존 — 제거.
- `[minor][grep:eslint-disable\s*$]` ESLint disable 사유 누락.

## Judgment-based 룰

- `[critical][judgment]` Promise 반환 함수의 await 누락 — race condition·예외 swallow.
- `[major][judgment]` `async` 함수가 명시적 `Promise<T>` 반환 타입 없이 추론 의존 (팀 컨벤션 따라).
- `[major][judgment]` 예외 catch 후 swallow (`catch {}` 또는 `catch (e) {}`) — 최소 로그.
- `[major][judgment]` React: useEffect dependency array 누락·과다 — exhaustive-deps 확인.
- `[minor][judgment]` `==` 사용 — `===` 권장.
- `[nit][judgment]` 함수 표현식 vs 선언 혼용 — 팀 컨벤션 따라.

## 누락 마무리 (축 5)

- 새 export 추가 → `index.ts` barrel 갱신 (팀이 barrel 운영 시).
- 새 `package.json` 의존성 추가 → `pnpm-lock.yaml` / `package-lock.json` 동기 갱신 여부.
- 새 환경변수 사용 → `.env.example` 갱신.
- 새 컴포넌트 (`.tsx`) → 대응 테스트 (`*.test.tsx`) 또는 Storybook (`*.stories.tsx`) 존재 (팀 컨벤션).

## Do-NOT (TS/JS 특화)

- `let` vs `const` 임의 강제 지적 금지 (rules.md 명시 시만).
- semicolon 유무 취향 지적 금지.
- arrow vs function keyword 취향 지적 금지.
- import 순서 (alphabetical, external-first 등) 취향 지적 금지 — lint 자동화 영역.
