"""WhatsApp channel implementation using Node.js bridge.
使用 Node.js 桥接的 WhatsApp 频道实现。
"""

import asyncio
import json
import mimetypes
import os
import secrets
import shutil
import subprocess
from collections import OrderedDict
from pathlib import Path
from typing import Any, Literal

from loguru import logger
from pydantic import Field

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import Base


class WhatsAppConfig(Base):
    """WhatsApp channel configuration.
    WhatsApp 频道配置。"""

    enabled: bool = False
    bridge_url: str = "ws://localhost:3001"
    bridge_token: str = ""
    allow_from: list[str] = Field(default_factory=list)
    group_policy: Literal["open", "mention"] = "open"  # "open" responds to all, "mention" only when @mentioned
    # "open" 响应所有人，"mention" 仅在 @mentioned 时响应


def _bridge_token_path() -> Path:
    """Get the path to store the bridge token.
    获取存储桥接令牌的路么。"""
    from nanobot.config.paths import get_runtime_subdir

    return get_runtime_subdir("whatsapp-auth") / "bridge-token"


def _load_or_create_bridge_token(path: Path) -> str:
    """Load a persisted bridge token or create one on first use.
    加载持久化的桥接令牌或在首次使用时创建一个。"""
    if path.exists():
        token = path.read_text(encoding="utf-8").strip()
        if token:
            return token

    path.parent.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(32)
    path.write_text(token, encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return token


class WhatsAppChannel(BaseChannel):
    """
    WhatsApp channel that connects to a Node.js bridge.
    连接到 Node.js 桥接的 WhatsApp 频道。

    The bridge uses @whiskeysockets/baileys to handle the WhatsApp Web protocol.
    桥接使用 @whiskeysockets/baileys 来处理 WhatsApp Web 协议。
    Communication between Python and Node.js is via WebSocket.
    Python 和 Node.js 之间的通信通过 WebSocket 进行。
    """

    name = "whatsapp"
    display_name = "WhatsApp"

    @classmethod
    def default_config(cls) -> dict[str, Any]:
        return WhatsAppConfig().model_dump(by_alias=True)

    def __init__(self, config: Any, bus: MessageBus):
        if isinstance(config, dict):
            config = WhatsAppConfig.model_validate(config)
        super().__init__(config, bus)
        self._ws = None
        self._connected = False
        self._processed_message_ids: OrderedDict[str, None] = OrderedDict()
        self._lid_to_phone: dict[str, str] = {}
        self._bridge_token: str | None = None

    def _effective_bridge_token(self) -> str:
        """Resolve the bridge token, generating a local secret when needed.
        解析桥接令牌，必要时生成本地密钥。"""
        if self._bridge_token is not None:
            return self._bridge_token
        configured = self.config.bridge_token.strip()
        if configured:
            self._bridge_token = configured
        else:
            self._bridge_token = _load_or_create_bridge_token(_bridge_token_path())
        return self._bridge_token

    async def login(self, force: bool = False) -> bool:
        """
        Set up and run the WhatsApp bridge for QR code login.
        设置并运行 WhatsApp 桥接以进行二维码登录。

        This spawns the Node.js bridge process which handles the WhatsApp
        authentication flow. The process blocks until the user scans the QR code
        or interrupts with Ctrl+C.
        这会生成 Node.js 桥接进程，该进程处理 WhatsApp 身份验证流程。
        该进程会阻塞，直到用户扫描二维码或使用 Ctrl+C 中断。
        """
        try:
            bridge_dir = _ensure_bridge_setup()
        except RuntimeError as e:
            logger.error("{}", e)
            return False

        env = {**os.environ}
        env["BRIDGE_TOKEN"] = self._effective_bridge_token()
        env["AUTH_DIR"] = str(_bridge_token_path().parent)

        logger.info("Starting WhatsApp bridge for QR login...")
        try:
            subprocess.run(
                [shutil.which("npm"), "start"], cwd=bridge_dir, check=True, env=env
            )
        except subprocess.CalledProcessError:
            return False

        return True

    async def start(self) -> None:
        """Start the WhatsApp channel by connecting to the bridge.
        通过连接到桥接来启动 WhatsApp 频道。"""
        import websockets

        bridge_url = self.config.bridge_url

        logger.info("Connecting to WhatsApp bridge at {}...", bridge_url)

        self._running = True

        while self._running:
            try:
                async with websockets.connect(bridge_url) as ws:
                    self._ws = ws
                    await ws.send(
                        json.dumps({"type": "auth", "token": self._effective_bridge_token()})
                    )
                    self._connected = True
                    logger.info("Connected to WhatsApp bridge")

                    # Listen for messages
                    # 监听消息
                    async for message in ws:
                        try:
                            await self._handle_bridge_message(message)
                        except Exception as e:
                            logger.error("Error handling bridge message: {}", e)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._connected = False
                self._ws = None
                logger.warning("WhatsApp bridge connection error: {}", e)

                if self._running:
                    logger.info("Reconnecting in 5 seconds...")
                    await asyncio.sleep(5)

    async def stop(self) -> None:
        """Stop the WhatsApp channel.
        停止 WhatsApp 频道。"""
        self._running = False
        self._connected = False

        if self._ws:
            await self._ws.close()
            self._ws = None

    async def send(self, msg: OutboundMessage) -> None:
        """Send a message through WhatsApp.
        通过 WhatsApp 发送消息。"""
        if not self._ws or not self._connected:
            logger.warning("WhatsApp bridge not connected")
            return

        chat_id = msg.chat_id

        if msg.content:
            try:
                payload = {"type": "send", "to": chat_id, "text": msg.content}
                await self._ws.send(json.dumps(payload, ensure_ascii=False))
            except Exception as e:
                logger.error("Error sending WhatsApp message: {}", e)
                raise

        for media_path in msg.media or []:
            try:
                mime, _ = mimetypes.guess_type(media_path)
                payload = {
                    "type": "send_media",
                    "to": chat_id,
                    "filePath": media_path,
                    "mimetype": mime or "application/octet-stream",
                    "fileName": media_path.rsplit("/", 1)[-1],
                }
                await self._ws.send(json.dumps(payload, ensure_ascii=False))
            except Exception as e:
                logger.error("Error sending WhatsApp media {}: {}", media_path, e)
                raise

    async def _handle_bridge_message(self, raw: str) -> None:
        """Handle a message from the bridge.
        处理来自桥接的消息。"""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON from bridge: {}", raw[:100])
            return

        msg_type = data.get("type")

        if msg_type == "message":
            # Incoming message from WhatsApp
            # 来自 WhatsApp 的传入消息
            # Deprecated by whatsapp: old phone number style typically: <phone>@s.whatspp.net
            # 已废弃的 whatsapp：旧电话号码样式通常为：<phone>@s.whatspp.net
            pn = data.get("pn", "")
            # New LID sytle typically:
            # 新的 LID 样式通常为：
            sender = data.get("sender", "")
            content = data.get("content", "")
            message_id = data.get("id", "")

            if message_id:
                if message_id in self._processed_message_ids:
                    return
                self._processed_message_ids[message_id] = None
                while len(self._processed_message_ids) > 1000:
                    self._processed_message_ids.popitem(last=False)

            # Extract just the phone number or lid as chat_id
            # 仅提取电话号码或 lid 作为 chat_id
            is_group = data.get("isGroup", False)
            was_mentioned = data.get("wasMentioned", False)

            if is_group and getattr(self.config, "group_policy", "open") == "mention":
                if not was_mentioned:
                    return

            # Classify by JID suffix: @s.whatsapp.net = phone, @lid.whatsapp.net = LID
            # The bridge's pn/sender fields don't consistently map to phone/LID across versions.
            # 按 JID 后缀分类：@s.whatsapp.net = 电话，@lid.whatsapp.net = LID
            # 桥接的 pn/sender 字段在不同版本中不一致地映射到电话/LID。
            raw_a = pn or ""
            raw_b = sender or ""
            id_a = raw_a.split("@")[0] if "@" in raw_a else raw_a
            id_b = raw_b.split("@")[0] if "@" in raw_b else raw_b

            phone_id = ""
            lid_id = ""
            for raw, extracted in [(raw_a, id_a), (raw_b, id_b)]:
                if "@s.whatsapp.net" in raw:
                    phone_id = extracted
                elif "@lid.whatsapp.net" in raw:
                    lid_id = extracted
                elif extracted and not phone_id:
                    phone_id = extracted  # best guess for bare values
                    # 裸值的最佳猜测

            if phone_id and lid_id:
                self._lid_to_phone[lid_id] = phone_id
            sender_id = phone_id or self._lid_to_phone.get(lid_id, "") or lid_id or id_a or id_b

            logger.info("Sender phone={} lid={} → sender_id={}", phone_id or "(empty)", lid_id or "(empty)", sender_id)

            # Extract media paths (images/documents/videos downloaded by the bridge)
            # 提取媒体路径（由桥接下载的图片/文档/视频）
            media_paths = data.get("media") or []

            # Handle voice transcription if it's a voice message
            # 如果是语音消息，则处理语音转录
            if content == "[Voice Message]":
                if media_paths:
                    logger.info("Transcribing voice message from {}...", sender_id)
                    transcription = await self.transcribe_audio(media_paths[0])
                    if transcription:
                        content = transcription
                        logger.info("Transcribed voice from {}: {}...", sender_id, transcription[:50])
                    else:
                        content = "[Voice Message: Transcription failed]"
                else:
                    content = "[Voice Message: Audio not available]"

            # Build content tags matching Telegram's pattern: [image: /path] or [file: /path]
            # 构建与 Telegram 模式匹配的内容标签：[image: /path] 或 [file: /path]
            if media_paths:
                for p in media_paths:
                    mime, _ = mimetypes.guess_type(p)
                    media_type = "image" if mime and mime.startswith("image/") else "file"
                    media_tag = f"[{media_type}: {p}]"
                    content = f"{content}\n{media_tag}" if content else media_tag

            await self._handle_message(
                sender_id=sender_id,
                chat_id=sender,  # Use full LID for replies
                # 使用完整 LID 进行回复
                content=content,
                media=media_paths,
                metadata={
                    "message_id": message_id,
                    "timestamp": data.get("timestamp"),
                    "is_group": data.get("isGroup", False),
                },
            )

        elif msg_type == "status":
            # Connection status update
            # 连接状态更新
            status = data.get("status")
            logger.info("WhatsApp status: {}", status)

            if status == "connected":
                self._connected = True
            elif status == "disconnected":
                self._connected = False

        elif msg_type == "qr":
            # QR code for authentication
            # 用于身份验证的二维码
            logger.info("Scan QR code in the bridge terminal to connect WhatsApp")

        elif msg_type == "error":
            logger.error("WhatsApp bridge error: {}", data.get("error"))


def _ensure_bridge_setup() -> Path:
    """
    Ensure the WhatsApp bridge is set up and built.
    确保 WhatsApp 桥接已设置并构建。

    Returns the bridge directory. Raises RuntimeError if npm is not found
    or bridge cannot be built.
    返回桥接目录。如果找不到 npm 或无法构建桥接，则抛出 RuntimeError。
    """
    from nanobot.config.paths import get_bridge_install_dir

    user_bridge = get_bridge_install_dir()

    if (user_bridge / "dist" / "index.js").exists():
        return user_bridge

    npm_path = shutil.which("npm")
    if not npm_path:
        raise RuntimeError("npm not found. Please install Node.js >= 18.")

    # Find source bridge
    # 查找源桥接
    current_file = Path(__file__)
    pkg_bridge = current_file.parent.parent / "bridge"
    src_bridge = current_file.parent.parent.parent / "bridge"

    source = None
    if (pkg_bridge / "package.json").exists():
        source = pkg_bridge
    elif (src_bridge / "package.json").exists():
        source = src_bridge

    if not source:
        raise RuntimeError(
            "WhatsApp bridge source not found. "
            "Try reinstalling: pip install --force-reinstall nanobot"
        )

    logger.info("Setting up WhatsApp bridge...")
    user_bridge.parent.mkdir(parents=True, exist_ok=True)
    if user_bridge.exists():
        shutil.rmtree(user_bridge)
    shutil.copytree(source, user_bridge, ignore=shutil.ignore_patterns("node_modules", "dist"))

    logger.info("  Installing dependencies...")
    subprocess.run([npm_path, "install"], cwd=user_bridge, check=True, capture_output=True)

    logger.info("  Building...")
    subprocess.run([npm_path, "run", "build"], cwd=user_bridge, check=True, capture_output=True)

    logger.info("Bridge ready")
    return user_bridge
