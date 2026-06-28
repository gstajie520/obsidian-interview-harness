#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""错题分析师 Agent 测试。

这些测试先规定 AnalyzerAgent 应该“看懂一条错题记录”，再去写实现。
这就是 TDD：先写会失败的测试，再补代码让测试通过。
"""

from __future__ import annotations

from typing import Any, Optional

from agents.roles.analyzer_agent import AnalyzerAgent


def make_agent() -> AnalyzerAgent:
    """创建一个不依赖真实 LLM 的 AnalyzerAgent。"""
    return AnalyzerAgent(config={"llm": {"model": "fake-model"}})


def build_record(
    *,
    scores: dict[str, float],
    weak_points: Optional[list[str]] = None,
) -> dict[str, Any]:
    """构造一条错题记录，类似 Java 里的测试 DTO。"""
    return {
        "question_id": "thread-sleep-wait",
        "module": "Java并发",
        "question": "sleep 和 wait 有什么区别？",
        "user_answer": "它们都能让线程暂停。",
        "scores": scores,
        "weak_points": weak_points or [],
    }


def test_analyzer_classifies_concept_confusion_from_weak_points() -> None:
    record = build_record(
        scores={
            "accuracy": 1.5,
            "completeness": 3.0,
            "depth": 3.0,
            "scenario": 3.0,
        },
        weak_points=["把 sleep 和 wait 的锁释放行为搞混"],
    )

    result = make_agent().analyze_wrong_answer(record)

    assert result["status"] == "analyzed"
    assert result["error_type"] == "concept_confusion"
    assert result["error_type_name"] == "概念混淆"
    assert result["remedial_actions"][0]["type"] == "comparison_table"
    assert "搞混" in " ".join(result["evidence"])
    assert "## 证据" in result["markdown"]


def test_analyzer_classifies_detail_missing_from_low_completeness() -> None:
    record = build_record(
        scores={
            "accuracy": 4.0,
            "completeness": 1.0,
            "depth": 3.0,
            "scenario": 3.0,
        },
        weak_points=["遗漏扩容阈值和触发条件"],
    )

    result = make_agent().analyze_wrong_answer(record)

    assert result["error_type"] == "detail_missing"
    assert result["lowest_dimension"] == "completeness"
    assert any(action["type"] == "detail_card" for action in result["remedial_actions"])


def test_analyzer_classifies_scenario_lack_from_low_scenario_score() -> None:
    record = build_record(
        scores={
            "accuracy": 3.5,
            "completeness": 3.0,
            "depth": 3.0,
            "scenario": 1.0,
        },
        weak_points=["缺少真实项目场景，不知道什么时候用"],
    )

    result = make_agent().analyze_wrong_answer(record)

    assert result["error_type"] == "scenario_lack"
    assert "场景" in result["suggestion"]
    assert any(action["type"] == "scenario_practice" for action in result["remedial_actions"])


def test_analyzer_classifies_prerequisite_gap_from_depth_signal() -> None:
    record = build_record(
        scores={
            "accuracy": 3.0,
            "completeness": 3.0,
            "depth": 1.0,
            "scenario": 2.5,
        },
        weak_points=["前置知识 Java 内存模型不扎实"],
    )

    result = make_agent().analyze_wrong_answer(record)

    assert result["error_type"] == "prerequisite_gap"
    assert "前置" in result["suggestion"]
    assert any(action["type"] == "prerequisite_review" for action in result["remedial_actions"])


def test_analyzer_falls_back_to_lowest_score_dimension() -> None:
    record = build_record(
        scores={
            "accuracy": 4.0,
            "completeness": 3.5,
            "depth": 2.0,
            "scenario": 3.0,
        },
    )

    result = make_agent().analyze_wrong_answer(record)

    assert result["error_type"] == "prerequisite_gap"
    assert result["lowest_dimension"] == "depth"
    assert any("depth=2.0" in evidence for evidence in result["evidence"])


def test_analyzer_process_routes_actions() -> None:
    agent = make_agent()
    record = build_record(
        scores={
            "accuracy": 1.0,
            "completeness": 3.0,
            "depth": 3.0,
            "scenario": 3.0,
        },
        weak_points=["概念理解错误"],
    )

    analyzed = agent.process(
        {
            "action": "analyze_wrong_answer",
            "record": record,
        }
    )
    unknown = agent.process({"action": "unknown"})
    invalid = agent.process("not-a-dict")

    assert analyzed["error_type"] == "concept_confusion"
    assert unknown["status"] == "error"
    assert invalid["status"] == "error"
