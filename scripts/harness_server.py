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
import re
import json
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

from agents.tools import memory_tools, question_tools
from scripts.multi_agent_orchestrator import MultiAgentOrchestrator


SUPPORTED_WEBSOCKET_MESSAGE_TYPES = {"submit_answer"}
ROOT_DIR = Path(__file__).resolve().parent.parent
UI_BUILD_ROOT = ROOT_DIR / "ui_build"
LEGACY_UI_ROOT = ROOT_DIR / "web_ui"


class CreateSessionRequest(BaseModel):
    """创建会话请求体。

    Pydantic 的 BaseModel 可以类比 Java 里的 DTO。FastAPI 会自动把
    JSON 请求体转换成这个对象，并做基础类型校验。
    """

    primary_agent: str = "interviewer"


def _get_ui_root() -> Path:
    """返回当前应被托管的前端目录。

    优先使用新的 Vite 构建产物目录 `ui_build/`；如果前端还没 build，则回退
    到旧的 `web_ui/` 原型页，避免本地开发直接启动后端时彻底不可用。
    """
    if (UI_BUILD_ROOT / "index.html").exists():
        return UI_BUILD_ROOT
    return LEGACY_UI_ROOT


def _resolve_ui_file(ui_root: Path, requested_path: str) -> Optional[Path]:
    """安全解析 `/ui/*` 对应的静态文件路径。

    这里会做一次 resolve()，确保最终路径仍然在 ui_root 下，避免用户通过
    `../` 之类的路径穿越访问到其他文件。
    """
    safe_root = ui_root.resolve()
    candidate = (safe_root / requested_path).resolve()
    if candidate == safe_root or safe_root in candidate.parents:
        return candidate
    return None


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

    @app.get("/ui")
    def ui_redirect() -> RedirectResponse:
        """浏览器访问 /ui 时重定向到静态首页。"""
        return RedirectResponse(url="/ui/")

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

    @app.get("/api/orchestration/runs")
    def get_orchestration_runs(
        session_id: str | None = Query(default=None),
        question_id: str | None = Query(default=None),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> dict[str, Any]:
        """查询编排闭环结果，支持按会话/题目过滤。"""
        runs = memory_tools.get_orchestration_runs(
            session_id=session_id if (session_id and session_id.strip()) else None,
            question_id=question_id if (question_id and question_id.strip()) else None,
            limit=limit,
        )
        return {
            "runs": [_normalize_orchestration_run(run) for run in runs],
            "count": len(runs),
        }

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

    @app.get("/ui/{requested_path:path}")
    def serve_ui(requested_path: str) -> FileResponse:
        """托管前端构建产物，并为 React Router 提供 SPA fallback。

        旧版静态 HTML 通过 `.html` 文件直接访问；新版 React 前端则需要：
        - 真实静态资源（如 /ui/assets/*.js）按文件返回。
        - 业务路由（如 /ui/dashboard）统一回退到 index.html，再交给前端路由。
        """
        ui_root = _get_ui_root()
        index_file = ui_root / "index.html"

        normalized = requested_path.strip("/")
        if not normalized:
            return FileResponse(index_file)

        candidate = _resolve_ui_file(ui_root, normalized)
        if candidate is not None and candidate.is_file():
            return FileResponse(candidate)
        if candidate is not None and candidate.is_dir():
            nested_index = candidate / "index.html"
            if nested_index.is_file():
                return FileResponse(nested_index)

        return FileResponse(index_file)

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
    session_id = str(message.get("session_id") or "")
    include_report = bool(message.get("include_report", False))

    if not question_id:
        await websocket.send_json(
            {
                "type": "evaluation_complete",
                "status": "error",
                "message": "缺少 question_id，无法执行评分。",
            }
        )
        return
    if not answer.strip():
        await websocket.send_json(
            {
                "type": "evaluation_complete",
                "status": "error",
                "message": "缺少 answer，无法执行评分。",
            }
        )
        return

    question = question_tools.get_question_by_id(question_id)
    if question is None:
        await websocket.send_json(
            {
                "type": "evaluation_complete",
                "status": "error",
                "message": f'未找到题目：{question_id}',
            }
        )
        return

    await websocket.send_json(
        {
            "type": "evaluation_chunk",
            "content": "已收到答案，正在进入评估流程...",
        }
    )
    await websocket.send_json(
        {
            "type": "evaluation_chunk",
            "content": "正在计算得分与弱点...",
        }
    )

    if not session_id:
        session_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    memory_tools.create_session(session_id=session_id, primary_agent="interviewer")

    scores = _score_answer(question=question, user_answer=answer)
    weak_points = _derive_weak_points(scores)
    record_id = memory_tools.add_learning_record(
        question_id=question_id,
        module=question.module,
        user_answer=answer,
        scores=scores,
        session_id=session_id,
        weak_points=weak_points,
        duration_seconds=0,
    )
    memory_tools.calculate_next_review(question_id, sum(scores.values()) / 4)

    orchestration = MultiAgentOrchestrator(
        config={"llm": {"model": "fake-model"}}
    ).orchestrate_after_answer(
        record={
            "question_id": question_id,
            "question": question.title,
            "module": question.module,
            "user_answer": answer,
            "scores": scores,
            "weak_points": weak_points,
            "consecutive_success": 0,
        },
        include_report=include_report,
        session_id=session_id,
        record_id=record_id,
    )

    await websocket.send_json(
        {
            "type": "evaluation_chunk",
            "content": "已完成记录保存，正在生成闭环反馈...",
        }
    )

    await websocket.send_json(
        {
            "type": "evaluation_complete",
            "status": "success",
            "question_id": question_id,
            "session_id": session_id,
            "answer_length": len(answer),
            "record_id": record_id,
            "scores": scores,
            "weak_points": weak_points,
            "overall_score": sum(scores.values()) / 4,
            "orchestration": {
                "run_id": orchestration.get("run_id"),
                "status": orchestration.get("status", "ok"),
                "question_id": orchestration.get("question_id"),
                "recommendation_type": orchestration.get("recommendation", {}).get(
                    "report_type"
                ),
                "events": len(orchestration.get("events") or []),
                "analysis": _orchestration_brief(
                    orchestration.get("analysis", {}),
                    keys=("status", "error_type", "main_gap", "remedial_advice"),
                ),
                "schedule": _orchestration_brief(
                    orchestration.get("schedule", {}),
                    keys=(
                        "status",
                        "next_review",
                        "review_interval_days",
                        "easiness_factor",
                    ),
                ),
                "relations": _orchestration_brief(
                    orchestration.get("relations", {}),
                    keys=("status", "count"),
                ),
                "recommendation": {
                    "report_type": orchestration.get("recommendation", {}).get(
                        "report_type"
                    ),
                    "status": orchestration.get("recommendation", {}).get("status"),
                    "summary": orchestration.get("recommendation", {}).get("summary"),
                },
                "encouragement": _orchestration_brief(
                    orchestration.get("encouragement", {}),
                    keys=("status", "encouragement", "hint"),
                ),
                "event_summary": _summarize_orchestration_events(
                    orchestration.get("events") or []
                ),
            },
            "message": "评分完成，闭环已写入。",
        }
    )


def _score_answer(question: Any, user_answer: str) -> dict[str, float]:
    """基于关键字覆盖度与答案长度给出启发式评分。"""
    title = str(getattr(question, "title", "") or "")
    content = str(getattr(question, "content", "") or "")
    expected = (question_tools.extract_typical_answer(content) or title or content).lower()
    expected_tokens = _extract_keywords(expected)
    answer_lower = user_answer.lower().strip()

    if not answer_lower:
        return {
            "accuracy": 0.0,
            "completeness": 0.0,
            "depth": 0.0,
            "scenario": 0.0,
        }

    if expected_tokens:
        hit = 0
        for token in expected_tokens:
            if token in answer_lower:
                hit += 1
        accuracy = min(5.0, (hit / len(expected_tokens)) * 5.0)
    else:
        accuracy = min(5.0, len(answer_lower) / 30.0)

    expected_len = len(expected) if expected else 50
    completeness = min(5.0, max(0.0, (len(answer_lower) / expected_len) * 5.0))
    scenario_keywords = {"场景", "应用", "例如", "用于", "在哪些", "在什么情况下", "举例"}
    scenario_score = 1.0 if any(k in answer_lower for k in scenario_keywords) else 0.0
    depth_score = min(
        5.0,
        2.5
        + max(0.0, (len(set(_extract_keywords(answer_lower)) & expected_tokens)))
        * 0.15,
    )
    return {
        "accuracy": _round_score(accuracy),
        "completeness": _round_score(completeness),
        "depth": _round_score(depth_score),
        "scenario": _round_score(scenario_score),
    }


def _extract_keywords(text: str) -> set[str]:
    """抽取文本关键词，兼容中英文。"""
    normalized = text.strip().lower()
    if not normalized:
        return set()
    tokens = set()
    for part in re.split(r"[\s,，。；;：:、()\[\]【】]+", normalized):
        token = part.strip()
        if not token:
            continue
        if re.fullmatch(r"[a-z0-9_#+-]+", token):
            tokens.add(token)
            continue
        for chunk in re.findall(r"[\u4e00-\u9fff]{2,6}", token):
            tokens.add(chunk)
    return tokens


def _derive_weak_points(scores: dict[str, float]) -> list[str]:
    """按低分项生成弱点评价。"""
    weak_points: list[str] = []
    if scores.get("accuracy", 0) < 3:
        weak_points.append("核心概念表达不完整")
    if scores.get("completeness", 0) < 3:
        weak_points.append("细节覆盖不足")
    if scores.get("depth", 0) < 3:
        weak_points.append("知识深度展开不足")
    if scores.get("scenario", 0) < 3:
        weak_points.append("场景化应用未覆盖")
    if not weak_points:
        weak_points.append("表述较完整")
    return weak_points


def _round_score(value: float) -> float:
    """统一评分精度，避免返回过长小数。"""
    return round(float(value), 2)


def _normalize_orchestration_run(run: dict[str, Any]) -> dict[str, Any]:
    """把 orchestration_runs 的 payload JSON 字符串标准化为对象。"""
    normalized = dict(run)
    payload = normalized.get("payload")
    if isinstance(payload, str):
        normalized["payload"] = _safe_json(payload)
    return normalized


def _safe_json(raw: str) -> Any:
    """安全解析 JSON，失败时返回原始字符串。"""
    try:
        return json.loads(raw)
    except Exception:
        return raw


def _orchestration_brief(data: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    """从闭环子结果中提取 UI 可直接展示的最小字段。"""
    if not isinstance(data, dict):
        return {}
    return {key: data.get(key) for key in keys if key in data}


def _summarize_orchestration_events(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """压缩事件日志，便于前端快速渲染。"""
    summary: list[dict[str, Any]] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        summary.append(
            {
                "agent": str(event.get("agent") or event.get("from_agent") or ""),
                "message": str(event.get("message") or event.get("message_type") or ""),
                "has_payload": bool(event.get("payload")),
            }
        )
    return summary


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "scripts.harness_server:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
