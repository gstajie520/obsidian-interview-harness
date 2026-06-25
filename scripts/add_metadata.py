#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Java 八股文背题进度追踪系统
为每道题目添加 YAML frontmatter，记录学习进度
"""

import os
import re
from datetime import datetime

# 知识库路径
KNOWLEDGE_BASE = r"D:\ajie\study\AI-Knowledge\Java八股文"

def add_frontmatter_to_file(filepath):
    """为单个文件添加 YAML frontmatter"""

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 如果已经有 frontmatter，跳过
    if content.startswith('---\n'):
        return False

    # 提取题目标题（去掉文件名前缀）
    filename = os.path.basename(filepath)
    # 移除所有 emoji 和特殊字符
    title = re.sub(r'[^\w\s一-鿿,.?!()（），。？！、]', '', filename).replace('.md', '').strip()

    # 获取所属模块
    module = os.path.basename(os.path.dirname(filepath))

    # 创建 frontmatter
    frontmatter = f"""---
题目: "{title}"
模块: "{module}"
熟练度: ⚪
上次复习:
复习次数: 0
标签: []
难度:
重要程度:
相关题目: []
---

"""

    # 添加到文件开头
    new_content = frontmatter + content

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True

def process_all_files():
    """处理所有 Markdown 文件"""

    print("Processing...")

    total = 0
    processed = 0

    for root, dirs, files in os.walk(KNOWLEDGE_BASE):
        for file in files:
            if file.endswith('.md'):
                total += 1
                filepath = os.path.join(root, file)

                if add_frontmatter_to_file(filepath):
                    processed += 1
                    if processed % 50 == 0:
                        print(f"Progress: {processed}/{total}")

    print(f"\nDone!")
    print(f"Total: {total}")
    print(f"Processed: {processed}")
    print(f"Skipped: {total - processed}")

if __name__ == '__main__':
    process_all_files()
