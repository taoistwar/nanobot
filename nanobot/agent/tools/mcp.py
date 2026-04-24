"""MCP client: connects to MCP servers and wraps their tools as native nanobot tools.

MCP 客户端：连接到 MCP 服务器并将其工具包装为原生 nanobot 工具。

This module provides MCP integration:
- Connect to MCP servers (stdio or HTTP SSE)
- Wrap MCP tools as nanobot tools
- Handle transient connection errors with retry

本模块提供 MCP 集成：
- 连接到 MCP 服务器（stdio 或 HTTP SSE）
- 将 MCP 工具包装为 nanobot 工具
- 使用重试处理瞬态连接错误
"""

import asyncio
import os
import shutil
from contextlib import AsyncExitStack
from typing import Any

import httpx
from loguru import logger

from nanobot.agent.tools.base import Tool
from nanobot.agent.tools.registry import ToolRegistry

# Transient connection errors that warrant a single retry / 需要单次重试的瞬态连接错误
# These typically happen when an MCP server restarts or a network connection is interrupted between calls / 这些错误通常发生在 MCP 服务器重启或网络调用之间中断时
_TRANSIENT_EXC_NAMES: frozenset[str] = frozenset((
    "ClosedResourceError",
    "BrokenResourceError",
    "EndOfStream",
    "BrokenPipeError",
    "ConnectionResetError",
    "ConnectionRefusedError",
    "ConnectionAbortedError",
    "ConnectionError",
))

# Windows shell command wrappers that need special handling for MCP stdio servers / Windows 上需要特殊处理以支持 MCP stdio 服务器的 shell 命令包装器
_WINDOWS_SHELL_LAUNCHERS: frozenset[str] = frozenset(("npx", "npm", "pnpm", "yarn", "bunx"))


def _is_transient(exc: BaseException) -> bool:
    """Check if an exception looks like a transient connection error / 检查异常是否看起来像瞬态连接错误"""
    return type(exc).__name__ in _TRANSIENT_EXC_NAMES


def _windows_command_basename(command: str) -> str:
    """Return the lowercase basename for a Windows command or path / 返回 Windows 命令或路径的小写基名"""
    return command.replace("\\", "/").rsplit("/", maxsplit=1)[-1].lower()


def _normalize_windows_stdio_command(
    command: str,
    args: list[str] | None,
    env: dict[str, str] | None,
) -> tuple[str, list[str], dict[str, str] | None]:
    """Wrap Windows shell launchers so MCP stdio servers start reliably / 包装 Windows shell 启动器以确保 MCP stdio 服务器可靠启动"""
    normalized_args = list(args or [])
    if os.name != "nt":
        return command, normalized_args, env

    basename = _windows_command_basename(command)
    if basename in {"cmd", "cmd.exe", "powershell", "powershell.exe", "pwsh", "pwsh.exe"}:
        return command, normalized_args, env

    if basename.endswith((".exe", ".com")):
        return command, normalized_args, env

    resolved = shutil.which(command, path=(env or {}).get("PATH")) or command
    resolved_basename = _windows_command_basename(resolved)
    should_wrap = (
        basename in _WINDOWS_SHELL_LAUNCHERS
        or basename.endswith((".cmd", ".bat"))
        or resolved_basename.endswith((".cmd", ".bat"))
    )
    if not should_wrap:
        return command, normalized_args, env

    comspec = (env or {}).get("COMSPEC") or os.environ.get("COMSPEC") or "cmd.exe"
    return comspec, ["/d", "/c", command, *normalized_args], env


def _extract_nullable_branch(options: Any) -> tuple[dict[str, Any], bool] | None:
    """Return the single non-null branch for nullable unions / 返回可空联合类型的单个非空分支"""
    if not isinstance(options, list):
        return None

    non_null: list[dict[str, Any]] = []
    saw_null = False
    for option in options:
        if not isinstance(option, dict):
            return None
        if option.get("type") == "null":
            saw_null = True
            continue
        non_null.append(option)

    if saw_null and len(non_null) == 1:
        return non_null[0], True
    return None


