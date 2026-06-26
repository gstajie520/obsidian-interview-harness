#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库初始化脚本：创建 SQLite 数据库和表结构。

这个脚本适合初次运行项目时执行一次。SQLite 是单文件数据库，
`learning.db` 不存在时会自动创建，比较适合本地学习项目。
"""

import sqlite3
import sys
from pathlib import Path

# Windows 编码设置，避免中文输出在部分控制台里乱码。
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / ".harness" / "db" / "learning.db"
SCHEMA_PATH = ROOT_DIR / ".harness" / "db" / "schema.sql"

def init_database() -> None:
    """初始化数据库。"""

    # 确保目录存在
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 连接数据库（如果不存在会自动创建）
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 读取并执行 schema
    print(f"📖 读取 schema: {SCHEMA_PATH}")
    # 使用 with 打开文件，执行完会自动关闭文件句柄。
    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
        schema_sql = file.read()

    print("🏗️  创建数据库表...")
    cursor.executescript(schema_sql)

    # 插入初始用户画像数据
    print("👤 初始化用户画像...")
    initial_profile = [
        ("total_study_days", "0", "pattern"),
        ("avg_daily_questions", "0", "pattern"),
        ("best_study_time", "unknown", "pattern"),
        ("learning_style", "unknown", "preference"),
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO user_profile "
        "(key, value, category) VALUES (?, ?, ?)",
        initial_profile,
    )

    conn.commit()
    print("✅ 数据库初始化完成！")
    print(f"📍 数据库位置: {DB_PATH}")

    # 显示表信息
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\n📊 已创建 {len(tables)} 张表:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"   - {table[0]}: {count} 条记录")

    conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Agent Harness - 数据库初始化")
    print("=" * 60)
    init_database()
    print("\n" + "=" * 60)
