"""
Convert Chat Completions messages/tools to Responses API format.
将 Chat Completions 消息/工具转换为 Responses API 格式。
"""

from __future__ import annotations

import json
from typing import Any


def convert_messages(messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    """
    Convert Chat Completions messages to Responses API input items.
    将 Chat Completions 消息转换为 Responses API 输入项。

    Returns ``(system_prompt, input_items)`` where *system_prompt* is extracted
    from any ``system`` role message and *input_items* is the Responses API
    ``input`` array.
    返回 ``(system_prompt, input_items)``，其中 *system_prompt* 从任何 ``system`` 角色消息中提取，
    *input_items* 是 Responses API 的 ``input`` 数组。
    """
    system_prompt = ""
    input_items: list[dict[str, Any]] = []

    for idx, msg in enumerate(messages):
        role = msg.get("role")
        content = msg.get("content")

        # 处理系统消息，提取系统提示词
        # Handle system messages, extract system prompt
        if role == "system":
            system_prompt = content if isinstance(content, str) else ""
            continue

        # 处理用户消息
        # Handle user messages
        if role == "user":
            input_items.append(convert_user_message(content))
            continue

        # 处理助手消息
        # Handle assistant messages
        if role == "assistant":
            if isinstance(content, str) and content:
                input_items.append({
                    "type": "message", "role": "assistant",
                    "content": [{"type": "output_text", "text": content}],
                    "status": "completed", "id": f"msg_{idx}",
                })
            # 处理工具调用
            # Handle tool calls
            for tool_call in msg.get("tool_calls", []) or []:
                fn = tool_call.get("function") or {}
                call_id, item_id = split_tool_call_id(tool_call.get("id"))
                input_items.append({
                    "type": "function_call",
                    "id": item_id or f"fc_{idx}",
                    "call_id": call_id or f"call_{idx}",
                    "name": fn.get("name"),
                    "arguments": fn.get("arguments") or "{}",
                })
            continue

        # 处理工具结果消息
        # Handle tool result messages
        if role == "tool":
            call_id, _ = split_tool_call_id(msg.get("tool_call_id"))
            output_text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
            input_items.append({"type": "function_call_output", "call_id": call_id, "output": output_text})

    return system_prompt, input_items


def convert_user_message(content: Any) -> dict[str, Any]:
    """
    Convert a user message's content to Responses API format.
    将用户消息内容转换为 Responses API 格式。

    Handles plain strings, ``text`` blocks -> ``input_text``, and
    ``image_url`` blocks -> ``input_image``.
    处理普通字符串、``text`` 块 -> ``input_text``，
    以及 ``image_url`` 块 -> ``input_image``。
    """
    if isinstance(content, str):
        return {"role": "user", "content": [{"type": "input_text", "text": content}]}
    if isinstance(content, list):
        converted: list[dict[str, Any]] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "text":
                converted.append({"type": "input_text", "text": item.get("text", "")})
            elif item.get("type") == "image_url":
                url = (item.get("image_url") or {}).get("url")
                if url:
                    converted.append({"type": "input_image", "image_url": url, "detail": "auto"})
        if converted:
            return {"role": "user", "content": converted}
    return {"role": "user", "content": [{"type": "input_text", "text": ""}]}


def convert_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Convert OpenAI function-calling tool schema to Responses API flat format.
    将 OpenAI 函数调用工具 schema 转换为 Responses API 扁平格式。
    """
    converted: list[dict[str, Any]] = []
    for tool in tools:
        fn = (tool.get("function") or {}) if tool.get("type") == "function" else tool
        name = fn.get("name")
        if not name:
            continue
        params = fn.get("parameters") or {}
        converted.append({
            "type": "function",
            "name": name,
            "description": fn.get("description") or "",
            "parameters": params if isinstance(params, dict) else {},
        })
    return converted


def split_tool_call_id(tool_call_id: Any) -> tuple[str, str | None]:
    """
    Split a compound ``call_id|item_id`` string.
    拆分复合的 ``call_id|item_id`` 字符串。

    Returns ``(call_id, item_id)`` where *item_id* may be ``None``.
    返回 ``(call_id, item_id)``，其中 *item_id* 可能为 ``None``。
    """
    if isinstance(tool_call_id, str) and tool_call_id:
        if "|" in tool_call_id:
            call_id, item_id = tool_call_id.split("|", 1)
            return call_id, item_id or None
        return tool_call_id, None
    return "call_0", None
