# foo — 도메인 요약

## 다중 DB

### Cross-domain Transaction Contracts

| source entry | external impact | type | location |
| --- | --- | --- | --- |
| `Foo::TaskService#cancel` | `Bar::ItemSheet` status | write | task_service.rb:44 |
