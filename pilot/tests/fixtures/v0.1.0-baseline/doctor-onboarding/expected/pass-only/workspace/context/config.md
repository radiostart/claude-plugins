# workspace config

## 설정

| 키 | 값 |
| --- | --- |
| commit_scopes | feat,fix,refactor,skills,chore,docs,test,wip |

## learn 언어 패턴

| 언어 | 의존성 추출 패턴 |
| --- | --- |
| python | import {module} · from {module} import |

| 역할 | 식별 패턴 |
| --- | --- |
| service | services/ |

## scope 카테고리

| scope 헤더 | project.md 대상 H3 | 표 헤더 |
| --- | --- | --- |
| ## Services | Services | Class / 파일 / 목적 |

## Ignore

| 패턴 | 사유 |
| --- | --- |
| node_modules/ | 외부 의존성 |
