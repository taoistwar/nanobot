"""用于将 ``data:...;base64,...`` URL 解码到磁盘的共享辅助工具。

最初位于 ``nanobot.api.server``；现在被 WebSocket 频道共享，
使 ``api`` + ``websocket`` 入口路径使用相同的解析、大小限制和文件系统布局。
"""

from __future__ import annotations

import base64
import mimetypes
import re
import uuid
from pathlib import Path

from nanobot.utils.helpers import safe_filename

DEFAULT_MAX_BYTES = 10 * 1024 * 1024
MAX_FILE_SIZE = DEFAULT_MAX_BYTES

_DATA_URL_RE = re.compile(r"^data:([^;]+);base64,(.+)$", re.DOTALL)


class FileSizeExceeded(Exception):
    """当解码后的数据超过调用者指定的大小限制时抛出。"""


def save_base64_data_url(
    data_url: str,
    media_dir: Path,
    *,
    max_bytes: int | None = None,
) -> str | None:
    """解码 ``data:<mime>;base64,<payload>`` URL 并持久化到磁盘。

    成功时返回绝对路径，URL 格式或 base64 数据格式错误时返回 ``None``。
    当解码后的数据大于 ``max_bytes``（默认 10 MB）时抛出 :class:`FileSizeExceeded`。
    """
    m = _DATA_URL_RE.match(data_url)
    if not m:
        return None
    mime_type, b64_payload = m.group(1), m.group(2)
    try:
        raw = base64.b64decode(b64_payload)
    except Exception:
        return None
    limit = DEFAULT_MAX_BYTES if max_bytes is None else max_bytes
    if len(raw) > limit:
        raise FileSizeExceeded(f"File exceeds {limit // (1024 * 1024)}MB limit")
    ext = mimetypes.guess_extension(mime_type) or ".bin"
    filename = f"{uuid.uuid4().hex[:12]}{ext}"
    dest = media_dir / safe_filename(filename)
    dest.write_bytes(raw)
    return str(dest)
