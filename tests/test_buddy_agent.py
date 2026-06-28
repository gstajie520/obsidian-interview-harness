#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""陪练伙伴 Agent 测试。

BuddyAgent 的目标是给“答题遇阻”的学习过程加上轻量学习支持：
- 3 级提示
- 通俗解释
- 学习状态触发的鼓励或休息建议
"""

from __future__ import annotations

from agents.roles.buddy_agent import BuddyAgent


def make_agent() -> BuddyAgent:
    """创建一个不依赖真实 LLM 的 BuddyAgent。"""
    return BuddyAgent(config={"llm": {"model": "fake-model"}})


def test_buddy_levels_and_hint() -> None:
    agent = make_agent()

    level_1 = agent.give_hint(
        question_id="hashmap-basic",
        user_answer="我记得是用数组和链表实现的",
        level=1,
    )
    level_2 = agent.give_hint(
        question_id="hashmap-basic",
        user_answer="我记得是用数组和链表实现的",
        level=2,
    )
    level_3 = agent.give_hint(
        question_id="hashmap-basic",
        user_answer="我记得是用数组和链表实现的",
        level=3,
    )

    assert level_1["status"] == "ok"
    assert level_2["status"] == "ok"
    assert level_3["status"] == "ok"
    assert level_1["hint_level"] == 1
    assert level_2["hint_level"] == 2
    assert level_3["hint_level"] == 3
    assert level_3["hint_type"] == "keyword"
    assert len(level_1["hint"]) >= 5
    assert len(level_2["hint"]) >= 5
    assert len(level_3["hint"]) >= 5


def test_buddy_explain_in_simple_terms() -> None:
    agent = make_agent()

    simple = agent.explain_in_simple_terms(
        "volatile 和 synchronized 的核心区别在于可见性和互斥锁策略"
    )

    assert simple["status"] == "ok"
    assert "通俗" in simple["message"]
    assert "volatile" in simple["message"]


def test_buddy_encouragement_and_break_suggestion() -> None:
    agent = make_agent()
    encouragement = agent.generate_encouragement("daily_progress", consecutive_success=3)
    break_suggestion = agent.suggest_break(
        mood="tired",
        consecutive_success=10,
        session_minutes=70,
    )

    assert encouragement["status"] == "ok"
    assert "鼓励" in encouragement["message"]
    assert break_suggestion["status"] == "ok"
    assert break_suggestion["recommendation"] == "take_break"


def test_buddy_process_routes_actions() -> None:
    agent = make_agent()

    hint = agent.process(
        {
            "action": "give_hint",
            "question_id": "volatile-memory",
            "user_answer": "可见性没写",
            "level": 2,
        }
    )
    explanation = agent.process(
        {
            "action": "explain_in_simple_terms",
            "text": "在内存屏障下，变量更新会被强制刷新到主内存。",
        }
    )
    encouragement = agent.process(
        {
            "action": "generate_encouragement",
            "trigger": "breakthrough",
            "consecutive_success": 5,
        }
    )
    unknown = agent.process({"action": "invalid"})
    invalid = agent.process("not-a-dict")

    assert hint["status"] == "ok"
    assert hint["hint_level"] == 2
    assert explanation["status"] == "ok"
    assert encouragement["status"] == "ok"
    assert unknown["status"] == "error"
    assert invalid["status"] == "error"
