"""Tool registry for dynamic tool management.

工具注册表：用于动态工具管理。

This module provides the ToolRegistry class for managing agent tools,
including registration, unregistration, and execution.

本模块提供 ToolRegistry 类用于管理代理工具，
包括注册、注销和执行。
"""

from typing import Any

from nanobot.agent.tools.base import Tool


class ToolRegistry:
    """
    Registry for agent tools.

    Allows dynamic registration and execution of tools.
    
    代理工具注册表。
    
    允许动态注册和执行工具。
    """

    def __init__(self):
        """Initialize the tool registry.
        
        初始化工具注册表。
        """
        self._tools: dict[str, Tool] = {}
        self._cached_definitions: list[dict[str, Any]] | None = None

    def register(self, tool: Tool) -> None:
        """Register a tool.
        
        注册工具。
        
        Args:
            tool: Tool to register / 要注册的工具
        """
        self._tools[tool.name] = tool
        self._cached_definitions = None

    def unregister(self, name: str) -> None:
        """Unregister a tool by name.
        
        按名称注销工具。
        
        Args:
            name: Tool name / 工具名称
        """
        self._tools.pop(name, None)
        self._cached_definitions = None

    def get(self, name: str) -> Tool | None:
        """Get a tool by name.
        
        按名称获取工具。
        
        Args:
            name: Tool name / 工具名称
            
        Returns:
            Tool or None / 工具或 None
        """
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        """Check if a tool is registered.
        
        检查工具是否已注册。
        
        Args:
            name: Tool name / 工具名称
            
        Returns:
            True if tool is registered / 如果工具已注册则返回 True
        """
        return name in self._tools

    @staticmethod
    def _schema_name(schema: dict[str, Any]) -> str:
        """Extract a normalized tool name from either OpenAI or flat schemas.
        
        从 OpenAI 或扁平模式中提取规范化的工具名称。
        
        Args:
            schema: Tool schema / 工具模式
            
        Returns:
            Normalized tool name / 规范化的工具名称
        """
        fn = schema.get("function")
        if isinstance(fn, dict):
            name = fn.get("name")
            if isinstance(name, str):
                return name
        name = schema.get("name")
        return name if isinstance(name, str) else ""

    def get_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions with stable ordering for cache-friendly prompts.

        Built-in tools are sorted first as a stable prefix, then MCP tools are
        sorted and appended.  The result is cached until the next
        register/unregister call.
        
        获取具有稳定顺序的工具定义，以便缓存友好的提示。
        
        内置工具首先排序作为稳定前缀，然后 MCP 工具排序并追加。
        结果会被缓存直到下一次 register/unregister 调用。
        
        Returns:
            List of tool definitions / 工具定义列表
        """
        if self._cached_definitions is not None:
            return self._cached_definitions

        definitions = [tool.to_schema() for tool in self._tools.values()]
        builtins: list[dict[str, Any]] = []
        mcp_tools: list[dict[str, Any]] = []
        for schema in definitions:
            name = self._schema_name(schema)
            if name.startswith("mcp_"):
                mcp_tools.append(schema)
            else:
                builtins.append(schema)

        builtins.sort(key=self._schema_name)
        mcp_tools.sort(key=self._schema_name)
        self._cached_definitions = builtins + mcp_tools
        return self._cached_definitions

    def prepare_call(
        self,
        name: str,
        params: dict[str, Any],
    ) -> tuple[Tool | None, dict[str, Any], str | None]:
        """Resolve, cast, and validate one tool call.
        
        解析、转换和验证一个工具调用。
        
        Args:
            name: Tool name / 工具名称
            params: Tool parameters / 工具参数
            
        Returns:
            Tuple of (tool, cast params, error message) / (工具，转换后的参数，错误消息) 元组
        """
        # Guard against invalid parameter types (e.g., list instead of dict)
        # 防止无效参数类型（例如，list 而不是 dict）
        if not isinstance(params, dict) and name in ('write_file', 'read_file'):
            return None, params, (
                f"Error: Tool '{name}' parameters must be a JSON object, got {type(params).__name__}. "
                "Use named parameters: tool_name(param1=\"value1\", param2=\"value2\")"
            )

        tool = self._tools.get(name)
        if not tool:
            return None, params, (
                f"Error: Tool '{name}' not found. Available: {', '.join(self.tool_names)}"
            )

        cast_params = tool.cast_params(params)
        errors = tool.validate_params(cast_params)
        if errors:
            return tool, cast_params, (
                f"Error: Invalid parameters for tool '{name}': " + "; ".join(errors)
            )
        return tool, cast_params, None

    async def execute(self, name: str, params: dict[str, Any]) -> Any:
        """Execute a tool by name with given parameters.
        
        按名称执行工具并给定参数。
        
        Args:
            name: Tool name / 工具名称
            params: Tool parameters / 工具参数
            
        Returns:
            Tool execution result or error message / 工具执行结果或错误消息
        """
        _HINT = "\n\n[Analyze the error above and try a different approach.]"
        tool, params, error = self.prepare_call(name, params)
        if error:
            return error + _HINT

        try:
            assert tool is not None  # guarded by prepare_call()
            result = await tool.execute(**params)
            if isinstance(result, str) and result.startswith("Error"):
                return result + _HINT
            return result
        except Exception as e:
            return f"Error executing {name}: {str(e)}" + _HINT

    @property
    def tool_names(self) -> list[str]:
        """Get list of registered tool names.
        
        获取已注册工具名称列表。
        
        Returns:
            List of tool names / 工具名称列表
        """
        return list(self._tools.keys())

    def __len__(self) -> int:
        """Get number of registered tools.
        
        获取已注册工具数量。
        
        Returns:
            Number of tools / 工具数量
        """
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if tool is registered.
        
        检查工具是否已注册。
        
        Args:
            name: Tool name / 工具名称
            
        Returns:
            True if tool is registered / 如果工具已注册则返回 True
        """
        return name in self._tools
