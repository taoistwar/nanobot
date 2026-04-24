"""Minimal command routing table for slash commands.
简洁的斜杠命令路由表实现。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Awaitable, Callable

if TYPE_CHECKING:
    from nanobot.bus.events import InboundMessage, OutboundMessage
    from nanobot.session.manager import Session

Handler = Callable[["CommandContext"], Awaitable["OutboundMessage | None"]]


@dataclass
class CommandContext:
    """Everything a command handler needs to produce a response.
    命令处理器生成响应所需的所有信息。"""

    msg: InboundMessage
    session: Session | None
    key: str
    raw: str
    args: str = ""
    loop: Any = None


class CommandRouter:
    """Pure dict-based command dispatch.
    纯字典实现的命令分发器。

    按顺序检查三个层级：
      1. *priority* — 精确匹配命令，在分发锁之前处理（如 /stop, /restart）。
      2. *exact* — 精确匹配命令，在分发锁内处理。
      3. *prefix* — 最长前缀优先匹配（如 "/team "）。
      4. *interceptors* — 备用谓词（如团队模式激活检查）。
    """

    def __init__(self) -> None:
        self._priority: dict[str, Handler] = {}
        self._exact: dict[str, Handler] = {}
        self._prefix: list[tuple[str, Handler]] = []
        self._interceptors: list[Handler] = []

    def priority(self, cmd: str, handler: Handler) -> None:
        """注册优先级命令（精确匹配，在锁外处理）。"""
        self._priority[cmd] = handler

    def exact(self, cmd: str, handler: Handler) -> None:
        """注册精确匹配命令（在锁内处理）。"""
        self._exact[cmd] = handler

    def prefix(self, pfx: str, handler: Handler) -> None:
        """注册前缀匹配命令（最长前缀优先）。"""
        self._prefix.append((pfx, handler))
        self._prefix.sort(key=lambda p: len(p[0]), reverse=True)

    def intercept(self, handler: Handler) -> None:
        """注册拦截器（备用谓词）。"""
        self._interceptors.append(handler)

    def is_priority(self, text: str) -> bool:
        """检查是否为优先级命令。"""
        return text.strip().lower() in self._priority

    def is_dispatchable_command(self, text: str) -> bool:
        """Check whether *text* matches any non-priority command tier (exact or prefix).
        检查文本是否匹配任何非优先级命令层级（精确或前缀）。

        Does NOT check priority or interceptor tiers.
        不检查优先级或拦截器层级。
        If this returns True, ``dispatch()`` is guaranteed to match a handler.
        如果返回 True，``dispatch()`` 保证能匹配到处理器。
        """
        cmd = text.strip().lower()
        if cmd in self._exact:
            return True
        for pfx, _ in self._prefix:
            if cmd.startswith(pfx):
                return True
        return False

    async def dispatch_priority(self, ctx: CommandContext) -> OutboundMessage | None:
        """Dispatch a priority command. Called from run() without the lock.
        分发优先级命令，从 run() 调用，不加锁。"""
        handler = self._priority.get(ctx.raw.lower())
        if handler:
            return await handler(ctx)
        return None

    async def dispatch(self, ctx: CommandContext) -> OutboundMessage | None:
        """Try exact, prefix, then interceptors. Returns None if unhandled.
        依次尝试精确匹配、前缀匹配和拦截器。如果未处理则返回 None。"""
        cmd = ctx.raw.lower()

        if handler := self._exact.get(cmd):
            return await handler(ctx)

        for pfx, handler in self._prefix:
            if cmd.startswith(pfx):
                ctx.args = ctx.raw[len(pfx):]
                return await handler(ctx)

        for interceptor in self._interceptors:
            result = await interceptor(ctx)
            if result is not None:
                return result

        return None
