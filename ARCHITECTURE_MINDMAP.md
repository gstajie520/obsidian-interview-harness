# Agent Harness 架构思维导图

## 🎯 系统总览

```
AI 面试陪练系统
├── 用户入口 (CLI)
│   └── scripts/cli_interview.py
│
├── Agent 层（智能决策）
│   └── InterviewerAgent (.harness/agents/interviewer_agent.py)
│       ├── 初始化
│       │   ├── 加载配置 (harness.yaml)
│       │   ├── 创建 Agent Loop
│       │   ├── 创建 Tool Registry
│       │   └── 创建 Context Manager
│       │
│       ├── 工具注册
│       │   ├── get_weak_modules (获取薄弱模块)
│       │   ├── get_question_from_module (抽题)
│       │   ├── get_all_modules (获取所有模块)
│       │   └── save_evaluation (保存评分)
│       │
│       └── 对话处理
│           ├── start_interview() - 开始面试
│           └── continue_interview() - 继续对话
│
├── 推理引擎（TAOR 循环）
│   └── Agent Loop (.harness/agents/agent_loop.py)
│       └── while not should_exit():
│           ├── 1️⃣ Think（思考）
│           │   ├── 组装 System Prompt
│           │   ├── 加载对话历史
│           │   ├── 调用 Context Manager 压缩上下文
│           │   └── 调用 LLM (DeepSeek)
│           │
│           ├── 2️⃣ Act（行动）
│           │   ├── 检查 LLM 返回的 tool_calls
│           │   ├── 如果有 → 执行工具
│           │   └── 如果没有 → 进入 Reflect
│           │
│           ├── 3️⃣ Observe（观察）
│           │   ├── 收集工具执行结果
│           │   └── 将结果添加到消息历史
│           │
│           └── 4️⃣ Reflect（反思）
│               ├── LLM 根据工具结果生成回复
│               └── 返回最终答案 OR 继续循环
│
├── 工具系统
│   ├── Tool Registry (.harness/agents/tool_registry.py)
│   │   ├── 注册工具（装饰器或手动）
│   │   ├── 生成 OpenAI function calling schema
│   │   ├── 解析 tool_calls
│   │   └── 执行工具并返回结果
│   │
│   ├── 题库工具 (.harness/tools/question_tools.py)
│   │   ├── get_all_modules() - 获取所有模块
│   │   ├── get_random_question() - 随机抽题
│   │   ├── parse_question_file() - 解析 Markdown 题目
│   │   └── search_questions() - 搜索题目
│   │
│   └── 记忆工具 (.harness/tools/memory_tools.py)
│       ├── get_weak_modules() - 获取薄弱模块
│       ├── add_learning_record() - 保存学习记录
│       ├── calculate_next_review() - SM-2 算法
│       └── get_learning_stats() - 学习统计
│
├── 上下文管理
│   └── Context Manager (.harness/agents/context_manager.py)
│       ├── count_tokens() - 统计 token 数
│       ├── should_compress() - 是否需要压缩
│       └── compress() - 压缩上下文
│           ├── 保留最近 N 轮对话
│           └── 早期对话用 LLM 摘要
│
├── 记忆系统（数据持久化）
│   ├── SQLite / MySQL
│   │   ├── question_metadata (题目元数据)
│   │   ├── learning_records (学习记录)
│   │   └── sessions (会话记录)
│   │
│   └── SM-2 复习算法
│       ├── 根据评分计算难度系数
│       ├── 计算下次复习间隔
│       └── 更新 next_review 字段
│
└── 配置系统
    ├── .harness/config/harness.yaml (主配置)
    │   ├── LLM 配置 (DeepSeek)
    │   ├── 数据库配置 (SQLite)
    │   └── Agent 配置
    │
    └── .harness/config/knowledge_bases.yaml (知识库配置)
        └── java_interview (1346 道题)
```

---

## 🔄 完整执行流程（以一次面试为例）

### 步骤 1：用户启动 CLI

```
用户执行: python scripts/cli_interview.py
    ↓
CLI 初始化 InterviewerAgent
    ↓
InterviewerAgent.__init__()
    ├── 加载 harness.yaml 配置
    ├── 创建 ToolRegistry
    │   └── 注册 4 个工具
    ├── 创建 ContextManager
    └── 创建 AgentLoop
```

### 步骤 2：开始面试

```
CLI 调用: agent.start_interview("你好，请给我出一道题")
    ↓
InterviewerAgent.start_interview()
    ├── 生成 session_id
    ├── 调用 memory_tools.create_session()
    │   └── 在数据库中创建会话记录
    └── 调用 agent_loop.run(user_message)
```

### 步骤 3：Agent Loop 循环（第 1 轮）

