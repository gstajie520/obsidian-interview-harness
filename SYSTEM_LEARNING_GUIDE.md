# 系统学习总览

> 目标读者：有 Java 基础、正在学习 Python、Agent Harness 和 AI 工程的新手。
>
> 阅读目标：不用一次记住所有细节，但要知道“用户输入后发生了什么”“每个文件负责什么”“下一步该读哪里”。

---

## 1. 先建立整体画面

这个项目可以先理解成一个“会调用工具的 AI 面试官”。

```text
用户在命令行输入
  -> CLI 脚本接收输入
  -> InterviewerAgent 判断这是开始面试还是继续回答
  -> AgentLoop 把消息发给 LLM
  -> LLM 决定是否调用工具
  -> ToolRegistry 真正执行 Python 工具函数
  -> question_tools 读题库，memory_tools 写数据库
  -> 工具结果回到 LLM
  -> LLM 组织成面试官回复
  -> CLI 打印给用户
```

如果用 Java Web 项目类比：

```text
Controller       -> scripts/cli_interview.py
Service          -> agents/roles/interviewer_agent.py
Framework Loop   -> agents/core/agent_loop.py
Function Router  -> agents/core/tool_registry.py
DAO / Repository -> agents/tools/memory_tools.py
File Repository  -> agents/tools/question_tools.py
Database         -> .harness/db/learning.db
```

区别是：传统 Java 项目通常由代码决定下一步调用哪个 Service；这个项目中，LLM 也参与决策，它可以根据上下文选择调用哪个工具。

---

## 2. 最重要的一句话

`AgentLoop` 是系统心脏，`ToolRegistry` 是工具电话簿，`InterviewerAgent` 是面试官角色，`question_tools` 和 `memory_tools` 是真正做事的业务工具。

你忘记代码时，先回到这句话。

---

## 3. 运行一次面试时的完整链路

### 3.1 程序启动

入口文件是：

```text
scripts/cli_interview.py
```

它做三件事：

```text
1. 打印欢迎信息
2. 创建 InterviewerAgent
3. 进入 while 循环，不断读取用户输入
```

Python 里 `asyncio.run(main())` 可以类比 Java 中启动一个异步任务入口。因为 LLM 调用、工具调用可能是 I/O 操作，所以这里使用 `async/await`。

### 3.2 创建面试官 Agent

代码进入：

```text
agents/roles/interviewer_agent.py
```

`InterviewerAgent.__init__()` 会做这些事：

```text
1. 调用父类 Agent，加载配置和 system prompt
2. 创建 ToolRegistry
3. 注册面试官可用工具
4. 创建 ContextManager
5. 创建 AgentLoop
6. 初始化 current_question 和 session_id
```

Java 类比：

```java
public InterviewerAgent() {
    super("interviewer");
    this.toolRegistry = new ToolRegistry();
    this.registerTools();
    this.contextManager = new ContextManager();
    this.agentLoop = new AgentLoop(this, toolRegistry);
}
```

### 3.3 开始面试

`cli_interview.py` 会调用：

```python
await agent.start_interview()
```

`start_interview()` 会：

```text
1. 生成 session_id
2. 调用 memory_tools.create_session() 创建学习会话
3. 把默认开场消息交给 AgentLoop.run()
```

这里的 `await` 表示“等待异步函数完成”。可以简单理解成：这一步可能耗时，但程序不会用阻塞式写法把所有异步能力锁死。

### 3.4 AgentLoop 开始循环

核心文件：

```text
agents/core/agent_loop.py
```

核心方法：

```python
async def run(self, user_input: str) -> str:
```

它执行 TAOR 循环：

```text
Think    调用 LLM，让模型决定下一步
Act      如果 LLM 返回 tool_calls，就记录工具调用
Observe  调用 ToolRegistry 执行工具，并把结果写回 messages
Reflect  如果没有工具调用，就返回最终回复
```

你可以把 `messages` 理解成 Java 里的 `List<Message>`，它保存本轮对话历史。

### 3.5 LLM 为什么能调用工具

LLM 自己不能直接执行 Python 函数。它只能返回类似这样的结构：

```json
{
  "tool_calls": [
    {
      "function": {
        "name": "get_weak_modules",
        "arguments": "{\"limit\": 5}"
      }
    }
  ]
}
```

真正执行工具的是：

```text
agents/core/tool_registry.py
```

`ToolRegistry` 的职责是：

```text
1. 注册工具函数
2. 生成 OpenAI function calling schema
3. 解析 LLM 返回的 tool_call
4. 执行对应 Python 函数
5. 把执行结果交回 AgentLoop
```

Java 类比：它像一个 `Map<String, Function>`，工具名是 key，真正的 Python 函数是 value。

### 3.6 抽题发生在哪里

工具名：

```text
get_question_from_module
```

注册位置：

```text
agents/roles/interviewer_agent.py
```

实际调用：

```text
agents/tools/question_tools.py
```

