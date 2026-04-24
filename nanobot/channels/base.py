"""Base channel interface for chat platforms.
聊天平台的基类接口定义。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from loguru import logger

from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus


class BaseChannel(ABC):
    """
    Abstract base class for chat channel implementations.
    聊天频道实现的抽象基类。

    Each channel (Telegram, Discord, etc.) should implement this interface
    to integrate with the nanobot message bus.
    每个频道（Telegram、Discord 等）都应实现此接口以接入 nanobot 消息总线。
    """

    name: str = "base"
    display_name: str = "Base"
    transcription_provider: str = "groq"
    transcription_api_key: str = ""
    transcription_api_base: str = ""
    transcription_language: str | None = None

    def __init__(self, config: Any, bus: MessageBus):
        """
        Initialize the channel.
        初始化频道。

        Args:
            config: Channel-specific configuration. 频道特定配置。
            bus: The message bus for communication. 用于通信的消息总线。
        """
        self.config = config
        self.bus = bus
        self._running = False

    async def transcribe_audio(self, file_path: str | Path) -> str:
        """Transcribe an audio file via Whisper (OpenAI or Groq). Returns empty string on failure.
        通过 Whisper（OpenAI 或 Groq）转录音频文件。失败时返回空字符串。"""
        if not self.transcription_api_key:
            return ""
        try:
            if self.transcription_provider == "openai":
                from nanobot.providers.transcription import OpenAITranscriptionProvider
                provider = OpenAITranscriptionProvider(
                    api_key=self.transcription_api_key,
                    api_base=self.transcription_api_base or None,
                    language=self.transcription_language or None,
                )
            else:
                from nanobot.providers.transcription import GroqTranscriptionProvider
                provider = GroqTranscriptionProvider(
                    api_key=self.transcription_api_key,
                    api_base=self.transcription_api_base or None,
                    language=self.transcription_language or None,
                )
            return await provider.transcribe(file_path)
        except Exception as e:
            logger.warning("{}: audio transcription failed: {}", self.name, e)
            return ""

    async def login(self, force: bool = False) -> bool:
        """
        Perform channel-specific interactive login (e.g. QR code scan).
        执行特定频道的交互式登录（例如二维码扫描）。

        Args:
            force: If True, ignore existing credentials and force re-authentication.
                如果为 True，则忽略现有凭据并强制重新认证。

        Returns True if already authenticated or login succeeds.
        如果已认证或登录成功则返回 True。
        Override in subclasses that support interactive login.
        在支持交互式登录的子类中重写。
        """
        return True

    @abstractmethod
    async def start(self) -> None:
        """
        Start the channel and begin listening for messages.
        启动频道并开始监听消息。

        This should be a long-running async task that:
        1. Connects to the chat platform
           连接到聊天平台
        2. Listens for incoming messages
           监听传入消息
        3. Forwards messages to the bus via _handle_message()
           通过 _handle_message() 将消息转发到总线
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the channel and clean up resources.
        停止频道并清理资源。"""
        pass

    @abstractmethod
    async def send(self, msg: OutboundMessage) -> None:
        """
        Send a message through this channel.
        通过此频道发送消息。

        Args:
            msg: The message to send. 要发送的消息。

        Implementations should raise on delivery failure so the channel manager
        can apply any retry policy in one place.
        实现应在投递失败时抛出异常，以便频道管理器统一应用重试策略。
        """
        pass

    async def send_delta(self, chat_id: str, delta: str, metadata: dict[str, Any] | None = None) -> None:
        """Deliver a streaming text chunk.
        投递流式文本块。

        Override in subclasses to enable streaming. Implementations should
        raise on delivery failure so the channel manager can retry.
        在子类中重写以启用流式传输。实现应在投递失败时抛出异常，以便频道管理器重试。

        Streaming contract: ``_stream_delta`` is a chunk, ``_stream_end`` ends
        the current segment, and stateful implementations must key buffers by
        ``_stream_id`` rather than only by ``chat_id``.
        流式协议：``_stream_delta`` 是一个数据块，``_stream_end`` 结束当前段落，
        有状态的实现必须使用 ``_stream_id`` 而不是仅使用 ``chat_id`` 来键控缓冲区。
        """
        pass

    @property
    def supports_streaming(self) -> bool:
        """True when config enables streaming AND this subclass implements send_delta.
        当配置启用流式传输且子类实现了 send_delta 时返回 True。"""
        cfg = self.config
        streaming = cfg.get("streaming", False) if isinstance(cfg, dict) else getattr(cfg, "streaming", False)
        return bool(streaming) and type(self).send_delta is not BaseChannel.send_delta

    def is_allowed(self, sender_id: str) -> bool:
        """Check if *sender_id* is permitted.  Empty list → deny all; ``"*"`` → allow all.
        检查 *sender_id* 是否被允许。空列表 → 拒绝所有；``"*"`` → 允许所有。"""
        if isinstance(self.config, dict):
            if "allow_from" in self.config:
                allow_list = self.config.get("allow_from")
            else:
                allow_list = self.config.get("allowFrom", [])
        else:
            allow_list = getattr(self.config, "allow_from", [])
        if not allow_list:
            logger.warning("{}: allow_from is empty — all access denied", self.name)
            return False
        if "*" in allow_list:
            return True
        return str(sender_id) in allow_list

    async def _handle_message(
        self,
        sender_id: str,
        chat_id: str,
        content: str,
        media: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        session_key: str | None = None,
    ) -> None:
        """
        Handle an incoming message from the chat platform.
        处理来自聊天平台的传入消息。

        This method checks permissions and forwards to the bus.
        此方法检查权限并将消息转发到总线。

        Args:
            sender_id: The sender's identifier. 发送者的标识符。
            chat_id: The chat/channel identifier. 聊天/频道标识符。
            content: Message text content. 消息文本内容。
            media: Optional list of media URLs. 可选的媒体 URL 列表。
            metadata: Optional channel-specific metadata. 可选的频道特定元数据。
            session_key: Optional session key override (e.g. thread-scoped sessions).
                可选的会话密钥覆盖（例如线程作用域的会话）。
        """
        if not self.is_allowed(sender_id):
            logger.warning(
                "Access denied for sender {} on channel {}. "
                "Add them to allowFrom list in config to grant access.",
                sender_id, self.name,
            )
            return

        meta = metadata or {}
        if self.supports_streaming:
            meta = {**meta, "_wants_stream": True}

        msg = InboundMessage(
            channel=self.name,
            sender_id=str(sender_id),
            chat_id=str(chat_id),
            content=content,
            media=media or [],
            metadata=meta,
            session_key_override=session_key,
        )

        await self.bus.publish_inbound(msg)

    @classmethod
    def default_config(cls) -> dict[str, Any]:
        """Return default config for onboard. Override in plugins to auto-populate config.json.
        返回用于初始化的默认配置。在插件中重写以自动填充 config.json。"""
        return {"enabled": False}

    @property
    def is_running(self) -> bool:
        """Check if the channel is running.
        检查频道是否正在运行。"""
        return self._running
