"""用于显示的路径缩写工具模块。"""

from __future__ import annotations

import os
import re
from urllib.parse import urlparse


def abbreviate_path(path: str, max_len: int = 40) -> str:
    """缩短文件路径或 URL，保留基名和关键目录。

    策略：
    1. 如果足够短则原样返回
    2. 将主目录替换为 ~/
    3. 从右向左，保留基名和父目录直到预算耗尽
    4. 前面加上 …/
    """
    if not path:
        return path

    # Handle URLs: preserve scheme://domain + filename
    if re.match(r"https?://", path):
        return _abbreviate_url(path, max_len)

    # Normalize separators to /
    normalized = path.replace("\\", "/")

    # Replace home directory
    home = os.path.expanduser("~").replace("\\", "/")
    if normalized.startswith(home + "/"):
        normalized = "~" + normalized[len(home):]
    elif normalized == home:
        normalized = "~"

    # Return early only after normalization and home replacement
    if len(normalized) <= max_len:
        return normalized

    # Split into segments
    parts = normalized.rstrip("/").split("/")
    if len(parts) <= 1:
        return normalized[:max_len - 1] + "\u2026"

    # Always keep the basename
    basename = parts[-1]
    # Budget: max_len minus "…/" prefix (2 chars) minus "/" separator minus basename
    budget = max_len - len(basename) - 3  # -3 for "…/" + final "/"

    # Walk backwards from parent, collecting segments
    kept: list[str] = []
    for seg in reversed(parts[:-1]):
        needed = len(seg) + 1  # segment + "/"
        if not kept and needed <= budget:
            kept.append(seg)
            budget -= needed
        elif kept:
            needed_with_sep = len(seg) + 1
            if needed_with_sep <= budget:
                kept.append(seg)
                budget -= needed_with_sep
            else:
                break
        else:
            break

    kept.reverse()
    if kept:
        return "\u2026/" + "/".join(kept) + "/" + basename
    return "\u2026/" + basename


def _abbreviate_url(url: str, max_len: int = 40) -> str:
    """缩短 URL，保留域名和文件名。"""
    if len(url) <= max_len:
        return url

    parsed = urlparse(url)
    domain = parsed.netloc  # e.g. "example.com"
    path_part = parsed.path  # e.g. "/api/v2/resource.json"

    # Extract filename from path
    segments = path_part.rstrip("/").split("/")
    basename = segments[-1] if segments else ""

    if not basename:
        # No filename, truncate URL
        return url[: max_len - 1] + "\u2026"

    budget = max_len - len(domain) - len(basename) - 4  # "…/" + "/"
    if budget < 0:
        trunc = max_len - len(domain) - 5  # "…/" + "/"
        return domain + "/\u2026/" + (basename[:trunc] if trunc > 0 else "")

    # Build abbreviated path
    kept: list[str] = []
    for seg in reversed(segments[:-1]):
        if len(seg) + 1 <= budget:
            kept.append(seg)
            budget -= len(seg) + 1
        else:
            break

    kept.reverse()
    if kept:
        return domain + "/\u2026/" + "/".join(kept) + "/" + basename
    return domain + "/\u2026/" + basename
