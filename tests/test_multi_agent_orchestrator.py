#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多 Agent 编排器测试。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scripts.multi_agent_orchestrator import MultiAgentOrchestrator
from agents.tools import memory_tools, question_tools


@pytest.fixture()
def isolated_environment(tmp_path: Path, monkeypatch: Any) -> None:
    """隔离数据库和题库，避免污染全局数据。"""
    monkeypatch.setattr(memory_tools, "_DIALECT", "sqlite")
    monkeypatch.setattr(memory_tools, "_INSERT_IGNORE", "INSERT OR IGNORE")
    monkeypatch.setattr(memory_tools, "_TODAY", "DATE('now')")
    monkeypatch.setattr(memory_tools, "SQLITE_PATH", tmp_path / "learning.db")

    kb_base = tmp_path / "knowledge"
    module_dir = kb_base / "Java基础"
    module_dir.mkdir(parents=True)
    (module_dir / "HashMap.md").write_text(
        "\n".join(
            [
                "---",
                "question_id: hashmap-basic",
                "---",
                "HashMap 的底层结构是什么？",
                "",
                "数组、链表和红黑树。",
            ]
        ),
        encoding="utf-8",
    )
    (module_dir / "ArrayList.md").write_text(
        "\n".join(
            [
                "---",
                "question_id: arraylist-basic",
                "---",
                "ArrayList 的扩容机制？",
                "",
                "数组扩容与复制。",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(question_tools, "QUESTION_BASE", kb_base)


def make_record() -> dict[str, Any]:
    """构造一条基础学习记录。"""
    return {
        "question_id": "hashmap-basic",
        "module": "Java基础",
        "question": "HashMap 的底层结构是什么？",
        "user_answer": "数组、链表和红黑树",
        "scores": {
            "accuracy": 4,
            "completeness": 3,
            "depth": 2,
            "scenario": 2,
        },
        "weak_points": ["场景化不足"],
        "consecutive_success": 4,
    }


def test_orchestrator_builds_end_to_end_flow(isolated_environment: None) -> None:
    orchestrator = MultiAgentOrchestrator(config={"llm": {"model": "fake-model"}})

    result = orchestrator.orchestrate_after_answer(make_record(), include_report=False)

    assert result["status"] == "ok"
    assert result["analysis"]["error_type"] == "scenario_lack"
    assert result["schedule"]["status"] == "scheduled"
    assert result["relations"]["status"] == "ok"
    assert result["recommendation"]["report_type"] == "daily"
    assert result["encouragement"]["status"] == "ok"
    assert len(result["events"]) >= 6
    assert result["events"][0]["agent"] == "orchestrator_start"


def test_orchestrator_switches_to_weekly_report(isolated_environment: None) -> None:
    orchestrator = MultiAgentOrchestrator(config={"llm": {"model": "fake-model"}})

    result = orchestrator.orchestrate_after_answer(make_record(), include_report=True)

    assert result["recommendation"]["report_type"] == "weekly"
    assert result["encouragement"]["encouragement"]["status"] == "ok"


def test_orchestrator_falls_back_when_analysis_fails(
    isolated_environment: None,
    monkeypatch: Any,
) -> None:
    orchestrator = MultiAgentOrchestrator(config={"llm": {"model": "fake-model"}})
    record = make_record()

    def broken_analyzer(_: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("analysis service unavailable")

    monkeypatch.setattr(orchestrator.analyzer, "analyze_wrong_answer", broken_analyzer)

    result = orchestrator.orchestrate_after_answer(record, include_report=False)

    assert result["analysis"]["status"] == "error"
    assert result["analysis"]["message"] == "错题分析失败: analysis service unavailable"
    agents = [event["agent"] for event in result["events"]]
    assert "analyzer_failed" in agents
    assert result["analysis"]["question_id"] == "hashmap-basic"
