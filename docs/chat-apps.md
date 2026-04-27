# Chat Apps
# 聊天应用程序

Connect nanobot to your favorite chat platform. Want to build your own? See the [Channel Plugin Guide](./channel-plugin-guide.md).
将纳米机器人连接到您最喜欢的聊天平台。想建立自己的吗？参见[Channel Plugin Guide](./channel-plugin-guide.md)。

| Channel<br>渠道 | What you need<br>你需要什么 |
|---------|---------------|
| **Telegram**<br>**电报** | Bot token from @BotFather<br>来自 @BotFather 的机器人令牌 |
| **Discord**<br>**不和谐** | Bot token + Message Content intent<br>机器人令牌+消息内容意图 |
| **WhatsApp**<br>**WhatsApp** | QR code scan (`nanobot channels login whatsapp`)<br>二维码扫描（`nanobot channels login whatsapp`） |
| **WeChat (Weixin)**<br>**微信(Weixin)** | QR code scan (`nanobot channels login weixin`)<br>二维码扫描（`nanobot channels login whatsapp`） |
| **Feishu**<br>**飞鼠** | App ID + App Secret<br>应用ID+应用秘密 |
| **DingTalk**<br>**钉钉** | App Key + App Secret<br>应用密钥+应用秘密 |
| **Slack**<br>**松弛** | Bot token + App-Level token<br>机器人代币 + 应用级代币 |
| **Matrix**<br>**矩阵** | Homeserver URL + Access token<br>主服务器 URL + 访问令牌 |
| **Email**<br>**电子邮件** | IMAP/SMTP credentials<br>IMAP/SMTP 凭据 |
| **QQ**<br>**QQ** | App ID + App Secret<br>应用ID+应用秘密 |
| **Wecom**<br>**威康** | Bot ID + Bot Secret<br>机器人 ID + 机器人秘密 |
| **Microsoft Teams**<br>**微软团队** | App ID + App Password + public HTTPS endpoint<br>应用程序 ID + 应用程序密码 + 公共 HTTPS 端点 |
| **Mochat**<br>**摩卡** | Claw token (auto-setup available)<br>爪令牌（可自动设置） |

<details>
<summary><b>Telegram</b> (Recommended)</summary>
<p>电报（推荐）</p>

**1. Create a bot**
**1.创建一个机器人**
- Open Telegram, search `@BotFather`
- 打开 Telegram，搜索 `@BotFather`
- Send `/newbot`, follow prompts
- 发送`/newbot`，按照提示操作
- Copy the token
- 复制令牌

