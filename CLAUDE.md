# AI 面试陪练系统 - 项目上下文

> **项目**: AI Interview Coach powered by Agent Harness  
> **版本**: 1.0.0  
> **更新**: 2026-06-24

---

## AI 协作执行规则

本节是给 AI 编码助手看的硬性执行规则。执行代码修改、文档修改或 Git 提交时，必须优先遵守本节。

### Git 提交硬性规则

- 提交前必须读取 `GIT_RULES.md`，并检查 `git status --short`。
- 提交信息必须使用中文描述，禁止纯英文 subject。
- 提交信息必须使用格式：`<type>(<scope>): <中文描述>`。
- `scope` 必须填写，使用小写英文、数字、短横线或下划线，例如 `agents`、`python-comments`、`git-rules`。
- 允许的 `type`：`feat`、`fix`、`docs`、`style`、`refactor`、`test`、`chore`、`perf`。
- 正确示例：`docs(python-comments): 补充初学者代码注释`。
- 错误示例：`refactor: standardize agents project structure`，原因是缺少 scope 且 subject 为英文。
- 每次完成文件修改并验证后必须提交；同一任务内相关文件可以合并为一个提交。
- 除非用户明确说“不要提交”或“先别提交”，否则最终回复前不能留下未提交修改。
- `git add`、`git commit`、`git reset`、`git config` 等会写入 `.git` 的命令禁止并行执行。
- 提交后必须执行 `git status --short` 和 `git log -1 --oneline` 验证结果。

本仓库使用 `.githooks/commit-msg` 校验提交信息。若 hook 未启用，执行：

```bash
git config core.hooksPath .githooks
```

---

## 📌 项目概述

这是一个基于 **Agent Harness 架构**的**通用智能面试助手系统**，支持多个面试领域（Java、Python、前端、算法等）。系统包含 6 个协作 Agent，具备持久记忆、智能调度、自动进化等能力。

### 通用性设计

- ✅ **多知识库支持**：可扩展到任何面试领域
- ✅ **统一的 Agent 架构**：所有知识库共享相同的 Agent
- ✅ **灵活配置**：通过配置文件添加新知识库
- ✅ **独立的学习记录**：每个知识库独立追踪学习进度

### 核心特性

- ✅ **多知识库支持**：Java、Python、前端、算法等（可扩展）
- ✅ **6 个专业 Agent**：面试官、复习调度器、知识关联器、错题分析师、监督助手、陪练伙伴
- ✅ **三层记忆系统**：短期（会话）、中期（学习记录）、长期（用户画像）
- ✅ **智能复习调度**：基于 SM-2 算法的遗忘曲线管理
- ✅ **知识图谱关联**：自动发现题目之间的关联
- ✅ **数据驱动分析**：精准识别薄弱环节，生成学习报告

---

## 🎓 学习模式

本项目采用**双轨实现**，既能深入理解原理，又能学习主流框架：

### 实现方案对比

| 方案 | 优势 | 适用场景 |
|------|------|---------|
| **原生实现** | 完全掌控、深入理解 Agent Loop 原理 | 学习、定制化需求 |
| **LangChain** | 快速开发、丰富的工具生态 | 快速原型、标准化场景 |
| **LangGraph** | 可视化流程、灵活编排 | 复杂多步骤任务 |

### 学习路径

```
第一周（Phase 0.5）: 原生实现 Agent Loop
  ↓ 理解 TAOR 循环原理
第二周（Phase 1）: 引入 LangChain 工具系统
  ↓ 学习工具封装最佳实践
第三周（Phase 2）: 尝试 LangGraph 状态图
  ↓ 学习复杂 Agent 编排
对比分析: 选择最适合的方案
```

详细说明见 `LANGCHAIN_INTEGRATION.md`

---

## 🌟 通用性设计

### 知识库架构

系统采用**知识库抽象层**，支持多个面试领域：

