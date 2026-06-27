#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""题库导入脚本测试。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from agents.tools import memory_tools, question_tools
from scripts import import_questions


@pytest.fixture()
def isolated_import_environment(
    tmp_path: Path,
    monkeypatch: Any,
) -> Path:
    """隔离导入脚本使用的题库目录和 SQLite 数据库。"""
    monkeypatch.setattr(memory_tools, "_DIALECT", "sqlite")
    monkeypatch.setattr(memory_tools, "_INSERT_IGNORE", "INSERT OR IGNORE")
    monkeypatch.setattr(memory_tools, "_TODAY", "DATE('now')")
    monkeypatch.setattr(memory_tools, "SQLITE_PATH", tmp_path / "learning.db")

    knowledge_base = tmp_path / "knowledge"
    java_module = knowledge_base / "Java基础"
    redis_module = knowledge_base / "Redis"
    java_module.mkdir(parents=True)
    redis_module.mkdir(parents=True)

    (java_module / "HashMap.md").write_text(
        "\n".join(
            [
                "---",
                "question_id: hashmap-basic",
                "---",
                "HashMap 的底层结构是什么？",
            ]
        ),
        encoding="utf-8",
    )
    (redis_module / "缓存穿透.md").write_text(
        "\n".join(
            [
                "---",
                "question_id: redis-cache-penetration",
                "---",
                "什么是缓存穿透？",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(question_tools, "QUESTION_BASE", knowledge_base)
    return knowledge_base


def test_import_questions_returns_inserted_count_and_is_idempotent(
    isolated_import_environment: Path,
) -> None:
    first_count = import_questions.import_questions()
    second_count = import_questions.import_questions()

    assert first_count == 2
    assert second_count == 0
    assert memory_tools.get_question_metadata("hashmap-basic")["module"] == (
        "Java基础"
    )
    assert memory_tools.get_question_metadata(
        "redis-cache-penetration"
    )["title"] == "缓存穿透"


def test_import_questions_can_limit_to_one_module(
    isolated_import_environment: Path,
) -> None:
    imported_count = import_questions.import_questions(module="Redis")

    assert imported_count == 1
    assert memory_tools.get_question_metadata("redis-cache-penetration")
    assert memory_tools.get_question_metadata("hashmap-basic") is None
