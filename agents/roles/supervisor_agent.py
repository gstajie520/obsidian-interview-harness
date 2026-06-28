#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""监督助手 Agent。

SupervisorAgent 负责把数据库里的学习数据整理成“人能看懂的报告”。
它本身不直接写 SQL，而是调用 `memory_tools`：
- SupervisorAgent：像 Java Service，负责组织报告结构。
- memory_tools：像 Repository/DAO，负责真正读取数据库。
"""

from __future__ import annotations

from typing import Any, Optional

from agents.core.base_agent import Agent
from agents.tools import memory_tools


class SupervisorAgent(Agent):
    """监督助手：负责学习报告和阶段性目标管理。"""

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        # 保留标准 Agent 形态。当前报告先用确定性代码生成，未来可以再让
        # LLM 基于这些结构化数据生成更自然的教练建议。
        super().__init__("supervisor", config)

    def generate_daily_report(self, limit: int = 5) -> dict[str, Any]:
        """生成每日学习简报。

        limit 控制薄弱模块和到期复习题最多展示几条。返回 dict 是为了让
        CLI、API、未来 Web UI 都能复用；markdown 字段则方便后续导出到
        Obsidian。
        """
        context = self._collect_report_context(limit)
        markdown = self._render_daily_markdown(context)
        return {
            "report_type": "daily",
            "stats": context["stats"],
            "weak_modules": context["weak_modules"],
            "due_reviews": context["due_reviews"],
            "due_review_count": len(context["due_reviews"]),
            "markdown": markdown,
        }

    def generate_weekly_report(self, limit: int = 5) -> dict[str, Any]:
        """生成周报 Markdown。

        当前版本先基于已有累计数据生成“阶段性总结”。等后续 memory_tools
        增加按日期聚合能力后，这里可以扩展成真正的 7 天趋势分析。
        """
        context = self._collect_report_context(limit)
        markdown = self._render_weekly_markdown(context)
        return {
            "report_type": "weekly",
            "stats": context["stats"],
            "weak_modules": context["weak_modules"],
            "due_reviews": context["due_reviews"],
            "due_review_count": len(context["due_reviews"]),
            "markdown": markdown,
        }

    def process(self, input_data: Any) -> Any:
        """同步入口，用 action 路由到具体报告能力。

        input_data 约定为 dict，类似 Java Controller 收到的 DTO。
        目前支持：
        - {"action": "daily_report", "limit": 5}
        - {"action": "weekly_report", "limit": 5}
        """
        data = input_data if isinstance(input_data, dict) else {}
        action = str(data.get("action") or "daily_report")
        limit = int(data.get("limit") or 5)

        if action == "daily_report":
            return self.generate_daily_report(limit=limit)
        if action == "weekly_report":
            return self.generate_weekly_report(limit=limit)

        return {
            "status": "error",
            "message": f"不支持的监督动作: {action}",
        }

    def _collect_report_context(self, limit: int) -> dict[str, Any]:
        """统一收集报告需要的数据。

        这样日报和周报不会重复写三次查询逻辑。可以类比 Java Service 中
        先组装一个 `ReportContext` 对象，再交给不同 render 方法输出。
        """
        return {
            "stats": memory_tools.get_learning_stats(),
            "weak_modules": memory_tools.get_weak_modules(limit),
            "due_reviews": memory_tools.get_due_reviews(limit),
        }

    def _render_daily_markdown(self, context: dict[str, Any]) -> str:
        """把结构化数据渲染成每日简报 Markdown。"""
        stats = context["stats"]
        weak_modules = context["weak_modules"]
        due_reviews = context["due_reviews"]
        return "\n".join(
            [
                "# 每日学习简报",
                "",
                "## 今日概览",
                f"- 今日已练习 {stats['today_count']} 题。",
                f"- 题库总数 {stats['total']} 题。",
                f"- 已掌握 {stats['mastered']} 题，掌握率 {self._percent(stats['mastery_rate'])}。",
                "",
                "## 薄弱模块",
                self._format_weak_modules(weak_modules),
                "",
                "## 今日复习",
                self._format_due_reviews(due_reviews),
                "",
                "## 明日建议",
                self._build_next_step_advice(weak_modules, due_reviews),
            ]
        )

    def _render_weekly_markdown(self, context: dict[str, Any]) -> str:
        """把结构化数据渲染成周报 Markdown。"""
        stats = context["stats"]
        weak_modules = context["weak_modules"]
        due_reviews = context["due_reviews"]
        return "\n".join(
            [
                "# 学习周报",
                "",
                "## 本周概览",
                f"- 当前已登记 {stats['total']} 道题。",
                f"- 已掌握 {stats['mastered']} 道题。",
                f"- 复习中 {stats['reviewing']} 道题。",
                f"- 学习中 {stats['learning']} 道题。",
                f"- 还有 {stats['untouched']} 道题未开始。",
                "",
                "## 重点薄弱模块",
                self._format_weak_modules(weak_modules),
                "",
                "## 待复习题目",
                self._format_due_reviews(due_reviews),
                "",
                "## 下周建议",
                self._build_next_step_advice(weak_modules, due_reviews),
            ]
        )

    def _format_weak_modules(self, weak_modules: list[str]) -> str:
        """格式化薄弱模块列表。"""
        if not weak_modules:
            return "- 暂时没有薄弱模块数据，先完成几道题再分析。"
        return "\n".join(
            f"- {index}. {module}"
            for index, module in enumerate(weak_modules, start=1)
        )

    def _format_due_reviews(self, due_reviews: list[dict[str, Any]]) -> str:
        """格式化到期复习题列表。"""
        if not due_reviews:
            return "- 今日没有到期复习题。"
        lines = []
        for index, item in enumerate(due_reviews, start=1):
            title = item.get("title") or item.get("question_id")
            module = item.get("module") or "未分类"
            lines.append(f"- {index}. [{module}] {title}")
        return "\n".join(lines)

    def _build_next_step_advice(
        self,
        weak_modules: list[str],
        due_reviews: list[dict[str, Any]],
    ) -> str:
        """根据当前数据生成下一步建议。"""
        if due_reviews:
            return "先完成到期复习题，再从薄弱模块补 1-2 道新题。"
        if weak_modules:
            return f"优先复盘 {weak_modules[0]} 模块，保持小步快跑。"
        return "先完成一次面试练习，系统有数据后会给出更准确建议。"

    def _percent(self, value: float) -> str:
        """把 0-1 的比例格式化为百分比字符串。"""
        return f"{value * 100:.1f}%"
