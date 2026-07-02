#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""项目统一入口。

这个文件相当于 Java 项目里更清晰的 main 方法：
- 把常见启动动作统一到一个入口。
- 新手不需要记住多个 scripts/*.py 文件名。
- 旧脚本仍然保留，main.py 只是负责命令分发。

推荐用法：
    python main.py                 # 默认启动 Web API + Web UI
    python main.py serve           # 显式启动 Web 服务
    python main.py cli             # 启动命令行面试
    python main.py init-db         # 初始化数据库
    python main.py import-questions --knowledge-base java_interview
    python main.py bootstrap       # 初始化数据库并导入题库
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import sys
from pathlib import Path
from typing import Optional


ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    # 直接运行 main.py 时，显式把项目根目录放进 sys.path，保证和
    # scripts/*.py 一样都能稳定 import 到 agents/scripts 包。
    sys.path.insert(0, str(ROOT_DIR))

def _load_script_module(module_name: str):
    """按需导入 scripts 下的模块，避免顶层导入带来的副作用。

    例如 cli_interview.py 在 Windows 下会重包 sys.stdout；如果在 main.py
    顶层 import，它会影响 pytest 的输出捕获。懒加载能把副作用限制在真正
    需要这个命令的执行路径里。
    """
    return importlib.import_module(f"scripts.{module_name}")


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="AI 面试陪练系统统一入口",
    )
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser(
        "serve",
        help="启动 FastAPI 服务和 Web UI",
    )
    serve_parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    serve_parser.add_argument("--port", type=int, default=8000, help="监听端口")
    serve_parser.add_argument(
        "--reload",
        action="store_true",
        help="启用 uvicorn 自动重载，适合本地开发",
    )

    subparsers.add_parser("cli", help="启动命令行面试")
    subparsers.add_parser("init-db", help="初始化 SQLite 数据库")

    import_parser = subparsers.add_parser(
        "import-questions",
        help="导入题库元数据到数据库",
    )
    import_parser.add_argument(
        "--knowledge-base",
        default=None,
        help="knowledge_bases.yaml 中的知识库键名，例如 java_interview",
    )
    import_parser.add_argument(
        "--module",
        default=None,
        help="只导入指定模块；不传则导入全部模块",
    )

    bootstrap_parser = subparsers.add_parser(
        "bootstrap",
        help="初始化数据库并导入题库，适合首次运行",
    )
    bootstrap_parser.add_argument(
        "--knowledge-base",
        default="java_interview",
        help="首次导入使用的知识库键名，默认 java_interview",
    )
    bootstrap_parser.add_argument(
        "--module",
        default=None,
        help="只导入指定模块；不传则导入全部模块",
    )

    return parser


def run_serve(host: str, port: int, reload_enabled: bool) -> None:
    """启动 Web 服务。

    这里等价于直接执行 scripts/harness_server.py，只是把启动参数集中到
    统一入口里，减少“到底该跑哪个脚本”的困惑。
    """
    import uvicorn

    uvicorn.run(
        "scripts.harness_server:app",
        host=host,
        port=port,
        reload=reload_enabled,
    )


def run_cli() -> None:
    """启动命令行面试。"""
    cli_interview = _load_script_module("cli_interview")
    asyncio.run(cli_interview.main())


def run_import_questions(
    knowledge_base: Optional[str],
    module: Optional[str],
) -> int:
    """导入题库元数据并返回新增数量。"""
    import_questions = _load_script_module("import_questions")
    if knowledge_base:
        switched = import_questions.question_tools.set_knowledge_base(knowledge_base)
        if not switched:
            raise SystemExit(f"知识库不存在或路径不可用: {knowledge_base}")

    count = import_questions.import_questions(module)
    print(f"已导入题目元数据: {count} 条")
    return count


def run_bootstrap(
    knowledge_base: Optional[str],
    module: Optional[str],
) -> None:
    """首次启动辅助命令：初始化数据库并导入题库。"""
    init_database = _load_script_module("init_database")
    print("开始初始化数据库...")
    init_database.init_database()
    print()
    print("开始导入题库元数据...")
    run_import_questions(knowledge_base=knowledge_base, module=module)
    print()
    print("初始化完成。现在可以执行 `python main.py` 打开 Web 服务。")


def dispatch(args: argparse.Namespace) -> None:
    """按子命令分发执行。

    这里单独拆函数，方便测试命令路由；类似 Java 里把 main() 里的 if/else
    提取成一个 ApplicationService。
    """
    command = args.command or "serve"

    if command == "serve":
        run_serve(
            host=getattr(args, "host", "127.0.0.1"),
            port=int(getattr(args, "port", 8000)),
            reload_enabled=bool(getattr(args, "reload", False)),
        )
        return

    if command == "cli":
        run_cli()
        return

    if command == "init-db":
        init_database = _load_script_module("init_database")
        init_database.init_database()
        return

    if command == "import-questions":
        run_import_questions(
            knowledge_base=getattr(args, "knowledge_base", None),
            module=getattr(args, "module", None),
        )
        return

    if command == "bootstrap":
        run_bootstrap(
            knowledge_base=getattr(args, "knowledge_base", "java_interview"),
            module=getattr(args, "module", None),
        )
        return

    raise SystemExit(f"不支持的命令: {command}")


def main(argv: Optional[list[str]] = None) -> None:
    """程序入口。"""
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch(args)


if __name__ == "__main__":
    main()
