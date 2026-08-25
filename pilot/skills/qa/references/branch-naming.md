# 작업 브랜치명 결정 (재작업 충돌 회피)

6-1 단계의 브랜치명 결정 알고리즘 상세. 생성·보고 흐름은 SKILL.md 본문이 SSOT.

기존 동일 base 브랜치(local + remote)를 조사한다:

```bash
git branch --all --format='%(refname:short)' \
  | sed 's#^origin/##' \
  | grep -E '^fix/{KEY}(-[0-9]+)?$' | sort -u
```

- 매칭이 **없으면** → 브랜치명 = `fix/{KEY}`.
- 매칭이 **있으면** (재작업) → 기존 suffix 의 최댓값 `N` 을 구한다 (suffix 없는
  `fix/{KEY}` 는 `N=1` 로 본다). 브랜치명 = `fix/{KEY}-{N+1}`.
  - 예: `fix/{KEY}` 만 있으면 → `fix/{KEY}-2`. `fix/{KEY}`·`fix/{KEY}-2` 가
    있으면 → `fix/{KEY}-3`. 같은 티켓 번호가 중복되지 않도록 항상 증가시킨다.
