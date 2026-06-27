#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""面试官 MVP 闭环测试。"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from agents.roles.interviewer_agent import InterviewerAgent
from agents.tools import memory_tools, question_tools


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


class InterviewFlowCompletions:
    """模拟一次抽题、作答、保存评分的 LLM 调用序列。"""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def create(self, **payload: Any) -> Any:
        self.calls.append(payload)
        current = len(self.calls)

        if current == 1:
            message = SimpleNamespace(
                content="先查询薄弱模块。",
                tool_calls=[
                    make_tool_call("call-1", "get_weak_modules", {"limit": 5})
                ],
            )
        elif current == 2:
            message = SimpleNamespace(
                content="没有历史记录，随机抽一道题。",
                tool_calls=[
                    make_tool_call("call-2", "get_question_from_module", {})
                ],
            )
        elif current == 3:
            message = SimpleNamespace(
                content="请回答：HashMap 的底层结构是什么？",
                tool_calls=None,
            )
        elif current == 4:
            message = SimpleNamespace(
                content="保存本轮评分。",
                tool_calls=[
                    make_tool_call(
                        "call-3",
                        "save_evaluation",
                        {
                            "question_id": "hashmap-basic",
                            "user_answer": "数组、链表和红黑树。",
                            "score_accuracy": 4,
                            "score_completeness": 3,
                            "score_depth": 3,
                            "score_scenario": 2,
                            "weak_points": "场景化不足",
                        },
                    )
                ],
            )
        else:
            message = SimpleNamespace(
                content="本轮评分已保存，建议补充 HashMap 使用场景。",
                tool_calls=None,
            )

        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class InterviewFlowLLMClient:
    """InterviewerAgent 可使用的最小假 LLM 客户端。"""

    def __init__(self) -> None:
        self.completions = InterviewFlowCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


@pytest.fixture()
def isolated_interviewer_environment(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    """隔离题库和数据库，避免测试污染真实数据。"""
    monkeypatch.setattr(memory_tools, "_DIALECT", "sqlite")
    monkeypatch.setattr(memory_tools, "_INSERT_IGNORE", "INSERT OR IGNORE")
    monkeypatch.setattr(memory_tools, "_TODAY", "DATE('now')")
    monkeypatch.setattr(memory_tools, "SQLITE_PATH", tmp_path / "learning.db")

    module_dir = tmp_path / "knowledge" / "Java基础"
    module_dir.mkdir(parents=True)
    (module_dir / "HashMap.md").write_text(
        "\n".join(
            [
                "---",
                "question_id: hashmap-basic",
                "---",
                "HashMap 的底层结构是什么？",
                "",
                "## 典型回答",
                "JDK 8 中 HashMap 主要由数组、链表和红黑树组成。",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(question_tools, "QUESTION_BASE", tmp_path / "knowledge")


def test_interviewer_agent_completes_one_question_mvp_flow(
    isolated_interviewer_environment: None,
) -> None:
    agent = InterviewerAgent(config={"llm": {"model": "fake-model"}})
    agent.llm_client = InterviewFlowLLMClient()

    opening = asyncio.run(agent.start_interview())
    feedback = asyncio.run(agent.continue_interview("数组、链表和红黑树。"))

    assert "HashMap" in opening
    assert "评分已保存" in feedback

    metadata = memory_tools.get_question_metadata("hashmap-basic")
    assert metadata is not None
    assert metadata["module"] == "Java基础"
    assert metadata["total_attempts"] == 1
    assert metadata["avg_score"] == 3.0
