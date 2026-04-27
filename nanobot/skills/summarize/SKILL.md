---
name: summarize
description: Summarize or extract text/transcripts from URLs, podcasts, and local files (great fallback for “transcribe this YouTube/video”).
homepage: https://summarize.sh
metadata: {"nanobot":{"emoji":"🧾","requires":{"bins":["summarize"]},"install":[{"id":"brew","kind":"brew","formula":"steipete/tap/summarize","bins":["summarize"],"label":"Install summarize (brew)"}]}}
---

# Summarize
摘要

Fast CLI to summarize URLs, local files, and YouTube links.
用于总结 URL、本地文件和 YouTube 链接的快速 CLI。

## When to use (trigger phrases)
何时使用（触发短语）

Use this skill immediately when the user asks any of:
当用户提出以下任一请求时，立即使用此技能：
- “use summarize.sh”
- “使用 summarize.sh”
- “what’s this link/video about?”
- “这个链接/视频讲的是什么？”
- “summarize this URL/article”
- “总结这个 URL/文章”
- “transcribe this YouTube/video” (best-effort transcript extraction; no `yt-dlp` needed)
- “转录这个 YouTube/视频”（尽力提取转录文本；不需要 `yt-dlp`）

## Quick start
快速开始

```bash
summarize "https://example.com" --model google/gemini-3-flash-preview
summarize "/path/to/file.pdf" --model google/gemini-3-flash-preview
summarize "https://youtu.be/dQw4w9WgXcQ" --youtube auto
```

## YouTube: summary vs transcript
YouTube：摘要与转录文本

Best-effort transcript (URLs only):
尽力提取转录文本（仅 URL）：

```bash
summarize "https://youtu.be/dQw4w9WgXcQ" --youtube auto --extract-only
```

If the user asked for a transcript but it’s huge, return a tight summary first, then ask which section/time range to expand.
如果用户要求转录文本但内容很大，先返回精简摘要，然后询问要展开哪个章节或时间范围。

## Model + keys
模型与密钥

Set the API key for your chosen provider:
为你选择的 provider 设置 API key：
- OpenAI: `OPENAI_API_KEY`
- OpenAI：`OPENAI_API_KEY`
- Anthropic: `ANTHROPIC_API_KEY`
- Anthropic：`ANTHROPIC_API_KEY`
- xAI: `XAI_API_KEY`
- xAI：`XAI_API_KEY`
- Google: `GEMINI_API_KEY` (aliases: `GOOGLE_GENERATIVE_AI_API_KEY`, `GOOGLE_API_KEY`)
- Google：`GEMINI_API_KEY`（别名：`GOOGLE_GENERATIVE_AI_API_KEY`、`GOOGLE_API_KEY`）

Default model is `google/gemini-3-flash-preview` if none is set.
如果未设置模型，默认模型为 `google/gemini-3-flash-preview`。

## Useful flags
有用的 flags

- `--length short|medium|long|xl|xxl|<chars>`
- `--length short|medium|long|xl|xxl|<chars>`
- `--max-output-tokens <count>`
- `--max-output-tokens <count>`
- `--extract-only` (URLs only)
- `--extract-only`（仅 URL）
- `--json` (machine readable)
- `--json`（机器可读）
- `--firecrawl auto|off|always` (fallback extraction)
- `--firecrawl auto|off|always`（备用提取）
- `--youtube auto` (Apify fallback if `APIFY_API_TOKEN` set)
- `--youtube auto`（如果设置了 `APIFY_API_TOKEN`，使用 Apify 备用方案）

## Config
配置

Optional config file: `~/.summarize/config.json`
可选配置文件：`~/.summarize/config.json`

```json
{ "model": "openai/gpt-5.2" }
```

Optional services:
可选服务：
- `FIRECRAWL_API_KEY` for blocked sites
- `FIRECRAWL_API_KEY` 用于被阻止的网站
- `APIFY_API_TOKEN` for YouTube fallback
- `APIFY_API_TOKEN` 用于 YouTube 备用方案