```yaml
知识库配置（knowledge_bases.yaml）:
  java_interview:      # Java 面试（已有 1346 题）
    path: "知识库/Java面试"
    enabled: true
  
  python_interview:    # Python 面试（待扩展）
    path: "知识库/Python面试"
    enabled: false
  
  frontend_interview:  # 前端面试（待扩展）
    path: "知识库/前端面试"
    enabled: false
```

### Agent 通用性

所有 Agent 都是**知识库无关**的：
- ✅ 面试官 Agent：可以面试任何领域
- ✅ 复习调度器：SM-2 算法适用于所有知识
- ✅ 知识关联器：基于 TF-IDF，适用于任何文本
- ✅ 错题分析师：分析逻辑通用

### 扩展新知识库

添加新知识库只需 3 步：

```bash
# 1. 创建目录
mkdir -p "知识库/Python面试"

# 2. 添加题目（Markdown 格式）
# 3. 更新配置文件 knowledge_bases.yaml
```

---

## 🏗️ 技术栈

### 后端
- **语言**: Python 3.9+
- **框架**: FastAPI（REST API + WebSocket）
- **数据库**: MySQL 8.0+
- **LLM**: OpenAI SDK（兼容 DeepSeek API，默认模型：deepseek-chat，可配置）
- **Agent 框架**: 
  - 原生实现（深入理解原理）
  - LangChain（工具系统）
  - LangGraph（状态图编排）
- **向量检索**: Chroma（知识关联）
- **Token 管理**: tiktoken

### 前端（计划）
- **框架**: React 18 + TypeScript
- **UI 库**: Ant Design
- **状态管理**: Zustand
- **图表**: ECharts

### 数据存储
- **结构化数据**: MySQL（学习记录、用户画像、复习队列）
- **文件存储**: Markdown（Obsidian 笔记、会话归档）

---

## 📂 项目结构

```
AI-Knowledge/
├── 知识库/                          # 通用知识库（可扩展）
│   ├── Java面试/                    # Java 技术面试（1346题）
│   │   ├── Java基础/
│   │   ├── JVM/
│   │   ├── Java并发/
│   │   └── ...（54个模块）
│   │
│   ├── Python面试/                  # 待扩展
│   ├── 前端面试/                    # 待扩展
│   └── 算法面试/                    # 待扩展
│
├── 学习记录/                        # 按知识库分类
│   ├── Java面试/
│   │   ├── 每日对话/
│   │   ├── 周报/
│   │   ├── 错题本/
│   │   └── 知识图谱/
│   │
│   ├── Python面试/
│   └── ...
│
├── agents/                          # 标准 Python Agents 包（正式实现）
│   ├── core/                        # 通用执行引擎
│   │   ├── base_agent.py            # Agent 基类
│   │   ├── agent_loop.py            # TAOR 循环
│   │   ├── tool_registry.py         # 工具注册
│   │   └── context_manager.py       # 上下文管理
│   │
│   ├── roles/                       # 具体 Agent 角色
│   │   ├── interviewer_agent.py     # 面试官（已实现）
│   │   ├── scheduler_agent.py       # 复习调度器（规划）
│   │   ├── linker_agent.py          # 知识关联器（规划）
│   │   ├── analyzer_agent.py        # 错题分析师（规划）
│   │   ├── supervisor_agent.py      # 监督助手（规划）
│   │   └── buddy_agent.py           # 陪练伙伴（规划）
│   │
│   ├── tools/                       # Agent 可调用工具
│   │   ├── question_tools.py        # 题库工具
│   │   └── memory_tools.py          # 记忆工具
│   │
│   └── definitions/                 # Agent 角色定义文档
│       ├── interviewer.md
│       ├── scheduler.md
│       ├── linker.md
│       ├── analyzer.md
│       ├── buddy.md
│       ├── supervisor.md
│       ├── orchestrator.md
│       ├── memory-reviewer.md
│       └── material-curator.md
│
├── .harness/                        # 配置、记忆和数据库
│   ├── config/
│   │   ├── harness.yaml             # 主配置
│   │   ├── agents_config.yaml       # Agent 配置
│   │   └── knowledge_bases.yaml     # 知识库配置
│   │
│   ├── memory/                      # 长期记忆文件
│   │   ├── USER.md                  # 用户画像
│   │   ├── MEMORY.md                # 记忆索引
│   │   └── session-archive/         # 会话归档
│   │
│   ├── db/                          # 数据库 Schema / SQLite 文件
│   │   ├── schema_mysql.sql
│   │   └── schema.sql
│
├── scripts/                         # 工具脚本
│   ├── init_database_mysql.py       # 数据库初始化
│   ├── cli_interview.py             # 命令行界面
│   ├── demo_full_flow.py            # 完整流程演示
│   └── test_agent_loop.py           # 核心引擎测试
│
├── tests/                           # 单元测试
│   └── test_core_engine.py          # 核心引擎测试
│
├── web_ui/                          # Web 前端（计划）
│
├── requirements.txt                 # Python 依赖
├── PLAN.md                          # 实施计划
├── AGENTS.md                        # Agent 架构文档
├── CLAUDE.md                        # 本文档
├── MYSQL_SETUP.md                   # MySQL 配置指南
└── COMPARISON_REPORT_V2.md          # Agent Harness 对比分析
```

