#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导入题库元数据到数据库。

脚本只写入题目 ID、路径、模块和标题，不会改动 Markdown 原文。默认读取
`.harness/config/knowledge_bases.yaml` 中启用的 Java 知识库。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

# 因为脚本在 scripts/ 目录下直接运行时，Python 默认只把 scripts/
# 加入搜索路径。上面手动加入项目根目录后，才能导入 agents 包。
from agents.tools import memory_tools, question_tools  # noqa: E402


def parse_args() -> argparse.Namespace:
    """解析命令行参数。

    argparse 是 Python 标准库，作用类似 Java 里常见的 CLI 参数解析库。
    """
    parser = argparse.ArgumentParser(description="导入题库元数据")
    parser.add_argument(
        "--knowledge-base",
        default=None,
        help="knowledge_bases.yaml 中的知识库键名，例如 java_interview",
    )
    parser.add_argument(
        "--module",
        default=None,
        help="只导入指定模块；不传则导入全部模块",
    )
    return parser.parse_args()


def import_questions(module: Optional[str] = None) -> int:
    """导入题目元数据，返回本次新增的题目数量。

    这里的“新增”很重要：重复运行导入脚本时，已经存在的题不会重复计数。
    这样用户看到 `0 条` 时，就知道不是失败，而是数据库已经导入过了。
    """
    # 如果传了 module，只导入这一个模块；否则导入全部模块。
    modules = [module] if module else question_tools.get_all_modules()
    imported_count = 0

    for module_name in modules:
        file_paths = question_tools.get_questions_in_module(module_name)
        for file_path in file_paths:
            question = question_tools.parse_question_file(file_path)
            if question is None:
                continue

            # 这里只初始化元数据，真正答题记录由面试过程写入。
            # inserted 是 bool 类型，类似 Java 里 boolean inserted。
            # True 表示本次插入成功；False 表示题目已存在，被数据库忽略。
            inserted = memory_tools.init_question_metadata(
                question_id=question.question_id,
                file_path=question.file_path,
                module=question.module,
                title=question.title,
            )
            if inserted:
                imported_count += 1

    return imported_count


def main() -> None:
    """脚本入口。"""
    args = parse_args()
    if args.knowledge_base:
        switched = question_tools.set_knowledge_base(args.knowledge_base)
        if not switched:
            raise SystemExit(f"知识库不存在或路径不可用: {args.knowledge_base}")

    count = import_questions(args.module)
    print(f"已导入题目元数据: {count} 条")


if __name__ == "__main__":
    # 直接运行脚本时进入 main；被测试 import 时不会自动执行。
    main()
