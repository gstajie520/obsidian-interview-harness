# LangChain/LangGraph 集成指南

> **更新**: 2026-06-28  
> **目的**: 学习和对比原生实现 vs 框架实现

---

## 🎯 集成策略

### 渐进式引入（三阶段）

```
Phase 0.5: 原生实现 Agent Loop（已完成）
  ↓
Phase 1: 对比 LangChain 工具系统
  ↓
Phase 2: 尝试 LangGraph 状态图
  ↓
对比分析和选择
```

---

## 📦 安装依赖

```bash
pip install langchain langchain-openai langchain-community langgraph chromadb
```

---

## 🔧 LangChain 集成方案

### 方案 A：混合模式（推荐）

**原生实现保留** + **LangChain 工具系统**

```python
# 使用 LangChain 的工具装饰器
import os

from langchain.tools import tool
from langchain_openai import ChatOpenAI

@tool
def get_random_question(module: str = None) -> dict:
    """从题库中随机获取一道题目
    
    Args:
        module: 模块名称，如"Java基础"、"JVM"等，不传则随机
    
    Returns:
        题目字典，包含 question_id, title, content, module
    """
    from agents.tools.question_tools import get_random_question as _get_question
    question = _get_question(module)
    return question.to_dict() if question else None

@tool
def evaluate_answer(question_id: str, user_answer: str, scores: dict) -> str:
    """评估用户回答并保存记录
    
    Args:
        question_id: 题目ID
        user_answer: 用户的回答
        scores: 评分字典，包含 accuracy, completeness, depth, scenario
    
    Returns:
        保存结果确认信息
    """
    from agents.tools.memory_tools import add_learning_record
    record_id = add_learning_record(
        question_id=question_id,
        user_answer=user_answer,
        scores=scores,
        session_id="current"
    )
    return f"记录已保存，ID: {record_id}"

# Agent Loop 仍然自己实现
class InterviewerAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            api_key=os.getenv("DEEPSEEK_API_KEY")
        )
        self.tools = [get_random_question, evaluate_answer]
    
    async def run(self, user_input: str):
        # 自定义 TAOR 循环
        # 但工具调用使用 LangChain 的格式
        ...
```

**优点**:
- ✅ 保留原生 Agent Loop 的控制力
- ✅ 使用 LangChain 的工具生态（自动生成 schema）
- ✅ 学习价值高（理解两者如何配合）

---

### 方案 B：LangChain Agent（简化）

**完全使用 LangChain 的 Agent**

```python
import os

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# 定义工具
tools = [get_random_question, evaluate_answer]

# 加载 prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

# 创建 Agent
llm = ChatOpenAI(
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
)
agent = create_openai_tools_agent(llm, tools, prompt)

# 执行器
agent_executor = AgentExecutor(agent=agent, tools=tools)

# 运行
result = agent_executor.invoke({"input": "开始面试"})
```

**优点**:
- ✅ 代码量少
- ✅ LangChain 处理所有底层逻辑

**缺点**:
- ❌ 黑盒，不知道内部如何工作
- ❌ 学习价值相对较低

---

### 方案 C：LangGraph（推荐学习）

**使用状态图构建 Agent**

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator

# 定义状态
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    question: dict
    evaluation: dict
    next_action: str

# 定义节点
def think_step(state: AgentState):
    """思考步骤"""
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

def act_step(state: AgentState):
    """行动步骤 - 调用工具"""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        # 执行工具调用
        tool_results = execute_tools(last_message.tool_calls)
        return {"messages": tool_results}
    return state

def observe_step(state: AgentState):
    """观察步骤 - 收集结果"""
    # 处理工具返回结果
    return state

def should_continue(state: AgentState):
    """决定是否继续循环"""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "act"  # 继续执行工具
    else:
        return END  # 结束

# 构建图
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("think", think_step)
workflow.add_node("act", act_step)
workflow.add_node("observe", observe_step)

# 添加边
workflow.set_entry_point("think")
workflow.add_edge("think", "act")
workflow.add_edge("act", "observe")
workflow.add_conditional_edges("observe", should_continue, {
    "act": "think",
    END: END
})

# 编译
app = workflow.compile()

