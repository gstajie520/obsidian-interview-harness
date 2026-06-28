#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""陪练伙伴 Agent。

BuddyAgent 提供轻量学习陪练能力：
- 3 级提示
- 通俗解释
- 学习状态下的鼓励与休息建议
"""

from __future__ import annotations

from typing import Any, Optional

from agents.core.base_agent import Agent

HINT_TEMPLATES: dict[int, dict[str, str]] = {
    1: {
        "type": "directional",
        "message": "先从问题本身最核心的定义或触发条件出发，不要先想着细节实现。",
    },
    2: {
        "type": "comparison",
        "message": "对比一个更熟悉的相邻概念，先找相似点，再找关键差异。",
    },
    3: {
        "type": "keyword",
        "message": "抓关键词：场景、约束、边界条件。先说核心定义，再举一个 10 秒例子。",
    },
}

SIMPLE_EXPLANATIONS: dict[str, str] = {
    "volatile": "把 volatile 想成“共享变量会尽快同步到主内存”。它主要解决可见性和顺序语义，不保证原子性。",
    "synchronized": "synchronized 可以理解为“这段逻辑有临界区锁”，同一时刻只允许一个线程执行。",
    "并发": "并发是多个任务轮流推进，不一定同时执行；关键是共享状态是否正确同步。",
    "hashmap": "HashMap 像查书架：先算桶位，再处理同桶冲突，核心是负载因子和扩容时机。",
}

STREAK_MESSAGES: dict[str, str] = {
    "streak_achievement": "鼓励：太好了，你连续答对 3 题，说明这类题的思路开始稳定了。",
    "breakthrough": "鼓励：这个点你突破了，说明你已经抓住了它和周边知识的边界关系。",
    "persistence": "鼓励：你已经连续学习多天了，形成了稳定的学习惯性，这很关键。",
    "default": "节奏很重要，先把一道题做到清楚，再向下一道迈进。",
}


class BuddyAgent(Agent):
    """陪练伙伴：负责提示、解释和学习陪伴。"""

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        # 保留标准 Agent 形态，方便与其他角色在 orchestrator 里统一调用。
        super().__init__("buddy", config)

    def give_hint(
        self,
        question_id: str,
        user_answer: str,
        level: int = 1,
    ) -> dict[str, Any]:
        """给出 1-3 级提示。

        level 对应学习者“卡住程度”：level1 方向引导，level2 对比提示，level3 关键词回收。
        """
        safe_level = max(1, min(int(level), 3))
        template = HINT_TEMPLATES[safe_level]
        return {
            "status": "ok",
            "question_id": question_id,
            "user_answer": user_answer,
            "hint_level": safe_level,
            "hint_type": template["type"],
            "hint": template["message"],
        }

    def explain_in_simple_terms(self, text: str) -> dict[str, Any]:
        """输出通俗语言解释。优先查找关键词映射，不命中则用通用模板。"""
        normalized = (text or "").strip().lower()
        explanation = self._find_simple_explanation(normalized)
        return {
            "status": "ok",
            "source_text": text,
            "message": f"通俗解释：{explanation}",
        }

    def generate_encouragement(
        self,
        trigger: str = "default",
        consecutive_success: int = 0,
    ) -> dict[str, Any]:
        """根据触发器和连对数生成鼓励。"""
        if consecutive_success >= 7:
            msg_key = "persistence"
        elif trigger == "breakthrough":
            msg_key = "breakthrough"
        elif consecutive_success >= 3:
            msg_key = "streak_achievement"
        else:
            msg_key = "default"
        return {
            "status": "ok",
            "trigger": trigger,
            "consecutive_success": consecutive_success,
            "message": STREAK_MESSAGES[msg_key],
        }

    def suggest_break(
        self,
        mood: str = "normal",
        consecutive_success: int = 0,
        session_minutes: int = 0,
    ) -> dict[str, Any]:
        """给出休息建议。

        规则很轻量：疲劳、超时或明显低质量输入时建议休息。
        """
        should_break = mood in {"tired", "burnout"} or session_minutes >= 60
        recommendation = "take_break" if should_break else "keep_going"
        message = (
            "建议 5~10 分钟离开屏幕，喝水并做眼保健，回来的复盘更稳。"
            if recommendation == "take_break"
            else "状态可继续，建议保持节奏，不要一次压太多题。"
        )
        return {
            "status": "ok",
            "recommendation": recommendation,
            "message": message,
        }

    def process(self, input_data: Any) -> Any:
        """同步入口，用 action 路由到具体陪练行为。"""
        if not isinstance(input_data, dict):
            return {
                "status": "error",
                "message": "陪练输入必须是 dict，类似 Java 里的 DTO。",
            }

        action = str(input_data.get("action") or "give_hint")
        if action == "give_hint":
            return self.give_hint(
                question_id=str(input_data.get("question_id") or ""),
                user_answer=str(input_data.get("user_answer") or ""),
                level=int(input_data.get("level") or 1),
            )
        if action == "explain_in_simple_terms":
            return self.explain_in_simple_terms(
                text=str(input_data.get("text") or ""),
            )
        if action == "generate_encouragement":
            return self.generate_encouragement(
                trigger=str(input_data.get("trigger") or "default"),
                consecutive_success=int(input_data.get("consecutive_success") or 0),
            )
        if action == "suggest_break":
            return self.suggest_break(
                mood=str(input_data.get("mood") or "normal"),
                consecutive_success=int(input_data.get("consecutive_success") or 0),
                session_minutes=int(input_data.get("session_minutes") or 0),
            )
        return {
            "status": "error",
            "message": f"不支持的陪练动作: {action}",
        }

    def _find_simple_explanation(self, normalized_text: str) -> str:
        """在映射中匹配关键词，找不到就返回通用解释。"""
        for keyword, message in SIMPLE_EXPLANATIONS.items():
            if keyword in normalized_text:
                return message
        return "这个问题可按“定义、适用场景、边界条件”三段说：先说是什么，再说什么时候用，最后说不适合用的场景。"
