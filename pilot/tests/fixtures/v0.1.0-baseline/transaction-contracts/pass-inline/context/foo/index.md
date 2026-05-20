# foo — 도메인 요약

## 다중 DB

foo 도메인은 `FooRecord` (foo DB) 를 primary 로 사용한다.
bar 도메인 연동 시 cross-domain transaction 발생.

### Cross-domain Transaction Contracts

| 본 도메인 entry | 외부 도메인 영향 | 변경 type | file:line |
| --- | --- | --- | --- |
| `Foo::TaskService#cancel` | `Bar::ItemSheet` status | write | task_service.rb:44-67 |
| `Foo::BatchService#execute` | `Bar::LogRecord` entry | create | batch_service.rb:12-30 |
