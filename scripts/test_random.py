#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试：随机抽取一道题并显示
"""

import os
import random
import sys

# Windows 编码设置
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KNOWLEDGE_BASE = r"D:\ajie\study\AI-Knowledge\Java八股文"

def get_all_questions():
    """获取所有题目文件"""
    questions = []
    for root, dirs, files in os.walk(KNOWLEDGE_BASE):
        for file in files:
            if file.endswith('.md') and not file.startswith('.'):
                questions.append(os.path.join(root, file))
    return questions

def show_random_question():
    """显示一道随机题目"""
    questions = get_all_questions()

    if not questions:
        print("未找到题目文件")
        return

    # 随机选择
    filepath = random.choice(questions)

    # 读取文件
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取模块
    module = os.path.basename(os.path.dirname(filepath))
    filename = os.path.basename(filepath)

    print("=" * 60)
    print(f"模块: {module}")
    print(f"题目: {filename}")
    print("=" * 60)
    print()

    # 提取典型回答部分
    if "# 典型回答" in content:
        parts = content.split("# 典型回答", 1)
        if len(parts) > 1:
            answer = parts[1].split("#", 1)[0].strip()
            print("典型回答:")
            print(answer[:300] + "..." if len(answer) > 300 else answer)
    else:
        print(content[:500])

    print()
    print("=" * 60)
    print(f"文件路径: {filepath}")
    print(f"题库共有 {len(questions)} 道题")

if __name__ == '__main__':
    show_random_question()
