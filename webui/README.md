# nanobot webui
# nanobot webui

The browser front-end for the nanobot gateway. It is built with Vite + React 18 +
TypeScript + Tailwind 3 + shadcn/ui, talks to the gateway over the WebSocket
multiplex protocol, and reads session metadata from the embedded REST surface
on the same port.
nanobot 网关的浏览器前端。它基于 Vite + React 18 + TypeScript + Tailwind 3 + shadcn/ui 构建，通过 WebSocket multiplex protocol 与网关通信，并从同一端口上的嵌入式 REST 接口读取会话元数据。

For the project overview, install guide, and general docs map, see the root
[`README.md`](../README.md).
如需查看项目概览、安装指南和通用文档索引，请参阅根目录的 [`README.md`](../README.md)。

## Current status
## 当前状态

> [!NOTE]
> The standalone WebUI development workflow currently requires a source
> checkout.
> 独立 WebUI 开发流程目前需要源码检出。
>
> WebUI changes in the GitHub repository may land before they are included in
> the next packaged release, so source installs and published package versions
> are not yet guaranteed to move in lockstep.
> GitHub 仓库中的 WebUI 变更可能会先于下一次打包发布合入，因此源码安装版本与已发布包版本目前尚不保证同步推进。

## Layout
## 布局

```text
webui/                 source tree (this directory)
nanobot/web/dist/      build output served by the gateway
```

## Develop from source
## 从源码开发

### 1. Install nanobot from source
### 1. 从源码安装 nanobot

From the repository root:
在仓库根目录中：

```bash
pip install -e .
```

### 2. Enable the WebSocket channel
### 2. 启用 WebSocket 通道

In `~/.nanobot/config.json`:
在 `~/.nanobot/config.json` 中：

```json
{ "channels": { "websocket": { "enabled": true } } }
```

### 3. Start the gateway
### 3. 启动网关

In one terminal:
在一个终端中：

```bash
nanobot gateway
```

### 4. Start the WebUI dev server
### 4. 启动 WebUI 开发服务器

In another terminal:
在另一个终端中：

```bash
cd webui
bun install            # npm install also works
bun run dev
```

Then open `http://127.0.0.1:5173`.
然后打开 `http://127.0.0.1:5173`。

By default, the dev server proxies `/api`, `/webui`, `/auth`, and WebSocket
traffic to `http://127.0.0.1:8765`.
默认情况下，开发服务器会将 `/api`、`/webui`、`/auth` 以及 WebSocket 流量代理到 `http://127.0.0.1:8765`。

If your gateway listens on a non-default port, point the dev server at it:
如果你的网关监听非默认端口，请将开发服务器指向该端口：

```bash
NANOBOT_API_URL=http://127.0.0.1:9000 bun run dev
```

## Build for packaged runtime
## 为打包运行时构建

```bash
cd webui
bun run build
```

This writes the production assets to `../nanobot/web/dist`, which is the
directory served by `nanobot gateway` and bundled into the Python wheel.
这会将生产资源写入 `../nanobot/web/dist`，该目录由 `nanobot gateway` 提供服务，并会打包进 Python wheel。

If you are cutting a release, run the build before packaging so the published
wheel contains the current WebUI assets.
如果你正在发布版本，请在打包前运行构建，以便发布的 wheel 包含当前 WebUI 资源。

## Test
## 测试

```bash
cd webui
bun run test
```

## Acknowledgements
## 致谢

- [`agent-chat-ui`](https://github.com/langchain-ai/agent-chat-ui) for UI and
  interaction inspiration across the chat surface.
- 感谢 [`agent-chat-ui`](https://github.com/langchain-ai/agent-chat-ui) 为聊天界面的 UI 和交互提供灵感。