**2. Configure**
**2.配置**

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["YOUR_USER_ID"]
    }
  }
}
```

> You can find your **User ID** in Telegram settings. It is shown as `@yourUserId`.
> 您可以在 Telegram 设置中找到您的**用户 ID**。显示为`@yourUserId`。
> Copy this value **without the `@` symbol** and paste it into the config file.
> 复制此值**不带 `@` 符号**并将其粘贴到配置文件中。


**3. Run**
**3.跑步**

```bash
nanobot gateway
```

</details>

<details>
<summary><b>Mochat (Claw IM)</b></summary>
<p>Mochat（爪即时通讯）</p>

Uses **Socket.IO WebSocket** by default, with HTTP polling fallback.
默认情况下使用 **Socket.IO WebSocket**，并使用 HTTP 轮询回退。

**1. Ask nanobot to set up Mochat for you**
**1.请 nanobot 为您设置 Mochat**

Simply send this message to nanobot (replace `xxx@xxx` with your real email):
只需将此消息发送给 Nanobot（将 `xxx@xxx` 替换为您的真实电子邮件）：

```
Read https://raw.githubusercontent.com/HKUDS/MoChat/refs/heads/main/skills/nanobot/skill.md and register on MoChat. My Email account is xxx@xxx Bind me as your owner and DM me on MoChat.
```

nanobot will automatically register, configure `~/.nanobot/config.json`, and connect to Mochat.
nanobot将自动注册、配置`~/.nanobot/config.json`并连接到Mochat。

**2. Restart gateway**
**2.重新启动网关**

```bash
nanobot gateway
```

That's it — nanobot handles the rest!
就是这样——纳米机器人处理剩下的事情！

<br>

<details>
<summary>Manual configuration (advanced)</summary>
<p>手动配置（高级）</p>

If you prefer to configure manually, add the following to `~/.nanobot/config.json`:
如果您更喜欢手动配置，请将以下内容添加到 `~/.nanobot/config.json`：

> Keep `claw_token` private. It should only be sent in `X-Claw-Token` header to your Mochat API endpoint.
> 保持 `claw_token` 的私密性。它只能在 `X-Claw-Token` 标头中发送到您的 Mochat API 端点。

```json
{
  "channels": {
    "mochat": {
      "enabled": true,
      "base_url": "https://mochat.io",
      "socket_url": "https://mochat.io",
      "socket_path": "/socket.io",
      "claw_token": "claw_xxx",
      "agent_user_id": "6982abcdef",
      "sessions": ["*"],
      "panels": ["*"],
      "reply_delay_mode": "non-mention",
      "reply_delay_ms": 120000
    }
  }
}
```



</details>

</details>

<details>
<summary><b>Discord</b></summary>
<p>不和谐</p>

**1. Create a bot**
**1.创建一个机器人**
- Go to https://discord.com/developers/applications
- 前往https://discord.com/developers/applications
- Create an application → Bot → Add Bot
- 创建应用程序 → 机器人 → 添加机器人
- Copy the bot token
- 复制机器人令牌

**2. Enable intents**
**2.启用意图**
- In the Bot settings, enable **MESSAGE CONTENT INTENT**
- 在机器人设置中，启用 **消息内容意图**
- (Optional) Enable **SERVER MEMBERS INTENT** if you plan to use allow lists based on member data
- （可选）如果您计划使用基于成员数据的允许列表，请启用 **服务器成员意图**

**3. Get your User ID**
**3.获取您的用户 ID**
- Discord Settings → Advanced → enable **Developer Mode**
- Discord 设置 → 高级 → 启用 **开发者模式**
- Right-click your avatar → **Copy User ID**
- 右键单击您的头像 → **复制用户 ID**

**4. Configure**
**4.配置**

```json
{
  "channels": {
    "discord": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["YOUR_USER_ID"],
      "allowChannels": [],
      "groupPolicy": "mention",
      "streaming": true
    }
  }
}
```

> `groupPolicy` controls how the bot responds in group channels:
> `groupPolicy` 控制机器人在群组频道中的响应方式：
> - `"mention"` (default) — Only respond when @mentioned
> - `"mention"`（默认）- 仅在@提及时响应
> - `"open"` — Respond to all messages
> - `"open"` — 回复所有消息
> DMs always respond when the sender is in `allowFrom`.
> 当发件人处于 `allowFrom` 时，DM 始终会做出响应。
> - If you set group policy to open create new threads as private threads and then @ the bot into it. Otherwise the thread itself and the channel in which you spawned it will spawn a bot session.
> - 如果您将组策略设置为打开创建新线程作为私有线程，然后@机器人进入其中。否则，线程本身和您生成它的通道将生成一个机器人会话。
> `allowChannels` restricts the bot to specific Discord channel IDs. Empty (default) means respond in every channel the bot can see. Example: `["1234567890", "0987654321"]`. The filter applies after `allowFrom`, so both must pass.
> `allowChannels` 将机器人限制为特定的 Discord 频道 ID。空（默认）意味着在机器人可以看到的每个通道中做出响应。示例：`["1234567890", "0987654321"]`。过滤器在 `allowFrom` 之后应用，因此两者都必须通过。
> `streaming` defaults to `true`. Disable it only if you explicitly want non-streaming replies.
> `streaming` 默认为 `true`。仅当您明确想要非流式回复时才禁用它。

**5. Invite the bot**
**5.邀请机器人**
- OAuth2 → URL Generator
- OAuth2 → URL 生成器
- Scopes: `bot`
- 范围：`bot`
- Bot Permissions: `Send Messages`, `Read Message History`
- 机器人权限：`Send Messages`、`Read Message History`
- Open the generated invite URL and add the bot to your server
- 打开生成的邀请 URL 并将机器人添加到您的服务器

**6. Run**
**6。跑步**

```bash
nanobot gateway
```

</details>

<details>
<summary><b>Matrix (Element)</b></summary>
<p>矩阵（元素）</p>

Install Matrix dependencies first:
首先安装 Matrix 依赖项：

```bash
pip install nanobot-ai[matrix]
```

> [!NOTE]
> [！笔记]
> Matrix is not supported on Windows. `matrix-nio[e2e]` depends on
> Windows 不支持矩阵。 `matrix-nio[e2e]` 取决于
> `python-olm`, which has no pre-built Windows wheel and is skipped by the
> `python-olm`，没有预先构建的 Windows 滚轮，并且被跳过
> `matrix` extra on `sys_platform == 'win32'`. The command above will still
> `sys_platform == 'win32'` 额外`matrix`。上面的命令仍然会
> succeed on Windows but without `matrix-nio` installed, so enabling the
> 在 Windows 上成功，但未安装 `matrix-nio`，因此启用
> Matrix channel will fail at startup. Use macOS, Linux, or WSL2.
> 矩阵通道将在启动时失败。使用 macOS、Linux 或 WSL2。

**1. Create/choose a Matrix account**
**1.创建/选择 Matrix 帐户**

- Create or reuse a Matrix account on your homeserver (for example `matrix.org`).
- 在您的家庭服务器上创建或重复使用 Matrix 帐户（例如 `matrix.org`）。
- Confirm you can log in with Element.
- 确认您可以使用 Element 登录。

**2. Get credentials**
**2.获取凭证**

- You need:
- 您需要：
  - `userId` (example: `@nanobot:matrix.org`)
  - `userId`（示例：`@nanobot:matrix.org`）
  - `password`

(Note: `accessToken` and `deviceId` are still supported for legacy reasons, but
（注意：由于遗留原因，仍然支持`accessToken`和`deviceId`，但是
for reliable encryption, password login is recommended instead. If the
为了可靠的加密，建议使用密码登录。如果
`password` is provided, `accessToken` and `deviceId` will be ignored.)
提供了`password`，`accessToken`和`deviceId`将被忽略。）

**3. Configure**
**3.配置**

```json
{
  "channels": {
    "matrix": {
      "enabled": true,
      "homeserver": "https://matrix.org",
      "userId": "@nanobot:matrix.org",
      "password": "mypasswordhere",
      "e2eeEnabled": true,
      "allowFrom": ["@your_user:matrix.org"],
      "groupPolicy": "open",
      "groupAllowFrom": [],
      "allowRoomMentions": false,
      "maxMediaBytes": 20971520
    }
  }
}
```

> Keep a persistent `matrix-store` — encrypted session state is lost if these change across restarts.
> 保持持久的 `matrix-store` — 如果这些状态在重新启动时发生变化，加密的会话状态就会丢失。

| Option<br>选项 | Description<br>描述 |
|--------|-------------|
| `allowFrom`<br>`allowFrom` | User IDs allowed to interact. Empty denies all; use `["*"]` to allow everyone.<br>允许交互的用户 ID。空虚否定一切；使用 `["*"]` 允许所有人。 |
| `groupPolicy`<br>`groupPolicy` | `open` (default), `mention`, or `allowlist`.<br>`open`（默认）、`mention`或`allowlist`。 |
| `groupAllowFrom`<br>`groupAllowFrom` | Room allowlist (used when policy is `allowlist`).<br>房间许可名单（当政策为 `allowlist` 时使用）。 |
| `allowRoomMentions`<br>`allowRoomMentions` | Accept `@room` mentions in mention mode.<br>在提及模式下接受`@room`提及。 |
| `e2eeEnabled`<br>`e2eeEnabled` | E2EE support (default `true`). Set `false` for plaintext-only.<br>E2EE 支持（默认`true`）。将 `false` 设置为纯文本。 |
| `maxMediaBytes`<br>`maxMediaBytes` | Max attachment size (default `20MB`). Set `0` to block all media.<br>最大附件大小（默认`20MB`）。设置 `0` 以阻止所有媒体。 |




**4. Run**
**4.跑步**

```bash
nanobot gateway
```

</details>

<details>
<summary><b>WhatsApp</b></summary>
<p>WhatsApp</p>

Requires **Node.js ≥18**.
需要 **Node.js ≥18**。

**1. Link device**
**1.链接设备**

```bash
nanobot channels login whatsapp
# Scan QR with WhatsApp → Settings → Linked Devices
```

**2. Configure**
**2.配置**

```json
{
  "channels": {
    "whatsapp": {
      "enabled": true,
      "allowFrom": ["+1234567890"]
    }
  }
}
```

**3. Run** (two terminals)
**3.运行**（两个终端）

```bash
# Terminal 1
nanobot channels login whatsapp

