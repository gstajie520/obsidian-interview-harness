#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""记忆工具测试。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from agents.tools import memory_tools


@pytest.fixture()
def isolated_sqlite_db(tmp_path: Path, monkeypatch: Any) -> Path:
    """让每个测试使用临时 SQLite 数据库，避免污染真实学习数据。"""
    monkeypatch.setattr(memory_tools, "_DIALECT", "sqlite")
    monkeypatch.setattr(memory_tools, "_INSERT_IGNORE", "INSERT OR IGNORE")
    monkeypatch.setattr(memory_tools, "_TODAY", "DATE('now')")
    monkeypatch.setattr(memory_tools, "SQLITE_PATH", tmp_path / "learning.db")
    return tmp_path / "learning.db"


def test_get_weak_modules_ignores_untouched_questions(
    isolated_sqlite_db: Path,
) -> None:
    memory_tools.init_question_metadata(
        question_id="jvm-untouched",
        file_path="knowledge/jvm.md",
        module="JVM",
        title="JVM 未答题",
    )
    memory_tools.init_question_metadata(
        question_id="redis-answered",
        file_path="knowledge/redis.md",
        module="Redis",
        title="Redis 已答题",
    )
    memory_tools.add_learning_record(
        question_id="redis-answered",
        module="Redis",
        user_answer="回答得不完整",
        scores={
            "accuracy": 2,
            "completeness": 2,
            "depth": 2,
            "scenario": 2,
        },
        session_id="test-session",
    )

    assert memory_tools.get_weak_modules(limit=5) == ["Redis"]


def test_get_weak_modules_returns_empty_when_only_untouched_questions(
    isolated_sqlite_db: Path,
) -> None:
    memory_tools.init_question_metadata(
        question_id="mysql-untouched",
        file_path="knowledge/mysql.md",
        module="MySQL",
        title="MySQL 未答题",
    )
    memory_tools.init_question_metadata(
        question_id="java-untouched",
        file_path="knowledge/java.md",
        module="Java",
        title="Java 未答题",
    )

    assert memory_tools.get_weak_modules(limit=5) == []
