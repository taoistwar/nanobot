"""
Runtime path helpers derived from the active config context.
从当前配置上下文派生的运行时路径辅助函数。
"""

from __future__ import annotations

from pathlib import Path

from nanobot.config.loader import get_config_path
from nanobot.utils.helpers import ensure_dir


def get_data_dir() -> Path:
    """
    Return the instance-level runtime data directory.
    返回实例级别的运行时数据目录。
    """
    return ensure_dir(get_config_path().parent)


def get_runtime_subdir(name: str) -> Path:
    """
    Return a named runtime subdirectory under the instance data dir.
    返回实例数据目录下指定的运行时子目录。
    """
    return ensure_dir(get_data_dir() / name)


def get_media_dir(channel: str | None = None) -> Path:
    """
    Return the media directory, optionally namespaced per channel.
    返回媒体目录，可选择按渠道命名空间隔离。

    Args:
        channel: Optional channel name for per-channel media directories.
                 可选的渠道名称，用于渠道隔离的媒体目录。
    """
    base = get_runtime_subdir("media")
    return ensure_dir(base / channel) if channel else base


def get_cron_dir() -> Path:
    """
    Return the cron storage directory.
    返回定时任务存储目录。
    """
    return get_runtime_subdir("cron")


def get_logs_dir() -> Path:
    """
    Return the logs directory.
    返回日志目录。
    """
    return get_runtime_subdir("logs")


def get_workspace_path(workspace: str | None = None) -> Path:
    """
    Resolve and ensure the agent workspace path.
    解析并确保 agent 工作区路径存在。
    """
    # 如果未指定 workspace，默认使用 ~/.nanobot/workspace
    # Use default ~/.nanobot/workspace if not specified
    path = Path(workspace).expanduser() if workspace else Path.home() / ".nanobot" / "workspace"
    return ensure_dir(path)


def is_default_workspace(workspace: str | Path | None) -> bool:
    """
    Return whether a workspace resolves to nanobot's default workspace path.
    判断 workspace 是否解析为 nanobot 的默认工作区路径。
    """
    current = Path(workspace).expanduser() if workspace is not None else Path.home() / ".nanobot" / "workspace"
    default = Path.home() / ".nanobot" / "workspace"
    return current.resolve(strict=False) == default.resolve(strict=False)


def get_cli_history_path() -> Path:
    """
    Return the shared CLI history file path.
    返回共享的 CLI 历史文件路径。
    """
    return Path.home() / ".nanobot" / "history" / "cli_history"


def get_bridge_install_dir() -> Path:
    """
    Return the shared WhatsApp bridge installation directory.
    返回共享的 WhatsApp bridge 安装目录。
    """
    return Path.home() / ".nanobot" / "bridge"


def get_legacy_sessions_dir() -> Path:
    """
    Return the legacy global session directory used for migration fallback.
    返回用于迁移回退的旧版全局会话目录。
    """
    return Path.home() / ".nanobot" / "sessions"