```
AgentLoop.run()
    ↓
【THINKING 状态】
    ├── 组装消息列表:
    │   ├── System Prompt (来自 .harness/prompts/interviewer.md)
    │   └── User: "你好，请给我出一道题"
    ├── 调用 ContextManager 检查是否需要压缩
    └── 调用 LLM (DeepSeek API):
        POST https://api.deepseek.com/chat/completions
        {
          "model": "deepseek-chat",
          "messages": [...],
          "tools": [
            {
              "type": "function",
              "function": {
                "name": "get_weak_modules",
                "description": "获取用户的薄弱模块列表",
                "parameters": {...}
              }
            },
            ...
          ]
        }
    ↓
LLM 返回:
    {
      "choices": [{
        "message": {
          "role": "assistant",
          "content": "好的，让我先看看你的薄弱模块...",
          "tool_calls": [{
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "get_weak_modules",
              "arguments": "{\"limit\": 5}"
            }
          }]
        }
      }]
    }
    ↓
【EXECUTING 状态】
    ├── 检测到 tool_calls
    ├── 调用 ToolRegistry.execute_tool()
    │   └── 执行 get_weak_modules(limit=5)
    │       └── memory_tools.get_weak_modules(5)
    │           └── SQL: SELECT module ... ORDER BY mastery_rate
    │           └── 返回: {"status": "no_data", "message": "还没有学习记录"}
    │
    └── 将工具结果添加到消息历史
    ↓
【OBSERVING 状态】
    └── 消息历史现在是:
        ├── System Prompt
        ├── User: "你好，请给我出一道题"
        ├── Assistant: (tool_calls: get_weak_modules)
        └── Tool: {"status": "no_data", ...}
    ↓
循环继续 → 回到 THINKING 状态
```

### 步骤 4：Agent Loop 循环（第 2 轮）

```
【THINKING 状态】
    ├── LLM 看到工具返回"还没有学习记录"
    └── LLM 决定调用另一个工具获取所有模块
    ↓
LLM 返回:
    {
      "tool_calls": [{
        "function": {
          "name": "get_question_from_module",
          "arguments": "{\"module\": \"Java基础\"}"
        }
      }]
    }
    ↓
【EXECUTING 状态】
    ├── 执行 get_question_from_module(module="Java基础")
    │   └── question_tools.get_random_question(module="Java基础")
    │       ├── 扫描 知识库/Java面试/Java基础/ 目录
    │       ├── 随机选一个 .md 文件
    │       ├── 解析 Markdown (frontmatter + 内容)
    │       └── 返回 Question 对象
    │
    ├── InterviewerAgent 存储到 self.current_question
    └── 返回工具结果:
        {
          "status": "success",
          "question_id": "finally中代码一定会执行吗？",
          "title": "finally中代码一定会执行吗？",
          "module": "Java基础",
          "preview": "..."
        }
    ↓
循环继续 → 回到 THINKING 状态
```

### 步骤 5：Agent Loop 循环（第 3 轮）

```
【THINKING 状态】
    ├── LLM 看到题目已获取
    └── LLM 决定不再调用工具，直接回复用户
    ↓
LLM 返回:
    {
      "message": {
        "role": "assistant",
        "content": "好的，题目已获取。以下是你的面试题：\n\n## 题目\n\n**finally 中的代码一定会执行吗？**\n\n请开始作答吧！"
      }
      // 注意：没有 tool_calls
    }
    ↓
【REFLECTING 状态】
    ├── 检测到没有 tool_calls
    ├── 将 assistant 消息添加到历史
    └── 返回最终回复给用户
    ↓
AgentLoop.run() 返回最终答案
    ↓
InterviewerAgent.start_interview() 返回
    ↓
CLI 显示: "面试官: 好的，题目已获取..."
```

### 步骤 6：用户作答

```
用户输入答案
    ↓
CLI 调用: agent.continue_interview(user_answer)
    ↓
AgentLoop.run(user_answer)
    ↓
【新一轮 TAOR 循环】
    LLM 评估答案 → 调用 save_evaluation 工具 → 保存到数据库 → 返回评分
```

### 步骤 7：数据持久化

```
save_evaluation 工具被调用
    ↓
memory_tools.add_learning_record()
    ├── INSERT INTO learning_records (...)
    │   VALUES (question_id, scores, weak_points, ...)
    │
    ├── UPDATE question_metadata
    │   SET total_attempts = total_attempts + 1,
    │       avg_score = (SELECT AVG(...)),
    │       ...
    │
    └── memory_tools.calculate_next_review(question_id, score)
        └── SM-2 算法:
            ├── new_easiness = easiness + (0.1 - (5 - score) * ...)
            ├── new_interval = 根据 repetitions 计算
            └── UPDATE question_metadata
                SET next_review = DATE('now', '+N days')
```

---

## 🧩 核心组件交互图

