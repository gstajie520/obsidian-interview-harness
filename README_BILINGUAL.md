# 🎓 Obsidian Interview Harness

> **AI Interview Coach powered by Obsidian + Agent Harness**

[中文](#中文) | [English](#english)

---

# 中文

## 🌟 项目简介

**Obsidian Interview Harness** 是一个基于 **Obsidian 知识库** + **Agent Harness 架构**的智能面试陪练系统。

### 核心特性

- ✨ **Obsidian 原生集成**：Markdown、双链、标签、知识图谱
- 🤖 **6 Agent 协作系统**：面试官、调度器、关联器、分析师、监督助手、陪练伙伴
- 🧠 **三层记忆架构**：短期（会话）+ 中期（学习记录）+ 长期（用户画像）
- 📈 **智能复习调度**：基于 SM-2 算法的遗忘曲线管理
- 🔗 **知识图谱关联**：自动发现题目之间的深层联系
- 📊 **数据驱动分析**：精准识别薄弱环节，生成学习报告
- 🎯 **多知识库支持**：Java、Python、前端、算法等（可扩展）

### 技术栈

- **后端**: Python 3.9+ / FastAPI
- **数据库**: MySQL 8.0 / SQLite
- **LLM**: DeepSeek / OpenAI Compatible API
- **Agent 框架**: 原生实现（TAOR 循环）
- **知识管理**: Obsidian
- **向量检索**: Chroma

---

## 🚀 快速开始

### 前置要求

- Python 3.9+
- MySQL 8.0+（或使用 SQLite）
- OpenAI 兼容 API（推荐 DeepSeek）
- Obsidian（可选，用于编辑知识库）

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/gstajie520/obsidian-interview-harness.git
cd obsidian-interview-harness

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key
cp .harness/config/harness.yaml.example .harness/config/harness.yaml
# 编辑 harness.yaml，填入你的 API Key

# 4. 初始化数据库（可选，使用 MySQL）
mysql -u root -p < .harness/db/schema_mysql.sql
# 或使用 SQLite（零配置）
python scripts/init_database.py

# 5. 启动面试
python scripts/cli_interview.py
```

---

## 📖 文档

- [📋 项目完整上下文](CLAUDE.md)
- [🤖 Agent 架构设计](AGENTS.md)
- [📅 实施计划](PLAN.md)
- [🗄️ MySQL 配置指南](MYSQL_SETUP.md)
- [🚀 新手快速入门](QUICKSTART_FOR_BEGINNERS.md)
- [🤝 贡献指南](CONTRIBUTING.md)

---

## 🤝 贡献

欢迎贡献！请阅读 [贡献指南](CONTRIBUTING.md)。

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE)。

---

## 📞 联系方式

- **GitHub Issues**: [提交问题](https://github.com/gstajie520/obsidian-interview-harness/issues)
- **Discussions**: [参与讨论](https://github.com/gstajie520/obsidian-interview-harness/discussions)

---

**祝你面试顺利！💪**

---

# English

## 🌟 Project Introduction

**Obsidian Interview Harness** is an AI interview coach system powered by **Obsidian Knowledge Base** + **Agent Harness Architecture**.

### Key Features

- ✨ **Obsidian Native Integration**: Markdown, backlinks, tags, knowledge graph
- 🤖 **6-Agent Collaboration System**: Interviewer, scheduler, linker, analyzer, supervisor, buddy
- 🧠 **Three-Layer Memory Architecture**: Short-term (session) + Medium-term (learning records) + Long-term (user profile)
- 📈 **Smart Review Scheduling**: Forgetting curve management based on SM-2 algorithm
- 🔗 **Knowledge Graph Association**: Automatically discover deep connections between questions
- 📊 **Data-Driven Analysis**: Precisely identify weak points and generate learning reports
- 🎯 **Multi-Knowledge-Base Support**: Java, Python, frontend, algorithms, etc. (extensible)

### Tech Stack

- **Backend**: Python 3.9+ / FastAPI
- **Database**: MySQL 8.0 / SQLite
- **LLM**: DeepSeek / OpenAI Compatible API
- **Agent Framework**: Native implementation (TAOR loop)
- **Knowledge Management**: Obsidian
- **Vector Search**: Chroma

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- MySQL 8.0+ (or use SQLite)
- OpenAI-compatible API (DeepSeek recommended)
- Obsidian (optional, for editing knowledge base)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/gstajie520/obsidian-interview-harness.git
cd obsidian-interview-harness

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API Key
cp .harness/config/harness.yaml.example .harness/config/harness.yaml
# Edit harness.yaml and add your API Key

# 4. Initialize database (optional, for MySQL)
mysql -u root -p < .harness/db/schema_mysql.sql
# Or use SQLite (zero configuration)
python scripts/init_database.py

# 5. Start the interview
python scripts/cli_interview.py
```

---

## 📖 Documentation

- [📋 Complete Project Context](CLAUDE.md)
- [🤖 Agent Architecture Design](AGENTS.md)
- [📅 Implementation Plan](PLAN.md)
- [🗄️ MySQL Configuration Guide](MYSQL_SETUP.md)
- [🚀 Beginner's Quick Start](QUICKSTART_FOR_BEGINNERS.md)
- [🤝 Contributing Guide](CONTRIBUTING.md)

---

## 🤝 Contributing

Contributions are welcome! Please read the [Contributing Guide](CONTRIBUTING.md).

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 📞 Contact

- **GitHub Issues**: [Submit an issue](https://github.com/gstajie520/obsidian-interview-harness/issues)
- **Discussions**: [Join the discussion](https://github.com/gstajie520/obsidian-interview-harness/discussions)

---

**Good luck with your interviews! 💪**
