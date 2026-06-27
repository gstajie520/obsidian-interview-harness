#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""复习调度器 Agent。

SchedulerAgent 负责“什么时候复习”和“先复习哪一道”。它不直接写 SQL，
而是调用 `memory_tools`。这样分层更清楚：
- SchedulerAgent：像 Java Service，编排业务流程。
- memory_tools：像 Repository/DAO，负责数据库读写。
"""

from __future__ import annotations

from typing import Any, Optional

from agents.core.base_agent import Agent
from agents.tools import memory_tools


class SchedulerAgent(Agent):
    """复习调度器：负责复习时间和优先级规划。"""

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        # 继承 Agent 的通用能力：配置、Prompt、LLM 客户端。
        # 当前调度逻辑不需要调用 LLM，但保留标准 Agent 形态，方便未来让
        # LLM 解释“为什么今天要复习这些题”。
        super().__init__("scheduler", config)

    def get_daily_review_list(self, limit: int = 20) -> dict[str, Any]:
        """生成每日复习清单。

        这里的清单来自 `memory_tools.get_due_reviews()`。底层 SQL 已经按
        “过期天数更多、平均分更低”排序；Scheduler 在这里补充前端和用户
        更容易理解的 priority_rank/reason/summary。
        """
        reviews = memory_tools.get_due_reviews(limit)
        items = [
            {
                **review,
                "priority_rank": index + 1,
                "reason": "已到期复习",
            }
            for index, review in enumerate(reviews)
        ]
        count = len(items)
        summary = (
            f"今日有 {count} 道题需要复习。"
            if count
            else "今日没有到期复习题。"
        )
        return {
            "items": items,
            "count": count,
            "summary": summary,
        }

    def schedule_next_review(
        self,
        question_id: str,
        performance: float,
    ) -> dict[str, Any]:
        """根据本次表现更新下一次复习时间。

        performance 是 0-5 分。真正的 SM-2 计算在 memory_tools 里完成；
        这里负责调用它，并把更新后的题目元数据返回给调用方。
        """
        memory_tools.calculate_next_review(question_id, performance)
        metadata = memory_tools.get_question_metadata(question_id)
        if metadata is None:
            return {
                "status": "not_found",
                "question_id": question_id,
            }
        return {
            "status": "scheduled",
            "question_id": question_id,
            "next_review": metadata.get("next_review"),
            "review_interval_days": metadata.get("review_interval_days"),
            "repetitions": metadata.get("repetitions"),
            "easiness_factor": metadata.get("easiness_factor"),
        }

    def process(self, input_data: Any) -> Any:
        """同步入口，用 action 路由到具体调度能力。

        input_data 约定为 dict，类似 Java Controller/Service 中收到的 DTO。
        目前支持：
        - {"action": "daily_review_list", "limit": 20}
        - {"action": "schedule_next_review", "question_id": "...", "performance": 4}
        """
        data = input_data if isinstance(input_data, dict) else {}
        action = str(data.get("action") or "daily_review_list")

        if action == "daily_review_list":
            return self.get_daily_review_list(
                limit=int(data.get("limit") or 20),
            )
        if action == "schedule_next_review":
            return self.schedule_next_review(
                question_id=str(data.get("question_id") or ""),
                performance=float(data.get("performance") or 0),
            )

        return {
            "status": "error",
            "message": f"不支持的调度动作: {action}",
        }
