---
name: clawhub
description: Search and install agent skills from ClawHub, the public skill registry.
homepage: https://clawhub.ai
metadata: {"nanobot":{"emoji":"🦞"}}
---

# ClawHub
ClawHub

Public skill registry for AI agents. Search by natural language (vector search).
面向 AI agent 的公共技能注册表。可通过自然语言搜索（向量搜索）。

## When to use
何时使用

Use this skill when the user asks any of:
当用户提出以下任一请求时使用此技能：
- "find a skill for …"
- “查找用于……的技能”
- "search for skills"
- “搜索技能”
- "install a skill"
- “安装技能”
- "what skills are available?"
- “有哪些可用技能？”
- "update my skills"
- “更新我的技能”

## Search
搜索

```bash
npx --yes clawhub@latest search "web scraping" --limit 5
```

## Install
安装

```bash
npx --yes clawhub@latest install <slug> --workdir ~/.nanobot/workspace
```

Replace `<slug>` with the skill name from search results. This places the skill into `~/.nanobot/workspace/skills/`, where nanobot loads workspace skills from. Always include `--workdir`.
将 `<slug>` 替换为搜索结果中的技能名称。这会把技能放入 `~/.nanobot/workspace/skills/`，nanobot 会从该位置加载工作区技能。始终包含 `--workdir`。

## Update
更新

```bash
npx --yes clawhub@latest update --all --workdir ~/.nanobot/workspace
```

## List installed
列出已安装项

```bash
npx --yes clawhub@latest list --workdir ~/.nanobot/workspace
```

## Notes
注意事项

- Requires Node.js (`npx` comes with it).
- 需要 Node.js（`npx` 会随 Node.js 提供）。
- No API key needed for search and install.
- 搜索和安装不需要 API key。
- Login (`npx --yes clawhub@latest login`) is only required for publishing.
- 只有发布时才需要登录（`npx --yes clawhub@latest login`）。
- `--workdir ~/.nanobot/workspace` is critical — without it, skills install to the current directory instead of the nanobot workspace.
- `--workdir ~/.nanobot/workspace` 很关键；没有它时，技能会安装到当前目录，而不是 nanobot 工作区。
- After install, remind the user to start a new session to load the skill.
- 安装后，提醒用户启动新会话以加载该技能。
