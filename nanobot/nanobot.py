"""
High-level programmatic interface to nanobot.
nanobot 的高级程序化接口。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nanobot.agent.hook import AgentHook
from nanobot.agent.loop import AgentLoop
from nanobot.bus.queue import MessageBus


@dataclass(slots=True)
class RunResult:
    """
    Result of a single agent run.
    单次 Agent 运行的执行结果。
    """

    content: str
    tools_used: list[str]
    messages: list[dict[str, Any]]


class Nanobot:
    """
    Programmatic facade for running the nanobot agent.
    运行 nanobot agent 的程序化外观类。

    Usage::
    使用示例::

        bot = Nanobot.from_config()
        result = await bot.run("Summarize this repo", hooks=[MyHook()])
        print(result.content)
    """

    def __init__(self, loop: AgentLoop) -> None:
        """
        Initialize Nanobot with an agent loop.
        使用 agent loop 初始化 Nanobot。

        Args:
            loop: AgentLoop instance that handles agent execution.
                  处理 agent 执行逻辑的 AgentLoop 实例。
        """
        self._loop = loop

    @classmethod
    def from_config(
        cls,
        config_path: str | Path | None = None,
        *,
        workspace: str | Path | None = None,
    ) -> Nanobot:
        """
        Create a Nanobot instance from a config file.
        从配置文件创建 Nanobot 实例。

        Args:
            config_path: Path to ``config.json``.  Defaults to
                ``~/.nanobot/config.json``.
                配置文件路径，默认为 ``~/.nanobot/config.json``。
            workspace: Override the workspace directory from config.
                       覆盖配置文件中的工作目录设置。
        """
        from nanobot.config.loader import load_config, resolve_config_env_vars
        from nanobot.config.schema import Config

        resolved: Path | None = None
        # 如果指定了配置文件路径，则解析该路径
        # Resolve the config file path if provided
        if config_path is not None:
            resolved = Path(config_path).expanduser().resolve()
            if not resolved.exists():
                raise FileNotFoundError(f"Config not found: {resolved}")

        # 加载配置并解析环境变量引用
        # Load config and resolve environment variable references
        config: Config = resolve_config_env_vars(load_config(resolved))
        # 如果传入了 workspace 参数，则覆盖配置中的 workspace 设置
        # Override workspace setting if workspace parameter is provided
        if workspace is not None:
            config.agents.defaults.workspace = str(
                Path(workspace).expanduser().resolve()
            )

        # 根据配置创建 LLM provider
        # Create LLM provider based on configuration
        provider = _make_provider(config)
        # 创建消息总线
        # Create message bus
        bus = MessageBus()
        defaults = config.agents.defaults

        # 创建 AgentLoop 实例，整合所有配置
        # Create AgentLoop instance with all configurations
        loop = AgentLoop(
            bus=bus,
            provider=provider,
            workspace=config.workspace_path,
            model=defaults.model,
            max_iterations=defaults.max_tool_iterations,
            context_window_tokens=defaults.context_window_tokens,
            context_block_limit=defaults.context_block_limit,
            max_tool_result_chars=defaults.max_tool_result_chars,
            provider_retry_mode=defaults.provider_retry_mode,
            web_config=config.tools.web,
            exec_config=config.tools.exec,
            restrict_to_workspace=config.tools.restrict_to_workspace,
            mcp_servers=config.tools.mcp_servers,
            timezone=defaults.timezone,
            unified_session=defaults.unified_session,
            disabled_skills=defaults.disabled_skills,
            session_ttl_minutes=defaults.session_ttl_minutes,
            tools_config=config.tools,
        )
        return cls(loop)

    async def run(
        self,
        message: str,
        *,
        session_key: str = "sdk:default",
        hooks: list[AgentHook] | None = None,
    ) -> RunResult:
        """
        Run the agent once and return the result.
        执行一次 agent 并返回结果。

        Args:
            message: The user message to process.
                     要处理的用户消息。
            session_key: Session identifier for conversation isolation.
                Different keys get independent history.
                会话标识符，用于隔离对话历史，不同 key 获得独立历史。
            hooks: Optional lifecycle hooks for this run.
                   可选的声明周期钩子。
        """
        # 保存之前的 hooks 以便恢复
        # Save previous hooks for restoration
        prev = self._loop._extra_hooks
        if hooks is not None:
            self._loop._extra_hooks = list(hooks)
        try:
            # 处理直接消息
            # Process the direct message
            response = await self._loop.process_direct(
                message, session_key=session_key,
            )
        finally:
            # 恢复之前的 hooks
            # Restore previous hooks
            self._loop._extra_hooks = prev

        content = (response.content if response else None) or ""
        return RunResult(content=content, tools_used=[], messages=[])


def _make_provider(config: Any) -> Any:
    """
    Create the LLM provider from config (extracted from CLI).
    根据配置创建 LLM provider（从 CLI 提取）。
    """
    from nanobot.providers.base import GenerationSettings
    from nanobot.providers.registry import find_by_name

    # 从配置中获取模型名称和 provider 信息
    # Get model name and provider info from config
    model = config.agents.defaults.model
    provider_name = config.get_provider_name(model)
    p = config.get_provider(model)
    spec = find_by_name(provider_name) if provider_name else None
    backend = spec.backend if spec else "openai_compat"

    # 验证必需的配置参数
    # Validate required configuration parameters
    if backend == "azure_openai":
        if not p or not p.api_key or not p.api_base:
            raise ValueError("Azure OpenAI requires api_key and api_base in config.")
    elif backend == "openai_compat" and not model.startswith("bedrock/"):
        needs_key = not (p and p.api_key)
        exempt = spec and (spec.is_oauth or spec.is_local or spec.is_direct)
        if needs_key and not exempt:
            raise ValueError(f"No API key configured for provider '{provider_name}'.")

    # 根据 backend 类型创建对应的 provider 实例
    # Create the appropriate provider instance based on backend type
    if backend == "openai_codex":
        from nanobot.providers.openai_codex_provider import OpenAICodexProvider

        provider = OpenAICodexProvider(default_model=model)
    elif backend == "github_copilot":
        from nanobot.providers.github_copilot_provider import GitHubCopilotProvider

        provider = GitHubCopilotProvider(default_model=model)
    elif backend == "azure_openai":
        from nanobot.providers.azure_openai_provider import AzureOpenAIProvider

        provider = AzureOpenAIProvider(
            api_key=p.api_key, api_base=p.api_base, default_model=model
        )
    elif backend == "anthropic":
        from nanobot.providers.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider(
            api_key=p.api_key if p else None,
            api_base=config.get_api_base(model),
            default_model=model,
            extra_headers=p.extra_headers if p else None,
        )
    else:
        from nanobot.providers.openai_compat_provider import OpenAICompatProvider

        provider = OpenAICompatProvider(
            api_key=p.api_key if p else None,
            api_base=config.get_api_base(model),
            default_model=model,
            extra_headers=p.extra_headers if p else None,
            spec=spec,
        )

    # 设置 generation 参数（temperature, max_tokens 等）
    # Set generation parameters (temperature, max_tokens, etc.)
    defaults = config.agents.defaults
    provider.generation = GenerationSettings(
        temperature=defaults.temperature,
        max_tokens=defaults.max_tokens,
        reasoning_effort=defaults.reasoning_effort,
    )
    return provider