def _normalize_schema_for_openai(schema: Any) -> dict[str, Any]:
    """Normalize only nullable JSON Schema patterns for tool definitions / 仅标准化可空 JSON Schema 模式以用于工具定义"""
    if not isinstance(schema, dict):
        return {"type": "object", "properties": {}}

    normalized = dict(schema)

    raw_type = normalized.get("type")
    if isinstance(raw_type, list):
        non_null = [item for item in raw_type if item != "null"]
        if "null" in raw_type and len(non_null) == 1:
            normalized["type"] = non_null[0]
            normalized["nullable"] = True

    for key in ("oneOf", "anyOf"):
        nullable_branch = _extract_nullable_branch(normalized.get(key))
        if nullable_branch is not None:
            branch, _ = nullable_branch
            merged = {k: v for k, v in normalized.items() if k != key}
            merged.update(branch)
            normalized = merged
            normalized["nullable"] = True
            break

    if "properties" in normalized and isinstance(normalized["properties"], dict):
        normalized["properties"] = {
            name: _normalize_schema_for_openai(prop) if isinstance(prop, dict) else prop
            for name, prop in normalized["properties"].items()
        }

    if "items" in normalized and isinstance(normalized["items"], dict):
        normalized["items"] = _normalize_schema_for_openai(normalized["items"])

    if normalized.get("type") != "object":
        return normalized

    normalized.setdefault("properties", {})
    normalized.setdefault("required", [])
    return normalized


class MCPToolWrapper(Tool):
    """Wraps a single MCP server tool as a nanobot Tool / 将单个 MCP 服务器工具包装为 nanobot 工具"""

    def __init__(self, session, server_name: str, tool_def, tool_timeout: int = 30):
        """Initialize the MCP tool wrapper / 初始化 MCP 工具包装器

        Args:
            session: MCP client session / MCP 客户端会话
            server_name: Name of the MCP server / MCP 服务器名称
            tool_def: MCP tool definition / MCP 工具定义
            tool_timeout: Timeout in seconds for tool execution / 工具执行超时时间（秒）
        """
        self._session = session
        self._original_name = tool_def.name
        self._name = f"mcp_{server_name}_{tool_def.name}"
        self._description = tool_def.description or tool_def.name
        raw_schema = tool_def.inputSchema or {"type": "object", "properties": {}}
        self._parameters = _normalize_schema_for_openai(raw_schema)
        self._tool_timeout = tool_timeout

    @property
    def name(self) -> str:
        """Return the tool name / 返回工具名称"""
        return self._name

    @property
    def description(self) -> str:
        """Return the tool description / 返回工具描述"""
        return self._description

    @property
    def parameters(self) -> dict[str, Any]:
        """Return the tool parameters schema / 返回工具参数模式"""
        return self._parameters

    async def execute(self, **kwargs: Any) -> str:
        """Execute the MCP tool with given arguments / 使用给定参数执行 MCP 工具

        Args:
            **kwargs: Tool arguments / 工具参数

        Returns:
            Tool execution result as string / 工具执行结果字符串
        """
        from mcp import types

        for attempt in range(2):  # At most 1 retry / 最多重试 1 次
            try:
                result = await asyncio.wait_for(
                    self._session.call_tool(self._original_name, arguments=kwargs),
                    timeout=self._tool_timeout,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "MCP tool '{}' timed out after {}s", self._name, self._tool_timeout
                )
                return f"(MCP tool call timed out after {self._tool_timeout}s)"
            except asyncio.CancelledError:
                # MCP SDK's anyio cancel scopes can leak CancelledError on timeout/failure.
                # Re-raise only if our task was externally cancelled (e.g. /stop).
                # MCP SDK 的 anyio 取消作用域可能在超时/失败时泄漏 CancelledError / 仅在任务被外部取消时重新抛出（例如 /stop）
                task = asyncio.current_task()
                if task is not None and task.cancelling() > 0:
                    raise
                logger.warning("MCP tool '{}' was cancelled by server/SDK", self._name)
                return "(MCP tool call was cancelled)"
            except Exception as exc:
                if _is_transient(exc):
                    if attempt == 0:
                        logger.warning(
                            "MCP tool '{}' hit transient error ({}), retrying once...",
                            self._name,
                            type(exc).__name__,
                        )
                        await asyncio.sleep(1)  # Brief backoff before retry / 重试前的短暂退避
                        continue
                    # Second transient failure — give up with retry-specific message
                    # 第二次瞬态失败 — 放弃并重试特定消息
                    logger.error(
                        "MCP tool '{}' failed after retry: {}: {}",
                        self._name,
                        type(exc).__name__,
                        exc,
                    )
                    return f"(MCP tool call failed after retry: {type(exc).__name__})"
                logger.exception(
                    "MCP tool '{}' failed: {}: {}",
                    self._name,
                    type(exc).__name__,
                    exc,
                )
                return f"(MCP tool call failed: {type(exc).__name__})"
            else:
                # Success — extract result / 成功 — 提取结果
                parts = []
                for block in result.content:
                    if isinstance(block, types.TextContent):
                        parts.append(block.text)
                    else:
                        parts.append(str(block))
                return "\n".join(parts) or "(no output)"

        return "(MCP tool call failed)"  # Unreachable, but satisfies type checkers / 不可达，但满足类型检查器


