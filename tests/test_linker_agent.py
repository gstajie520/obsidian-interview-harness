#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识关联器 Agent 测试。

LinkerAgent 的第一版目标不是复杂向量检索，而是先用“模块 + 关键词 +
标题相似度”做轻量推荐。测试先写清楚业务期望，再实现代码。
"""

from __future__ import annotations

from typing import Any

from agents.roles.linker_agent import LinkerAgent


def make_agent() -> LinkerAgent:
    """创建一个不依赖真实 LLM 的 LinkerAgent。"""
    return LinkerAgent(config={"llm": {"model": "fake-model"}})


def question(
    question_id: str,
    module: str,
    title: str,
    content: str,
) -> dict[str, Any]:
    """构造测试题目，类似 Java 里的测试 DTO。"""
    return {
        "question_id": question_id,
        "module": module,
        "title": title,
        "content": content,
    }


def test_linker_extracts_keywords_from_title_and_content() -> None:
    agent = make_agent()

    keywords = agent.extract_keywords(
        "HashMap 扩容机制",
        "HashMap 数组 链表 红黑树 负载因子 resize 扩容",
        max_keywords=6,
    )

    assert "hashmap" in keywords
    assert "扩容机制" in keywords or "扩容" in keywords
    assert "负载因子" in keywords
    assert len(keywords) <= 6


def test_linker_recommends_same_module_and_shared_keywords_first() -> None:
    agent = make_agent()
    source = question(
        "hashmap-basic",
        "Java集合",
        "HashMap 底层原理",
        "数组 链表 红黑树 扩容 负载因子",
    )
    candidates = [
        question(
            "redis-cache",
            "Redis",
            "缓存穿透怎么解决",
            "缓存 空值 布隆过滤器",
        ),
        question(
            "hashmap-resize",
            "Java集合",
            "HashMap 扩容机制",
            "负载因子 resize 数组 链表",
        ),
        question(
            "arraylist-grow",
            "Java集合",
            "ArrayList 扩容机制",
            "数组 扩容 容量",
        ),
    ]

    result = agent.find_related_questions(source, candidates, top_k=2)

    assert result["count"] == 2
    assert result["items"][0]["question_id"] == "hashmap-resize"
    assert result["items"][0]["score"] > result["items"][1]["score"]
    assert "同模块" in result["items"][0]["reason"]


def test_linker_detects_relation_types() -> None:
    agent = make_agent()
    source = question(
        "hashmap-basic",
        "Java集合",
        "HashMap 底层原理",
        "数组 链表 红黑树",
    )
    candidates = [
        question(
            "hashmap-vs-concurrent",
            "Java集合",
            "HashMap 和 ConcurrentHashMap 区别",
            "线程安全 对比 区别",
        ),
        question(
            "hashmap-in-project",
            "Java集合",
            "项目中如何选择 Map",
            "业务场景 并发 读多写少",
        ),
        question(
            "java-collection-basic",
            "Java基础",
            "Java 集合基础",
            "前置知识 List Map Set",
        ),
    ]

    result = agent.find_related_questions(source, candidates, top_k=3)
    relation_by_id = {
        item["question_id"]: item["relation_type"]
        for item in result["items"]
    }

    assert relation_by_id["hashmap-vs-concurrent"] == "compare"
    assert relation_by_id["hashmap-in-project"] == "scenario"
    assert relation_by_id["java-collection-basic"] == "prerequisite"


def test_linker_process_routes_actions() -> None:
    agent = make_agent()
    source = question("jmm-basic", "Java并发", "Java 内存模型", "可见性 有序性")
    candidates = [
        question("volatile-basic", "Java并发", "volatile 原理", "可见性 有序性"),
    ]

    related = agent.process(
        {
            "action": "find_related_questions",
            "question": source,
            "candidates": candidates,
            "top_k": 1,
        }
    )
    keywords = agent.process(
        {
            "action": "extract_keywords",
            "title": "volatile 原理",
            "content": "可见性 有序性 禁止指令重排",
        }
    )
    unknown = agent.process({"action": "unknown"})
    invalid = agent.process("not-a-dict")

    assert related["items"][0]["question_id"] == "volatile-basic"
    assert "volatile" in keywords["keywords"]
    assert unknown["status"] == "error"
    assert invalid["status"] == "error"
