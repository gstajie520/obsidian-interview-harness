#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 面试陪练系统
随机抽题，记录答题情况，更新复习进度
"""

import os
import sys
import re
import random
import yaml
from datetime import datetime

# Windows 控制台编码设置
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

KNOWLEDGE_BASE = r"D:\ajie\study\AI-Knowledge\Java八股文"

def parse_frontmatter(content):
    """解析 YAML frontmatter"""
    if not content.startswith('---\n'):
        return None, content

    try:
        end = content.find('\n---\n', 4)
        if end == -1:
            return None, content

        frontmatter_str = content[4:end]
        body = content[end + 5:]

        metadata = yaml.safe_load(frontmatter_str)
        return metadata, body
    except:
        return None, content

def update_frontmatter(filepath, mastery_level):
    """更新题目的复习记录"""

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    metadata, body = parse_frontmatter(content)

    if metadata is None:
        print(f"❌ 该题目缺少元数据，请先运行 add_metadata.py")
        return False

    # 更新复习记录
    metadata['熟练度'] = mastery_level
    metadata['上次复习'] = datetime.now().strftime('%Y-%m-%d')
    metadata['复习次数'] = metadata.get('复习次数', 0) + 1

    # 重新生成 frontmatter
    new_frontmatter = "---\n" + yaml.dump(metadata, allow_unicode=True, sort_keys=False) + "---\n\n"
    new_content = new_frontmatter + body

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True

def get_random_question(module=None, exclude_mastered=False):
    """随机获取一道题"""

    all_files = []

    for root, dirs, files in os.walk(KNOWLEDGE_BASE):
        if module and module not in root:
            continue

        for file in files:
            if file.endswith('.md') and file.startswith('✅'):
                filepath = os.path.join(root, file)

                # 如果设置排除已掌握，检查元数据
                if exclude_mastered:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    metadata, _ = parse_frontmatter(content)
                    if metadata and metadata.get('熟练度') == '🟢':
                        continue

                all_files.append(filepath)

    if not all_files:
        return None

    return random.choice(all_files)

def practice_mode():
    """练习模式"""

    print("\n" + "="*60)
    print("🎯 Java 八股文 AI 陪练系统")
    print("="*60 + "\n")

    print("选择练习模式：")
    print("1. 随机抽题（全部）")
    print("2. 只练习未掌握的题")
    print("3. 指定模块练习")
    print("0. 退出")

    choice = input("\n请选择 (0-3): ").strip()

    if choice == '0':
        return

    exclude_mastered = (choice == '2')
    module = None

    if choice == '3':
        print("\n可选模块：")
        modules = set()
        for root, dirs, files in os.walk(KNOWLEDGE_BASE):
            if root != KNOWLEDGE_BASE:
                module_name = os.path.basename(root)
                modules.add(module_name)

        for i, m in enumerate(sorted(modules), 1):
            print(f"{i}. {m}")

        module_choice = input("\n请输入模块名称: ").strip()
        module = module_choice

    # 开始练习
    questions_answered = 0

    while True:
        filepath = get_random_question(module, exclude_mastered)

        if not filepath:
            print("\n❌ 没有找到符合条件的题目")
            break

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        metadata, body = parse_frontmatter(content)

        question_title = metadata.get('题目', os.path.basename(filepath))
        module_name = metadata.get('模块', '')

        print("\n" + "="*60)
        print(f"📝 题目 #{questions_answered + 1}")
        print(f"📁 模块: {module_name}")
        print(f"❓ {question_title}")
        print("="*60 + "\n")

        input("⏸️  思考完毕后按回车查看答案...")

        # 显示答案
        print("\n" + "-"*60)
        print("📖 参考答案：")
        print("-"*60)

        # 提取"典型回答"部分
        typical_answer = ""
        if "# 典型回答" in body:
            parts = body.split("# 典型回答", 1)
            if len(parts) > 1:
                answer_part = parts[1].split("#", 1)[0]
                typical_answer = answer_part.strip()
                print(typical_answer[:500] + "..." if len(typical_answer) > 500 else typical_answer)
        else:
            print(body[:500] + "...")

        print("\n" + "-"*60)

        # 评价掌握程度
        print("\n你的掌握程度：")
        print("1. 🟢 已掌握（可流畅回答）")
        print("2. 🟡 需复习（基本会答）")
        print("3. 🔴 待学习（不会或很模糊）")
        print("s. 跳过此题")
        print("q. 结束练习")

        mastery = input("\n请选择 (1-3/s/q): ").strip().lower()

        if mastery == 'q':
            break
        elif mastery == 's':
            continue
        elif mastery in ['1', '2', '3']:
            mastery_map = {'1': '🟢', '2': '🟡', '3': '🔴'}
            update_frontmatter(filepath, mastery_map[mastery])
            questions_answered += 1
            print(f"\n✅ 已记录！你已练习 {questions_answered} 道题")
        else:
            print("❌ 无效选择，跳过此题")

    print(f"\n✨ 本次练习结束！共完成 {questions_answered} 道题")
    print(f"💪 继续加油！")

if __name__ == '__main__':
    practice_mode()
