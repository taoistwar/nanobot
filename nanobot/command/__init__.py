"""Slash command routing and built-in handlers."""
# 斜杠命令路由和内置处理器
# 提供命令解析、分发和内置命令注册功能

from nanobot.command.builtin import register_builtin_commands
from nanobot.command.router import CommandContext, CommandRouter

__all__ = ["CommandContext", "CommandRouter", "register_builtin_commands"]
