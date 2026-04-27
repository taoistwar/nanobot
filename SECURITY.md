# Security Policy

# 安全政策

## Reporting a Vulnerability

## 报告漏洞

If you discover a security vulnerability in nanobot, please report it by:

如果你在 nanobot 中发现安全漏洞，请通过以下方式报告：

1. **DO NOT** open a public GitHub issue<br>**不要** 创建公开 GitHub issue
2. Create a private security advisory on GitHub or contact the repository maintainers (xubinrencs@gmail.com)<br>在 GitHub 上创建私有安全公告，或联系仓库维护者（xubinrencs@gmail.com）
3. Include:<br>请包含：
   - Description of the vulnerability<br>漏洞描述
   - Steps to reproduce<br>复现步骤
   - Potential impact<br>潜在影响
   - Suggested fix (if any)<br>建议修复方案（如有）

We aim to respond to security reports within 48 hours.

我们目标是在 48 小时内回复安全报告。

## Security Best Practices

## 安全最佳实践

### 1. API Key Management

### 1. API Key 管理

**CRITICAL**: Never commit API keys to version control.

**关键**：切勿将 API keys 提交到版本控制系统。

```bash
# ✅ Good: Store in config file with restricted permissions
chmod 600 ~/.nanobot/config.json

# ❌ Bad: Hardcoding keys in code or committing them
```

**Recommendations:**

**建议：**
- Store API keys in `~/.nanobot/config.json` with file permissions set to `0600`<br>将 API keys 存储在 `~/.nanobot/config.json` 中，并将文件权限设置为 `0600`
- Consider using environment variables for sensitive keys<br>考虑使用环境变量保存敏感 keys
- Use OS keyring/credential manager for production deployments<br>生产部署中使用操作系统 keyring/credential manager
- Rotate API keys regularly<br>定期轮换 API keys
- Use separate API keys for development and production<br>开发和生产环境使用不同的 API keys

### 2. Channel Access Control

### 2. Channel 访问控制

**IMPORTANT**: Always configure `allowFrom` lists for production use.

