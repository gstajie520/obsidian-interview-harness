# AI 面试陪练 Agents 项目

> 一个基于本地知识库、SQLite 记忆库和多 Agent 架构的 AI 面试陪练系统。

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Agent 架构](https://img.shields.io/badge/Agents-Architecture-orange.svg)](AGENTS.md)

## 当前项目是什么

这个仓库正在实现一个“AI 面试陪练系统”。它的核心目标是：

- 从 `知识库/` 中读取面试题。
- 使用面试官 Agent 发起提问、追问和评分。
- 把答题记录保存到 `.harness/db/learning.db`。
- 根据学习记录识别薄弱点，并安排后续复习。
- 逐步扩展为 6 个协作 Agent：面试官、复习调度器、知识关联器、错题分析师、监督助手、陪练伙伴。

当前代码已经整理为标准 Python Agents 项目结构：正式代码放在 `agents/`，配置、数据库和记忆文件放在 `.harness/`。

## 如果你是 Python 初学者

建议先按这个顺序读，不要直接从所有代码开始：

```text
1. SYSTEM_LEARNING_GUIDE.md       系统学习总览，把业务、Python 和 AI 概念串起来
2. LEARNING_MAP.md                快速恢复记忆的流程图和回忆卡片
3. QUICKSTART_FOR_BEGINNERS.md    从零运行项目的操作说明
4. scripts/cli_interview.py       用户输入进入系统的地方
5. agents/roles/interviewer_agent.py  面试官 Agent 如何组装工具和循环
```

本项目后续代码会尽量使用“学习型注释”：解释业务流程、关键 Python 语法，并用 Java 类比帮助理解。

## 当前状态

| 模块 | 状态 | 说明 |
|------|------|------|
| Agent 核心引擎 | 已实现 | `AgentLoop`、`ToolRegistry`、`ContextManager`、`BaseAgent` |
| 面试官 Agent | 已实现 | 可启动基础面试流程 |
| 题库工具 | 已实现 | 读取 Markdown 题库并解析题目信息 |
| 记忆工具 | 已实现 | 保存学习记录、题目元数据和复习信息 |
| SQLite 数据库 | 已实现 | 默认零配置使用 |
| MySQL | 可选 | 有配置和 schema，非默认启动方式 |
| FastAPI 基础服务 | 已实现 | 会话、统计和题目查询接口可用 |
| 复习调度器 Agent | 基础实现 | 可生成每日复习清单、更新下次复习时间 |
| 监督助手 Agent | 基础实现 | 可生成日报、周报 Markdown，并汇总薄弱模块和到期复习 |
| 错题分析师 Agent | 基础实现 | 可识别四类错因，输出证据、补救建议和 Markdown |
| LinkerAgent | 基础实现 | 已支持关键词/模块/标题相似度推荐与关系类型 |
| BuddyAgent | 基础实现 | 支持 3 级提示、通俗解释和陪练建议 |
| 其他 2 个 Agent | 进行中 | 知识关联器和陪练伙伴已具备基础能力，编排器正在串联 |
| Web UI | 已工程化 | `frontend/` 使用 React + TypeScript + Vite 实现，FastAPI `/ui` 托管 `ui_build/` 构建产物 |

## 快速开始

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 1.1 前端开发依赖（改造或重建 UI 时）

```bash
cd frontend
npm install
```

首次拉代码后，如果你只想直接启动后端查看现成界面，可以先不执行这一步，因为仓库已经提交了最新的 `ui_build/` 构建产物。

### 2. 准备配置文件

```bash
cp .harness/config/harness.yaml.example .harness/config/harness.yaml
```

如果你在 Windows PowerShell 中没有 `cp`，可以用：

```powershell
Copy-Item .harness\config\harness.yaml.example .harness\config\harness.yaml
```

然后编辑 `.harness/config/harness.yaml`，填入 DeepSeek 配置：

```yaml
llm:
  provider: "deepseek"
  base_url: "https://api.deepseek.com"
  api_key: "你的 DeepSeek API Key"
  model: "deepseek-chat"
```

也可以不把密钥写进文件，改用环境变量：

```powershell
$env:DEEPSEEK_API_KEY="你的 DeepSeek API Key"
```

### 3. 初始化数据库

```bash
python scripts/init_database.py
```

默认会创建 SQLite 数据库：

```text
.harness/db/learning.db
```

### 4. 导入题库元数据

```bash
python scripts/import_questions.py --knowledge-base java_interview
```

这个命令只会把题目的路径、模块、标题等元数据写入数据库，不会修改 Markdown 原文。

### 5. 使用统一入口启动项目

推荐直接使用根目录入口 `main.py`，不要再手动记多个 `scripts/*.py`：

```bash
python main.py
```

默认行为：

```text
启动 FastAPI 服务，并托管 Web UI
地址：http://127.0.0.1:8000/ui/
```

如果你修改了 `frontend/` 里的 React 源码，记得先重新构建：

```bash
cd frontend
npm run build
```

常用子命令：

```bash
python main.py serve
python main.py cli
python main.py init-db
python main.py import-questions --knowledge-base java_interview
python main.py bootstrap
```

其中：

```text
serve             启动 Web API + Web UI
cli               启动命令行面试
init-db           初始化 SQLite 数据库
import-questions  导入题库元数据
bootstrap         初始化数据库并导入题库，适合首次运行
```

### 6. 启动命令行面试

```bash
python main.py cli
```

常用命令：

```text
help   查看帮助
stats  查看学习统计
quit   退出面试
```

如果你仍想直接运行旧脚本，也可以继续使用：

```bash
python scripts/cli_interview.py
```

### 7. 启动 API 服务

```bash
python main.py serve
```

服务默认监听：

```text
http://127.0.0.1:8000
```

常用接口：

```text
GET  /api/health
GET  /api/stats/overview
GET  /api/questions/random
POST /api/session/create
WS   /ws/interview
```

`/ws/interview` 已实现提交答案到评分闭环的最小实时流程：返回阶段化 `evaluation_chunk` 及最终 `evaluation_complete`，并落库学习记录与多 Agent 编排结果。真实 LLM 流式打分后续可继续增强。

旧方式仍然可用：

```bash
python scripts/harness_server.py
```

### 8. 打开 Web UI

服务启动后，浏览器访问 `/ui` 即可使用四页静态站点：

```text
http://127.0.0.1:8000/ui/             仪表盘入口
http://127.0.0.1:8000/ui/dashboard    仪表盘：整体进度、掌握率、薄弱模块、到期复习
http://127.0.0.1:8000/ui/interview    面试：WebSocket 实时提交答案与闭环结果
http://127.0.0.1:8000/ui/review       复习：到期列表 + 题库检索，一键跳转练习
http://127.0.0.1:8000/ui/stats        统计：关键指标、掌握度分布、薄弱模块
```

前端现在已经迁移为真正的工程化项目：

- `frontend/src/routes/`：页面级路由组件
- `frontend/src/components/`：可复用 UI 组件
- `frontend/src/lib/api.ts`：REST / WebSocket 类型与访问封装
- `ui_build/`：Vite 构建产物，由 FastAPI `/ui` 托管

## 项目结构

```text
AI-Knowledge/
├── agents/                         # 正式 Python Agents 包
│   ├── core/                       # 通用执行引擎
│   │   ├── agent_loop.py           # TAOR 循环
│   │   ├── base_agent.py           # Agent 基类
│   │   ├── context_manager.py      # 上下文和 token 管理
│   │   └── tool_registry.py        # 工具注册和执行
│   ├── roles/                      # 具体 Agent 角色
│   │   ├── interviewer_agent.py    # 面试官 Agent
│   │   ├── scheduler_agent.py      # 复习调度器基础能力
│   │   ├── linker_agent.py         # 知识关联器骨架
│   │   ├── analyzer_agent.py       # 错题分析师基础能力
│   │   ├── supervisor_agent.py     # 监督助手基础报告能力
│   │   └── buddy_agent.py          # 陪练伙伴骨架
│   ├── tools/                      # Agent 可调用工具
│   │   ├── question_tools.py       # 题库读取工具
│   │   └── memory_tools.py         # 学习记录和记忆工具
│   └── definitions/                # Agent 角色定义文档
├── .harness/                       # 运行配置、数据库和记忆
│   ├── config/                     # harness.yaml 等配置
│   ├── db/                         # SQLite / MySQL schema
│   └── memory/                     # 用户画像和长期记忆
├── scripts/                        # 可直接运行的脚本
│   ├── init_database.py            # 初始化 SQLite
│   ├── import_questions.py         # 导入题库元数据
│   ├── cli_interview.py            # 命令行面试入口
│   ├── harness_server.py           # FastAPI 服务入口
│   └── demo_full_flow.py           # 完整流程演示
├── frontend/                       # React + TypeScript + Vite 前端源码
│   ├── src/
│   │   ├── routes/                 # Dashboard / Interview / Review / Stats 路由页
│   │   ├── components/             # 复用组件
│   │   ├── lib/                    # API / 类型 / 工具函数
│   │   └── styles/                 # 全局样式系统
│   ├── public/                     # 公开静态资源
│   ├── package.json
│   └── vite.config.ts
├── ui_build/                       # 前端构建产物（FastAPI `/ui` 托管目标）
├── tests/                          # 自动化测试
├── 知识库/                         # Markdown 面试题库
├── 学习记录/                       # Obsidian 风格学习记录
├── AGENTS.md                       # Agent 架构说明
├── CLAUDE.md                       # 项目上下文
├── PLAN.md                         # 实施计划
└── GIT_RULES.md                    # Git 提交规范
```

## 核心概念

### TAOR 循环

Agent Loop 使用 TAOR 流程：

```text
Think    让 LLM 思考下一步
Act      如果需要工具，就执行工具调用
Observe  把工具结果放回消息历史
Reflect  判断是否继续循环或输出最终回复
```

### 工具注册

`agents/core/tool_registry.py` 负责把普通 Python 函数注册成 LLM 可调用工具，并生成 OpenAI function calling 兼容格式。

### 上下文管理

`agents/core/context_manager.py` 负责统计 token、监控阈值，并在上下文过长时保留最近对话、压缩较早内容。

### 记忆系统

当前主要使用 SQLite 作为中期记忆：

- `learning_records`：每次答题记录。
- `question_metadata`：题目掌握状态。
- `review_queue`：复习安排。
- `user_profile`：用户画像信息。

长期记忆文件放在 `.harness/memory/`。

## 常用开发命令

运行核心测试：

```bash
python -m pytest tests/test_core_engine.py
```

运行全部测试：

```bash
python -m pytest tests -q
```

前端本地开发：

```bash
cd frontend
npm run dev
```

前端生产构建：

```bash
cd frontend
npm run build
```

验证 Agent Loop 脚本：

```bash
python scripts/test_agent_loop.py
```

启动 FastAPI 服务：

```bash
python scripts/harness_server.py
```

检查 Python 文件是否能编译：

```bash
python -m compileall agents scripts tests
```

## 配置说明

主配置文件：

```text
.harness/config/harness.yaml
```

配置模板：

```text
.harness/config/harness.yaml.example
```

默认模型是 DeepSeek：

```yaml
llm:
  provider: "deepseek"
  model: "deepseek-chat"
```

如果后续要换成其他 OpenAI 兼容模型，优先改配置，不要在代码里写死模型名。

## 文档入口

- [SYSTEM_LEARNING_GUIDE.md](SYSTEM_LEARNING_GUIDE.md)：系统学习总览，适合从 Java 转 Python/AI 的学习路线。
- [AGENTS.md](AGENTS.md)：6 个 Agent 的职责和协作方式。
- [CLAUDE.md](CLAUDE.md)：项目上下文、开发约束和运行说明。
- [PLAN.md](PLAN.md)：阶段计划和待办路线。
- [GIT_RULES.md](GIT_RULES.md)：提交信息格式和 Git 工作流。
- [CONTRIBUTING.md](CONTRIBUTING.md)：贡献规范。
- [MYSQL_SETUP.md](MYSQL_SETUP.md)：可选 MySQL 配置。
- [QUICKSTART_FOR_BEGINNERS.md](QUICKSTART_FOR_BEGINNERS.md)：更适合新手的入门说明。

## Git 提交规则

本项目要求使用中文约定式提交：

```text
<type>(<scope>): <中文描述>
```

示例：

```bash
git commit -m "docs(readme): 更新项目说明"
```

本仓库已配置 `.githooks/commit-msg` 校验提交信息。更详细规则见 [GIT_RULES.md](GIT_RULES.md)。

## 开源协议

本项目采用 [MIT License](LICENSE)。


