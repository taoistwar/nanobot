"""Track file-read state for read-before-edit warnings and read deduplication.

跟踪文件读取状态，用于编辑前读取警告和读取去重。

This module provides utilities to track when files have been read and written,
allowing the agent to warn about potentially stale file content and deduplicate
redundant read operations.

本模块提供实用工具来跟踪文件何时被读取和写入，
允许代理警告可能过时的文件内容并去重冗余的读取操作。
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ReadState:
    """File read state.
    
    文件读取状态。
    
    Attributes:
        mtime: File modification time / 文件修改时间
        offset: Read offset / 读取偏移量
        limit: Read limit / 读取限制
        content_hash: Content hash / 内容哈希
        can_dedup: Whether can deduplicate / 是否可去重
    """
    mtime: float
    offset: int
    limit: int | None
    content_hash: str | None
    can_dedup: bool


_state: dict[str, ReadState] = {}
"""Global state tracking / 全局状态跟踪"""


def _hash_file(p: str) -> str | None:
    """Calculate SHA256 hash of a file.
    
    计算文件的 SHA256 哈希。
    
    Args:
        p: File path / 文件路径
        
    Returns:
        SHA256 hash or None on error / SHA256 哈希或出错时返回 None
    """
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except OSError:
        return None


def record_read(path: str | Path, offset: int = 1, limit: int | None = None) -> None:
    """Record that a file was read (called after successful read).
    
    记录文件已被读取（在成功读取后调用）。
    
    Args:
        path: File path / 文件路径
        offset: Read offset / 读取偏移量
        limit: Read limit / 读取限制
    """
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
    
    记录文件已被写入（更新状态中的 mtime）。
    
    Args:
        path: File path / 文件路径
    """
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

    Returns None if OK, or a warning string.
    When mtime changed but file content is identical (e.g. touch, editor save),
    the check passes to avoid false-positive staleness warnings.
    
    检查文件是否已读取且是新鲜的。
    
    如果正常则返回 None，否则返回警告字符串。
    当 mtime 改变但文件内容相同时（例如 touch、编辑器保存），
    检查会通过以避免误报的过时警告。
    
    Args:
        path: File path / 文件路径
        
    Returns:
        None if OK, warning string otherwise / 如果正常则为 None，否则为警告字符串
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
    # mtime 未变 - 仍然检查内容哈希以检测快速修改
    if entry.content_hash and _hash_file(p) != entry.content_hash:
        return "Warning: file has been modified since last read. Re-read to verify content before editing."
    return None


def is_unchanged(path: str | Path, offset: int = 1, limit: int | None = None) -> bool:
    """Return True if file was previously read with same params and content is unchanged.
    
    如果文件之前使用相同参数读取且内容未改变则返回 True。
    
    Args:
        path: File path / 文件路径
        offset: Read offset / 读取偏移量
        limit: Read limit / 读取限制
        
    Returns:
        True if unchanged / 如果未改变则返回 True
    """
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
        # mtime 改变 - 检查内容是否也改变了
        current_hash = _hash_file(p)
        if current_hash != entry.content_hash:
            # Content actually changed - don't dedup
            # 内容实际改变了 - 不去重
            entry.can_dedup = False
            return False
        # Content identical despite mtime change (e.g. touch) - mark as not dedupable to force full read next time
        # 尽管 mtime 改变但内容相同（例如 touch）- 标记为不可去重以强制下次完全读取
        entry.can_dedup = False
        return True
    # mtime unchanged - content must be identical
    # mtime 未变 - 内容必须相同
    return True


def clear() -> None:
    """Clear all tracked state (useful for testing).
    
    清除所有跟踪的状态（对测试有用）。
    """
    _state.clear()
