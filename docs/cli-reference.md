# CLI Reference
# CLI 参考

| Command<br>命令 | Description<br>描述 |
|---------|-------------|
| `nanobot onboard`<br>`nanobot onboard` | Initialize config & workspace at `~/.nanobot/`<br>在 `~/.nanobot/` 初始化配置和工作区 |
| `nanobot onboard --wizard`<br>`nanobot onboard --wizard` | Launch the interactive onboarding wizard<br>启动交互式入职向导 |
| `nanobot onboard -c <config> -w <workspace>`<br>`nanobot onboard -c <config> -w <workspace>` | Initialize or refresh a specific instance config and workspace<br>初始化或刷新特定实例配置和工作区 |
| `nanobot agent -m "..."`<br>`nanobot agent -m "..."` | Chat with the agent<br>与代理聊天 |
| `nanobot agent -w <workspace>`<br>`nanobot agent -w <workspace>` | Chat against a specific workspace<br>针对特定工作区聊天 |
| `nanobot agent -w <workspace> -c <config>`<br>`nanobot agent -w <workspace> -c <config>` | Chat against a specific workspace/config<br>针对特定工作区/配置进行聊天 |
| `nanobot agent`<br>`nanobot agent` | Interactive chat mode<br>互动聊天模式 |
| `nanobot agent --no-markdown`<br>`nanobot agent --no-markdown` | Show plain-text replies<br>显示纯文本回复 |
| `nanobot agent --logs`<br>`nanobot agent --logs` | Show runtime logs during chat<br>在聊天期间显示运行时日志 |
| `nanobot serve`<br>`nanobot serve` | Start the OpenAI-compatible API<br>启动OpenAI兼容的API |
| `nanobot gateway`<br>`nanobot gateway` | Start the gateway<br>启动网关 |
| `nanobot status`<br>`nanobot status` | Show status<br>显示状态 |
| `nanobot provider login openai-codex`<br>`nanobot provider login openai-codex` | OAuth login for providers<br>提供商的 OAuth 登录 |
| `nanobot channels login <channel>`<br>`nanobot channels login <channel>` | Authenticate a channel interactively<br>以交互方式验证通道 |
| `nanobot channels status`<br>`nanobot channels status` | Show channel status<br>显示通道状态 |

Interactive mode exits: `exit`, `quit`, `/exit`, `/quit`, `:q`, or `Ctrl+D`.
交互模式退出：`exit`、`quit`、`/exit`、`/quit`、`:q`或`Ctrl+D`。
