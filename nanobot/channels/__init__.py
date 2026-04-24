"""Chat channels module with plugin architecture.
聊天频道模块，采用插件架构。
"""

from nanobot.channels.base import BaseChannel
from nanobot.channels.manager import ChannelManager

__all__ = ["BaseChannel", "ChannelManager"]
