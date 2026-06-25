#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
面试官 Agent - 智能出题和评估

这是一个完整的 Agent Harness 实现，整合了：
- Agent Loop（TAOR 循环）
- Tool Registry（工具注册系统）
- Context Manager（上下文管理）
- Memory System（记忆系统）
"""

import asyncio
import datetime
from typing import Any, Optional

from agents.core.agent_loop import AgentLoop
from agents.core.base_agent import Agent
from agents.core.context_manager import ContextManager
from agents.core.tool_registry import ToolRegistry
from agents.tools import memory_tools, question_tools


class InterviewerAgent(Agent):
    """面试官 Agent - 完整的 Harness 实现

    架构：
    - 推理与编排层：Agent Loop（TAOR 循环）
    - 上下文与记忆层：Context Manager + Memory System
    - 工具层：Tool Registry + 题库工具 + 记忆工具
    """

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__("interviewer", config)

        # 初始化工具注册表
        self.tool_registry = ToolRegistry()
        self._register_tools()

        # 初始化上下文管理器
        llm_config = self.config.get("llm", {})
        context_config = self.config.get("context", {})
        context_model = context_config.get("model") or llm_config.get(
            "model",
            "deepseek-chat",
        )
        summary_model = context_config.get("summary_model") or context_model

        self.context_manager = ContextManager(
            # 这些值都可以在 .harness/config/harness.yaml 的 context 段调整。
            max_tokens=int(context_config.get("max_tokens", 128000)),
            threshold=float(context_config.get("threshold", 0.92)),
            model=context_model,
            summary_model=summary_model,
            retain_recent_rounds=int(
                context_config.get("retain_recent_rounds", 10)
            ),
        )

        # 初始化 Agent Loop
        self.agent_loop = AgentLoop(
            agent=self,
            tool_registry=self.tool_registry,
            max_rounds=30,
            context_manager=self.context_manager,
        )

        # 当前会话状态
        self.current_question = None
        self.session_id = None

    def _register_tools(self) -> None:
        """注册面试官可用的工具

        遵循工具注册最佳实践：
        1. 每个工具有清晰的 name 和 description
        2. 工具之间职责分离
        3. 返回结构化数据（dict）
        """

        @self.tool_registry.register(
            name="get_weak_modules",
            description="获取用户的薄弱模块列表，返回掌握率最低的模块",
        )
        def get_weak_modules(limit: int = 5) -> dict[str, Any]:
            """获取薄弱模块"""
            try:
                modules = memory_tools.get_weak_modules(limit)
                if not modules:
                    return {
                        "status": "no_data",
                        "message": "还没有学习记录，建议从任意模块开始",
                        "modules": [],
                    }
                return {
                    "status": "success",
                    "modules": modules,
                    "count": len(modules),
                }
            except Exception as e:
                return {"status": "error", "message": str(e)}

        @self.tool_registry.register(
            name="get_question_from_module",
            description="从指定模块随机获取一道题目，不返回完整答案防止泄露",
        )
        def get_question_from_module(
            module: Optional[str] = None,
        ) -> dict[str, Any]:
            """从模块获取题目"""
            try:
                q = question_tools.get_random_question(module=module)
                if not q:
                    return {
                        "status": "not_found",
                        "message": f'模块 "{module}" 中没有找到题目',
                    }

                # 存储当前题目到 Agent 状态
                self.current_question = q

                # 返回题目（不包含完整答案）
                preview = (
                    q.content[:200] + "..."
                    if len(q.content) > 200
                    else q.content
                )
                return {
                    "status": "success",
                    "question_id": q.question_id,
                    "title": q.title,
                    "module": q.module,
                    "preview": preview,
                }
            except Exception as e:
                return {"status": "error", "message": str(e)}

        @self.tool_registry.register(
            name="get_all_modules",
            description="获取所有可用的模块列表",
        )
        def get_all_modules() -> dict[str, Any]:
            """获取所有模块"""
            try:
                modules = question_tools.get_all_modules()
                return {
                    "status": "success",
                    "modules": modules,
                    "count": len(modules),
                }
            except Exception as e:
                return {"status": "error", "message": str(e)}

        @self.tool_registry.register(
            name="save_evaluation",
            description="保存用户答题的评估结果，包括四维度评分和薄弱点",
        )
        def save_evaluation(
            question_id: str,
            user_answer: str,
            score_accuracy: float,
            score_completeness: float,
            score_depth: float,
            score_scenario: float,
            weak_points: str = "",
        ) -> dict[str, Any]:
            """保存评估结果

            Args:
                question_id: 题目 ID
                user_answer: 用户的答案
                score_accuracy: 准确性评分 (0-5)
                score_completeness: 完整性评分 (0-5)
                score_depth: 深度评分 (0-5)
                score_scenario: 场景化评分 (0-5)
                weak_points: 薄弱点描述（逗号分隔）
            """
            try:
                # 构建评分字典
                scores = {
                    "accuracy": float(score_accuracy),
                    "completeness": float(score_completeness),
                    "depth": float(score_depth),
                    "scenario": float(score_scenario),
                }

                # 解析薄弱点
                weak_list = [
                    point.strip()
                    for point in weak_points.split(",")
                    if point.strip()
                ]

                # 获取题目信息
                q = self.current_question
                if not q:
                    return {
                        "status": "error",
                        "message": "当前没有活跃的题目",
                    }

                # 保存学习记录
                record_id = memory_tools.add_learning_record(
                    question_id=question_id,
                    module=q.module,
                    user_answer=user_answer,
                    scores=scores,
                    session_id=self.session_id or "default",
                    weak_points=weak_list,
                    duration_seconds=0,
                )

                # 更新 SM-2 复习调度
                overall_score = sum(scores.values()) / len(scores)
                memory_tools.calculate_next_review(question_id, overall_score)

                return {
                    "status": "success",
                    "record_id": record_id,
                    "overall_score": overall_score,
                    "message": "评估结果已保存",
                }
            except Exception as e:
                return {"status": "error", "message": str(e)}

    async def start_interview(
        self,
        initial_message: Optional[str] = None,
    ) -> str:
        """开始面试会话

        Args:
            initial_message: 用户的初始消息

        Returns:
            面试官的回复
        """
        # 生成会话 ID
        self.session_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        memory_tools.create_session(self.session_id, "interviewer")

        # 默认开场消息
        if not initial_message:
            initial_message = "你好！我准备开始面试了，请帮我选一道薄弱模块的题目。"

        # 运行 Agent Loop
        response = await self.agent_loop.run(initial_message)
        return response

    async def continue_interview(self, user_message: str) -> str:
        """继续面试对话

        Args:
            user_message: 用户的消息（答案或指令）

        Returns:
            面试官的回复
        """
        response = await self.agent_loop.run(user_message)
        return response

    def reset(self) -> None:
        """重置面试会话"""
        self.agent_loop.clear_messages()
        self.current_question = None
        self.session_id = None

    def process(self, input_data: Any) -> str:
        """同步接口（兼容基类）"""
        return asyncio.run(self.start_interview(input_data))


if __name__ == "__main__":
    # 测试
    print("="*60)
    print("面试官 Agent 测试")
    print("="*60)

    async def test() -> None:
        agent = InterviewerAgent()
        print("\n✓ Agent 初始化成功")
        print(f"  - 工具数量: {len(agent.tool_registry.tools)}")
        print(f"  - 上下文窗口: {agent.context_manager.max_tokens} tokens")
        print(f"  - 最大轮次: {agent.agent_loop.max_rounds}")

        # 测试工具注册
        print("\n✓ 已注册工具:")
        for tool_name in agent.tool_registry.tools.keys():
            print(f"  - {tool_name}")

        print("\n✓ 面试官 Agent 准备就绪！")
        print("\n运行 'python scripts/cli_interview.py' 开始面试")

    asyncio.run(test())
