# 🎓 Obsidian Interview Harness

> **基于 Obsidian 知识库 + Agent Harness 架构的智能面试陪练系统**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Agent Harness](https://img.shields.io/badge/Agent-Harness-orange.svg)](AGENTS.md)
[![MySQL](https://img.shields.io/badge/Database-MySQL%208.0-blue.svg)](MYSQL_SETUP.md)
[![Obsidian](https://img.shields.io/badge/Obsidian-Compatible-purple.svg)](https://obsidian.md/)

[English](#english) | [中文](#中文)

---

## 🌟 项目亮点

- ✨ **Obsidian 原生集成**：基于 Obsidian Markdown 知识库，支持双链、标签、图谱
- 🤖 **6 Agent 协作系统**：面试官、复习调度器、知识关联器、错题分析师、监督助手、陪练伙伴
- 🧠 **三层记忆架构**：短期（会话）+ 中期（学习记录）+ 长期（用户画像）
- 📈 **智能复习调度**：基于 SM-2 算法的遗忘曲线管理
- 🔗 **知识图谱关联**：自动发现题目之间的深层联系
- 📊 **数据驱动分析**：精准识别薄弱环节，生成学习报告
- 🎯 **多知识库支持**：Java、Python、前端、算法等（可扩展）

---

## 💡 为什么选择 Obsidian + Harness？

### Obsidian：知识管理的最佳选择

- ✅ **纯 Markdown**：Git 友好，版本控制，团队协作
- ✅ **双向链接**：`[[Java并发]]` 自动建立知识关联
- ✅ **图谱可视化**：一键查看题目关系网络
- ✅ **标签系统**：`#高频` `#字节跳动` `#2024秋招` 灵活分类
- ✅ **离线优先**：数据完全掌控，隐私安全

### Agent Harness：生产级 Agent 架构

- ✅ **TAOR 循环**：Think → Act → Observe → Reflect
- ✅ **工具注册系统**：Python 函数 → LLM 可调用工具
- ✅ **上下文管理**：Token 统计、消息压缩、长期记忆
- ✅ **多 Agent 协作**：监督、调度、分析、关联独立运行

---

## 🎬 快速开始

### 前置要求

- Python 3.9+
- MySQL 8.0+（或使用 SQLite）
- OpenAI 兼容 API（推荐 DeepSeek）
- Obsidian（可选，用于编辑知识库）

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/obsidian-interview-harness.git
cd obsidian-interview-harness

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key
cp .harness/config/harness.yaml.example .harness/config/harness.yaml
# 编辑 harness.yaml，填入你的 DeepSeek API Key

# 4. 初始化数据库（MySQL）
mysql -u root -p < .harness/db/schema_mysql.sql
# 或使用 SQLite（零配置）
python scripts/init_database.py

# 5. 导入题库（1346 道 Java 面试题）
python scripts/import_questions.py --knowledge-base java_interview

# 6. 启动命令行界面
python scripts/cli_interview.py
```

### 效果预览

```
🎯 AI 面试陪练系统 v1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 当前知识库: Java 面试
📊 已掌握: 120 题 | 📝 复习中: 45 题 | 🔴 薄弱: 12 题

请选择模式：
1. 随机练习
2. 智能复习（推荐）
3. 错题重做
4. 知识图谱探索

> 2

🤖 面试官：请说说 Java 中 synchronized 的实现原理？

👤 你的回答：[开始输入...]
```

---

## 📁 项目结构

```
obsidian-interview-harness/
├── 知识库/                          # Obsidian 知识库（多领域）
│   ├── Java面试/                    # ✅ 已有 1346 题，54 模块
│   │   ├── Java基础/
│   │   ├── JVM/
│   │   ├── Java并发/
│   │   └── ...
│   │
│   ├── Python面试/                  # 待扩展
│   ├── 前端面试/                    # 待扩展
│   └── 算法面试/                    # 待扩展
│
├── 学习记录/                        # 按知识库分类
│   ├── Java面试/
│   │   ├── 每日对话/                # Obsidian 笔记格式
│   │   ├── 周报/
│   │   ├── 错题本/
│   │   └── 知识图谱/
│   │
│   └── ...
│
├── agents/                          # Agent 核心实现
│   ├── core/                        # 通用执行引擎
│   │   ├── agent_loop.py            # TAOR 循环
│   │   ├── base_agent.py            # Agent 基类
│   │   ├── tool_registry.py         # 工具注册
│   │   └── context_manager.py       # 上下文管理
│   │
│   ├── roles/                       # 6 个 Agent 角色
│   │   ├── interviewer_agent.py     # ✅ 面试官（已实现）
│   │   ├── scheduler_agent.py       # 📅 复习调度器（规划中）
│   │   ├── linker_agent.py          # 🔗 知识关联器（规划中）
│   │   ├── analyzer_agent.py        # 📊 错题分析师（规划中）
│   │   ├── supervisor_agent.py      # 👀 监督助手（规划中）
│   │   └── buddy_agent.py           # 👥 陪练伙伴（规划中）
│   │
│   ├── tools/                       # Agent 工具
│   │   ├── question_tools.py        # 题库操作
│   │   └── memory_tools.py          # 记忆管理
│   │
│   └── definitions/                 # Agent 角色定义
│
├── .harness/                        # 配置与数据
│   ├── config/
│   │   ├── harness.yaml             # 主配置
│   │   ├── harness.yaml.example     # 配置模板
│   │   ├── agents_config.yaml       # Agent 配置
│   │   └── knowledge_bases.yaml     # 知识库配置
│   │
│   ├── memory/                      # 长期记忆
│   │   ├── USER.md                  # 用户画像
│   │   └── MEMORY.md                # 记忆索引
│   │
│   └── db/                          # 数据库 Schema
│
├── scripts/                         # 工具脚本
│   ├── cli_interview.py             # 命令行界面
│   ├── import_questions.py          # 题库导入
│   └── demo_full_flow.py            # 完整流程演示
│
└── docs/                            # 完整文档
    ├── CLAUDE.md                    # 项目完整上下文
    ├── AGENTS.md                    # Agent 架构设计
    ├── PLAN.md                      # 实施计划
    └── MYSQL_SETUP.md               # 数据库配置
```

---

## 🚀 核心特性

### 1️⃣ Obsidian 原生集成

**示例题目**（`知识库/Java面试/JVM/垃圾回收.md`）：

```markdown
---
tags: [高频, JVM, 垃圾回收]
difficulty: ⭐⭐⭐
companies: [字节跳动, 阿里巴巴]
---

# 请说说 CMS 和 G1 垃圾收集器的区别？

## 参考答案
CMS（Concurrent Mark Sweep）是一款以获取最短回收停顿时间为目标的收集器...

[[新生代GC]] | [[老年代GC]] | [[STW问题]]

## 追问方向
1. CMS 有哪些缺点？
2. G1 的 Region 设计有什么好处？
3. 什么场景下会选择 ZGC？
```

**在 Obsidian 中打开知识库**：

```bash
# 1. 打开 Obsidian
# 2. 打开文件夹 -> 选择 "知识库/Java面试"
# 3. 享受双链、图谱、标签的强大功能！
```

### 2️⃣ Agent Harness 架构

**6 个专业 Agent 协作**：

| Agent | 职责 | 状态 | 核心能力 |
|-------|------|------|---------|
| 🎤 **面试官** | 提问、追问、评分 | ✅ 已实现 | 四维度评分（准确性、完整性、深度、场景化） |
| 📅 **复习调度器** | 智能推荐复习 | 📋 规划中 | SM-2 算法 + 遗忘曲线 |
| 🔗 **知识关联器** | 发现题目关联 | 📋 规划中 | TF-IDF + 向量检索 |
| 📊 **错题分析师** | 深度错题分析 | 📋 规划中 | 识别薄弱点、生成报告 |
| 👀 **监督助手** | 防止作弊、纠偏 | 📋 规划中 | 检测复制粘贴、提示偏离 |
| 👥 **陪练伙伴** | 鼓励、建议、陪伴 | 📋 规划中 | 情感支持、学习建议 |

**TAOR 循环示意**：

```python
# Agent Loop 核心实现
while not should_exit():
    # 1. Think: 调用 LLM
    response = await llm.create(messages, tools)
    
    # 2. Act: 执行工具调用
    if response.tool_calls:
        results = await execute_tools(response.tool_calls)
        
        # 3. Observe: 收集结果
        add_tool_results(results)
    else:
        # 4. Reflect: 返回最终答案
        return response.content
```

### 3️⃣ 三层记忆系统

```
┌─────────────────────────────────────┐
│  短期记忆（会话级）                    │
│  - 当前对话上下文                     │
│  - 最近 20 轮对话                     │
└─────────────────────────────────────┘
            ↓ 会话结束归档
┌─────────────────────────────────────┐
│  中期记忆（学习记录）                  │
│  - learning_records: 答题记录         │
│  - question_metadata: 题目元数据      │
│  - error_analysis: 错题分析           │
└─────────────────────────────────────┘
            ↓ 定期提取模式
┌─────────────────────────────────────┐
│  长期记忆（用户画像）                  │
│  - USER.md: 用户偏好                  │
│  - LEARNING_PATTERN.md: 学习模式      │
└─────────────────────────────────────┘
```

### 4️⃣ 智能复习调度（SM-2 算法）

基于艾宾浩斯遗忘曲线：

```python
# 答对 → 间隔延长
第一次: 1 天后
第二次: 6 天后
第三次: 15 天后 (6 × 2.5)
第四次: 37 天后 (15 × 2.5)

# 答错 → 重置为 1 天
```

---

## 🗄️ 数据库设计

**8 张核心表**：

```sql
-- 1. 学习记录表（每次答题的详细记录）
learning_records: 
  - 四维度评分（准确性、完整性、深度、场景化）
  - 追问记录
  - 薄弱点分析

-- 2. 题目元数据表（掌握情况）
question_metadata:
  - mastery_level: 🟢🟡🔴⚪
  - SM-2 调度参数（next_review, easiness_factor）
  - 知识关联

-- 3. 知识关联表（题目关系）
knowledge_relations:
  - 对比关系（CMS vs G1）
  - 递进关系（基础 → 进阶）
  - 场景关系（电商场景、金融场景）

-- 4-8. error_analysis / sessions / user_profile / review_queue / agent_interactions
```

详细 Schema：[.harness/db/schema_mysql.sql](.harness/db/schema_mysql.sql)

---

## 🛠️ 技术栈

| 类别 | 技术选型 | 说明 |
|------|---------|------|
| **后端** | Python 3.9+ | 主语言 |
| **Web 框架** | FastAPI | REST API + WebSocket |
| **数据库** | MySQL 8.0 / SQLite | 结构化数据存储 |
| **LLM** | DeepSeek / OpenAI | 兼容 OpenAI SDK |
| **Agent 框架** | 原生实现 | TAOR 循环、工具注册 |
| **向量检索** | Chroma | 知识关联 |
| **知识管理** | Obsidian | Markdown 编辑器 |
| **前端（计划）** | React + TypeScript | Web UI |

---

## 📖 使用指南

### 添加新知识库

```bash
# 1. 在 Obsidian 或任何编辑器中创建新文件夹
mkdir -p "知识库/Python面试/基础语法"

# 2. 添加题目（Markdown 格式）
# 格式与 Java 面试题相同，参考：
# 知识库/Java面试/Java基础/基础语法.md

# 3. 编辑配置文件
vim .harness/config/knowledge_bases.yaml

# 4. 导入题库
python scripts/import_questions.py --knowledge-base python_interview
```

### 自定义 Agent 行为

编辑 Agent 定义文件：

```bash
vim agents/definitions/interviewer.md
```

示例修改：

```markdown
# 面试官 Agent

## 核心职责
- 提问：从题库随机选题
- 追问：根据回答质量追问 2-3 轮（← 修改这里）
- 评分：四维度打分
```

### 在 Obsidian 中使用

1. **打开知识库**：Obsidian → 打开文件夹 → 选择 `知识库/Java面试`
2. **编辑题目**：支持双链、标签、图谱
3. **查看关联**：点击 `[[Java并发]]` 跳转到相关题目
4. **图谱可视化**：`Ctrl+G` 查看知识图谱

---

## 🎯 路线图

- [x] **Phase 0**: 基础设施（已完成）
- [x] **Phase 0.5**: Agent Loop 核心（已完成）
- [x] **Phase 1**: 面试官 Agent（已完成）
- [ ] **Phase 2**: 复习调度器 + 知识关联器
- [ ] **Phase 3**: 错题分析师 + 监督助手
- [ ] **Phase 4**: 陪练伙伴 + Web UI
- [ ] **Phase 5**: 多用户支持 + 团队协作
- [ ] **Phase 6**: 移动端 App
- [ ] **Phase 7**: 语音面试模式

详细计划：[PLAN.md](PLAN.md)

---

## 📚 文档

- [🏗️ 项目上下文](CLAUDE.md) - 开发必读，完整项目信息
- [🤖 Agent 架构](AGENTS.md) - 6 个 Agent 的详细设计
- [📋 实施计划](PLAN.md) - 完整的开发路线图
- [🗄️ MySQL 配置](MYSQL_SETUP.md) - 数据库配置指南
- [📊 对比分析](COMPARISON_REPORT_V2.md) - 与生产级 Agent Harness 的对比
- [🚀 快速入门](QUICKSTART_FOR_BEGINNERS.md) - 新手入门指南

---

## 🤝 贡献指南

欢迎贡献！请遵循以下规范：

1. **Fork 项目** → **创建分支** → **提交 PR**
2. **代码风格**: PEP 8 规范
3. **提交规范**: 使用约定式提交（Conventional Commits）
   ```bash
   feat: 添加 XXX 功能
   fix: 修复 XXX 问题
   docs: 更新文档
   refactor: 重构 XXX 模块
   ```
4. **测试**: 新功能必须包含单元测试

详细指南：[CONTRIBUTING.md](CONTRIBUTING.md)（待创建）

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE)。

你可以自由地：
- ✅ 使用、复制、修改、合并、出版发行
- ✅ 用于商业用途
- ⚠️ 但需保留原作者版权声明

---

## 🙏 致谢

本项目灵感来源于：

- **Agent Harness 理论**: [Agent-Harness-Develop-Book](Agent-Harness-Develop-Book/)
- **Obsidian**: [强大的知识管理工具](https://obsidian.md/)
- **SuperMemo SM-2**: 间隔重复算法
- **OpenAI Function Calling**: 工具调用标准

---

## 📞 联系方式

- **GitHub Issues**: [提交问题](https://github.com/yourusername/obsidian-interview-harness/issues)
- **讨论区**: [GitHub Discussions](https://github.com/yourusername/obsidian-interview-harness/discussions)

---

## ⭐ Star History

如果这个项目对你有帮助，欢迎 Star ⭐ 支持！

---

<div align="center">

**祝你面试顺利！💪**

Made with ❤️ by AI Interview Coach Team

</div>
