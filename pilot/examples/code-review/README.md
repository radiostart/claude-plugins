# examples/code-review/

`@pilot-code-review` 가 워크스페이스에서 읽는 `{lang}.md` 파일의 **사전 작성된 예시**입니다.

## 위치 의미

- `${CLAUDE_PLUGIN_ROOT}/skills/context/shared/review-rules-template.md` — **빈 형식 템플릿**. `/pilot:code-review-init` 전략 B 가 워크스페이스로 복사.
- `${CLAUDE_PLUGIN_ROOT}/examples/code-review/` — **본 디렉토리**. 이미 채워진 참고 자료. `/pilot:code-review-init` 전략 A 가 복사. 플러그인은 본 디렉토리를 자동 로드하지 **않음**.

플러그인은 본 디렉토리를 컨텍스트로 읽지 않습니다. `@pilot-code-review` 의 로딩 체인은 `workspace/context/review/` 만 봅니다.

## 사용법

`/pilot:code-review-init {lang}` 으로 셋업하거나, 직접 복사:

```bash
cp ${CLAUDE_PLUGIN_ROOT}/examples/code-review/ruby.md \
   workspace/context/review/ruby.md
```

복사 후 다음을 정리:

1. 헤더의 "참고용 예시" 안내 문구 삭제
2. 사용하지 않는 프레임워크 섹션 삭제 (예: 비-Rails 프로젝트는 `## Rails 특화 룰` 제거)
3. 팀 컨벤션과 충돌하는 룰 수정·삭제
4. 팀 도메인 룰 추가

## 수록된 예시

| 언어 | 파일 | 프레임워크 섹션 |
|---|---|---|
| Python | [python.md](python.md) | (없음) |
| TypeScript | [typescript.md](typescript.md) | (없음) |
| JavaScript | [javascript.md](javascript.md) | React |
| Ruby | [ruby.md](ruby.md) | Rails |
| PHP | [php.md](php.md) | Laravel, Symfony |
| Kotlin | [kotlin.md](kotlin.md) | Android |
| Java | [java.md](java.md) | Spring |

## 빈 형식부터 시작하고 싶다면

사전 작성된 예시 없이 형식만 잡고 직접 채우려면 `review-rules-template.md` 복사:

```bash
cp ${CLAUDE_PLUGIN_ROOT}/skills/context/shared/review-rules-template.md \
   workspace/context/review/{lang}.md
```

또는 `/pilot:code-review-init {lang}` 전략 C 로 Claude 가 코드베이스 기준 contextual 룰 draft 를 생성하게 할 수 있습니다.

## 유지보수 정책

본 예시는 community best practice 스냅샷입니다. 플러그인 메인테이너가 큰 변화 (예: 새 Rails major) 시 업데이트하지만 **stale 위험 인지** — 팀 워크스페이스의 `{lang}.md` 가 실제 진실의 소스. 예시와 워크스페이스가 어긋나면 **워크스페이스가 우선**.
