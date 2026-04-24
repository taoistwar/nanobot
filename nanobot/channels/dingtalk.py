"""DingTalk/DingDing channel implementation using Stream Mode.
使用流模式的钉钉/叮叮频道实现。
"""

import asyncio
import json
import mimetypes
import os
import time
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import httpx
from loguru import logger
from pydantic import Field

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import Base

try:
    from dingtalk_stream import (
        AckMessage,
        CallbackHandler,
        CallbackMessage,
        Credential,
        DingTalkStreamClient,
    )
    from dingtalk_stream.chatbot import ChatbotMessage

    DINGTALK_AVAILABLE = True
except ImportError:
    DINGTALK_AVAILABLE = False
    # Fallback so class definitions don't crash at module level
    # 后备方案，使类定义在模块级别不会崩溃
    CallbackHandler = object  # type: ignore[assignment,misc]
    CallbackMessage = None  # type: ignore[assignment,misc]
    AckMessage = None  # type: ignore[assignment,misc]
    ChatbotMessage = None  # type: ignore[assignment,misc]


class NanobotDingTalkHandler(CallbackHandler):
    """
    Standard DingTalk Stream SDK Callback Handler.
    Parses incoming messages and forwards them to the Nanobot channel.
    标准的钉钉流 SDK 回调处理器。
    解析传入消息并将其转发到 Nanobot 频道。
    """

    def __init__(self, channel: "DingTalkChannel"):
        super().__init__()
        self.channel = channel

    async def process(self, message: CallbackMessage):
        """Process incoming stream message.
        处理传入的流消息。"""
        try:
            # Parse using SDK's ChatbotMessage for robust handling
            # 使用 SDK 的 ChatbotMessage 进行解析以获得稳健的处理
            chatbot_msg = ChatbotMessage.from_dict(message.data)

            # Extract text content; fall back to raw dict if SDK object is empty
            # 提取文本内容；如果 SDK 对象为空则回退到原始字典
            content = ""
            if chatbot_msg.text:
                content = chatbot_msg.text.content.strip()
            elif chatbot_msg.extensions.get("content", {}).get("recognition"):
                content = chatbot_msg.extensions["content"]["recognition"].strip()
            if not content:
                content = message.data.get("text", {}).get("content", "").strip()

            # Handle file/image messages
            # 处理文件/图片消息
            file_paths = []
            if chatbot_msg.message_type == "picture" and chatbot_msg.image_content:
                download_code = chatbot_msg.image_content.download_code
                if download_code:
                    sender_uid = chatbot_msg.sender_staff_id or chatbot_msg.sender_id or "unknown"
                    fp = await self.channel._download_dingtalk_file(download_code, "image.jpg", sender_uid)
                    if fp:
                        file_paths.append(fp)
                        content = content or "[Image]"

            elif chatbot_msg.message_type == "file":
                download_code = message.data.get("content", {}).get("downloadCode") or message.data.get("downloadCode")
                fname = message.data.get("content", {}).get("fileName") or message.data.get("fileName") or "file"
                if download_code:
                    sender_uid = chatbot_msg.sender_staff_id or chatbot_msg.sender_id or "unknown"
                    fp = await self.channel._download_dingtalk_file(download_code, fname, sender_uid)
                    if fp:
                        file_paths.append(fp)
                        content = content or "[File]"

            elif chatbot_msg.message_type == "richText" and chatbot_msg.rich_text_content:
                rich_list = chatbot_msg.rich_text_content.rich_text_list or []
                for item in rich_list:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") == "text":
                        t = item.get("text", "").strip()
                        if t:
                            content = (content + " " + t).strip() if content else t
                    elif item.get("downloadCode"):
                        dc = item["downloadCode"]
                        fname = item.get("fileName") or "file"
                        sender_uid = chatbot_msg.sender_staff_id or chatbot_msg.sender_id or "unknown"
                        fp = await self.channel._download_dingtalk_file(dc, fname, sender_uid)
                        if fp:
                            file_paths.append(fp)
                            content = content or "[File]"

            if file_paths:
                file_list = "\n".join("- " + p for p in file_paths)
                content = content + "\n\nReceived files:\n" + file_list

            if not content:
                logger.warning(
                    "Received empty or unsupported message type: {}",
                    chatbot_msg.message_type,
                )
                return AckMessage.STATUS_OK, "OK"

            sender_id = chatbot_msg.sender_staff_id or chatbot_msg.sender_id
            sender_name = chatbot_msg.sender_nick or "Unknown"

            conversation_type = message.data.get("conversationType")
            conversation_id = (
                message.data.get("conversationId")
                or message.data.get("openConversationId")
            )

            logger.info("Received DingTalk message from {} ({}): {}", sender_name, sender_id, content)

            # Forward to Nanobot via _on_message (non-blocking).
            # Store reference to prevent GC before task completes.
            # 通过 _on_message 转发到 Nanobot（非阻塞）。
            # 存储引用以防止任务完成前被 GC 回收。
            task = asyncio.create_task(
                self.channel._on_message(
                    content,
                    sender_id,
                    sender_name,
                    conversation_type,
                    conversation_id,
                )
            )
            self.channel._background_tasks.add(task)
            task.add_done_callback(self.channel._background_tasks.discard)

            return AckMessage.STATUS_OK, "OK"

        except Exception as e:
            logger.error("Error processing DingTalk message: {}", e)
            # Return OK to avoid retry loop from DingTalk server
            # 返回 OK 以避免钉钉服务器重试循环
            return AckMessage.STATUS_OK, "Error"


