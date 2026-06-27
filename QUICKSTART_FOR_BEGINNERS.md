# 🎓 新手快速入门指南

> **适合人群**: 完全不懂 Agent Harness 的小白  
> **预计时间**: 1 小时理解核心概念，2-3 天实践掌握

---

## 📚 第一步：理解"什么是 Agent Harness"

### 用一句话解释

**Agent Harness 是一个让 AI 能够"自己调用工具"的框架。**

### 举个例子

**没有 Agent Harness 时：**
```
用户: "帮我查一下今天天气"
AI: "抱歉，我无法访问实时数据"  ❌
```

**有了 Agent Harness 后：**
```
用户: "帮我查一下今天天气"
AI 内心: "我需要调用 get_weather 工具"
  ↓ 自动调用工具
  ↓ 获取结果：{"temp": 25, "weather": "晴"}
AI: "今天25度，晴天☀️"  ✅
```

**关键区别**：AI 不再只会"说话"，还会"行动"（调用工具）！

---

## 🧩 第二步：理解核心概念

### 1. Agent（智能体）

**定义**: 一个有明确角色和任务的 AI

**类比**: 
- 面试官 Agent = 一个专门面试别人的 AI
- 翻译 Agent = 一个专门翻译的 AI
- 代码审查 Agent = 一个专门审查代码的 AI

**在我们的项目中**:
```python
# agents/roles/interviewer_agent.py
class InterviewerAgent:
    """面试官 Agent - 专门出题、评分、追问"""
    
    system_prompt = """
    你是一个 Java 面试官。
    你的职责是：
    1. 从薄弱模块出题
    2. 评估答案（四维度评分）
    3. 追问深度问题
    """
```

---

### 2. Tool（工具）

**定义**: Agent 可以调用的 Python 函数

**类比**: 就像给 AI 配备了"超能力"
- `get_weak_modules()` = 让 AI 能"看到"用户薄弱模块
- `get_question_from_module()` = 让 AI 能"抽取"题目
- `save_evaluation()` = 让 AI 能"保存"评分到数据库

**在我们的项目中**:
```python
# agents/roles/interviewer_agent.py（注册工具）
self.tool_registry.register(
    name="get_weak_modules",
    description="获取用户最薄弱的模块列表，用于针对性出题",
    parameters={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "返回前 N 个薄弱模块"
            }
        }
    },
    function=lambda limit=5: get_weak_modules(limit)
)
```

**工具的本质**: 就是一个普通的 Python 函数 + 一段描述（告诉 AI 这个工具是干什么的）

---

### 3. TAOR 循环（核心中的核心）

**TAOR = Think → Act → Observe → Reflect**

这是 Agent Harness 的"心脏"，让 AI 能够：
1. **Think（思考）**: 调用 LLM，决定下一步做什么
2. **Act（行动）**: 如果需要，调用工具
3. **Observe（观察）**: 收集工具执行结果
4. **Reflect（反思）**: 根据结果继续思考 OR 给出最终答案

#### 实际执行流程

```
用户: "请给我出一道 JVM 的题"
    ↓
┌─────────────────────────────────────────┐
│  第 1 轮 TAOR 循环                      │
├─────────────────────────────────────────┤
│ Think: LLM 思考                         │
│   "我需要先看看用户的薄弱模块"        │
│   → 决定调用 get_weak_modules          │
│                                         │
│ Act: 执行工具                           │
│   → get_weak_modules(limit=5)          │
│                                         │
│ Observe: 收集结果                       │
│   → {"modules": ["JVM", "并发"]}       │
│                                         │
│ Reflect: 决定继续循环                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  第 2 轮 TAOR 循环                      │
├─────────────────────────────────────────┤
│ Think: LLM 看到结果                     │
│   "JVM 是薄弱项，我去抽一道题"        │
│   → 决定调用 get_question_from_module  │
│                                         │
│ Act: 执行工具                           │
│   → get_question_from_module("JVM")    │
│                                         │
│ Observe: 收集结果                       │
│   → {"title": "什么是 GC Root?"}       │
│                                         │
│ Reflect: 决定继续循环                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  第 3 轮 TAOR 循环                      │
├─────────────────────────────────────────┤
│ Think: LLM 看到题目                     │
│   "题目已经拿到了，可以出题了"        │
│   → 不调用工具，直接回复              │
│                                         │
│ Reflect: 返回最终答案                  │
│   "以下是你的题目：什么是 GC Root?"   │
└─────────────────────────────────────────┘
    ↓
返回给用户
```

**关键点**:
- ✅ 每轮循环都会调用 LLM
- ✅ LLM 自己决定是否调用工具
- ✅ 循环会一直持续，直到 LLM 不再需要工具（给出最终回复）

---

### 4. Context Manager（上下文管理器）

