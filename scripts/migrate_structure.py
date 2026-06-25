#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目录结构迁移脚本
将旧的结构迁移到通用的知识库架构
"""

import os
import shutil
import sys
from pathlib import Path

# Windows 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent

def migrate_structure():
    """迁移目录结构"""

    print("=" * 60)
    print("🔄 目录结构迁移")
    print("=" * 60)

    # 1. 创建新目录结构
    print("\n📁 步骤 1: 创建新目录结构...")

    knowledge_base_root = ROOT_DIR / "知识库"
    knowledge_base_root.mkdir(exist_ok=True)

    java_interview = knowledge_base_root / "Java面试"
    java_interview.mkdir(exist_ok=True)

    learning_records_root = ROOT_DIR / "学习记录"
    learning_records_root.mkdir(exist_ok=True)

    java_learning = learning_records_root / "Java面试"
    java_learning.mkdir(exist_ok=True)

    # 创建子目录
    for subdir in ["每日对话", "周报", "错题本", "知识图谱"]:
        (java_learning / subdir).mkdir(exist_ok=True)

    print("✅ 新目录结构创建完成")

    # 2. 迁移 Java八股文
    old_java_path = ROOT_DIR / "Java八股文"

    if old_java_path.exists():
        print(f"\n📦 步骤 2: 迁移题库...")
        print(f"   从: {old_java_path}")
        print(f"   到: {java_interview}")

        # 检查目标目录是否为空
        if list(java_interview.iterdir()):
            print("⚠️  目标目录非空，跳过迁移（避免覆盖）")
        else:
            # 移动所有内容
            for item in old_java_path.iterdir():
                if item.name not in ['.git', '__pycache__']:
                    shutil.move(str(item), str(java_interview / item.name))

            print("✅ 题库迁移完成")

            # 删除旧目录
            try:
                old_java_path.rmdir()
                print("✅ 旧目录已删除")
            except:
                print("⚠️  旧目录未删除（可能非空），请手动检查")
    else:
        print("\n⚠️  未找到 'Java八股文' 目录，跳过迁移")

    # 3. 迁移学习记录（如果有）
    old_records = ROOT_DIR / "学习记录"
    if old_records.exists() and old_records != learning_records_root:
        print(f"\n📝 步骤 3: 迁移学习记录...")

        for item in old_records.iterdir():
            if item.name != "Java面试":
                dest = java_learning / item.name
                if not dest.exists():
                    shutil.move(str(item), str(dest))

        print("✅ 学习记录迁移完成")

    # 4. 显示新结构
    print("\n" + "=" * 60)
    print("✅ 迁移完成！新的目录结构：")
    print("=" * 60)
    print("""
AI-Knowledge/
├── 知识库/
│   └── Java面试/                    # 1346 道题
│       ├── Java基础/
│       ├── JVM/
│       └── ...（54个模块）
│
├── 学习记录/
│   └── Java面试/
│       ├── 每日对话/
│       ├── 周报/
│       ├── 错题本/
│       └── 知识图谱/
│
└── .harness/
    └── config/
        └── knowledge_bases.yaml    # 知识库配置
    """)

    print("=" * 60)
    print("\n💡 后续步骤：")
    print("   1. 检查迁移结果")
    print("   2. 更新数据库（如果已导入题库）")
    print("   3. 根据需要添加其他知识库（Python、前端、算法等）")
    print("=" * 60)

if __name__ == '__main__':
    try:
        migrate_structure()
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
