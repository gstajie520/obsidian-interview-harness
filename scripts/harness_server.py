#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FastAPI 服务入口。

这层可以类比 Java Spring Boot 的 Controller 层：
- 接收 HTTP 请求。
- 调用 agents/tools 里的业务函数。
- 把 Python 对象转换成 JSON 响应。

注意：这里先实现不依赖真实 LLM 的最小 API。面试对话和 WebSocket 会在
后续 Phase 中继续补充，避免一次把服务层、前端和 LLM 流式调用全部混在一起。
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.tools import memory_tools, question_tools


SUPPORTED_WEBSOCKET_MESSAGE_TYPES = {"submit_answer"}


class CreateSessionRequest(BaseModel):
    """创建会话请求体。

    Pydantic 的 BaseModel 可以类比 Java 里的 DTO。FastAPI 会自动把
    JSON 请求体转换成这个对象，并做基础类型校验。
    """

    primary_agent: str = "interviewer"


def create_app() -> FastAPI:
    """创建 FastAPI 应用，方便测试和 uvicorn 复用。

    Java/Spring 项目通常靠框架扫描 Controller；FastAPI 更常见的写法是
    显式创建 app，再用装饰器注册路由。
    """
    app = FastAPI(
        title="AI 面试陪练 Agent Harness API",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        """健康检查：给前端、curl 或部署平台确认服务已启动。"""
        return {"status": "ok"}

    @app.post("/api/session/create")
    def create_session(request: CreateSessionRequest) -> dict[str, str]:
        """创建学习会话。"""
        # uuid4 用来生成几乎不会重复的 ID；前缀日期方便人类看日志。
        session_id = (
            datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            + "-"
            + uuid.uuid4().hex[:8]
        )
        memory_tools.create_session(session_id, request.primary_agent)
        return {
            "session_id": session_id,
            "primary_agent": request.primary_agent,
        }

    @app.get("/api/session/{session_id}")
    def get_session(session_id: str) -> dict[str, Any]:
        """查询学习会话。"""
        session = memory_tools.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="session not found")
        return session

    @app.delete("/api/session/{session_id}")
    def delete_session(session_id: str) -> dict[str, Any]:
        """删除学习会话。"""
        deleted = memory_tools.delete_session(session_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="session not found")
        return {"session_id": session_id, "deleted": True}

    @app.get("/api/stats/overview")
    def stats_overview() -> dict[str, Any]:
        """总体学习统计。"""
        return memory_tools.get_learning_stats()

    @app.get("/api/stats/weak-modules")
    def stats_weak_modules(
        limit: int = Query(default=5, ge=1, le=50),
    ) -> dict[str, Any]:
        """薄弱模块列表。"""
        modules = memory_tools.get_weak_modules(limit)
        return {"modules": modules, "count": len(modules)}

    @app.get("/api/stats/due-reviews")
    def stats_due_reviews(
        limit: int = Query(default=20, ge=1, le=100),
    ) -> dict[str, Any]:
        """到期复习题目列表。"""
        reviews = memory_tools.get_due_reviews(limit)
        return {"reviews": reviews, "count": len(reviews)}

    @app.get("/api/questions/random")
    def random_question(
        module: Optional[str] = None,
    ) -> dict[str, Any]:
        """随机获取一道题。"""
        question = question_tools.get_random_question(module=module)
        if question is None:
            raise HTTPException(status_code=404, detail="question not found")
        return question.to_dict()

    @app.get("/api/questions/search")
    def search_questions(
        keyword: str = Query(min_length=1),
        module: Optional[str] = None,
    ) -> dict[str, Any]:
        """按关键词搜索题目。"""
        questions = question_tools.search_questions(keyword, module=module)
        return {
            "questions": [question.to_dict() for question in questions],
            "count": len(questions),
        }

    @app.get("/api/questions/{question_id}")
    def question_by_id(question_id: str) -> dict[str, Any]:
        """按 question_id 查询题目。"""
        question = question_tools.get_question_by_id(question_id)
        if question is None:
            raise HTTPException(status_code=404, detail="question not found")
        return question.to_dict()

    @app.websocket("/ws/interview")
    async def interview_websocket(websocket: WebSocket) -> None:
        """面试 WebSocket 通道。

        WebSocket 可以类比一个“不断开的 HTTP 连接”。普通 REST 是一次请求
        一次响应；WebSocket 建立连接后，前后端可以多次互发 JSON 消息。

        当前版本先提供稳定协议骨架：收到答案后返回两段事件，方便前端先
        完成实时消息联调。真实 LLM 流式评分会在后续版本接入。
        """
        await websocket.accept()
        await websocket.send_json({"type": "connection_open"})

        try:
            while True:
                message = await websocket.receive_json()
                message_type = str(message.get("type") or "")

                if message_type not in SUPPORTED_WEBSOCKET_MESSAGE_TYPES:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": f"不支持的消息类型: {message_type}",
                        }
                    )
                    continue

                await _handle_submit_answer_message(websocket, message)
        except WebSocketDisconnect:
            return

    return app


async def _handle_submit_answer_message(
    websocket: WebSocket,
    message: dict[str, Any],
) -> None:
    """处理用户提交答案的 WebSocket 消息。

    这个函数先不直接调用 LLM。原因是 WebSocket 协议、前端实时显示、LLM
    流式输出是三个不同问题；先把协议稳定下来，后续再把 Agent 接进来。
    """
    question_id = str(message.get("question_id") or "")
    answer = str(message.get("answer") or "")

    await websocket.send_json(
        {
            "type": "evaluation_chunk",
            "content": "已收到答案，正在进入评估流程...",
        }
    )
    await websocket.send_json(
        {
            "type": "evaluation_complete",
            "status": "received",
            "question_id": question_id,
            "answer_length": len(answer),
            "scores": None,
            "message": "真实 LLM 评分将在后续版本接入。",
        }
    )


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "scripts.harness_server:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
