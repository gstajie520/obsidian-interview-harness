#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核心执行引擎冒烟测试脚本。

运行方式：
    python scripts/test_agent_loop.py

这个脚本不用真实 LLM，而是用 Fake LLM 模拟 3 轮工具调用，适合快速确认
ToolRegistry、AgentLoop、ContextManager 三个核心模块是否能一起工作。
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.core.agent_loop import AgentLoop
from agents.core.context_manager import ContextManager
from agents.core.tool_registry import ToolRegistry


def make_tool_call(call_id: str, name: str, arguments: dict[str, Any]) -> Any:
    """构造一个和 OpenAI SDK 类似的 tool_call 对象。"""
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(
            name=name,
            arguments=json.dumps(arguments, ensure_ascii=False),
        ),
    )


class FakeCompletions:
    """模拟 chat.completions.create。"""

    def __init__(self) -> None:
        self.call_count = 0

    async def create(self, **_: Any) -> Any:
        self.call_count += 1
        if self.call_count == 1:
            message = SimpleNamespace(
                content="第 1 轮：先调用 greet。",
                tool_calls=[
                    make_tool_call("call-1", "greet", {"name": "候选人"})
                ],
            )
        elif self.call_count == 2:
            message = SimpleNamespace(
                content="第 2 轮：计算 2 + 3。",
                tool_calls=[make_tool_call("call-2", "add", {"a": 2, "b": 3})],
            )
        elif self.call_count == 3:
            message = SimpleNamespace(
                content="第 3 轮：回显工具观察结果。",
                tool_calls=[
                    make_tool_call("call-3", "echo", {"text": "观察完成"})
                ],
            )
        else:
            message = SimpleNamespace(
                content="模拟对话完成，Agent Loop 可以返回最终答案。",
                tool_calls=None,
            )
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeLLMClient:
    """AgentLoop 需要的最小 LLM 客户端结构。"""

    def __init__(self) -> None:
        self.completions = FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


class FakeAgent:
    """冒烟测试用 Agent。"""

    def __init__(self) -> None:
        self.system_prompt = "你是一个用于冒烟测试的面试助手。"
        self.config = {
            "llm": {
                "model": "fake-model",
                "temperature": 0.1,
                "max_tokens": 200,
            }
        }
        self.llm_client = FakeLLMClient()


async def test_tool_registry() -> None:
    """验证注册工具、生成 schema、执行同步/异步工具。"""
    registry = ToolRegistry()

    @registry.register()
    def greet(name: str) -> str:
        return f"你好，{name}"

    @registry.register(description="两个整数相加")
    def add(a: int, b: int) -> int:
        return a + b

    @registry.register()
    async def echo(text: str) -> dict[str, str]:
        return {"echo": text}

    schemas = registry.get_tool_schemas()
    assert len(schemas) == 3
    assert await registry.execute("add", {"a": 2, "b": 3}) == 5
    assert await registry.execute("echo", {"text": "ok"}) == {"echo": "ok"}
    print("[通过] ToolRegistry 注册和执行")


async def test_agent_loop() -> None:
    """验证 AgentLoop 能跑完 3 轮工具调用并返回最终答案。"""
    registry = ToolRegistry()

    @registry.register()
    def greet(name: str) -> str:
        return f"你好，{name}"

    @registry.register()
    def add(a: int, b: int) -> int:
        return a + b

    @registry.register()
    async def echo(text: str) -> str:
        return text

    agent = FakeAgent()
    loop = AgentLoop(agent=agent, tool_registry=registry, max_rounds=5)
    result = await loop.run("开始一次模拟面试")

    assert result.endswith("最终答案。")
    assert loop.round == 4
    assert len([m for m in loop.messages if m["role"] == "tool"]) == 3
    print("[通过] AgentLoop 3 轮工具调用")


async def test_context_manager() -> None:
    """验证上下文压缩会保留最近 10 轮并摘要旧消息。"""
    manager = ContextManager(
        max_tokens=120,
        threshold=0.5,
        retain_recent_rounds=10,
    )
    messages = [
        {
            "role": "user" if index % 2 == 0 else "assistant",
            "content": f"第 {index} 条消息 " + ("内容 " * 20),
        }
        for index in range(30)
    ]

    assert manager.should_compress(messages)
    compressed = await manager.compress(messages)
    assert len(compressed) == 21
    assert compressed[0]["content"].startswith("[早期对话摘要]")
    print("[通过] ContextManager 上下文压缩")


async def main() -> None:
    print("=" * 60)
    print("Agent Harness 核心执行引擎冒烟测试")
    print("=" * 60)
    await test_tool_registry()
    await test_agent_loop()
    await test_context_manager()
    print("=" * 60)
    print("全部冒烟测试通过")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
