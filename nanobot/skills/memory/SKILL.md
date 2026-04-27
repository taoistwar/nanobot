---
name: memory
description: Two-layer memory system with Dream-managed knowledge files.
always: true
---

# Memory
记忆

## Structure
结构

- `SOUL.md` — Bot personality and communication style. **Managed by Dream.** Do NOT edit.
- `SOUL.md` — 机器人人格和沟通风格。**由 Dream 管理。**不要编辑。
- `USER.md` — User profile and preferences. **Managed by Dream.** Do NOT edit.
- `USER.md` — 用户资料和偏好。**由 Dream 管理。**不要编辑。
- `memory/MEMORY.md` — Long-term facts (project context, important events). **Managed by Dream.** Do NOT edit.
- `memory/MEMORY.md` — 长期事实（项目上下文、重要事件）。**由 Dream 管理。**不要编辑。
- `memory/history.jsonl` — append-only JSONL, not loaded into context. Prefer the built-in `grep` tool to search it.
- `memory/history.jsonl` — 仅追加的 JSONL，不会加载到上下文中。优先使用内置 `grep` 工具搜索它。

## Search Past Events
搜索过往事件

`memory/history.jsonl` is JSONL format — each line is a JSON object with `cursor`, `timestamp`, `content`.
`memory/history.jsonl` 是 JSONL 格式；每一行都是包含 `cursor`、`timestamp`、`content` 的 JSON 对象。

- For broad searches, start with `grep(..., path="memory", glob="*.jsonl", output_mode="count")` or the default `files_with_matches` mode before expanding to full content
- 对于广泛搜索，先使用 `grep(..., path="memory", glob="*.jsonl", output_mode="count")` 或默认的 `files_with_matches` 模式，再展开到完整内容
- Use `output_mode="content"` plus `context_before` / `context_after` when you need the exact matching lines
- 需要精确匹配行时，使用 `output_mode="content"` 并搭配 `context_before` / `context_after`
- Use `fixed_strings=true` for literal timestamps or JSON fragments
- 对字面量时间戳或 JSON 片段使用 `fixed_strings=true`
- Use `head_limit` / `offset` to page through long histories
- 使用 `head_limit` / `offset` 分页浏览较长历史记录
- Use `exec` only as a last-resort fallback when the built-in search cannot express what you need
- 仅在内置搜索无法表达需求时，才将 `exec` 作为最后的备用方案

Examples (replace `keyword`):
示例（替换 `keyword`）：
- `grep(pattern="keyword", path="memory/history.jsonl", case_insensitive=true)`
- `grep(pattern="keyword", path="memory/history.jsonl", case_insensitive=true)`
- `grep(pattern="2026-04-02 10:00", path="memory/history.jsonl", fixed_strings=true)`
- `grep(pattern="2026-04-02 10:00", path="memory/history.jsonl", fixed_strings=true)`
- `grep(pattern="keyword", path="memory", glob="*.jsonl", output_mode="count", case_insensitive=true)`
- `grep(pattern="keyword", path="memory", glob="*.jsonl", output_mode="count", case_insensitive=true)`
- `grep(pattern="oauth|token", path="memory", glob="*.jsonl", output_mode="content", case_insensitive=true)`
- `grep(pattern="oauth|token", path="memory", glob="*.jsonl", output_mode="content", case_insensitive=true)`

## Important
重要事项

- **Do NOT edit SOUL.md, USER.md, or MEMORY.md.** They are automatically managed by Dream.
- **不要编辑 SOUL.md、USER.md 或 MEMORY.md。**它们由 Dream 自动管理。
- If you notice outdated information, it will be corrected when Dream runs next.
- 如果你发现过时信息，Dream 下次运行时会进行修正。
- Users can view Dream's activity with the `/dream-log` command.
- 用户可以使用 `/dream-log` 命令查看 Dream 的活动。
