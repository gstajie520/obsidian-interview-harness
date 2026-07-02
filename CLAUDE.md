# AI 面试陪练系统 - 项目上下文

> **项目**: AI Interview Coach powered by Agent Harness  
> **版本**: 1.1.0  
> **更新**: 2026-06-28

---

## AI 协作执行规则

本节是给 Claude、Codex、Cursor 等 AI 编码助手看的硬性规则。执行代码修改、文档修改或 Git 提交时，必须优先遵守本节。

### Git 提交硬性规则

- 提交前必须读取 `GIT_RULES.md`，并检查 `git status --short`。
- 提交信息必须使用中文描述，禁止纯英文 subject。
- 提交信息必须使用格式：`<type>(<scope>): <中文描述>`。
- `scope` 必须填写，使用小写英文、数字、短横线或下划线，例如 `agents`、`python-comments`、`git-rules`。
- 允许的 `type`：`feat`、`fix`、`docs`、`style`、`refactor`、`test`、`chore`、`perf`。
- 正确示例：`docs(project): 同步项目文档状态`。
- 每次完成文件修改并验证后必须提交；同一任务内相关文件可以合并为一个提交。
- 除非用户明确说“不要提交”或“先别提交”，否则最终回复前不能留下未提交修改。
- `git add`、`git commit`、`git reset`、`git config` 等会写入 `.git` 的命令禁止并行执行。
- 提交后必须执行 `git status --short` 和 `git log -1 --oneline` 验证结果。

本仓库使用 `.githooks/commit-msg` 校验提交信息。若 hook 未启用，执行：

```bash
git config core.hooksPath .githooks
```

### 学习型开发规则

项目维护者是 Python 初学者，有 Java 基础。AI 修改 Python 代码时，必须兼顾“功能实现”和“学习可读性”：

- 业务流程要写清楚：关键函数、数据流、数据库写入、Agent 调用链路都要让初学者能跟上。
- 对 Python 特有语法要适当补充注释，例如装饰器、上下文管理器、列表推导式、`async/await`、`Optional`、`dict.get()`、解包、`dataclass`。
- 优先用 Java 类比解释，例如“类似 Java 的 Map / POJO / try-with-resources / super(...)”。
- 注释解释“为什么这样做”和“这一步在流程里的作用”，不要写无意义注释，例如“把 a 赋值给 a”。
- 新增或修改复杂逻辑时，优先拆成小函数，并给函数写清楚 docstring，便于边开发边学习 Python、Agent Harness 和 AI 工程知识。

---

## 项目定位

这是一个基于 **Agent Harness 架构** 的 AI 面试陪练系统。当前默认使用本地 SQLite 记忆库，逐步扩展为多 Agent、API 服务、Web UI 和 Obsidian 集成。

核心目标：

- 从 `知识库/` 中读取 Markdown 面试题。
- 使用面试官 Agent 发起提问、追问和评分。
- 将学习记录、题目掌握度和复习时间写入 `.harness/db/learning.db`。
- 根据答题记录识别薄弱模块，并通过 SM-2 思路安排复习。
- 最终形成 6 个协作 Agent：面试官、复习调度器、知识关联器、错题分析师、监督助手、陪练伙伴。

---

## 当前真实进度

| 模块 | 状态 | 说明 |
|---|---|---|
| Agent 核心引擎 | 已实现 | `AgentLoop`、`ToolRegistry`、`ContextManager`、`BaseAgent` |
| LLM 调用重试 | 已实现 | `AgentLoop` 内置指数退避重试，处理网络抖动和临时 API 错误 |
| 并行工具执行 | 已实现 | 同一轮多个 tool call 可并行执行 |
| 面试官 Agent | 已实现 MVP | 可启动基础面试闭环，支持工具注册和学习记录写入 |
| 题库导入 | 已实现 | `scripts/import_questions.py` 支持幂等导入，重复执行不会重复写入元数据 |
| 记忆工具 | 已实现 | 学习记录、题目元数据、薄弱模块、复习时间 |
| 数据库 | SQLite 默认、MySQL 可选 | 零配置优先使用 SQLite；MySQL 有 schema 和说明，但不是默认启动方式 |
| CLI | 已实现 | `scripts/cli_interview.py` 是当前主要交互入口 |
| FastAPI 服务 | 已实现基础能力 | 会话、统计、题目查询、健康检查接口可用 |
| WebSocket | 协议骨架已实现 | `/ws/interview` 可联调实时消息，真实 LLM 流式评分待接入 |
| 复习调度器 Agent | 基础实现 | 可生成每日复习清单，并更新题目下次复习时间 |
| 监督助手 Agent | 基础实现 | 可生成日报、周报 Markdown，并汇总薄弱模块和到期复习 |
| 错题分析师 Agent | 基础实现 | 可识别概念混淆、细节遗漏、场景不足、前置知识缺失，并输出补救建议 |
| 其他角色 Agent | 基础实现/进行中 | `LinkerAgent`、`BuddyAgent` 已具备基础能力，继续补齐关联质量 |
| 多 Agent 编排 | 进行中 | 已有多 Agent 编排线性路径，消息总线未实现 |
| Web UI | 已工程化 | `frontend/` 使用 React + TypeScript + Vite，FastAPI `/ui` 托管 `ui_build/` 构建产物并提供 SPA fallback |
| Obsidian 自动导出 | 未实现 | 现阶段仍以数据库和 Markdown 知识库为主 |

