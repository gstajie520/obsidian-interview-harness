# AI 面试陪练 Agent Harness - 最新实施计划

> **文档版本**: 1.1.0  
> **创建日期**: 2026-06-24  
> **最近更新**: 2026-06-28  
> **当前重点**: 在已完成 CLI、API 基础能力和复习调度器后，继续补齐其余 Agent 和多 Agent 编排。

---

## 1. 项目目标

构建一个基于 Agent Harness 理念的 AI 面试陪练系统，让用户可以一边练习面试题，一边积累学习记录、识别薄弱点、自动安排复习，并逐步扩展到 Web UI 和 Obsidian 笔记工作流。

核心能力：

- 从 `知识库/` 读取 Markdown 面试题。
- 通过面试官 Agent 完成提问、追问、评分和反馈。
- 将答题记录、题目掌握度、复习时间写入 `.harness/db/learning.db`。
- 使用 SM-2 思路安排复习。
- 逐步形成 6 个协作 Agent：面试官、复习调度器、知识关联器、错题分析师、监督助手、陪练伙伴。

---

## 2. 当前技术栈

### 后端

- **语言**: Python 3.9+
- **API**: FastAPI + WebSocket
- **默认数据库**: SQLite，零配置优先
- **可选数据库**: MySQL，保留 schema 和配置说明
- **LLM**: OpenAI 兼容接口，默认 DeepSeek `deepseek-chat`
- **配置**: PyYAML + python-dotenv
- **测试**: pytest + `scripts/test_agent_loop.py`

### Agent Harness

- **AgentLoop**: 手写 TAOR 循环，已支持 LLM 重试和同轮并行工具执行。
- **ToolRegistry**: 注册 Python 函数，并生成 OpenAI function calling 兼容 schema。
- **ContextManager**: 统计 token，并在上下文过长时压缩消息。
- **BaseAgent**: 统一配置、Prompt 和 LLM 客户端初始化。

### 前端和集成规划

- **Web UI**: 计划 React + TypeScript + Vite。
- **Obsidian**: 计划自动导出学习记录、周报、错题本和知识图谱。
- **LangChain / LangGraph**: 当前先保留原生实现用于学习底层原理，后续再做框架对比。

---

## 3. 当前文件结构和状态

```text
obsidian-interview-harness/
├── agents/
│   ├── core/
│   │   ├── base_agent.py            ✅ Agent 基类
│   │   ├── agent_loop.py            ✅ TAOR 循环、LLM 重试、并行工具执行
│   │   ├── context_manager.py       ✅ 上下文 token 管理
│   │   └── tool_registry.py         ✅ 工具注册和执行
│   ├── roles/
│   │   ├── interviewer_agent.py     ✅ 面试官 MVP
│   │   ├── scheduler_agent.py       ✅ 复习调度器基础能力
│   │   ├── linker_agent.py          ⏳ 知识关联器骨架
│   │   ├── analyzer_agent.py        ⏳ 错题分析师骨架
│   │   ├── supervisor_agent.py      ✅ 监督助手基础报告能力
│   │   └── buddy_agent.py           ⏳ 陪练伙伴骨架
│   ├── tools/
│   │   ├── question_tools.py        ✅ 题库读取工具
│   │   └── memory_tools.py          ✅ 学习记录和复习记忆工具
│   └── definitions/                 ✅ Agent 角色定义文档
├── scripts/
│   ├── cli_interview.py             ✅ 命令行面试入口
│   ├── harness_server.py            ✅ FastAPI / WebSocket 服务
│   ├── import_questions.py          ✅ 幂等题库导入
│   ├── init_database.py             ✅ SQLite 初始化
│   ├── init_database_mysql.py       ✅ MySQL 初始化（可选）
│   ├── demo_full_flow.py            ✅ 完整流程演示
│   └── test_agent_loop.py           ✅ 核心引擎冒烟测试
├── tests/
│   ├── test_config_defaults.py      ✅ 默认配置测试
│   ├── test_core_engine.py          ✅ 核心引擎测试
│   ├── test_harness_server.py       ✅ API 服务测试
│   ├── test_import_questions.py     ✅ 导入脚本测试
│   ├── test_interviewer_mvp_flow.py ✅ 面试闭环测试
│   ├── test_memory_tools.py         ✅ 记忆工具测试
│   └── test_scheduler_agent.py      ✅ 复习调度器测试
├── .harness/
│   ├── config/
│   │   ├── harness.yaml.example     ✅ 默认 SQLite 配置模板
│   │   ├── harness.yaml             ✅ 本地运行配置
│   │   └── agents_config.yaml       ✅ Agent 配置
│   └── db/
│       ├── schema.sql               ✅ SQLite schema
│       └── schema_mysql.sql         ✅ MySQL schema
├── README.md                        ✅ 项目首页
├── CLAUDE.md                        ✅ 项目上下文
├── AGENTS.md                        ✅ Agent 架构文档
├── SYSTEM_LEARNING_GUIDE.md         ✅ 初学者学习总览
├── LEARNING_MAP.md                  ✅ 思维导图
└── GIT_RULES.md                     ✅ Git 提交规则
```

