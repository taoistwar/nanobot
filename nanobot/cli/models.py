"""Model information helpers for the onboard wizard.
模型信息辅助函数，用于 onboard 向导。

Model database / autocomplete is temporarily disabled while litellm is
being replaced.  All public function signatures are preserved so callers
continue to work without changes.
模型数据库/自动补全功能在 litellm 替换期间暂时禁用。所有公共函数签名已保留，以便调用者继续正常工作。
"""

from __future__ import annotations

from typing import Any


def get_all_models() -> list[str]:
    """获取所有可用模型列表。
    当前返回空列表，模型数据库已禁用。"""
    return []


def find_model_info(model_name: str) -> dict[str, Any] | None:
    """查找模型信息。
    当前返回 None，模型数据库已禁用。"""
    return None


def get_model_context_limit(model: str, provider: str = "auto") -> int | None:
    """获取模型的上下文窗口限制。
    当前返回 None，模型数据库已禁用。"""
    return None


def get_model_suggestions(partial: str, provider: str = "auto", limit: int = 20) -> list[str]:
    """获取模型建议列表。
    当前返回空列表，模型数据库已禁用。"""
    return []


def format_token_count(tokens: int) -> str:
    """Format token count for display (e.g., 200000 -> '200,000').
    格式化 token 数量用于显示（如 200000 -> '200,000'）。"""
    return f"{tokens:,}"