---

## 技术栈

### 后端

- **语言**: Python 3.9+
- **API**: FastAPI + WebSocket
- **默认数据库**: SQLite，配置模板为 `.harness/config/harness.yaml.example`
- **可选数据库**: MySQL，参考 `MYSQL_SETUP.md`
- **LLM SDK**: OpenAI 兼容接口，默认模型为 DeepSeek `deepseek-chat`
- **配置**: PyYAML + python-dotenv
- **测试**: pytest + `scripts/test_agent_loop.py`

### AI / Agent Harness

- **AgentLoop**: 手写 TAOR 循环，帮助学习 Agent Harness 原理。
- **ToolRegistry**: 将普通 Python 函数包装成 LLM 可调用工具。
- **ContextManager**: 统计 token，并在上下文过长时压缩消息。
- **未来方向**: 在理解原生实现后，再对比学习 LangChain / LangGraph。

### 前端和集成规划

- **Web UI**: 已迁移到 React + TypeScript + Vite 工程；后续继续增强交互和图表。
- **Obsidian**: 计划自动生成学习记录、周报和错题笔记。

---

## 项目结构

```text
obsidian-interview-harness/
├── agents/
│   ├── core/
│   │   ├── base_agent.py            # Agent 基类：配置、prompt、LLM 客户端
│   │   ├── agent_loop.py            # TAOR 循环、LLM 重试、并行工具执行
│   │   ├── context_manager.py       # 上下文 token 统计和压缩
│   │   └── tool_registry.py         # 工具注册和执行
│   ├── roles/
│   │   ├── interviewer_agent.py     # 面试官 MVP
│   │   ├── scheduler_agent.py       # 复习调度器基础能力
│   │   ├── linker_agent.py          # 知识关联器骨架
│   │   ├── analyzer_agent.py        # 错题分析师基础能力
│   │   ├── supervisor_agent.py      # 监督助手基础报告能力
│   │   └── buddy_agent.py           # 陪练伙伴骨架
│   ├── tools/
│   │   ├── question_tools.py        # Markdown 题库读取
│   │   └── memory_tools.py          # SQLite/MySQL 记忆读写
│   └── definitions/                 # 各 Agent 的 system prompt
├── scripts/
│   ├── cli_interview.py             # 命令行面试入口
│   ├── harness_server.py            # FastAPI / WebSocket 服务
│   ├── import_questions.py          # 题库元数据导入
│   ├── init_database.py             # 初始化 SQLite
│   ├── init_database_mysql.py       # 初始化 MySQL（可选）
│   ├── demo_full_flow.py            # 完整流程演示
│   └── test_agent_loop.py           # 核心引擎冒烟测试
├── tests/
│   ├── test_config_defaults.py
│   ├── test_core_engine.py
│   ├── test_harness_server.py
│   ├── test_import_questions.py
│   ├── test_interviewer_mvp_flow.py
│   ├── test_memory_tools.py
│   ├── test_analyzer_agent.py
│   ├── test_supervisor_agent.py
│   └── test_scheduler_agent.py
├── .harness/
│   ├── config/
│   │   ├── harness.yaml.example     # 默认 SQLite 配置模板
│   │   ├── harness.yaml             # 本地运行配置
│   │   └── agents_config.yaml
│   ├── db/
│   │   ├── schema.sql               # SQLite schema
│   │   └── schema_mysql.sql         # MySQL schema
│   └── memory/                      # 用户画像和长期记忆文件
├── frontend/                        # React + TypeScript + Vite 前端源码
│   ├── src/
│   │   ├── routes/                  # Dashboard / Interview / Review / Stats 路由页
│   │   ├── components/              # 复用 UI 组件
│   │   ├── lib/                     # API / 类型 / 工具函数
│   │   └── styles/                  # 全局样式系统
│   ├── public/                      # 公开静态资源
│   ├── package.json
│   └── vite.config.ts
├── ui_build/                        # FastAPI `/ui` 默认托管的前端构建产物
├── web_ui/                          # 旧版静态原型页（保留作迁移参考）
├── 知识库/                          # Markdown 面试题库
├── 学习记录/                        # Obsidian 风格学习记录目录
├── AGENTS.md                        # 6 个 Agent 的架构设计
├── PLAN.md                          # 最新实施计划
├── SYSTEM_LEARNING_GUIDE.md         # 面向初学者的系统学习总览
├── LEARNING_MAP.md                  # 思维导图和记忆卡片
├── README.md                        # 项目首页和快速开始
└── GIT_RULES.md                     # Git 提交规则
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

如果要开发或重建前端，再安装 Node 依赖：

```bash
cd frontend
npm install
```

### 2. 准备配置

```bash
cp .harness/config/harness.yaml.example .harness/config/harness.yaml
```

PowerShell 可用：

```powershell
Copy-Item .harness\config\harness.yaml.example .harness\config\harness.yaml
```

默认数据库类型是 `sqlite`。如果要调用真实 LLM，需要配置 DeepSeek API Key：

```powershell
$env:DEEPSEEK_API_KEY="你的 DeepSeek API Key"
```

### 3. 初始化数据库并导入题库

```bash
python scripts/init_database.py
python scripts/import_questions.py --knowledge-base java_interview
```

### 4. 使用统一入口启动项目

推荐优先使用根目录 `main.py`：

```bash
python main.py
```

默认会启动 FastAPI 服务和 `/ui` 前端。

常用子命令：

```bash
python main.py serve
python main.py cli
python main.py init-db
python main.py import-questions --knowledge-base java_interview
python main.py bootstrap
```

### 5. 启动命令行面试

```bash
python main.py cli
```

常用命令：

```text
help   查看帮助
stats  查看学习统计
quit   退出面试
```

### 6. 启动 API 服务

```bash
python main.py serve
```

如果修改了 React 前端源码，先重新构建：

```bash
cd frontend
npm run build
```

常用接口：

```text
GET    /api/health
POST   /api/session/create
GET    /api/session/{session_id}
DELETE /api/session/{session_id}
GET    /api/stats/overview
GET    /api/stats/weak-modules
GET    /api/stats/due-reviews
GET    /api/questions/random
GET    /api/questions/search
GET    /api/questions/{question_id}
WS     /ws/interview
```

---

## 测试和验证

当前自动化测试放在 `tests/`，不是 `scripts/`。

```bash
python -m pytest tests -q
python -m compileall agents scripts tests
python scripts/test_agent_loop.py
```

这些验证分别覆盖：

- `pytest`：业务和 API 自动化测试。
- `compileall`：检查 Python 文件语法能否编译。
- `test_agent_loop.py`：核心 Agent Loop 冒烟测试。

---

## 当前开发优先级

1. **补齐 LinkerAgent**：先做轻量关键词/模块关联，再考虑 TF-IDF。
2. **补齐 BuddyAgent**：实现提示、通俗解释和学习陪伴能力。
3. **增强 AnalyzerAgent**：后续接入相似错误检索和补救题推荐。
4. **实现多 Agent 编排器**：让 Interviewer、Scheduler、Analyzer、Linker、Supervisor 能串起来。
5. **增强 WebSocket**：从协议骨架升级到真实面试流式交互。
6. **增强 Web UI**：已完成 Dashboard/Interview/Review/Stats 四页静态站点，后续接入真实 LLM 流式与更丰富的图表。
7. **开发 Obsidian 导出**：在 API 稳定后推进。

---

## 关键概念速记

### TAOR 循环

```text
Think    调用 LLM，让模型判断下一步
Act      如果 LLM 返回 tool_calls，就准备执行工具
Observe  ToolRegistry 执行 Python 工具，并把结果放回消息历史
Reflect  LLM 基于工具结果继续思考，或输出最终回复
```

### Java 类比

```text
scripts/cli_interview.py          -> Controller / main 方法
agents/roles/interviewer_agent.py -> Service
agents/core/agent_loop.py         -> 框架执行循环
agents/core/tool_registry.py      -> Map<String, Function>
agents/tools/memory_tools.py      -> Repository / DAO
.harness/db/learning.db           -> 数据库
```

### SM-2 复习

答得差就缩短复习间隔，答得好就拉长间隔。当前具体计算在 `agents/tools/memory_tools.py`，`SchedulerAgent` 负责调用和组织结果。

---

## 参考文档

- `README.md`：项目首页和快速开始。
- `PLAN.md`：最新阶段计划和下一步开发路线。
- `AGENTS.md`：6 个 Agent 的职责和协作设计。
- `SYSTEM_LEARNING_GUIDE.md`：面向初学者的系统学习总览。
- `LEARNING_MAP.md`：思维导图和记忆卡片。
- `COMPARISON_REPORT_V2.md`：与目标 Agent Harness 能力的差距分析。
- `MYSQL_SETUP.md`：可选 MySQL 配置。
- `GIT_RULES.md`：Git 提交格式和流程。

---

## 更新日志

### v1.1.0 (2026-06-28)

- 同步当前真实状态：SQLite 默认、FastAPI 基础服务、WebSocket 协议骨架、SchedulerAgent 部分实现。
- 更新测试位置和测试清单。
- 明确后续优先级：Linker、Buddy、Analyzer 增强、多 Agent 编排、WebSocket 增强。

### v1.0.0 (2026-06-24)

- 初始版本。
- 完成基础设施规划和 6 个 Agent 架构设计。