`question_tools.get_random_question()` 会：

```text
1. 找到知识库目录
2. 找到模块目录
3. 收集 Markdown 文件
4. 随机选一个文件
5. 解析 frontmatter 和正文
6. 返回 Question dataclass
```

`dataclass` 可以类比 Java 的 POJO / record：主要用来装数据。

### 3.7 保存评分发生在哪里

工具名：

```text
save_evaluation
```

实际写数据库：

```text
agents/tools/memory_tools.py
```

主要写两类数据：

```text
learning_records    每一次答题记录
question_metadata   每一道题的掌握状态、平均分、复习时间
```

保存之后还会调用：

```python
memory_tools.calculate_next_review(question_id, overall_score)
```

它使用 SM-2 思路计算下次复习时间。简单说：答得差，明天复习；答得好，复习间隔变长。

---

## 4. 项目分层说明

### 4.1 入口层：scripts

```text
scripts/
├── cli_interview.py       命令行面试入口
├── harness_server.py      FastAPI / WebSocket 服务入口
├── import_questions.py    导入题库元数据
├── init_database.py       初始化 SQLite 数据库
├── test_agent_loop.py     核心引擎冒烟测试
└── demo_full_flow.py      演示完整流程
```

新手优先读：

```text
1. scripts/cli_interview.py
2. scripts/import_questions.py
3. scripts/test_agent_loop.py
```

### 4.2 核心层：agents/core

```text
agents/core/
├── base_agent.py       Agent 基类：加载配置、prompt、LLM 客户端
├── agent_loop.py       TAOR 循环：系统心脏
├── tool_registry.py    工具注册和调用：工具电话簿
└── context_manager.py  上下文压缩：防止消息太长
```

这一层更像框架代码。业务越复杂，越应该让这些核心能力保持通用。

### 4.3 角色层：agents/roles

```text
agents/roles/
├── interviewer_agent.py  面试官，目前最完整
├── scheduler_agent.py    复习调度器，基础能力已实现
├── linker_agent.py       知识关联器，骨架
├── analyzer_agent.py     错题分析师，骨架
├── supervisor_agent.py   监督助手，基础报告能力已实现
└── buddy_agent.py        陪练伙伴，骨架
```

当前开发重点还是 `InterviewerAgent`，其他角色先理解职责，不急着深入。

### 4.4 工具层：agents/tools

```text
agents/tools/
├── question_tools.py  读 Markdown 题库
└── memory_tools.py    写学习数据库
```

工具层最接近传统业务代码。你学习 Python 时，可以多从这一层开始，因为它不像 AgentLoop 那么抽象。

### 4.5 定义层：agents/definitions

这里是 Markdown prompt，告诉 LLM 每个 Agent 的角色和行为规则。

```text
agents/definitions/interviewer.md
```

它不是 Python 代码，但会影响 LLM 怎么提问、追问和反馈。

---

## 5. Python 语法学习路线

这个项目里最常见的 Python 语法，可以按下面顺序学。

| Python 写法 | 在项目哪里出现 | Java 类比 | 你需要理解什么 |
|---|---|---|---|
| `dict` | 配置、工具参数、LLM 消息 | `Map<String, Object>` | 用 key/value 表示结构化数据 |
| `list` | messages、工具列表 | `List<T>` | 保存有顺序的数据 |
| `Path` | 题库路径、配置路径 | `java.nio.file.Path` | 比字符串拼路径更安全 |
| `with open(...)` | 读 YAML、读文件 | try-with-resources | 自动关闭资源 |
| `Optional[str]` | 可选参数 | `String` 可能为 `null` | 这个值可能没有 |
| `dataclass` | `Question` | POJO / record | 自动生成构造方法等 |
| `async def` / `await` | AgentLoop、CLI | CompletableFuture 思路 | 等待异步 I/O |
| 装饰器 `@registry.register()` | 工具注册 | 注解 + 注册逻辑 | 给函数附加注册行为 |
| 列表推导式 | 提取 weak_points 等 | Stream map/filter | 简洁构造列表 |
| `*args` / `**kwargs` | 工具执行 | 反射调用参数 | 把 dict 展开成函数参数 |

学习建议：不要先系统背 Python 语法。每次看到一个语法，就回到它在业务里的作用。

---

## 6. Agent Harness、LangChain、LangGraph 的关系

### 6.1 当前项目是什么

当前项目是一个手写的轻量 Agent Harness。它自己实现了：

```text
AgentLoop       类似 LangChain AgentExecutor / LangGraph 执行循环
ToolRegistry    类似 LangChain tools
ContextManager  类似上下文压缩和 memory 管理
memory_tools    类似业务侧 memory / persistence
```

这样做的好处是：你能看清楚底层发生了什么，不会一开始就被框架封装挡住。

### 6.2 和 LangChain 怎么对应

LangChain 里常见概念：

