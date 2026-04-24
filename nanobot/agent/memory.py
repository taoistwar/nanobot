"""Memory system: pure file I/O store, lightweight Consolidator, and Dream processor.

记忆系统：纯文件 I/O 存储、轻量级 Consolidator 和 Dream 处理器。

This module provides three key components:
1. MemoryStore: Pure file I/O for memory files (MEMORY.md, history.jsonl, etc.)
2. Consolidator: Token-budget triggered consolidation of session history
3. Dream: Cron-scheduled memory analysis and processing

该模块提供三个关键组件：
1. MemoryStore: 记忆文件（MEMORY.md、history.jsonl 等）的纯文件 I/O
2. Consolidator: 基于 token 预算触发的会话历史整合
3. Dream: 定时记忆分析和处理
"""

from __future__ import annotations

import asyncio
import json
import re
import weakref
import tiktoken
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterator

from loguru import logger

from nanobot.utils.prompt_templates import render_template
from nanobot.utils.helpers import ensure_dir, estimate_message_tokens, estimate_prompt_tokens_chain, strip_think, truncate_text

from nanobot.agent.runner import AgentRunSpec, AgentRunner
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.utils.gitstore import GitStore

if TYPE_CHECKING:
    from nanobot.providers.base import LLMProvider
    from nanobot.session.manager import Session, SessionManager


# ---------------------------------------------------------------------------
# MemoryStore — pure file I/O layer
# ---------------------------------------------------------------------------

