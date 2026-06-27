#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""复习调度器 Agent 测试。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from agents.roles.scheduler_agent import SchedulerAgent
from agents.tools import memory_tools


@pytest.fixture()
def isolated_scheduler_db(tmp_path: Path, monkeypatch: Any) -> Path:
    """让 Scheduler 测试使用临时 SQLite 数据库。"""
    monkeypatch.setattr(memory_tools, "_DIALECT", "sqlite")
    monkeypatch.setattr(memory_tools, "_INSERT_IGNORE", "INSERT OR IGNORE")
    monkeypatch.setattr(memory_tools, "_TODAY", "DATE('now')")
    monkeypatch.setattr(memory_tools, "SQLITE_PATH", tmp_path / "learning.db")
    return tmp_path / "learning.db"


def mark_question_due(
    question_id: str,
    *,
    next_review: str,
    avg_score: float,
) -> None:
    """直接把题目标记为到期复习，用于构造测试数据。"""
    conn = memory_tools.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE question_metadata
        SET next_review = ?, avg_score = ?, mastery_level = 'learning'
        WHERE question_id = ?
        """,
        (next_review, avg_score, question_id),
    )
    conn.commit()
    conn.close()


def seed_answered_question(
    question_id: str,
    module: str,
    title: str,
    *,
    score: float,
) -> None:
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
        session_id="scheduler-test",
    )


def test_scheduler_agent_generates_daily_review_list(
    isolated_scheduler_db: Path,
) -> None:
    seed_answered_question("redis-cache", "Redis", "缓存穿透", score=2)
    seed_answered_question("jvm-gc", "JVM", "GC Roots", score=3)
    mark_question_due("redis-cache", next_review="2020-01-01", avg_score=2)
    mark_question_due("jvm-gc", next_review="2020-01-02", avg_score=3)

    scheduler = SchedulerAgent(config={"llm": {"model": "fake-model"}})
    result = scheduler.get_daily_review_list(limit=5)

    assert result["count"] == 2
    assert result["items"][0]["question_id"] == "redis-cache"
    assert result["items"][0]["priority_rank"] == 1
    assert result["items"][0]["reason"] == "已到期复习"
    assert result["summary"] == "今日有 2 道题需要复习。"


def test_scheduler_agent_updates_next_review_schedule(
    isolated_scheduler_db: Path,
) -> None:
    seed_answered_question("hashmap-basic", "Java基础", "HashMap", score=4)

    scheduler = SchedulerAgent(config={"llm": {"model": "fake-model"}})
    result = scheduler.schedule_next_review("hashmap-basic", performance=4)

    assert result["question_id"] == "hashmap-basic"
    assert result["next_review"] is not None
    assert result["review_interval_days"] >= 1
    assert result["repetitions"] >= 1


def test_scheduler_agent_process_routes_actions(
    isolated_scheduler_db: Path,
) -> None:
    scheduler = SchedulerAgent(config={"llm": {"model": "fake-model"}})

    result = scheduler.process({"action": "daily_review_list", "limit": 3})

    assert result["count"] == 0
    assert result["summary"] == "今日没有到期复习题。"