**图例**: ✅ 已完成或可用 | ⏳ 骨架/待实现

---

## 4. 已完成阶段

### Phase 0: 基础设施 ✅

已完成：

- 项目目录结构。
- SQLite schema 和初始化脚本。
- MySQL schema 和可选初始化脚本。
- 配置模板 `.harness/config/harness.yaml.example`，默认数据库为 SQLite。
- 题库工具 `question_tools.py`。
- 记忆工具 `memory_tools.py`。
- Agent 基类 `base_agent.py`。
- 面试官 Prompt 和 6 个 Agent 定义文档。

验证方式：

```bash
python scripts/init_database.py
python -m pytest tests/test_config_defaults.py tests/test_memory_tools.py -q
```

### Phase 0.5: Agent Loop 核心引擎 ✅

已完成：

- `ToolRegistry` 工具注册、schema 生成、工具执行。
- `AgentLoop` TAOR 循环。
- `ContextManager` token 统计和压缩逻辑。
- LLM 调用重试机制。
- 同一轮多个工具并行执行。
- 核心引擎单元测试和冒烟测试。

验证方式：

```bash
python -m pytest tests/test_core_engine.py -q
python scripts/test_agent_loop.py
```

### Phase 1: 面试官 Agent MVP ✅

已完成：

- `InterviewerAgent` 基础面试闭环。
- 命令行入口 `scripts/cli_interview.py`。
- 题库元数据导入脚本 `scripts/import_questions.py`。
- 导入幂等性：重复运行不会重复写入元数据。
- 学习记录保存、薄弱模块统计、复习时间计算。
- 面试闭环测试。

验证方式：

```bash
python scripts/import_questions.py --knowledge-base java_interview
python scripts/cli_interview.py
python -m pytest tests/test_import_questions.py tests/test_interviewer_mvp_flow.py -q
```

### Phase 2: FastAPI 服务基础能力 ✅

已完成：

- `scripts/harness_server.py`。
- 健康检查接口。
- 会话创建、查询、删除接口。
- 学习统计、薄弱模块、到期复习接口。
- 随机题、题目搜索、题目详情接口。
- `/ws/interview` WebSocket 协议骨架。
- API 自动化测试。

当前边界：

- REST API 已可供前端联调。
- WebSocket 目前是稳定协议骨架，真实 LLM 流式评分尚未接入。

验证方式：

```bash
python scripts/harness_server.py
python -m pytest tests/test_harness_server.py -q
```

### Phase 3.1: 复习调度器 Agent 基础能力 ✅

已完成：

- `SchedulerAgent.get_daily_review_list(limit=20)`。
- `SchedulerAgent.schedule_next_review(question_id, performance)`。
- `SchedulerAgent.process(input_data)` action 路由。
- 复习清单和下次复习时间测试。

验证方式：

```bash
python -m pytest tests/test_scheduler_agent.py -q
```

---

## 5. 当前未完成项

| 模块 | 状态 | 说明 |
|---|---|---|
| SupervisorAgent | 基础完成 | 已支持日报、周报 Markdown、薄弱模块和到期复习汇总；趋势分析后续增强 |
| AnalyzerAgent | 待实现 | 错题原因分类、相似错误、补救建议 |
| LinkerAgent | 待实现 | 相关题推荐、知识关系、后续可引入 TF-IDF |
| BuddyAgent | 待实现 | 分级提示、通俗解释、学习陪伴 |
| 多 Agent 编排器 | 待实现 | 统一协调 6 个 Agent 的调用关系 |
| 消息总线 | 待实现 | Agent 间事件通知和协作日志 |
| WebSocket 真实流式面试 | 待实现 | 将协议骨架接入 InterviewerAgent / LLM |
| Web UI | 待实现 | Dashboard、Interview、Review、Stats 页面 |
| Obsidian 导出 | 待实现 | 学习记录、周报、错题本自动生成 Markdown |

---

## 6. 下一步开发计划

### Step 1: AnalyzerAgent 错题分析

优先级最高，因为 SupervisorAgent 已能生成基础报告，下一步需要把低分记录转成可执行的补救建议。

目标：