---

## 🗄️ 数据库设计

### 核心表结构（8张表）

#### 1. learning_records - 学习记录表
存储每次答题的详细记录，包括四维度评分、追问记录等。

```sql
CREATE TABLE learning_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    question_id VARCHAR(255) NOT NULL,
    module VARCHAR(100) NOT NULL,
    
    -- 四维度评分（面试官 Agent）
    score_accuracy DECIMAL(3,2),      -- 准确性 0-5
    score_completeness DECIMAL(3,2),  -- 完整性 0-5
    score_depth DECIMAL(3,2),         -- 深度 0-5
    score_scenario DECIMAL(3,2),      -- 场景化 0-5
    overall_score DECIMAL(3,2),       -- 综合得分
    
    -- 答题内容
    user_answer TEXT,
    weak_points JSON,                 -- 薄弱点
    duration_seconds INT,
    
    -- 追问记录
    follow_up_questions JSON,
    follow_up_answers JSON,
    
    session_id VARCHAR(100)
);
```

#### 2. question_metadata - 题目元数据表
存储题目的掌握情况和复习调度信息。

```sql
CREATE TABLE question_metadata (
    question_id VARCHAR(255) PRIMARY KEY,
    file_path VARCHAR(500) NOT NULL,
    module VARCHAR(100) NOT NULL,
    
    -- 掌握情况
    mastery_level VARCHAR(10) DEFAULT '⚪',  -- 🟢🟡🔴⚪
    total_attempts INT DEFAULT 0,
    avg_score DECIMAL(3,2),
    
    -- 复习调度（SM-2 算法）
    last_review DATE,
    next_review DATE,
    review_interval_days INT DEFAULT 1,
    easiness_factor DECIMAL(3,2) DEFAULT 2.50,
    repetitions INT DEFAULT 0,
    
    -- 知识关联
    related_questions JSON,
    keywords JSON
);
```

#### 3. knowledge_relations - 知识关联表
存储题目之间的关联关系（对比、递进、场景、前置）。

#### 4. error_analysis - 错误分析表
存储错题的深度分析结果。

#### 5. sessions - 会话记录表
存储每次学习会话的统计信息。

#### 6. user_profile - 用户画像表
存储用户偏好、学习模式等长期记忆。

#### 7. review_queue - 复习队列表
存储待复习题目的队列。

#### 8. agent_interactions - Agent 协作日志
记录 Agent 之间的通信。

---

## ⚙️ 配置说明

### 主配置文件：harness.yaml