```text
LLM / ChatModel   模型调用
Tool              工具函数
Agent             会决定是否调用工具的智能体
Memory            对话或业务记忆
Chain / Runnable  可组合的执行单元
```

本项目对应关系：

```text
Agent._init_llm_client()      -> ChatModel 初始化
ToolRegistry.register()       -> @tool
AgentLoop.run()               -> AgentExecutor.invoke()
memory_tools.py               -> Memory / persistence
question_tools.py             -> Retriever / Tool
```

### 6.3 和 LangGraph 怎么对应

LangGraph 更强调“状态图”：

```text
State   当前任务状态
Node    一个处理节点
Edge    节点之间怎么跳转
Graph   整体流程图
```

如果用 LangGraph 思维看当前系统：

```text
State:
  messages, current_question, session_id

Nodes:
  call_llm
  execute_tools
  save_evaluation
  ask_question

Edges:
  LLM 有 tool_calls -> execute_tools
  LLM 无 tool_calls -> finish
  工具执行完成 -> call_llm
```

也就是说，当前 `AgentLoop` 是一个手写版的小型状态图。

---

## 7. 测试文件怎么帮助你理解系统

测试不是只给机器看的，也可以当学习材料。

```text
tests/test_core_engine.py
  学 AgentLoop、ToolRegistry、ContextManager 怎么配合

tests/test_interviewer_mvp_flow.py
  学一次完整面试如何从抽题到保存评分

tests/test_memory_tools.py
  学学习记录和薄弱模块怎么写入/查询

tests/test_import_questions.py
  学题库元数据导入脚本怎么保证重复运行安全

tests/test_config_defaults.py
  学默认配置为什么必须保持 SQLite 零配置

tests/test_harness_server.py
  学 FastAPI 会话、统计、题目查询接口怎么被验证

tests/test_scheduler_agent.py
  学复习调度器怎么生成每日清单、更新下次复习时间

tests/test_supervisor_agent.py
  学监督助手怎么把统计、薄弱模块和复习清单整理成 Markdown 报告
```

推荐阅读方法：

```text
1. 先看测试函数名
2. 再看 Arrange / Act / Assert
3. 最后回到真实代码找对应函数
```

Java 类比：pytest 测试函数就像 JUnit 的 `@Test` 方法，只是 Python 不一定需要类。

---

## 8. 建议阅读顺序

### 第 1 轮：只看主流程

```text
1. README.md
2. SYSTEM_LEARNING_GUIDE.md
3. LEARNING_MAP.md
4. scripts/cli_interview.py
5. agents/roles/interviewer_agent.py
```

目标：知道用户输入后发生了什么。

### 第 2 轮：看 Agent Harness 核心

```text
1. agents/core/agent_loop.py
2. agents/core/tool_registry.py
3. agents/core/context_manager.py
4. tests/test_core_engine.py
```

目标：理解工具调用循环。

### 第 3 轮：看业务工具

```text
1. agents/tools/question_tools.py
2. agents/tools/memory_tools.py
3. scripts/import_questions.py
4. tests/test_memory_tools.py
5. tests/test_import_questions.py
```

目标：理解题库和数据库。

### 第 4 轮：看规划和扩展

```text
1. AGENTS.md
2. PLAN.md
3. COMPARISON_REPORT_V2.md
4. LANGCHAIN_INTEGRATION.md
```

目标：理解项目未来会怎么扩展。

---

## 9. 常用命令

初始化数据库：

```powershell
python scripts\init_database.py
```

导入题库：

```powershell
python scripts\import_questions.py --knowledge-base java_interview
```

启动命令行面试：

```powershell
python scripts\cli_interview.py
```

跑全部测试：

```powershell
python -m pytest tests -q
```

检查 Python 文件能否编译：

```powershell
python -m compileall agents scripts tests
```

跑核心冒烟测试：

```powershell
python scripts\test_agent_loop.py
```

---

## 10. 以后开发时的学习原则

### 先问业务问题

不要一上来问“这个语法是什么”，先问：

```text
这段代码在业务流程中负责哪一步？
它读了什么数据？
它改了什么状态？
它把结果交给谁？
```

### 再看 Python 写法

业务位置清楚后，再看语法：

```text
这个 dict 存的是什么结构？
这个 Optional 什么时候是 None？
这个 await 在等哪个异步操作？
这个装饰器注册了什么工具？
```

### 最后看 AI 概念

```text
这个函数是 Agent、Tool、Memory、Context 里的哪一种？
如果换成 LangChain，它会是哪一层？
如果换成 LangGraph，它会是 Node、State 还是 Edge？
```

---

## 11. 一张压缩版记忆卡

```text
CLI 接收输入
InterviewerAgent 组装角色
AgentLoop 控制 TAOR 循环
LLM 决定是否调用工具
ToolRegistry 执行工具
question_tools 读题
memory_tools 记忆
ContextManager 防止上下文过长
tests 证明链路没坏
```

如果你看代码看晕了，就回到这张卡片。
