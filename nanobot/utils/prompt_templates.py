"""加载和渲染 nanobot/templates/ 下的代理系统提示模板（Jinja2）。

代理提示位于 ``templates/agent/``（传入名称如 ``agent/identity.md``）。
共享片段位于 ``agent/_snippets/``，通过
``{% include 'agent/_snippets/....md' %}`` 引用。
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

_TEMPLATES_ROOT = Path(__file__).resolve().parent.parent / "templates"


@lru_cache
def _environment() -> Environment:
    # 纯文本提示：不 HTML 转义变量值
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_ROOT)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_template(name: str, *, strip: bool = False, **kwargs: Any) -> str:
    """渲染 ``templates/`` 下名为 ``name`` 的模板（如 ``agent/identity.md``）。

    当文件以不需要保留的尾随换行符结尾时，对单行用户面向字符串使用 ``strip=True``。
    """
    text = _environment().get_template(name).render(**kwargs)
    return text.rstrip() if strip else text
