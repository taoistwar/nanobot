# Deployment
# 部署

## Docker
## 码头工人

> [!TIP]
> [！提示]
> The `-v ~/.nanobot:/home/nanobot/.nanobot` flag mounts your local config directory into the container, so your config and workspace persist across container restarts.
> `-v ~/.nanobot:/home/nanobot/.nanobot` 标志将本地配置目录安装到容器中，因此您的配置和工作空间在容器重新启动后仍然存在。
> The container runs as user `nanobot` (UID 1000). If you get **Permission denied**, fix ownership on the host first: `sudo chown -R 1000:1000 ~/.nanobot`, or pass `--user $(id -u):$(id -g)` to match your host UID. Podman users can use `--userns=keep-id` instead.
> 容器以用户 `nanobot` (UID 1000) 身份运行。如果您收到 **权限被拒绝**，请首先修复主机上的所有权：`sudo chown -R 1000:1000 ~/.nanobot`，或传递 `--user $(id -u):$(id -g)` 以匹配您的主机 UID。 Podman 用户可以使用 `--userns=keep-id` 代替。

### Docker Compose
### Docker 组合

```bash
docker compose run --rm nanobot-cli onboard   # first-time setup
vim ~/.nanobot/config.json                     # add API keys
docker compose up -d nanobot-gateway           # start gateway
```

```bash
docker compose run --rm nanobot-cli agent -m "Hello!"   # run CLI
docker compose logs -f nanobot-gateway                   # view logs
docker compose down                                      # stop
```

### Docker
### 码头工人

```bash
# Build the image
docker build -t nanobot .

# Initialize config (first time only)
docker run -v ~/.nanobot:/home/nanobot/.nanobot --rm nanobot onboard

# Edit config on host to add API keys
vim ~/.nanobot/config.json

# Run gateway (connects to enabled channels, e.g. Telegram/Discord/Mochat)
docker run -v ~/.nanobot:/home/nanobot/.nanobot -p 18790:18790 nanobot gateway

# Or run a single command
docker run -v ~/.nanobot:/home/nanobot/.nanobot --rm nanobot agent -m "Hello!"
docker run -v ~/.nanobot:/home/nanobot/.nanobot --rm nanobot status
```

## Linux Service
## Linux服务

Run the gateway as a systemd user service so it starts automatically and restarts on failure.
将网关作为 systemd 用户服务运行，以便它自动启动并在失败时重新启动。

**1. Find the nanobot binary path:**
**1.找到纳米机器人二进制路径：**

```bash
which nanobot   # e.g. /home/user/.local/bin/nanobot
```

**2. Create the service file** at `~/.config/systemd/user/nanobot-gateway.service` (replace `ExecStart` path if needed):
**2.在 `~/.config/systemd/user/nanobot-gateway.service` 创建服务文件**（如果需要，替换 `ExecStart` 路径）：

```ini
[Unit]
Description=Nanobot Gateway
After=network.target

[Service]
Type=simple
ExecStart=%h/.local/bin/nanobot gateway
Restart=always
RestartSec=10
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=%h

[Install]
WantedBy=default.target
```

**3. Enable and start:**
**3.启用并启动：**

```bash
systemctl --user daemon-reload
systemctl --user enable --now nanobot-gateway
```

**Common operations:**
**常用操作：**

```bash
systemctl --user status nanobot-gateway        # check status
systemctl --user restart nanobot-gateway       # restart after config changes
journalctl --user -u nanobot-gateway -f        # follow logs
```

If you edit the `.service` file itself, run `systemctl --user daemon-reload` before restarting.
如果您编辑 `.service` 文件本身，请在重新启动之前运行 `systemctl --user daemon-reload`。

> **Note:** User services only run while you are logged in. To keep the gateway running after logout, enable lingering:
> **注意：** 用户服务仅在您登录时运行。要在注销后保持网关运行，请启用延迟：
>
> ```bash
> loginctl enable-linger $USER
> ```