class MemoryStore:
    """Pure file I/O for memory files: MEMORY.md, history.jsonl, SOUL.md, USER.md.
    
    记忆文件的纯文件 I/O：MEMORY.md、history.jsonl、SOUL.md、USER.md。
    
    This class handles all file operations for the memory system:
    - Reading/writing MEMORY.md (long-term facts)
    - Managing history.jsonl (append-only conversation history)
    - Processing SOUL.md (agent identity) and USER.md (user preferences)
    - Cursor tracking for incremental processing
    - Git integration for version control
    
    该类处理记忆系统的所有文件操作：
    - 读取/写入 MEMORY.md（长期事实）
    - 管理 history.jsonl（仅追加的对话历史）
    - 处理 SOUL.md（代理身份）和 USER.md（用户偏好）
    - 增量处理的游标跟踪
    - Git 集成的版本控制
    """

    _DEFAULT_MAX_HISTORY = 1000  # Default max history entries / 默认最大历史条目数
    _LEGACY_ENTRY_START_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2}[^\]]*)\]\s*")  # Regex for legacy entry start / 旧版条目开始的正则表达式
    _LEGACY_TIMESTAMP_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]\s*")  # Regex for legacy timestamp / 旧版时间戳的正则表达式
    _LEGACY_RAW_MESSAGE_RE = re.compile(
        r"^\[\d{4}-\d{2}-\d{2}[^\]]*\]\s+[A-Z][A-Z0-9_]*(?:\s+\[tools:\s*[^\]]+\])?:"
    )  # Regex for raw legacy messages / 旧版原始消息的正则表达式

    def __init__(self, workspace: Path, max_history_entries: int = _DEFAULT_MAX_HISTORY):
        """Initialize the memory store.
        
        初始化记忆存储。
        
        Args:
            workspace: Workspace directory path / 工作区目录路径
            max_history_entries: Maximum history entries to retain / 保留的最大历史条目数
        """
        self.workspace = workspace  # Workspace directory / 工作区目录
        self.max_history_entries = max_history_entries  # Max history entries to retain / 保留的最大历史条目数
        self.memory_dir = ensure_dir(workspace / "memory")  # Memory directory (created if not exists) / 记忆目录（不存在则创建）
        self.memory_file = self.memory_dir / "MEMORY.md"  # Long-term memory file / 长期记忆文件
        self.history_file = self.memory_dir / "history.jsonl"  # Append-only conversation history / 仅追加的对话历史
        self.legacy_history_file = self.memory_dir / "HISTORY.md"  # Legacy history file (for migration) / 旧版历史文件（用于迁移）
        self.soul_file = workspace / "SOUL.md"  # Agent identity file / 代理身份文件
        self.user_file = workspace / "USER.md"  # User preferences file / 用户偏好文件
        self._cursor_file = self.memory_dir / ".cursor"  # History cursor for incremental reading / 增量读取的历史游标
        self._dream_cursor_file = self.memory_dir / ".dream_cursor"  # Dream processing cursor / Dream 处理游标
        self._corruption_logged = False  # Rate-limit corruption warning / 限制损坏警告频率
        self._oversize_logged = False  # Rate-limit oversize entry warning / 限制超大条目警告频率
        self._git = GitStore(workspace, tracked_files=[
            "SOUL.md", "USER.md", "memory/MEMORY.md",
        ])  # Git integration for version control / Git 版本控制集成
        self._maybe_migrate_legacy_history()

    @property
    def git(self) -> GitStore:
        """Get the GitStore instance for version control.
        
        获取用于版本控制的 GitStore 实例。
        
        Returns:
            GitStore instance / GitStore 实例
        """
        return self._git

    # -- generic helpers -----------------------------------------------------
    # -- 通用辅助方法 --------------------------------------------------------

    @staticmethod
    def read_file(path: Path) -> str:
        """Read a file and return its content.
        
        读取文件并返回其内容。
        
        Args:
            path: File path to read / 要读取的文件路径
            
        Returns:
            File content as string, or empty string if file not found / 文件内容字符串，如果文件不存在则返回空字符串
        """
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    def _maybe_migrate_legacy_history(self) -> None:
        """One-time upgrade from legacy HISTORY.md to history.jsonl.
        
        从旧版 HISTORY.md 一次性升级到 history.jsonl。

        The migration is best-effort and prioritizes preserving as much content
        as possible over perfect parsing.
        
        迁移采用尽力而为的方式，优先考虑保留尽可能多的内容，而不是完美解析。
        """
        if not self.legacy_history_file.exists():
            return
        if self.history_file.exists() and self.history_file.stat().st_size > 0:
            return

        try:
            legacy_text = self.legacy_history_file.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError:
            logger.exception("Failed to read legacy HISTORY.md for migration")
            return

        entries = self._parse_legacy_history(legacy_text)
        try:
            if entries:
                self._write_entries(entries)
                last_cursor = entries[-1]["cursor"]
                self._cursor_file.write_text(str(last_cursor), encoding="utf-8")
                # Default to "already processed" so upgrades do not replay the
                # user's entire historical archive into Dream on first start.
                self._dream_cursor_file.write_text(str(last_cursor), encoding="utf-8")

            backup_path = self._next_legacy_backup_path()
            self.legacy_history_file.replace(backup_path)
            logger.info(
                "Migrated legacy HISTORY.md to history.jsonl ({} entries)",
                len(entries),
            )
        except Exception:
            logger.exception("Failed to migrate legacy HISTORY.md")

    def _parse_legacy_history(self, text: str) -> list[dict[str, Any]]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized:
            return []

        fallback_timestamp = self._legacy_fallback_timestamp()
        entries: list[dict[str, Any]] = []
        chunks = self._split_legacy_history_chunks(normalized)

        for cursor, chunk in enumerate(chunks, start=1):
            timestamp = fallback_timestamp
            content = chunk
            match = self._LEGACY_TIMESTAMP_RE.match(chunk)
            if match:
                timestamp = match.group(1)
                remainder = chunk[match.end():].lstrip()
                if remainder:
                    content = remainder

            entries.append({
                "cursor": cursor,
                "timestamp": timestamp,
                "content": content,
            })
        return entries

    def _split_legacy_history_chunks(self, text: str) -> list[str]:
        lines = text.split("\n")
    def _parse_legacy_chunks(self, lines: list[str]) -> list[str]:
        """Parse legacy HISTORY.md format into chunks.
        
        将旧版 HISTORY.md 格式解析为块。
        
        Args:
            lines: Lines from legacy history file / 旧版历史文件的行
            
        Returns:
            List of parsed chunks / 解析后的块列表
        """
        chunks: list[str] = []
        current: list[str] = []
        saw_blank_separator = False

        for line in lines:
            if saw_blank_separator and line.strip() and current:
                chunks.append("\n".join(current).strip())
                current = [line]
                saw_blank_separator = False
                continue
            if self._should_start_new_legacy_chunk(line, current):
                chunks.append("\n".join(current).strip())
                current = [line]
                saw_blank_separator = False
                continue
            current.append(line)
            saw_blank_separator = not line.strip()

        if current:
            chunks.append("\n".join(current).strip())
        return [chunk for chunk in chunks if chunk]

    def _should_start_new_legacy_chunk(self, line: str, current: list[str]) -> bool:
        """Check if line should start a new chunk in legacy format.
        
        检查行是否应该在旧版格式中开始新块。
        
        Args:
            line: Current line / 当前行
            current: Current chunk lines / 当前块行
            
        Returns:
            True if new chunk should start / 如果应开始新块则返回 True
        """
        if not current:
            return False
        if not self._LEGACY_ENTRY_START_RE.match(line):
            return False
        if self._is_raw_legacy_chunk(current) and self._LEGACY_RAW_MESSAGE_RE.match(line):
            return False
        return True

    def _is_raw_legacy_chunk(self, lines: list[str]) -> bool:
        """Check if chunk is a raw legacy message.
        
        检查块是否为旧版原始消息。
        
        Args:
            lines: Chunk lines / 块的行
            
        Returns:
            True if raw legacy chunk / 如果是旧版原始块则返回 True
        """
        first_nonempty = next((line for line in lines if line.strip()), "")
        match = self._LEGACY_TIMESTAMP_RE.match(first_nonempty)
        if not match:
            return False
        return first_nonempty[match.end():].lstrip().startswith("[RAW]")

    def _legacy_fallback_timestamp(self) -> str:
        """Get fallback timestamp from legacy history file mtime.
        
        从旧版历史文件修改时间获取回退时间戳。
        
        Returns:
            Fallback timestamp string / 回退时间戳字符串
        """
        try:
            return datetime.fromtimestamp(
                self.legacy_history_file.stat().st_mtime,
            ).strftime("%Y-%m-%d %H:%M")
        except OSError:
            return datetime.now().strftime("%Y-%m-%d %H:%M")

    def _next_legacy_backup_path(self) -> Path:
        """Find next available backup path for legacy history file.
        
        为旧版历史文件查找下一个可用的备份路径。
        
        Returns:
            Next backup file path / 下一个备份文件路径
        """
        candidate = self.memory_dir / "HISTORY.md.bak"
        suffix = 2
        while candidate.exists():
            candidate = self.memory_dir / f"HISTORY.md.bak.{suffix}"
            suffix += 1
        return candidate

    # -- MEMORY.md (long-term facts) -----------------------------------------
    # -- MEMORY.md（长期事实） ------------------------------------------------

    def read_memory(self) -> str:
        """Read the MEMORY.md file content.
        
        读取 MEMORY.md 文件内容。
        
        Returns:
            Memory file content / 记忆文件内容
        """
        return self.read_file(self.memory_file)

    def write_memory(self, content: str) -> None:
        """Write content to MEMORY.md file.
        
        将内容写入 MEMORY.md 文件。
        
        Args:
            content: Content to write / 要写入的内容
        """
        self.memory_file.write_text(content, encoding="utf-8")

    # -- SOUL.md -------------------------------------------------------------
    # -- SOUL.md（代理身份） --------------------------------------------------

    def read_soul(self) -> str:
        """Read the SOUL.md file (agent identity).
        
        读取 SOUL.md 文件（代理身份）。
        
        Returns:
            Soul file content / 身份文件内容
        """
        return self.read_file(self.soul_file)

    def write_soul(self, content: str) -> None:
        """Write content to SOUL.md file.
        
        将内容写入 SOUL.md 文件。
        
        Args:
            content: Content to write / 要写入的内容
        """
        self.soul_file.write_text(content, encoding="utf-8")

    # -- USER.md -------------------------------------------------------------
    # -- USER.md（用户偏好） --------------------------------------------------

    def read_user(self) -> str:
        """Read the USER.md file (user preferences).
        
        读取 USER.md 文件（用户偏好）。
        
        Returns:
            User file content / 用户文件内容
        """
        return self.read_file(self.user_file)

    def write_user(self, content: str) -> None:
        """Write content to USER.md file.
        
        将内容写入 USER.md 文件。
        
        Args:
            content: Content to write / 要写入的内容
        """
        self.user_file.write_text(content, encoding="utf-8")

    # -- context injection (used by context.py) ------------------------------
    # -- 上下文注入（由 context.py 使用） -------------------------------------

    def get_memory_context(self) -> str:
        """Get memory context for inclusion in agent prompts.
        
        获取要包含在代理提示词中的记忆上下文。
        
        Returns:
            Formatted memory context string, or empty string if no memory / 格式化的记忆上下文字符串，如果没有记忆则返回空字符串
        """
        long_term = self.read_memory()
        return f"## Long-term Memory\n{long_term}" if long_term else ""

    # -- history.jsonl — append-only, JSONL format ---------------------------

    def append_history(self, entry: str, *, max_chars: int | None = None) -> int:
        """Append entry to history.jsonl and return its auto-incrementing cursor.
        
        将条目追加到 history.jsonl 并返回其自增游标。

        Entries are passed through `strip_think` to drop template-level leaks
        (e.g. unclosed `<think` prefixes, `<channel|>` markers) before being
        persisted. If the cleaned content is empty but the raw entry wasn't,
        the record is persisted with an empty string rather than falling back
        to the raw leak — otherwise `strip_think`'s guarantees would be
        undone by history replay / consolidation downstream.
        
        条目在持久化之前会通过 `strip_think` 过滤掉模板级泄漏
        （例如未闭合的 `<think` 前缀、`<channel|>` 标记）。
        如果清理后的内容为空但原始条目不为空，
        记录会以空字符串持久化，而不是回退到原始泄漏内容
        —— 否则 `strip_think` 的保证会被下游的历史回放/整合撤销。

        Args:
            entry: History entry content / 历史条目内容
            max_chars: Maximum characters (default: _HISTORY_ENTRY_HARD_CAP) / 最大字符数（默认：_HISTORY_ENTRY_HARD_CAP）
            
        Returns:
            Auto-incrementing cursor value / 自增游标值
        """
        limit = max_chars if max_chars is not None else _HISTORY_ENTRY_HARD_CAP
        cursor = self._next_cursor()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        raw = entry.rstrip()
        if len(raw) > limit:
            if not self._oversize_logged:
                self._oversize_logged = True
                logger.warning(
                    "history entry exceeds {} chars ({}); truncating. "
                    "Usually means a caller forgot its own cap; "
                    "further occurrences suppressed.",
                    limit, len(raw),
                )
            raw = truncate_text(raw, limit)
        content = strip_think(raw)
        if raw and not content:
            logger.debug(
                "history entry {} stripped to empty (likely template leak); "
                "persisting empty content to avoid re-polluting context",
                cursor,
            )
        record = {"cursor": cursor, "timestamp": ts, "content": content}
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._cursor_file.write_text(str(cursor), encoding="utf-8")
        return cursor

    @staticmethod
    def _valid_cursor(value: Any) -> int | None:
        """Int cursors only — reject bool (``isinstance(True, int)`` is True).
        
        仅接受整数游标 —— 拒绝布尔值（因为 ``isinstance(True, int)`` 为 True）。
        
        Args:
            value: Value to validate / 要验证的值
            
        Returns:
            Valid cursor integer or None / 有效的游标整数或 None
        """
        if isinstance(value, bool) or not isinstance(value, int):
            return None
        return value

    def _iter_valid_entries(self) -> Iterator[tuple[dict[str, Any], int]]:
        """Yield ``(entry, cursor)`` for entries with int cursors; warn once on corruption.
        
        为具有整数游标的条目生成 ``(entry, cursor)``；遇到损坏时警告一次。
        
        Yields:
            Tuple of entry dict and cursor / 条目字典和游标的元组
        """
        poisoned: Any = None
        for entry in self._read_entries():
            raw = entry.get("cursor")
            if raw is None:
                continue
            cursor = self._valid_cursor(raw)
            if cursor is None:
                poisoned = raw
                continue
            yield entry, cursor
        if poisoned is not None and not self._corruption_logged:
            self._corruption_logged = True
            logger.warning(
                "history.jsonl contains a non-int cursor ({!r}); dropping it. "
                "Usually caused by an external writer; further occurrences suppressed.",
                poisoned,
            )

    def _next_cursor(self) -> int:
        """Read the current cursor counter and return the next value.
        
        读取当前游标计数器并返回下一个值。
        
        Returns:
            Next cursor value / 下一个游标值
        """
        if self._cursor_file.exists():
            try:
                return int(self._cursor_file.read_text(encoding="utf-8").strip()) + 1
            except (ValueError, OSError):
                pass
        # Fast path: trust the tail when intact.  Otherwise scan the whole
        # file and take ``max`` — that stays correct even if the monotonic
        # invariant was broken by external writes.
        # 快速路径：当尾部完整时信任尾部。否则扫描整个文件并取 \u201cmax\u201d —— 
        # 即使外部写入破坏了单调不变性也能保持正确。
        last = self._read_last_entry() or {}
        cursor = self._valid_cursor(last.get("cursor"))
        if cursor is not None:
            return cursor + 1
        return max((c for _, c in self._iter_valid_entries()), default=0) + 1

    def read_unprocessed_history(self, since_cursor: int) -> list[dict[str, Any]]:
        """Return history entries with a valid cursor > *since_cursor*.
        
        返回具有有效游标 > *since_cursor* 的历史条目。
        
        Args:
            since_cursor: Cursor to filter from / 从中过滤的游标
            
        Returns:
            List of unprocessed history entries / 未处理的历史条目列表
        """
        return [e for e, c in self._iter_valid_entries() if c > since_cursor]

    def compact_history(self) -> None:
        """Drop oldest entries if the file exceeds *max_history_entries*.
        
        如果文件超过 *max_history_entries* 则删除最旧的条目。
        
        Args:
            max_history_entries: Maximum number of history entries to keep / 要保留的最大历史条目数
        """
        if self.max_history_entries <= 0:
            return
        entries = self._read_entries()
        if len(entries) <= self.max_history_entries:
            return
        kept = entries[-self.max_history_entries:]
        self._write_entries(kept)

    # -- JSONL helpers -------------------------------------------------------
    # -- JSONL 辅助函数 ------------------------------------------------------

    def _read_entries(self) -> list[dict[str, Any]]:
        """Read all entries from history.jsonl.
        
        从 history.jsonl 读取所有条目。
        
        Returns:
            List of entry dictionaries / 条目字典列表
        """
        entries: list[dict[str, Any]] = []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            pass
        return entries

    def _read_last_entry(self) -> dict[str, Any] | None:
        """Read the last entry from the JSONL file efficiently.
        
        高效地从 JSONL 文件读取最后一个条目。
        
        Returns:
            Last entry dict or None if file is empty / 最后一个条目字典，如果文件为空则返回 None
        """
        try:
            with open(self.history_file, "rb") as f:
                f.seek(0, 2)
                size = f.tell()
                if size == 0:
                    return None
                read_size = min(size, 4096)
                f.seek(size - read_size)
                data = f.read().decode("utf-8")
                lines = [l for l in data.split("\n") if l.strip()]
                if not lines:
                    return None
                return json.loads(lines[-1])
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
            return None

    def _write_entries(self, entries: list[dict[str, Any]]) -> None:
        """Overwrite history.jsonl with the given entries.
        
        用给定的条目覆盖 history.jsonl。
        
        Args:
            entries: List of entry dictionaries to write / 要写入的条目字典列表
        """
        with open(self.history_file, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # -- dream cursor --------------------------------------------------------
    # -- 梦境游标 ------------------------------------------------------------

    def get_last_dream_cursor(self) -> int:
        """Get the last processed Dream cursor value.
        
        获取最后处理的梦境游标值。
        
        Returns:
            Last dream cursor / 最后梦境游标
        """
        if self._dream_cursor_file.exists():
            try:
                return int(self._dream_cursor_file.read_text(encoding="utf-8").strip())
            except (ValueError, OSError):
                pass
        return 0

    def set_last_dream_cursor(self, cursor: int) -> None:
        """Set the last processed Dream cursor value.
        
        设置最后处理的梦境游标值。
        
        Args:
            cursor: Dream cursor value / 梦境游标值
        """
        self._dream_cursor_file.write_text(str(cursor), encoding="utf-8")

    # -- message formatting utility ------------------------------------------
    # -- 消息格式化工具 ------------------------------------------------------

    @staticmethod
    def _format_messages(messages: list[dict]) -> str:
        """Format messages into a readable string representation.
        
        将消息格式化为可读的字符串表示。
        
        Args:
            messages: List of message dictionaries / 消息字典列表
            
        Returns:
            Formatted message string / 格式化后的消息字符串
        """
        lines = []
        for message in messages:
            if not message.get("content"):
                continue
            tools = f" [tools: {', '.join(message['tools_used'])}]" if message.get("tools_used") else ""
            lines.append(
                f"[{message.get('timestamp', '?')[:16]}] {message['role'].upper()}{tools}: {message['content']}"
            )
        return "\n".join(lines)

    def raw_archive(self, messages: list[dict], *, max_chars: int | None = None) -> None:
        """Fallback: dump raw messages to history.jsonl without LLM summarization.
        
        回退方案：将原始消息转储到 history.jsonl，不使用 LLM 总结。
        
        Args:
            messages: Raw messages to archive / 要归档的原始消息
            max_chars: Maximum characters (default: _RAW_ARCHIVE_MAX_CHARS) / 最大字符数（默认：_RAW_ARCHIVE_MAX_CHARS）
        """
        limit = max_chars if max_chars is not None else _RAW_ARCHIVE_MAX_CHARS
        formatted = truncate_text(self._format_messages(messages), limit)
        self.append_history(
            f"[RAW] {len(messages)} messages\n"
            f"{formatted}"
        )
        logger.warning(
            "Memory consolidation degraded: raw-archived {} messages", len(messages)
        )



# ---------------------------------------------------------------------------
# Consolidator — lightweight token-budget triggered consolidation
# 整合器 —— 轻量级基于 token 预算触发的整合
# ---------------------------------------------------------------------------


# Individual history.jsonl writers cap their own payloads tightly; the
# _HISTORY_ENTRY_HARD_CAP at append_history() is a belt-and-suspenders default
# that catches any new caller that forgot to set its own cap.
# 各个 history.jsonl 写入器严格限制自己的负载；append_history() 处的 _HISTORY_ENTRY_HARD_CAP
# 是双重保险默认值，用于捕获任何忘记设置自己上限的新调用者。
_RAW_ARCHIVE_MAX_CHARS = 16_000       # fallback dump (LLM failed) / 回退转储（LLM 失败时）
_ARCHIVE_SUMMARY_MAX_CHARS = 8_000    # LLM-produced consolidation summary / LLM 生成的整合摘要
_HISTORY_ENTRY_HARD_CAP = 64_000      # emergency cap in append_history / append_history 中的紧急上限


class Consolidator:
    """Lightweight consolidation: summarizes evicted messages into history.jsonl.
    
    轻量级整合：将被逐出的消息摘要到 history.jsonl 中。
    """

    _MAX_CONSOLIDATION_ROUNDS = 5
    """Maximum consolidation rounds / 最大整合轮数"""

    _SAFETY_BUFFER = 1024  # extra headroom for tokenizer estimation drift
    """安全缓冲，用于 token 化器估算漂移的额外余量"""

    def __init__(
        self,
        store: MemoryStore,
        provider: LLMProvider,
        model: str,
        sessions: SessionManager,
        context_window_tokens: int,
        build_messages: Callable[..., list[dict[str, Any]]],
        get_tool_definitions: Callable[[], list[dict[str, Any]]],
        max_completion_tokens: int = 4096,
    ):
        """Initialize the Consolidator.
        
        初始化整合器。
        
        Args:
            store: Memory store / 记忆存储
            provider: LLM provider / LLM 提供者
            model: Model name / 模型名称
            sessions: Session manager / 会话管理器
            context_window_tokens: Context window size in tokens / 上下文窗口大小（token 数）
            build_messages: Function to build messages / 构建消息的函数
            get_tool_definitions: Function to get tool definitions / 获取工具定义的函数
            max_completion_tokens: Max completion tokens / 最大完成 token 数
        """
        self.store = store
        self.provider = provider
        self.model = model
        self.sessions = sessions
        self.context_window_tokens = context_window_tokens
        self.max_completion_tokens = max_completion_tokens
        self._build_messages = build_messages
        self._get_tool_definitions = get_tool_definitions
        self._locks: weakref.WeakValueDictionary[str, asyncio.Lock] = (
            weakref.WeakValueDictionary()
        )

    def get_lock(self, session_key: str) -> asyncio.Lock:
        """Return the shared consolidation lock for one session.
        
        返回一个会话的共享整合锁。
        
        Args:
            session_key: Session key / 会话键
            
        Returns:
            Async lock for the session / 会话的异步锁
        """
        return self._locks.setdefault(session_key, asyncio.Lock())

    def pick_consolidation_boundary(
        self,
        session: Session,
        tokens_to_remove: int,
    ) -> tuple[int, int] | None:
        """Pick a user-turn boundary that removes enough old prompt tokens.
        
        选择一个用户轮次边界，以移除足够的旧提示 token。
        
        Args:
            session: Session object / 会话对象
            tokens_to_remove: Number of tokens to remove / 要删除的 token 数
            
        Returns:
            Tuple of (boundary index, removed tokens) or None / (边界索引，删除的 token 数) 元组或 None
        """
        start = session.last_consolidated
        if start >= len(session.messages) or tokens_to_remove <= 0:
            return None

        removed_tokens = 0
        last_boundary: tuple[int, int] | None = None
        for idx in range(start, len(session.messages)):
            message = session.messages[idx]
            if idx > start and message.get("role") == "user":
                last_boundary = (idx, removed_tokens)
                if removed_tokens >= tokens_to_remove:
                    return last_boundary
            removed_tokens += estimate_message_tokens(message)

        return last_boundary

    def estimate_session_prompt_tokens(
        self,
        session: Session,
        *,
        session_summary: str | None = None,
    ) -> tuple[int, str]:
        """Estimate current prompt size for the normal session history view.
        
        估算正常会话历史视图的当前提示大小。
        
        Args:
            session: Session object / 会话对象
            session_summary: Optional session summary / 可选的会话摘要
            
        Returns:
            Tuple of (estimated tokens, source method) / (估算 token 数，来源方法) 元组
        """
        history = session.get_history(max_messages=0)
        channel, chat_id = (session.key.split(":", 1) if ":" in session.key else (None, None))
        probe_messages = self._build_messages(
            history=history,
            current_message="[token-probe]",
            channel=channel,
            chat_id=chat_id,
            session_summary=session_summary,
        )
        return estimate_prompt_tokens_chain(
            self.provider,
            self.model,
            probe_messages,
            self._get_tool_definitions(),
        )

    @property
    def _input_token_budget(self) -> int:
        """Available input token budget for consolidation LLM.
        
        可用于整合 LLM 的输入 token 预算。
        
        Returns:
            Token budget / Token 预算
        """
        return self.context_window_tokens - self.max_completion_tokens - self._SAFETY_BUFFER

    def _truncate_to_token_budget(self, text: str) -> str:
        """Truncate text so it fits within the consolidation LLM's token budget.
        
        截断文本以适应整合 LLM 的 token 预算。
        
        Args:
            text: Text to truncate / 要截断的文本
            
        Returns:
            Truncated text / 截断后的文本
        """
        budget = self._input_token_budget
        if budget <= 0:
            return truncate_text(text, _RAW_ARCHIVE_MAX_CHARS)
        try:
            enc = tiktoken.get_encoding("cl100k_base")
            tokens = enc.encode(text)
            if len(tokens) <= budget:
                return text
            return enc.decode(tokens[:budget]) + "\n... (truncated)"
        except Exception:
            return truncate_text(text, budget * 4)

    async def archive(self, messages: list[dict]) -> str | None:
        """Summarize messages via LLM and append to history.jsonl.

        Returns the summary text on success, None if nothing to archive.
        
        通过 LLM 总结消息并追加到 history.jsonl。
        
        成功时返回摘要文本，没有要归档的内容时返回 None。
        
        Args:
            messages: Messages to summarize / 要总结的消息
            
        Returns:
            Summary text or None / 摘要文本或 None
        """
        if not messages:
            return None
        try:
            formatted = MemoryStore._format_messages(messages)
            formatted = self._truncate_to_token_budget(formatted)
            response = await self.provider.chat_with_retry(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": render_template(
                            "agent/consolidator_archive.md",
                            strip=True,
                        ),
                    },
                    {"role": "user", "content": formatted},
                ],
                tools=None,
                tool_choice=None,
            )
            if response.finish_reason == "error":
                raise RuntimeError(f"LLM returned error: {response.content}")
            summary = response.content or "[no summary]"
            self.store.append_history(summary, max_chars=_ARCHIVE_SUMMARY_MAX_CHARS)
            return summary
        except Exception:
            logger.warning("Consolidation LLM call failed, raw-dumping to history")
            self.store.raw_archive(messages)
            return None

    async def maybe_consolidate_by_tokens(
        self,
        session: Session,
        *,
        session_summary: str | None = None,
    ) -> None:
        """Loop: archive old messages until prompt fits within safe budget.

        The budget reserves space for completion tokens and a safety buffer
        so the LLM request never exceeds the context window.
        
        循环：归档旧消息直到提示适应安全预算。
        
        预算为完成 token 和安全缓冲预留空间，因此 LLM 请求永远不会超过上下文窗口。
        
        Args:
            session: Session object / 会话对象
            session_summary: Optional session summary / 可选的会话摘要
        """
        if not session.messages or self.context_window_tokens <= 0:
            return

        lock = self.get_lock(session.key)
        async with lock:
            budget = self._input_token_budget
            target = budget // 2
            try:
                estimated, source = self.estimate_session_prompt_tokens(
                    session,
                    session_summary=session_summary,
                )
            except Exception:
                logger.exception("Token estimation failed for {}", session.key)
                estimated, source = 0, "error"
            if estimated <= 0:
                return
            if estimated < budget:
                unconsolidated_count = len(session.messages) - session.last_consolidated
                logger.debug(
                    "Token consolidation idle {}: {}/{} via {}, msgs={}",
                    session.key,
                    estimated,
                    self.context_window_tokens,
                    source,
                    unconsolidated_count,
                )
                return

            last_summary = None
            for round_num in range(self._MAX_CONSOLIDATION_ROUNDS):
                if estimated <= target:
                    break

                boundary = self.pick_consolidation_boundary(session, max(1, estimated - target))
                if boundary is None:
                    logger.debug(
                        "Token consolidation: no safe boundary for {} (round {})",
                        session.key,
                        round_num,
                    )
                    break

                end_idx = boundary[0]

                chunk = session.messages[session.last_consolidated:end_idx]
                if not chunk:
                    break

                logger.info(
                    "Token consolidation round {} for {}: {}/{} via {}, chunk={} msgs",
                    round_num,
                    session.key,
                    estimated,
                    self.context_window_tokens,
                    source,
                    len(chunk),
                )
                summary = await self.archive(chunk)
                # Advance the cursor either way: on success the chunk was
                # summarized; on failure archive() already raw-archived it as
                # a breadcrumb. Re-archiving the same chunk on the next call
                # would just emit duplicate [RAW] entries.
                # 无论如何都要推进游标：成功时块已被总结；
                # 失败时 archive() 已将其作为面包屑原始归档。
                # 下次调用时重新归档相同的块只会产生重复的 [RAW] 条目。
                if summary:
                    last_summary = summary
                session.last_consolidated = end_idx
                self.sessions.save(session)
                if not summary:
                    # LLM is degraded — stop hammering it this call;
                    # the next invocation can retry a fresh chunk.
                    # LLM 已降级 —— 本次调用停止重复尝试；
                    # 下次调用可以重试新的块。
                    # LLM is degraded — stop hammering it this call;
                    # the next invocation can retry a fresh chunk.
                    break

                try:
                    estimated, source = self.estimate_session_prompt_tokens(
                        session,
                        session_summary=session_summary,
                    )
                except Exception:
                    logger.exception("Token estimation failed for {}", session.key)
                    estimated, source = 0, "error"
                if estimated <= 0:
                    break

            # Persist the last summary to session metadata so it can be injected
            # into the runtime context on the next prepare_session() call, aligning
            # the summary injection strategy with AutoCompact._archive().
            # 将最后的摘要持久化到会话元数据中，以便在下一次 prepare_session() 调用时
            # 可以将其注入运行时上下文，使摘要注入策略与 AutoCompact._archive() 保持一致。
            if last_summary and last_summary != "(nothing)":
                session.metadata["_last_summary"] = {
                    "text": last_summary,
                    "last_active": session.updated_at.isoformat(),
                }
                self.sessions.save(session)