class MCPResourceWrapper(Tool):
    """Wraps an MCP resource URI as a read-only nanobot Tool / 将 MCP 资源 URI 包装为只读 nanobot 工具"""

    def __init__(self, session, server_name: str, resource_def, resource_timeout: int = 30):
        """Initialize the MCP resource wrapper / 初始化 MCP 资源包装器

        Args:
            session: MCP client session / MCP 客户端会话
            server_name: Name of the MCP server / MCP 服务器名称
            resource_def: MCP resource definition / MCP 资源定义
            resource_timeout: Timeout in seconds for resource read / 资源读取超时时间（秒）
        """
        self._session = session
        self._uri = resource_def.uri
        self._name = f"mcp_{server_name}_resource_{resource_def.name}"
        desc = resource_def.description or resource_def.name
        self._description = f"[MCP Resource] {desc}\nURI: {self._uri}"
        self._parameters: dict[str, Any] = {
            "type": "object",
            "properties": {},
            "required": [],
        }
        self._resource_timeout = resource_timeout

    @property
    def name(self) -> str:
        """Return the resource tool name / 返回资源工具名称"""
        return self._name

    @property
    def description(self) -> str:
        """Return the resource tool description / 返回资源工具描述"""
        return self._description

    @property
    def parameters(self) -> dict[str, Any]:
        """Return the resource tool parameters schema / 返回资源工具参数模式"""
        return self._parameters

    @property
    def read_only(self) -> bool:
        """Return True indicating this is a read-only tool / 返回 True 表示这是只读工具"""
        return True

    async def execute(self, **kwargs: Any) -> str:
        """Execute the MCP resource read operation / 执行 MCP 资源读取操作

        Args:
            **kwargs: Tool arguments (unused for resources) / 工具参数（资源不使用）

        Returns:
            Resource content as string / 资源内容字符串
        """
        from mcp import types

        for attempt in range(2):
            try:
                result = await asyncio.wait_for(
                    self._session.read_resource(self._uri),
                    timeout=self._resource_timeout,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "MCP resource '{}' timed out after {}s", self._name, self._resource_timeout
                )
                return f"(MCP resource read timed out after {self._resource_timeout}s)"
            except asyncio.CancelledError:
                task = asyncio.current_task()
                if task is not None and task.cancelling() > 0:
                    raise
                logger.warning("MCP resource '{}' was cancelled by server/SDK", self._name)
                return "(MCP resource read was cancelled)"
            except Exception as exc:
                if _is_transient(exc):
                    if attempt == 0:
                        logger.warning(
                            "MCP resource '{}' hit transient error ({}), retrying once...",
                            self._name,
                            type(exc).__name__,
                        )
                        await asyncio.sleep(1)
                        continue
                    logger.error(
                        "MCP resource '{}' failed after retry: {}: {}",
                        self._name,
                        type(exc).__name__,
                        exc,
                    )
                    return f"(MCP resource read failed after retry: {type(exc).__name__})"
                logger.exception(
                    "MCP resource '{}' failed: {}: {}",
                    self._name,
                    type(exc).__name__,
                    exc,
                )
                return f"(MCP resource read failed: {type(exc).__name__})"
            else:
                parts: list[str] = []
                for block in result.contents:
                    if isinstance(block, types.TextResourceContents):
                        parts.append(block.text)
                    elif isinstance(block, types.BlobResourceContents):
                        parts.append(f"[Binary resource: {len(block.blob)} bytes]")
                    else:
                        parts.append(str(block))
                return "\n".join(parts) or "(no output)"

        return "(MCP resource read failed)"  # Unreachable / 不可达


