"""重启通知消息的辅助工具模块。"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

RESTART_NOTIFY_CHANNEL_ENV = "NANOBOT_RESTART_NOTIFY_CHANNEL"
RESTART_NOTIFY_CHAT_ID_ENV = "NANOBOT_RESTART_NOTIFY_CHAT_ID"
RESTART_STARTED_AT_ENV = "NANOBOT_RESTART_STARTED_AT"


@dataclass(frozen=True)
class RestartNotice:
    channel: str
    chat_id: str
    started_at_raw: str


def format_restart_completed_message(started_at_raw: str) -> str:
    """构建重启完成文本，并在可用时包含已用时间。"""
    elapsed_suffix = ""
    if started_at_raw:
        try:
            elapsed_s = max(0.0, time.time() - float(started_at_raw))
            elapsed_suffix = f" in {elapsed_s:.1f}s"
        except ValueError:
            pass
    return f"Restart completed{elapsed_suffix}."


def set_restart_notice_to_env(*, channel: str, chat_id: str) -> None:
    """将重启通知环境变量写入，供下一个进程使用。"""
    os.environ[RESTART_NOTIFY_CHANNEL_ENV] = channel
    os.environ[RESTART_NOTIFY_CHAT_ID_ENV] = chat_id
    os.environ[RESTART_STARTED_AT_ENV] = str(time.time())


def consume_restart_notice_from_env() -> RestartNotice | None:
    """读取并清除本进程的重启通知环境变量（仅执行一次）。"""
    channel = os.environ.pop(RESTART_NOTIFY_CHANNEL_ENV, "").strip()
    chat_id = os.environ.pop(RESTART_NOTIFY_CHAT_ID_ENV, "").strip()
    started_at_raw = os.environ.pop(RESTART_STARTED_AT_ENV, "").strip()
    if not (channel and chat_id):
        return None
    return RestartNotice(channel=channel, chat_id=chat_id, started_at_raw=started_at_raw)


def should_show_cli_restart_notice(notice: RestartNotice, session_id: str) -> bool:
    """当此 CLI 会话中应显示重启通知时返回 True。"""
    if notice.channel != "cli":
        return False
    if ":" in session_id:
        _, cli_chat_id = session_id.split(":", 1)
    else:
        cli_chat_id = session_id
    return not notice.chat_id or notice.chat_id == cli_chat_id
