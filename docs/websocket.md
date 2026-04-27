# WebSocket Server Channel
# WebSocket 服务器通道

Nanobot can act as a WebSocket server, allowing external clients (web apps, CLIs, scripts) to interact with the agent in real time via persistent connections.
Nanobot 可以充当 WebSocket 服务器，允许外部客户端（Web 应用程序、CLI、脚本）通过持久连接与代理实时交互。

## Features
## 特征

- Bidirectional real-time communication over WebSocket
- 通过 WebSocket 进行双向实时通信
- Streaming support — receive agent responses token by token
- 流支持——逐个接收代理响应令牌
- Token-based authentication (static tokens and short-lived issued tokens)
- 基于令牌的身份验证（静态令牌和短期发行的令牌）
- Multi-chat multiplexing — one connection can run many concurrent `chat_id`s
- 多聊天复用 — 一个连接可以运行多个并发 `chat_id`
- TLS/SSL support (WSS) with enforced TLSv1.2 minimum
- TLS/SSL 支持 (WSS)，最低强制执行 TLSv1.2
- Client allow-list via `allowFrom`
- 通过 `allowFrom` 的客户端允许列表
- Auto-cleanup of dead connections
- 自动清理死连接

## Quick Start
## 快速入门

### 1. Configure
### 1. 配置

Add to `config.json` under `channels.websocket`:
添加到`channels.websocket`下的`config.json`：

```json
{
  "channels": {
    "websocket": {
      "enabled": true,
      "host": "127.0.0.1",
      "port": 8765,
      "path": "/",
      "websocketRequiresToken": false,
      "allowFrom": ["*"],
      "streaming": true
    }
  }
}
```

### 2. Start nanobot
### 2.启动纳米机器人

```bash
nanobot gateway
```

You should see:
你应该看到：

```text
WebSocket server listening on ws://127.0.0.1:8765/
```

### 3. Connect a client
### 3. 连接客户端

```bash
# Using websocat
websocat ws://127.0.0.1:8765/?client_id=alice

# Using Python
import asyncio, json, websockets

async def main():
    async with websockets.connect("ws://127.0.0.1:8765/?client_id=alice") as ws:
        ready = json.loads(await ws.recv())
        print(ready)  # {"event": "ready", "chat_id": "...", "client_id": "alice"}
        await ws.send(json.dumps({"content": "Hello nanobot!"}))
        reply = json.loads(await ws.recv())
        print(reply["text"])

asyncio.run(main())
```

## Connection URL
## 连接网址

```text
ws://{host}:{port}{path}?client_id={id}&token={token}
```

| Parameter<br>范围 | Required<br>必需的 | Description<br>描述 |
|-----------|----------|-------------|
| `client_id`<br>`client_id` | No<br>不 | Identifier for `allowFrom` authorization. Auto-generated as `anon-xxxxxxxxxxxx` if omitted. Truncated to 128 chars.<br>`allowFrom`授权的标识符。如果省略，则自动生成为 `anon-xxxxxxxxxxxx`。截断为 128 个字符。 |
| `token`<br>`token` | Conditional<br>有条件的 | Authentication token. Required when `websocketRequiresToken` is `true` or `token` (static secret) is configured.<br>身份验证令牌。配置`websocketRequiresToken`为`true`或`token`（静态秘密）时必填。 |

## Wire Protocol
## 有线协议

All frames are JSON text. Each message has an `event` field.
所有框架都是 JSON 文本。每条消息都有一个 `event` 字段。

### Server → Client
### 服务器→客户端

**`ready`** — sent immediately after connection is established:
**`ready`** — 连接建立后立即发送：

```json
{
  "event": "ready",
  "chat_id": "uuid-v4",
  "client_id": "alice"
}
```

**`message`** — full agent response:
**`message`** — 完整的代理回复：

```json
{
  "event": "message",
  "chat_id": "uuid-v4",
  "text": "Hello! How can I help?",
  "media": ["/tmp/image.png"],
  "reply_to": "msg-id"
}
```

`media` and `reply_to` are only present when applicable.
`media` 和 `reply_to` 仅在适用时出现。

**`delta`** — streaming text chunk (only when `streaming: true`):
**`delta`** — 流文本块（仅当`streaming: true`时）：

```json
{
  "event": "delta",
  "chat_id": "uuid-v4",
  "text": "Hello",
  "stream_id": "s1"
}
```

