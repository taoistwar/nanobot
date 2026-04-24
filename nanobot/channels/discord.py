"""Discord channel implementation using discord.py.
使用 discord.py 的 Discord 频道实现。
"""

from __future__ import annotations

import asyncio
import importlib.util
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from loguru import logger
from pydantic import Field

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.command.builtin import build_help_text
from nanobot.config.paths import get_media_dir
from nanobot.config.schema import Base
from nanobot.utils.helpers import safe_filename, split_message

DISCORD_AVAILABLE = importlib.util.find_spec("discord") is not None
if TYPE_CHECKING:
    import aiohttp
    import discord
    from discord import app_commands
    from discord.abc import Messageable

if DISCORD_AVAILABLE:
    import discord
    from discord import app_commands
    from discord.abc import Messageable

MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024  # 20MB
MAX_MESSAGE_LEN = 2000  # Discord 消息字符限制
TYPING_INTERVAL_S = 8


@dataclass
class _StreamBuf:
    """Per-chat streaming accumulator for progressive Discord message edits.
    每个聊天的流式累积器，用于渐进式 Discord 消息编辑。"""

    text: str = ""
    message: Any | None = None
    last_edit: float = 0.0
    stream_id: str | None = None


class DiscordConfig(Base):
    """Discord channel configuration.
    Discord 频道配置。"""

    enabled: bool = False
    token: str = ""
    allow_from: list[str] = Field(default_factory=list)
    allow_channels: list[str] = Field(default_factory=list)  # Allowed channel IDs (empty = all)
    # 允许的频道 ID（空 = 全部）
    intents: int = 37377
    group_policy: Literal["mention", "open"] = "mention"
    read_receipt_emoji: str = "👀"
    working_emoji: str = "🔧"
    working_emoji_delay: float = 2.0
    streaming: bool = True
    proxy: str | None = None
    proxy_username: str | None = None
    proxy_password: str | None = None


