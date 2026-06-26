#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工具注册表：把普通 Python 函数变成 LLM 可以调用的工具。

这层代码负责三件事：
1. 注册工具函数，并保存工具的名称、说明和参数 Schema。
2. 生成 OpenAI function calling 需要的 `tools` 格式。
3. 收到 LLM 的 tool_call 后，解析参数并真正执行 Python 函数。

初学者可以把它理解成“工具电话簿”：LLM 只知道工具名和参数格式，
真正执行工具的是这里的 `execute_tool()`。
"""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional, Union
from typing import get_args, get_origin


# 这里用别名减少重复书写。可以把 JsonDict 理解成 Java 里的
# `Map<String, Object>`，只是 Python 写法更轻量。
JsonDict = Dict[str, Any]
ToolFunction = Callable[..., Any]


class ToolRegistryError(Exception):
    """工具注册表的基础异常。"""


class ToolArgumentError(ToolRegistryError):
    """当 LLM 传来的工具参数格式不正确时抛出。"""


@dataclass(frozen=True)
class ToolCallRequest:
    """统一后的工具调用请求。

    OpenAI SDK 可能返回对象，也可能在测试里使用 dict。为了后续执行简单，
    我们先把它们统一成这个结构。

    `@dataclass` 类似 Java 的 Lombok `@Data` / record：Python 会自动生成
    `__init__`、`__repr__` 等方法。`frozen=True` 表示创建后不建议再修改，
    类似 Java 里不可变对象的思路。
    """

    name: str
    arguments: JsonDict
    call_id: Optional[str] = None


@dataclass(frozen=True)
class RegisteredTool:
    """一个已注册工具的完整信息。"""

    name: str
    description: str
    parameters: JsonDict
    function: ToolFunction

    def to_openai_schema(self) -> JsonDict:
        """转换成 OpenAI function calling 需要的工具格式。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """工具注册与执行入口。"""

    def __init__(self) -> None:
        # 前面的下划线表示“内部字段”。Python 不强制 private，但约定外部
        # 不要直接改它；需要读取时通过下面的 `tools` property。
        self._tools: Dict[str, RegisteredTool] = {}

    @property
    def tools(self) -> Dict[str, RegisteredTool]:
        """返回已注册工具的副本，避免外部直接改内部状态。

        `@property` 让调用方可以写 `registry.tools`，效果像访问字段；
        但内部仍然可以执行函数逻辑。这和 Java 的 getter 思路接近。
        """
        return dict(self._tools)

    def register(
        self,
        func: Optional[ToolFunction] = None,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[JsonDict] = None,
    ) -> Union[ToolFunction, Callable[[ToolFunction], ToolFunction]]:
        """注册一个工具，支持两种写法。

        写法一：`registry.register(func, name="xxx", parameters={...})`
        写法二：`@registry.register(name="xxx")`

        如果没有手写 `parameters`，会根据函数签名自动生成一个基础 Schema。
        """
        if func is None:
            # 当 register 被当作装饰器使用时，Python 会先执行这里，返回一个
            # decorator 函数；随后再把真正被装饰的函数传给 decorator。
            # Java 里没有完全一样的语法，可以把它理解成“注册回调函数”。

            def decorator(target: ToolFunction) -> ToolFunction:
                self.register(
                    target,
                    name=name,
                    description=description,
                    parameters=parameters,
                )
                return target

            return decorator

        tool_name = name or func.__name__
        self._validate_tool_name(tool_name)

        # Python 的 `or` 常用来做默认值选择：左边有值就用左边，否则用右边。
        tool_description = (
            description
            or inspect.getdoc(func)
            or f"执行工具 {tool_name}。"
        )
        tool_parameters = parameters or self._schema_from_signature(func)
        if not isinstance(tool_parameters, dict):
            raise ValueError("parameters 必须是 JSON Schema 字典")

        self._tools[tool_name] = RegisteredTool(
            name=tool_name,
            description=tool_description,
            parameters=tool_parameters,
            function=func,
        )
        return func

    def unregister(self, name: str) -> None:
        """移除一个工具；不存在时不报错。"""
        self._tools.pop(name, None)

    def get_tool_schemas(self) -> list[JsonDict]:
        """返回所有工具的 OpenAI function calling Schema。"""
        return [tool.to_openai_schema() for tool in self._tools.values()]

    async def execute_tool(self, tool_call: Any) -> Any:
        """执行 LLM 发出的 tool_call。

        这里不把解析错误继续抛给外层，而是返回 `{"error": "..."}`
        作为工具执行结果。这样 Agent Loop 可以把错误反馈给 LLM 继续修正。
        """
        try:
            request = self.parse_tool_call(tool_call)
            return await self.execute(request.name, request.arguments)
        except ToolRegistryError as exc:
            return {"error": str(exc)}

    async def execute(
        self,
        name: str,
        arguments: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """按工具名执行已注册的 Python 函数。"""
        if name not in self._tools:
            return {"error": f"工具不存在: {name}"}

        tool = self._tools[name]
        # Mapping 是“只要求像 dict 一样能读”的类型。这里转成真正的 dict，
        # 后面才能用 `**kwargs` 展开成函数参数。
        kwargs = dict(arguments or {})
        try:
            # `func(**kwargs)` 表示把字典展开为关键字参数：
            # {"limit": 5} 会变成 func(limit=5)。
            result = tool.function(**kwargs)
            if inspect.isawaitable(result):
                # 工具可以是普通函数，也可以是 async 函数；如果返回值可 await，
                # 就等待它完成。这样注册方不用关心工具是同步还是异步。
                result = await result
            return result
        except Exception as exc:
            return {"error": f"工具 {name} 执行失败: {exc}"}

    def parse_tool_call(self, tool_call: Any) -> ToolCallRequest:
        """把 OpenAI SDK 对象或 dict 统一解析成 ToolCallRequest。"""
        # OpenAI SDK 返回的是对象，测试代码经常用 dict。统一读字段可以减少
        # 后续分支判断。
        call_id = self._read_value(tool_call, "id")
        function = self._read_value(tool_call, "function")
        if function is None:
            raise ToolArgumentError("tool_call.function 不能为空")

        name = self._read_value(function, "name")
        raw_arguments = self._read_value(function, "arguments", default={})
        if not name:
            raise ToolArgumentError("tool_call.function.name 不能为空")

        return ToolCallRequest(
            name=str(name),
            arguments=self._parse_arguments(raw_arguments),
            call_id=str(call_id) if call_id else None,
        )

    def has_tool(self, name: str) -> bool:
        """判断某个工具名是否已经注册。"""
        return name in self._tools

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and self.has_tool(name)

    @staticmethod
    def _read_value(
        source: Any,
        key: str,
        default: Any = None,
    ) -> Any:
        """同时支持从 dict 和对象属性读取字段。

        `@staticmethod` 表示这个方法不需要访问 `self`，只是放在类里做归类。
        """
        if isinstance(source, Mapping):
            return source.get(key, default)
        return getattr(source, key, default)

    @staticmethod
    def _parse_arguments(raw_arguments: Any) -> JsonDict:
        """解析 LLM 传来的工具参数。

        OpenAI 的 `function.arguments` 通常是 JSON 字符串；测试或本地调用
        也可能直接传 dict。这里统一转换为 dict。
        """
        if raw_arguments in (None, ""):
            return {}
        if isinstance(raw_arguments, Mapping):
            return dict(raw_arguments)
        if isinstance(raw_arguments, str):
            try:
                parsed = json.loads(raw_arguments)
            except json.JSONDecodeError as exc:
                raise ToolArgumentError(
                    f"工具参数不是合法 JSON: {raw_arguments}"
                ) from exc
            if not isinstance(parsed, dict):
                raise ToolArgumentError("工具参数必须是 JSON 对象")
            return parsed
        raise ToolArgumentError("工具参数必须是 dict 或 JSON 对象字符串")

    @staticmethod
    def _validate_tool_name(name: str) -> None:
        """校验工具名，避免传给 OpenAI 时被拒绝。"""
        if not name:
            raise ValueError("工具名不能为空")
        allowed = set(
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789_-"
        )
        if any(char not in allowed for char in name):
            raise ValueError("工具名只能包含字母、数字、下划线和短横线")

    @classmethod
    def _schema_from_signature(cls, func: ToolFunction) -> JsonDict:
        """根据函数参数自动生成最小可用的 JSON Schema。

        `inspect.signature()` 是 Python 的反射能力，类似 Java 反射读取方法
        参数。这里用它把函数签名转换成 LLM 能理解的参数 Schema。
        """
        signature = inspect.signature(func)
        properties: JsonDict = {}
        required: list[str] = []

        for param_name, param in signature.parameters.items():
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue
            properties[param_name] = cls._annotation_to_schema(
                param.annotation
            )
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        schema: JsonDict = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        return schema

    @classmethod
    def _annotation_to_schema(cls, annotation: Any) -> JsonDict:
        """把常见 Python 类型标注转换为 JSON Schema 类型。"""
        if annotation is inspect.Parameter.empty:
            return {"type": "string"}

        origin = get_origin(annotation)
        args = get_args(annotation)
        if origin is Union:
            non_none_args = [arg for arg in args if arg is not type(None)]
            if len(non_none_args) == 1:
                return cls._annotation_to_schema(non_none_args[0])

        if origin in (list, tuple, set):
            return {"type": "array"}
        if origin in (dict, Mapping):
            return {"type": "object"}

        mapping = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            dict: "object",
            list: "array",
        }
        return {"type": mapping.get(annotation, "string")}