**`stream_end`** — signals the end of a streaming segment:
**`stream_end`** — 表示流片段的结束：

```json
{
  "event": "stream_end",
  "chat_id": "uuid-v4",
  "stream_id": "s1"
}
```

**`attached`** — confirmation for `new_chat` / `attach` inbound envelopes (see [Multi-chat multiplexing](#multi-chat-multiplexing)):
**`attached`** — `new_chat` / `attach` 入站信封的确认（参见[Multi-chat multiplexing](#multi-chat-multiplexing)）：

```json
{"event": "attached", "chat_id": "uuid-v4"}
```

**`error`** — soft error for malformed inbound envelopes. The connection stays open:
**`error`** — 入站信封格式错误的软错误。连接保持打开状态：

```json
{"event": "error", "detail": "invalid chat_id"}
```

### Client → Server
### 客户端→服务器

**Legacy (default chat):** send a plain string, or a JSON object with a recognized text field:
**旧版（默认聊天）：** 发送纯字符串或带有可识别文本字段的 JSON 对象：

```json
"Hello nanobot!"
```

```json
{"content": "Hello nanobot!"}
```

Recognized fields: `content`, `text`, `message` (checked in that order). Invalid JSON is treated as plain text. These frames route to the connection's default `chat_id` (the one announced in `ready`).
识别字段：`content`、`text`、`message`（按顺序检查）。无效的 JSON 将被视为纯文本。这些帧路由到连接的默认`chat_id`（`ready`中宣布的那个）。

**Typed envelopes (multi-chat):** any JSON object with a string `type` field is a typed envelope:
**类型化信封（多聊天）：**任何带有字符串 `type` 字段的 JSON 对象都是类型化信封：

| `type`<br>`type` | Fields<br>领域 | Effect<br>影响 |
|--------|--------|--------|
| `new_chat`<br>`new_chat` | — | Server mints a new `chat_id`, subscribes this connection, replies with `attached`.<br>服务器创建一个新的`chat_id`，订阅此连接，回复`attached`。 |
| `attach`<br>`attach` | `chat_id`<br>`chat_id` | Subscribe to an existing `chat_id` (e.g. after a page reload). Replies with `attached`.<br>订阅现有的 `chat_id` （例如页面重新加载后）。回复`attached`。 |
| `message`<br>`message` | `chat_id`, `content`<br>`chat_id`, `content` | Send `content` on `chat_id`. First use auto-attaches; no explicit `attach` needed.<br>在`chat_id`发送`content`。首先使用自动附加；不需要明确的`attach`。 |

See [Multi-chat multiplexing](#multi-chat-multiplexing) for the full flow.
完整流程请参见[Multi-chat multiplexing](#multi-chat-multiplexing)。

## Configuration Reference
## 配置参考

All fields go under `channels.websocket` in `config.json`.
所有字段都位于 `config.json` 中的 `channels.websocket` 之下。

### Connection
### 联系

| Field<br>场地 | Type<br>类型 | Default<br>默认 | Description<br>描述 |
|-------|------|---------|-------------|
| `enabled`<br>`enabled` | bool<br>布尔值 | `false`<br>`false` | Enable the WebSocket server.<br>启用 WebSocket 服务器。 |
| `host`<br>`host` | string<br>细绳 | `"127.0.0.1"` | Bind address. Use `"0.0.0.0"` to accept external connections.<br>绑定地址。使用`"0.0.0.0"`接受外部连接。 |
| `port`<br>`port` | int<br>整数 | `8765` | Listen port.<br>监听端口。 |
| `path`<br>`path` | string<br>细绳 | `"/"` | WebSocket upgrade path. Trailing slashes are normalized (root `/` is preserved).<br>WebSocket升级路径。尾部斜杠被标准化（保留根`/`）。 |
| `maxMessageBytes`<br>`maxMessageBytes` | int<br>整数 | `37748736` | Maximum inbound message size in bytes (1 KB – 40 MB). Default (36 MB) is sized to accept up to 4 base64-encoded image attachments at 8 MB each; lower it if the channel only carries text.<br>最大入站消息大小（以字节为单位）（1 KB – 40 MB）。默认 (36 MB) 大小最多可接受 4 个 Base64 编码的图像附件，每个附件 8 MB；如果通道仅传输文本，则降低它。 |

### Authentication
### 验证

| Field<br>场地 | Type<br>类型 | Default<br>默认 | Description<br>描述 |
|-------|------|---------|-------------|
| `token`<br>`token` | string<br>细绳 | `""` | Static shared secret. When set, clients must provide `?token=<value>` matching this secret (timing-safe comparison). Issued tokens are also accepted as a fallback.<br>静态共享秘密。设置后，客户端必须提供与此秘密匹配的`?token=<value>`（定时安全比较）。发行的代币也被接受作为后备方案。 |
| `websocketRequiresToken`<br>`websocketRequiresToken` | bool<br>布尔值 | `true`<br>`true` | When `true` and no static `token` is configured, clients must still present a valid issued token. Set to `false` to allow unauthenticated connections (only safe for local/trusted networks).<br>当`true`且未配置静态`token`时，客户端仍必须提供有效的已颁发令牌。设置为 `false` 以允许未经身份验证的连接（仅对本地/可信网络安全）。 |
| `tokenIssuePath`<br>`tokenIssuePath` | string<br>细绳 | `""` | HTTP path for issuing short-lived tokens. Must differ from `path`. See [Token Issuance](#token-issuance).<br>用于颁发短期令牌的 HTTP 路径。必须不同于 `path`。参见[Token Issuance](#token-issuance)。 |
| `tokenIssueSecret`<br>`tokenIssueSecret` | string<br>细绳 | `""` | Secret required to obtain tokens via the issue endpoint. If empty, any client can obtain tokens (logged as a warning).<br>通过发行端点获取令牌所需的秘密。如果为空，则任何客户端都可以获得令牌（记录为警告）。 |
| `tokenTtlS`<br>`tokenTtlS` | int<br>整数 | `300` | Time-to-live for issued tokens in seconds (30 – 86,400).<br>已发行代币的生存时间（30 – 86,400）。 |

### Access Control
### 访问控制

| Field<br>场地 | Type<br>类型 | Default<br>默认 | Description<br>描述 |
|-------|------|---------|-------------|
| `allowFrom`<br>`allowFrom` | list of string<br>字符串列表 | `["*"]` | Allowed `client_id` values. `"*"` allows all; `[]` denies all.<br>允许的 `client_id` 值。 `"*"` 允许所有； `[]` 否认一切。 |

### Streaming
### 流媒体

| Field<br>场地 | Type<br>类型 | Default<br>默认 | Description<br>描述 |
|-------|------|---------|-------------|
| `streaming`<br>`streaming` | bool<br>布尔值 | `true`<br>`true` | Enable streaming mode. The agent sends `delta` + `stream_end` frames instead of a single `message`.<br>启用流模式。代理发送 `delta` + `stream_end` 帧，而不是单个 `message`。 |

### Keep-alive
### 保持活动状态

| Field<br>场地 | Type<br>类型 | Default<br>默认 | Description<br>描述 |
|-------|------|---------|-------------|
| `pingIntervalS`<br>`pingIntervalS` | float<br>漂浮 | `20.0` | WebSocket ping interval in seconds (5 – 300).<br>WebSocket ping 间隔以秒为单位 (5 – 300)。 |
| `pingTimeoutS`<br>`pingTimeoutS` | float<br>漂浮 | `20.0` | Time to wait for a pong before closing the connection (5 – 300).<br>关闭连接之前等待 pong 的时间 (5 – 300)。 |

### TLS/SSL
### 传输层安全/SSL

| Field<br>场地 | Type<br>类型 | Default<br>默认 | Description<br>描述 |
|-------|------|---------|-------------|
| `sslCertfile`<br>`sslCertfile` | string<br>细绳 | `""` | Path to the TLS certificate file (PEM). Both `sslCertfile` and `sslKeyfile` must be set to enable WSS.<br>TLS 证书文件 (PEM) 的路径。必须设置`sslCertfile`和`sslKeyfile`才能启用WSS。 |
| `sslKeyfile`<br>`sslKeyfile` | string<br>细绳 | `""` | Path to the TLS private key file (PEM). Minimum TLS version is enforced as TLSv1.2.<br>TLS 私钥文件 (PEM) 的路径。最低 TLS 版本强制为 TLSv1.2。 |

## Token Issuance
## 代币发行

For production deployments where `websocketRequiresToken: true`, use short-lived tokens instead of embedding static secrets in clients.
对于`websocketRequiresToken: true`的生产部署，请使用短期令牌，而不是在客户端中嵌入静态机密。

### How it works
### 它是如何运作的

1. Client sends `GET {tokenIssuePath}` with `Authorization: Bearer {tokenIssueSecret}` (or `X-Nanobot-Auth` header).
1. 客户端发送带有`Authorization: Bearer {tokenIssueSecret}`（或`X-Nanobot-Auth`标头）的`GET {tokenIssuePath}`。
2. Server responds with a one-time-use token:
2. 服务器使用一次性令牌进行响应：

```json
{"token": "nbwt_aBcDeFg...", "expires_in": 300}
```

3. Client opens WebSocket with `?token=nbwt_aBcDeFg...&client_id=...`.
3. 客户端使用`?token=nbwt_aBcDeFg...&client_id=...`打开WebSocket。
4. The token is consumed (single use) and cannot be reused.
4. 令牌已消耗（一次性使用）且无法重复使用。

### Example setup
### 设置示例

```json
{
  "channels": {
    "websocket": {
      "enabled": true,
      "port": 8765,
      "path": "/ws",
      "tokenIssuePath": "/auth/token",
      "tokenIssueSecret": "your-secret-here",
      "tokenTtlS": 300,
      "websocketRequiresToken": true,
      "allowFrom": ["*"],
      "streaming": true
    }
  }
}
```

Client flow:
客户流程：

```bash
# 1. Obtain a token
curl -H "Authorization: Bearer your-secret-here" http://127.0.0.1:8765/auth/token

# 2. Connect using the token
websocat "ws://127.0.0.1:8765/ws?client_id=alice&token=nbwt_aBcDeFg..."
```

### Limits
### 限制

- Issued tokens are single-use — each token can only complete one handshake.
- 发行的代币是一次性的——每个代币只能完成一次握手。
- Outstanding tokens are capped at 10,000. Requests beyond this return HTTP 429.
- 未偿代币上限为 10,000 个。超出此范围的请求将返回 HTTP 429。
- Expired tokens are purged lazily on each issue or validation request.
- 每次发出或验证请求时都会延迟清除过期的令牌。

## Multi-chat multiplexing
## 多聊天复用

A single WebSocket can carry many concurrent chats. The server tracks `chat_id -> {connections}` as a fan-out set, so the same chat can also be mirrored across multiple connections (e.g. two browser tabs).
单个 WebSocket 可以承载许多并发聊天。服务器将 `chat_id -> {connections}` 作为扇出集进行跟踪，因此同一聊天也可以跨多个连接（例如两个浏览器选项卡）进行镜像。

### Typical flow (web UI with a sidebar)
### 典型流程（带有侧边栏的 Web UI）

```text
client                                server
  | --- connect -------------------->  |
  | <-- {"event":"ready",              |
  |      "chat_id":"d3..."}   (default)|
  |                                     |
  | --- {"type":"new_chat"} --------->  |
  | <-- {"event":"attached",            |
  |      "chat_id":"a1..."}             |
  |                                     |
  | --- {"type":"message",              |
  |      "chat_id":"a1...",             |
  |      "content":"hi"} ------------>  |
  | <-- {"event":"delta", ...}          |
  | <-- {"event":"stream_end", ...}     |
  |                                     |
  | --- {"type":"attach",               |  # after page reload
  |      "chat_id":"a1..."} --------->  |
  | <-- {"event":"attached", ...}       |
```

### Rules
### 规则

- Every outbound event carries `chat_id`. Clients must dispatch by that field.
- 每个出站事件都会携带`chat_id`。客户必须通过该字段发送。
- `chat_id` format: `^[A-Za-z0-9_:-]{1,64}$`. Non-matching values return `error`.
- `chat_id` 格式：`^[A-Za-z0-9_:-]{1,64}$`。不匹配的值返回`error`。
- `message` auto-attaches on first use — no separate `attach` is required for chats the server minted (`new_chat`) on the same connection.
- `message` 首次使用时自动附加 — 服务器在同一连接上创建 (`new_chat`) 的聊天不需要单独的 `attach`。
- Errors (invalid envelope, unknown `type`, bad `chat_id`) are soft: the server replies with `{"event":"error","detail":"..."}` and keeps the connection open.
- 错误（无效信封、未知 `type`、错误 `chat_id`）是软错误：服务器回复 `{"event":"error","detail":"..."}` 并保持连接打开。

### Backward compatibility
### 向后兼容性

Legacy clients that only send plain text or `{"content": ...}` keep working unchanged: those frames route to the connection's default `chat_id` (the one from `ready`). No config flag is needed.
仅发送纯文本或 `{"content": ...}` 的旧客户端保持不变：这些帧路由到连接的默认 `chat_id`（来自 `ready` 的帧）。不需要配置标志。

### Security boundary
### 安全边界

`chat_id` is a *capability*: anyone holding a valid WebSocket auth credential and the chat_id can attach to that conversation and see its output. This is safe for nanobot's local, single-user model. Multi-tenant deployments should namespace chat_ids per user (or introduce a per-tenant auth gate) — nanobot does not do this today.
`chat_id` 是一种*功能*：任何持有有效 WebSocket 身份验证凭证和 chat_id 的人都可以附加到该对话并查看其输出。这对于纳米机器人的本地单用户模型来说是安全的。多租户部署应该为每个用户命名空间 chat_ids（或引入每个租户的身份验证门）——现在 Nanobot 还没有这样做。

## Security Notes
## 安全说明

- **Timing-safe comparison**: Static token validation uses `hmac.compare_digest` to prevent timing attacks.
- **定时安全比较**：静态令牌验证使用`hmac.compare_digest`来防止定时攻击。
- **Defense in depth**: `allowFrom` is checked at both the HTTP handshake level and the message level.
- **深度防御**：在HTTP握手级别和消息级别都检查`allowFrom`。
- **chat_id as capability**: see [Multi-chat multiplexing](#multi-chat-multiplexing). Auth on the WebSocket handshake is the single line of defense; callers who pass it can attach to any chat_id they know.
- **chat_id 作为功能**：参见 [Multi-chat multiplexing](#multi-chat-multiplexing)。 WebSocket 握手上的身份验证是单道防线；传递它的呼叫者可以附加到他们知道的任何 chat_id。
- **TLS enforcement**: When SSL is enabled, TLSv1.2 is the minimum allowed version.
- **TLS 强制**：启用 SSL 时，TLSv1.2 是允许的最低版本。
- **Default-secure**: `websocketRequiresToken` defaults to `true`. Explicitly set it to `false` only on trusted networks.
- **默认安全**：`websocketRequiresToken` 默认为`true`。仅在可信网络上将其显式设置为`false`。

## Media Files
## 媒体文件

Outbound `message` events may include a `media` field containing local filesystem paths. Remote clients cannot access these files directly — they need either:
出站 `message` 事件可能包括包含本地文件系统路径的 `media` 字段。远程客户端无法直接访问这些文件 - 他们需要：

- A shared filesystem mount, or
- 共享文件系统挂载，或
- An HTTP file server serving the nanobot media directory
- 为 Nanobot 媒体目录提供服务的 HTTP 文件服务器

## Common Patterns
## 常见模式

### Trusted local network (no auth)
### 受信任的本地网络（无需身份验证）

```json
{
  "channels": {
    "websocket": {
      "enabled": true,
      "host": "0.0.0.0",
      "port": 8765,
      "websocketRequiresToken": false,
      "allowFrom": ["*"],
      "streaming": true
    }
  }
}
```

### Static token (simple auth)
### 静态令牌（简单身份验证）

```json
{
  "channels": {
    "websocket": {
      "enabled": true,
      "token": "my-shared-secret",
      "allowFrom": ["alice", "bob"]
    }
  }
}
```

Clients connect with `?token=my-shared-secret&client_id=alice`.
客户端与`?token=my-shared-secret&client_id=alice`连接。

### Public endpoint with issued tokens
### 具有已发行令牌的公共端点

```json
{
  "channels": {
    "websocket": {
      "enabled": true,
      "host": "0.0.0.0",
      "port": 8765,
      "path": "/ws",
      "tokenIssuePath": "/auth/token",
      "tokenIssueSecret": "production-secret",
      "websocketRequiresToken": true,
      "sslCertfile": "/etc/ssl/certs/server.pem",
      "sslKeyfile": "/etc/ssl/private/server-key.pem",
      "allowFrom": ["*"]
    }
  }
}
```

### Custom path
### 自定义路径

```json
{
  "channels": {
    "websocket": {
      "enabled": true,
      "path": "/chat/ws",
      "allowFrom": ["*"]
    }
  }
}
```

Clients connect to `ws://127.0.0.1:8765/chat/ws?client_id=...`. Trailing slashes are normalized, so `/chat/ws/` works the same.
客户端连接到`ws://127.0.0.1:8765/chat/ws?client_id=...`。尾部斜杠已标准化，因此 `/chat/ws/` 的作用相同。
