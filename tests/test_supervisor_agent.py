#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""监督助手 Agent 测试。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from agents.roles.supervisor_agent import SupervisorAgent
from agents.tools import memory_tools


@pytest.fixture()
def isolated_supervisor_db(tmp_path: Path, monkeypatch: Any) -> Path:
    """让 Supervisor 测试使用临时 SQLite 数据库。"""
    monkeypatch.setattr(memory_tools, "_DIALECT", "sqlite")
    monkeypatch.setattr(memory_tools, "_INSERT_IGNORE", "INSERT OR IGNORE")
    monkeypatch.setattr(memory_tools, "_TODAY", "DATE('now')")
    monkeypatch.setattr(memory_tools, "SQLITE_PATH", tmp_path / "learning.db")
    return tmp_path / "learning.db"


def seed_learning_record(
    question_id: str,
    module: str,
    title: str,
    *,
    score: float,
) -> None:
    """插入一条已作答题目，给报告生成准备测试数据。"""
    memory_tools.init_question_metadata(
        question_id=question_id,
        file_path=f"knowledge/{question_id}.md",
        module=module,
        title=title,
    )
    memory_tools.add_learning_record(
        question_id=question_id,
        module=module,
        user_answer="测试答案",
        scores={
            "accuracy": score,
            "completeness": score,
            "depth": score,
            "scenario": score,
        },
        session_id="supervisor-test",
    )


def mark_question_due(question_id: str, next_review: str) -> None:
    """把题目标记为到期复习，模拟 Scheduler 产生的复习队列。"""
    conn = memory_tools.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE question_metadata
        SET next_review = ?
        WHERE question_id = ?
        """,
        (next_review, question_id),
    )
    conn.commit()
    conn.close()


def test_supervisor_generates_daily_report(
    isolated_supervisor_db: Path,
) -> None:
    seed_learning_record("redis-cache", "Redis", "缓存穿透", score=2)
    seed_learning_record("jvm-gc", "JVM", "GC Roots", score=4)
    mark_question_due("redis-cache", "2020-01-01")

    supervisor = SupervisorAgent(config={"llm": {"model": "fake-model"}})
    report = supervisor.generate_daily_report(limit=5)

    assert report["report_type"] == "daily"
    assert report["stats"]["today_count"] == 2
    assert report["weak_modules"] == ["Redis", "JVM"]
    assert report["due_review_count"] == 1
    assert "# 每日学习简报" in report["markdown"]
    assert "今日已练习 2 题" in report["markdown"]
    assert "Redis" in report["markdown"]


def test_supervisor_generates_weekly_report_markdown(
    isolated_supervisor_db: Path,
) -> None:
    seed_learning_record("hashmap-basic", "Java基础", "HashMap", score=4)

    supervisor = SupervisorAgent(config={"llm": {"model": "fake-model"}})
    report = supervisor.generate_weekly_report(limit=3)

    assert report["report_type"] == "weekly"
    assert report["stats"]["mastered"] == 1
    assert "# 学习周报" in report["markdown"]
    assert "本周概览" in report["markdown"]
    assert "下周建议" in report["markdown"]


def test_supervisor_process_routes_actions(
    isolated_supervisor_db: Path,
) -> None:
    supervisor = SupervisorAgent(config={"llm": {"model": "fake-model"}})

    daily = supervisor.process({"action": "daily_report", "limit": 2})
    weekly = supervisor.process({"action": "weekly_report", "limit": 2})
    unknown = supervisor.process({"action": "unknown"})

    assert daily["report_type"] == "daily"
    assert weekly["report_type"] == "weekly"
    assert unknown["status"] == "error"
