"""用于 /status 命令的网络搜索 provider 使用量获取模块。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class SearchUsageInfo:
    """由 provider 获取器返回的结构化使用量信息。"""

    provider: str  # 提供者名称
    supported: bool = False          # 提供者是否有使用量 API
    error: str | None = None         # API 调用失败时设置

    # 使用量计数器（None = 此提供者不可用）
    used: int | None = None
    limit: int | None = None
    remaining: int | None = None
    reset_date: str | None = None    # ISO 日期字符串，如 "2026-05-01"

    # Tavily 特定的细分
    search_used: int | None = None
    extract_used: int | None = None
    crawl_used: int | None = None

    def format(self) -> str:
        """返回用于 /status 输出的人类可读多行字符串。"""
        lines = [f"🔍 Web Search: {self.provider}"]

        if not self.supported:
            lines.append("   Usage tracking: not available for this provider")
            return "\n".join(lines)

        if self.error:
            lines.append(f"   Usage: unavailable ({self.error})")
            return "\n".join(lines)

        if self.used is not None and self.limit is not None:
            lines.append(f"   Usage: {self.used} / {self.limit} requests")
        elif self.used is not None:
            lines.append(f"   Usage: {self.used} requests")

        # Tavily breakdown
        breakdown_parts = []
        if self.search_used is not None:
            breakdown_parts.append(f"Search: {self.search_used}")
        if self.extract_used is not None:
            breakdown_parts.append(f"Extract: {self.extract_used}")
        if self.crawl_used is not None:
            breakdown_parts.append(f"Crawl: {self.crawl_used}")
        if breakdown_parts:
            lines.append(f"   Breakdown: {' | '.join(breakdown_parts)}")

        if self.remaining is not None:
            lines.append(f"   Remaining: {self.remaining} requests")

        if self.reset_date:
            lines.append(f"   Resets: {self.reset_date}")

        return "\n".join(lines)


async def fetch_search_usage(
    provider: str,
    api_key: str | None = None,
) -> SearchUsageInfo:
    """获取配置的网络搜索 provider 的使用量信息。

    参数:
        provider: Provider 名称（如 "tavily"、"brave"、"duckduckgo"）
        api_key:  Provider 的 API 密钥（回退到环境变量）

    返回:
        SearchUsageInfo，其中可用字段被填充
    """
    p = (provider or "duckduckgo").strip().lower()

    if p == "tavily":
        return await _fetch_tavily_usage(api_key)
    else:
        # brave, duckduckgo, searxng, jina, unknown — no usage API
        return SearchUsageInfo(provider=p, supported=False)


# ---------------------------------------------------------------------------
# Tavily
# ---------------------------------------------------------------------------

async def _fetch_tavily_usage(api_key: str | None) -> SearchUsageInfo:
    """从 GET https://api.tavily.com/usage 获取使用量。"""
    import httpx

    key = api_key or os.environ.get("TAVILY_API_KEY", "")
    if not key:
        return SearchUsageInfo(
            provider="tavily",
            supported=True,
            error="TAVILY_API_KEY not configured",
        )

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                "https://api.tavily.com/usage",
                headers={"Authorization": f"Bearer {key}"},
            )
            r.raise_for_status()
        data: dict[str, Any] = r.json()
        return _parse_tavily_usage(data)
    except httpx.HTTPStatusError as e:
        return SearchUsageInfo(
            provider="tavily",
            supported=True,
            error=f"HTTP {e.response.status_code}",
        )
    except Exception as e:
        return SearchUsageInfo(
            provider="tavily",
            supported=True,
            error=str(e)[:80],
        )


def _parse_tavily_usage(data: dict[str, Any]) -> SearchUsageInfo:
    """解析 Tavily /usage 响应。

    实际 API 响应结构：
    {
      "account": {
        "current_plan": "Researcher",
        "plan_usage": 20,
        "plan_limit": 1000,
        "search_usage": 20,
        "crawl_usage": 0,
        "extract_usage": 0,
        "map_usage": 0,
        "research_usage": 0,
        "paygo_usage": 0,
        "paygo_limit": null
      }
    }
    """
    account = data.get("account") or {}
    used = account.get("plan_usage")
    limit = account.get("plan_limit")

    # Compute remaining
    remaining = None
    if used is not None and limit is not None:
        remaining = max(0, limit - used)

    return SearchUsageInfo(
        provider="tavily",
        supported=True,
        used=used,
        limit=limit,
        remaining=remaining,
        search_used=account.get("search_usage"),
        extract_used=account.get("extract_usage"),
        crawl_used=account.get("crawl_usage"),
    )


