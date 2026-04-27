# Install and Quick Start
# 安装和快速启动

## Install
## 安装

> [!IMPORTANT]
> [！重要的]
> This README may describe features that are available first in the latest source code.
> 本自述文件可能描述最新源代码中首先提供的功能。
> If you want the newest features and experiments, install from source.
> 如果您想要最新的功能和实验，请从源代码安装。
> If you want the most stable day-to-day experience, install from PyPI or with `uv`.
> 如果您想要最稳定的日常体验，请从 PyPI 或使用 `uv` 安装。

**Install from source** (latest features, experimental changes may land here first; recommended for development)
**从源代码安装**（最新功能、实验性更改可能首先出现在此处；建议用于开发）

```bash
git clone https://github.com/HKUDS/nanobot.git
cd nanobot
pip install -e .
```

**Install with [uv](https://github.com/astral-sh/uv)** (stable release, fast)
**使用[uv](https://github.com/astral-sh/uv)**安装（稳定发布，快速）

```bash
uv tool install nanobot-ai
```

**Install from PyPI** (stable release)
**从 PyPI 安装**（稳定版本）

```bash
pip install nanobot-ai
```

### Update to latest version
### 更新到最新版本

**PyPI / pip**
**PyPI / 点**

```bash
pip install -U nanobot-ai
nanobot --version
```

**uv**
**紫外线**

```bash
uv tool upgrade nanobot-ai
nanobot --version
```

**Using WhatsApp?** Rebuild the local bridge after upgrading:
**使用 WhatsApp？** 升级后重建本地网桥：

```bash
rm -rf ~/.nanobot/bridge
nanobot channels login whatsapp
```

## Quick Start
## 快速入门

> [!TIP]
> [！提示]
> Set your API key in `~/.nanobot/config.json`.
> 在 `~/.nanobot/config.json` 中设置您的 API 密钥。
> Get API keys: [OpenRouter](https://openrouter.ai/keys) (Global)
> 获取 API 密钥：[OpenRouter](https://openrouter.ai/keys)（全局）
>
> For other LLM providers, please see [`configuration.md`](./configuration.md).
> 对于其他 LLM 提供商，请参阅[`configuration.md`](./configuration.md)。
>
> For web search capability setup, please see the web-search section in [`configuration.md`](./configuration.md#web-search).
> 对于网络搜索功能设置，请参阅[`configuration.md`](./configuration.md#web-search)中的网络搜索部分。

**1. Initialize**
**1.初始化**

```bash
nanobot onboard
```

Use `nanobot onboard --wizard` if you want the interactive setup wizard.
如果您想要交互式设置向导，请使用`nanobot onboard --wizard`。

**2. Configure** (`~/.nanobot/config.json`)
**2.配置** (`~/.nanobot/config.json`)

Configure these **two parts** in your config (other options have defaults).
在您的配置中配置这**两个部分**（其他选项有默认值）。

*Set your API key* (e.g. OpenRouter, recommended for global users):
*设置您的API密钥*（例如OpenRouter，推荐全球用户）：
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
*设置您的模型*（可选择固定提供商 - 默认为自动检测）：
```json
{
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-5",
      "provider": "openrouter"
    }
  }
}
```

**3. Chat**
**3.聊天**

```bash
nanobot agent
```

That's it! You have a working AI agent in 2 minutes.
就是这样！ 2 分钟内您就拥有了一个可以工作的 AI 代理。
