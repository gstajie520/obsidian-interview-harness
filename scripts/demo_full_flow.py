#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证脚本 - 模拟一次完整的面试流程

演示：
1. 面试官调用工具抽题
2. 用户作答
3. 面试官评分并保存到数据库
4. SM-2 算法计算下次复习时间
"""

import sys
import asyncio
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# demo 脚本和正式命令行入口一样，需要先把项目根目录放进导入路径。
from agents.roles.interviewer_agent import InterviewerAgent
from agents.tools import memory_tools


async def demo() -> None:
    """模拟一次完整流程。

    这个函数是 async，因为 InterviewerAgent 内部会调用 AgentLoop，而
    AgentLoop 可能发起网络请求或等待异步工具。
    """
    print("🎓 Agent Harness 完整流程演示")
    print("=" * 70)

    # 初始化
    agent = InterviewerAgent()
    print(f"\n✓ 面试官 Agent 已就绪")
    print(f"  模型: {agent.config['llm']['model']}")
    print(f"  工具数: {len(agent.tool_registry.tools)}")

    # 第一轮：抽题
    print("\n【第一轮】面试官抽题")
    print("-" * 70)
    response1 = await agent.start_interview("请从 Java基础 模块给我出一道题")
    print(f"面试官: {response1}")

    # 第二轮：用户作答
    print("\n【第二轮】用户作答")
    print("-" * 70)
    user_answer = """
finally 中的代码不一定会执行。
会执行的情况：正常的 try-catch-finally 流程。
不会执行的情况：
1. System.exit() 被调用
2. JVM 崩溃
3. 线程被 kill
4. 电源断电等物理原因
    """.strip()

    print(f"你: {user_answer}")

    # 第三轮：面试官评分
    print("\n【第三轮】面试官评分")
    print("-" * 70)
    response2 = await agent.continue_interview(user_answer)
    print(f"面试官: {response2}")

    # 查看数据库
    print("\n【数据库验证】")
    print("-" * 70)
    stats = memory_tools.get_learning_stats()
    print(f"✓ 数据已保存到 SQLite")
    print(f"  今日学习: {stats['today_count']} 题")
    print(f"  总题数: {stats['total']}")

    print("\n" + "=" * 70)
    print("🎉 完整流程演示成功！")
    print("\n运行以下命令开始真实面试：")
    print("  python scripts/cli_interview.py")


if __name__ == "__main__":
    # asyncio.run 会创建事件循环并执行 demo 协程。
    asyncio.run(demo())
