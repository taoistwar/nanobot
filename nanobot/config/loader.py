"""
Configuration loading utilities.
配置加载工具模块。
"""

import json
import os
import re
from pathlib import Path
from typing import Any

import pydantic
from loguru import logger
from pydantic import BaseModel

from nanobot.config.schema import Config

# Global variable to store current config path (for multi-instance support)
# 全局变量，用于存储当前配置路径（支持多实例）
_current_config_path: Path | None = None


def set_config_path(path: Path) -> None:
    """
    Set the current config path (used to derive data directory).
    设置当前配置路径（用于派生数据目录）。
    """
    global _current_config_path
    _current_config_path = path


def get_config_path() -> Path:
    """
    Get the configuration file path.
    获取配置文件路径。
    """
    if _current_config_path:
        return _current_config_path
    return Path.home() / ".nanobot" / "config.json"


def load_config(config_path: Path | None = None) -> Config:
    """
    Load configuration from file or create default.
    从文件加载配置或创建默认配置。

    Args:
        config_path: Optional path to config file. Uses default if not provided.
                     可选的配置文件路径，如未提供则使用默认路径。

    Returns:
        Loaded configuration object.
        已加载的配置对象。
    """
    path = config_path or get_config_path()

    config = Config()
    # 如果配置文件存在，尝试加载并验证
    # Try to load and validate if config file exists
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            # 执行配置迁移以兼容旧格式
            # Migrate config to support old formats
            data = _migrate_config(data)
            config = Config.model_validate(data)
        except (json.JSONDecodeError, ValueError, pydantic.ValidationError) as e:
            logger.warning(f"Failed to load config from {path}: {e}")
            logger.warning("Using default configuration.")

    # 应用 SSRF 白名单到网络安全模块
    # Apply SSRF whitelist to network security module
    _apply_ssrf_whitelist(config)
    return config


def _apply_ssrf_whitelist(config: Config) -> None:
    """
    Apply SSRF whitelist from config to the network security module.
    将配置中的 SSRF 白名单应用到网络安全模块。
    """
    from nanobot.security.network import configure_ssrf_whitelist

    configure_ssrf_whitelist(config.tools.ssrf_whitelist)


def save_config(config: Config, config_path: Path | None = None) -> None:
    """
    Save configuration to file.
    将配置保存到文件。

    Args:
        config: Configuration to save.
                要保存的配置。
        config_path: Optional path to save to. Uses default if not provided.
                     可选的保存路径，如未提供则使用默认路径。
    """
    path = config_path or get_config_path()
    # 确保父目录存在
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    data = config.model_dump(mode="json", by_alias=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# 正则表达式模式，用于匹配 ${VAR} 格式的环境变量引用
# Regex pattern to match ${VAR} format environment variable references
_ENV_REF_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def resolve_config_env_vars(config: Config) -> Config:
    """
    Return *config* with ``${VAR}`` env-var references resolved.
    返回已解析 ``${VAR}`` 环境变量引用的 *config*。

    Walks in place so fields declared with ``exclude=True`` (e.g.
    ``DreamConfig.cron``) survive; returns the same instance when no
    references are present. Raises ``ValueError`` if a referenced
    variable is not set.
    就地遍历，因此使用 ``exclude=True`` 声明的字段（如 ``DreamConfig.cron``）会保留；
    如果没有引用则返回相同实例。如果引用的变量未设置，则引发 ``ValueError``。
    """
    return _resolve_in_place(config)


def _resolve_in_place(obj: Any) -> Any:
    """
    Recursively resolve environment variable references in place.
    原地递归解析环境变量引用。
    """
    # 处理字符串类型，替换 ${VAR} 为对应的环境变量值
    # Handle string type, replace ${VAR} with corresponding environment variable value
    if isinstance(obj, str):
        new = _ENV_REF_PATTERN.sub(_env_replace, obj)
        return new if new != obj else obj
    # 处理 Pydantic BaseModel 类型
    # Handle Pydantic BaseModel type
    if isinstance(obj, BaseModel):
        updates: dict[str, Any] = {}
        for name in type(obj).model_fields:
            old = getattr(obj, name)
            new = _resolve_in_place(old)
            if new is not old:
                updates[name] = new
        # 处理 extra 字段
        # Handle extra fields
        extras = obj.__pydantic_extra__
        new_extras: dict[str, Any] | None = None
        if extras:
            resolved = {k: _resolve_in_place(v) for k, v in extras.items()}
            if any(resolved[k] is not extras[k] for k in extras):
                new_extras = resolved
        if not updates and new_extras is None:
            return obj
        copy = obj.model_copy(update=updates) if updates else obj.model_copy()
        if new_extras is not None:
            copy.__pydantic_extra__ = new_extras
        return copy
    # 处理字典类型
    # Handle dict type
    if isinstance(obj, dict):
        resolved = {k: _resolve_in_place(v) for k, v in obj.items()}
        return resolved if any(resolved[k] is not obj[k] for k in obj) else obj
    # 处理列表类型
    # Handle list type
    if isinstance(obj, list):
        resolved = [_resolve_in_place(v) for v in obj]
        return resolved if any(nv is not ov for nv, ov in zip(resolved, obj)) else obj
    return obj


def _resolve_env_vars(obj: object) -> object:
    """
    Recursively resolve ``${VAR}`` patterns in plain strings/dicts/lists.
    在普通字符串/字典/列表中递归解析 ``${VAR}`` 模式。
    """
    if isinstance(obj, str):
        return _ENV_REF_PATTERN.sub(_env_replace, obj)
    if isinstance(obj, dict):
        return {k: _resolve_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_env_vars(v) for v in obj]
    return obj


def _env_replace(match: re.Match[str]) -> str:
    """
    Replace a single env-var match with its value.
    将单个环境变量匹配替换为其值。
    """
    name = match.group(1)
    value = os.environ.get(name)
    if value is None:
        raise ValueError(
            f"Environment variable '{name}' referenced in config is not set"
        )
    return value


def _migrate_config(data: dict) -> dict:
    """
    Migrate old config formats to current.
    将旧版配置格式迁移到当前版本。
    """
    # 将 tools.exec.restrictToWorkspace 迁移到 tools.restrictToWorkspace
    # Move tools.exec.restrictToWorkspace → tools.restrictToWorkspace
    tools = data.get("tools", {})
    exec_cfg = tools.get("exec", {})
    if "restrictToWorkspace" in exec_cfg and "restrictToWorkspace" not in tools:
        tools["restrictToWorkspace"] = exec_cfg.pop("restrictToWorkspace")

    # 将 tools.myEnabled / tools.mySet 迁移到 tools.my.{enable, allowSet}
    # Move tools.myEnabled / tools.mySet → tools.my.{enable, allowSet}
    # 旧版平铺键在 MyTool 初始版本中使用；将其包装到子配置中
    # 可以保持 `web` / `exec` / `my` 的对称性并留出扩展空间
    if "myEnabled" in tools or "mySet" in tools:
        my_cfg = tools.setdefault("my", {})
        if "myEnabled" in tools and "enable" not in my_cfg:
            my_cfg["enable"] = tools.pop("myEnabled")
        else:
            tools.pop("myEnabled", None)
        if "mySet" in tools and "allowSet" not in my_cfg:
            my_cfg["allowSet"] = tools.pop("mySet")
        else:
            tools.pop("mySet", None)

    return data
