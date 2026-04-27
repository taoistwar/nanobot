![cover-v5-optimized](./images/GitHub_README.png)

<div align="center">
  <p>
    <a href="https://pypi.org/project/nanobot-ai/"><img src="https://img.shields.io/pypi/v/nanobot-ai" alt="PyPI"></a>
    <a href="https://pepy.tech/project/nanobot-ai"><img src="https://static.pepy.tech/badge/nanobot-ai" alt="Downloads"></a>
    <img src="https://img.shields.io/badge/python-≥3.11-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <a href="https://github.com/HKUDS/nanobot/graphs/commit-activity" target="_blank">
        <img alt="Commits last month" src="https://img.shields.io/github/commit-activity/m/HKUDS/nanobot?labelColor=%20%2332b583&color=%20%2312b76a"></a>
    <a href="https://github.com/HKUDS/nanobot/issues?q=is%3Aissue%20is%3Aclosed" target="_blank">
        <img alt="Issues closed" src="https://img.shields.io/github/issues-search?query=repo%3AHKUDS%2Fnanobot%20is%3Aissue%20is%3Aclosed&label=issues%20closed&labelColor=%20%237d89b0&color=%20%235d6b98"></a>
    <a href="https://twitter.com/intent/follow?screen_name=nanobot_project" target="_blank">
        <img src="https://img.shields.io/twitter/follow/nanobot_project?logo=X&color=%20%23f5f5f5" alt="follow on X(Twitter)"></a>
    <a href="https://nanobot.wiki/docs/latest/getting-started/nanobot-overview"><img src="https://img.shields.io/badge/Docs-nanobot.wiki-blue?style=flat&logo=readthedocs&logoColor=white" alt="Docs"></a>
    <a href="./COMMUNICATION.md"><img src="https://img.shields.io/badge/Feishu-Group-E9DBFC?style=flat&logo=feishu&logoColor=white" alt="Feishu"></a>
    <a href="./COMMUNICATION.md"><img src="https://img.shields.io/badge/WeChat-Group-C5EAB4?style=flat&logo=wechat&logoColor=white" alt="WeChat"></a>
    <a href="https://discord.gg/MnCvHqpUGB"><img src="https://img.shields.io/badge/Discord-Community-5865F2?style=flat&logo=discord&logoColor=white" alt="Discord"></a>
  </p>
</div>