```yaml
# LLM 配置
llm:
  provider: "openai"
  base_url: "https://api.deepseek.com"
  base_url_env: "DEEPSEEK_BASE_URL"
  api_key: null
  api_key_env: "DEEPSEEK_API_KEY"
  model: "deepseek-chat"
  model_env: "DEEPSEEK_MODEL"
  temperature: 0.7
  max_tokens: 2000

# 数据库配置
database:
  type: "mysql"
  host: "localhost"
  port: 3306
  database: "ai_interview"
  user: "root"
  password: "your_password"  # 请修改
  charset: "utf8mb4"

# 知识库配置
knowledge_base:
  default: "java_interview"           # 默认知识库
  config_file: "knowledge_bases.yaml" # 知识库配置文件

# 记忆系统配置
memory:
  short_term:
    enabled: true
    max_turns: 20
  medium_term:
    enabled: true
    storage: "database"
  long_term:
    enabled: true
    files:
      - ".harness/memory/USER.md"
      - ".harness/memory/LEARNING_PATTERN.md"

# Agent 配置
agents:
  interviewer:
    enabled: true
    prompt_template: "agents/definitions/interviewer.md"
  
  scheduler:
    enabled: true
    algorithm: "sm2"
    initial_interval: 1
  
  linker:
    enabled: true
    similarity_threshold: 0.7
  
  analyzer:
    enabled: true
  
  supervisor:
    enabled: true
  
  buddy:
    enabled: true
```

---

## 🔧 开发规范

### 代码风格

- **Python**: PEP 8 规范
- **注释**: 关键逻辑必须添加中文注释
- **类型提示**: 使用 Type Hints

### Git 工作流

**单人开发模式**：

- ✅ **直接在 main 分支开发** - 无需创建新分支
- ✅ **每完成一个功能就提交** - 保持提交频率
- ✅ **使用中文约定式提交** - `<type>(<scope>): <中文描述>`

**提交示例**:
```bash
# 简单提交
git add .
git commit -m "feat(agent-loop): 实现 Agent Loop 核心循环"

# 详细提交
git commit -m "feat(agent-loop): 实现 TAOR 循环

- 添加 Think → Act → Observe → Reflect 四步循环
- 实现退出条件控制
- 支持工具调用"
```

**详细规则**: 参考 `GIT_RULES.md`

### 工具使用

```python
# 从标准 agents 包导入
from agents.tools.question_tools import get_random_question, search_questions
from agents.tools.memory_tools import add_learning_record, get_weak_modules
from agents.roles.interviewer_agent import InterviewerAgent
from agents.core.agent_loop import AgentLoop
from agents.core.tool_registry import ToolRegistry

```

### 命名约定

- **Agent 类**: `XxxAgent` （如 `InterviewerAgent`）
- **工具函数**: `snake_case` （如 `get_random_question`）
- **配置文件**: `kebab-case.yaml`
- **数据库表**: `snake_case`

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 MySQL（参考 MYSQL_SETUP.md）
mysql -u root -p

# 初始化数据库
python scripts/init_database_mysql.py
```

### 2. 导入题库

```bash
# 导入 Java 面试题（1346 道）到数据库
python scripts/import_questions.py --knowledge-base java_interview
```

### 3. 启动服务

```bash
# 命令行模式（推荐）
python scripts/cli_interview.py

# 完整流程演示
python scripts/demo_full_flow.py
```

### 4. 添加新知识库（可选）

```bash
# 1. 创建目录
mkdir -p "知识库/Python面试"

# 2. 添加题目（Markdown 格式）
# 格式与 Java面试 题目相同

# 3. 编辑配置文件
vim .harness/config/knowledge_bases.yaml
# 将 python_interview 的 enabled 改为 true

