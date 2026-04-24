"""Track file-read state for read-before-edit warnings and read deduplication.
// 跟踪文件读取状态，用于读取前编辑警告和读取去重。
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ReadState:
    """文件读取状态的记录。
    // Record of file read state."""
    mtime: float
    offset: int
    limit: int | None
    content_hash: str | None
    can_dedup: bool


_state: dict[str, ReadState] = {}


def _hash_file(p: str) -> str | None:
    """计算文件的 SHA256 哈希值。
    // Compute SHA256 hash of a file."""
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except OSError:
        return None


def record_read(path: str | Path, offset: int = 1, limit: int | None = None) -> None:
    """Record that a file was read (called after successful read).
    // 记录文件已被读取（在成功读取后调用）。"""
    p = str(Path(path).resolve())
    try:
        mtime = os.path.getmtime(p)
    except OSError:
        return
    _state[p] = ReadState(
        mtime=mtime,
        offset=offset,
        limit=limit,
        content_hash=_hash_file(p),
        can_dedup=True,
    )


def record_write(path: str | Path) -> None:
    """Record that a file was written (updates mtime in state).
    // 记录文件已被写入（更新状态中的 mtime）。"""
    p = str(Path(path).resolve())
    try:
        mtime = os.path.getmtime(p)
    except OSError:
        _state.pop(p, None)
        return
    _state[p] = ReadState(
        mtime=mtime,
        offset=1,
        limit=None,
        content_hash=_hash_file(p),
        can_dedup=False,
    )


def check_read(path: str | Path) -> str | None:
    """Check if a file has been read and is fresh.
    // 检查文件是否已被读取且是新鲜的。

    Returns None if OK, or a warning string.
    // 如果 OK 返回 None，否则返回警告字符串。
    When mtime changed but file content is identical (e.g. touch, editor save),
    the check passes to avoid false-positive staleness warnings.
    // 当 mtime 改变但文件内容相同时（例如 touch、编辑器保存），检查通过以避免误报。
    """
    p = str(Path(path).resolve())
    entry = _state.get(p)
    if entry is None:
        return "Warning: file has not been read yet. Read it first to verify content before editing."
    try:
        current_mtime = os.path.getmtime(p)
    except OSError:
        return None
    if current_mtime != entry.mtime:
        if entry.content_hash and _hash_file(p) == entry.content_hash:
            entry.mtime = current_mtime
            return None
        return "Warning: file has been modified since last read. Re-read to verify content before editing."
    # mtime unchanged - still check content hash to detect quick modifications
    # mtime 未改变——仍然检查内容哈希以检测快速修改
    if entry.content_hash and _hash_file(p) != entry.content_hash:
        return "Warning: file has been modified since last read. Re-read to verify content before editing."
    return None


def is_unchanged(path: str | Path, offset: int = 1, limit: int | None = None) -> bool:
    """Return True if file was previously read with same params and content is unchanged.
    // 如果文件之前以相同参数读取且内容未改变，返回 True。"""
    p = str(Path(path).resolve())
    entry = _state.get(p)
    if entry is None:
        return False
    if not entry.can_dedup:
        return False
    if entry.offset != offset or entry.limit != limit:
        return False
    try:
        current_mtime = os.path.getmtime(p)
    except OSError:
        return False
    if current_mtime != entry.mtime:
        # mtime changed - check if content also changed
        # mtime 改变——检查内容是否也改变了
        current_hash = _hash_file(p)
        if current_hash != entry.content_hash:
            # Content actually changed - don't dedup
            # 内容实际改变了——不去重
            entry.can_dedup = False
            return False
        # Content identical despite mtime change (e.g. touch) - mark as not dedupable to force full read next time
        # 内容相同但 mtime 改变了（例如 touch）——标记为不可去重以强制下次完全读取
        entry.can_dedup = False
        return True
    # mtime unchanged - content must be identical
    # mtime 未改变——内容必定相同
    return True


def clear() -> None:
    """Clear all tracked state (useful for testing).
    // 清除所有跟踪状态（用于测试）。"""
    _state.clear()
