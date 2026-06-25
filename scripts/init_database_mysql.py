#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本 - 支持 MySQL
创建数据库和表结构
"""

import sys
import yaml
from pathlib import Path

# Windows 编码设置
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
CONFIG_PATH = ROOT_DIR / ".harness" / "config" / "harness.yaml"
SCHEMA_PATH = ROOT_DIR / ".harness" / "db" / "schema_mysql.sql"

def load_config():
    """加载配置文件"""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def init_mysql_database():
    """初始化 MySQL 数据库"""

    try:
        import pymysql
    except ImportError:
        print("❌ 缺少依赖: pymysql")
        print("请运行: pip install pymysql")
        return False

    config = load_config()
    db_config = config['database']

    print(f"📡 连接 MySQL: {db_config['host']}:{db_config['port']}")

    # 先连接到 MySQL（不指定数据库）
    try:
        conn = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            charset=db_config.get('charset', 'utf8mb4')
        )
        cursor = conn.cursor()

        # 读取并执行 schema
        print(f"📖 读取 schema: {SCHEMA_PATH}")
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        print("🏗️  创建数据库和表...")

        # 分割 SQL 语句并逐个执行
        statements = [s.strip() for s in schema_sql.split(';') if s.strip()]

        for statement in statements:
            if statement:
                try:
                    cursor.execute(statement)
                except pymysql.Error as e:
                    # 忽略已存在的错误
                    if 'already exists' not in str(e).lower():
                        print(f"⚠️  警告: {e}")

        conn.commit()
        print("✅ 数据库初始化完成！")

        # 切换到目标数据库
        cursor.execute(f"USE {db_config['database']}")

        # 显示表信息
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"\n📊 已创建 {len(tables)} 张表:")

        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   - {table_name}: {count} 条记录")

        cursor.close()
        conn.close()

        print(f"\n📍 数据库: {db_config['database']} @ {db_config['host']}")
        return True

    except pymysql.Error as e:
        print(f"❌ 数据库错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Agent Harness - 数据库初始化 (MySQL)")
    print("=" * 60)

    success = init_mysql_database()

    if success:
        print("\n" + "=" * 60)
        print("✅ 初始化成功！")
        print("\n下一步:")
        print("  1. 运行 python scripts/import_questions.py 导入题库")
        print("  2. 运行 python scripts/cli_interface.py 开始使用")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 初始化失败，请检查:")
        print("  1. MySQL 是否已安装并启动")
        print("  2. 配置文件中的用户名和密码是否正确")
        print("  3. 是否已安装 pymysql: pip install pymysql")
        print("=" * 60)