# ---------------------------------------------------------------------------
# Dream — heavyweight cron-scheduled memory consolidation
# 梦境 —— 重量级定时计划内存整合
# ---------------------------------------------------------------------------


# Single source of truth for the staleness threshold used in _annotate_with_ages
# *and* in the Phase 1 prompt template (passed as `stale_threshold_days`).
# Keep code and prompt aligned — if you bump this, the LLM's instruction string
# updates automatically.
# _annotate_with_ages 中使用的陈旧阈值以及_phase_1 提示模板（作为 `stale_threshold_days` 传递）
# 的唯一真实来源。保持代码和提示一致 —— 如果修改此值，LLM 的指令字符串会自动更新。
_STALE_THRESHOLD_DAYS = 14
"""陈旧阈值天数 / 陈旧阈值（天）"""


class Dream:
    """Two-phase memory processor: analyze history.jsonl, then edit files via AgentRunner.

    Phase 1 produces an analysis summary (plain LLM call).
    Phase 2 delegates to AgentRunner with read_file / edit_file tools so the
    LLM can make targeted, incremental edits instead of replacing entire files.
    
    两阶段内存处理器：分析 history.jsonl，然后通过 AgentRunner 编辑文件。
    
    第一阶段生成分析摘要（普通 LLM 调用）。
    第二阶段委托给具有 read_file / edit_file 工具的 AgentRunner，因此
    LLM 可以进行有针对性的增量编辑，而不是替换整个文件。
    """

    # Caps on prompt-bound inputs so Dream's LLM calls never exceed the model's
    # context window just because a file (or a legacy large history entry) grew
    # unexpectedly. Each file still appears in full via read_file when the agent
    # needs it in Phase 2 — these caps only bound the Phase 1/2 prompt preview.
    # 对提示绑定输入的上限进行限制，以便 Dream 的 LLM 调用永远不会仅仅因为文件
    # （或旧版大型历史条目）意外增长而超出模型的上下文窗口。
    # 当代理在第二阶段需要时，每个文件仍然通过 read_file 完整出现 —— 
    # 这些上限仅限制第一阶段/第二阶段的提示预览。
    _MEMORY_FILE_MAX_CHARS = 32_000
    """Memory file max chars / 记忆文件最大字符数"""
    _SOUL_FILE_MAX_CHARS = 16_000
    """Soul file max chars / 身份文件最大字符数"""
    _USER_FILE_MAX_CHARS = 16_000
    """User file max chars / 用户文件最大字符数"""
    _HISTORY_ENTRY_PREVIEW_MAX_CHARS = 4_000
    """History entry preview max chars / 历史条目预览最大字符数"""

    def __init__(
        self,
        store: MemoryStore,
        provider: LLMProvider,
        model: str,
        max_batch_size: int = 20,
        max_iterations: int = 10,
        max_tool_result_chars: int = 16_000,
        annotate_line_ages: bool = True,
    ):
        """Initialize the Dream memory processor.
        
        初始化梦境内存处理器。
        
        Args:
            store: Memory store / 记忆存储
            provider: LLM provider / LLM 提供者
            model: Model name / 模型名称
            max_batch_size: Maximum batch size / 最大批次大小
            max_iterations: Maximum iterations / 最大迭代次数
            max_tool_result_chars: Maximum tool result characters / 最大工具结果字符数
            annotate_line_ages: Whether to annotate line ages / 是否注释行年龄
        """
        self.store = store
        self.provider = provider
        self.model = model
        self.max_batch_size = max_batch_size
        self.max_iterations = max_iterations
        self.max_tool_result_chars = max_tool_result_chars
        # Kill switch for the git-blame-based per-line age annotation in Phase 1.
        # Default True keeps the #3212 behavior; set False to feed MEMORY.md raw
        # (e.g. if a specific LLM reacts poorly to the `← Nd` suffix).
        # 第一阶段基于 git-blame 的逐行年龄注释的关闭开关。
        # 默认 True 保持 #3212 行为；设置为 False 以原始方式提供 MEMORY.md
        # （例如，如果特定 LLM 对 `← Nd` 后缀反应不佳）。
        self.annotate_line_ages = annotate_line_ages
        self._runner = AgentRunner(provider)
        self._tools = self._build_tools()

    # -- tool registry -------------------------------------------------------
    # -- 工具注册表 ----------------------------------------------------------

    def _build_tools(self) -> ToolRegistry:
        """Build a minimal tool registry for the Dream agent.
        
        为梦境代理构建最小工具注册表。
        
        Returns:
            Tool registry / 工具注册表
        """
        from nanobot.agent.skills import BUILTIN_SKILLS_DIR
        from nanobot.agent.tools.filesystem import EditFileTool, ReadFileTool, WriteFileTool

        tools = ToolRegistry()
        workspace = self.store.workspace
        # Allow reading builtin skills for reference during skill creation
        # 允许在创建技能时读取内置技能作为参考
        extra_read = [BUILTIN_SKILLS_DIR] if BUILTIN_SKILLS_DIR.exists() else None
        tools.register(ReadFileTool(
            workspace=workspace,
            allowed_dir=workspace,
            extra_allowed_dirs=extra_read,
        ))
        tools.register(EditFileTool(workspace=workspace, allowed_dir=workspace))
        # write_file resolves relative paths from workspace root, but can only
        # write under skills/ so the prompt can safely use skills/<name>/SKILL.md.
        # write_file 从工作区根目录解析相对路径，但只能写入 skills/ 下，
        # 因此提示可以安全地使用 skills/<name>/SKILL.md。
        skills_dir = workspace / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        tools.register(WriteFileTool(workspace=workspace, allowed_dir=skills_dir))
        return tools

    # -- skill listing --------------------------------------------------------
    # -- 技能列表 -------------------------------------------------------------

    def _list_existing_skills(self) -> list[str]:
        """List existing skills as 'name — description' for dedup context.
        
        将现有技能列为 'name — description' 格式以进行去重上下文。
        
        Returns:
            List of skill entries / 技能条目列表
        """
        import re as _re

        from nanobot.agent.skills import BUILTIN_SKILLS_DIR

        _DESC_RE = _re.compile(r"^description:\s*(.+)$", _re.MULTILINE | _re.IGNORECASE)
        entries: dict[str, str] = {}
        for base in (self.store.workspace / "skills", BUILTIN_SKILLS_DIR):
            if not base.exists():
                continue
            for d in base.iterdir():
                if not d.is_dir():
                    continue
                skill_md = d / "SKILL.md"
                if not skill_md.exists():
                    continue
                # Prefer workspace skills over builtin (same name)
                # 优先使用工作区技能而非内置技能（同名时）
                if d.name in entries and base == BUILTIN_SKILLS_DIR:
                    continue
                content = skill_md.read_text(encoding="utf-8")[:500]
                m = _DESC_RE.search(content)
                desc = m.group(1).strip() if m else "(no description)"
                entries[d.name] = desc
        return [f"{name} — {desc}" for name, desc in sorted(entries.items())]

    # -- main entry ----------------------------------------------------------
    # -- 主入口 --------------------------------------------------------------

    def _annotate_with_ages(self, content: str) -> str:
        """Append per-line age suffixes to MEMORY.md content.

        Each non-blank line whose age exceeds ``_STALE_THRESHOLD_DAYS`` gets a
        suffix like ``← 30d`` indicating days since last modification.
        Returns the original content unchanged if git is unavailable,
        annotate fails, or the line count doesn't match the age count
        (which can happen with an uncommitted working-tree edit — better to
        skip annotation than to tag the wrong line).
        SOUL.md and USER.md are never annotated.
        
        为 MEMORY.md 内容追加逐行年龄后缀。
        
        每个年龄超过 ``_STALE_THRESHOLD_DAYS`` 的非空行都会获得一个后缀，
        如 ``← 30d``，表示距上次修改的天数。
        如果 git 不可用、注释失败或行数与年龄数不匹配
        （可能发生在未提交的工作树编辑中 —— 最好跳过注释而不是标记错误的行），
        则返回原始内容不变。
        SOUL.md 和 USER.md 从不会被注释。
        
        Args:
            content: MEMORY.md content / MEMORY.md 内容
            
        Returns:
            Annotated content or original content / 注释后的内容或原始内容
        """
        file_path = "memory/MEMORY.md"
        try:
            ages = self.store.git.line_ages(file_path)
        except Exception:
            logger.debug("line_ages failed for {}", file_path)
            return content
        if not ages:
            return content

        had_trailing = content.endswith("\n")
        lines = content.splitlines()
        # If HEAD-blob line count disagrees with the working-tree content we
        # received, ages would be assigned to the wrong lines — skip entirely
        # and feed the LLM un-annotated content rather than misleading data.
        # 如果 HEAD-blob 行数与我们收到的工作树内容不一致，
        # 年龄将被分配给错误的行 —— 完全跳过并向 LLM 提供未注释内容，而不是误导性数据。
        if len(lines) != len(ages):
            logger.debug(
                "line_ages length mismatch for {} (lines={}, ages={}); skipping annotation",
                file_path, len(lines), len(ages),
            )
            return content

        annotated: list[str] = []
        for line, age in zip(lines, ages):
            if not line.strip():
                annotated.append(line)
                continue
            if age.age_days > _STALE_THRESHOLD_DAYS:
                annotated.append(f"{line}  \u2190 {age.age_days}d")
            else:
                annotated.append(line)
        result = "\n".join(annotated)
        if had_trailing:
            result += "\n"
        return result

    async def run(self) -> bool:
        """Process unprocessed history entries. Returns True if work was done.
        
        处理未处理的历史条目。如果完成了工作则返回 True。
        
        Returns:
            True if work was done / 如果完成了工作则返回 True
        """
        from nanobot.agent.skills import BUILTIN_SKILLS_DIR

        last_cursor = self.store.get_last_dream_cursor()
        entries = self.store.read_unprocessed_history(since_cursor=last_cursor)
        if not entries:
            return False

        batch = entries[: self.max_batch_size]
        logger.info(
            "Dream: processing {} entries (cursor {}→{}), batch={}",
            len(entries), last_cursor, batch[-1]["cursor"], len(batch),
        )

        # Build history text for LLM — cap each entry so a legacy oversized
        # record (e.g. pre-#3412 raw_archive dump) can't blow up the prompt.
        # 为 LLM 构建历史文本 —— 限制每个条目，这样旧版超大记录
        # （例如 #3412 之前的 raw_archive 转储）就不会搞垮提示。
        history_text = "\n".join(
            f"[{e['timestamp']}] "
            f"{truncate_text(e['content'], self._HISTORY_ENTRY_PREVIEW_MAX_CHARS)}"
            for e in batch
        )

        # Current file contents + per-line age annotations (MEMORY.md only).
        # Each file is capped in the *prompt preview* only; Phase 2 still sees
        # the full file via the read_file tool.
        # 当前文件内容 + 逐行年龄注释（仅限 MEMORY.md）。
        # 每个文件仅在 *提示预览* 中有限制；第二阶段仍然通过 read_file 工具看到完整文件。
        current_date = datetime.now().strftime("%Y-%m-%d")
        raw_memory = self.store.read_memory() or "(empty)"
        annotated_memory = (
            self._annotate_with_ages(raw_memory)
            if self.annotate_line_ages
            else raw_memory
        )
        current_memory = truncate_text(annotated_memory, self._MEMORY_FILE_MAX_CHARS)
        current_soul = truncate_text(
            self.store.read_soul() or "(empty)", self._SOUL_FILE_MAX_CHARS,
        )
        current_user = truncate_text(
            self.store.read_user() or "(empty)", self._USER_FILE_MAX_CHARS,
        )

        file_context = (
            f"## Current Date\n{current_date}\n\n"
            f"## Current MEMORY.md ({len(current_memory)} chars)\n{current_memory}\n\n"
            f"## Current SOUL.md ({len(current_soul)} chars)\n{current_soul}\n\n"
            f"## Current USER.md ({len(current_user)} chars)\n{current_user}"
        )

        # Phase 1: Analyze (no skills list — dedup is Phase 2's job)
        # 第一阶段：分析（没有技能列表 —— 去重是第二阶段的工作）
        phase1_prompt = (
            f"## Conversation History\n{history_text}\n\n{file_context}"
        )

        try:
            phase1_response = await self.provider.chat_with_retry(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": render_template(
                            "agent/dream_phase1.md",
                            strip=True,
                            stale_threshold_days=_STALE_THRESHOLD_DAYS,
                        ),
                    },
                    {"role": "user", "content": phase1_prompt},
                ],
                tools=None,
                tool_choice=None,
            )
            analysis = phase1_response.content or ""
            logger.debug("Dream Phase 1 analysis ({} chars): {}", len(analysis), analysis[:500])
        except Exception:
            logger.exception("Dream Phase 1 failed")
            return False

        # Phase 2: Delegate to AgentRunner with read_file / edit_file
        # 第二阶段：委托给具有 read_file / edit_file 的 AgentRunner
        existing_skills = self._list_existing_skills()
        skills_section = ""
        if existing_skills:
            skills_section = (
                "\n\n## Existing Skills\n"
                + "\n".join(f"- {s}" for s in existing_skills)
            )
        phase2_prompt = f"## Analysis Result\n{analysis}\n\n{file_context}{skills_section}"

        tools = self._tools
        skill_creator_path = BUILTIN_SKILLS_DIR / "skill-creator" / "SKILL.md"
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": render_template(
                    "agent/dream_phase2.md",
                    strip=True,
                    skill_creator_path=str(skill_creator_path),
                ),
            },
            {"role": "user", "content": phase2_prompt},
        ]

        try:
            result = await self._runner.run(AgentRunSpec(
                initial_messages=messages,
                tools=tools,
                model=self.model,
                max_iterations=self.max_iterations,
                max_tool_result_chars=self.max_tool_result_chars,
                fail_on_tool_error=False,
            ))
            logger.debug(
                "Dream Phase 2 complete: stop_reason={}, tool_events={}",
                result.stop_reason, len(result.tool_events),
            )
            for ev in (result.tool_events or []):
                logger.info("Dream tool_event: name={}, status={}, detail={}", ev.get("name"), ev.get("status"), ev.get("detail", "")[:200])
        except Exception:
            logger.exception("Dream Phase 2 failed")
            result = None

        # Build changelog from tool events
        # 从工具事件构建变更日志
        changelog: list[str] = []
        if result and result.tool_events:
            for event in result.tool_events:
                if event["status"] == "ok":
                    changelog.append(f"{event['name']}: {event['detail']}")

        # Advance cursor — always, to avoid re-processing Phase 1
        # 推进游标 —— 始终如此，以避免重新处理第一阶段
        new_cursor = batch[-1]["cursor"]
        self.store.set_last_dream_cursor(new_cursor)
        self.store.compact_history()

        if result and result.stop_reason == "completed":
            logger.info(
                "Dream done: {} change(s), cursor advanced to {}",
                len(changelog), new_cursor,
            )
        else:
            reason = result.stop_reason if result else "exception"
            logger.warning(
                "Dream incomplete ({}): cursor advanced to {}",
                reason, new_cursor,
            )

        # Git auto-commit (only when there are actual changes)
        # Git 自动提交（仅在有实际更改时）
        if changelog and self.store.git.is_initialized():
            ts = batch[-1]["timestamp"]
            summary = f"dream: {ts}, {len(changelog)} change(s)"
            commit_msg = f"{summary}\n\n{analysis.strip()}"
            sha = self.store.git.auto_commit(commit_msg)
            if sha:
                logger.info("Dream commit: {}", sha)

        return True
