"""Shared lifecycle hook primitives for agent runs.

代理运行时的共享生命周期钩子原语。

This module provides hook classes that allow customization of the agent execution lifecycle:
- AgentHookContext: Mutable per-iteration state exposed to runner hooks
- AgentHook: Minimal lifecycle surface for shared runner customization
- CompositeHook: Fan-out hook that delegates to an ordered list of hooks

该模块提供钩子类，允许自定义代理执行生命周期：
- AgentHookContext: 暴露给运行器钩子的每次迭代可变状态
- AgentHook: 用于共享运行器自定义的最小生命周期表面
- CompositeHook: 扇出钩子，委托给有序的钩子列表
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from nanobot.providers.base import LLMResponse, ToolCallRequest


@dataclass(slots=True)
class AgentHookContext:
    """Mutable per-iteration state exposed to runner hooks.
    
    暴露给运行器钩子的每次迭代可变状态。
    
    Attributes:
        iteration: Current iteration number / 当前迭代次数
        messages: Message list for the LLM call / LLM 调用的消息列表
        response: LLM response object / LLM 响应对象
        usage: Token usage statistics / Token 使用统计
        tool_calls: List of tool calls to execute / 要执行的工具调用列表
        tool_results: Results from executed tools / 已执行工具的结果
        tool_events: Tool execution events / 工具执行事件
        final_content: Final response content / 最终响应内容
        stop_reason: Reason for stopping / 停止原因
        error: Error message if any / 错误消息（如果有）
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


class AgentHook:
    """Minimal lifecycle surface for shared runner customization.
    
    用于共享运行器自定义的最小生命周期表面。
    
    This class provides empty default implementations for all lifecycle hooks.
    Subclass or compose with CompositeHook to customize behavior.
    
    该类为所有生命周期钩子提供空的默认实现。
    子类化或使用 CompositeHook 组合来自定义行为。
    """

    def __init__(self, reraise: bool = False) -> None:
        """Initialize the hook.
        
        Args:
            reraise: If True, re-raise exceptions instead of logging / 如果为 True，重新抛出异常而不是记录日志
        """
        self._reraise = reraise

    def wants_streaming(self) -> bool:
        return False

    async def before_iteration(self, context: AgentHookContext) -> None:
        pass

    async def on_stream(self, context: AgentHookContext, delta: str) -> None:
        pass

    async def on_stream_end(self, context: AgentHookContext, *, resuming: bool) -> None:
        pass

    async def before_execute_tools(self, context: AgentHookContext) -> None:
        pass

    async def after_iteration(self, context: AgentHookContext) -> None:
        pass

    def finalize_content(self, context: AgentHookContext, content: str | None) -> str | None:
        return content


class CompositeHook(AgentHook):
    """Fan-out hook that delegates to an ordered list of hooks.
    
    扇出钩子，委托给有序的钩子列表。

    Error isolation: async methods catch and log per-hook exceptions
    so a faulty custom hook cannot crash the agent loop.
    ``finalize_content`` is a pipeline (no isolation — bugs should surface).
    
    错误隔离：异步方法捕获并记录每个钩子的异常，
    因此故障的自定义钩子不会使代理循环崩溃。
    ``finalize_content`` 是一个管道（无隔离 - 错误应该暴露）。
    """

    __slots__ = ("_hooks",)  # Reduce memory usage / 减少内存使用

    def __init__(self, hooks: list[AgentHook]) -> None:
        """Initialize with a list of hooks.
        
        Args:
            hooks: List of hook instances to delegate to / 要委托的钩子实例列表
        """
        super().__init__()
        self._hooks = list(hooks)

    def wants_streaming(self) -> bool:
        return any(h.wants_streaming() for h in self._hooks)

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