# 运行
result = app.invoke({"messages": [HumanMessage(content="开始面试")]})
```

**优点**:
- ✅ 可视化流程（可以生成状态图）
- ✅ 灵活控制每个步骤
- ✅ 适合复杂的多步骤 Agent
- ✅ 学习价值最高

---

## 📊 三种方案对比

| 特性 | 原生实现 | LangChain Agent | LangGraph |
|------|---------|----------------|-----------|
| **代码量** | 多 | 少 | 中 |
| **学习曲线** | 陡峭 | 平缓 | 中等 |
| **灵活性** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **可控性** | 完全 | 黑盒 | 可控 |
| **调试难度** | 容易 | 困难 | 中等 |
| **学习价值** | 理解原理 | 快速上手 | **最佳平衡** |

---

## 🎓 学习路径

### 已完成：原生实现（Phase 0.5）

**目标**: 深入理解 Agent Loop 原理

```python
# 手写 TAOR 循环
while not should_exit():
    # Think
    response = llm.create(messages, tools)
    
    # Act
    if response.tool_calls:
        results = execute_tools(response.tool_calls)
        
        # Observe
        messages.append(results)
    else:
        # Reflect
        return response.content
```

### 下一步可选：LangChain 工具（Phase 1）

**目标**: 学习工具系统最佳实践

```python
# 使用 @tool 装饰器
@tool
def my_tool(arg: str) -> str:
    """工具描述"""
    return result

# LangChain 自动生成 schema
tools = [tool1, tool2]
llm_with_tools = llm.bind_tools(tools)
```

### 第三周：LangGraph 状态图（Phase 2）

**目标**: 学习复杂 Agent 编排

```python
# 可视化流程
workflow.add_node("step1", func1)
workflow.add_node("step2", func2)
workflow.add_conditional_edges("step1", router)

# 编译并运行
app = workflow.compile()
result = app.invoke(initial_state)
```

---

## 📂 目录结构调整

```
agents/
├── core/
│   ├── base_agent.py           # 原生 Agent 基类
│   ├── agent_loop.py           # 原生 Agent Loop
│   └── tool_registry.py        # 原生工具注册
│
├── integrations/langchain/     # LangChain 版本（可选规划）
│   ├── lc_tools.py             # LangChain 工具定义
│   ├── lc_agent.py             # LangChain Agent
│   └── lc_interviewer.py       # 面试官（LangChain版）
│
└── integrations/langgraph/     # LangGraph 版本（可选规划）
    ├── lg_state.py             # 状态定义
    ├── lg_nodes.py             # 节点函数
    ├── lg_graph.py             # 状态图构建
    └── lg_interviewer.py       # 面试官（LangGraph版）
```

---

## 🧪 对比测试

创建统一接口，方便对比：

```python
# scripts/compare_implementations.py

import asyncio

async def test_native():
    """测试原生实现"""
    from agents.core.agent_loop import AgentLoop
    agent = AgentLoop()
    result = await agent.run("开始面试")
    return result

async def test_langchain():
    """测试 LangChain 实现"""
    from agents.integrations.langchain.lc_agent import LangChainAgent
    agent = LangChainAgent()
    result = await agent.run("开始面试")
    return result

async def test_langgraph():
    """测试 LangGraph 实现"""
    from agents.integrations.langgraph.lg_graph import LangGraphAgent
    agent = LangGraphAgent()
    result = await agent.run("开始面试")
    return result

# 性能对比
import time

for name, test_func in [
    ("原生实现", test_native),
    ("LangChain", test_langchain),
    ("LangGraph", test_langgraph)
]:
    start = time.time()
    result = asyncio.run(test_func())
    elapsed = time.time() - start
    print(f"{name}: {elapsed:.2f}s")
```

---

## 📚 学习资源

### 官方文档

- **LangChain**: https://python.langchain.com/docs/
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **LangSmith**: https://smith.langchain.com/ (调试工具)

### 推荐教程

1. **LangChain 快速入门**
   - Agents 基础
   - Tool 系统
   - Memory 管理

2. **LangGraph 教程**
   - 状态图概念
   - 条件路由
   - 人机协作

3. **最佳实践**
   - 生产环境部署
   - 性能优化
   - 错误处理

---

## ✅ 下一步行动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 选择学习路径

**A. 激进路线** - 直接用 LangGraph（Phase 0.5）
- 快速上手框架
- 少写代码

**B. 稳健路线** - 先原生后框架（推荐）
- Phase 0.5: 原生实现（理解原理）
- Phase 1: 引入 LangChain（学习工具）
- Phase 2: 尝试 LangGraph（学习编排）

**C. 对比路线** - 同时实现两个版本
- 深入理解差异
- 学习价值最高（但工作量大）

---

**你选择哪条路线？** 🚀

我可以帮你实现任意一条！
