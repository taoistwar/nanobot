# nanobot Skills
nanobot 技能

This directory contains built-in skills that extend nanobot's capabilities.
此目录包含用于扩展 nanobot 能力的内置技能。

## Skill Format
技能格式

Each skill is a directory containing a `SKILL.md` file with:
每个技能都是一个目录，其中包含带有以下内容的 `SKILL.md` 文件：
- YAML frontmatter (name, description, metadata)
- YAML frontmatter（name、description、metadata）
- Markdown instructions for the agent
- 面向 agent 的 Markdown 指令

When skills reference large local documentation or logs, prefer nanobot's built-in
`grep` / `glob` tools to narrow the search space before loading full files.
Use `grep(output_mode="count")` / `files_with_matches` for broad searches first,
use `head_limit` / `offset` to page through large result sets,
and `glob(entry_type="dirs")` when discovering directory structure matters.
当技能引用大型本地文档或日志时，优先使用 nanobot 内置的 `grep` / `glob` 工具，在加载完整文件之前缩小搜索范围。先使用 `grep(output_mode="count")` / `files_with_matches` 进行广泛搜索，使用 `head_limit` / `offset` 分页浏览大型结果集；当目录结构发现很重要时，使用 `glob(entry_type="dirs")`。

## Attribution
归属说明

These skills are adapted from [OpenClaw](https://github.com/openclaw/openclaw)'s skill system.
这些技能改编自 [OpenClaw](https://github.com/openclaw/openclaw) 的技能系统。
The skill format and metadata structure follow OpenClaw's conventions to maintain compatibility.
技能格式和 metadata 结构遵循 OpenClaw 的约定，以保持兼容性。

## Available Skills
可用技能

| Skill | Description |
|-------|-------------|
| `github` | Interact with GitHub using the `gh` CLI |
| `github` | 使用 `gh` CLI 与 GitHub 交互 |
| `weather` | Get weather info using wttr.in and Open-Meteo |
| `weather` | 使用 wttr.in 和 Open-Meteo 获取天气信息 |
| `summarize` | Summarize URLs, files, and YouTube videos |
| `summarize` | 总结 URL、文件和 YouTube 视频 |
| `tmux` | Remote-control tmux sessions |
| `tmux` | 远程控制 tmux 会话 |
| `clawhub` | Search and install skills from ClawHub registry |
| `clawhub` | 从 ClawHub 注册表搜索并安装技能 |
| `skill-creator` | Create new skills |
| `skill-creator` | 创建新技能 |
