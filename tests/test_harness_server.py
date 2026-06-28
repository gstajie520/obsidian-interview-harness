#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FastAPI 服务测试。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from agents.tools import memory_tools, question_tools
from scripts.harness_server import create_app


@pytest.fixture()
def isolated_api_environment(tmp_path: Path, monkeypatch: Any) -> None:
    """隔离 API 测试使用的题库目录和 SQLite 数据库。"""
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
                "",
                "## 典型回答",
                "JDK 8 中 HashMap 主要由数组、链表和红黑树组成。",
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
    memory_tools.init_question_metadata(
        question_id="hashmap-basic",
        file_path=str(java_module / "HashMap.md"),
        module="Java基础",
        title="HashMap",
    )
    memory_tools.add_learning_record(
        question_id="hashmap-basic",
        module="Java基础",
        user_answer="数组、链表和红黑树。",
        scores={
            "accuracy": 2,
            "completeness": 2,
            "depth": 2,
            "scenario": 2,
        },
        session_id="seed-session",
    )


@pytest.fixture()
def api_client(isolated_api_environment: None) -> TestClient:
    """创建 FastAPI 测试客户端，类似 Spring MockMvc。"""
    return TestClient(create_app())


def test_health_endpoint(api_client: TestClient) -> None:
    response = api_client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ui_entry_redirect(api_client: TestClient) -> None:
    response = api_client.get("/ui", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/ui/"


def test_ui_index_served(api_client: TestClient) -> None:
    response = api_client.get("/ui/")
    assert response.status_code == 200
    text = response.text
    assert "<title>AI 面试陪练 - Interview UI</title>" in text
    assert "AI 面试陪练 - Interview UI" in text


def test_session_lifecycle(api_client: TestClient) -> None:
    created = api_client.post(
        "/api/session/create",
        json={"primary_agent": "interviewer"},
    )
    assert created.status_code == 200
    session_id = created.json()["session_id"]

    fetched = api_client.get(f"/api/session/{session_id}")
    assert fetched.status_code == 200
    assert fetched.json()["session_id"] == session_id

    deleted = api_client.delete(f"/api/session/{session_id}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True

    missing = api_client.get(f"/api/session/{session_id}")
    assert missing.status_code == 404


def test_stats_endpoints(api_client: TestClient) -> None:
    overview = api_client.get("/api/stats/overview")
    weak_modules = api_client.get("/api/stats/weak-modules?limit=3")
    due_reviews = api_client.get("/api/stats/due-reviews?limit=3")

    assert overview.status_code == 200
    assert overview.json()["total"] == 1
    assert weak_modules.status_code == 200
    assert weak_modules.json()["modules"] == ["Java基础"]
    assert due_reviews.status_code == 200
    assert "reviews" in due_reviews.json()


def test_question_endpoints(api_client: TestClient) -> None:
    random_question = api_client.get("/api/questions/random?module=Java基础")
    by_id = api_client.get("/api/questions/hashmap-basic")
    search = api_client.get("/api/questions/search?keyword=HashMap")

    assert random_question.status_code == 200
    assert random_question.json()["question_id"] == "hashmap-basic"
    assert by_id.status_code == 200
    assert by_id.json()["module"] == "Java基础"
    assert search.status_code == 200
    assert search.json()["count"] == 1


def test_interview_websocket_submit_answer_protocol(
    api_client: TestClient,
) -> None:
    with api_client.websocket_connect("/ws/interview") as websocket:
        connected = websocket.receive_json()
        assert connected["type"] == "connection_open"

        websocket.send_json(
            {
                "type": "submit_answer",
                "question_id": "hashmap-basic",
                "answer": "数组、链表和红黑树。",
            }
        )

        chunk = websocket.receive_json()
        chunk2 = websocket.receive_json()
        chunk3 = websocket.receive_json()
        complete = websocket.receive_json()

        assert chunk == {
            "type": "evaluation_chunk",
            "content": "已收到答案，正在进入评估流程...",
        }
        assert chunk2 == {
            "type": "evaluation_chunk",
            "content": "正在计算得分与弱点...",
        }
        assert chunk3 == {
            "type": "evaluation_chunk",
            "content": "已完成记录保存，正在生成闭环反馈...",
        }
        assert complete["type"] == "evaluation_complete"
        assert complete["question_id"] == "hashmap-basic"
        assert complete["status"] == "success"
        assert complete["answer_length"] == 10
        assert "scores" in complete
        assert complete["orchestration"]["events"] >= 5


def test_orchestration_runs_api_by_session_and_question(
    api_client: TestClient,
) -> None:
    """WS 评分后，闭环记录可通过 API 按会话和题目查询。"""
    with api_client.websocket_connect("/ws/interview") as websocket:
        websocket.receive_json()
        websocket.send_json(
            {
                "type": "submit_answer",
                "question_id": "hashmap-basic",
                "answer": "数组、链表和红黑树。",
                "include_report": True,
                "session_id": "session-fixed-001",
            }
        )

        _ = websocket.receive_json()
        _ = websocket.receive_json()
        _ = websocket.receive_json()
        complete = websocket.receive_json()

    response = api_client.get(
        "/api/orchestration/runs?session_id=session-fixed-001&question_id=hashmap-basic"
    )
    body = response.json()
    assert response.status_code == 200
    assert body["count"] == 1

    run = body["runs"][0]
    assert run["session_id"] == "session-fixed-001"
    assert run["question_id"] == "hashmap-basic"
    assert int(run["learning_record_id"]) == complete["record_id"]
    assert (
        run["payload"]["analysis_error_type"]
        == complete["orchestration"]["analysis"]["error_type"]
    )
    assert int(run["id"]) >= 1
    assert complete["orchestration"]["recommendation"]["report_type"] == "weekly"
    assert "summary" in complete["orchestration"]["recommendation"]


def test_interview_websocket_submit_answer_with_invalid_payload(api_client: TestClient) -> None:
    with api_client.websocket_connect("/ws/interview") as websocket:
        websocket.receive_json()
        websocket.send_json(
            {
                "type": "submit_answer",
                "question_id": "",
                "answer": "any",
            }
        )
        complete = websocket.receive_json()

        assert complete["type"] == "evaluation_complete"
        assert complete["status"] == "error"
        assert "缺少 question_id" in complete["message"]


def test_interview_websocket_submit_unknown_question(api_client: TestClient) -> None:
    with api_client.websocket_connect("/ws/interview") as websocket:
        websocket.receive_json()
        websocket.send_json(
            {
                "type": "submit_answer",
                "question_id": "unknown-question-id",
                "answer": "any answer",
            }
        )
        complete = websocket.receive_json()

        assert complete["type"] == "evaluation_complete"
        assert complete["status"] == "error"
        assert "未找到题目" in complete["message"]


def test_interview_websocket_reports_unknown_message_type(
    api_client: TestClient,
) -> None:
    with api_client.websocket_connect("/ws/interview") as websocket:
        websocket.receive_json()
        websocket.send_json({"type": "unknown"})

        error = websocket.receive_json()

        assert error["type"] == "error"
        assert "不支持的消息类型" in error["message"]