class MCPPromptWrapper(Tool):
    """Wraps an MCP prompt as a read-only nanobot Tool / 将 MCP 提示词包装为只读 nanobot 工具"""

    def __init__(self, session, server_name: str, prompt_def, prompt_timeout: int = 30):
        """Initialize the MCP prompt wrapper / 初始化 MCP 提示词包装器

        Args:
            session: MCP client session / MCP 客户端会话
            server_name: Name of the MCP server / MCP 服务器名称
            prompt_def: MCP prompt definition / MCP 提示词定义
            prompt_timeout: Timeout in seconds for prompt call / 提示词调用超时时间（秒）
        """
        self._session = session
        self._prompt_name = prompt_def.name
        self._name = f"mcp_{server_name}_prompt_{prompt_def.name}"
        desc = prompt_def.description or prompt_def.name
        self._description = (
            f"[MCP Prompt] {desc}\n"
            "Returns a filled prompt template that can be used as a workflow guide / "
            "返回可用于工作流指南的已填充提示词模板"
        )
        self._prompt_timeout = prompt_timeout

        # Build parameters from prompt arguments / 从提示词参数构建参数
        properties: dict[str, Any] = {}
        required: list[str] = []
        for arg in prompt_def.arguments or []:
            prop: dict[str, Any] = {"type": "string"}
            if getattr(arg, "description", None):
                prop["description"] = arg.description
            properties[arg.name] = prop
            if arg.required:
                required.append(arg.name)
        self._parameters: dict[str, Any] = {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    @property
    def name(self) -> str:
        """Return the prompt tool name / 返回提示词工具名称"""
        return self._name

    @property
    def description(self) -> str:
        """Return the prompt tool description / 返回提示词工具描述"""
        return self._description

    @property
    def parameters(self) -> dict[str, Any]:
        """Return the prompt tool parameters schema / 返回提示词工具参数模式"""
        return self._parameters

    @property
    def read_only(self) -> bool:
        """Return True indicating this is a read-only tool / 返回 True 表示这是只读工具"""
        return True

    async def execute(self, **kwargs: Any) -> str:
        """Execute the MCP prompt call / 执行 MCP 提示词调用

        Args:
            **kwargs: Prompt arguments / 提示词参数

        Returns:
            Filled prompt template as string / 已填充的提示词模板字符串
        """
        from mcp import types
        from mcp.shared.exceptions import McpError

        for attempt in range(2):
            try:
                result = await asyncio.wait_for(
                    self._session.get_prompt(self._prompt_name, arguments=kwargs),
                    timeout=self._prompt_timeout,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "MCP prompt '{}' timed out after {}s", self._name, self._prompt_timeout
                )
                return f"(MCP prompt call timed out after {self._prompt_timeout}s)"
            except asyncio.CancelledError:
                task = asyncio.current_task()
                if task is not None and task.cancelling() > 0:
                    raise
                logger.warning("MCP prompt '{}' was cancelled by server/SDK", self._name)
                return "(MCP prompt call was cancelled)"
            except McpError as exc:
                logger.error(
                    "MCP prompt '{}' failed: code={} message={}",
                    self._name,
                    exc.error.code,
                    exc.error.message,
                )
                return f"(MCP prompt call failed: {exc.error.message} [code {exc.error.code}])"
            except Exception as exc:
                if _is_transient(exc):
                    if attempt == 0:
                        logger.warning(
                            "MCP prompt '{}' hit transient error ({}), retrying once...",
                            self._name,
                            type(exc).__name__,
                        )
                        await asyncio.sleep(1)
                        continue
                    logger.error(
                        "MCP prompt '{}' failed after retry: {}: {}",
                        self._name,
                        type(exc).__name__,
                        exc,
                    )
                    return f"(MCP prompt call failed after retry: {type(exc).__name__})"
                logger.exception(
                    "MCP prompt '{}' failed: {}: {}",
                    self._name,
                    type(exc).__name__,
                    exc,
                )
                return f"(MCP prompt call failed: {type(exc).__name__})"
            else:
                parts: list[str] = []
                for message in result.messages:
                    content = message.content
                    if isinstance(content, types.TextContent):
                        parts.append(content.text)
                    elif isinstance(content, list):
                        for block in content:
                            if isinstance(block, types.TextContent):
                                parts.append(block.text)
                            else:
                                parts.append(str(block))
                    else:
                        parts.append(str(content))
                return "\n".join(parts) or "(no output)"

        return "(MCP prompt call failed)"  # Unreachable / 不可达


async def connect_mcp_servers(
    mcp_servers: dict, registry: ToolRegistry
) -> dict[str, AsyncExitStack]:
    """Connect to configured MCP servers and register their tools, resources, and prompts / 连接到已配置的 MCP 服务器并注册其工具、资源和提示词

    This function establishes connections to all configured MCP servers using their
    specified transport type (stdio, SSE, or Streamable HTTP). Each server gets its
    own AsyncExitStack and runs in a dedicated task to prevent cancel scope conflicts.
    All discovered tools, resources, and prompts are registered with the provided
    ToolRegistry.

    此函数使用指定的传输类型（stdio、SSE 或 Streamable HTTP）连接到所有已配置的 MCP 服务器。
    每个服务器都有自己的 AsyncExitStack 并在专用任务中运行，以防止取消作用域冲突。
    所有发现的工具、资源和提示词都将注册到提供的 ToolRegistry 中。

    Args:
        mcp_servers: Dictionary of server configurations / 服务器配置字典
        registry: ToolRegistry to register discovered tools / 用于注册已发现工具的工具注册表

    Returns:
        Dictionary mapping server name to its AsyncExitStack / 将服务器名称映射到其 AsyncExitStack 的字典
    """
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.sse import sse_client
    from mcp.client.stdio import stdio_client
    from mcp.client.streamable_http import streamable_http_client

    async def connect_single_server(name: str, cfg) -> tuple[str, AsyncExitStack | None]:
        """Connect to a single MCP server and register its capabilities / 连接到单个 MCP 服务器并注册其功能

        This nested function handles the connection logic for one MCP server, including
        transport setup, session initialization, and capability discovery. It supports
        stdio, SSE, and Streamable HTTP transports.

        此嵌套函数处理单个 MCP 服务器的连接逻辑，包括传输设置、会话初始化和功能发现。
        它支持 stdio、SSE 和 Streamable HTTP 传输。

        Args:
            name: Server name for identification / 用于标识的服务器名称
            cfg: Server configuration object / 服务器配置对象

        Returns:
            Tuple of (server_name, AsyncExitStack or None) / （服务器名称，AsyncExitStack 或 None）元组
        """
        server_stack = AsyncExitStack()
        await server_stack.__aenter__()

        try:
            transport_type = cfg.type
            if not transport_type:
                if cfg.command:
                    transport_type = "stdio"
                elif cfg.url:
                    transport_type = (
                        "sse" if cfg.url.rstrip("/").endswith("/sse") else "streamableHttp"
                    )
                else:
                    logger.warning("MCP server '{}': no command or url configured, skipping", name)
                    await server_stack.aclose()
                    return name, None

            if transport_type == "stdio":
                command, args, env = _normalize_windows_stdio_command(
                    cfg.command,
                    cfg.args,
                    cfg.env or None,
                )
                params = StdioServerParameters(
                    command=command,
                    args=args,
                    env=env,
                )
                read, write = await server_stack.enter_async_context(stdio_client(params))
            elif transport_type == "sse":

                def httpx_client_factory(
                    headers: dict[str, str] | None = None,
                    timeout: httpx.Timeout | None = None,
                    auth: httpx.Auth | None = None,
                ) -> httpx.AsyncClient:
                    merged_headers = {
                        "Accept": "application/json, text/event-stream",
                        **(cfg.headers or {}),
                        **(headers or {}),
                    }
                    return httpx.AsyncClient(
                        headers=merged_headers or None,
                        follow_redirects=True,
                        timeout=timeout,
                        auth=auth,
                    )

                read, write = await server_stack.enter_async_context(
                    sse_client(cfg.url, httpx_client_factory=httpx_client_factory)
                )
            elif transport_type == "streamableHttp":
                http_client = await server_stack.enter_async_context(
                    httpx.AsyncClient(
                        headers=cfg.headers or None,
                        follow_redirects=True,
                        timeout=None,
                    )
                )
                read, write, _ = await server_stack.enter_async_context(
                    streamable_http_client(cfg.url, http_client=http_client)
                )
            else:
                logger.warning("MCP server '{}': unknown transport type '{}'", name, transport_type)
                await server_stack.aclose()
                return name, None

            session = await server_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            tools = await session.list_tools()
            enabled_tools = set(cfg.enabled_tools)
            allow_all_tools = "*" in enabled_tools
            registered_count = 0
            matched_enabled_tools: set[str] = set()
            available_raw_names = [tool_def.name for tool_def in tools.tools]
            available_wrapped_names = [f"mcp_{name}_{tool_def.name}" for tool_def in tools.tools]
            for tool_def in tools.tools:
                wrapped_name = f"mcp_{name}_{tool_def.name}"
                if (
                    not allow_all_tools
                    and tool_def.name not in enabled_tools
                    and wrapped_name not in enabled_tools
                ):
                    logger.debug(
                        "MCP: skipping tool '{}' from server '{}' (not in enabledTools)",
                        wrapped_name,
                        name,
                    )
                    continue
                wrapper = MCPToolWrapper(session, name, tool_def, tool_timeout=cfg.tool_timeout)
                registry.register(wrapper)
                logger.debug("MCP: registered tool '{}' from server '{}'", wrapper.name, name)
                registered_count += 1
                if enabled_tools:
                    if tool_def.name in enabled_tools:
                        matched_enabled_tools.add(tool_def.name)
                    if wrapped_name in enabled_tools:
                        matched_enabled_tools.add(wrapped_name)

            if enabled_tools and not allow_all_tools:
                unmatched_enabled_tools = sorted(enabled_tools - matched_enabled_tools)
                if unmatched_enabled_tools:
                    logger.warning(
                        "MCP server '{}': enabledTools entries not found: {}. Available raw names: {}. "
                        "Available wrapped names: {}",
                        name,
                        ", ".join(unmatched_enabled_tools),
                        ", ".join(available_raw_names) or "(none)",
                        ", ".join(available_wrapped_names) or "(none)",
                    )

            try:
                resources_result = await session.list_resources()
                for resource in resources_result.resources:
                    wrapper = MCPResourceWrapper(
                        session, name, resource, resource_timeout=cfg.tool_timeout
                    )
                    registry.register(wrapper)
                    registered_count += 1
                    logger.debug(
                        "MCP: registered resource '{}' from server '{}'", wrapper.name, name
                    )
            except Exception as e:
                logger.debug("MCP server '{}': resources not supported or failed: {}", name, e)

            try:
                prompts_result = await session.list_prompts()
                for prompt in prompts_result.prompts:
                    wrapper = MCPPromptWrapper(
                        session, name, prompt, prompt_timeout=cfg.tool_timeout
                    )
                    registry.register(wrapper)
                    registered_count += 1
                    logger.debug("MCP: registered prompt '{}' from server '{}'", wrapper.name, name)
            except Exception as e:
                logger.debug("MCP server '{}': prompts not supported or failed: {}", name, e)

            logger.info(
                "MCP server '{}': connected, {} capabilities registered", name, registered_count
            )
            return name, server_stack

        except Exception as e:
            hint = ""
            text = str(e).lower()
            if any(
                marker in text
                for marker in (
                    "parse error",
                    "invalid json",
                    "unexpected token",
                    "jsonrpc",
                    "content-length",
                )
            ):
                hint = (
                    " Hint: this looks like stdio protocol pollution. Make sure the MCP server writes "
                    "only JSON-RPC to stdout and sends logs/debug output to stderr instead."
                )
            logger.error("MCP server '{}': failed to connect: {}{}", name, e, hint)
            try:
                await server_stack.aclose()
            except Exception:
                pass
            return name, None

    server_stacks: dict[str, AsyncExitStack] = {}

    tasks: list[asyncio.Task] = []
    for name, cfg in mcp_servers.items():
        task = asyncio.create_task(connect_single_server(name, cfg))
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        name = list(mcp_servers.keys())[i]
        if isinstance(result, BaseException):
            if not isinstance(result, asyncio.CancelledError):
                logger.error("MCP server '{}' connection task failed: {}", name, result)
        elif result is not None and result[1] is not None:
            server_stacks[result[0]] = result[1]

    return server_stacks
