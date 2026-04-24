"""Shared lifecycle hook primitives for agent runs.
// 代理运行生命周期钩子基元，提供运行迭代各阶段的扩展点。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from nanobot.providers.base import LLMResponse, ToolCallRequest


# 每次迭代的可变状态容器，暴露给 runner 钩子使用
# Mutable per-iteration state exposed to runner hooks
@dataclass(slots=True)
class AgentHookContext:
    """Mutable per-iteration state exposed to runner hooks.
    // 每次迭代的可变状态，暴露给 runner 钩子使用。
    """

    iteration: int
    messages: list[dict[str, Any]]
    response: LLMResponse | None = None
    usage: dict[str, int] = field(default_factory=dict)
    tool_calls: list[ToolCallRequest] = field(default_factory=list)
    tool_results: list[Any] = field(default_factory=list)
    tool_events: list[dict[str, str]] = field(default_factory=list)
    final_content: str | None = None
    stop_reason: str | None = None
    error: str | None = None


# 生命周期钩子抽象基类，提供 runner 自定义的最小接口
# Minimal lifecycle surface for shared runner customization
class AgentHook:
    """Minimal lifecycle surface for shared runner customization.
    // 生命周期钩子抽象基类，为 runner 提供自定义扩展的最小接口。
    """

    def __init__(self, reraise: bool = False) -> None:
        self._reraise = reraise

    def wants_streaming(self) -> bool:
        return False

    # 迭代开始前调用，可用于准备检查或状态更新
    # Called before iteration starts, can be used for preparation or state updates
    async def before_iteration(self, context: AgentHookContext) -> None:
        pass

    # 流式输出时的内容增量回调
    # Called with each content delta during streaming
    async def on_stream(self, context: AgentHookContext, delta: str) -> None:
        pass

    # 流式输出结束时的回调
    # Called when streaming ends
    async def on_stream_end(self, context: AgentHookContext, *, resuming: bool) -> None:
        pass

    # 工具执行前的回调
    # Called before tool execution
    async def before_execute_tools(self, context: AgentHookContext) -> None:
        pass

    # 迭代结束后的回调
    # Called after iteration completes
    async def after_iteration(self, context: AgentHookContext) -> None:
        pass

    # 最终内容确定前的回调，可用于内容后处理
    # Called before final content is finalized, can be used for post-processing
    def finalize_content(self, context: AgentHookContext, content: str | None) -> str | None:
        return content


# 组合钩子，将调用分发给有序的钩子列表
# Fan-out hook that delegates to an ordered list of hooks
class CompositeHook(AgentHook):
    """Fan-out hook that delegates to an ordered list of hooks.
    // 组合钩子，将调用分发给有序的钩子列表。

    Error isolation: async methods catch and log per-hook exceptions
    so a faulty custom hook cannot crash the agent loop.
    // 错误隔离：异步方法捕获并记录每个钩子的异常，防止故障钩子导致代理循环崩溃。
    ``finalize_content`` is a pipeline (no isolation — bugs should surface).
    // finalize_content 是管道式调用（无隔离——bug 会暴露出来）。
    """

    __slots__ = ("_hooks",)

    def __init__(self, hooks: list[AgentHook]) -> None:
        super().__init__()
        self._hooks = list(hooks)

    def wants_streaming(self) -> bool:
        return any(h.wants_streaming() for h in self._hooks)

    # 安全地遍历每个钩子执行方法，隔离单个钩子的异常
    # Safely iterate through each hook and execute method, isolating individual hook exceptions
    async def _for_each_hook_safe(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        for h in self._hooks:
            if getattr(h, "_reraise", False):
                await getattr(h, method_name)(*args, **kwargs)
                continue

            try:
                await getattr(h, method_name)(*args, **kwargs)
            except Exception:
                logger.exception("AgentHook.{} error in {}", method_name, type(h).__name__)

    async def before_iteration(self, context: AgentHookContext) -> None:
        await self._for_each_hook_safe("before_iteration", context)

    async def on_stream(self, context: AgentHookContext, delta: str) -> None:
        await self._for_each_hook_safe("on_stream", context, delta)

    async def on_stream_end(self, context: AgentHookContext, *, resuming: bool) -> None:
        await self._for_each_hook_safe("on_stream_end", context, resuming=resuming)

    async def before_execute_tools(self, context: AgentHookContext) -> None:
        await self._for_each_hook_safe("before_execute_tools", context)

    async def after_iteration(self, context: AgentHookContext) -> None:
        await self._for_each_hook_safe("after_iteration", context)

    def finalize_content(self, context: AgentHookContext, content: str | None) -> str | None:
        for h in self._hooks:
            content = h.finalize_content(context, content)
        return content