class DingTalkConfig(Base):
    """DingTalk channel configuration using Stream mode.
    使用流模式的钉钉频道配置。"""

    enabled: bool = False
    client_id: str = ""
    client_secret: str = ""
    allow_from: list[str] = Field(default_factory=list)


class DingTalkChannel(BaseChannel):
    """
    DingTalk channel using Stream Mode.
    使用流模式的钉钉频道。

    Uses WebSocket to receive events via `dingtalk-stream` SDK.
    通过 `dingtalk-stream` SDK 使用 WebSocket 接收事件。
    Uses direct HTTP API to send messages (SDK is mainly for receiving).
    使用直接 HTTP API 发送消息（SDK 主要用于接收）。

    Supports both private (1:1) and group chats.
    支持私聊（1:1）和群聊。
    Group chat_id is stored with a "group:" prefix to route replies back.
    群聊 chat_id 存储时带有 "group:" 前缀，以便路由回复。
    """

    name = "dingtalk"
    display_name = "DingTalk"
    _IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    _AUDIO_EXTS = {".amr", ".mp3", ".wav", ".ogg", ".m4a", ".aac"}
    _VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    _ZIP_BEFORE_UPLOAD_EXTS = {".htm", ".html"}

    @classmethod
    def default_config(cls) -> dict[str, Any]:
        return DingTalkConfig().model_dump(by_alias=True)

    def __init__(self, config: Any, bus: MessageBus):
        if isinstance(config, dict):
            config = DingTalkConfig.model_validate(config)
        super().__init__(config, bus)
        self.config: DingTalkConfig = config
        self._client: Any = None
        self._http: httpx.AsyncClient | None = None

        # Access Token management for sending messages
        # 用于发送消息的访问令牌管理
        self._access_token: str | None = None
        self._token_expiry: float = 0

        # Hold references to background tasks to prevent GC
        # 持有后台任务的引用以防止被 GC 回收
        self._background_tasks: set[asyncio.Task] = set()

    async def start(self) -> None:
        """Start the DingTalk bot with Stream Mode.
        使用流模式启动钉钉机器人。"""
        try:
            if not DINGTALK_AVAILABLE:
                logger.error(
                    "DingTalk Stream SDK not installed. Run: pip install dingtalk-stream"
                )
                return

            if not self.config.client_id or not self.config.client_secret:
                logger.error("DingTalk client_id and client_secret not configured")
                return

            self._running = True
            self._http = httpx.AsyncClient()

            logger.info(
                "Initializing DingTalk Stream Client with Client ID: {}...",
                self.config.client_id,
            )
            credential = Credential(self.config.client_id, self.config.client_secret)
            self._client = DingTalkStreamClient(credential)

            # Register standard handler
            # 注册标准处理器
            handler = NanobotDingTalkHandler(self)
            self._client.register_callback_handler(ChatbotMessage.TOPIC, handler)

            logger.info("DingTalk bot started with Stream Mode")

            # Reconnect loop: restart stream if SDK exits or crashes
            # 重连循环：如果 SDK 退出或崩溃则重启流
            while self._running:
                try:
                    await self._client.start()
                except Exception as e:
                    logger.warning("DingTalk stream error: {}", e)
                if self._running:
                    logger.info("Reconnecting DingTalk stream in 5 seconds...")
                    await asyncio.sleep(5)

        except Exception as e:
            logger.exception("Failed to start DingTalk channel: {}", e)

    async def stop(self) -> None:
        """Stop the DingTalk bot.
        停止钉钉机器人。"""
        self._running = False
        # Close the shared HTTP client
        # 关闭共享的 HTTP 客户端
        if self._http:
            await self._http.aclose()
            self._http = None
        # Cancel outstanding background tasks
        # 取消未完成的后台任务
        for task in self._background_tasks:
            task.cancel()
        self._background_tasks.clear()

    async def _get_access_token(self) -> str | None:
        """Get or refresh Access Token.
        获取或刷新访问令牌。"""
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token

        url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
        data = {
            "appKey": self.config.client_id,
            "appSecret": self.config.client_secret,
        }

        if not self._http:
            logger.warning("DingTalk HTTP client not initialized, cannot refresh token")
            return None

        try:
            resp = await self._http.post(url, json=data)
            resp.raise_for_status()
            res_data = resp.json()
            self._access_token = res_data.get("accessToken")
            # Expire 60s early to be safe
            # 为安全起见，提前 60 秒过期
            self._token_expiry = time.time() + int(res_data.get("expireIn", 7200)) - 60
            return self._access_token
        except Exception as e:
            logger.error("Failed to get DingTalk access token: {}", e)
            return None

    @staticmethod
    def _is_http_url(value: str) -> bool:
        """Check if the value is an HTTP/HTTPS URL.
        检查值是否为 HTTP/HTTPS URL。"""
        return urlparse(value).scheme in ("http", "https")

    def _guess_upload_type(self, media_ref: str) -> str:
        """Guess the upload type based on file extension.
        根据文件扩展名猜测上传类型。"""
        ext = Path(urlparse(media_ref).path).suffix.lower()
        if ext in self._IMAGE_EXTS: return "image"
        if ext in self._AUDIO_EXTS: return "voice"
        if ext in self._VIDEO_EXTS: return "video"
        return "file"

    def _guess_filename(self, media_ref: str, upload_type: str) -> str:
        """Guess the filename from media reference.
        从媒体引用中猜测文件名。"""
        name = os.path.basename(urlparse(media_ref).path)
        return name or {"image": "image.jpg", "voice": "audio.amr", "video": "video.mp4"}.get(upload_type, "file.bin")

    @staticmethod
    def _zip_bytes(filename: str, data: bytes) -> tuple[bytes, str, str]:
        """Zip bytes data with a filename.
        将字节数据压缩为带文件名的 zip。"""
        stem = Path(filename).stem or "attachment"
        safe_name = filename or "attachment.bin"
        zip_name = f"{stem}.zip"
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(safe_name, data)
        return buffer.getvalue(), zip_name, "application/zip"

    def _normalize_upload_payload(
        self,
        filename: str,
        data: bytes,
        content_type: str | None,
    ) -> tuple[bytes, str, str | None]:
        """Normalize upload payload, zipping HTML files if needed.
        规范化上传载荷，必要时压缩 HTML 文件。"""
        ext = Path(filename).suffix.lower()
        if ext in self._ZIP_BEFORE_UPLOAD_EXTS or content_type == "text/html":
            logger.info(
                "DingTalk does not accept raw HTML attachments, zipping {} before upload",
                filename,
            )
            return self._zip_bytes(filename, data)
        return data, filename, content_type

    async def _read_media_bytes(
        self,
        media_ref: str,
    ) -> tuple[bytes | None, str | None, str | None]:
        """Read media bytes from URL or local file.
        从 URL 或本地文件读取媒体字节。"""
        if not media_ref:
            return None, None, None

        if self._is_http_url(media_ref):
            if not self._http:
                return None, None, None
            try:
                resp = await self._http.get(media_ref, follow_redirects=True)
                if resp.status_code >= 400:
                    logger.warning(
                        "DingTalk media download failed status={} ref={}",
                        resp.status_code,
                        media_ref,
                    )
                    return None, None, None
                content_type = (resp.headers.get("content-type") or "").split(";")[0].strip()
                filename = self._guess_filename(media_ref, self._guess_upload_type(media_ref))
                return resp.content, filename, content_type or None
            except httpx.TransportError as e:
                logger.error("DingTalk media download network error ref={} err={}", media_ref, e)
                raise
            except Exception as e:
                logger.error("DingTalk media download error ref={} err={}", media_ref, e)
                return None, None, None

        try:
            if media_ref.startswith("file://"):
                parsed = urlparse(media_ref)
                local_path = Path(unquote(parsed.path))
            else:
                local_path = Path(os.path.expanduser(media_ref))
            if not local_path.is_file():
                logger.warning("DingTalk media file not found: {}", local_path)
                return None, None, None
            data = await asyncio.to_thread(local_path.read_bytes)
            content_type = mimetypes.guess_type(local_path.name)[0]
            return data, local_path.name, content_type
        except Exception as e:
            logger.error("DingTalk media read error ref={} err={}", media_ref, e)
            return None, None, None

    async def _upload_media(
        self,
        token: str,
        data: bytes,
        media_type: str,
        filename: str,
        content_type: str | None,
    ) -> str | None:
        """Upload media to DingTalk and return media_id.
        将媒体上传到钉钉并返回 media_id。"""
        if not self._http:
            return None
        url = f"https://oapi.dingtalk.com/media/upload?access_token={token}&type={media_type}"
        mime = content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        files = {"media": (filename, data, mime)}

        try:
            resp = await self._http.post(url, files=files)
            text = resp.text
            result = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            if resp.status_code >= 400:
                logger.error("DingTalk media upload failed status={} type={} body={}", resp.status_code, media_type, text[:500])
                return None
            errcode = result.get("errcode", 0)
            if errcode != 0:
                logger.error("DingTalk media upload api error type={} errcode={} body={}", media_type, errcode, text[:500])
                return None
            sub = result.get("result") or {}
            media_id = result.get("media_id") or result.get("mediaId") or sub.get("media_id") or sub.get("mediaId")
            if not media_id:
                logger.error("DingTalk media upload missing media_id body={}", text[:500])
                return None
            return str(media_id)
        except httpx.TransportError as e:
            logger.error("DingTalk media upload network error type={} err={}", media_type, e)
            raise
        except Exception as e:
            logger.error("DingTalk media upload error type={} err={}", media_type, e)
            return None

    async def _send_batch_message(
        self,
        token: str,
        chat_id: str,
        msg_key: str,
        msg_param: dict[str, Any],
    ) -> bool:
        """Send batch message via DingTalk API.
        通过钉钉 API 发送批量消息。"""
        if not self._http:
            logger.warning("DingTalk HTTP client not initialized, cannot send")
            return False

        headers = {"x-acs-dingtalk-access-token": token}
        if chat_id.startswith("group:"):
            # Group chat
            # 群聊
            url = "https://api.dingtalk.com/v1.0/robot/groupMessages/send"
            payload = {
                "robotCode": self.config.client_id,
                "openConversationId": chat_id[6:],  # Remove "group:" prefix,
                # 移除 "group:" 前缀
                "msgKey": msg_key,
                "msgParam": json.dumps(msg_param, ensure_ascii=False),
            }
        else:
            # Private chat
            # 私聊
            url = "https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend"
            payload = {
                "robotCode": self.config.client_id,
                "userIds": [chat_id],
                "msgKey": msg_key,
                "msgParam": json.dumps(msg_param, ensure_ascii=False),
            }

        try:
            resp = await self._http.post(url, json=payload, headers=headers)
            body = resp.text
            if resp.status_code != 200:
                logger.error("DingTalk send failed msgKey={} status={} body={}", msg_key, resp.status_code, body[:500])
                return False
            try: result = resp.json()
            except Exception: result = {}
            errcode = result.get("errcode")
            if errcode not in (None, 0):
                logger.error("DingTalk send api error msgKey={} errcode={} body={}", msg_key, errcode, body[:500])
                return False
            logger.debug("DingTalk message sent to {} with msgKey={}", chat_id, msg_key)
            return True
        except httpx.TransportError as e:
            logger.error("DingTalk network error sending message msgKey={} err={}", msg_key, e)
            raise
        except Exception as e:
            logger.error("Error sending DingTalk message msgKey={} err={}", msg_key, e)
            return False

    async def _send_markdown_text(self, token: str, chat_id: str, content: str) -> bool:
        """Send markdown text message.
        发送 markdown 文本消息。"""
        return await self._send_batch_message(
            token,
            chat_id,
            "sampleMarkdown",
            {"text": content, "title": "Nanobot Reply"},
        )

    async def _send_media_ref(self, token: str, chat_id: str, media_ref: str) -> bool:
        """Send media file by reference.
        通过引用发送媒体文件。"""
        media_ref = (media_ref or "").strip()
        if not media_ref:
            return True

        upload_type = self._guess_upload_type(media_ref)
        if upload_type == "image" and self._is_http_url(media_ref):
            ok = await self._send_batch_message(
                token,
                chat_id,
                "sampleImageMsg",
                {"photoURL": media_ref},
            )
            if ok:
                return True
            logger.warning("DingTalk image url send failed, trying upload fallback: {}", media_ref)

        data, filename, content_type = await self._read_media_bytes(media_ref)
        if not data:
            logger.error("DingTalk media read failed: {}", media_ref)
            return False

        filename = filename or self._guess_filename(media_ref, upload_type)
        data, filename, content_type = self._normalize_upload_payload(filename, data, content_type)
        file_type = Path(filename).suffix.lower().lstrip(".")
        if not file_type:
            guessed = mimetypes.guess_extension(content_type or "")
            file_type = (guessed or ".bin").lstrip(".")
        if file_type == "jpeg":
            file_type = "jpg"

        media_id = await self._upload_media(
            token=token,
            data=data,
            media_type=upload_type,
            filename=filename,
            content_type=content_type,
        )
        if not media_id:
            return False

        if upload_type == "image":
            # Verified in production: sampleImageMsg accepts media_id in photoURL.
            # 生产环境验证：sampleImageMsg 接受 media_id 作为 photoURL。
            ok = await self._send_batch_message(
                token,
                chat_id,
                "sampleImageMsg",
                {"photoURL": media_id},
            )
            if ok:
                return True
            logger.warning("DingTalk image media_id send failed, falling back to file: {}", media_ref)

        return await self._send_batch_message(
            token,
            chat_id,
            "sampleFile",
            {"mediaId": media_id, "fileName": filename, "fileType": file_type},
        )

    async def send(self, msg: OutboundMessage) -> None:
        """Send a message through DingTalk.
        通过钉钉发送消息。"""
        token = await self._get_access_token()
        if not token:
            return

        if msg.content and msg.content.strip():
            await self._send_markdown_text(token, msg.chat_id, msg.content.strip())

        for media_ref in msg.media or []:
            ok = await self._send_media_ref(token, msg.chat_id, media_ref)
            if ok:
                continue
            logger.error("DingTalk media send failed for {}", media_ref)
            # Send visible fallback so failures are observable by the user.
            # 发送可见的回退内容，以便用户可以观察到失败。
            filename = self._guess_filename(media_ref, self._guess_upload_type(media_ref))
            await self._send_markdown_text(
                token,
                msg.chat_id,
                f"[Attachment send failed: {filename}]",
            )

    async def _on_message(
        self,
        content: str,
        sender_id: str,
        sender_name: str,
        conversation_type: str | None = None,
        conversation_id: str | None = None,
    ) -> None:
        """Handle incoming message (called by NanobotDingTalkHandler).
        处理传入消息（由 NanobotDingTalkHandler 调用）。

        Delegates to BaseChannel._handle_message() which enforces allow_from
        permission checks before publishing to the bus.
        委托给 BaseChannel._handle_message()，后者在发布到总线之前执行 allow_from 权限检查。
        """
        try:
            logger.info("DingTalk inbound: {} from {}", content, sender_name)
            is_group = conversation_type == "2" and conversation_id
            chat_id = f"group:{conversation_id}" if is_group else sender_id
            await self._handle_message(
                sender_id=sender_id,
                chat_id=chat_id,
                content=str(content),
                metadata={
                    "sender_name": sender_name,
                    "platform": "dingtalk",
                    "conversation_type": conversation_type,
                },
            )
        except Exception as e:
            logger.error("Error publishing DingTalk message: {}", e)

    async def _download_dingtalk_file(
        self,
        download_code: str,
        filename: str,
        sender_id: str,
    ) -> str | None:
        """Download a DingTalk file to the media directory, return local path.
        将钉钉文件下载到媒体目录，返回本地路径。"""
        from nanobot.config.paths import get_media_dir

        try:
            token = await self._get_access_token()
            if not token or not self._http:
                logger.error("DingTalk file download: no token or http client")
                return None

            # Step 1: Exchange downloadCode for a temporary download URL
            # 步骤 1：用 downloadCode 换取临时下载 URL
            api_url = "https://api.dingtalk.com/v1.0/robot/messageFiles/download"
            headers = {"x-acs-dingtalk-access-token": token, "Content-Type": "application/json"}
            payload = {"downloadCode": download_code, "robotCode": self.config.client_id}
            resp = await self._http.post(api_url, json=payload, headers=headers)
            if resp.status_code != 200:
                logger.error("DingTalk get download URL failed: status={}, body={}", resp.status_code, resp.text)
                return None

            result = resp.json()
            download_url = result.get("downloadUrl")
            if not download_url:
                logger.error("DingTalk download URL not found in response: {}", result)
                return None

            # Step 2: Download the file content
            # 步骤 2：下载文件内容
            file_resp = await self._http.get(download_url, follow_redirects=True)
            if file_resp.status_code != 200:
                logger.error("DingTalk file download failed: status={}", file_resp.status_code)
                return None

            # Save to media directory (accessible under workspace)
            # 保存到媒体目录（在 workspace 下可访问）
            download_dir = get_media_dir("dingtalk") / sender_id
            download_dir.mkdir(parents=True, exist_ok=True)
            file_path = download_dir / filename
            await asyncio.to_thread(file_path.write_bytes, file_resp.content)
            logger.info("DingTalk file saved: {}", file_path)
            return str(file_path)
        except Exception as e:
            logger.error("DingTalk file download error: {}", e)
            return None