**重要**：生产使用时务必配置 `allowFrom` 列表。

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["123456789", "987654321"]
    },
    "whatsapp": {
      "enabled": true,
      "allowFrom": ["+1234567890"]
    }
  }
}
```

**Security Notes:**

**安全说明：**
- In `v0.1.4.post3` and earlier, an empty `allowFrom` allowed all users. Since `v0.1.4.post4`, empty `allowFrom` denies all access by default — set `["*"]` to explicitly allow everyone.<br>在 `v0.1.4.post3` 及更早版本中，空的 `allowFrom` 会允许所有用户。从 `v0.1.4.post4` 起，空的 `allowFrom` 默认拒绝所有访问；设置 `["*"]` 可显式允许所有人。
- Get your Telegram user ID from `@userinfobot`<br>从 `@userinfobot` 获取你的 Telegram user ID
- Use full phone numbers with country code for WhatsApp<br>WhatsApp 使用带国家代码的完整电话号码
- Review access logs regularly for unauthorized access attempts<br>定期查看访问日志，检查未授权访问尝试

### 3. Shell Command Execution

### 3. Shell 命令执行

The `exec` tool can execute shell commands. While dangerous command patterns are blocked, you should:

`exec` 工具可以执行 shell 命令。虽然危险命令模式会被阻止，但你仍应：

- ✅ **Enable the bwrap sandbox** (`"tools.exec.sandbox": "bwrap"`) for kernel-level isolation (Linux only)<br>**启用 bwrap sandbox**（`"tools.exec.sandbox": "bwrap"`）以获得内核级隔离（仅 Linux）
- ✅ Review all tool usage in agent logs<br>在 agent 日志中审查所有工具使用情况
- ✅ Understand what commands the agent is running<br>了解 agent 正在运行哪些命令
- ✅ Use a dedicated user account with limited privileges<br>使用权限受限的专用用户账户
- ✅ Never run nanobot as root<br>切勿以 root 身份运行 nanobot
- ❌ Don't disable security checks<br>不要禁用安全检查
- ❌ Don't run on systems with sensitive data without careful review<br>未经仔细审查，不要在包含敏感数据的系统上运行

**Exec sandbox (bwrap):**

**Exec sandbox (bwrap)：**

On Linux, set `"tools.exec.sandbox": "bwrap"` to wrap every shell command in a [bubblewrap](https://github.com/containers/bubblewrap) sandbox. This uses Linux kernel namespaces to restrict what the process can see:

在 Linux 上，设置 `"tools.exec.sandbox": "bwrap"` 可将每个 shell 命令包装在 [bubblewrap](https://github.com/containers/bubblewrap) sandbox 中。这会使用 Linux kernel namespaces 限制进程可见的内容：

- Workspace directory → **read-write** (agent works normally)<br>工作区目录 → **读写**（agent 正常工作）
- Media directory → **read-only** (can read uploaded attachments)<br>媒体目录 → **只读**（可读取上传的附件）
- System directories (`/usr`, `/bin`, `/lib`) → **read-only** (commands still work)<br>系统目录（`/usr`、`/bin`、`/lib`）→ **只读**（命令仍可工作）
- Config files and API keys (`~/.nanobot/config.json`) → **hidden** (masked by tmpfs)<br>配置文件和 API keys（`~/.nanobot/config.json`）→ **隐藏**（由 tmpfs 遮蔽）

Requires `bwrap` installed (`apt install bubblewrap`). Pre-installed in the official Docker image. **Not available on macOS or Windows** — bubblewrap depends on Linux kernel namespaces.

需要安装 `bwrap`（`apt install bubblewrap`）。官方 Docker 镜像中已预装。**macOS 或 Windows 不可用**，因为 bubblewrap 依赖 Linux kernel namespaces。

Enabling the sandbox also automatically activates `restrictToWorkspace` for file tools.

启用 sandbox 也会自动为文件工具激活 `restrictToWorkspace`。

**Blocked patterns:**

**被阻止的模式：**
- `rm -rf /` - Root filesystem deletion<br>`rm -rf /` - 删除根文件系统
- Fork bombs<br>Fork 炸弹
- Filesystem formatting (`mkfs.*`)<br>文件系统格式化（`mkfs.*`）
- Raw disk writes<br>原始磁盘写入
- Other destructive operations<br>其他破坏性操作

### 4. File System Access

### 4. 文件系统访问

File operations have path traversal protection, but:

文件操作具有路径穿越保护，但：

- ✅ Enable `restrictToWorkspace` or the bwrap sandbox to confine file access<br>启用 `restrictToWorkspace` 或 bwrap sandbox 来限制文件访问
- ✅ Run nanobot with a dedicated user account<br>使用专用用户账户运行 nanobot
- ✅ Use filesystem permissions to protect sensitive directories<br>使用文件系统权限保护敏感目录
- ✅ Regularly audit file operations in logs<br>定期在日志中审计文件操作
- ❌ Don't give unrestricted access to sensitive files<br>不要对敏感文件授予不受限制的访问权限

### 5. Network Security

### 5. 网络安全

**API Calls:**

**API 调用：**
- All external API calls use HTTPS by default<br>所有外部 API 调用默认使用 HTTPS
- Timeouts are configured to prevent hanging requests<br>已配置超时以防止请求挂起
- Consider using a firewall to restrict outbound connections if needed<br>如有需要，考虑使用防火墙限制出站连接

**WhatsApp Bridge:**

**WhatsApp Bridge：**
- The bridge binds to `127.0.0.1:3001` (localhost only, not accessible from external network)<br>bridge 绑定到 `127.0.0.1:3001`（仅 localhost，外部网络不可访问）
- Set `bridgeToken` in config to enable shared-secret authentication between Python and Node.js<br>在配置中设置 `bridgeToken`，启用 Python 与 Node.js 之间的共享密钥认证
- Keep authentication data in `~/.nanobot/whatsapp-auth` secure (mode 0700)<br>保护 `~/.nanobot/whatsapp-auth` 中的认证数据（模式 0700）

### 6. Dependency Security

### 6. 依赖安全

**Critical**: Keep dependencies updated!

**关键**：保持依赖更新！

```bash
# Check for vulnerable dependencies
pip install pip-audit
pip-audit