**问题**: LLM 有上下文长度限制（如 128K tokens）

**解决方案**: 当对话太长时，自动压缩

**工作原理**:
```python
# 假设对话历史有 100 轮
messages = [
    {"role": "user", "content": "第1个问题"},
    {"role": "assistant", "content": "第1个回答"},
    ...
    {"role": "user", "content": "第100个问题"},
]

# Context Manager 检查 token 使用率
if token_usage > 92%:
    # 保留最近 10 轮
    recent = messages[-20:]  # 最近 10 轮 = 20 条消息
    
    # 早期 90 轮用 LLM 摘要
    early = messages[:-20]
    summary = llm.summarize(early)  # "用户主要问了 Java 基础和 JVM 问题"
    
    # 重新组装
    messages = [
        {"role": "system", "content": f"之前的对话摘要：{summary}"},
        *recent
    ]
```

**效果**: 即使对话再长，也不会超出 LLM 窗口限制

---

### 5. Tool Registry（工具注册表）

**作用**: 管理所有工具

**核心方法**:
1. `register()` - 注册一个工具
2. `get_tool_schemas()` - 生成 OpenAI function calling 格式
3. `execute_tool()` - 执行工具

**OpenAI Function Calling 格式**:
```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weak_modules",
        "description": "获取用户的薄弱模块列表",
        "parameters": {
          "type": "object",
          "properties": {
            "limit": {
              "type": "integer",
              "description": "返回前 N 个薄弱模块"
            }
          },
          "required": ["limit"]
        }
      }
    }
  ]
}
```

这个 JSON 会被传给 LLM，LLM 看到后就知道"我可以调用这些工具"。

---

## 🔍 第三步：追踪一次完整的执行流程

让我们打开调试模式，看看系统内部到底发生了什么：

### 启动面试

```bash
python scripts/cli_interview.py
```

### 用户输入

```
用户: 请给我出一道题
```

### 系统内部执行（详细日志）

```
[CLI] 用户输入: 请给我出一道题
  ↓
[InterviewerAgent] start_interview() 被调用
  ↓
[Agent Loop] 开始 TAOR 循环
  ↓
════════════════════════════════════════
  第 1 轮循环
════════════════════════════════════════
[Agent Loop] 第 1/30 轮开始
[Agent Loop] 当前状态: THINKING
  ↓
[Agent Loop] 调用 Context Manager
[Context Manager] Token 使用率: 5% (无需压缩)
  ↓
[Agent Loop] 调用 LLM
  ↓
┌─────────────────────────────────────────┐
│  发送给 LLM 的内容                      │
├─────────────────────────────────────────┤
│ messages: [                             │
│   {                                     │
│     "role": "system",                   │
│     "content": "你是一个面试官..."     │
│   },                                    │
│   {                                     │
│     "role": "user",                     │
│     "content": "请给我出一道题"        │
│   }                                     │
│ ]                                       │
│                                         │
│ tools: [                                │
│   {                                     │
│     "type": "function",                 │
│     "function": {                       │
│       "name": "get_weak_modules",       │
│       ...                               │
│     }                                   │
│   },                                    │
│   ...                                   │
│ ]                                       │
└─────────────────────────────────────────┘
  ↓
[LLM Response] DeepSeek 返回:
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
[Agent Loop] 检测到 1 个工具调用
[Agent Loop] 当前状态: EXECUTING
  ↓
[Tool Registry] 执行工具: get_weak_modules
[Tool Registry] 解析参数: {"limit": 5}
  ↓
[Memory Tools] get_weak_modules(5) 被调用
[Memory Tools] SQL: SELECT module, AVG(overall_score) ...
[Memory Tools] 结果: {"status": "no_data", "message": "还没有学习记录"}
  ↓
[Tool Registry] 工具执行完成
[Agent Loop] 工具 get_weak_modules 执行完成
  ↓
[Agent Loop] 当前状态: OBSERVING
[Agent Loop] 将工具结果添加到消息历史
  ↓
消息历史现在是:
[
  {"role": "system", "content": "你是一个面试官..."},
  {"role": "user", "content": "请给我出一道题"},
  {"role": "assistant", "tool_calls": [...]},
  {"role": "tool", "content": "{\"status\": \"no_data\"}", "tool_call_id": "call_abc123"}
]
  ↓
[Agent Loop] 继续下一轮循环
  ↓
════════════════════════════════════════
  第 2 轮循环
════════════════════════════════════════
[Agent Loop] 第 2/30 轮开始
[Agent Loop] 当前状态: THINKING
  ↓
[Agent Loop] 调用 LLM（带上之前的工具结果）
  ↓
[LLM Response] DeepSeek 看到"还没有学习记录"，决定随机出题:
{
  "tool_calls": [{
    "function": {
      "name": "get_question_from_module",
      "arguments": "{\"module\": \"Java基础\"}"
    }
  }]
}
  ↓
[Agent Loop] 检测到 1 个工具调用
[Agent Loop] 当前状态: EXECUTING
  ↓
[Tool Registry] 执行工具: get_question_from_module
  ↓
[Question Tools] get_random_question("Java基础") 被调用
[Question Tools] 扫描目录: 知识库/Java面试/Java基础/
[Question Tools] 找到 50 个题目文件
[Question Tools] 随机选择: finally中代码一定会执行吗.md
[Question Tools] 解析 Markdown...
[Question Tools] 返回 Question 对象
  ↓
[Tool Registry] 工具执行完成
[Agent Loop] 工具 get_question_from_module 执行完成
  ↓
[Agent Loop] 继续下一轮循环
  ↓
════════════════════════════════════════
  第 3 轮循环
════════════════════════════════════════
[Agent Loop] 第 3/30 轮开始
[Agent Loop] 当前状态: THINKING
  ↓
[Agent Loop] 调用 LLM（带上题目）
  ↓
[LLM Response] DeepSeek 决定不再调用工具，直接回复:
{
  "message": {
    "role": "assistant",
    "content": "好的，题目已获取。以下是你的面试题：\n\n## 题目\n\n**finally 中的代码一定会执行吗？**\n\n请开始作答吧！",
    "tool_calls": null  ← 没有工具调用
  }
}
  ↓
[Agent Loop] LLM 返回最终回复，循环结束
[Agent Loop] 当前状态: IDLE
  ↓
[InterviewerAgent] 返回最终答案
  ↓
[CLI] 显示给用户:
════════════════════════════════════════
面试官: 好的，题目已获取。以下是你的面试题：

## 题目

**finally 中的代码一定会执行吗？**

请开始作答吧！
════════════════════════════════════════
```

