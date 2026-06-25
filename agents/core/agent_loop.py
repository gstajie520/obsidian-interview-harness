#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agent Loop：执行 Think -> Act -> Observe -> Reflect 循环。

TAOR 可以理解成一个会反复工作的“面试助手主循环”：
- Think：把消息历史和工具列表发给 LLM，让它决定下一步。
- Act：如果 LLM 要调用工具，就记录这次工具调用。
- Observe：真正执行工具，并把工具结果写回消息历史。
- Reflect：如果 LLM 不再调用工具，就返回最终回复。

本模块只负责“循环和消息流转”，不关心具体工具怎么实现。
具体工具由 `ToolRegistry` 执行。
"""

from __future__ import annotations

import inspect
import json
from enum import Enum
from typing import Any, Dict, Mapping, Optional


JsonDict = Dict[str, Any]
DEFAULT_LLM_MODEL = "deepseek-chat"


class AgentState(str, Enum):
    """Agent Loop 当前所处的状态。"""

    IDLE = "IDLE"
    THINKING = "THINKING"
    EXECUTING = "EXECUTING"
    OBSERVING = "OBSERVING"


class AgentLoop:
    """运行一个完整的 TAOR 循环。"""

    def __init__(
        self,
        agent: Any,
        tool_registry: Any,
        max_rounds: int = 30,
        context_manager: Optional[Any] = None,
    ) -> None:
        if max_rounds <= 0:
            raise ValueError("max_rounds 必须大于 0")

        self.agent = agent
        self.tool_registry = tool_registry
        self.max_rounds = max_rounds
        self.context_manager = context_manager
        self.round = 0
        self.messages: list[JsonDict] = []
        self.state = AgentState.IDLE

    async def run(self, user_input: str) -> str:
        """处理一次用户输入，并返回最终回复文本。

        注意：一次 `run()` 里可能会调用多轮 LLM，因为 LLM 可能先调用工具，
        再根据工具结果继续思考。
        """
        self.round = 0
        self.add_message("user", user_input)

        while not self.should_exit():
            self.round += 1

            # Think：先让 LLM 根据当前消息历史决定下一步。
            self.state = AgentState.THINKING
            await self._compress_messages_if_needed()
            response = await self._call_llm()
            message = self._extract_message(response)
            tool_calls = self._get_tool_calls(message)

            if tool_calls:
                # Act：LLM 选择调用工具时，先把 assistant 的 tool_calls 记下来。
                self.state = AgentState.EXECUTING
                self.messages.append(self._assistant_tool_message(message))

                # Observe：执行每个工具，再把工具结果作为 tool 消息写回历史。
                self.state = AgentState.OBSERVING
                for tool_call in tool_calls:
                    result = await self.tool_registry.execute_tool(tool_call)
                    self.messages.append(
                        self._tool_result_message(tool_call, result)
                    )
                continue

            # Reflect：没有工具调用，说明 LLM 已经给出最终回答。
            final_content = self._get_value(message, "content", default="")
            self.add_message("assistant", str(final_content or ""))
            self.state = AgentState.IDLE
            return str(final_content or "")

        self.state = AgentState.IDLE
        return f"已达到最大轮数 {self.max_rounds}，任务尚未完成。"

    def add_message(self, role: str, content: str) -> None:
        """向消息历史追加一条普通对话消息。"""
        self.messages.append({"role": role, "content": content})

    def clear_messages(self) -> None:
        """清空当前循环保存的消息历史。"""
        self.messages = []
        self.round = 0
        self.state = AgentState.IDLE

    def should_exit(self) -> bool:
        """判断是否已经用完本次 run 的最大轮数。"""
        return self.round >= self.max_rounds

    def get_messages(self) -> list[JsonDict]:
        """返回消息历史副本，方便测试或调试。"""
        return [dict(message) for message in self.messages]

    async def _compress_messages_if_needed(self) -> None:
        """如果上下文快超限，就调用 ContextManager 压缩早期消息。"""
        if self.context_manager is None:
            return
        self.messages = await self.context_manager.compress_if_needed(
            self.messages,
            self._llm_client(),
        )

    async def _call_llm(self) -> Any:
        """调用 OpenAI 兼容的 chat.completions.create 接口。"""
        client = self._llm_client()
        create = client.chat.completions.create
        config = getattr(self.agent, "config", {}) or {}
        llm_config = config.get("llm", {})

        payload: JsonDict = {
            "model": llm_config.get("model") or DEFAULT_LLM_MODEL,
            "messages": self._build_llm_messages(),
            "temperature": llm_config.get("temperature", 0.7),
            "max_tokens": llm_config.get("max_tokens", 2000),
        }

        tool_schemas = self.tool_registry.get_tool_schemas()
        if tool_schemas:
            payload["tools"] = tool_schemas

        response = create(**payload)
        if inspect.isawaitable(response):
            response = await response
        return response

    def _llm_client(self) -> Any:
        """取出 agent 上的 LLM 客户端。"""
        client = getattr(self.agent, "llm_client", None)
        if client is None:
            raise ValueError("agent.llm_client 不能为空")
        return client

    def _build_llm_messages(self) -> list[JsonDict]:
        """拼接 system prompt 和已有消息历史。"""
        system_prompt = getattr(self.agent, "system_prompt", "")
        if not system_prompt:
            return list(self.messages)
        return [{"role": "system", "content": system_prompt}, *self.messages]

    @classmethod
    def _extract_message(cls, response: Any) -> Any:
        """兼容 dict、字符串和 OpenAI SDK 对象三种响应形态。"""
        if isinstance(response, str):
            return {"role": "assistant", "content": response}
        if isinstance(response, Mapping):
            choices = response.get("choices", [])
            if choices:
                choice = choices[0]
                if isinstance(choice, Mapping):
                    return choice.get("message", {})
                return getattr(choice, "message", {})
            return response

        choices = getattr(response, "choices", [])
        if choices:
            return getattr(choices[0], "message", None)
        return response

    @classmethod
    def _get_tool_calls(cls, message: Any) -> list[Any]:
        """从 assistant message 中取出工具调用列表。"""
        tool_calls = cls._get_value(message, "tool_calls", default=None)
        return list(tool_calls or [])

    @classmethod
    def _assistant_tool_message(cls, message: Any) -> JsonDict:
        """把 assistant 的工具调用转成可保存的 dict。"""
        return {
            "role": "assistant",
            "content": cls._get_value(message, "content", default=""),
            "tool_calls": [
                cls._tool_call_to_dict(call)
                for call in cls._get_tool_calls(message)
            ],
        }

    @classmethod
    def _tool_result_message(cls, tool_call: Any, result: Any) -> JsonDict:
        """把工具执行结果包装成 OpenAI 约定的 tool 消息。"""
        return {
            "role": "tool",
            "tool_call_id": str(cls._get_value(tool_call, "id", "")),
            "content": cls._serialize_tool_result(result),
        }

    @classmethod
    def _tool_call_to_dict(cls, tool_call: Any) -> JsonDict:
        """把 SDK 对象形式的 tool_call 转成普通 dict，便于保存历史。"""
        function = cls._get_value(tool_call, "function", default={})
        return {
            "id": cls._get_value(tool_call, "id", default=""),
            "type": cls._get_value(tool_call, "type", default="function"),
            "function": {
                "name": cls._get_value(function, "name", default=""),
                "arguments": cls._get_value(
                    function,
                    "arguments",
                    default="{}",
                ),
            },
        }

    @staticmethod
    def _serialize_tool_result(result: Any) -> str:
        """工具结果必须作为字符串放进消息历史。"""
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False)

    @staticmethod
    def _get_value(source: Any, key: str, default: Any = None) -> Any:
        """同时支持从 dict 和对象属性读取字段。"""
        if isinstance(source, Mapping):
            return source.get(key, default)
        return getattr(source, key, default)