if DISCORD_AVAILABLE:

    class DiscordBotClient(discord.Client):
        """discord.py client that forwards events to the channel.
        将事件转发到频道的 discord.py 客户端。"""

        def __init__(
            self,
            channel: DiscordChannel,
            *,
            intents: discord.Intents,
            proxy: str | None = None,
            proxy_auth: aiohttp.BasicAuth | None = None,
        ) -> None:
            super().__init__(intents=intents, proxy=proxy, proxy_auth=proxy_auth)
            self._channel = channel
            self.tree = app_commands.CommandTree(self)
            self._register_app_commands()

        async def on_ready(self) -> None:
            """Called when the bot is ready.
            当机器人就绪时调用。"""
            self._channel._bot_user_id = str(self.user.id) if self.user else None
            logger.info("Discord bot connected as user {}", self._channel._bot_user_id)
            try:
                synced = await self.tree.sync()
                logger.info("Discord app commands synced: {}", len(synced))
            except Exception as e:
                logger.warning("Discord app command sync failed: {}", e)

        async def on_message(self, message: discord.Message) -> None:
            """Handle incoming message events.
            处理传入的消息事件。"""
            await self._channel._handle_discord_message(message)

        async def _reply_ephemeral(self, interaction: discord.Interaction, text: str) -> bool:
            """Send an ephemeral interaction response and report success.
            发送临时交互响应并报告成功。"""
            try:
                await interaction.response.send_message(text, ephemeral=True)
                return True
            except Exception as e:
                logger.warning("Discord interaction response failed: {}", e)
                return False

        async def _forward_slash_command(
            self,
            interaction: discord.Interaction,
            command_text: str,
        ) -> None:
            """Forward slash command to channel handler.
            将斜杠命令转发到频道处理器。"""
            sender_id = str(interaction.user.id)
            channel_id = interaction.channel_id

            if channel_id is None:
                logger.warning("Discord slash command missing channel_id: {}", command_text)
                return

            if not self._channel.is_allowed(sender_id):
                await self._reply_ephemeral(interaction, "You are not allowed to use this bot.")
                return

            await self._reply_ephemeral(interaction, f"Processing {command_text}...")

            await self._channel._handle_message(
                sender_id=sender_id,
                chat_id=str(channel_id),
                content=command_text,
                metadata={
                    "interaction_id": str(interaction.id),
                    "guild_id": str(interaction.guild_id) if interaction.guild_id else None,
                    "is_slash_command": True,
                },
            )

        def _register_app_commands(self) -> None:
            """Register Discord app commands (slash commands).
            注册 Discord 应用命令（斜杠命令）。"""
            commands = (
                ("new", "Stop current task and start a new conversation", "/new"),
                ("stop", "Stop the current task", "/stop"),
                ("restart", "Restart the bot", "/restart"),
                ("status", "Show bot status", "/status"),
            )

            for name, description, command_text in commands:

                @self.tree.command(name=name, description=description)
                async def command_handler(
                    interaction: discord.Interaction,
                    _command_text: str = command_text,
                ) -> None:
                    await self._forward_slash_command(interaction, _command_text)

            @self.tree.command(name="help", description="Show available commands")
            async def help_command(interaction: discord.Interaction) -> None:
                sender_id = str(interaction.user.id)
                if not self._channel.is_allowed(sender_id):
                    await self._reply_ephemeral(interaction, "You are not allowed to use this bot.")
                    return
                await self._reply_ephemeral(interaction, build_help_text())

            @self.tree.error
            async def on_app_command_error(
                interaction: discord.Interaction,
                error: app_commands.AppCommandError,
            ) -> None:
                command_name = interaction.command.qualified_name if interaction.command else "?"
                logger.warning(
                    "Discord app command failed user={} channel={} cmd={} error={}",
                    interaction.user.id,
                    interaction.channel_id,
                    command_name,
                    error,
                )

        async def send_outbound(self, msg: OutboundMessage) -> None:
            """Send a nanobot outbound message using Discord transport rules.
            使用 Discord 传输规则发送 nanobot 出站消息。"""
            channel_id = int(msg.chat_id)

            channel = self.get_channel(channel_id)
            if channel is None:
                try:
                    channel = await self.fetch_channel(channel_id)
                except Exception as e:
                    logger.warning("Discord channel {} unavailable: {}", msg.chat_id, e)
                    return

            reference, mention_settings = self._build_reply_context(channel, msg.reply_to)
            sent_media = False
            failed_media: list[str] = []

            for index, media_path in enumerate(msg.media or []):
                if await self._send_file(
                    channel,
                    media_path,
                    reference=reference if index == 0 else None,
                    mention_settings=mention_settings,
                ):
                    sent_media = True
                else:
                    failed_media.append(Path(media_path).name)

            for index, chunk in enumerate(
                self._build_chunks(msg.content or "", failed_media, sent_media)
            ):
                kwargs: dict[str, Any] = {"content": chunk}
                if index == 0 and reference is not None and not sent_media:
                    kwargs["reference"] = reference
                    kwargs["allowed_mentions"] = mention_settings
                await channel.send(**kwargs)

        async def _send_file(
            self,
            channel: Messageable,
            file_path: str,
            *,
            reference: discord.PartialMessage | None,
            mention_settings: discord.AllowedMentions,
        ) -> bool:
            """Send a file attachment via discord.py.
            通过 discord.py 发送文件附件。"""
            path = Path(file_path)
            if not path.is_file():
                logger.warning("Discord file not found, skipping: {}", file_path)
                return False

            if path.stat().st_size > MAX_ATTACHMENT_BYTES:
                logger.warning("Discord file too large (>20MB), skipping: {}", path.name)
                return False

            try:
                kwargs: dict[str, Any] = {"file": discord.File(path)}
                if reference is not None:
                    kwargs["reference"] = reference
                    kwargs["allowed_mentions"] = mention_settings
                await channel.send(**kwargs)
                logger.info("Discord file sent: {}", path.name)
                return True
            except Exception as e:
                logger.error("Error sending Discord file {}: {}", path.name, e)
                return False

        @staticmethod
        def _build_chunks(content: str, failed_media: list[str], sent_media: bool) -> list[str]:
            """Build outbound text chunks, including attachment-failure fallback text.
            构建出站文本块，包括附件失败回退文本。"""
            chunks = split_message(content, MAX_MESSAGE_LEN)
            if chunks or not failed_media or sent_media:
                return chunks
            fallback = "\n".join(f"[attachment: {name} - send failed]" for name in failed_media)
            return split_message(fallback, MAX_MESSAGE_LEN)

        @staticmethod
        def _build_reply_context(
            channel: Messageable,
            reply_to: str | None,
        ) -> tuple[discord.PartialMessage | None, discord.AllowedMentions]:
            """Build reply context for outbound messages.
            为出站消息构建回复上下文。"""
            mention_settings = discord.AllowedMentions(replied_user=False)
            if not reply_to:
                return None, mention_settings
            try:
                message_id = int(reply_to)
            except ValueError:
                logger.warning("Invalid Discord reply target: {}", reply_to)
                return None, mention_settings

            return channel.get_partial_message(message_id), mention_settings