---

## 🛠️ 第四步：动手实践

### 练习 1：运行系统并观察日志

```bash
# 1. 启动面试
python scripts/cli_interview.py

# 2. 输入问题
> 请给我出一道题

# 3. 观察控制台输出，找到：
# - [Agent Loop] 第 X 轮开始
# - [Agent Loop] 检测到 X 个工具调用
# - [Agent Loop] 工具 XXX 执行完成
```

### 练习 2：阅读核心代码

**推荐阅读顺序**:

1. **agent_loop.py** - 先理解 TAOR 循环
   - 重点看 `run()` 方法
   - 理解 while 循环的退出条件
   - 理解 Think/Act/Observe/Reflect 四个阶段

2. **tool_registry.py** - 再理解工具系统
   - 重点看 `register()` 方法
   - 理解 `get_tool_schemas()` 如何生成 OpenAI 格式
   - 理解 `execute_tool()` 如何执行工具

3. **interviewer_agent.py** - 最后看完整 Agent
   - 重点看 `__init__()` 中的工具注册
   - 理解 `start_interview()` 如何调用 Agent Loop

### 练习 3：添加一个简单的工具

```python
# 在 interviewer_agent.py 的 __init__() 中添加

# 新增一个"打招呼"工具
def say_hello(name: str) -> str:
    return f"你好，{name}！"

self.tool_registry.register(
    name="say_hello",
    description="向用户打招呼",
    parameters={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "用户的名字"
            }
        },
        "required": ["name"]
    },
    function=say_hello
)
```

**测试**:
```
> 请叫我"小明"并打招呼

# LLM 会自动调用 say_hello("小明")
# 返回："你好，小明！"
```

---

## 📖 第五步：深入学习资源

### 必读文档（按优先级排序）

1. **README.md** ⭐⭐⭐⭐⭐
   - 快速启动
   - 当前目录结构
   - 常用命令

2. **AGENTS.md** ⭐⭐⭐⭐
   - 六个 Agent 的职责
   - 协作流程
   - 配置说明

3. **CLAUDE.md** ⭐⭐⭐
   - 项目概览
   - 技术栈
   - 数据库设计

4. **Agent-Harness-Develop-Book/README.md** ⭐⭐⭐⭐⭐
   - Agent Harness 理论基础
   - 设计模式
   - 最佳实践

### 代码阅读路径

```
第 1 天：理解执行流程
  ├─ scripts/cli_interview.py (入口)
  ├─ agents/roles/interviewer_agent.py (Agent 主体)
  └─ agents/core/agent_loop.py (TAOR 循环)

第 2 天：理解工具系统
  ├─ agents/core/tool_registry.py (工具注册)
  ├─ agents/tools/question_tools.py (题库工具)
  └─ agents/tools/memory_tools.py (记忆工具)

第 3 天：理解高级特性
  ├─ agents/core/context_manager.py (上下文压缩)
  └─ PLAN.md (后续扩展计划)
```

---

## 🎯 第六步：常见问题

### Q1: TAOR 循环为什么要"循环"？

