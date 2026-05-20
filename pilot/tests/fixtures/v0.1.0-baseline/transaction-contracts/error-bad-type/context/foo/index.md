# foo — 도메인 요약

## 다중 DB

### Cross-domain Transaction Contracts

| 본 도메인 entry | 외부 도메인 영향 | 변경 type | file:line |
| --- | --- | --- | --- |
| `Foo::TaskService#cancel` | `Bar::ItemSheet` status | delete | task_service.rb:44-67 |
