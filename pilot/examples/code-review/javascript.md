# 코드 리뷰 — JavaScript

> **참고용 예시**. 플러그인은 본 파일을 로드하지 않는다. `workspace/context/review/javascript.md` 로 복사 후 편집.

## 적용 범위

확장자: `.js`, `.jsx`, `.mjs`, `.cjs`. 변경된 hunk 에만 적용.

## Grep-friendly 위반 룰

- `[major][grep:console\.(log|debug|info)\(]` 프로덕션 코드의 console 출력 — 제거 또는 logger.
- `[major][grep:^\s*var\s+]` `var` 선언 — `let`/`const` 권장 (block scope).
- `[major][grep:\beval\s*\(]` `eval()` — 보안·성능 안티패턴, 대안 검토.
- `[major][grep:\.innerHTML\s*=]` `innerHTML` 할당 — 변수 보간 시 XSS 위험, `textContent` 또는 sanitize.
- `[minor][grep:^\s*debugger\s*;?\s*$]` `debugger` 잔존 — 제거.
- `[minor][grep:[^=!<>]==[^=]]` 느슨한 `==` — `===` 권장.
- `[minor][grep:eslint-disable\s*$]` ESLint disable 사유 누락.
- `[nit][grep:new\s+(String|Number|Boolean)\(]` 원시 wrapper 생성 — 리터럴 사용.

## Judgment-based 룰

- `[critical][judgment]` Promise 반환 함수의 `await` 누락 — race condition·예외 swallow.
- `[major][judgment]` `async` 함수의 catch 누락 — uncaught rejection.
- `[major][judgment]` 예외 catch 후 swallow (`catch {}` 또는 `catch (e) {}`) — 최소 로그 또는 재발생.
- `[major][judgment]` React: useEffect dependency array 누락·과다 — exhaustive-deps 확인.
- `[major][judgment]` React: hook 을 조건문·반복문 안에서 호출 — Rules of Hooks 위반.
- `[minor][judgment]` callback hell (3 단 이상 중첩) — `async/await` 또는 Promise chain.
- `[minor][judgment]` mutable global state 변경 — pure function 권장.

## 누락 마무리 (축 5)

- 새 `package.json` 의존성 추가 → `pnpm-lock.yaml` / `package-lock.json` / `yarn.lock` 동기 갱신 여부.
- 새 환경변수 사용 (`process.env.X`) → `.env.example` 갱신.
- 새 export → barrel (`index.js`) 갱신 (팀이 barrel 운영 시).
- 새 컴포넌트 → 대응 테스트 (`*.test.js`/`*.test.jsx`) 또는 Storybook 존재 (팀 컨벤션).

## Do-NOT (JS 특화)

- semicolon 유무 취향 지적 금지.
- arrow vs function keyword 취향 지적 금지.
- import 순서 (alphabetical, external-first 등) 취향 지적 금지 — lint 자동화 영역.
- `let` vs `const` 임의 강제 지적 금지 (rules.md 명시 시만).
