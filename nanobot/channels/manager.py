"""Channel manager for coordinating chat channels.
用于协调聊天频道的频道管理器。
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import Config
from nanobot.utils.restart import consume_restart_notice_from_env, format_restart_completed_message

if TYPE_CHECKING:
    from nanobot.session.manager import SessionManager


def _default_webui_dist() -> Path | None:
    """Return the absolute path to the bundled webui dist directory if it exists.
    返回捆绑的 webui dist 目录的绝对路径（如果存在）。"""
    try:
        import nanobot.web as web_pkg  # type: ignore[import-not-found]
    except ImportError:
        return None
    candidate = Path(web_pkg.__file__).resolve().parent / "dist"
    return candidate if candidate.is_dir() else None

# Retry delays for message sending (exponential backoff: 1s, 2s, 4s)
# 消息发送重试延迟（指数退避：1秒、2秒、4秒）
_SEND_RETRY_DELAYS = (1, 2, 4)


class ChannelManager:
    """
    Manages chat channels and coordinates message routing.
    管理聊天频道并协调消息路由。

    Responsibilities:
    - Initialize enabled channels (Telegram, WhatsApp, etc.)
      初始化已启用的频道（Telegram、WhatsApp 等）
    - Start/stop channels
      启动/停止频道
    - Route outbound messages
      路由出站消息
    """

    def __init__(
        self,
        config: Config,
        bus: MessageBus,
        *,
        session_manager: "SessionManager | None" = None,
    ):
        self.config = config
        self.bus = bus
        self._session_manager = session_manager
        self.channels: dict[str, BaseChannel] = {}
        self._dispatch_task: asyncio.Task | None = None

        self._init_channels()

    def _init_channels(self) -> None:
        """Initialize channels discovered via pkgutil scan + entry_points plugins.
        初始化通过 pkgutil 扫描和 entry_points 插件发现的频道。"""
        from nanobot.channels.registry import discover_all

        transcription_provider = self.config.channels.transcription_provider
        transcription_key = self._resolve_transcription_key(transcription_provider)
        transcription_base = self._resolve_transcription_base(transcription_provider)
        transcription_language = self.config.channels.transcription_language

        for name, cls in discover_all().items():
            section = getattr(self.config.channels, name, None)
            if section is None:
                continue
            enabled = (
                section.get("enabled", False)
                if isinstance(section, dict)
                else getattr(section, "enabled", False)
            )
            if not enabled:
                continue
            try:
                kwargs: dict[str, Any] = {}
                # Only the WebSocket channel currently hosts the embedded webui
                # surface; other channels stay oblivious to these knobs.
                # 目前只有 WebSocket 频道承载嵌入式 webui；
                # 其他频道对这些旋钮一无所知。
                if cls.name == "websocket" and self._session_manager is not None:
                    kwargs["session_manager"] = self._session_manager
                    static_path = _default_webui_dist()
                    if static_path is not None:
                        kwargs["static_dist_path"] = static_path
                channel = cls(section, self.bus, **kwargs)
                channel.transcription_provider = transcription_provider
                channel.transcription_api_key = transcription_key
                channel.transcription_api_base = transcription_base
                channel.transcription_language = transcription_language
                self.channels[name] = channel
                logger.info("{} channel enabled", cls.display_name)
            except Exception as e:
                logger.warning("{} channel not available: {}", name, e)

        self._validate_allow_from()

    def _resolve_transcription_key(self, provider: str) -> str:
        """Pick the API key for the configured transcription provider.
        为配置的转录提供商选择 API 密钥。"""
        try:
            if provider == "openai":
                return self.config.providers.openai.api_key
            return self.config.providers.groq.api_key
        except AttributeError:
            return ""

    def _resolve_transcription_base(self, provider: str) -> str:
        """Pick the API base URL for the configured transcription provider.
        为配置的转录提供商选择 API 基础 URL。"""
        try:
            if provider == "openai":
                return self.config.providers.openai.api_base or ""
            return self.config.providers.groq.api_base or ""
        except AttributeError:
            return ""

    def _validate_allow_from(self) -> None:
        for name, ch in self.channels.items():
            cfg = ch.config
            if isinstance(cfg, dict):
                if "allow_from" in cfg:
                    allow = cfg.get("allow_from")
                else:
                    allow = cfg.get("allowFrom")
            else:
                allow = getattr(cfg, "allow_from", None)
            if allow == []:
                raise SystemExit(
                    f'Error: "{name}" has empty allowFrom (denies all). '
                    f'Set ["*"] to allow everyone, or add specific user IDs.'
                )

    async def _start_channel(self, name: str, channel: BaseChannel) -> None:
        """Start a channel and log any exceptions.
        启动频道并记录任何异常。"""
        try:
            await channel.start()
        except Exception as e:
            logger.error("Failed to start channel {}: {}", name, e)

    async def start_all(self) -> None:
        """Start all channels and the outbound dispatcher.
        启动所有频道和出站调度器。"""
        if not self.channels:
            logger.warning("No channels enabled")
            return

        # Start outbound dispatcher
        # 启动出站调度器
        self._dispatch_task = asyncio.create_task(self._dispatch_outbound())

        # Start channels
        # 启动频道
        tasks = []
        for name, channel in self.channels.items():
            logger.info("Starting {} channel...", name)
            tasks.append(asyncio.create_task(self._start_channel(name, channel)))

        self._notify_restart_done_if_needed()

        # Wait for all to complete (they should run forever)
        # 等待所有完成（它们应该永远运行）
        await asyncio.gather(*tasks, return_exceptions=True)

    def _notify_restart_done_if_needed(self) -> None:
        """Send restart completion message when runtime env markers are present.
        当存在运行时环境标记时发送重启完成消息。"""
        notice = consume_restart_notice_from_env()
        if not notice:
            return
        target = self.channels.get(notice.channel)
        if not target:
            return
        asyncio.create_task(self._send_with_retry(
            target,
            OutboundMessage(
                channel=notice.channel,
                chat_id=notice.chat_id,
                content=format_restart_completed_message(notice.started_at_raw),
            ),
        ))

    async def stop_all(self) -> None:
        """Stop all channels and the dispatcher.
        停止所有频道和调度器。"""
        logger.info("Stopping all channels...")

        # Stop dispatcher
        # 停止调度器
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass

        # Stop all channels
        # 停止所有频道
        for name, channel in self.channels.items():
            try:
                await channel.stop()
                logger.info("Stopped {} channel", name)
            except Exception as e:
                logger.error("Error stopping {}: {}", name, e)

    async def _dispatch_outbound(self) -> None:
        """Dispatch outbound messages to the appropriate channel.
        将出站消息调度到相应的频道。"""
        logger.info("Outbound dispatcher started")

        # Buffer for messages that couldn't be processed during delta coalescing
        # (since asyncio.Queue doesn't support push_front)
        # 在增量合并期间无法处理的消息的缓冲区
        #（因为 asyncio.Queue 不支持 push_front）
        pending: list[OutboundMessage] = []

        while True:
            try:
                # First check pending buffer before waiting on queue
                # 在等待队列之前先检查待处理缓冲区
                if pending:
                    msg = pending.pop(0)
                else:
                    msg = await asyncio.wait_for(
                        self.bus.consume_outbound(),
                        timeout=1.0
                    )

                if msg.metadata.get("_progress"):
                    if msg.metadata.get("_tool_hint") and not self.config.channels.send_tool_hints:
                        # Skip tool hints if not configured to send them
                        # 如果未配置发送工具提示，则跳过
                        continue
                    if not msg.metadata.get("_tool_hint") and not self.config.channels.send_progress:
                        # Skip progress if not configured to send it
                        # 如果未配置发送进度，则跳过
                        continue

                if msg.metadata.get("_retry_wait"):
                    continue

                # Coalesce consecutive _stream_delta messages for the same (channel, chat_id)
                # to reduce API calls and improve streaming latency
                # 合并相同（频道，聊天ID）的连续 _stream_delta 消息
                # 以减少 API 调用并改善流式延迟
                if msg.metadata.get("_stream_delta") and not msg.metadata.get("_stream_end"):
                    msg, extra_pending = self._coalesce_stream_deltas(msg)
                    pending.extend(extra_pending)

                channel = self.channels.get(msg.channel)
                if channel:
                    # Send message with retry policy
                    # 使用重试策略发送消息
                    await self._send_with_retry(channel, msg)
                else:
                    logger.warning("Unknown channel: {}", msg.channel)

            except asyncio.TimeoutError:
                # No message available in queue, continue polling
                # 队列中没有可用消息，继续轮询
                continue
            except asyncio.CancelledError:
                # Dispatcher shutdown requested
                # 请求关闭调度器
                break

    @staticmethod
    async def _send_once(channel: BaseChannel, msg: OutboundMessage) -> None:
        """Send one outbound message without retry policy.
        不使用重试策略发送一条出站消息。"""
        if msg.metadata.get("_stream_delta") or msg.metadata.get("_stream_end"):
            await channel.send_delta(msg.chat_id, msg.content, msg.metadata)
        elif not msg.metadata.get("_streamed"):
            # Regular message send
            # 普通消息发送
            await channel.send(msg)

    def _coalesce_stream_deltas(
        self, first_msg: OutboundMessage
    ) -> tuple[OutboundMessage, list[OutboundMessage]]:
        """Merge consecutive _stream_delta messages for the same (channel, chat_id).
        合并相同（频道，聊天ID）的连续 _stream_delta 消息。

        This reduces the number of API calls when the queue has accumulated multiple
        deltas, which happens when LLM generates faster than the channel can process.
        当 LLM 生成速度快于频道处理速度时（队列中累积了多个增量），这可以减少 API 调用次数。

        Returns:
            tuple of (merged_message, list_of_non_matching_messages)
            返回：（合并消息，不匹配消息列表）
        """
        target_key = (first_msg.channel, first_msg.chat_id)
        combined_content = first_msg.content
        final_metadata = dict(first_msg.metadata or {})
        non_matching: list[OutboundMessage] = []

        # Only merge consecutive deltas. As soon as we hit any other message,
        # stop and hand that boundary back to the dispatcher via `pending`.
        # 仅合并连续增量。一旦遇到其他消息，
        # 停止并通过 `pending` 将该边界交回给调度器。
        while True:
            try:
                next_msg = self.bus.outbound.get_nowait()
            except asyncio.QueueEmpty:
                break

            # Check if this message belongs to the same stream
            # 检查此消息是否属于同一流
            same_target = (next_msg.channel, next_msg.chat_id) == target_key
            is_delta = next_msg.metadata and next_msg.metadata.get("_stream_delta")
            is_end = next_msg.metadata and next_msg.metadata.get("_stream_end")

            if same_target and is_delta and not final_metadata.get("_stream_end"):
                # Accumulate content
                # 累积内容
                combined_content += next_msg.content
                # If we see _stream_end, remember it and stop coalescing this stream
                # 如果看到 _stream_end，记录它并停止合并此流
                if is_end:
                    final_metadata["_stream_end"] = True
                    # Stream ended - stop coalescing this stream
                    # 流已结束 - 停止合并此流
                    break
            else:
                # First non-matching message defines the coalescing boundary.
                # 第一个不匹配的消息定义合并边界。
                non_matching.append(next_msg)
                break

        merged = OutboundMessage(
            channel=first_msg.channel,
            chat_id=first_msg.chat_id,
            content=combined_content,
            metadata=final_metadata,
        )
        return merged, non_matching

    async def _send_with_retry(self, channel: BaseChannel, msg: OutboundMessage) -> None:
        """Send a message with retry on failure using exponential backoff.
        使用指数退避算法在失败时重试发送消息。

        Note: CancelledError is re-raised to allow graceful shutdown.
        注意：重新引发 CancelledError 以允许优雅关闭。
        """
        max_attempts = max(self.config.channels.send_max_retries, 1)

        for attempt in range(max_attempts):
            try:
                await self._send_once(channel, msg)
                return  # Send succeeded
                # 发送成功
            except asyncio.CancelledError:
                raise  # Propagate cancellation for graceful shutdown
                # 传播取消信号以实现优雅关闭
            except Exception as e:
                if attempt == max_attempts - 1:
                    logger.error(
                        "Failed to send to {} after {} attempts: {} - {}",
                        msg.channel, max_attempts, type(e).__name__, e
                    )
                    return
                delay = _SEND_RETRY_DELAYS[min(attempt, len(_SEND_RETRY_DELAYS) - 1)]
                logger.warning(
                    "Send to {} failed (attempt {}/{}): {}, retrying in {}s",
                    msg.channel, attempt + 1, max_attempts, type(e).__name__, delay
                )
                try:
                    await asyncio.sleep(delay)
                except asyncio.CancelledError:
                    raise  # Propagate cancellation during sleep
                    # 在睡眠期间传播取消信号

    def get_channel(self, name: str) -> BaseChannel | None:
        """Get a channel by name.
        通过名称获取频道。"""
        return self.channels.get(name)

    def get_status(self) -> dict[str, Any]:
        """Get status of all channels.
        获取所有频道的状态。"""
        return {
            name: {
                "enabled": True,
                "running": channel.is_running
            }
            for name, channel in self.channels.items()
        }

    @property
    def enabled_channels(self) -> list[str]:
        """Get list of enabled channel names.
        获取已启用频道名称的列表。"""
        return list(self.channels.keys())