```
┌──────────────────────────────────────────────────────────┐
│                    用户（CLI）                            │
└────────────────────┬─────────────────────────────────────┘
                     │
                     │ "你好，请出题"
                     ↓
┌──────────────────────────────────────────────────────────┐
│              InterviewerAgent                             │
│  ┌────────────────────────────────────────────────────┐  │
│  │           Agent Loop (TAOR 循环)                   │  │
│  │                                                     │  │
│  │  Think → ┌─────────────┐                          │  │
│  │          │ LLM (DeepSeek)                          │  │
│  │          └──────┬──────┘                           │  │
│  │                 │ tool_calls?                      │  │
│  │                 ↓                                   │  │
│  │  Act ──→ ┌─────────────┐                          │  │
│  │          │ Tool Registry│←──── 工具定义           │  │
│  │          └──────┬──────┘                           │  │
│  │                 │ execute()                        │  │
│  │                 ↓                                   │  │
│  │  Observe ┌─────────────┐                          │  │
│  │          │ Tool Result │                           │  │
│  │          └──────┬──────┘                           │  │
│  │                 │                                   │  │
│  │                 ↓                                   │  │
│  │  Reflect ──→ 最终答案 or 继续循环                 │  │
│  │                                                     │  │
│  └────────────────────────────────────────────────────┘  │
│                                                           │
│  辅助组件:                                               │
│  ├─ Context Manager ← 压缩上下文，防止超窗口           │
│  ├─ Tool Registry   ← 工具注册、schema 生成、执行      │
│  └─ Memory System   ← 数据库读写、SM-2 算法            │
└──────────────────────────────────────────────────────────┘
                     ↓                ↑
        ┌────────────┴────────────────┴───────┐
        │                                      │
   ┌────▼────┐                        ┌───────▼──────┐
   │ 题库工具│                        │  记忆工具    │
   │ (1346题)│                        │  (SQLite DB) │
   └─────────┘                        └──────────────┘
```

---

## 📝 关键数据流

### 数据流 1：题目获取

```
用户 → Agent Loop → LLM → tool_call(get_question_from_module)
                            ↓
                      Tool Registry
                            ↓
                      question_tools.py
                            ↓
                      扫描 知识库/Java面试/
                            ↓
                      解析 Markdown 文件
                            ↓
                      返回 Question 对象 → Agent Loop → LLM → 最终回复
```

### 数据流 2：评分保存

```
用户答案 → Agent Loop → LLM → tool_call(save_evaluation)
                               ↓
                         Tool Registry
                               ↓
                         memory_tools.py
                               ↓
                         ┌─────┴─────┐
                         ↓           ↓
                   add_learning_record  calculate_next_review
                         ↓               ↓
                   INSERT INTO      SM-2 算法计算
                   learning_records     ↓
                                   UPDATE question_metadata
                                   SET next_review = ...
```

### 数据流 3：上下文压缩

```
对话历史增长 → Context Manager.should_compress()
                        ↓
                   token 使用率 > 92%?
                        ↓ Yes
                Context Manager.compress()
                        ↓
                保留最近 10 轮
                        ↓
                早期对话 → LLM 摘要 → 插入为 system 消息
```

---

## 🎓 学习建议

### 从哪里开始阅读代码？

**推荐顺序：**

1. **先看流程** → 读本文档理解整体流程
2. **CLI 入口** → `scripts/cli_interview.py` (简单，看懂交互流程)
3. **Agent 主体** → `.harness/agents/interviewer_agent.py` (核心 Agent)
4. **Agent Loop** → `.harness/agents/agent_loop.py` (TAOR 循环引擎)
5. **工具系统** → `.harness/agents/tool_registry.py` (工具如何注册和执行)
6. **具体工具** → `.harness/tools/*.py` (题库工具、记忆工具)
7. **上下文管理** → `.harness/agents/context_manager.py` (高级特性)

### 调试技巧

在 `agent_loop.py` 的关键位置加 print：

```python
# agent_loop.py 第 60 行附近
async def run(self, user_input: str) -> str:
    print(f"[DEBUG] 用户输入: {user_input}")
    
    while not self.should_exit():
        print(f"[DEBUG] 第 {self.round} 轮循环开始")
        print(f"[DEBUG] 当前状态: {self.state}")
        
        response = await self._call_llm()
        tool_calls = self._get_tool_calls(message)
        
        if tool_calls:
            print(f"[DEBUG] 检测到工具调用: {[tc.function.name for tc in tool_calls]}")
```

---

## 📚 相关文档

- `HARNESS_COMPLETION_REPORT.md` - 完成度报告
- `HARNESS_IMPLEMENTATION.md` - 实施路线图
- `Agent-Harness-Develop-Book/README.md` - 理论手册
- `CLAUDE.md` - 项目上下文

---

**现在你可以按照这个思维导图，从上到下、从左到右理解整个系统了！** 🎉
