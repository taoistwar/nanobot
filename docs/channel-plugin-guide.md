# Channel Plugin Guide
# 频道插件指南

Build a custom nanobot channel in three steps: subclass, package, install.
通过三个步骤构建自定义纳米机器人通道：子类、打包、安装。

> **Note:** We recommend developing channel plugins against a source checkout of nanobot (`pip install -e .`) rather than a PyPI release, so you always have access to the latest base-channel features and APIs.
> **注意：** 我们建议针对 Nanobot (`pip install -e .`) 的源代码检查而不是 PyPI 版本开发通道插件，以便您始终可以访问最新的基础通道功能和 API。

## How It Works
## 它是如何运作的

nanobot discovers channel plugins via Python [entry points](https://packaging.python.org/en/latest/specifications/entry-points/). When `nanobot gateway` starts, it scans:
nanobot 通过 Python [entry points](https://packaging.python.org/en/latest/specifications/entry-points/) 发现通道插件。当`nanobot gateway`启动时，它会扫描：

1. Built-in channels in `nanobot/channels/`
1. `nanobot/channels/`内置频道
2. External packages registered under the `nanobot.channels` entry point group
2. 在 `nanobot.channels` 入口点组下注册的外部包

If a matching config section has `"enabled": true`, the channel is instantiated and started.
如果匹配的配置部分具有`"enabled": true`，则通道将被实例化并启动。

## Quick Start
## 快速入门

We'll build a minimal webhook channel that receives messages via HTTP POST and sends replies back.
我们将构建一个最小的 Webhook 通道，通过 HTTP POST 接收消息并发回回复。

### Project Structure
### 项目结构

```text
nanobot-channel-webhook/
├── nanobot_channel_webhook/
│   ├── __init__.py          # re-export WebhookChannel
│   └── channel.py           # channel implementation
└── pyproject.toml
```

### 1. Create Your Channel
### 1. 创建您的频道

```python
# nanobot_channel_webhook/__init__.py
from nanobot_channel_webhook.channel import WebhookChannel

__all__ = ["WebhookChannel"]
```

```python
# nanobot_channel_webhook/channel.py
import asyncio
from typing import Any

from aiohttp import web
from loguru import logger
from pydantic import Field

from nanobot.channels.base import BaseChannel
from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.config.schema import Base


class WebhookConfig(Base):
    """Webhook channel configuration."""
    enabled: bool = False
    port: int = 9000
    allow_from: list[str] = Field(default_factory=list)


class WebhookChannel(BaseChannel):
    name = "webhook"
    display_name = "Webhook"

    def __init__(self, config: Any, bus: MessageBus):
        if isinstance(config, dict):
            config = WebhookConfig(**config)
        super().__init__(config, bus)

    @classmethod
    def default_config(cls) -> dict[str, Any]:
        return WebhookConfig().model_dump(by_alias=True)

    async def start(self) -> None:
        """Start an HTTP server that listens for incoming messages.

        IMPORTANT: start() must block forever (or until stop() is called).
        If it returns, the channel is considered dead.
        """
        self._running = True
        port = self.config.port

        app = web.Application()
        app.router.add_post("/message", self._on_request)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info("Webhook listening on :{}", port)

        # Block until stopped
        while self._running:
            await asyncio.sleep(1)

        await runner.cleanup()

    async def stop(self) -> None:
        self._running = False

    async def send(self, msg: OutboundMessage) -> None:
        """Deliver an outbound message.

        msg.content  — markdown text (convert to platform format as needed)
        msg.media    — list of local file paths to attach
        msg.chat_id  — the recipient (same chat_id you passed to _handle_message)
        msg.metadata — may contain "_progress": True for streaming chunks
        """
        logger.info("[webhook] -> {}: {}", msg.chat_id, msg.content[:80])
        # In a real plugin: POST to a callback URL, send via SDK, etc.

    async def _on_request(self, request: web.Request) -> web.Response:
        """Handle an incoming HTTP POST."""
        body = await request.json()
        sender = body.get("sender", "unknown")
        chat_id = body.get("chat_id", sender)
        text = body.get("text", "")
        media = body.get("media", [])       # list of URLs

        # This is the key call: validates allowFrom, then puts the
        # message onto the bus for the agent to process.
        await self._handle_message(
            sender_id=sender,
            chat_id=chat_id,
            content=text,
            media=media,
        )

        return web.json_response({"ok": True})
```

### 2. Register the Entry Point
### 2. 注册入口点

```toml
# pyproject.toml
[project]
name = "nanobot-channel-webhook"
version = "0.1.0"
dependencies = ["nanobot-ai", "aiohttp"]

[project.entry-points."nanobot.channels"]
webhook = "nanobot_channel_webhook:WebhookChannel"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["nanobot_channel_webhook"]
```

The key (`webhook`) becomes the config section name. The value points to your `BaseChannel` subclass.
键 (`webhook`) 成为配置节名称。该值指向您的 `BaseChannel` 子类。

### 3. Install & Configure
### 3. 安装和配置

```bash
pip install -e .
nanobot plugins list      # verify "Webhook" shows as "plugin"
nanobot onboard           # auto-adds default config for detected plugins
```

Edit `~/.nanobot/config.json`:
编辑`~/.nanobot/config.json`：

```json
{
  "channels": {
    "webhook": {
      "enabled": true,
      "port": 9000,
      "allowFrom": ["*"]
    }
  }
}
```

### 4. Run & Test
### 4. 运行和测试

```bash
nanobot gateway
```

In another terminal:
在另一个终端中：

```bash
curl -X POST http://localhost:9000/message \
  -H "Content-Type: application/json" \
  -d '{"sender": "user1", "chat_id": "user1", "text": "Hello!"}'
```

The agent receives the message and processes it. Replies arrive in your `send()` method.
代理接收消息并处理它。回复将到达您的 `send()` 方法。

## BaseChannel API
## 基础频道API

### Required (abstract)
### 必填（摘要）

| Method<br>方法 | Description<br>描述 |
|--------|-------------|
| `async start()`<br>`async start()` | **Must block forever.** Connect to platform, listen for messages, call `_handle_message()` on each. If this returns, the channel is dead.<br>**必须永远阻塞。** 连接到平台，监听消息，在每个消息上调用 `_handle_message()`。如果返回，则该通道已失效。 |
| `async stop()`<br>`async stop()` | Set `self._running = False` and clean up. Called when gateway shuts down.<br>设置`self._running = False`并清理。当网关关闭时调用。 |
| `async send(msg: OutboundMessage)`<br>`async send(msg: OutboundMessage)` | Deliver an outbound message to the platform.<br>向平台发送出站消息。 |

### Interactive Login
### 互动登录

If your channel requires interactive authentication (e.g. QR code scan), override `login(force=False)`:
如果您的频道需要交互式身份验证（例如二维码扫描），请覆盖 `login(force=False)`：

```python
async def login(self, force: bool = False) -> bool:
    """
    Perform channel-specific interactive login.

    Args:
        force: If True, ignore existing credentials and re-authenticate.

    Returns True if already authenticated or login succeeds.
    """
    # For QR-code-based login:
    # 1. If force, clear saved credentials
    # 2. Check if already authenticated (load from disk/state)
    # 3. If not, show QR code and poll for confirmation
    # 4. Save token on success
```

Channels that don't need interactive login (e.g. Telegram with bot token, Discord with bot token) inherit the default `login()` which just returns `True`.
不需要交互式登录的频道（例如带有机器人令牌的 Telegram、带有机器人令牌的 Discord）继承默认的 `login()`，它仅返回 `True`。

Users trigger interactive login via:
用户通过以下方式触发交互式登录：
```bash
nanobot channels login <channel_name>
nanobot channels login <channel_name> --force  # re-authenticate
```

### Provided by Base
### 基地提供

| Method / Property<br>方法/属性 | Description<br>描述 |
|-------------------|-------------|
| `_handle_message(sender_id, chat_id, content, media?, metadata?, session_key?)`<br>`_handle_message(sender_id, chat_id, content, media?, metadata?, session_key?)` | **Call this when you receive a message.** Checks `is_allowed()`, then publishes to the bus. Automatically sets `_wants_stream` if `supports_streaming` is true.<br>**收到消息时调用此方法。** 检查 `is_allowed()`，然​​后发布到总线。如果 `supports_streaming` 为 true，则自动设置 `_wants_stream`。 |
| `is_allowed(sender_id)`<br>`is_allowed(sender_id)` | Checks against `config.allow_from`; `"*"` allows all, `[]` denies all.<br>检查`config.allow_from`； `"*"`允许所有，`[]`拒绝所有。 |
| `default_config()` (classmethod)<br>`default_config()`（类方法） | Returns default config dict for `nanobot onboard`. Override to declare your fields.<br>返回 `nanobot onboard` 的默认配置字典。覆盖以声明您的字段。 |
| `transcribe_audio(file_path)`<br>`transcribe_audio(file_path)` | Transcribes audio via Groq Whisper (if configured).<br>通过 Groq Whisper 转录音频（如果已配置）。 |
| `supports_streaming` (property)<br>`supports_streaming`（属性） | `True` when config has `"streaming": true` **and** subclass overrides `send_delta()`.<br>`True` 当配置具有 `"streaming": true` **和** 子类覆盖 `send_delta()` 时。 |
| `is_running`<br>`is_running` | Returns `self._running`.<br>返回`self._running`。 |
| `login(force=False)`<br>`login(force=False)` | Perform interactive login (e.g. QR code scan). Returns `True` if already authenticated or login succeeds. Override in subclasses that support interactive login.<br>执行交互式登录（例如扫描二维码）。如果已通过身份验证或登录成功，则返回`True`。在支持交互式登录的子类中重写。 |

### Optional (streaming)
### 可选（流式传输）

| Method<br>方法 | Description<br>描述 |
|--------|-------------|
| `async send_delta(chat_id, delta, metadata?)`<br>`async send_delta(chat_id, delta, metadata?)` | Override to receive streaming chunks. See [Streaming Support](#streaming-support) for details.<br>覆盖以接收流数据块。详情请参阅[Streaming Support](#streaming-support)。 |

### Message Types
### 消息类型

```python
@dataclass
class OutboundMessage:
    channel: str        # your channel name
    chat_id: str        # recipient (same value you passed to _handle_message)
    content: str        # markdown text — convert to platform format as needed
    media: list[str]    # local file paths to attach (images, audio, docs)
    metadata: dict      # may contain: "_progress" (bool) for streaming chunks,
                        #              "message_id" for reply threading
```

## Streaming Support
## 流媒体支持

Channels can opt into real-time streaming — the agent sends content token-by-token instead of one final message. This is entirely optional; channels work fine without it.
通道可以选择实时流——代理逐个令牌发送内容，而不是一条最终消息。这完全是可选的；没有它渠道就可以正常工作。

### How It Works
### 它是如何运作的

When **both** conditions are met, the agent streams content through your channel:
当满足**两个**条件时，代理会通过您的频道传输内容：

1. Config has `"streaming": true`
1. 配置有`"streaming": true`
2. Your subclass overrides `send_delta()`
2. 你的子类覆盖 `send_delta()`

If either is missing, the agent falls back to the normal one-shot `send()` path.
如果其中一个缺失，代理就会退回到正常的一次性 `send()` 路径。

### Implementing `send_delta`
### 实施`send_delta`

Override `send_delta` to handle two types of calls:
覆盖 `send_delta` 来处理两种类型的调用：

```python
async def send_delta(self, chat_id: str, delta: str, metadata: dict[str, Any] | None = None) -> None:
    meta = metadata or {}

    if meta.get("_stream_end"):
        # Streaming finished — do final formatting, cleanup, etc.
        return

    # Regular delta — append text, update the message on screen
    # delta contains a small chunk of text (a few tokens)
```

**Metadata flags:**
**元数据标志：**

| Flag<br>旗帜 | Meaning<br>意义 |
|------|---------|
| `_stream_delta: True`<br>`_stream_delta: True` | A content chunk (delta contains the new text)<br>内容块（增量包含新文本） |
| `_stream_end: True`<br>`_stream_end: True` | Streaming finished (delta is empty)<br>流式传输完成（增量为空） |

### Example: Webhook with Streaming
### 示例：带有流式传输的 Webhook

```python
class WebhookChannel(BaseChannel):
    name = "webhook"
    display_name = "Webhook"

    def __init__(self, config: Any, bus: MessageBus):
        if isinstance(config, dict):
            config = WebhookConfig(**config)
        super().__init__(config, bus)
        self._buffers: dict[str, str] = {}

    async def send_delta(self, chat_id: str, delta: str, metadata: dict[str, Any] | None = None) -> None:
        meta = metadata or {}
        if meta.get("_stream_end"):
            text = self._buffers.pop(chat_id, "")
            # Final delivery — format and send the complete message
            await self._deliver(chat_id, text, final=True)
            return

        self._buffers.setdefault(chat_id, "")
        self._buffers[chat_id] += delta
        # Incremental update — push partial text to the client
        await self._deliver(chat_id, self._buffers[chat_id], final=False)

    async def send(self, msg: OutboundMessage) -> None:
        # Non-streaming path — unchanged
        await self._deliver(msg.chat_id, msg.content, final=True)
```

### Config
### 配置

Enable streaming per channel:
启用每个通道的流式传输：

```json
{
  "channels": {
    "webhook": {
      "enabled": true,
      "streaming": true,
      "allowFrom": ["*"]
    }
  }
}
```

When `streaming` is `false` (default) or omitted, only `send()` is called — no streaming overhead.
当`streaming`为`false`（默认）或省略时，仅调用`send()`——没有流开销。

### BaseChannel Streaming API
### BaseChannel 流媒体 API

| Method / Property<br>方法/属性 | Description<br>描述 |
|-------------------|-------------|
| `async send_delta(chat_id, delta, metadata?)`<br>`async send_delta(chat_id, delta, metadata?)` | Override to handle streaming chunks. No-op by default.<br>覆盖以处理流数据块。默认情况下无操作。 |
| `supports_streaming` (property)<br>`supports_streaming`（属性） | Returns `True` when config has `streaming: true` **and** subclass overrides `send_delta`.<br>当配置具有 `streaming: true` **和** 子类覆盖 `send_delta` 时，返回 `True`。 |

## Config
## 配置

### Why Pydantic model is required
### 为什么需要 Pydantic 模型

`BaseChannel.is_allowed()` reads the permission list via `getattr(self.config, "allow_from", [])`. This works for Pydantic models where `allow_from` is a real Python attribute, but **fails silently for plain `dict`** — `dict` has no `allow_from` attribute, so `getattr` always returns the default `[]`, causing all messages to be denied.
`BaseChannel.is_allowed()`通过`getattr(self.config, "allow_from", [])`读取权限列表。这适用于 Pydantic 模型，其中 `allow_from` 是真正的 Python 属性，但 **对于普通 `dict`** 会默默失败 - `dict` 没有 `allow_from` 属性，因此 `getattr` 始终返回默认的 `[]`，导致所有消息被拒绝。

Built-in channels use Pydantic config models (subclassing `Base` from `nanobot.config.schema`). Plugin channels **must do the same**.
内置通道使用 Pydantic 配置模型（从 `nanobot.config.schema` 子类化 `Base`）。插件通道**必须执行相同的操作**。

### Pattern
### 图案

1. Define a Pydantic model inheriting from `nanobot.config.schema.Base`:
1. 定义一个继承于 `nanobot.config.schema.Base` 的 Pydantic 模型：

```python
from pydantic import Field
from nanobot.config.schema import Base

class WebhookConfig(Base):
    """Webhook channel configuration."""
    enabled: bool = False
    port: int = 9000
    allow_from: list[str] = Field(default_factory=list)
```

`Base` is configured with `alias_generator=to_camel` and `populate_by_name=True`, so JSON keys like `"allowFrom"` and `"allow_from"` are both accepted.
`Base` 配置了 `alias_generator=to_camel` 和 `populate_by_name=True`，因此像 `"allowFrom"` 和 `"allow_from"` 这样的 JSON 键都被接受。

2. Convert `dict` → model in `__init__`:
2. 转换 `dict` → `__init__` 中的模型：

```python
from typing import Any
from nanobot.bus.queue import MessageBus

class WebhookChannel(BaseChannel):
    def __init__(self, config: Any, bus: MessageBus):
        if isinstance(config, dict):
            config = WebhookConfig(**config)
        super().__init__(config, bus)
```

3. Access config as attributes (not `.get()`):
3. 将配置作为属性访问（不是 `.get()`）：

```python
async def start(self) -> None:
    port = self.config.port
    token = self.config.token
```

`allowFrom` is handled automatically by `_handle_message()` — you don't need to check it yourself.
`allowFrom` 由 `_handle_message()` 自动处理 — 您无需自己检查。

Override `default_config()` so `nanobot onboard` auto-populates `config.json`:
覆盖 `default_config()`，因此 `nanobot onboard` 自动填充 `config.json`：

```python
@classmethod
def default_config(cls) -> dict[str, Any]:
    return WebhookConfig().model_dump(by_alias=True)
```

> **Note:** `default_config()` returns a plain `dict` (not a Pydantic model) because it's used to serialize into `config.json`. The recommended way is to instantiate your config model and call `model_dump(by_alias=True)` — this automatically uses camelCase keys (`allowFrom`) and keeps defaults in a single source of truth.
> **注意：** `default_config()` 返回一个普通的 `dict` （不是 Pydantic 模型），因为它用于序列化为 `config.json`。推荐的方法是实例化您的配置模型并调用`model_dump(by_alias=True)`——这会自动使用驼峰式键（`allowFrom`）并将默认值保留在单一事实来源中。

If not overridden, the base class returns `{"enabled": false}`.
如果不被重写，基类将返回 `{"enabled": false}`。

## Naming Convention
## 命名约定

| What<br>什么 | Format<br>格式 | Example<br>例子 |
|------|--------|---------|
| PyPI package<br>PyPI包 | `nanobot-channel-{name}`<br>`nanobot-channel-{name}` | `nanobot-channel-webhook`<br>`nanobot-channel-webhook` |
| Entry point key<br>入口点键 | `{name}`<br>`{name}` | `webhook`<br>`webhook` |
| Config section<br>配置部分 | `channels.{name}`<br>`channels.{name}` | `channels.webhook`<br>`channels.webhook` |
| Python package<br>Python包 | `nanobot_channel_{name}`<br>`nanobot_channel_{name}` | `nanobot_channel_webhook`<br>`nanobot_channel_webhook` |

## Local Development
## 本地发展

```bash
git clone https://github.com/you/nanobot-channel-webhook
cd nanobot-channel-webhook
pip install -e .
nanobot plugins list    # should show "Webhook" as "plugin"
nanobot gateway         # test end-to-end
```

## Verify
## 核实

```bash
$ nanobot plugins list

  Name       Source    Enabled
  telegram   builtin  yes
  discord    builtin  no
  webhook    plugin   yes
```