# Update to latest secure versions
pip install --upgrade nanobot-ai
```

For Node.js dependencies (WhatsApp bridge):

对于 Node.js 依赖（WhatsApp bridge）：
```bash
cd bridge
npm audit
npm audit fix
```

**Important Notes:**

**重要说明：**
- Keep `litellm` updated to the latest version for security fixes<br>保持 `litellm` 更新到最新版本以获得安全修复
- We've updated `ws` to `>=8.17.1` to fix DoS vulnerability<br>我们已将 `ws` 更新到 `>=8.17.1` 以修复 DoS 漏洞
- Run `pip-audit` or `npm audit` regularly<br>定期运行 `pip-audit` 或 `npm audit`
- Subscribe to security advisories for nanobot and its dependencies<br>订阅 nanobot 及其依赖的安全公告

### 7. Production Deployment

### 7. 生产部署

For production use:

生产使用时：

1. **Isolate the Environment**<br>**隔离环境**
   ```bash
   # Run in a container or VM
   docker run --rm -it python:3.11
   pip install nanobot-ai
   ```

2. **Use a Dedicated User**<br>**使用专用用户**
   ```bash
   sudo useradd -m -s /bin/bash nanobot
   sudo -u nanobot nanobot gateway
   ```

3. **Set Proper Permissions**<br>**设置合适权限**
   ```bash
   chmod 700 ~/.nanobot
   chmod 600 ~/.nanobot/config.json
   chmod 700 ~/.nanobot/whatsapp-auth
   ```

4. **Enable Logging**<br>**启用日志**
   ```bash
   # Configure log monitoring
   tail -f ~/.nanobot/logs/nanobot.log
   ```

5. **Use Rate Limiting**<br>**使用速率限制**
   - Configure rate limits on your API providers<br>在你的 API providers 上配置速率限制
   - Monitor usage for anomalies<br>监控使用情况以发现异常
   - Set spending limits on LLM APIs<br>为 LLM APIs 设置支出上限

6. **Regular Updates**<br>**定期更新**
   ```bash
   # Check for updates weekly
   pip install --upgrade nanobot-ai
   ```

### 8. Development vs Production

### 8. 开发环境与生产环境

**Development:**

**开发环境：**
- Use separate API keys<br>使用独立的 API keys
- Test with non-sensitive data<br>使用非敏感数据测试
- Enable verbose logging<br>启用详细日志
- Use a test Telegram bot<br>使用测试 Telegram bot

**Production:**

**生产环境：**
- Use dedicated API keys with spending limits<br>使用带支出限制的专用 API keys
- Restrict file system access<br>限制文件系统访问
- Enable audit logging<br>启用审计日志
- Regular security reviews<br>定期安全审查
- Monitor for unusual activity<br>监控异常活动

### 9. Data Privacy

### 9. 数据隐私

- **Logs may contain sensitive information** - secure log files appropriately<br>**日志可能包含敏感信息** - 请妥善保护日志文件
- **LLM providers see your prompts** - review their privacy policies<br>**LLM providers 会看到你的提示词** - 请查看其隐私政策
- **Chat history is stored locally** - protect the `~/.nanobot` directory<br>**聊天历史存储在本地** - 请保护 `~/.nanobot` 目录
- **API keys are in plain text** - use OS keyring for production<br>**API keys 以明文保存** - 生产环境请使用 OS keyring

### 10. Incident Response

### 10. 事件响应

If you suspect a security breach:

如果你怀疑发生安全事件：

1. **Immediately revoke compromised API keys**<br>**立即撤销受影响的 API keys**
2. **Review logs for unauthorized access**<br>**查看日志中是否存在未授权访问**
   ```bash
   grep "Access denied" ~/.nanobot/logs/nanobot.log
   ```
3. **Check for unexpected file modifications**<br>**检查是否存在意外文件修改**
4. **Rotate all credentials**<br>**轮换所有凭据**
5. **Update to latest version**<br>**更新到最新版本**
6. **Report the incident** to maintainers<br>**向维护者报告事件**

## Security Features

## 安全功能

### Built-in Security Controls

### 内置安全控制

✅ **Input Validation**

✅ **输入验证**
- Path traversal protection on file operations<br>文件操作的路径穿越保护
- Dangerous command pattern detection<br>危险命令模式检测
- Input length limits on HTTP requests<br>HTTP 请求输入长度限制

✅ **Authentication**

✅ **认证**
- Allow-list based access control — in `v0.1.4.post3` and earlier empty `allowFrom` allowed all; since `v0.1.4.post4` it denies all (`["*"]` explicitly allows all)<br>基于 allow-list 的访问控制；在 `v0.1.4.post3` 及更早版本中空的 `allowFrom` 允许所有人，从 `v0.1.4.post4` 起则拒绝所有人（`["*"]` 显式允许所有人）
- Failed authentication attempt logging<br>失败认证尝试日志记录

✅ **Resource Protection**

✅ **资源保护**
- Command execution timeouts (60s default)<br>命令执行超时（默认 60 秒）
- Output truncation (10KB limit)<br>输出截断（10KB 限制）
- HTTP request timeouts (10-30s)<br>HTTP 请求超时（10-30 秒）

✅ **Secure Communication**

✅ **安全通信**
- HTTPS for all external API calls<br>所有外部 API 调用使用 HTTPS
- TLS for Telegram API<br>Telegram API 使用 TLS
- WhatsApp bridge: localhost-only binding + optional token auth<br>WhatsApp bridge：仅绑定 localhost，加可选 token 认证

## Known Limitations

## 已知限制

⚠️ **Current Security Limitations:**

⚠️ **当前安全限制：**

1. **No Rate Limiting** - Users can send unlimited messages (add your own if needed)<br>**无速率限制** - 用户可以发送无限量消息（如有需要请自行添加）
2. **Plain Text Config** - API keys stored in plain text (use keyring for production)<br>**明文配置** - API keys 以明文存储（生产环境请使用 keyring）
3. **No Session Management** - No automatic session expiry<br>**无会话管理** - 没有自动会话过期机制
4. **Limited Command Filtering** - Only blocks obvious dangerous patterns (enable the bwrap sandbox for kernel-level isolation on Linux)<br>**命令过滤有限** - 仅阻止明显危险模式（在 Linux 上启用 bwrap sandbox 以获得内核级隔离）
5. **No Audit Trail** - Limited security event logging (enhance as needed)<br>**无审计轨迹** - 安全事件日志有限（可按需增强）

## Security Checklist

## 安全检查清单

Before deploying nanobot:

部署 nanobot 之前：

- [ ] API keys stored securely (not in code)<br>API keys 已安全存储（不在代码中）
- [ ] Config file permissions set to 0600<br>配置文件权限已设置为 0600
- [ ] `allowFrom` lists configured for all channels<br>已为所有 channels 配置 `allowFrom` 列表
- [ ] Running as non-root user<br>以非 root 用户运行
- [ ] Exec sandbox enabled (`"tools.exec.sandbox": "bwrap"`) on Linux deployments<br>Linux 部署中已启用 Exec sandbox（`"tools.exec.sandbox": "bwrap"`）
- [ ] File system permissions properly restricted<br>文件系统权限已正确限制
- [ ] Dependencies updated to latest secure versions<br>依赖已更新到最新安全版本
- [ ] Logs monitored for security events<br>已监控日志中的安全事件
- [ ] Rate limits configured on API providers<br>已在 API providers 上配置速率限制
- [ ] Backup and disaster recovery plan in place<br>已准备备份和灾难恢复计划
- [ ] Security review of custom skills/tools<br>已对自定义 skills/tools 进行安全审查

## Updates

## 更新

**Last Updated**: 2026-04-05

**最后更新**：2026-04-05

For the latest security updates and announcements, check:

如需最新安全更新和公告，请查看：
- GitHub Security Advisories: https://github.com/HKUDS/nanobot/security/advisories<br>GitHub Security Advisories：https://github.com/HKUDS/nanobot/security/advisories
- Release Notes: https://github.com/HKUDS/nanobot/releases<br>Release Notes：https://github.com/HKUDS/nanobot/releases

## License

## 许可证

See LICENSE file for details.

详情请见 LICENSE 文件。
