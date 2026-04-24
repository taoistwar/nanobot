"""JSON Schema fragment types: all subclass :class:`~nanobot.agent.tools.base.Schema` for descriptions and constraints on tool parameters.
// JSON Schema 片段类型：全部继承自 nanobot.agent.tools.base.Schema，用于描述和约束工具参数。

- ``to_json_schema()``: returns a dict compatible with :meth:`~nanobot.agent.tools.base.Schema.validate_json_schema_value` /
  :class:`~nanobot.agent.tools.base.Tool`.
  // 返回与 validate_json_schema_value / Tool 兼容的字典。
- ``validate_value(value, path)``: validates a single value against this schema; returns a list of error messages (empty means valid).
  // 根据此 schema 验证单个值；返回错误消息列表（空意味着有效）。

Shared validation and fragment normalization are on the class methods of :class:`~nanobot.agent.tools.base.Schema`.
// 共享验证和片段规范化在 nanobot.agent.tools.base.Schema 的类方法中。

Note: Python does not allow subclassing ``bool``, so booleans use :class:`BooleanSchema`.
// 注意：Python 不允许子类化 bool，所以布尔值使用 BooleanSchema。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from nanobot.agent.tools.base import Schema


class StringSchema(Schema):
    """String parameter: ``description`` documents the field; optional length bounds and enum.
    // 字符串参数：description 记录字段；可选长度限制和枚举。
    """

    def __init__(
        self,
        description: str = "",
        *,
        min_length: int | None = None,
        max_length: int | None = None,
        enum: tuple[Any, ...] | list[Any] | None = None,
        nullable: bool = False,
    ) -> None:
        self._description = description
        self._min_length = min_length
        self._max_length = max_length
        self._enum = tuple(enum) if enum is not None else None
        self._nullable = nullable

    def to_json_schema(self) -> dict[str, Any]:
        t: Any = "string"
        if self._nullable:
            t = ["string", "null"]
        d: dict[str, Any] = {"type": t}
        if self._description:
            d["description"] = self._description
        if self._min_length is not None:
            d["minLength"] = self._min_length
        if self._max_length is not None:
            d["maxLength"] = self._max_length
        if self._enum is not None:
            d["enum"] = list(self._enum)
        return d


class IntegerSchema(Schema):
    """Integer parameter: optional placeholder int (legacy ctor signature), description, and bounds.
    // 整数参数：可选的占位符 int（旧构造函数签名）、描述和边界。
    """

    def __init__(
        self,
        value: int = 0,
        *,
        description: str = "",
        minimum: int | None = None,
        maximum: int | None = None,
        enum: tuple[int, ...] | list[int] | None = None,
        nullable: bool = False,
    ) -> None:
        self._value = value
        self._description = description
        self._minimum = minimum
        self._maximum = maximum
        self._enum = tuple(enum) if enum is not None else None
        self._nullable = nullable

    def to_json_schema(self) -> dict[str, Any]:
        t: Any = "integer"
        if self._nullable:
            t = ["integer", "null"]
        d: dict[str, Any] = {"type": t}
        if self._description:
            d["description"] = self._description
        if self._minimum is not None:
            d["minimum"] = self._minimum
        if self._maximum is not None:
            d["maximum"] = self._maximum
        if self._enum is not None:
            d["enum"] = list(self._enum)
        return d


class NumberSchema(Schema):
    """Numeric parameter (JSON number): description and optional bounds.
    // 数字参数（JSON 数字）：描述和可选边界。
    """

    def __init__(
        self,
        value: float = 0.0,
        *,
        description: str = "",
        minimum: float | None = None,
        maximum: float | None = None,
        enum: tuple[float, ...] | list[float] | None = None,
        nullable: bool = False,
    ) -> None:
        self._value = value
        self._description = description
        self._minimum = minimum
        self._maximum = maximum
        self._enum = tuple(enum) if enum is not None else None
        self._nullable = nullable

    def to_json_schema(self) -> dict[str, Any]:
        t: Any = "number"
        if self._nullable:
            t = ["number", "null"]
        d: dict[str, Any] = {"type": t}
        if self._description:
            d["description"] = self._description
        if self._minimum is not None:
            d["minimum"] = self._minimum
        if self._maximum is not None:
            d["maximum"] = self._maximum
        if self._enum is not None:
            d["enum"] = list(self._enum)
        return d


class BooleanSchema(Schema):
    """Boolean parameter (standalone class because Python forbids subclassing ``bool``).
    // 布尔参数（独立类，因为 Python 禁止子类化 bool）。
    """

    def __init__(
        self,
        *,
        description: str = "",
        default: bool | None = None,
        nullable: bool = False,
    ) -> None:
        self._description = description
        self._default = default
        self._nullable = nullable

    def to_json_schema(self) -> dict[str, Any]:
        t: Any = "boolean"
        if self._nullable:
            t = ["boolean", "null"]
        d: dict[str, Any] = {"type": t}
        if self._description:
            d["description"] = self._description
        if self._default is not None:
            d["default"] = self._default
        return d


class ArraySchema(Schema):
    """Array parameter: element schema is given by ``items``.
    // 数组参数：元素 schema 由 items 指定。
    """

    def __init__(
        self,
        items: Any | None = None,
        *,
        description: str = "",
        min_items: int | None = None,
        max_items: int | None = None,
        nullable: bool = False,
    ) -> None:
        self._items_schema: Any = items if items is not None else StringSchema("")
        self._description = description
        self._min_items = min_items
        self._max_items = max_items
        self._nullable = nullable

    def to_json_schema(self) -> dict[str, Any]:
        t: Any = "array"
        if self._nullable:
            t = ["array", "null"]
        d: dict[str, Any] = {
            "type": t,
            "items": Schema.fragment(self._items_schema),
        }
        if self._description:
            d["description"] = self._description
        if self._min_items is not None:
            d["minItems"] = self._min_items
        if self._max_items is not None:
            d["maxItems"] = self._max_items
        return d


class ObjectSchema(Schema):
    """Object parameter: ``properties`` or keyword args are field names; values are child Schema or JSON Schema dicts.
    // 对象参数：properties 或关键字参数是字段名；值是子 Schema 或 JSON Schema 字典。
    """

    def __init__(
        self,
        properties: Mapping[str, Any] | None = None,
        *,
        required: list[str] | None = None,
        description: str = "",
        additional_properties: bool | dict[str, Any] | None = None,
        nullable: bool = False,
        **kwargs: Any,
    ) -> None:
        self._properties = dict(properties or {}, **kwargs)
        self._required = list(required or [])
        self._root_description = description
        self._additional_properties = additional_properties
        self._nullable = nullable

    def to_json_schema(self) -> dict[str, Any]:
        t: Any = "object"
        if self._nullable:
            t = ["object", "null"]
        props = {k: Schema.fragment(v) for k, v in self._properties.items()}
        out: dict[str, Any] = {"type": t, "properties": props}
        if self._required:
            out["required"] = self._required
        if self._root_description:
            out["description"] = self._root_description
        if self._additional_properties is not None:
            out["additionalProperties"] = self._additional_properties
        return out


def tool_parameters_schema(
    *,
    required: list[str] | None = None,
    description: str = "",
    **properties: Any,
) -> dict[str, Any]:
    """Build root tool parameters ``{"type": "object", "properties": ...}`` for :meth:`Tool.parameters`.
    // 构建工具根参数 {"type": "object", "properties": ...} 用于 Tool.parameters。"""
    return ObjectSchema(
        required=required,
        description=description,
        **properties,
    ).to_json_schema()
