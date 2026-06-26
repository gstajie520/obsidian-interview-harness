#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""上下文管理：统计 token，并在接近模型上限时压缩旧对话。

LLM 每次请求都有上下文长度限制。面试练习时间一长，消息历史会越来越大。
本模块的职责是：
1. 估算当前消息历史占用了多少 token。
2. 超过阈值时触发压缩，默认阈值是 92%。
3. 保留最近 10 轮完整对话，把更早的内容压缩成一条摘要。
"""

from __future__ import annotations

import inspect
import json
from typing import Any, Dict, Iterable, Mapping, Optional


JsonDict = Dict[str, Any]
DEFAULT_TOKENIZER_MODEL = "deepseek-chat"


class _FallbackEncoding:
    """tiktoken 不可用时的兜底编码器。

    它按字符计数，结果会比真实 token 粗糙，但能保证代码离线可运行。
    """

    @staticmethod
    def encode(text: str) -> list[str]:
        return list(text)


class ContextManager:
    """负责 token 统计和上下文压缩。"""

    def __init__(
        self,
        max_tokens: int = 128_000,
        threshold: float = 0.92,
        model: str = DEFAULT_TOKENIZER_MODEL,
        retain_recent_rounds: int = 10,
        summary_model: Optional[str] = None,
    ) -> None:
        if max_tokens <= 0:
            raise ValueError("max_tokens 必须大于 0")
        if not 0 < threshold <= 1:
            raise ValueError("threshold 必须在 (0, 1] 范围内")
        if retain_recent_rounds <= 0:
            raise ValueError("retain_recent_rounds 必须大于 0")

        # 这些字段都是普通实例属性。Python 不需要提前声明成员变量类型，
        # 但通过上面的函数签名已经给出了类型提示。
        self.max_tokens = max_tokens
        self.threshold = threshold
        self.model = model
        self.retain_recent_rounds = retain_recent_rounds
        self.summary_model = summary_model or model
        self.encoding = self._load_encoding(model)

    def count_tokens(self, messages: Iterable[Mapping[str, Any]]) -> int:
        """估算一组 chat messages 的 token 数量。"""
        total = 0
        # Iterable 表示“能被 for 循环遍历的对象”，可以是 list、tuple，
        # 也可以是生成器。这里不要求一定传 list。
        for message in messages:
            # ChatML 每条消息有少量结构开销，这里用 4 做近似值。
            total += 4
            total += self._count_text(str(message.get("role", "")))
            total += self._count_text(str(message.get("name", "")))
            total += self._count_text(
                self._stringify(message.get("content", ""))
            )

            if "tool_calls" in message:
                total += self._count_text(
                    json.dumps(message["tool_calls"], ensure_ascii=False)
                )

        return total

    def usage_rate(self, messages: Iterable[Mapping[str, Any]]) -> float:
        """返回当前上下文使用率，例如 0.92 表示用了 92%。"""
        return self.count_tokens(messages) / self.max_tokens

    def should_compress(self, messages: Iterable[Mapping[str, Any]]) -> bool:
        """判断是否需要压缩上下文。"""
        return self.usage_rate(messages) >= self.threshold

    async def compress_if_needed(
        self,
        messages: list[JsonDict],
        llm_client: Optional[Any] = None,
    ) -> list[JsonDict]:
        """超过阈值才压缩；没超过就原样返回副本。"""
        if not self.should_compress(messages):
            return list(messages)
        return await self.compress(messages, llm_client)

    async def compress(
        self,
        messages: list[JsonDict],
        llm_client: Optional[Any] = None,
    ) -> list[JsonDict]:
        """压缩旧消息，并保留最近几轮完整对话。

        `retain_recent_rounds=10` 时，会保留最近 20 条消息。因为一轮对话
        通常包含 user 和 assistant 两条消息；工具调用时会更多，但这个近似
        足够支撑 MVP。
        """
        retain_count = self.retain_recent_rounds * 2
        if len(messages) <= retain_count:
            return list(messages)

        # Python 切片语法：
        # messages[:-retain_count] 取前面的旧消息；
        # messages[-retain_count:] 取最后 retain_count 条消息。
        old_messages = messages[:-retain_count]
        recent_messages = messages[-retain_count:]
        summary = await self._summarize(old_messages, llm_client)
        summary_message = {
            "role": "system",
            "content": f"[早期对话摘要] {summary}",
        }
        return [summary_message] + list(recent_messages)

    async def _summarize(
        self,
        messages: list[JsonDict],
        llm_client: Optional[Any],
    ) -> str:
        """优先用 LLM 摘要；不可用时使用本地摘要兜底。"""
        if llm_client is None:
            return self._local_summary(messages)

        prompt = (
            "请把下面的面试练习对话压缩成 200 字以内的中文摘要。"
            "保留薄弱点、工具结果、未完成任务和重要结论。\n\n"
            f"{json.dumps(messages, ensure_ascii=False)}"
        )

        try:
            if hasattr(llm_client, "summarize"):
                # 测试或自定义客户端可以提供 summarize 方法，避免强依赖
                # OpenAI SDK 的完整响应格式。
                result = llm_client.summarize(prompt)
                if inspect.isawaitable(result):
                    result = await result
                return str(result)

            create = llm_client.chat.completions.create
            response = create(
                model=self.summary_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )
            if inspect.isawaitable(response):
                response = await response
            return self._extract_message_content(response)
        except Exception:
            # 摘要失败时不能让整个面试中断，所以退回到本地摘要。
            return self._local_summary(messages)

    @staticmethod
    def _extract_message_content(response: Any) -> str:
        """从 OpenAI 兼容响应里取出 assistant 文本。"""
        if isinstance(response, Mapping):
            choices = response.get("choices", [])
            if choices:
                choice = choices[0]
                if isinstance(choice, Mapping):
                    message = choice.get("message", {})
                    return str(message.get("content", ""))
                message = getattr(choice, "message", None)
                return str(getattr(message, "content", ""))
            return ""

        choices = getattr(response, "choices", [])
        if choices:
            message = getattr(choices[0], "message", None)
            return str(getattr(message, "content", ""))
        return ""

    def _count_text(self, text: str) -> int:
        return len(self.encoding.encode(text))

    @staticmethod
    def _stringify(value: Any) -> str:
        """把任意消息内容转成字符串，便于统一统计 token。"""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        # 非字符串内容可能是 dict/list，转 JSON 能保留结构信息。
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _local_summary(messages: list[JsonDict]) -> str:
        """没有 LLM 时，用前几条消息拼出一个简单摘要。"""
        snippets = []
        for message in messages[:8]:
            role = message.get("role", "unknown")
            content = ContextManager._stringify(message.get("content", ""))
            snippets.append(f"{role}: {content[:120]}")

        summary = "；".join(snippets)
        if len(messages) > 8:
            summary += f"；另有 {len(messages) - 8} 条早期消息已省略"
        return summary[:800]

    @staticmethod
    def _load_encoding(model: str) -> Any:
        """加载 tiktoken 编码器，失败时使用本地兜底。"""
        try:
            import tiktoken

            try:
                return tiktoken.encoding_for_model(model)
            except KeyError:
                return tiktoken.get_encoding("cl100k_base")
        except Exception:
            return _FallbackEncoding()
