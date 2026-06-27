#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 MOC (Map of Content) 索引层，用 Obsidian wikilink 构建思维导图
"""

import os
import sys
from pathlib import Path
from urllib.parse import quote
from collections import defaultdict

# Obsidian wikilink 中会被特殊解析的字符：
#   #  -> 标题锚点    ^ -> 块引用    [ ] -> 链接边界    | -> 别名分隔
# 含这些字符的标题改用 Markdown 链接 [显示](路径) 绕过解析
WIKILINK_UNSAFE = set('#^[]|')

# Windows 下确保中文输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def has_unsafe_chars(name: str) -> bool:
    """检查文件名是否含 wikilink 不安全字符"""
    return any(c in name for c in WIKILINK_UNSAFE)


def sanitize_wikilink(name: str) -> str:
    """
    去掉 .md 后缀，返回干净的标题
    """
    if name.endswith('.md'):
        name = name[:-3]
    return name


def collect_knowledge_base(base_path: Path) -> dict:
    """
    收集知识库结构：模块 → 题目列表
    """
    modules = {}
    all_basenames = {}  # basename -> [(module_name, md_file), ...] 用于检测跨模块重名

    # 遍历一级目录（模块）
    for module_dir in sorted(base_path.iterdir()):
        if not module_dir.is_dir():
            continue

        module_name = module_dir.name

        # 跳过隐藏目录
        if module_name.startswith('.'):
            continue

        # 模块自身的索引文件（module_dir/module_name.md），扫描时需排除
        module_index_file = module_dir / f"{module_name}.md"

        # 收集该模块下所有 .md 文件
        questions = []
        for md_file in sorted(module_dir.rglob('*.md')):
            # 跳过模块索引文件本身，避免重复运行时把它当成题目
            if md_file == module_index_file:
                continue

            # 相对于模块目录的路径
            rel_path = md_file.relative_to(module_dir)

            # 如果文件在子目录里，且子目录名和文件同名，说明是"题目+图片"结构
            # 例如: Java基础/✅Java是值传递还是引用传递？/✅Java是值传递还是引用传递？.md
            # 我们只取文件名作为题目
            question_title = sanitize_wikilink(md_file.name)

            questions.append({
                'title': question_title,
                'file': md_file,
                'rel_path': rel_path,
                'unsafe': has_unsafe_chars(md_file.name),  # 含特殊字符的标记为 unsafe
                'module': module_name
            })

            # 记录 basename，用于跨模块重名检测
            basename = md_file.name
            if basename not in all_basenames:
                all_basenames[basename] = []
            all_basenames[basename].append((module_name, md_file))

        if questions:
            modules[module_name] = questions

    # 第二遍：检测跨模块重名，将重名题目也标记为 unsafe
    for basename, locations in all_basenames.items():
        if len(locations) > 1:
            # 跨模块重名，用 wikilink 会歧义，改用 Markdown 链接
            for module_name, md_file in locations:
                # 找到该题目在 modules 中的位置并标记
                for q in modules[module_name]:
                    if q['file'] == md_file:
                        q['unsafe'] = True
                        break

    return modules


def generate_main_moc(modules: dict, output_path: Path):
    """
    生成主索引 Java面试.md
    """
    content = [
        "---",
        "type: moc",
        "tags: [java, interview, index]",
        "---",
        "",
        "# Java 面试知识库",
        "",
        "> 本文件是自动生成的 MOC (Map of Content) 主索引",
        "> 通过 Obsidian 图谱视图可以看到完整的知识结构",
        "",
        "## 🚀 快速入口",
        "",
        "- [[📊学习仪表盘]] — 用 Dataview 自动统计掌握度、待复习题目",
        "- [[🧭插件使用速查]] — Spaced Repetition / Breadcrumbs / Dataview / Excalidraw 操作手册",
        "",
        "## 📚 知识模块",
        "",
    ]

    # 统计信息
    total_questions = sum(len(qs) for qs in modules.values())
    content.extend([
        f"**共 {len(modules)} 个模块，{total_questions} 道题目**",
        "",
    ])

    # 按题目数量排序模块
    sorted_modules = sorted(modules.items(), key=lambda x: len(x[1]), reverse=True)

    # 分类显示
    categories = {
        "核心基础": ["Java基础", "Java并发", "JVM", "集合类"],
        "数据库": ["MySQL", "Redis", "Oracle"],
        "中间件": ["Spring", "SpringCloud", "MyBatis", "Dubbo", "Netty"],
        "消息队列": ["Kafka", "RocketMQ", "RabbitMQ"],
        "搜索&存储": ["ElasticSearch", "分库分表"],
        "分布式": ["分布式", "微服务", "Zookeeper", "配置中心"],
        "高性能": ["高并发", "高性能", "高可用", "本地缓存"],
        "系统基础": ["操作系统", "计算机网络", "数据结构"],
        "开发工具": ["Maven&Git", "IDEA", "容器", "Tomcat", "日志", "单元测试"],
        "实战应用": ["场景题", "编程题", "线上问题排查", "项目难点&亮点"],
        "架构设计": ["架构设计", "设计模式", "DDD"],
        "面试技巧": ["面经实战", "面试必备", "非技术问题", "智商题"],
        "其他": []
    }

    # 记录已分类的模块
    categorized = set()

    for cat_name, cat_modules in categories.items():
        if cat_name == "其他":
            continue

        # 找出该分类下存在的模块
        existing = [(m, modules[m]) for m in cat_modules if m in modules]
        if not existing:
            continue

        content.append(f"### {cat_name}")
        content.append("")

        for module_name, questions in existing:
            content.append(f"- [[{module_name}]] ({len(questions)} 题)")
            categorized.add(module_name)

        content.append("")

    # 其他未分类模块
    uncategorized = [m for m in sorted_modules if m[0] not in categorized]
    if uncategorized:
        content.append("### 其他")
        content.append("")
        for module_name, questions in uncategorized:
            content.append(f"- [[{module_name}]] ({len(questions)} 题)")
        content.append("")

    # 写入文件
    output_path.write_text('\n'.join(content), encoding='utf-8')
    print(f"✅ 生成主索引: {output_path}")


def render_question_link(q: dict) -> str:
    """
    渲染单个题目的链接。
    - 普通标题用 wikilink: [[标题]]
    - 含特殊字符 (# ^ [ ] |) 的标题改用 Markdown 链接，
      路径相对于模块索引文件（即模块目录），并做 URL 编码，避免 Obsidian 误解析
    """
    title = q['title']
    if not q['unsafe']:
        return f"- [[{title}]]"

    # rel_path 是相对模块目录的路径；模块索引文件也在模块目录下，故可直接使用
    rel = q['rel_path'].as_posix()
    # 保留 / 作为路径分隔，其余字符编码
    encoded = quote(rel)
    return f"- [{title}]({encoded})"


def generate_module_moc(module_name: str, questions: list, output_path: Path):
    """
    生成模块索引文件
    """
    content = [
        f"# {module_name}",
        "",
        f"> 本模块共 {len(questions)} 道题目",
        "",
        "## 📋 题目列表",
        "",
    ]

    # 按字母/数字排序
    for q in questions:
        content.append(render_question_link(q))

    content.extend([
        "",
        "---",
        "",
        "[[Java面试]] | 返回主索引",
    ])

    # 写入文件
    output_path.write_text('\n'.join(content), encoding='utf-8')
    print(f"  ✅ {module_name}: {len(questions)} 题")


def main():
    # 知识库路径
    base_path = Path(__file__).parent.parent / "知识库" / "Java面试"

    if not base_path.exists():
        print(f"❌ 知识库路径不存在: {base_path}")
        return 1

    print(f"📁 扫描知识库: {base_path}")
    print()

    # 收集结构
    modules = collect_knowledge_base(base_path)

    if not modules:
        print("❌ 未找到任何模块")
        return 1

    print(f"✅ 找到 {len(modules)} 个模块")
    print()

    # 生成主索引（放在 知识库/ 目录下）
    main_moc_path = base_path.parent / "Java面试.md"
    generate_main_moc(modules, main_moc_path)
    print()

    # 为每个模块生成索引文件
    print("📝 生成模块索引:")
    for module_name, questions in sorted(modules.items()):
        module_dir = base_path / module_name
        module_moc_path = module_dir / f"{module_name}.md"
        generate_module_moc(module_name, questions, module_moc_path)

    print()
    print("=" * 60)
    print("🎉 MOC 索引生成完成！")
    print()
    print("📍 主索引位置:", main_moc_path.relative_to(Path.cwd()))
    print()
    print("💡 使用方法:")
    print("   1. 在 Obsidian 中打开 Java面试.md")
    print("   2. 按 Ctrl+G 打开图谱视图")
    print("   3. 选择【局部图谱】，设置深度为 2-3")
    print("   4. 即可看到思维导图结构")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