# 4. 导入题库
python scripts/import_questions.py --knowledge-base python_interview
```

---

## 📊 当前进度

### ✅ Phase 0: 基础设施（已完成）
- [x] 项目结构
- [x] 配置文件
- [x] 数据库 Schema（MySQL）
- [x] 题库工具
- [x] 记忆工具
- [x] Agent 基类
- [x] 文档体系

### ⏳ Phase 0.5: Agent Loop 核心（进行中）
- [ ] 工具注册系统（1.5h）
- [ ] Agent Loop（2h）
- [ ] 上下文管理（1h）

### ⏳ Phase 1: 面试官 Agent（待实现）
- [ ] 面试官 Agent 实现
- [ ] 题库导入脚本
- [ ] 命令行界面

### 📅 Phase 2-7: 后续阶段
参考 `PLAN.md`

---

## 🎯 关键概念

### Agent Loop (TAOR 闭环)

核心执行引擎，实现 **Think → Act → Observe → Reflect** 循环。

```python
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

### SM-2 复习算法

基于艾宾浩斯遗忘曲线的间隔重复算法。

```python
def calculate_next_review(easiness, repetitions, performance):
    if performance < 3:
        return 1  # 答错，1天后复习
    elif repetitions == 0:
        return 1  # 第一次，1天后
    elif repetitions == 1:
        return 6  # 第二次，6天后
    else:
        return int(interval * easiness)  # 后续按难度系数递增
```

### 四维度评分

面试官 Agent 从 4 个维度评估答案：

1. **准确性 (Accuracy)**: 概念是否正确
2. **完整性 (Completeness)**: 是否覆盖关键点
3. **深度 (Depth)**: 是否理解原理
4. **场景化 (Scenario)**: 能否结合实际应用

---

## 🐛 常见问题

### 数据库连接失败

**问题**: `Can't connect to MySQL server`

**解决**:
```bash
# 检查 MySQL 是否启动
net start MySQL  # Windows
sudo systemctl start mysql  # Linux

# 检查配置文件中的密码是否正确
# 编辑 .harness/config/harness.yaml
```

### 题库工具测试失败

**问题**: `No module named '.harness'`

**解决**:
```bash
# 确保在项目根目录运行
cd D:\ajie\study\AI-Knowledge
python -m agents.tools.question_tools
```

### 中文编码问题

**问题**: Windows 下中文乱码

**解决**: 所有 Python 文件开头已添加编码处理
```python
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

---

## 📚 参考文档

- **实施计划**: `PLAN.md` - 完整的开发路线图
- **Agent 架构**: `AGENTS.md` - 6 个 Agent 的详细设计
- **对比分析**: `COMPARISON_REPORT_V2.md` - 与生产级 Agent Harness 的对比
- **MySQL 配置**: `MYSQL_SETUP.md` - 数据库配置指南
- **理论手册**: `Agent-Harness-Develop-Book/README.md` - Agent Harness 理论基础

---

## 🤝 贡献指南

### 开发流程

1. 阅读 `PLAN.md` 了解当前阶段
2. 选择一个待实现的模块
3. 参考 `AGENTS.md` 了解设计
4. 编写代码 + 单元测试
5. 更新文档

### 测试规范

```python
# 所有新功能必须包含测试
# 测试文件放在 scripts/ 目录
# 命名规范: test_xxx.py

# 示例
async def test_agent_loop():
    agent = Agent('test')
    loop = AgentLoop(agent, max_rounds=5)
    result = await loop.run("测试输入")
    assert result is not None
```

---

## 📝 更新日志

### v1.0.0 (2026-06-24)
- 初始版本
- 完成基础设施搭建
- 设计 6 个 Agent 架构
- 完成数据库 Schema 设计
- 从 SQLite 迁移到 MySQL
- 生成完整文档体系

---

## 📞 联系方式

**项目维护者**: AI 面试陪练系统开发团队  
**最后更新**: 2026-06-24

---

## 🎉 致谢

本项目基于以下开源项目和理论：

- **Agent Harness 理论**: Agent-Harness-Develop-Book
- **Claude Code**: Anthropic 的生产级 Agent 实现
- **OpenCode**: 开源编程 Agent
- **SuperMemo SM-2**: 间隔重复算法
- **TF-IDF**: 文本相似度计算

---

**祝你面试顺利！💪**