🐈 **nanobot** is an open-source and ultra-lightweight AI agent in the spirit of [OpenClaw](https://github.com/openclaw/openclaw), [Claude Code](https://www.anthropic.com/claude-code), and [Codex](https://www.openai.com/codex/). It keeps the core agent loop small and readable while still supporting chat channels, memory, MCP and practical deployment paths, so you can go from local setup to a long-running personal agent with minimal overhead.

**nanobot** 是一个开源且超轻量的 AI agent，延续了 [OpenClaw](https://github.com/openclaw/openclaw)、[Claude Code](https://www.anthropic.com/claude-code) 和 [Codex](https://www.openai.com/codex/) 的理念。它保持核心 agent loop 小巧且可读，同时仍支持 chat channels、memory、MCP 和实用部署路径，让你能以极低开销从本地设置走向长期运行的个人 agent。

## 📢 News

## 新闻

- **2026-04-21** 🚀 Released **v0.1.5.post2** — Windows & Python 3.14 support, Office document reading, SSE streaming for the OpenAI-compatible API, and stronger reliability across sessions, memory, and channels. Please see [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.5.post2) for details.<br>发布 **v0.1.5.post2**：支持 Windows 与 Python 3.14、Office 文档读取、OpenAI-compatible API 的 SSE streaming，并增强 sessions、memory 和 channels 的可靠性。详情请见 [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.5.post2)。
- **2026-04-20** 🎨 Kimi K2.6 support, Telegram long-message split, WebUI typography & dark-mode polish.<br>支持 Kimi K2.6，Telegram 长消息拆分，WebUI 字体排版与暗色模式打磨。
- **2026-04-19** 🌐 WebUI i18n locale switcher, atomic session writes with auto-repair.<br>WebUI i18n locale 切换器，带自动修复的 atomic session 写入。
- **2026-04-18** 🧪 Initial WebUI chat, smarter setup wizard menus, WebSocket multi-chat multiplexing.<br>初版 WebUI chat，更智能的 setup wizard 菜单，WebSocket 多 chat 复用。
- **2026-04-17** 🪟 Windows & Python 3.14 CI, Dream line-age memory, email self-loop guard.<br>Windows 与 Python 3.14 CI，Dream line-age memory，email 自循环防护。
- **2026-04-16** 📡 SSE streaming for OpenAI-compatible API, Discord channel allow-list.<br>OpenAI-compatible API 的 SSE streaming，Discord channel allow-list。
- **2026-04-15** 🎛️ LM Studio & nullable API keys, MiniMax thinking endpoint, runtime SelfTool.<br>LM Studio 与可为空的 API keys，MiniMax thinking endpoint，runtime SelfTool。
- **2026-04-14** 🚀 Released **v0.1.5.post1** — Dream skill discovery, mid-turn follow-up injection, WebSocket channel, and deeper channel integrations. Please see [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.5.post1) for details.<br>发布 **v0.1.5.post1**：Dream skill discovery、回合中 follow-up 注入、WebSocket channel，以及更深入的 channel integrations。详情请见 [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.5.post1)。
- **2026-04-13** 🛡️ Agent turn hardened — user messages persisted early, auto-compact skips active tasks.<br>Agent turn 加固：用户消息提前持久化，auto-compact 跳过活动任务。
- **2026-04-12** 🔒 Lark global domain support, Dream learns discovered skills, shell sandbox tightened.<br>支持 Lark global domain，Dream 学习已发现 skills，shell sandbox 加固。
- **2026-04-11** ⚡ Context compact shrinks sessions on the fly; Kagi web search; QQ & WeCom full media.<br>Context compact 动态压缩 sessions；Kagi web search；QQ 与 WeCom 完整媒体支持。

<details>
<summary>Earlier news</summary>

早期新闻

- **2026-04-10** 📓 Notebook editing tool, multiple MCP servers, Feishu streaming & done-emoji.<br>Notebook editing tool，多个 MCP servers，Feishu streaming 与 done-emoji。
- **2026-04-09** 🔌 WebSocket channel, unified cross-channel session, `disabled_skills` config.<br>WebSocket channel，统一 cross-channel session，`disabled_skills` 配置。
- **2026-04-08** 📤 API file uploads, OpenAI reasoning auto-routing with Responses fallback.<br>API 文件上传，带 Responses fallback 的 OpenAI reasoning 自动路由。
- **2026-04-07** 🧠 Anthropic adaptive thinking, MCP resources & prompts exposed as tools.<br>Anthropic adaptive thinking，MCP resources 与 prompts 作为 tools 暴露。
- **2026-04-06** 🛰️ Langfuse observability, unified Whisper transcription, email attachments.<br>Langfuse observability，统一 Whisper transcription，email attachments。
- **2026-04-05** 🚀 Released **v0.1.5** — sturdier long-running tasks, Dream two-stage memory, production-ready sandboxing and programming Agent SDK. Please see [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.5) for details.<br>发布 **v0.1.5**：更稳健的长期运行任务、Dream two-stage memory、生产就绪 sandboxing 和 programming Agent SDK。详情请见 [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.5)。
- **2026-04-04** 🚀 Jinja2 response templates, Dream memory hardened, smarter retry handling.<br>Jinja2 response templates，Dream memory 加固，更智能的 retry handling。
- **2026-04-03** 🧠 Xiaomi MiMo provider, chain-of-thought reasoning visible, Telegram UX polish.<br>Xiaomi MiMo provider，可见 chain-of-thought reasoning，Telegram UX 打磨。
- **2026-04-02** 🧱 Long-running tasks run more reliably — core runtime hardening.<br>长期运行任务更可靠：core runtime 加固。
- **2026-04-01** 🔑 GitHub Copilot auth restored; stricter workspace paths; OpenRouter Claude caching fix.<br>恢复 GitHub Copilot auth；更严格的 workspace paths；OpenRouter Claude caching 修复。
- **2026-03-31** 🛰️ WeChat multimodal alignment, Discord/Matrix polish, Python SDK facade, MCP and tool fixes.<br>WeChat multimodal 对齐，Discord/Matrix 打磨，Python SDK facade，MCP 与 tool 修复。
- **2026-03-30** 🧩 OpenAI-compatible API tightened; composable agent lifecycle hooks.<br>OpenAI-compatible API 加固；可组合 agent lifecycle hooks。
- **2026-03-29** 💬 WeChat voice, typing, QR/media resilience; fixed-session OpenAI-compatible API.<br>WeChat voice、typing、QR/media 韧性；fixed-session OpenAI-compatible API。
- **2026-03-28** 📚 Provider docs refresh; skill template wording fix.<br>Provider docs 刷新；skill template 文案修复。
- **2026-03-27** 🚀 Released **v0.1.4.post6** — architecture decoupling, litellm removal, end-to-end streaming, WeChat channel, and a security fix. Please see [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4.post6) for details.<br>发布 **v0.1.4.post6**：架构解耦、移除 litellm、end-to-end streaming、WeChat channel，以及一项安全修复。详情请见 [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4.post6)。
- **2026-03-26** 🏗️ Agent runner extracted and lifecycle hooks unified; stream delta coalescing at boundaries.<br>提取 Agent runner 并统一 lifecycle hooks；在边界处合并 stream delta。
- **2026-03-25** 🌏 StepFun provider, configurable timezone, Gemini thought signatures.<br>StepFun provider，可配置 timezone，Gemini thought signatures。
- **2026-03-24** 🔧 WeChat compatibility, Feishu CardKit streaming, test suite restructured.<br>WeChat 兼容性，Feishu CardKit streaming，test suite 重构。
- **2026-03-23** 🔧 Command routing refactored for plugins, WhatsApp/WeChat media, unified channel login CLI.<br>为 plugins 重构 command routing，WhatsApp/WeChat media，统一 channel login CLI。
- **2026-03-22** ⚡ End-to-end streaming, WeChat channel, Anthropic cache optimization, `/status` command.<br>End-to-end streaming，WeChat channel，Anthropic cache 优化，`/status` 命令。
- **2026-03-21** 🔒 Replace `litellm` with native `openai` + `anthropic` SDKs. Please see [commit](https://github.com/HKUDS/nanobot/commit/3dfdab7).<br>将 `litellm` 替换为原生 `openai` + `anthropic` SDKs。请见 [commit](https://github.com/HKUDS/nanobot/commit/3dfdab7)。
- **2026-03-20** 🧙 Interactive setup wizard — pick your provider, model autocomplete, and you're good to go.<br>交互式 setup wizard：选择 provider，model autocomplete，然后即可开始。
- **2026-03-19** 💬 Telegram gets more resilient under load; Feishu now renders code blocks properly.<br>Telegram 在负载下更有韧性；Feishu 现在能正确渲染代码块。
- **2026-03-18** 📷 Telegram can now send media via URL. Cron schedules show human-readable details.<br>Telegram 现在可通过 URL 发送媒体。Cron schedules 显示人类可读详情。
- **2026-03-17** ✨ Feishu formatting glow-up, Slack reacts when done, custom endpoints support extra headers, and image handling is more reliable.<br>Feishu 格式显示升级，Slack 完成后响应，custom endpoints 支持 extra headers，image handling 更可靠。
- **2026-03-16** 🚀 Released **v0.1.4.post5** — a refinement-focused release with stronger reliability and channel support, and a more dependable day-to-day experience. Please see [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4.post5) for details.<br>发布 **v0.1.4.post5**：一个聚焦打磨的版本，提供更强可靠性和 channel support，以及更可靠的日常体验。详情请见 [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4.post5)。
- **2026-03-15** 🧩 DingTalk rich media, smarter built-in skills, and cleaner model compatibility.<br>DingTalk rich media，更智能的 built-in skills，更清晰的 model compatibility。
- **2026-03-14** 💬 Channel plugins, Feishu replies, and steadier MCP, QQ, and media handling.<br>Channel plugins，Feishu replies，以及更稳定的 MCP、QQ 和 media handling。
- **2026-03-13** 🌐 Multi-provider web search, LangSmith, and broader reliability improvements.<br>Multi-provider web search，LangSmith，以及更广泛的可靠性改进。
- **2026-03-12** 🚀 VolcEngine support, Telegram reply context, `/restart`, and sturdier memory.<br>支持 VolcEngine，Telegram reply context，`/restart`，以及更稳健的 memory。
- **2026-03-11** 🔌 WeCom, Ollama, cleaner discovery, and safer tool behavior.<br>WeCom、Ollama，更清晰的 discovery，以及更安全的 tool behavior。
- **2026-03-10** 🧠 Token-based memory, shared retries, and cleaner gateway and Telegram behavior.<br>Token-based memory，共享 retries，以及更清晰的 gateway 和 Telegram behavior。
- **2026-03-09** 💬 Slack thread polish and better Feishu audio compatibility.<br>Slack thread 打磨和更好的 Feishu audio compatibility。
- **2026-03-08** 🚀 Released **v0.1.4.post4** — a reliability-packed release with safer defaults, better multi-instance support, sturdier MCP, and major channel and provider improvements. Please see [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4.post4) for details.<br>发布 **v0.1.4.post4**：一个可靠性增强版本，包含更安全默认值、更好的 multi-instance support、更稳健的 MCP，以及主要 channel 和 provider 改进。详情请见 [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4.post4)。
- **2026-03-07** 🚀 Azure OpenAI provider, WhatsApp media, QQ group chats, and more Telegram/Feishu polish.<br>Azure OpenAI provider，WhatsApp media，QQ group chats，以及更多 Telegram/Feishu 打磨。
- **2026-03-06** 🪄 Lighter providers, smarter media handling, and sturdier memory and CLI compatibility.<br>更轻量的 providers，更智能的 media handling，以及更稳健的 memory 和 CLI compatibility。
- **2026-03-05** ⚡️ Telegram draft streaming, MCP SSE support, and broader channel reliability fixes.<br>Telegram draft streaming，MCP SSE support，以及更广泛的 channel reliability 修复。
- **2026-03-04** 🛠️ Dependency cleanup, safer file reads, and another round of test and Cron fixes.<br>Dependency cleanup，更安全的 file reads，以及又一轮 test 和 Cron 修复。
- **2026-03-03** 🧠 Cleaner user-message merging, safer multimodal saves, and stronger Cron guards.<br>更清晰的 user-message merging，更安全的 multimodal saves，以及更强的 Cron guards。
- **2026-03-02** 🛡️ Safer default access control, sturdier Cron reloads, and cleaner Matrix media handling.<br>更安全的默认 access control，更稳健的 Cron reloads，以及更清晰的 Matrix media handling。
- **2026-03-01** 🌐 Web proxy support, smarter Cron reminders, and Feishu rich-text parsing improvements.<br>Web proxy support，更智能的 Cron reminders，以及 Feishu rich-text parsing 改进。
- **2026-02-28** 🚀 Released **v0.1.4.post3** — cleaner context, hardened session history, and smarter agent. Please see [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4.post3) for details.<br>发布 **v0.1.4.post3**：更清晰的 context、加固的 session history，以及更智能的 agent。详情请见 [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4.post3)。
- **2026-02-27** 🧠 Experimental thinking mode support, DingTalk media messages, Feishu and QQ channel fixes.<br>支持实验性 thinking mode，DingTalk media messages，Feishu 和 QQ channel 修复。
- **2026-02-26** 🛡️ Session poisoning fix, WhatsApp dedup, Windows path guard, Mistral compatibility.<br>Session poisoning 修复，WhatsApp dedup，Windows path guard，Mistral compatibility。
- **2026-02-25** 🧹 New Matrix channel, cleaner session context, auto workspace template sync.<br>新增 Matrix channel，更清晰的 session context，auto workspace template sync。
- **2026-02-24** 🚀 Released **v0.1.4.post2** — a reliability-focused release with a redesigned heartbeat, prompt cache optimization, and hardened provider & channel stability. See [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4.post2) for details.<br>发布 **v0.1.4.post2**：聚焦可靠性的版本，包含重新设计的 heartbeat、prompt cache optimization，以及加固的 provider 与 channel stability。详情请见 [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4.post2)。
- **2026-02-23** 🔧 Virtual tool-call heartbeat, prompt cache optimization, Slack mrkdwn fixes.<br>Virtual tool-call heartbeat，prompt cache optimization，Slack mrkdwn 修复。
- **2026-02-22** 🛡️ Slack thread isolation, Discord typing fix, agent reliability improvements.<br>Slack thread isolation，Discord typing 修复，agent reliability 改进。
- **2026-02-21** 🎉 Released **v0.1.4.post1** — new providers, media support across channels, and major stability improvements. See [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4.post1) for details.<br>发布 **v0.1.4.post1**：新增 providers、跨 channels 的 media support，以及重大稳定性改进。详情请见 [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4.post1)。
- **2026-02-20** 🐦 Feishu now receives multimodal files from users. More reliable memory under the hood.<br>Feishu 现在可接收用户的 multimodal files。底层 memory 更可靠。
- **2026-02-19** ✨ Slack now sends files, Discord splits long messages, and subagents work in CLI mode.<br>Slack 现在可发送 files，Discord 拆分长消息，subagents 可在 CLI mode 中工作。
- **2026-02-18** ⚡️ nanobot now supports VolcEngine, MCP custom auth headers, and Anthropic prompt caching.<br>nanobot 现在支持 VolcEngine、MCP custom auth headers 和 Anthropic prompt caching。
- **2026-02-17** 🎉 Released **v0.1.4** — MCP support, progress streaming, new providers, and multiple channel improvements. Please see [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4) for details.<br>发布 **v0.1.4**：MCP support、progress streaming、新 providers，以及多个 channel 改进。详情请见 [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4)。
- **2026-02-16** 🦞 nanobot now integrates a [ClawHub](https://clawhub.ai) skill — search and install public agent skills.<br>nanobot 现在集成 [ClawHub](https://clawhub.ai) skill，可搜索并安装 public agent skills。
- **2026-02-15** 🔑 nanobot now supports OpenAI Codex provider with OAuth login support.<br>nanobot 现在支持带 OAuth login support 的 OpenAI Codex provider。
- **2026-02-14** 🔌 nanobot now supports MCP! See [MCP section](#mcp-model-context-protocol) for details.<br>nanobot 现在支持 MCP！详情请见 [MCP section](#mcp-model-context-protocol)。
- **2026-02-13** 🎉 Released **v0.1.3.post7** — includes security hardening and multiple improvements. **Please upgrade to the latest version to address security issues**. See [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.3.post7) for more details.<br>发布 **v0.1.3.post7**：包含安全加固和多项改进。**请升级到最新版本以解决安全问题**。更多详情请见 [release notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.3.post7)。
- **2026-02-12** 🧠 Redesigned memory system — Less code, more reliable. Join the [discussion](https://github.com/HKUDS/nanobot/discussions/566) about it!<br>重新设计 memory system：代码更少，更可靠。欢迎加入相关 [discussion](https://github.com/HKUDS/nanobot/discussions/566)！
- **2026-02-11** ✨ Enhanced CLI experience and added MiniMax support!<br>增强 CLI 体验并添加 MiniMax support！
- **2026-02-10** 🎉 Released **v0.1.3.post6** with improvements! Check the updates [notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.3.post6) and our [roadmap](https://github.com/HKUDS/nanobot/discussions/431).<br>发布包含改进的 **v0.1.3.post6**！查看更新 [notes](https://github.com/HKUDS/nanobot/releases/tag/v0.1.3.post6) 和我们的 [roadmap](https://github.com/HKUDS/nanobot/discussions/431)。
- **2026-02-09** 💬 Added Slack, Email, and QQ support — nanobot now supports multiple chat platforms!<br>新增 Slack、Email 和 QQ support：nanobot 现在支持多个 chat platforms！
- **2026-02-08** 🔧 Refactored Providers—adding a new LLM provider now takes just 2 simple steps! Check [here](#providers).<br>重构 Providers：添加新的 LLM provider 现在只需 2 个简单步骤！请查看 [here](#providers)。
- **2026-02-07** 🚀 Released **v0.1.3.post5** with Qwen support & several key improvements! Check [here](https://github.com/HKUDS/nanobot/releases/tag/v0.1.3.post5) for details.<br>发布 **v0.1.3.post5**，包含 Qwen support 和若干关键改进！详情请查看 [here](https://github.com/HKUDS/nanobot/releases/tag/v0.1.3.post5)。
- **2026-02-06** ✨ Added Moonshot/Kimi provider, Discord integration, and enhanced security hardening!<br>新增 Moonshot/Kimi provider、Discord integration，并增强 security hardening！
- **2026-02-05** ✨ Added Feishu channel, DeepSeek provider, and enhanced scheduled tasks support!<br>新增 Feishu channel、DeepSeek provider，并增强 scheduled tasks support！
- **2026-02-04** 🚀 Released **v0.1.3.post4** with multi-provider & Docker support! Check [here](https://github.com/HKUDS/nanobot/releases/tag/v0.1.3.post4) for details.<br>发布 **v0.1.3.post4**，包含 multi-provider 与 Docker support！详情请查看 [here](https://github.com/HKUDS/nanobot/releases/tag/v0.1.3.post4)。
- **2026-02-03** ⚡ Integrated vLLM for local LLM support and improved natural language task scheduling!<br>集成 vLLM 以支持本地 LLM，并改进自然语言任务调度！
- **2026-02-02** 🎉 nanobot officially launched! Welcome to try 🐈 nanobot!<br>nanobot 正式发布！欢迎试用 nanobot！

</details>


## 💡 Key Features of nanobot

## nanobot 的核心特性

- **Ultra-lightweight**: stable long-running agent behavior with a small, readable core.<br>**超轻量**：以小巧、可读的核心提供稳定的长期运行 agent 行为。
- **Research-ready**: the codebase is intentionally simple enough to study, modify, and extend.<br>**适合研究**：代码库刻意保持足够简单，便于学习、修改和扩展。
- **Practical**: chat channels, API, memory, MCP, and deployment paths are already built in.<br>**实用**：已内置 chat channels、API、memory、MCP 和部署路径。
- **Hackable**: you can start fast, then go deeper through repo docs instead of a monolithic landing page.<br>**易改造**：你可以快速开始，然后通过 repo docs 深入了解，而不是依赖单体式落地页。

## 📦 Install

## 安装

> [!IMPORTANT]
> If you want the newest features and experiments, install from source. 
> 
> If you want the most stable day-to-day experience, install from PyPI or with `uv`.
> 如果你想体验最新功能和实验特性，请从源码安装。
>
> 如果你想获得最稳定的日常体验，请从 PyPI 安装或使用 `uv`。

**Install from source**

**从源码安装**

```bash
git clone https://github.com/HKUDS/nanobot.git
cd nanobot
pip install -e .
```

**Install with `uv`**

**使用 `uv` 安装**

```bash
uv tool install nanobot-ai
```

**Install from PyPI**

**从 PyPI 安装**

```bash
pip install nanobot-ai
```

## 🚀 Quick Start

## 快速开始

**1. Initialize**

**1. 初始化**

```bash
nanobot onboard
```

**2. Configure** (`~/.nanobot/config.json`)

**2. 配置**（`~/.nanobot/config.json`）

Configure these **two parts** in your config (other options have defaults). Add or merge the following blocks into your existing config instead of replacing the whole file.

在你的配置中设置以下 **两个部分**（其他选项有默认值）。请将下列区块添加或合并到现有配置中，而不是替换整个文件。

*Set your API key* (e.g. [OpenRouter](https://openrouter.ai/keys), recommended for global users):

*设置你的 API key*（例如 [OpenRouter](https://openrouter.ai/keys)，推荐全球用户使用）：

```json
{
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-xxx"
    }
  }
}
```

*Set your model* (optionally pin a provider — defaults to auto-detection):

*设置你的 model*（可选固定 provider，默认自动检测）：

```json
{
  "agents": {
    "defaults": {
      "provider": "openrouter",
      "model": "anthropic/claude-opus-4-6"
    }
  }
}
```

**3. Chat**

**3. 聊天**

```bash
nanobot agent
```


- Want different LLM providers, web search, MCP, security settings, or more config options? See [Configuration](./docs/configuration.md)<br>想使用不同的 LLM providers、web search、MCP、安全设置或更多配置选项？请见 [Configuration](./docs/configuration.md)
- Want to run nanobot in chat apps like Telegram, Discord, WeChat or Feishu? See [Chat Apps](./docs/chat-apps.md)<br>想在 Telegram、Discord、WeChat 或 Feishu 等 chat apps 中运行 nanobot？请见 [Chat Apps](./docs/chat-apps.md)
- Want Docker or Linux service deployment? See [Deployment](./docs/deployment.md)<br>想使用 Docker 或 Linux service 部署？请见 [Deployment](./docs/deployment.md)

## 🧪 WebUI (Development)

## WebUI（开发）

> [!NOTE]
> The WebUI development workflow currently requires a source checkout and is not yet shipped together with the official packaged release. See [WebUI Document](./webui/README.md) for full WebUI development docs and build steps.
> WebUI 开发流程目前需要源码检出，尚未随官方打包版本一起发布。完整的 WebUI 开发文档和构建步骤请见 [WebUI Document](./webui/README.md)。

<p align="center">
  <img src="images/nanobot_webui.png" alt="nanobot webui preview" width="900">
</p>

**1. Enable the WebSocket channel in `~/.nanobot/config.json`**

**1. 在 `~/.nanobot/config.json` 中启用 WebSocket channel**

```json
{ "channels": { "websocket": { "enabled": true } } }
```

**2. Start the gateway**

**2. 启动 gateway**

```bash
nanobot gateway
```

**3. Start the webui dev server**

**3. 启动 webui dev server**

```bash
cd webui
bun install
bun run dev
```

## 🏗️ Architecture

## 架构

<p align="center">
  <img src="images/nanobot_arch.png" alt="nanobot architecture" width="800">
</p>

🐈 nanobot stays lightweight by centering everything around a small agent loop: messages come in from chat apps, the LLM decides when tools are needed, and memory or skills are pulled in only as context instead of becoming a heavy orchestration layer. That keeps the core path readable and easy to extend, while still letting you add channels, tools, memory, and deployment options without turning the system into a monolith.

nanobot 通过围绕一个小型 agent loop 组织一切来保持轻量：消息来自 chat apps，LLM 决定何时需要工具，memory 或 skills 仅作为 context 被拉入，而不会变成沉重的编排层。这让核心路径保持可读且易扩展，同时仍允许你添加 channels、tools、memory 和部署选项，而不会把系统变成单体。

## ✨ Features

## 功能

<table align="center">
  <tr align="center">
    <th><p align="center">📈 24/7 Real-Time Market Analysis<br>全天候实时市场分析</p></th>
    <th><p align="center">🚀 Full-Stack Software Engineer<br>全栈软件工程师</p></th>
    <th><p align="center">📅 Smart Daily Routine Manager<br>智能日常事务管理器</p></th>
    <th><p align="center">📚 Personal Knowledge Assistant<br>个人知识助手</p></th>
  </tr>
  <tr>
    <td align="center"><p align="center"><img src="case/search.gif" width="180" height="400"></p></td>
    <td align="center"><p align="center"><img src="case/code.gif" width="180" height="400"></p></td>
    <td align="center"><p align="center"><img src="case/schedule.gif" width="180" height="400"></p></td>
    <td align="center"><p align="center"><img src="case/memory.gif" width="180" height="400"></p></td>
  </tr>
  <tr>
    <td align="center">Discovery • Insights • Trends<br>发现 • 洞察 • 趋势</td>
    <td align="center">Develop • Deploy • Scale<br>开发 • 部署 • 扩展</td>
    <td align="center">Schedule • Automate • Organize<br>安排 • 自动化 • 组织</td>
    <td align="center">Learn • Memory • Reasoning<br>学习 • 记忆 • 推理</td>
  </tr>
</table>

## 📚 Docs

## 文档

Browse the [repo docs](./docs/README.md) for the latest features and GitHub development version, or visit [nanobot.wiki](https://nanobot.wiki/docs/latest/getting-started/nanobot-overview) for the stable release documentation.

浏览 [repo docs](./docs/README.md) 以了解最新功能和 GitHub 开发版本，或访问 [nanobot.wiki](https://nanobot.wiki/docs/latest/getting-started/nanobot-overview) 查看稳定版文档。

- Talk to your nanobot with familiar chat apps: [Chat Apps](./docs/chat-apps.md)<br>使用熟悉的 chat apps 与你的 nanobot 对话：[Chat Apps](./docs/chat-apps.md)
- Configure providers, web search, MCP, and runtime behavior: [Configuration](./docs/configuration.md)<br>配置 providers、web search、MCP 和 runtime behavior：[Configuration](./docs/configuration.md)
- Integrate nanobot with local tools and automations: [OpenAI-Compatible API](./docs/openai-api.md) · [Python SDK](./docs/python-sdk.md)<br>将 nanobot 与本地工具和自动化集成：[OpenAI-Compatible API](./docs/openai-api.md) · [Python SDK](./docs/python-sdk.md)
- Run nanobot with Docker or as a Linux service: [Deployment](./docs/deployment.md)<br>使用 Docker 或作为 Linux service 运行 nanobot：[Deployment](./docs/deployment.md)

## 🤝 Contribute & Roadmap

## 贡献与路线图

PRs welcome! The codebase is intentionally small and readable. 🤗

欢迎 PR！代码库刻意保持小巧且可读。

### Branching Strategy

### 分支策略

| Branch<br>分支 | Purpose<br>用途 |
|--------|---------|
| `main` | Stable releases — bug fixes and minor improvements<br>稳定版本：bug 修复和小改进 |
| `nightly` | Experimental features — new features and breaking changes<br>实验性功能：新功能和破坏性变更 |

**Unsure which branch to target?** See [CONTRIBUTING.md](./CONTRIBUTING.md) for details.

**不确定目标哪个分支？** 详情请见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

**Roadmap** — Pick an item and [open a PR](https://github.com/HKUDS/nanobot/pulls)!

**路线图**：选择一项并 [open a PR](https://github.com/HKUDS/nanobot/pulls)！

- **Multi-modal** — See and hear (images, voice, video)<br>**多模态**：看见和听见（图像、语音、视频）
- **Long-term memory** — Never forget important context<br>**长期记忆**：永不遗忘重要 context
- **Better reasoning** — Multi-step planning and reflection<br>**更强推理**：多步规划和反思
- **More integrations** — Calendar and more<br>**更多集成**：日历及更多
- **Self-improvement** — Learn from feedback and mistakes<br>**自我改进**：从反馈和错误中学习

### Contributors

### 贡献者

<a href="https://github.com/HKUDS/nanobot/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=HKUDS/nanobot&max=100&columns=12&updated=20260210" alt="Contributors" />
</a>


## ⭐ Star History

## Star 历史

<div align="center">
  <a href="https://star-history.com/#HKUDS/nanobot&Date">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=HKUDS/nanobot&type=Date&theme=dark" />
      <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=HKUDS/nanobot&type=Date" />
      <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=HKUDS/nanobot&type=Date" style="border-radius: 15px; box-shadow: 0 0 30px rgba(0, 217, 255, 0.3);" />
    </picture>
  </a>
</div>

<p align="center">
  <em> Thanks for visiting ✨ nanobot!</em><br><br>
  <em>感谢访问 nanobot！</em><br><br>
  <img src="https://visitor-badge.laobi.icu/badge?page_id=HKUDS.nanobot&style=for-the-badge&color=00d4ff" alt="Views">
</p>