class DiscordChannel(BaseChannel):
    """Discord channel using discord.py.
    使用 discord.py 的 Discord 频道。"""

    name = "discord"
    display_name = "Discord"
    _STREAM_EDIT_INTERVAL = 0.8

    @classmethod
    def default_config(cls) -> dict[str, Any]:
        return DiscordConfig().model_dump(by_alias=True)

    @staticmethod
    def _channel_key(channel_or_id: Any) -> str:
        """Normalize channel-like objects and ids to a stable string key.
        将类频道对象和 ID 规范化为稳定的字符串键。"""
        channel_id = getattr(channel_or_id, "id", channel_or_id)
        return str(channel_id)

    def __init__(self, config: Any, bus: MessageBus):
        if isinstance(config, dict):
            config = DiscordConfig.model_validate(config)
        super().__init__(config, bus)
        self.config: DiscordConfig = config
        self._client: DiscordBotClient | None = None
        self._typing_tasks: dict[str, asyncio.Task[None]] = {}
        self._bot_user_id: str | None = None
        self._pending_reactions: dict[str, Any] = {}  # chat_id -> message object
        # chat_id -> 消息对象
        self._working_emoji_tasks: dict[str, asyncio.Task[None]] = {}
        self._stream_bufs: dict[str, _StreamBuf] = {}

    async def start(self) -> None:
        """Start the Discord client.
        启动 Discord 客户端。"""
        if not DISCORD_AVAILABLE:
            logger.error("discord.py not installed. Run: pip install nanobot-ai[discord]")
            return

        if not self.config.token:
            logger.error("Discord bot token not configured")
            return

        try:
            intents = discord.Intents.none()
            intents.value = self.config.intents

            proxy_auth = None
            has_user = bool(self.config.proxy_username)
            has_pass = bool(self.config.proxy_password)
            if has_user and has_pass:
                import aiohttp

                proxy_auth = aiohttp.BasicAuth(
                    login=self.config.proxy_username,
                    password=self.config.proxy_password,
                )
            elif has_user != has_pass:
                logger.warning(
                    "Discord proxy auth incomplete: both proxy_username and "
                    "proxy_password must be set; ignoring partial credentials",
                )

            self._client = DiscordBotClient(
                self,
                intents=intents,
                proxy=self.config.proxy,
                proxy_auth=proxy_auth,
            )
        except Exception as e:
            logger.error("Failed to initialize Discord client: {}", e)
            self._client = None
            self._running = False
            return

        self._running = True
        logger.info("Starting Discord client via discord.py...")

        try:
            await self._client.start(self.config.token)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("Discord client startup failed: {}", e)
        finally:
            self._running = False
            await self._reset_runtime_state(close_client=True)

    async def stop(self) -> None:
        """Stop the Discord channel.
        停止 Discord 频道。"""
        self._running = False
        await self._reset_runtime_state(close_client=True)

    async def send(self, msg: OutboundMessage) -> None:
        """Send a message through Discord using discord.py.
        通过 discord.py 发送消息到 Discord。"""
        client = self._client
        if client is None or not client.is_ready():
            logger.warning("Discord client not ready; dropping outbound message")
            return

        is_progress = bool((msg.metadata or {}).get("_progress"))

        try:
            await client.send_outbound(msg)
        except Exception as e:
            logger.error("Error sending Discord message: {}", e)
            raise
        finally:
            if not is_progress:
                await self._stop_typing(msg.chat_id)
                await self._clear_reactions(msg.chat_id)

    async def send_delta(
        self, chat_id: str, delta: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Progressive Discord delivery: send once, then edit until the stream ends.
        渐进式 Discord 投递：发送一次，然后编辑直到流结束。"""
        client = self._client
        if client is None or not client.is_ready():
            logger.warning("Discord client not ready; dropping stream delta")
            return

        meta = metadata or {}
        stream_id = meta.get("_stream_id")

        if meta.get("_stream_end"):
            buf = self._stream_bufs.get(chat_id)
            if not buf or buf.message is None or not buf.text:
                return
            if stream_id is not None and buf.stream_id is not None and buf.stream_id != stream_id:
                return
            await self._finalize_stream(chat_id, buf)
            return

        buf = self._stream_bufs.get(chat_id)
        if buf is None or (
            stream_id is not None and buf.stream_id is not None and buf.stream_id != stream_id
        ):
            buf = _StreamBuf(stream_id=stream_id)
            self._stream_bufs[chat_id] = buf
        elif buf.stream_id is None:
            buf.stream_id = stream_id

        buf.text += delta
        if not buf.text.strip():
            return

        target = await self._resolve_channel(chat_id)
        if target is None:
            logger.warning("Discord stream target {} unavailable", chat_id)
            return

        now = time.monotonic()
        if buf.message is None:
            try:
                buf.message = await target.send(content=buf.text)
                buf.last_edit = now
            except Exception as e:
                logger.warning("Discord stream initial send failed: {}", e)
                raise
            return

        if (now - buf.last_edit) < self._STREAM_EDIT_INTERVAL:
            return

        try:
            await buf.message.edit(content=DiscordBotClient._build_chunks(buf.text, [], False)[0])
            buf.last_edit = now
        except Exception as e:
            logger.warning("Discord stream edit failed: {}", e)
            raise

    async def _handle_discord_message(self, message: discord.Message) -> None:
        """Handle incoming Discord messages from discord.py.
        处理来自 discord.py 的传入 Discord 消息。

        Self-loop guard: only drop messages from this bot's own account. Messages
        from other bots are allowed through so multi-agent setups (one bot asking
        another for help, a bot mentioning another by @name, etc.) can work.
        Bot-from-bot loops are still prevented per-instance because each bot
        still ignores its own outbound messages. (#3217)
        自我循环防护：仅丢弃来自此机器人自己账户的消息。
        允许来自其他机器人的消息通过，以便多代理设置（一个机器人向另一个求助，
        一个机器人通过 @名称提及另一个等）可以工作。
        每个实例仍然防止机器人之间的循环，因为每个机器人仍然忽略自己的出站消息。
        """
        if self._bot_user_id is not None and str(message.author.id) == self._bot_user_id:
            return

        sender_id = str(message.author.id)
        channel_id = self._channel_key(message.channel)
        content = message.content or ""

        if not self._should_accept_inbound(message, sender_id, content):
            return

        media_paths, attachment_markers = await self._download_attachments(message.attachments)
        full_content = self._compose_inbound_content(content, attachment_markers)
        metadata = self._build_inbound_metadata(message)

        await self._start_typing(message.channel)

        # Add read receipt reaction immediately, working emoji after delay
        # 立即添加已读回执反应，延迟后添加工作中表情
        try:
            await message.add_reaction(self.config.read_receipt_emoji)
            self._pending_reactions[channel_id] = message
        except Exception as e:
            logger.debug("Failed to add read receipt reaction: {}", e)

        # Delayed working indicator (cosmetic — not tied to subagent lifecycle)
        # 延迟工作中的指示器（装饰性的 — 与子代理生命周期无关）
        async def _delayed_working_emoji() -> None:
            await asyncio.sleep(self.config.working_emoji_delay)
            try:
                await message.add_reaction(self.config.working_emoji)
            except Exception:
                pass

        self._working_emoji_tasks[channel_id] = asyncio.create_task(_delayed_working_emoji())

        try:
            await self._handle_message(
                sender_id=sender_id,
                chat_id=channel_id,
                content=full_content,
                media=media_paths,
                metadata=metadata,
            )
        except Exception:
            await self._clear_reactions(channel_id)
            await self._stop_typing(channel_id)
            raise

    async def _on_message(self, message: discord.Message) -> None:
        """Backward-compatible alias for legacy tests/callers.
        面向旧测试/调用者的向后兼容别名。"""
        await self._handle_discord_message(message)

    async def _resolve_channel(self, chat_id: str) -> Any | None:
        """Resolve a Discord channel from cache first, then network fetch.
        首先从缓存解析 Discord 频道，然后从网络获取。"""
        client = self._client
        if client is None or not client.is_ready():
            return None
        channel_id = int(chat_id)
        channel = client.get_channel(channel_id)
        if channel is not None:
            return channel
        try:
            return await client.fetch_channel(channel_id)
        except Exception as e:
            logger.warning("Discord channel {} unavailable: {}", chat_id, e)
            return None

    async def _finalize_stream(self, chat_id: str, buf: _StreamBuf) -> None:
        """Commit the final streamed content and flush overflow chunks.
        提交最终流式内容并刷新溢出块。"""
        chunks = DiscordBotClient._build_chunks(buf.text, [], False)
        if not chunks:
            self._stream_bufs.pop(chat_id, None)
            return

        try:
            await buf.message.edit(content=chunks[0])
        except Exception as e:
            logger.warning("Discord final stream edit failed: {}", e)
            raise

        target = getattr(buf.message, "channel", None) or await self._resolve_channel(chat_id)
        if target is None:
            logger.warning("Discord stream follow-up target {} unavailable", chat_id)
            self._stream_bufs.pop(chat_id, None)
            return

        for extra_chunk in chunks[1:]:
            await target.send(content=extra_chunk)

        self._stream_bufs.pop(chat_id, None)
        await self._stop_typing(chat_id)
        await self._clear_reactions(chat_id)

    def _should_accept_inbound(
        self,
        message: discord.Message,
        sender_id: str,
        content: str,
    ) -> bool:
        """Check if inbound Discord message should be processed.
        检查是否应该处理入站 Discord 消息。"""
        if not self.is_allowed(sender_id):
            return False
        # Channel-based filtering: only respond in allowed channels
        # 基于频道的过滤：仅在允许的频道中响应
        allow_channels = self.config.allow_channels
        if allow_channels:
            channel_id = self._channel_key(message.channel)
            if channel_id not in allow_channels:
                return False
        if message.guild is not None and not self._should_respond_in_group(message, content):
            return False
        return True

    async def _download_attachments(
        self,
        attachments: list[discord.Attachment],
    ) -> tuple[list[str], list[str]]:
        """Download supported attachments and return paths + display markers.
        下载支持的附件并返回路径和显示标记。"""
        media_paths: list[str] = []
        markers: list[str] = []
        media_dir = get_media_dir("discord")

        for attachment in attachments:
            filename = attachment.filename or "attachment"
            if attachment.size and attachment.size > MAX_ATTACHMENT_BYTES:
                markers.append(f"[attachment: {filename} - too large]")
                continue
            try:
                media_dir.mkdir(parents=True, exist_ok=True)
                safe_name = safe_filename(filename)
                file_path = media_dir / f"{attachment.id}_{safe_name}"
                await attachment.save(file_path)
                media_paths.append(str(file_path))
                markers.append(f"[attachment: {file_path.name}]")
            except Exception as e:
                logger.warning("Failed to download Discord attachment: {}", e)
                markers.append(f"[attachment: {filename} - download failed]")

        return media_paths, markers

    @staticmethod
    def _compose_inbound_content(content: str, attachment_markers: list[str]) -> str:
        """Combine message text with attachment markers.
        将消息文本与附件标记组合。"""
        content_parts = [content] if content else []
        content_parts.extend(attachment_markers)
        return "\n".join(part for part in content_parts if part) or "[empty message]"

    @staticmethod
    def _build_inbound_metadata(message: discord.Message) -> dict[str, str | None]:
        """Build metadata for inbound Discord messages.
        为入站 Discord 消息构建元数据。"""
        reply_to = (
            str(message.reference.message_id)
            if message.reference and message.reference.message_id
            else None
        )
        return {
            "message_id": str(message.id),
            "guild_id": str(message.guild.id) if message.guild else None,
            "reply_to": reply_to,
        }

    def _should_respond_in_group(self, message: discord.Message, content: str) -> bool:
        """Check if the bot should respond in a guild channel based on policy.
        根据策略检查机器人是否应在公会频道中响应。"""
        if self.config.group_policy == "open":
            return True

        if self.config.group_policy == "mention":
            bot_user_id = self._bot_user_id
            if bot_user_id is None:
                logger.debug(
                    "Discord message in {} ignored (bot identity unavailable)", message.channel.id
                )
                return False

            if any(str(user.id) == bot_user_id for user in message.mentions):
                return True
            if f"<@{bot_user_id}>" in content or f"<@!{bot_user_id}>" in content:
                return True

            logger.debug("Discord message in {} ignored (bot not mentioned)", message.channel.id)
            return False

        return True

    async def _start_typing(self, channel: Messageable) -> None:
        """Start periodic typing indicator for a channel.
        为频道启动定期打字指示器。"""
        channel_id = self._channel_key(channel)
        await self._stop_typing(channel_id)

        async def typing_loop() -> None:
            while self._running:
                try:
                    async with channel.typing():
                        await asyncio.sleep(TYPING_INTERVAL_S)
                except asyncio.CancelledError:
                    return
                except Exception as e:
                    logger.debug("Discord typing indicator failed for {}: {}", channel_id, e)
                    return

        self._typing_tasks[channel_id] = asyncio.create_task(typing_loop())

    async def _stop_typing(self, channel_id: str) -> None:
        """Stop typing indicator for a channel.
        停止频道的打字指示器。"""
        task = self._typing_tasks.pop(self._channel_key(channel_id), None)
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def _clear_reactions(self, chat_id: str) -> None:
        """Remove all pending reactions after bot replies.
        机器人在回复后清除所有待处理反应。"""
        # Cancel delayed working emoji if it hasn't fired yet
        # 如果延迟工作中的表情尚未触发，则取消
        task = self._working_emoji_tasks.pop(chat_id, None)
        if task and not task.done():
            task.cancel()

        msg_obj = self._pending_reactions.pop(chat_id, None)
        if msg_obj is None:
            return
        bot_user = self._client.user if self._client else None
        for emoji in (self.config.read_receipt_emoji, self.config.working_emoji):
            try:
                await msg_obj.remove_reaction(emoji, bot_user)
            except Exception:
                pass

    async def _cancel_all_typing(self) -> None:
        """Stop all typing tasks.
        停止所有打字任务。"""
        channel_ids = list(self._typing_tasks)
        for channel_id in channel_ids:
            await self._stop_typing(channel_id)

    async def _reset_runtime_state(self, close_client: bool) -> None:
        """Reset client and typing state.
        重置客户端和打字状态。"""
        await self._cancel_all_typing()
        self._stream_bufs.clear()
        if close_client and self._client is not None and not self._client.is_closed():
            try:
                await self._client.close()
            except Exception as e:
                logger.warning("Discord client close failed: {}", e)
        self._client = None
        self._bot_user_id = None