# Terminal 2
nanobot gateway
```

> WhatsApp bridge updates are not applied automatically for existing installations.
> WhatsApp 桥接更新不会自动应用于现有安装。
> After upgrading nanobot, rebuild the local bridge with:
> 升级 nanobot 后，使用以下命令重建本地网桥：
> `rm -rf ~/.nanobot/bridge && nanobot channels login whatsapp`

</details>

<details>
<summary><b>Feishu</b></summary>
<p>飞书</p>

Uses **WebSocket** long connection — no public IP required.
使用 **WebSocket** 长连接 — 不需要公共 IP。

**1. Create a Feishu bot**
**1.创建飞书机器人**
- Visit [Feishu Open Platform](https://open.feishu.cn/app)
- 访问[Feishu Open Platform](https://open.feishu.cn/app)
- Create a new app → Enable **Bot** capability
- 创建新应用程序 → 启用 **Bot** 功能
- **Permissions**:
- **权限**：
  - `im:message` (send messages) and `im:message.p2p_msg:readonly` (receive messages)
  - `im:message`（发送消息）和`im:message.p2p_msg:readonly`（接收消息）
  - **Streaming replies** (default in nanobot): add **`cardkit:card:write`** (often labeled **Create and update cards** in the Feishu developer console). Required for CardKit entities and streamed assistant text. Older apps may not have it yet — open **Permission management**, enable the scope, then **publish** a new app version if the console requires it.
  - **流式回复**（nanobot中默认）：添加**`cardkit:card:write`**（通常在飞书开发者控制台中标记为**创建和更新卡片**）。 CardKit 实体和流式助理文本是必需的。较旧的应用程序可能还没有 - 打开**权限管理**，启用范围，然后**发布**新的应用程序版本（如果控制台需要）。
  - If you **cannot** add `cardkit:card:write`, set `"streaming": false` under `channels.feishu` (see below). The bot still works; replies use normal interactive cards without token-by-token streaming.
  - 如果您**无法**添加 `cardkit:card:write`，请在 `channels.feishu` 下设置 `"streaming": false`（见下文）。机器人仍然可以工作；回复使用普通的交互式卡，无需逐个令牌流式传输。
- **Events**: Add `im.message.receive_v1` (receive messages)
- **活动**：添加`im.message.receive_v1`（接收消息）
  - Select **Long Connection** mode (requires running nanobot first to establish connection)
  - 选择**长连接**模式（需要先运行nanobot才能建立连接）
- Get **App ID** and **App Secret** from "Credentials & Basic Info"
- 从“凭据和基本信息”获取 **App ID** 和 **App Secret**
- Publish the app
- 发布应用程序

**2. Configure**
**2.配置**

```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "cli_xxx",
      "appSecret": "xxx",
      "encryptKey": "",
      "verificationToken": "",
      "allowFrom": ["ou_YOUR_OPEN_ID"],
      "groupPolicy": "mention",
      "reactEmoji": "OnIt",
      "doneEmoji": "DONE",
      "toolHintPrefix": "🔧",
      "streaming": true,
      "domain": "feishu"
    }
  }
}
```

> `streaming` defaults to `true`. Use `false` if your app does not have **`cardkit:card:write`** (see permissions above).
> `streaming` 默认为 `true`。如果您的应用没有 **`cardkit:card:write`** （请参阅上面的权限），请使用 `false`。
> `encryptKey` and `verificationToken` are optional for Long Connection mode.
> 对于长连接模式，`encryptKey`和`verificationToken`是可选的。
> `allowFrom`: Add your open_id (find it in nanobot logs when you message the bot). Use `["*"]` to allow all users.
> `allowFrom`：添加您的 open_id（当您向机器人发送消息时，可以在 Nanobot 日志中找到它）。使用 `["*"]` 允许所有用户。
> `groupPolicy`: `"mention"` (default — respond only when @mentioned), `"open"` (respond to all group messages). Private chats always respond.
> `groupPolicy`：`"mention"`（默认 — 仅在@提及时回复），`"open"`（回复所有群组消息）。私人聊天总是回复。
> `reactEmoji`: Emoji for "processing" status (default: `OnIt`). See [available emojis](https://open.larkoffice.com/document/server-docs/im-v1/message-reaction/emojis-introduce).
> `reactEmoji`：“正在处理”状态的表情符号（默认：`OnIt`）。参见[available emojis](https://open.larkoffice.com/document/server-docs/im-v1/message-reaction/emojis-introduce)。
> `doneEmoji`: Optional emoji for "completed" status (e.g., `DONE`, `OK`, `HEART`). When set, bot adds this reaction after removing `reactEmoji`.
> `doneEmoji`：表示“已完成”状态的可选表情符号（例如，`DONE`、`OK`、`HEART`）。设置后，机器人会在删除 `reactEmoji` 后添加此反应。
> `toolHintPrefix`: Prefix for inline tool hints in streaming cards (default: `🔧`).
> `toolHintPrefix`：流卡中内联工具提示的前缀（默认值：`🔧`）。
> `domain`: `"feishu"` (default) for China (open.feishu.cn), `"lark"` for international Lark (open.larksuite.com).
> `domain`：中国（open.feishu.cn）`"feishu"`（默认），国际 Lark（open.larksuite.com）`"lark"`。

**3. Run**
**3.跑步**

```bash
nanobot gateway
```

> [!TIP]
> [!提示]
> Feishu uses WebSocket to receive messages — no webhook or public IP needed!
> 飞书使用WebSocket接收消息——无需webhook或公共IP！

</details>

<details>
<summary><b>QQ (QQ单聊)</b></summary>
<p>QQ (QQ单聊)</p>

Uses **botpy SDK** with WebSocket — no public IP required. Currently supports **private messages only**.
使用 **botpy SDK** 和 WebSocket，无需公网 IP。目前仅支持**私聊消息**。

**1. Register & create bot**
**1. 注册并创建机器人**
- Visit [QQ Open Platform](https://q.qq.com) → Register as a developer (personal or enterprise)
- 访问[QQ Open Platform](https://q.qq.com) → 注册成为开发者（个人或企业）
- Create a new bot application
- 创建新的机器人应用
- Go to **开发设置 (Developer Settings)** → copy **AppID** and **AppSecret**
- 进入**开发设置（开发者设置）** → 复制**AppID** 和 **AppSecret**

**2. Set up sandbox for testing**
**2. 设置用于测试的沙盒**
- In the bot management console, find **沙箱配置 (Sandbox Config)**
- 在机器人管理控制台中，找到**沙箱配置（Sandbox Config）**
- Under **在消息列表配置**, click **添加成员** and add your own QQ number
- 在**在消息列表配置**下，点击**添加成员**，添加自己的QQ号
- Once added, scan the bot's QR code with mobile QQ → open the bot profile → tap "发消息" to start chatting
- 添加后，用手Q扫描机器人二维码→打开机器人资料→点击“发消息”开始聊天

**3. Configure**
**3.配置**

> - `allowFrom`: Add your openid (find it in nanobot logs when you message the bot). Use `["*"]` for public access.
> - `allowFrom`：添加您的 openid（当您向机器人发送消息时，可以在 Nanobot 日志中找到它）。使用`["*"]`进行公共访问。
> - `msgFormat`: Optional. Use `"plain"` (default) for maximum compatibility with legacy QQ clients, or `"markdown"` for richer formatting on newer clients.
> - `msgFormat`：可选。使用 `"plain"`（默认）可最大限度地兼容旧版 QQ 客户端，或使用 `"markdown"` 在新客户端上实现更丰富的格式。
> - For production: submit a review in the bot console and publish. See [QQ Bot Docs](https://bot.q.qq.com/wiki/) for the full publishing flow.
> - 对于生产：在机器人控制台中提交评论并发布。完整的发布流程请参见[QQ Bot Docs](https://bot.q.qq.com/wiki/)。

```json
{
  "channels": {
    "qq": {
      "enabled": true,
      "appId": "YOUR_APP_ID",
      "secret": "YOUR_APP_SECRET",
      "allowFrom": ["YOUR_OPENID"],
      "msgFormat": "plain"
    }
  }
}
```

**4. Run**
**4.跑步**

```bash
nanobot gateway
```

Now send a message to the bot from QQ — it should respond!
现在从 QQ 给机器人发送消息，它应该会回复。

</details>

<details>
<summary><b>DingTalk (钉钉)</b></summary>
<p>DingTalk (钉钉)</p>

Uses **Stream Mode** — no public IP required.
使用 **流模式** — 无需公共 IP。

**1. Create a DingTalk bot**
**1.创建钉钉机器人**
- Visit [DingTalk Open Platform](https://open-dev.dingtalk.com/)
- 访问[Feishu Open Platform](https://open.feishu.cn/app)
- Create a new app -> Add **Robot** capability
- 创建一个新应用程序 -> 添加 **机器人** 功能
- **Configuration**:
- **配置**：
  - Toggle **Stream Mode** ON
  - 打开**流模式**
- **Permissions**: Add necessary permissions for sending messages
- **权限**：添加发送消息所需的权限
- Get **AppKey** (Client ID) and **AppSecret** (Client Secret) from "Credentials"
- 从“凭据”获取 **AppKey**（客户端 ID）和 **AppSecret**（客户端密钥）
- Publish the app
- 发布应用程序

**2. Configure**
**2.配置**

```json
{
  "channels": {
    "dingtalk": {
      "enabled": true,
      "clientId": "YOUR_APP_KEY",
      "clientSecret": "YOUR_APP_SECRET",
      "allowFrom": ["YOUR_STAFF_ID"]
    }
  }
}
```

> `allowFrom`: Add your staff ID. Use `["*"]` to allow all users.
> `allowFrom`：添加您的员工ID。使用 `["*"]` 允许所有用户。

**3. Run**
**3.跑步**

```bash
nanobot gateway
```

</details>

<details>
<summary><b>Slack</b></summary>
<p>Slack</p>

Uses **Socket Mode** — no public URL required.
使用**套接字模式** — 不需要公共 URL。

**1. Create a Slack app**
**1.创建 Slack 应用程序**
- Go to [Slack API](https://api.slack.com/apps) → **Create New App** → "From scratch"
- 转到 [Slack API](https://api.slack.com/apps) → **创建新应用程序** → “从头开始”
- Pick a name and select your workspace
- 选择一个名称并选择您的工作空间

**2. Configure the app**
**2.配置应用程序**
- **Socket Mode**: Toggle ON → Generate an **App-Level Token** with `connections:write` scope → copy it (`xapp-...`)
- **套接字模式**：打开→生成具有`connections:write`范围的**应用程序级令牌**→复制它（`xapp-...`）
- **OAuth & Permissions**: Add bot scopes: `chat:write`, `reactions:write`, `app_mentions:read`
- **OAuth 和权限**：添加机器人范围：`chat:write`、`reactions:write`、`app_mentions:read`
- **Event Subscriptions**: Toggle ON → Subscribe to bot events: `message.im`, `message.channels`, `app_mention` → Save Changes
- **事件订阅**：打开 → 订阅机器人事件：`message.im`、`message.channels`、`app_mention` → 保存更改
- **App Home**: Scroll to **Show Tabs** → Enable **Messages Tab** → Check **"Allow users to send Slash commands and messages from the messages tab"**
- **应用程序主页**：滚动到 **显示选项卡** → 启用 **消息选项卡** → 选中 **“允许用户从消息选项卡发送 Slash 命令和消息”**
- **Install App**: Click **Install to Workspace** → Authorize → copy the **Bot Token** (`xoxb-...`)
- **安装应用程序**：点击**安装到工作区**→授权→复制**Bot Token**（`xoxb-...`）

**3. Configure nanobot**
**3.配置纳米机器人**

```json
{
  "channels": {
    "slack": {
      "enabled": true,
      "botToken": "xoxb-...",
      "appToken": "xapp-...",
      "allowFrom": ["YOUR_SLACK_USER_ID"],
      "groupPolicy": "mention"
    }
  }
}
```

**4. Run**
**4.跑步**

```bash
nanobot gateway
```

DM the bot directly or @mention it in a channel — it should respond!
直接私信机器人或在频道中@提及它 - 它应该做出响应！

> [!TIP]
> [!提示]
> - `groupPolicy`: `"mention"` (default — respond only when @mentioned), `"open"` (respond to all channel messages), or `"allowlist"` (restrict to specific channels).
> - `groupPolicy`：`"mention"`（默认 — 仅在@提及时响应）、`"open"`（响应所有频道消息）或`"allowlist"`（仅限特定频道）。
> - DM policy defaults to open. Set `"dm": {"enabled": false}` to disable DMs.
> - DM 策略默认打开。设置 `"dm": {"enabled": false}` 以禁用 DM。

</details>

<details>
<summary><b>Email</b></summary>
<p>电子邮件</p>

Give nanobot its own email account. It polls **IMAP** for incoming mail and replies via **SMTP** — like a personal email assistant.
为纳米机器人提供自己的电子邮件帐户。它轮询 **IMAP** 接收邮件并通过 **SMTP** 进行回复 - 就像个人电子邮件助理一样。

**1. Get credentials (Gmail example)**
**1.获取凭据（Gmail 示例）**
- Create a dedicated Gmail account for your bot (e.g. `my-nanobot@gmail.com`)
- 为您的机器人创建专用 Gmail 帐户（例如 `my-nanobot@gmail.com`）
- Enable 2-Step Verification → Create an [App Password](https://myaccount.google.com/apppasswords)
- 启用两步验证→创建[App Password](https://myaccount.google.com/apppasswords)
- Use this app password for both IMAP and SMTP
- 将此应用程序密码用于 IMAP 和 SMTP

**2. Configure**
**2.配置**

> - `consentGranted` must be `true` to allow mailbox access. This is a safety gate — set `false` to fully disable.
> - `consentGranted` 必须为 `true` 才能允许邮箱访问。这是一个安全门 — 将 `false` 设置为完全禁用。
> - `allowFrom`: Add your email address. Use `["*"]` to accept emails from anyone.
> - `allowFrom`：添加您的电子邮件地址。使用 `["*"]` 接受任何人发来的电子邮件。
> - `smtpUseTls` and `smtpUseSsl` default to `true` / `false` respectively, which is correct for Gmail (port 587 + STARTTLS). No need to set them explicitly.
> - `smtpUseTls` 和 `smtpUseSsl` 默认分别为 `true` / `false`，这对于 Gmail（端口 587 + STARTTLS）是正确的。无需显式设置它们。
> - Set `"autoReplyEnabled": false` if you only want to read/analyze emails without sending automatic replies.
> - 如果您只想阅读/分析电子邮件而不发送自动回复，请设置`"autoReplyEnabled": false`。
> - `allowedAttachmentTypes`: Save inbound attachments matching these MIME types — `["*"]` for all, e.g. `["application/pdf", "image/*"]` (default `[]` = disabled).
> - `allowedAttachmentTypes`：保存与这些 MIME 类型匹配的入站附件 — `["*"]` 适用于所有附件，例如`["application/pdf", "image/*"]`（默认`[]` = 禁用）。
> - `maxAttachmentSize`: Max size per attachment in bytes (default `2000000` / 2MB).
> - `maxAttachmentSize`：每个附件的最大大小（以字节为单位）（默认`2000000`/2MB）。
> - `maxAttachmentsPerEmail`: Max attachments to save per email (default `5`).
> - `maxAttachmentsPerEmail`：每封电子邮件保存的最大附件数（默认`5`）。

```json
{
  "channels": {
    "email": {
      "enabled": true,
      "consentGranted": true,
      "imapHost": "imap.gmail.com",
      "imapPort": 993,
      "imapUsername": "my-nanobot@gmail.com",
      "imapPassword": "your-app-password",
      "smtpHost": "smtp.gmail.com",
      "smtpPort": 587,
      "smtpUsername": "my-nanobot@gmail.com",
      "smtpPassword": "your-app-password",
      "fromAddress": "my-nanobot@gmail.com",
      "allowFrom": ["your-real-email@gmail.com"],
      "allowedAttachmentTypes": ["application/pdf", "image/*"]
    }
  }
}
```


**3. Run**
**3.跑步**

```bash
nanobot gateway
```

</details>

<details>
<summary><b>WeChat (微信 / Weixin)</b></summary>
<p>微信（微信/Weixin）</p>

Uses **HTTP long-poll** with QR-code login via the ilinkai personal WeChat API. No local WeChat desktop client is required.
通过 ilinkai 个人微信 API 使用 **HTTP 长轮询** 和二维码登录。无需本地微信桌面客户端。

**1. Install with WeChat support**
**1.通过微信支持安装**

```bash
pip install "nanobot-ai[weixin]"
```

**2. Configure**
**2.配置**

```json
{
  "channels": {
    "weixin": {
      "enabled": true,
      "allowFrom": ["YOUR_WECHAT_USER_ID"]
    }
  }
}
```

> - `allowFrom`: Add the sender ID you see in nanobot logs for your WeChat account. Use `["*"]` to allow all users.
> - `allowFrom`：添加您在微信帐户的 Nanobot 日志中看到的发件人 ID。使用 `["*"]` 允许所有用户。
> - `token`: Optional. If omitted, log in interactively and nanobot will save the token for you.
> - `token`：可选。如果省略，则以交互方式登录，nanobot 将为您保存令牌。
> - `routeTag`: Optional. When your upstream Weixin deployment requires request routing, nanobot will send it as the `SKRouteTag` header.
> - `routeTag`：可选。当您的上游微信部署需要请求路由时，nanobot 会将其作为 `SKRouteTag` 标头发送。
> - `stateDir`: Optional. Defaults to nanobot's runtime directory for Weixin state.
> - `stateDir`：可选。默认为微信状态下 Nanobot 的运行时目录。
> - `pollTimeout`: Optional long-poll timeout in seconds.
> - `pollTimeout`：可选的长轮询超时（以秒为单位）。

**3. Login**
**3.登录**

```bash
nanobot channels login weixin
```

Use `--force` to re-authenticate and ignore any saved token:
使用 `--force` 重新验证并忽略任何保存的令牌：

```bash
nanobot channels login weixin --force
```

**4. Run**
**4.跑步**

```bash
nanobot gateway
```

</details>

<details>
<summary><b>Wecom (企业微信)</b></summary>
<p>Wecom（企业微信）</p>

> Here we use [wecom-aibot-sdk-python](https://github.com/chengyongru/wecom_aibot_sdk) (community Python version of the official [@wecom/aibot-node-sdk](https://www.npmjs.com/package/@wecom/aibot-node-sdk)).
> 这里我们使用[wecom-aibot-sdk-python](https://github.com/chengyongru/wecom_aibot_sdk)（官方[@wecom/aibot-node-sdk](https://www.npmjs.com/package/@wecom/aibot-node-sdk)的社区Python版本）。
>
> Uses **WebSocket** long connection — no public IP required.
> 使用 **WebSocket** 长连接 — 不需要公共 IP。

**1. Install the optional dependency**
**1.安装可选依赖项**

```bash
pip install nanobot-ai[wecom]
```

**2. Create a WeCom AI Bot**
**2.创建 WeCom AI 机器人**

Go to the WeCom admin console → Intelligent Robot → Create Robot → select **API mode** with **long connection**. Copy the Bot ID and Secret.
进入WeCom管理控制台→智能机器人→创建机器人→选择**API模式**和**长连接**。复制 Bot ID 和 Secret。

**3. Configure**
**3.配置**

```json
{
  "channels": {
    "wecom": {
      "enabled": true,
      "botId": "your_bot_id",
      "secret": "your_bot_secret",
      "allowFrom": ["your_id"]
    }
  }
}
```

**4. Run**
**4.跑步**

```bash
nanobot gateway
```

</details>

<details>
<summary><b>Microsoft Teams</b> (MVP — DM only)</summary>
<p>Microsoft Teams（MVP - 仅限 DM）</p>

> Direct-message text in/out, tenant-aware OAuth, conversation reference persistence.
> 直接消息文本输入/输出、租户感知 OAuth、对话参考持久性。
> Uses a public HTTPS webhook — no WebSocket; you need a tunnel or reverse proxy.
> 使用公共 HTTPS webhook — 无 WebSocket；您需要隧道或反向代理。

**1. Install the optional dependency**
**1.安装可选依赖项**

```bash
pip install nanobot-ai[msteams]
```

**2. Create a Teams / Azure bot app registration**
**2.创建 Teams/Azure 机器人应用程序注册**

Create or reuse a Microsoft Teams / Azure bot app registration. Set the bot messaging endpoint to a public HTTPS URL ending in `/api/messages`.
创建或重复使用 Microsoft Teams/Azure 机器人应用程序注册。将机器人消息传递端点设置为以 `/api/messages` 结尾的公共 HTTPS URL。

**3. Configure**
**3.配置**

```json
{
  "channels": {
    "msteams": {
      "enabled": true,
      "appId": "YOUR_APP_ID",
      "appPassword": "YOUR_APP_SECRET",
      "tenantId": "YOUR_TENANT_ID",
      "host": "0.0.0.0",
      "port": 3978,
      "path": "/api/messages",
      "allowFrom": ["*"],
      "replyInThread": true,
      "mentionOnlyResponse": "Hi — what can I help with?",
      "validateInboundAuth": true
    }
  }
}
```

> - `replyInThread: true` replies to the triggering Teams activity when a stored `activity_id` is available.
> - 当存储的 `activity_id` 可用时，`replyInThread: true` 回复触发 Teams 活动。
> - `mentionOnlyResponse` controls what Nanobot receives when a user sends only a bot mention (`<at>Nanobot</at>`). Set to `""` to ignore mention-only messages.
> - `mentionOnlyResponse` 控制当用户仅发送机器人提及时 Nanobot 接收的内容 (`<at>Nanobot</at>`)。设置为 `""` 以忽略仅提及的消息。
> - `validateInboundAuth: true` enables inbound Bot Framework bearer-token validation (signature, issuer, audience, lifetime, `serviceUrl`). This is the safe default for public deployments. Only set it to `false` for local development or tightly controlled testing.
> - `validateInboundAuth: true` 启用入站 Bot Framework 不记名令牌验证（签名、颁发者、受众、生命周期、`serviceUrl`）。这是公共部署的安全默认设置。仅将其设置为 `false` 用于本地开发或严格控制的测试。

**4. Run**
**4.跑步**

```bash
nanobot gateway
```

</details>
