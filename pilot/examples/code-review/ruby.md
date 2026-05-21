# 코드 리뷰 — Ruby / Rails

> **참고용 예시**. 플러그인은 본 파일을 로드하지 않는다. `workspace/context/review/ruby.md` 로 복사 후 편집.
> Rails 룰은 본 파일의 `## Rails 특화 룰` 섹션 — 비-Rails 프로젝트는 복사 시 해당 섹션 삭제.

## 적용 범위

확장자: `.rb`, `.rake`, `.erb`, 파일명 `Gemfile` / `Rakefile`. 변경된 hunk 에만 적용.

## Grep-friendly 위반 룰

- `[major][grep:^\s*puts\s+]` 프로덕션 코드의 `puts` — `Rails.logger` / `Logger` 권장.
- `[major][grep:^\s*p\s+\w]` 디버그용 `p` 출력 잔존 — 제거.
- `[major][grep:rescue\s*$]` bare `rescue` — 구체 예외 클래스 또는 `rescue => e` + 로깅.
- `[major][grep:rescue\s+Exception\b]` `rescue Exception` — `StandardError` 권장 (시스템 시그널 흡수 방지).
- `[minor][grep:binding\.(pry|irb)|byebug]` 디버거 잔존 — 제거.
- `[minor][grep:\.send\(:]` `send(:private_method)` — public API 또는 `public_send` 권장.
- `[nit][grep:^\s*#\s*TODO\b|#\s*FIXME\b]` 새 TODO/FIXME — 티켓 ID 또는 책임자 첨부 권장.

## Judgment-based 룰

- `[major][judgment]` mutable default (`def f(x = [])`) — 함수 호출 간 공유, `nil` sentinel + 내부 초기화.
- `[major][judgment]` 블록 내 `return` — outer scope 탈출, `next`/`break` 의도 확인.
- `[minor][judgment]` `each` 후 `<<` 누적 — `map` / `reduce` 권장.
- `[minor][judgment]` 긴 method chain (`.a.b.c.d.e`) — Law of Demeter 위반, delegate 검토.

## Rails 특화 룰

- `[critical][judgment]` N+1 쿼리 — `includes`/`preload`/`eager_load` 누락. ActiveRecord 호출이 loop 안에 있으면 의심.
- `[critical][grep:\.where\(["'][^"']*#\{]` SQL injection — `where("col = #{var}")` 금지, placeholder (`where("col = ?", var)`) 사용.
- `[major][judgment]` Strong Parameters 누락 (`params.permit(...)`) — controller 의 mass assignment.
- `[major][judgment]` `before_action` 의 조건부 (`if:`/`unless:`/`only:`/`except:`) 불일치 — 컨트롤러 일관성.
- `[major][judgment]` ActiveRecord callback (`after_save`, `after_commit`) 에 부수효과 — service object 분리 검토.
- `[major][grep:\bhtml_safe\b|\braw\(]` `html_safe` / `raw` 사용 — XSS 위험, 검증 후 사용.
- `[minor][judgment]` 새 마이그레이션 — `change` 메서드 reversibility 확인 (`up`/`down` 필요 여부).
- `[minor][judgment]` ERB 안 `<%= %>` 에 사용자 입력 — `h()` / `sanitize` 검토.

## 누락 마무리 (축 5)

- 새 ActiveRecord 모델·컬럼 → `db/migrate/` 마이그레이션 파일 존재 확인.
- 새 gem 추가 → `Gemfile` 등재 + `Gemfile.lock` 동기.
- 새 controller action → `config/routes.rb` 라우트 등재.
- 새 model·service → 대응 spec (`spec/models/`, `spec/services/`) 또는 `test/` 존재 (팀 컨벤션).

## Do-NOT (Ruby 특화)

- single-quote vs double-quote 취향 지적 금지 — rules.md 명시 시만.
- `do...end` vs `{...}` 블록 형태 취향 지적 금지.
- `return` 명시 vs 암묵 취향 지적 금지.
- `Symbol#to_proc` (`&:method`) vs lambda 취향 지적 금지.
- RuboCop 자동화 영역 (라인 길이·들여쓰기) 지적 금지.
