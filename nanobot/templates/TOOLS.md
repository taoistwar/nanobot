# Tool Usage Notes
# 工具使用说明

Tool signatures are provided automatically via function calling.
工具签名会通过函数调用自动提供。
This file documents non-obvious constraints and usage patterns.
本文档记录不明显的约束和使用模式。

## exec — Safety Limits
## exec — 安全限制

- Commands have a configurable timeout (default 60s)
- 命令具有可配置的超时时间（默认 60 秒）
- Dangerous commands are blocked (rm -rf, format, dd, shutdown, etc.)
- 危险命令会被阻止（rm -rf、format、dd、shutdown 等）
- Output is truncated at 10,000 characters
- 输出会在 10,000 个字符处截断
- `restrictToWorkspace` config can limit file access to the workspace
- `restrictToWorkspace` 配置可以将文件访问限制在工作区内

## glob — File Discovery
## glob — 文件发现

- Use `glob` to find files by pattern before falling back to shell commands
- 在回退到 shell 命令之前，使用 `glob` 按模式查找文件
- Simple patterns like `*.py` match recursively by filename
- 像 `*.py` 这样的简单模式会按文件名递归匹配
- Use `entry_type="dirs"` when you need matching directories instead of files
- 当你需要匹配目录而不是文件时，使用 `entry_type="dirs"`
- Use `head_limit` and `offset` to page through large result sets
- 使用 `head_limit` 和 `offset` 对大型结果集分页
- Prefer this over `exec` when you only need file paths
- 当你只需要文件路径时，优先使用它而不是 `exec`

## grep — Content Search
## grep — 内容搜索

- Use `grep` to search file contents inside the workspace
- 使用 `grep` 搜索工作区内的文件内容
- Default behavior returns only matching file paths (`output_mode="files_with_matches"`)
- 默认行为只返回匹配的文件路径（`output_mode="files_with_matches"`）
- Supports optional `glob` filtering plus `context_before` / `context_after`
- 支持可选的 `glob` 过滤以及 `context_before` / `context_after`
- Supports `type="py"`, `type="ts"`, `type="md"` and similar shorthand filters
- 支持 `type="py"`、`type="ts"`、`type="md"` 以及类似的简写过滤器
- Use `fixed_strings=true` for literal keywords containing regex characters
- 对包含正则字符的字面量关键词使用 `fixed_strings=true`
- Use `output_mode="files_with_matches"` to get only matching file paths
- 使用 `output_mode="files_with_matches"` 仅获取匹配的文件路径
- Use `output_mode="count"` to size a search before reading full matches
- 使用 `output_mode="count"` 在读取完整匹配前估算搜索规模
- Use `head_limit` and `offset` to page across results
- 使用 `head_limit` 和 `offset` 对结果分页
- Prefer this over `exec` for code and history searches
- 对代码和历史搜索，优先使用它而不是 `exec`
- Binary or oversized files may be skipped to keep results readable
- 为保持结果可读，二进制文件或超大文件可能会被跳过

## cron — Scheduled Reminders
## cron — 定时提醒

- Please refer to cron skill for usage.
- 使用方法请参考 cron skill。