- 根据低分学习记录识别错误类型。
- 支持四类错误：概念混淆、细节遗漏、场景不足、前置知识缺失。
- 生成补救建议。
- 后续可和 LinkerAgent 结合推荐补救题。

建议文件：

```text
agents/roles/analyzer_agent.py
tests/test_analyzer_agent.py
```

### Step 2: LinkerAgent 知识关联

目标：

- 先实现轻量版：同模块、关键词、标题相似度。
- 再考虑 TF-IDF 和余弦相似度。
- 推荐相关题，服务于“学完一题顺手扩展一题”。

建议文件：

```text
agents/roles/linker_agent.py
tests/test_linker_agent.py
```

### Step 3: BuddyAgent 陪练伙伴

目标：

- 实现 3 级提示。
- 实现通俗解释。
- 根据学习状态生成简短鼓励或休息建议。

建议文件：

```text
agents/roles/buddy_agent.py
tests/test_buddy_agent.py
```

### Step 4: 多 Agent 编排器

目标：

- 串联 `SchedulerAgent -> InterviewerAgent -> AnalyzerAgent -> LinkerAgent -> SupervisorAgent`。
- 初期不需要复杂 DAG，先实现清晰的线性编排。
- 保留事件记录，为后续消息总线做铺垫。

建议文件：

```text
scripts/multi_agent_orchestrator.py
tests/test_multi_agent_orchestrator.py
```

---

## 7. 里程碑

### Milestone 1: CLI MVP 可用 ✅

- [x] 数据库初始化成功。
- [x] 能导入题库元数据。
- [x] 命令行能启动面试流程。
- [x] 学习记录能保存。
- [x] 核心测试通过。

### Milestone 2: API 服务就绪 ✅

- [x] FastAPI 服务器能启动。
- [x] 基础 REST API 正常工作。
- [x] WebSocket 协议骨架可用。
- [x] API 测试覆盖主要接口。

### Milestone 3: 单 Agent 能力补齐 ⏳

- [x] InterviewerAgent MVP。
- [x] SchedulerAgent 基础能力。
- [x] SupervisorAgent 基础报告能力。
- [ ] AnalyzerAgent 错题分析能力。
- [ ] LinkerAgent 关联推荐能力。
- [ ] BuddyAgent 陪练能力。

### Milestone 4: 多 Agent 协作 ⏳

- [ ] 编排器能串联主要学习流程。
- [ ] Agent 协作结果可记录。
- [ ] 错题、相关题、学习报告能在一次流程中形成闭环。

### Milestone 5: Web UI ⏳

- [ ] Dashboard 页面。
- [ ] Interview 页面。
- [ ] Review 页面。
- [ ] Stats 页面。
- [ ] WebSocket 实时对话。

### Milestone 6: Obsidian 集成 ⏳

- [ ] 自动生成每日学习记录。
- [ ] 自动生成周报。
- [ ] 自动生成错题本。
- [ ] 自动更新学习仪表盘。

---

## 8. 验证命令

每次完成开发后，至少运行：

```bash
python -m pytest tests -q
python -m compileall agents scripts tests
python scripts/test_agent_loop.py
```

如果修改了 API，额外运行：

```bash
python -m pytest tests/test_harness_server.py -q
```

如果修改了数据库或记忆工具，额外运行：

```bash
python -m pytest tests/test_memory_tools.py tests/test_scheduler_agent.py -q
```

---

## 9. 初学者阅读路线

如果忘记系统流程，按这个顺序恢复记忆：

```text
1. README.md
2. SYSTEM_LEARNING_GUIDE.md
3. LEARNING_MAP.md
4. scripts/cli_interview.py
5. agents/roles/interviewer_agent.py
6. agents/core/agent_loop.py
7. agents/core/tool_registry.py
8. agents/tools/memory_tools.py
```

Java 类比：

```text
CLI / API        -> Controller
InterviewerAgent -> Service
AgentLoop        -> 框架执行循环
ToolRegistry     -> Map<String, Function>
memory_tools     -> Repository / DAO
SQLite           -> 本地数据库
```

---

## 10. 文档维护规则

每完成一个功能，需要同步检查这些文档：

- `PLAN.md`：阶段状态、下一步计划、里程碑。
- `CLAUDE.md`：项目上下文、真实能力、测试命令。
- `README.md`：快速开始和当前状态。
- `AGENTS.md`：Agent 职责、实现状态、示例调用。
- `SYSTEM_LEARNING_GUIDE.md`：初学者阅读路线和文件说明。
- `COMPARISON_REPORT_V2.md`：如果修复了报告里的差距，需要更新状态。

提交前必须运行验证，并按 `GIT_RULES.md` 使用中文约定式提交。
