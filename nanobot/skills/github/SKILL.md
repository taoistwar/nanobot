---
name: github
description: "Interact with GitHub using the `gh` CLI. Use `gh issue`, `gh pr`, `gh run`, and `gh api` for issues, PRs, CI runs, and advanced queries."
metadata: {"nanobot":{"emoji":"🐙","requires":{"bins":["gh"]},"install":[{"id":"brew","kind":"brew","formula":"gh","bins":["gh"],"label":"Install GitHub CLI (brew)"},{"id":"apt","kind":"apt","package":"gh","bins":["gh"],"label":"Install GitHub CLI (apt)"}]}}
---

# GitHub Skill
GitHub 技能

Use the `gh` CLI to interact with GitHub. Always specify `--repo owner/repo` when not in a git directory, or use URLs directly.
使用 `gh` CLI 与 GitHub 交互。不在 git 目录中时，始终指定 `--repo owner/repo`，或者直接使用 URL。

## Pull Requests
拉取请求

Check CI status on a PR:
检查 PR 上的 CI 状态：
```bash
gh pr checks 55 --repo owner/repo
```

List recent workflow runs:
列出最近的 workflow 运行记录：
```bash
gh run list --repo owner/repo --limit 10
```

View a run and see which steps failed:
查看一次运行并了解哪些步骤失败：
```bash
gh run view <run-id> --repo owner/repo
```

View logs for failed steps only:
仅查看失败步骤的日志：
```bash
gh run view <run-id> --repo owner/repo --log-failed
```

## API for Advanced Queries
用于高级查询的 API

The `gh api` command is useful for accessing data not available through other subcommands.
`gh api` 命令适合访问其他子命令无法获取的数据。

Get PR with specific fields:
获取包含特定字段的 PR：
```bash
gh api repos/owner/repo/pulls/55 --jq '.title, .state, .user.login'
```

## JSON Output
JSON 输出

Most commands support `--json` for structured output.  You can use `--jq` to filter:
大多数命令都支持使用 `--json` 输出结构化数据。你可以使用 `--jq` 进行过滤：

```bash
gh issue list --repo owner/repo --json number,title --jq '.[] | "\(.number): \(.title)"'
```
