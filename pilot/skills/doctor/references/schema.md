# doctor — 스키마 검사 모드 (`--schema`)

플러그인 구조 전용 검사. workspace 와 무관.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py --schema
```

검사 범위 SSOT: [`.claude-plugin/PLUGIN_SCHEMA_NOTES.md`](../../../../.claude-plugin/PLUGIN_SCHEMA_NOTES.md).

---

## 검사 항목

1. **`plugin.json`** — 필수·금지 키.
2. **`hooks/hooks.json`** — matcher 허용값.
3. **`skills/*/SKILL.md` · `agents/*.md`** — frontmatter.
4. **`version` ↔ git tag 일치** — 불일치는 WARN.

CI 에서 자동 실행 — `.github/workflows/validate.yml`.
