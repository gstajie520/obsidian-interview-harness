#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行面试界面 - 完整的 Agent Harness 体验

这是一个基于 Agent Harness 理论的智能面试助手：
- 面试官 Agent：智能出题、评分、追问
- Agent Loop：TAOR 循环（Think → Act → Observe → Reflect）
- Tool System：题库工具、记忆工具、评估工具
- Memory System：三层记忆（短期/中期/长期）
- Context System：上下文管理与自动压缩

使用方法：
    python main.py cli

兼容旧方式：
    python scripts/cli_interview.py

输入 'quit' 或 'q' 退出面试。
"""

import sys
import asyncio
from pathlib import Path

# Windows 控制台编码修复。很多 Windows 终端默认编码不是 UTF-8，
# 不处理时中文和图标可能显示乱码。
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding="utf-8",
        errors="replace",
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer,
        encoding="utf-8",
        errors="replace",
    )

# 添加项目根目录到 Python 路径，正式实现从根目录 `agents` 包导入。
# 直接运行 scripts/cli_interview.py 时，Python 默认只认识 scripts 目录；
# 加入 ROOT_DIR 后，下面才能 import agents。
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from agents.roles.interviewer_agent import InterviewerAgent
from agents.tools import memory_tools


def print_banner() -> None:
    """打印欢迎横幅。"""
    print("=" * 70)
    print(" " * 15 + "🎓 AI 面试陪练系统 - Agent Harness 版")
    print("=" * 70)
    print()
    print("【系统架构】")
    print("  推理层：Agent Loop（TAOR 循环）")
    print("  上下文层：Context Manager + Memory System")
    print("  工具层：Tool Registry + 题库工具 + 记忆工具")
    print("  数据层：SQLite（零配置）/ MySQL（可选）")
    print()
    print("【面试流程】")
    print("  1. 面试官 Agent 会调用工具获取你的薄弱模块")
    print("  2. 从薄弱模块中随机抽一道题")
    print("  3. 你作答后，Agent 会从四个维度评分（准确性/完整性/深度/场景化）")
    print("  4. 评分结果保存到数据库，SM-2 算法自动安排复习")
    print("  5. 下次面试会优先复习到期的题目")
    print()
    print("【命令】")
    print("  quit / q   - 退出面试")
    print("  help       - 显示帮助")
    print("  stats      - 查看学习统计")
    print()
    print("=" * 70)
    print()


def print_help() -> None:
    """打印帮助信息。"""
    print("\n" + "=" * 70)
    print("【帮助信息】")
    print()
    print("基本对话：")
    print("  - 直接输入你的答案，面试官会评估")
    print("  - 说'换一道题'或'下一题'，面试官会抽新题")
    print("  - 说'这题太难了'，面试官会换个模块")
    print()
    print("特殊命令：")
    print("  quit / q   - 退出面试")
    print("  help       - 显示此帮助")
    print("  stats      - 查看学习统计")
    print()
    print("工作原理：")
    print("  - 面试官是一个 Agent，有自己的推理循环（Agent Loop）")
    print("  - 它可以调用工具（get_weak_modules、get_question_from_module、save_evaluation）")
    print("  - 每次调用 LLM 后，如果需要调用工具，就执行工具并把结果反馈给 LLM")
    print("  - 这个循环一直持续到 LLM 给出最终回复（不再需要工具）")
    print("  - 这就是 TAOR 循环：Think（思考）→ Act（行动/调工具）→")
    print("                    Observe（观察结果）→ Reflect（反思/最终回复）")
    print()
    print("=" * 70 + "\n")


def print_stats(agent: InterviewerAgent) -> None:
    """打印学习统计。"""
    print("\n" + "=" * 70)
    print("【学习统计】")
    print()
    try:
        stats = memory_tools.get_learning_stats()
        print(f"  总题数: {stats['total']}")
        print(f"  已掌握: {stats['mastered']} 🟢")
        print(f"  复习中: {stats['reviewing']} 🟡")
        print(f"  学习中: {stats['learning']} 🔴")
        print(f"  未接触: {stats['untouched']} ⚪")
        print(f"  掌握率: {stats['mastery_rate']*100:.1f}%")
        print(f"  今日学习: {stats['today_count']} 题")
        print()

        # 薄弱模块
        weak = memory_tools.get_weak_modules(5)
        if weak:
            print(f"  薄弱模块（前5）: {', '.join(weak)}")

        # 待复习
        due = memory_tools.get_due_reviews(5)
        if due:
            print(f"  待复习题目: {len(due)} 道")
    except Exception as e:
        print(f"  统计查询失败: {e}")

    print("=" * 70 + "\n")


async def main():
    """主程序。

    这是 async 函数，因为面试过程会调用 AgentLoop。真实接入 LLM 时，
    网络请求属于 I/O 操作，用 async/await 更适合。
    """
    print_banner()

    # 初始化面试官 Agent
    print("正在初始化面试官 Agent...")
    try:
        agent = InterviewerAgent()
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        print("\n可能的原因：")
        print("  1. 配置文件不存在或格式错误")
        print("  2. API 密钥无效")
        print("  3. 依赖包未安装")
        print("\n请检查 .harness/config/harness.yaml 配置文件。")
        return

    print(f"✓ 面试官 Agent 准备就绪！")
    print(f"  - 模型: {agent.config.get('llm', {}).get('model', '未知')}")
    print(f"  - 上下文窗口: {agent.context_manager.max_tokens:,} tokens")
    print(f"  - 已注册工具: {len(agent.tool_registry.tools)} 个")
    print(f"  - 最大循环轮次: {agent.agent_loop.max_rounds}")
    print()

    # 开始面试
    print("【面试开始】")
    print("-" * 70)
    print()

    try:
        # 第一轮：自动开场。await 表示等待 Agent 完成一轮异步流程。
        print("面试官: ", end="", flush=True)
        response = await agent.start_interview()
        print(response)
        print()

        # 持续对话
        while True:
            # input() 会阻塞等待用户输入；strip() 去掉首尾空格和换行。
            user_input = input("你: ").strip()
            print()

            if not user_input:
                continue

            # 处理特殊命令
            if user_input.lower() in ["quit", "q", "exit"]:
                print("面试结束！感谢参与。")
                print_stats(agent)
                break

            if user_input.lower() == 'help':
                print_help()
                continue

            if user_input.lower() == 'stats':
                print_stats(agent)
                continue

            # 继续面试对话
            print("面试官: ", end="", flush=True)
            try:
                response = await agent.continue_interview(user_input)
                print(response)
                print()
            except KeyboardInterrupt:
                print("\n\n面试被中断。")
                break
            except Exception as e:
                print(f"\n\n❌ 错误: {e}")
                print("面试官遇到了问题，但你可以继续尝试...\n")

    except KeyboardInterrupt:
        print("\n\n面试被中断。")
    except Exception as e:
        print(f"\n\n❌ 严重错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n再见！👋")


if __name__ == "__main__":
    # 直接运行本文件时启动命令行程序；被测试或其他模块 import 时不启动。
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n程序被中断。")
    except Exception as e:
        print(f"\n启动失败: {e}")
        import traceback
        traceback.print_exc()
