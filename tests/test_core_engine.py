#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核心执行引擎测试。

现在主实现位于标准 Python 包 `agents` 下，测试直接按包导入。
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from agents.core.agent_loop import AgentLoop, AgentState
from agents.core.base_agent import Agent
from agents.core.context_manager import ContextManager
from agents.core.tool_registry import ToolRegistry
from agents.roles.interviewer_agent import InterviewerAgent
from agents.roles.interviewer_agent import InterviewerAgent


def make_tool_call(call_id: str, name: str, arguments: dict[str, Any]) -> Any:
    """构造一个 OpenAI SDK 风格的 tool_call 对象。"""
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(
            name=name,
            arguments=json.dumps(arguments, ensure_ascii=False),
        ),
    )


class FakeCompletions:
    """假的 LLM create 接口，用于模拟多轮工具调用。"""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def create(self, **payload: Any) -> Any:
        self.calls.append(payload)
        current = len(self.calls)
        if current == 1:
            message = SimpleNamespace(
                content="我先查询候选人姓名。",
                tool_calls=[
                    make_tool_call("call-1", "greet", {"name": "小明"})
                ],
            )
        elif current == 2:
            message = SimpleNamespace(
                content="我再计算一个分数。",
                tool_calls=[
                    make_tool_call("call-2", "add", {"a": 2, "b": 3})
                ],
            )
        elif current == 3:
            message = SimpleNamespace(
                content="我最后回显观察结果。",
                tool_calls=[
                    make_tool_call("call-3", "echo", {"text": "完成"})
                ],
            )
        else:
            message = SimpleNamespace(
                content="基础对话循环已完成。",
                tool_calls=None,
            )
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeLLMClient:
    """符合 agent_loop 需要的最小 LLM 客户端。"""

    def __init__(self) -> None:
        self.completions = FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


class FakeAgent:
    """测试用 Agent，只提供配置、system prompt 和 llm_client。"""

    def __init__(self) -> None:
        self.system_prompt = "你是一个测试 Agent。"
        self.config = {
            "llm": {
                "model": "fake-model",
                "temperature": 0.1,
                "max_tokens": 200,
            }
        }
        self.llm_client = FakeLLMClient()


def test_tool_registry_registers_and_executes_tools() -> None:
    registry = ToolRegistry()

    def greet(name: str) -> str:
        """生成问候语。"""
        return f"你好，{name}"

    def add(a: int, b: int) -> int:
        return a + b

    @registry.register(name="echo")
    async def echo(text: str) -> dict[str, str]:
        return {"echo": text}

    registry.register(greet)
    registry.register(add, description="两个整数相加")

    schemas = registry.get_tool_schemas()
    names = {schema["function"]["name"] for schema in schemas}
    assert names == {"greet", "add", "echo"}

    greet_call = {
        "id": "call-1",
        "function": {
            "name": "greet",
            "arguments": '{"name": "小明"}',
        },
    }
    assert asyncio.run(registry.execute_tool(greet_call)) == "你好，小明"
    assert asyncio.run(registry.execute("add", {"a": 2, "b": 3})) == 5
    assert asyncio.run(registry.execute("echo", {"text": "ok"})) == {
        "echo": "ok"
    }


def test_agent_loop_runs_three_tool_rounds_then_final_answer() -> None:
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

    result = asyncio.run(loop.run("开始模拟面试"))

    assert result == "基础对话循环已完成。"
    assert loop.round == 4
    assert loop.state == AgentState.IDLE
    assert len(agent.llm_client.completions.calls) == 4
    assert "tools" in agent.llm_client.completions.calls[0]

    tool_messages = [
        message for message in loop.get_messages()
        if message["role"] == "tool"
    ]
    assert len(tool_messages) == 3
    assert tool_messages[0]["tool_call_id"] == "call-1"


def test_agent_loop_defaults_to_deepseek_when_model_missing() -> None:
    registry = ToolRegistry()

    @registry.register()
    def greet(name: str) -> str:
        return f"你好，{name}"

    agent = FakeAgent()
    agent.config = {"llm": {"temperature": 0.1, "max_tokens": 200}}
    loop = AgentLoop(agent=agent, tool_registry=registry, max_rounds=5)

    asyncio.run(loop.run("开始模拟面试"))

    assert agent.llm_client.completions.calls[0]["model"] == "deepseek-chat"


def test_agent_llm_config_can_be_overridden_by_environment(
    monkeypatch: Any,
) -> None:
    monkeypatch.setenv("TEST_DEEPSEEK_MODEL", "deepseek-reasoner")

    agent = Agent(
        "demo",
        config={
            "llm": {
                "model": "deepseek-chat",
                "model_env": "TEST_DEEPSEEK_MODEL",
            }
        },
    )

    assert agent.config["llm"]["model"] == "deepseek-reasoner"
    assert agent.config["llm"]["base_url"] == "https://api.deepseek.com"


def test_context_manager_compresses_old_messages() -> None:
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

    assert manager.should_compress(messages) is True
    compressed = asyncio.run(manager.compress(messages))

    assert len(compressed) == 21
    assert compressed[0]["role"] == "system"
    assert compressed[0]["content"].startswith("[早期对话摘要]")
    assert compressed[-1]["content"] == messages[-1]["content"]


def test_context_manager_skips_compression_when_under_threshold() -> None:
    manager = ContextManager(max_tokens=10_000, threshold=0.9)
    messages = [{"role": "user", "content": "短消息"}]

    result = asyncio.run(manager.compress_if_needed(messages))

    assert result == messages
    assert result is not messages


def test_legacy_harness_entrypoints_still_import() -> None:
    """旧 `.harness` 文件仍可作为兼容入口按路径导入。"""
    import importlib.util
    import sys
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[1]
    legacy_path = root_dir / ".harness" / "agents" / "agent_loop.py"
    spec = importlib.util.spec_from_file_location(
        "legacy_agent_loop_for_test",
        legacy_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["legacy_agent_loop_for_test"] = module
    spec.loader.exec_module(module)

    assert module.AgentLoop is AgentLoop


def test_interviewer_agent_standard_entrypoint_imports() -> None:
    """面试官 Agent 应该能从标准 `agents.roles` 入口导入。"""
    assert InterviewerAgent.__name__ == "InterviewerAgent"


def test_interviewer_agent_standard_entrypoint_imports() -> None:
    """面试官 Agent 应该能从标准 `agents.roles` 入口导入。"""
    assert InterviewerAgent.__name__ == "InterviewerAgent"
