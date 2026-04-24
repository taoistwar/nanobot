"""Auto compact: proactive compression of idle sessions to reduce token cost and latency."""

from __future__ import annotations

from collections.abc import Collection
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from loguru import logger
from nanobot.session.manager import Session, SessionManager

if TYPE_CHECKING:
    from nanobot.agent.memory import Consolidator


class AutoCompact:
    """Automatic session compaction for idle sessions.
    
    自动压缩空闲会话，减少 token 消耗和延迟。
    """
    
    _RECENT_SUFFIX_MESSAGES = 8  # Number of recent messages to retain / 保留的最近消息数量

    def __init__(self, sessions: SessionManager, consolidator: Consolidator,
                 session_ttl_minutes: int = 0):
        """Initialize AutoCompact.
        
        Args:
            sessions: Session manager instance / 会话管理器实例
            consolidator: Memory consolidator instance / 记忆压缩器实例
            session_ttl_minutes: Session TTL in minutes (0 = disabled) / 会话超时时间（分钟，0=禁用）
        """
        self.sessions = sessions  # Session manager / 会话管理器
        self.consolidator = consolidator  # Memory consolidator / 记忆压缩器
        self._ttl = session_ttl_minutes  # Session TTL in minutes / 会话超时时间（分钟）
        self._archiving: set[str] = set()  # Set of session keys currently being archived / 正在归档的会话键集合
        self._summaries: dict[str, tuple[str, datetime]] = {}  # Cached summaries per session / 每个会话的缓存摘要

    def _is_expired(self, ts: datetime | str | None,
                    now: datetime | None = None) -> bool:
        """Check if a session has expired based on TTL.
        
        根据 TTL 检查会话是否已过期。
        
        Args:
            ts: Timestamp to check / 要检查的时间戳
            now: Current time (defaults to now) / 当前时间（默认为现在）
            
        Returns:
            True if expired, False otherwise / 过期返回 True，否则返回 False
        """
        if self._ttl <= 0 or not ts:
            return False
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return ((now or datetime.now()) - ts).total_seconds() >= self._ttl * 60

    @staticmethod
    def _format_summary(text: str, last_active: datetime) -> str:
        """Format a session summary with idle time information.
        
        格式化会话摘要，包含空闲时间信息。
        
        Args:
            text: Summary text / 摘要文本
            last_active: Last active timestamp / 最后活动时间戳
            
        Returns:
            Formatted summary string / 格式化后的摘要字符串
        """
        idle_min = int((datetime.now() - last_active).total_seconds() / 60)
        return f"Inactive for {idle_min} minutes.\nPrevious conversation summary: {text}"

    def _split_unconsolidated(
        self, session: Session,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Split live session tail into archiveable prefix and retained recent suffix.
        
        将活动会话的尾部分割为可归档的前缀和保留的最近后缀。
        
        Args:
            session: Session to split / 要分割的会话
            
        Returns:
            Tuple of (archiveable messages, retained messages) / (可归档消息，保留消息) 的元组
        """
        tail = list(session.messages[session.last_consolidated:])
        if not tail:
            return [], []

        probe = Session(
            key=session.key,
            messages=tail.copy(),
            created_at=session.created_at,
            updated_at=session.updated_at,
            metadata={},
            last_consolidated=0,
        )
        probe.retain_recent_legal_suffix(self._RECENT_SUFFIX_MESSAGES)
        kept = probe.messages
        cut = len(tail) - len(kept)
        return tail[:cut], kept

    def check_expired(self, schedule_background: Callable[[Coroutine], None],
                      active_session_keys: Collection[str] = ()) -> None:
        """Schedule archival for idle sessions, skipping those with in-flight agent tasks.
        
        为空闲会话调度归档，跳过有正在进行的代理任务的会话。
        
        Args:
            schedule_background: Callback to schedule background tasks / 调度后台任务的回调
            active_session_keys: Set of currently active session keys / 当前活动会话键集合
        """
        now = datetime.now()
        for info in self.sessions.list_sessions():
            key = info.get("key", "")
            if not key or key in self._archiving:
                continue
            if key in active_session_keys:
                continue
            if self._is_expired(info.get("updated_at"), now):
                self._archiving.add(key)
                schedule_background(self._archive(key))

    async def _archive(self, key: str) -> None:
        """Archive an idle session by consolidating its messages.
        
        通过整合消息来归档空闲会话。
        
        Args:
            key: Session key to archive / 要归档的会话键
        """
        try:
            self.sessions.invalidate(key)
            session = self.sessions.get_or_create(key)
            archive_msgs, kept_msgs = self._split_unconsolidated(session)
            if not archive_msgs and not kept_msgs:
                session.updated_at = datetime.now()
                self.sessions.save(session)
                return

            last_active = session.updated_at
            summary = ""
            if archive_msgs:
                summary = await self.consolidator.archive(archive_msgs) or ""
            if summary and summary != "(nothing)":
                self._summaries[key] = (summary, last_active)
                session.metadata["_last_summary"] = {"text": summary, "last_active": last_active.isoformat()}
            session.messages = kept_msgs
            session.last_consolidated = 0
            session.updated_at = datetime.now()
            self.sessions.save(session)
            if archive_msgs:
                logger.info(
                    "Auto-compact: archived {} (archived={}, kept={}, summary={})",
                    key,
                    len(archive_msgs),
                    len(kept_msgs),
                    bool(summary),
                )
        except Exception:
            logger.exception("Auto-compact: failed for {}", key)
        finally:
            self._archiving.discard(key)

    def prepare_session(self, session: Session, key: str) -> tuple[Session, str | None]:
        """Prepare a session for use, injecting summary if available.
        
        准备会话以供使用，如果有摘要则注入。
        
        Args:
            session: Session to prepare / 要准备的会话
            key: Session key / 会话键
            
        Returns:
            Tuple of (prepared session, optional summary) / (准备好的会话，可选摘要) 的元组
        """
        if key in self._archiving or self._is_expired(session.updated_at):
            logger.info("Auto-compact: reloading session {} (archiving={})", key, key in self._archiving)
            session = self.sessions.get_or_create(key)
        # Hot path: summary from in-memory dict (process hasn't restarted).
        # Also clean metadata copy so stale _last_summary never leaks to disk.
        entry = self._summaries.pop(key, None)
        if entry:
            session.metadata.pop("_last_summary", None)
            return session, self._format_summary(entry[0], entry[1])
        if "_last_summary" in session.metadata:
            meta = session.metadata.pop("_last_summary")
            self.sessions.save(session)
            return session, self._format_summary(meta["text"], datetime.fromisoformat(meta["last_active"]))
        return session, None
