#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量给题目和模块索引添加 frontmatter，激活 Dataview/Spaced Repetition/Breadcrumbs 插件
"""

import os
import sys
from pathlib import Path
import re

# Windows 下确保中文输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def has_frontmatter(content: str) -> bool:
    """检查文件是否已有 frontmatter"""
    return content.startswith('---\n') or content.startswith('---\r\n')


def generate_question_tags(module_name: str) -> list:
    """
    根据模块名生成标签
    """
    tags = ['java', 'interview']

    # 核心技术标签映射
    tag_map = {
        'Java基础': ['java-basic'],
        'Java并发': ['java-concurrency', 'thread'],
        'JVM': ['jvm', 'gc'],
        '集合类': ['collection'],
        'MySQL': ['mysql', 'database'],
        'Redis': ['redis', 'cache'],
        'Spring': ['spring'],
        'SpringCloud': ['spring-cloud', 'microservice'],
        'MyBatis': ['mybatis', 'orm'],
        'Kafka': ['kafka', 'mq'],
        'RocketMQ': ['rocketmq', 'mq'],
        'RabbitMQ': ['rabbitmq', 'mq'],
        'Dubbo': ['dubbo', 'rpc'],
        'Netty': ['netty', 'network'],
        'ElasticSearch': ['elasticsearch', 'search'],
        '分布式': ['distributed'],
        '微服务': ['microservice'],
        '高并发': ['high-concurrency'],
        '高性能': ['performance'],
        '操作系统': ['os'],
        '计算机网络': ['network'],
        '数据结构': ['data-structure'],
        '算法': ['algorithm'],
        '设计模式': ['design-pattern'],
    }

    if module_name in tag_map:
        tags.extend(tag_map[module_name])

    return tags


def add_question_frontmatter(file_path: Path, module_name: str) -> bool:
    """
    给题目文件添加 frontmatter
    """
    content = file_path.read_text(encoding='utf-8')

    # 如果已有 frontmatter，跳过
    if has_frontmatter(content):
        return False

    # 生成标签
    tags = generate_question_tags(module_name)
    tags_str = ', '.join(tags)

    # 构造 frontmatter
    frontmatter = f"""---
up: "[[{module_name}]]"
tags: [{tags_str}]
mastery: ⚪
---

"""

    # 插入到文件开头
    new_content = frontmatter + content
    file_path.write_text(new_content, encoding='utf-8')
    return True


def add_module_frontmatter(file_path: Path, module_name: str) -> bool:
    """
    给模块索引文件添加 frontmatter
    """
    content = file_path.read_text(encoding='utf-8')

    # 如果已有 frontmatter，跳过
    if has_frontmatter(content):
        return False

    # 构造 frontmatter
    frontmatter = f"""---
up: "[[Java面试]]"
type: moc
module: {module_name}
---

"""

    # 插入到文件开头
    new_content = frontmatter + content
    file_path.write_text(new_content, encoding='utf-8')
    return True


def add_main_index_frontmatter(file_path: Path) -> bool:
    """
    给主索引添加 frontmatter
    """
    content = file_path.read_text(encoding='utf-8')

    # 如果已有 frontmatter，跳过
    if has_frontmatter(content):
        return False

    # 构造 frontmatter
    frontmatter = """---
type: moc
tags: [java, interview, index]
---

"""

    # 插入到文件开头
    new_content = frontmatter + content
    file_path.write_text(new_content, encoding='utf-8')
    return True


def main():
    # 知识库路径
    base_path = Path(__file__).parent.parent / "知识库" / "Java面试"
    main_index = base_path.parent / "Java面试.md"

    if not base_path.exists():
        print(f"❌ 知识库路径不存在: {base_path}")
        return 1

    print("📁 开始批量添加 frontmatter")
    print()

    # 统计
    stats = {
        'main_index': 0,
        'module_index': 0,
        'questions': 0,
        'skipped': 0
    }

    # 1. 处理主索引
    if main_index.exists():
        if add_main_index_frontmatter(main_index):
            stats['main_index'] = 1
            print(f"✅ 主索引: {main_index.name}")
        else:
            stats['skipped'] += 1

    print()
    print("📝 处理模块:")

    # 2. 遍历模块
    for module_dir in sorted(base_path.iterdir()):
        if not module_dir.is_dir():
            continue

        module_name = module_dir.name

        # 跳过隐藏目录
        if module_name.startswith('.'):
            continue

        # 模块索引文件
        module_index = module_dir / f"{module_name}.md"

        # 处理模块索引
        if module_index.exists():
            if add_module_frontmatter(module_index, module_name):
                stats['module_index'] += 1

        # 处理该模块下所有题目
        question_count = 0
        for md_file in module_dir.rglob('*.md'):
            # 跳过模块索引本身
            if md_file == module_index:
                continue

            # 添加 frontmatter
            if add_question_frontmatter(md_file, module_name):
                stats['questions'] += 1
                question_count += 1
            else:
                stats['skipped'] += 1

        print(f"  ✅ {module_name}: {question_count} 题")

    print()
    print("=" * 60)
    print("🎉 Frontmatter 添加完成！")
    print()
    print(f"📊 统计:")
    print(f"  主索引:   {stats['main_index']} 个")
    print(f"  模块索引: {stats['module_index']} 个")
    print(f"  题目:     {stats['questions']} 道")
    print(f"  跳过:     {stats['skipped']} 个（已有 frontmatter）")
    print()
    print("💡 现在可以使用:")
    print("  1. Spaced Repetition - 间隔复习所有题目")
    print("  2. Breadcrumbs - 每题顶部显示所属模块导航")
    print("  3. Dataview - 查询和筛选题目")
    print()
    print("🔍 Dataview 示例查询（在任意笔记里写）:")
    print()
    print("```dataview")
    print("TABLE mastery AS 掌握度, file.folder AS 模块")
    print("FROM #java")
    print("WHERE mastery = \"⚪\"")
    print("LIMIT 10")
    print("```")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