**A**: 因为很多任务需要多步完成。

例如：
```
用户: "帮我分析薄弱模块并出3道题"

第 1 轮: LLM 调用 get_weak_modules
第 2 轮: LLM 看到结果，调用 get_question_from_module (第1题)
第 3 轮: LLM 调用 get_question_from_module (第2题)
第 4 轮: LLM 调用 get_question_from_module (第3题)
第 5 轮: LLM 整理3道题，返回最终答案
```

如果没有循环，LLM 只能调用一次工具就结束了。

---

### Q2: LLM 怎么知道要调用哪个工具？

**A**: 通过 **OpenAI Function Calling** 机制。

我们把工具定义（名称、描述、参数）传给 LLM，LLM 根据用户问题自己判断需要调用哪个工具。

就像给 LLM 一个"工具手册"：
```
工具1: get_weak_modules - 获取薄弱模块
工具2: get_question_from_module - 从模块抽题
工具3: save_evaluation - 保存评分

用户问: "给我出一道题"
LLM 思考: "需要先获取薄弱模块，所以调用工具1"
```

---

### Q3: 为什么需要 Context Manager？

**A**: 因为对话太长会超出 LLM 的上下文窗口。

**场景**:
```
用户连续练习 100 道题
  ↓
对话历史有 200 轮（每题 2 轮）
  ↓
消息列表有几百万个 token
  ↓
超出 LLM 的 128K 窗口限制
  ↓
LLM 报错："上下文太长"
```

**Context Manager 的作用**:
- 保留最近 10-20 轮对话（最重要）
- 早期对话用 LLM 摘要成一段话
- 这样就永远不会超窗口

---

### Q4: 工具函数必须是 async 的吗？

**A**: 不是，普通函数也可以。

Agent Loop 会自动兼容：
```python
# 同步工具
def get_weak_modules(limit: int) -> dict:
    return {"modules": [...]}

# 异步工具
async def get_weak_modules(limit: int) -> dict:
    data = await db.query(...)
    return {"modules": data}
```

两种都可以注册，Agent Loop 会自动检测并调用。

---

### Q5: 如果 LLM 调用了不存在的工具怎么办？

**A**: Tool Registry 会返回错误信息。

```python
# tool_registry.py 的 execute_tool() 方法
if tool_name not in self._tools:
    return {
        "status": "error",
        "message": f"工具 {tool_name} 不存在"
    }
```

这个错误会反馈给 LLM，LLM 会看到错误并调整策略。

---

## 🚀 第七步：下一步学习

### 初级目标（1-2 周）
- ✅ 理解 TAOR 循环原理
- ✅ 能够添加简单工具
- ✅ 能够运行和调试系统

### 中级目标（3-4 周）
- ✅ 理解复习调度 Agent 的基础实现
- ⬜ 实现新的业务 Agent（如监督助手、错题分析师）
- ⬜ 添加复杂工具（如知识图谱工具）
- ⬜ 优化 Context Manager（压缩策略）

### 高级目标（1-2 个月）
- ⬜ 实现 Multi-Agent 协作（多个 Agent 互相调用）
- ⬜ 添加 Web UI
- ⬜ 性能优化（并发、缓存）

---

## 📞 遇到问题怎么办？

### 调试技巧

1. **添加 print 语句**
   ```python
   # agent_loop.py
   print(f"[DEBUG] 当前轮次: {self.round}")
   print(f"[DEBUG] LLM 返回: {response}")
   ```

2. **查看数据库**
   ```bash
   # SQLite
   sqlite3 .harness/db/learning.db
   SELECT * FROM learning_records LIMIT 5;
   ```

3. **检查配置文件**
   ```bash
   # 确认 LLM API 配置正确
   cat .harness/config/harness.yaml
   ```

### 常见报错

| 报错 | 原因 | 解决方案 |
|------|------|----------|
| `ModuleNotFoundError: No module named 'agents'` | Python 路径问题 | 在项目根目录运行 |
| `Connection refused` | LLM API 无法访问 | 检查网络、API key |
| `Unexpected argument 'tools'` | LLM 不支持 function calling | 确认使用支持的模型（如 deepseek-chat） |

---

## 🎉 总结

### 核心要点

1. **Agent Harness = LLM + 工具系统 + TAOR 循环**
2. **TAOR 循环让 AI 能够"自己决定调用哪些工具"**
3. **所有复杂功能都是由简单工具组合而成**

### 学习路径

```
理解概念 → 阅读代码 → 动手实践 → 添加工具 → 实现新 Agent
```

### 记住这句话

> **"Agent Harness 的魔法不在于代码有多复杂，而在于让 LLM 自己决定做什么。"**

---

**祝你学习顺利！如有疑问，优先查看 `README.md` 和 `AGENTS.md`。** 🚀
