"""Streaming renderer for CLI output.

Uses Rich Live with auto_refresh=False for stable, flicker-free
markdown rendering during streaming. Ellipsis mode handles overflow.
"""

from __future__ import annotations

import sys
import time

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text

from nanobot import __logo__


def _make_console() -> Console:
    """Create a Console that emits plain text when stdout is not a TTY.
    创建控制台实例，当 stdout 不是 TTY 时输出纯文本。

    Rich 的 spinner、Live 渲染和光标可见性转义码都依赖 ``Console.is_terminal``。
    强制 ``force_terminal=True`` 会覆盖 ``isatty()`` 检查，导致控制序列污染程序化消费者。
    遵循 ``isatty()`` 可保持交互式终端中的 Rich 输出，同时在其他地方输出纯文本。
    """
    return Console(file=sys.stdout, force_terminal=sys.stdout.isatty())


class ThinkingSpinner:
    """Spinner that shows 'nanobot is thinking...' with pause support.
    显示 'nanobot is thinking...' 的旋转指示器，支持暂停。"""

    def __init__(self, console: Console | None = None):
        c = console or _make_console()
        self._spinner = c.status("[dim]nanobot is thinking...[/dim]", spinner="dots")
        self._active = False

    def __enter__(self):
        self._spinner.start()
        self._active = True
        return self

    def __exit__(self, *exc):
        self._active = False
        self._spinner.stop()
        return False

    def pause(self):
        """Context manager: temporarily stop spinner for clean output.
        上下文管理器：临时停止旋转指示器以获得清晰输出。"""
        from contextlib import contextmanager

        @contextmanager
        def _ctx():
            if self._spinner and self._active:
                self._spinner.stop()
            try:
                yield
            finally:
                if self._spinner and self._active:
                    self._spinner.start()

        return _ctx()


class StreamRenderer:
    """Rich Live streaming with markdown. auto_refresh=False avoids render races.
    使用 Rich Live 进行 Markdown 流式渲染，auto_refresh=False 避免渲染竞争。

    Deltas 来自 agent loop，已预先过滤（无 <think> 标签）。

    每轮流程：
      spinner -> 首个可见 delta -> header + Live 渲染 ->
      on_end -> Live 停止（内容保留在屏幕上）
    """

    def __init__(self, render_markdown: bool = True, show_spinner: bool = True):
        self._md = render_markdown
        self._show_spinner = show_spinner
        self._buf = ""
        self._live: Live | None = None
        self._t = 0.0
        self.streamed = False
        self._spinner: ThinkingSpinner | None = None
        self._start_spinner()

    def _render(self):
        return Markdown(self._buf) if self._md and self._buf else Text(self._buf or "")

    def _start_spinner(self) -> None:
        if self._show_spinner:
            self._spinner = ThinkingSpinner()
            self._spinner.__enter__()

    def _stop_spinner(self) -> None:
        if self._spinner:
            self._spinner.__exit__(None, None, None)
            self._spinner = None

    async def on_delta(self, delta: str) -> None:
        """处理流式响应的增量数据。"""
        self.streamed = True
        self._buf += delta
        if self._live is None:
            if not self._buf.strip():
                return
            self._stop_spinner()
            c = _make_console()
            c.print()
            c.print(f"[cyan]{__logo__} nanobot[/cyan]")
            self._live = Live(self._render(), console=c, auto_refresh=False)
            self._live.start()
        now = time.monotonic()
        if (now - self._t) > 0.15:
            self._live.update(self._render())
            self._live.refresh()
            self._t = now

    async def on_end(self, *, resuming: bool = False) -> None:
        """流式响应结束时的处理。"""
        if self._live:
            self._live.update(self._render())
            self._live.refresh()
            self._live.stop()
            self._live = None
        self._stop_spinner()
        if resuming:
            self._buf = ""
            self._start_spinner()
        else:
            _make_console().print()

    def stop_for_input(self) -> None:
        """Stop spinner before user input to avoid prompt_toolkit conflicts.
        在用户输入前停止旋转指示器，避免与 prompt_toolkit 冲突。"""
        self._stop_spinner()

    async def close(self) -> None:
        """Stop spinner/live without rendering a final streamed round.
        停止旋转指示器/Live，不渲染最终的流式轮次。"""
        if self._live:
            self._live.stop()
            self._live = None
        self._stop_spinner()
