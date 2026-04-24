"""
nanobot - A lightweight AI agent framework
nanobot - 轻量级 AI Agent 框架
"""

from importlib.metadata import PackageNotFoundError, version as _pkg_version
from pathlib import Path
import tomllib


def _read_pyproject_version() -> str | None:
    """
    Read the source-tree version when package metadata is unavailable.
    当包元数据不可用时，从源码树读取版本号。
    """
    # 定位 pyproject.toml 文件
    # Locate the pyproject.toml file
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    if not pyproject.exists():
        return None
    # 解析 TOML 格式的配置文件获取版本号
    # Parse the TOML configuration file to extract version
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return data.get("project", {}).get("version")


def _resolve_version() -> str:
    """
    Resolve the installed package version or fallback to source version.
    解析已安装包的版本，或回退到源码版本。
    """
    try:
        # 尝试从已安装的包中获取版本
        # Try to get version from installed package
        return _pkg_version("nanobot-ai")
    except PackageNotFoundError:
        # Source checkouts often import nanobot without installed dist-info.
        # 源码检出通常没有安装 dist-info，尝试从 pyproject.toml 读取
        return _read_pyproject_version() or "0.1.5.post2"


__version__ = _resolve_version()
__logo__ = "🐈"

from nanobot.nanobot import Nanobot, RunResult

__all__ = ["Nanobot", "RunResult"]
