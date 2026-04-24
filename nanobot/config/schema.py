"""
Configuration schema using Pydantic.
使用 Pydantic 的配置schema。
"""

from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_settings import BaseSettings

from nanobot.cron.types import CronSchedule


class Base(BaseModel):
    """
    Base model that accepts both camelCase and snake_case keys.
    基础模型，同时支持 camelCase 和 snake_case 键名。
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class ChannelsConfig(Base):
    """
    Configuration for chat channels.
    聊天渠道配置。

    Built-in and plugin channel configs are stored as extra fields (dicts).
    内置和插件渠道配置存储为额外字段（字典）。
    Each channel parses its own config in __init__.
    每个渠道在 __init__ 中解析自己的配置。
    Per-channel "streaming": true enables streaming output (requires send_delta impl).
    每个渠道的 "streaming": true 启用流式输出（需要实现 send_delta）。
    """

    model_config = ConfigDict(extra="allow")

    send_progress: bool = True  # stream agent's text progress to the channel / 将 agent 的文本进度流式传输到渠道
    send_tool_hints: bool = False  # stream tool-call hints (e.g. read_file("…")) / 流式传输工具调用提示
    send_max_retries: int = Field(default=3, ge=0, le=10)  # Max delivery attempts (initial send included) / 最大投递尝试次数
    transcription_provider: str = "groq"  # Voice transcription backend: "groq" or "openai" / 语音转录后端
    transcription_language: str | None = Field(default=None, pattern=r"^[a-z]{2,3}$")  # Optional ISO-639-1 hint for audio transcription / 可选的 ISO-639-1 语音转录语言提示


class DreamConfig(Base):
    """
    Dream memory consolidation configuration.
    梦境记忆整合配置。
    """

    _HOUR_MS = 3_600_000

    interval_h: int = Field(default=2, ge=1)  # Every 2 hours by default / 默认每2小时执行一次
    cron: str | None = Field(default=None, exclude=True)  # Legacy compatibility override / 旧版兼容性覆盖
    model_override: str | None = Field(
        default=None,
        validation_alias=AliasChoices("modelOverride", "model", "model_override"),
    )  # Optional Dream-specific model override / 可选的 Dream 专用模型覆盖
    max_batch_size: int = Field(default=20, ge=1)  # Max history entries per run / 每次运行的最大历史条目数
    # Bumped from 10 to 15 in #3212 (exp002: +30% dedup, no accuracy loss; >15 plateaus).
    # 在 #3212 中从 10 提升到 15（exp002: +30% 去重，无准确率损失；>15 趋于平稳）。
    max_iterations: int = Field(default=15, ge=1)  # Max tool calls per Phase 2 / 第二阶段最大工具调用次数
    # Per-line git-blame age annotation in Phase 1 prompt (see #3212). Default
    # on — set to False to feed MEMORY.md raw if a specific LLM reacts poorly
    # to the `← Nd` suffix or you want deterministic, git-independent prompts.
    # 第一阶段提示中的逐行 git-blame 年龄注释（见 #3212）。
    # 默认为开——如果特定 LLM 对 `← Nd` 后缀反应不佳或想要确定性的、独立的 git 提示，
    # 请设置为 False 以原始方式提供 MEMORY.md。
    annotate_line_ages: bool = True

    def build_schedule(self, timezone: str) -> CronSchedule:
        """
        Build the runtime schedule, preferring the legacy cron override if present.
        构建运行时调度计划，如果存在则优先使用旧版 cron 覆盖。
        """
        if self.cron:
            return CronSchedule(kind="cron", expr=self.cron, tz=timezone)
        return CronSchedule(kind="every", every_ms=self.interval_h * self._HOUR_MS)

    def describe_schedule(self) -> str:
        """
        Return a human-readable summary for logs and startup output.
        返回适合日志和启动输出的人类可读摘要。
        """
        if self.cron:
            return f"cron {self.cron} (legacy)"
        hours = self.interval_h
        return f"every {hours}h"


class AgentDefaults(Base):
    """
    Default agent configuration.
    默认 agent 配置。
    """

    workspace: str = "~/.nanobot/workspace"
    model: str = "anthropic/claude-opus-4-5"
    provider: str = (
        "auto"  # Provider name (e.g. "anthropic", "openrouter") or "auto" for auto-detection / Provider 名称或 "auto" 自动检测
    )
    max_tokens: int = 8192
    context_window_tokens: int = 65_536
    context_block_limit: int | None = None
    temperature: float = 0.1
    max_tool_iterations: int = 200
    max_tool_result_chars: int = 16_000
    provider_retry_mode: Literal["standard", "persistent"] = "standard"
    reasoning_effort: str | None = None  # low / medium / high / adaptive - enables LLM thinking mode / 启用 LLM 思考模式
    timezone: str = "UTC"  # IANA timezone, e.g. "Asia/Shanghai", "America/New_York" / IANA 时区
    unified_session: bool = False  # Share one session across all channels (single-user multi-device) / 在所有渠道间共享一个会话
    disabled_skills: list[str] = Field(default_factory=list)  # Skill names to exclude from loading / 要排除加载的技能名称
    session_ttl_minutes: int = Field(
        default=0,
        ge=0,
        validation_alias=AliasChoices("idleCompactAfterMinutes", "sessionTtlMinutes"),
        serialization_alias="idleCompactAfterMinutes",
    )  # Auto-compact idle threshold in minutes (0 = disabled) / 自动压缩空闲阈值（分钟）
    dream: DreamConfig = Field(default_factory=DreamConfig)


class AgentsConfig(Base):
    """
    Agent configuration.
    Agent 配置。
    """

    defaults: AgentDefaults = Field(default_factory=AgentDefaults)


class ProviderConfig(Base):
    """
    LLM provider configuration.
    LLM provider 配置。
    """

    api_key: str | None = None
    api_base: str | None = None
    extra_headers: dict[str, str] | None = None  # Custom headers (e.g. APP-Code for AiHubMix) / 自定义请求头


class ProvidersConfig(Base):
    """
    Configuration for LLM providers.
    LLM providers 配置。
    """

    custom: ProviderConfig = Field(default_factory=ProviderConfig)  # Any OpenAI-compatible endpoint / 任意 OpenAI 兼容端点
    azure_openai: ProviderConfig = Field(default_factory=ProviderConfig)  # Azure OpenAI (model = deployment name) / Azure OpenAI
    anthropic: ProviderConfig = Field(default_factory=ProviderConfig)
    openai: ProviderConfig = Field(default_factory=ProviderConfig)
    openrouter: ProviderConfig = Field(default_factory=ProviderConfig)
    deepseek: ProviderConfig = Field(default_factory=ProviderConfig)
    groq: ProviderConfig = Field(default_factory=ProviderConfig)
    zhipu: ProviderConfig = Field(default_factory=ProviderConfig)
    dashscope: ProviderConfig = Field(default_factory=ProviderConfig)
    vllm: ProviderConfig = Field(default_factory=ProviderConfig)
    ollama: ProviderConfig = Field(default_factory=ProviderConfig)  # Ollama local models / Ollama 本地模型
    lm_studio: ProviderConfig = Field(default_factory=ProviderConfig)  # LM Studio local models / LM Studio 本地模型
    ovms: ProviderConfig = Field(default_factory=ProviderConfig)  # OpenVINO Model Server (OVMS) / OpenVINO 模型服务器
    gemini: ProviderConfig = Field(default_factory=ProviderConfig)
    moonshot: ProviderConfig = Field(default_factory=ProviderConfig)
    minimax: ProviderConfig = Field(default_factory=ProviderConfig)
    minimax_anthropic: ProviderConfig = Field(default_factory=ProviderConfig)  # MiniMax Anthropic endpoint (thinking) / MiniMax Anthropic 端点
    mistral: ProviderConfig = Field(default_factory=ProviderConfig)
    stepfun: ProviderConfig = Field(default_factory=ProviderConfig)  # Step Fun (阶跃星辰) / 阶跃星辰
    xiaomi_mimo: ProviderConfig = Field(default_factory=ProviderConfig)  # Xiaomi MIMO (小米) / 小米
    aihubmix: ProviderConfig = Field(default_factory=ProviderConfig)  # AiHubMix API gateway / AiHubMix API 网关
    siliconflow: ProviderConfig = Field(default_factory=ProviderConfig)  # SiliconFlow (硅基流动) / 硅基流动
    volcengine: ProviderConfig = Field(default_factory=ProviderConfig)  # VolcEngine (火山引擎) / 火山引擎
    volcengine_coding_plan: ProviderConfig = Field(default_factory=ProviderConfig)  # VolcEngine Coding Plan / 火山引擎编程计划
    byteplus: ProviderConfig = Field(default_factory=ProviderConfig)  # BytePlus (VolcEngine international) / BytePlus
    byteplus_coding_plan: ProviderConfig = Field(default_factory=ProviderConfig)  # BytePlus Coding Plan / BytePlus 编程计划
    openai_codex: ProviderConfig = Field(default_factory=ProviderConfig, exclude=True)  # OpenAI Codex (OAuth) / OpenAI Codex
    github_copilot: ProviderConfig = Field(default_factory=ProviderConfig, exclude=True)  # Github Copilot (OAuth) / Github Copilot
    qianfan: ProviderConfig = Field(default_factory=ProviderConfig)  # Qianfan (百度千帆) / 百度千帆


class HeartbeatConfig(Base):
    """
    Heartbeat service configuration.
    心跳服务配置。
    """

    enabled: bool = True
    interval_s: int = 30 * 60  # 30 minutes / 30 分钟
    keep_recent_messages: int = 8


class ApiConfig(Base):
    """
    OpenAI-compatible API server configuration.
    OpenAI 兼容 API 服务器配置。
    """

    host: str = "127.0.0.1"  # Safer default: local-only bind. / 更安全的默认值：仅本地绑定
    port: int = 8900
    timeout: float = 120.0  # Per-request timeout in seconds. / 每个请求的超时时间（秒）


class GatewayConfig(Base):
    """
    Gateway/server configuration.
    网关/服务器配置。
    """

    host: str = "127.0.0.1"  # Safer default: local-only bind. / 更安全的默认值：仅本地绑定
    port: int = 18790
    heartbeat: HeartbeatConfig = Field(default_factory=HeartbeatConfig)


class WebSearchConfig(Base):
    """
    Web search tool configuration.
    Web 搜索工具配置。
    """

    provider: str = "duckduckgo"  # brave, tavily, duckduckgo, searxng, jina, kagi / 支持的搜索引擎
    api_key: str = ""
    base_url: str = ""  # SearXNG base URL / SearXNG 基础 URL
    max_results: int = 5
    timeout: int = 30  # Wall-clock timeout (seconds) for search operations / 搜索操作的超时时间（秒）


class WebToolsConfig(Base):
    """
    Web tools configuration.
    Web 工具配置。
    """

    enable: bool = True
    proxy: str | None = (
        None  # HTTP/SOCKS5 proxy URL, e.g. "http://127.0.0.1:7890" or "socks5://127.0.0.1:1080" / 代理 URL
    )
    search: WebSearchConfig = Field(default_factory=WebSearchConfig)


class ExecToolConfig(Base):
    """
    Shell exec tool configuration.
    Shell 执行工具配置。
    """

    enable: bool = True
    timeout: int = 60
    path_append: str = ""
    sandbox: str = ""  # sandbox backend: "" (none) or "bwrap" / 沙箱后端
    allowed_env_keys: list[str] = Field(default_factory=list)  # Env var names to pass through to subprocess / 传递给子进程的环境变量名

class MCPServerConfig(Base):
    """
    MCP server connection configuration (stdio or HTTP).
    MCP 服务器连接配置（stdio 或 HTTP）。
    """

    type: Literal["stdio", "sse", "streamableHttp"] | None = None  # auto-detected if omitted / 如省略则自动检测
    command: str = ""  # Stdio: command to run (e.g. "npx") / 要运行的命令
    args: list[str] = Field(default_factory=list)  # Stdio: command arguments / 命令参数
    env: dict[str, str] = Field(default_factory=dict)  # Stdio: extra env vars / 额外环境变量
    url: str = ""  # HTTP/SSE: endpoint URL / HTTP/SSE 端点 URL
    headers: dict[str, str] = Field(default_factory=dict)  # HTTP/SSE: custom headers / 自定义请求头
    tool_timeout: int = 30  # seconds before a tool call is cancelled / 工具调用取消前的秒数
    enabled_tools: list[str] = Field(default_factory=lambda: ["*"])  # Only register these tools / 仅注册这些工具

class MyToolConfig(Base):
    """
    Self-inspection tool configuration.
    自我检查工具配置。
    """

    enable: bool = True  # register the `my` tool (agent runtime state inspection) / 注册 `my` 工具
    allow_set: bool = False  # let `my` modify loop state (read-only if False) / 允许 `my` 修改 loop 状态


class ToolsConfig(Base):
    """
    Tools configuration.
    工具配置。
    """

    web: WebToolsConfig = Field(default_factory=WebToolsConfig)
    exec: ExecToolConfig = Field(default_factory=ExecToolConfig)
    my: MyToolConfig = Field(default_factory=MyToolConfig)
    restrict_to_workspace: bool = False  # restrict all tool access to workspace directory / 限制所有工具访问工作区目录
    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict)
    ssrf_whitelist: list[str] = Field(default_factory=list)  # CIDR ranges to exempt from SSRF blocking / SSRF 白名单


class Config(BaseSettings):
    """
    Root configuration for nanobot.
    nanobot 的根配置。
    """

    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    gateway: GatewayConfig = Field(default_factory=GatewayConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)

    @property
    def workspace_path(self) -> Path:
        """
        Get expanded workspace path.
        获取展开后的工作区路径。
        """
        return Path(self.agents.defaults.workspace).expanduser()

    def _match_provider(
        self, model: str | None = None
    ) -> tuple["ProviderConfig | None", str | None]:
        """
        Match provider config and its registry name. Returns (config, spec_name).
        匹配 provider 配置及其注册名称。返回 (config, spec_name)。
        """
        from nanobot.providers.registry import PROVIDERS, find_by_name

        forced = self.agents.defaults.provider
        # 如果强制指定了 provider，优先使用
        # If a provider is forced, use it first
        if forced != "auto":
            spec = find_by_name(forced)
            if spec:
                p = getattr(self.providers, spec.name, None)
                return (p, spec.name) if p else (None, None)
            return None, None

        # 标准化模型名称以进行匹配
        # Normalize model name for matching
        model_lower = (model or self.agents.defaults.model).lower()
        model_normalized = model_lower.replace("-", "_")
        model_prefix = model_lower.split("/", 1)[0] if "/" in model_lower else ""
        normalized_prefix = model_prefix.replace("-", "_")

        def _kw_matches(kw: str) -> bool:
            """
            Check if keyword matches the model name.
            检查关键词是否匹配模型名称。
            """
            kw = kw.lower()
            return kw in model_lower or kw.replace("-", "_") in model_normalized

        # 显式 provider 前缀优先——防止 `github-copilot/...codex` 匹配到 openai_codex
        # Explicit provider prefix wins — prevents `github-copilot/...codex` matching openai_codex
        for spec in PROVIDERS:
            p = getattr(self.providers, spec.name, None)
            if p and model_prefix and normalized_prefix == spec.name:
                if spec.is_oauth or spec.is_local or p.api_key:
                    return p, spec.name

        # 通过关键词匹配（按 PROVIDERS 注册表顺序）
        # Match by keyword (order follows PROVIDERS registry)
        for spec in PROVIDERS:
            p = getattr(self.providers, spec.name, None)
            if p and any(_kw_matches(kw) for kw in spec.keywords):
                if spec.is_oauth or spec.is_local or p.api_key:
                    return p, spec.name

        # 回退：配置了 api_base 的本地 provider 可以路由没有 provider 特定关键词的模型
        # Fallback: configured local providers can route models without provider-specific keywords
        local_fallback: tuple[ProviderConfig, str] | None = None
        for spec in PROVIDERS:
            if not spec.is_local:
                continue
            p = getattr(self.providers, spec.name, None)
            if not (p and p.api_base):
                continue
            if spec.detect_by_base_keyword and spec.detect_by_base_keyword in p.api_base:
                return p, spec.name
            if local_fallback is None:
                local_fallback = (p, spec.name)
        if local_fallback:
            return local_fallback

        # 回退：网关优先，然后是其他（按注册表顺序）
        # Fallback: gateways first, then others (follows registry order)
        # OAuth providers are NOT valid fallbacks — they require explicit model selection
        # OAuth providers 不是有效的回退——它们需要明确的模型选择
        for spec in PROVIDERS:
            if spec.is_oauth:
                continue
            p = getattr(self.providers, spec.name, None)
            if p and p.api_key:
                return p, spec.name
        return None, None

    def get_provider(self, model: str | None = None) -> ProviderConfig | None:
        """
        Get matched provider config (api_key, api_base, extra_headers). Falls back to first available.
        获取匹配的 provider 配置。回退到第一个可用的。
        """
        p, _ = self._match_provider(model)
        return p

    def get_provider_name(self, model: str | None = None) -> str | None:
        """
        Get the registry name of the matched provider (e.g. "deepseek", "openrouter").
        获取匹配的 provider 的注册名称。
        """
        _, name = self._match_provider(model)
        return name

    def get_api_key(self, model: str | None = None) -> str | None:
        """
        Get API key for the given model. Falls back to first available.
        获取给定模型的 API key。回退到第一个可用的。
        """
        p = self.get_provider(model)
        return p.api_key if p else None

    def get_api_base(self, model: str | None = None) -> str | None:
        """
        Get API base URL for the given model, falling back to the provider default when present.
        获取给定模型的 API 基础 URL，优先使用 provider 配置的 api_base，否则使用 provider 默认值。
        """
        from nanobot.providers.registry import find_by_name

        p, name = self._match_provider(model)
        if p and p.api_base:
            return p.api_base
        if name:
            spec = find_by_name(name)
            if spec and spec.default_api_base:
                return spec.default_api_base
        return None

    model_config = ConfigDict(env_prefix="NANOBOT_", env_nested_delimiter="__")
