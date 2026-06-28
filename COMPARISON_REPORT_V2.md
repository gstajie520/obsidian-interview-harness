# 🎯 Agent Harness 精准对比分析（第二版）

> **原则**: 只补充必要的核心功能，避免过度设计  
> **对比基准**: Agent-Harness-Develop-Book（2960行生产级实践指南）  
> **日期**: 2026-06-24
> **当前状态**: P0 核心引擎已迁移到 `agents/core/`，本文保留为架构对比和决策记录。

---

## 📊 核心发现

经过深入分析，当时项目的主要问题是：

### ✅ 已做得很好的部分

1. **四层架构设计** - 完整且清晰
2. **数据库设计** - 8张表，覆盖全面
3. **记忆系统分层** - 短期、中期、长期概念正确
4. **多Agent角色设计** - 6个Agent职责清晰

### ❌ 核心缺失（必须补充）

根据手册标准，当前项目缺失以下**5个核心模块**，按优先级排序：

---

## 🔴 P0 - 必须立即补充（系统无法运行）

### 1. Agent Loop (TAOR 闭环) ⭐⭐⭐⭐⭐

**当时问题**: `base_agent.py` 只有 `call_llm()` 单次调用，**没有循环**

**当前状态**: 已由 `agents/core/agent_loop.py` 提供 TAOR 循环。

**影响**: 
- ❌ 无法自主完成多步骤任务
- ❌ 面试官 Agent 无法追问
- ❌ 不能使用工具（tools）

**标准实现**（来自手册）:
```python
class AgentLoop:
    def __init__(self, agent, max_rounds=30):
        self.agent = agent
        self.max_rounds = max_rounds
        self.round = 0
        self.messages = []
    
    async def run(self, user_input: str):
        """TAOR 循环：Think → Act → Observe → Reflect"""
        self.messages.append({'role': 'user', 'content': user_input})
        
        while self.round < self.max_rounds:
            self.round += 1
            
            # Think: 调用 LLM
            response = await self.agent.call_llm(self.messages)
            
            # Act: 如果有 tool_calls
            if response.tool_calls:
                # 执行工具
                results = await self.execute_tools(response.tool_calls)
                
                # Observe: 收集结果
                self.messages.append({
                    'role': 'assistant',
                    'tool_calls': response.tool_calls
                })
                for res in results:
                    self.messages.append({
                        'role': 'tool',
                        'tool_call_id': res['id'],
                        'content': res['output']
                    })
            else:
                # Reflect: 返回最终答案
                return response.content
        
        return "达到最大轮次"
```

**实现要点**:
- Think → Act → Observe → Reflect 四步循环
- 退出条件：无 tool_calls、达到 max_rounds、用户中断
- 消息历史累积

**预计时间**: 2小时

---

### 2. 工具注册与调用系统 ⭐⭐⭐⭐

**当时问题**: 只有工具函数（`question_tools`, `memory_tools`），**没有注册机制**

**当前状态**: 已由 `agents/core/tool_registry.py` 提供注册、Schema 生成和调用执行。

**影响**:
- ❌ LLM 不知道有哪些工具可用
- ❌ 无法生成 tool_calls
- ❌ Agent Loop 无法执行工具

**标准实现**（来自手册）:
```python
class ToolRegistry:
    def __init__(self):
        self.tools = {}
    
    def register(self, func, name: str, description: str, parameters: dict):
        """注册工具"""
        self.tools[name] = {
            'function': func,
            'description': description,
            'parameters': parameters
        }
    
    def get_tool_schemas(self):
        """生成 OpenAI function calling 格式的 schema"""
        return [
            {
                'type': 'function',
                'function': {
                    'name': name,
                    'description': tool['description'],
                    'parameters': tool['parameters']
                }
            }
            for name, tool in self.tools.items()
        ]
    
    async def execute_tool(self, tool_call):
        """执行工具调用"""
        tool_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        if tool_name not in self.tools:
            return {'error': f'Tool {tool_name} not found'}
        
        func = self.tools[tool_name]['function']
        result = await func(**args)
        return result

# 使用示例
registry = ToolRegistry()

# 注册工具
registry.register(
    func=get_random_question,
    name='get_random_question',
    description='从题库中随机获取一道题目',
    parameters={
        'type': 'object',
        'properties': {
            'module': {
                'type': 'string',
                'description': '模块名称，如 Java基础、JVM等'
            }
        }
    }
)

# 在 LLM 调用时传入
response = llm.create(
    messages=messages,
    tools=registry.get_tool_schemas()  # ← 关键
)
```

**实现要点**:
- 装饰器或手动注册工具
- 自动生成 OpenAI function calling schema
- 执行工具并返回结果

**预计时间**: 1.5小时

---

### 3. 上下文管理（Token 监控 + 压缩）⭐⭐⭐⭐

**当时问题**: 没有 Token 统计和压缩，长对话会超限

**当前状态**: 已由 `agents/core/context_manager.py` 提供 Token 统计和压缩策略。

**影响**:
- ❌ 复习10道题以上就可能超限
- ❌ 对话中断，用户体验差
- ❌ 浪费 Token

**标准实现**（来自手册）:
```python
import tiktoken

class ContextManager:
    def __init__(self, max_tokens=128000, model="deepseek-chat"):
        self.max_tokens = max_tokens
        self.encoding = tiktoken.encoding_for_model(model)
    
    def count_tokens(self, messages):
        """统计 Token 数"""
        total = 0
        for msg in messages:
            content = str(msg.get('content', ''))
            total += len(self.encoding.encode(content))
        return total
    
    def should_compress(self, messages):
        """判断是否需要压缩（超过92%）"""
        current = self.count_tokens(messages)
        return current / self.max_tokens > 0.92
    
    async def compress(self, messages, llm_client):
        """压缩：保留最近10轮，早期对话LLM摘要"""
        if len(messages) <= 20:
            return messages
        
        recent = messages[-20:]  # 保留最近10轮（20条消息）
        old = messages[:-20]
        
        # LLM 摘要早期对话
        summary_prompt = f"将以下对话总结为简短摘要（200字内）：\n{old}"
        summary = await llm_client.create(
            messages=[{'role': 'user', 'content': summary_prompt}]
        )
        
        # 构建压缩后的消息
        compressed = [
            {'role': 'system', 'content': f'[早期对话摘要] {summary}'}
        ] + recent
        
        print(f"压缩：{len(messages)} → {len(compressed)} 条消息")
        return compressed
```

**实现要点**:
- 使用 `tiktoken` 统计 Token
- 阈值触发（92%）
- 保留最近对话 + 早期摘要

**预计时间**: 1小时

---

## 🟡 P1 - 重要但非紧急（提升体验）

### 4. 重试机制（指数退避）⭐⭐⭐

**问题**: 网络抖动、API 限流会导致失败，没有重试

**当前状态**: 已在 `agents/core/agent_loop.py` 的 LLM completion 调用处实现可配置重试，默认 3 次，支持 `retry_attempts`、`retry_initial_delay`、`retry_max_delay` 配置。

**影响**:
- 🟡 稳定性差
- 🟡 用户体验不好

**标准实现**（来自手册）:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=30)
)
async def call_llm_with_retry(self, messages):
    """带重试的 LLM 调用"""
    try:
        return await self.llm_client.create(messages=messages)
    except openai.RateLimitError:
        await asyncio.sleep(60)  # 速率限制，等待更久
        raise
    except openai.APIError as e:
        if e.status_code >= 500:
            raise  # 服务端错误，可重试
        else:
            raise Exception(f"不可重试错误: {e}")
```

**实现要点**:
- 最多重试3次
- 指数退避：1s, 2s, 4s, 8s...
- 区分可重试（5xx）和不可重试错误（4xx）

**预计时间**: 0.5小时

---

### 5. 并行工具执行（可选优化）⭐⭐

**问题**: 多个工具只能串行执行

**当前状态**: 已在 `agents/core/agent_loop.py` 中实现同一轮工具调用并行执行，使用 `asyncio.gather(..., return_exceptions=True)` 并保持 tool 消息写回顺序稳定。

**影响**:
- 🟡 性能慢（但面试场景影响不大）

**标准实现**（来自手册）:
```python
async def execute_tools_parallel(self, tool_calls):
    """并行执行多个工具"""
    tasks = [
        asyncio.create_task(self.execute_tool(call))
        for call in tool_calls
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

**实现要点**:
- 使用 `asyncio.gather`
- 部分失败容错

**预计时间**: 1小时

---

## 🟢 P2 - 可选增强（后期优化）

### 6. Checkpoint（中断恢复）

**问题**: 长任务中断后无法恢复

**影响**: 🟢 面试场景不太需要（单次面试通常不超过30分钟）

### 7. 流式处理（Streaming）

**问题**: 无法实时显示 AI 回复

**影响**: 🟢 体验优化，非必须

### 8. MCP 支持

**问题**: 无法接入外部工具

**影响**: 🟢 扩展性，当前内置工具够用

---

## ❌ 明确不需要的部分（避免过度设计）

根据你的项目场景（面试助手），以下功能**不需要**：

1. ❌ **SubAgent 委派** - 单一面试官 Agent 足够
2. ❌ **DAG 工作流** - 面试流程是线性的
3. ❌ **Agent Teams / Swarm** - 6个Agent是协作，不是对等通信
4. ❌ **Plan & Execute 模式** - 面试不需要复杂规划
5. ❌ **A2A 协议** - 不需要跨平台
6. ❌ **Git Worktree 沙箱** - 不修改代码，无需隔离
7. ❌ **Bash AST 解析** - 不执行命令，无需安全检测

---

## 📋 最终补充清单（当前状态）

### 必须补充（P0）- 已完成

| 模块 | 优先级 | 时间 | 理由 |
|------|-------|------|------|
| **Agent Loop** | ✅ 已完成 | 2h | 已提供 TAOR 循环 |
| **工具注册系统** | ✅ 已完成 | 1.5h | 已支持工具注册、schema 生成和执行 |
| **上下文管理** | ✅ 已完成 | 1h | 已支持 token 统计和压缩策略 |

### 建议补充（P1）- 1.5小时

| 模块 | 优先级 | 时间 | 理由 |
|------|-------|------|------|
| **重试机制** | ✅ 已完成 | 0.5h | 提升稳定性 |
| **并行工具执行** | ✅ 已完成 | 1h | 性能优化 |

**结论**: P0 + P1 已完成，核心 Agent Harness 引擎已经可用。

---

## 🎯 当前实施建议

核心引擎不再是瓶颈。下一步应把开发重心从“框架能不能跑”转到“业务 Agent 是否真正有用”：

1. **SupervisorAgent**：把学习记录转成日报、周报和下一步建议。
2. **AnalyzerAgent**：分析低分记录，输出错误类型和补救建议。
3. **LinkerAgent**：推荐相关题，帮助形成知识网络。
4. **BuddyAgent**：提供分级提示和通俗解释。
5. **多 Agent 编排器**：把复习、面试、分析、推荐、报告串成闭环。

当前同步：SupervisorAgent 和 AnalyzerAgent 已完成基础能力。下一步应优先补齐 LinkerAgent，再补 BuddyAgent，并在此基础上推进多 Agent 编排器。

---

## 📁 文件结构（精简版）

```
agents/core/
├── base_agent.py           ✅ Agent 基类
├── agent_loop.py           ✅ Agent Loop
├── tool_registry.py        ✅ 工具注册
└── context_manager.py      ✅ 上下文管理
```

正式代码统一放在 `agents/` 包内，`.harness/` 只保留配置、数据库和记忆文件。

---

## 🔍 与第一版对比的变化

### 第一版的问题
- ❌ 包含了 Checkpoint（面试场景不需要）
- ❌ 包含了并行执行（优先级不高）
- ❌ 没有强调**工具注册系统**的关键性

### 第二版的改进
- ✅ 聚焦3个核心模块（Loop + 工具 + 上下文）
- ✅ 明确区分 P0/P1/P2
- ✅ 明确列出**不需要**的部分
- ✅ 减少时间：从 4-5h 到实际 4.5h（更精准）

---

## ✅ 总结

### 当前结论

**当前项目 = 核心引擎已补齐 + 业务 Agent 需要继续完善**

- ✅ 数据库、记忆、配置 → 已可用
- ✅ Agent Loop、工具系统、上下文管理 → 已完成
- ✅ 重试机制、并行工具执行 → 已完成
- ✅ Supervisor / Analyzer → 基础业务能力已完成
- ⏳ Linker / Buddy → 待补齐业务能力
- ⏳ WebSocket 真实流式评分、Web UI、Obsidian 导出 → 后续增强

### 关键差距

当前最大的差距已经不是 P0 引擎，而是多 Agent 业务闭环：系统需要把“出题和记录”继续扩展成“复习调度、错题分析、相关题推荐、学习报告、陪练提示”的完整学习流程。

---

**报告完成**: 2026-06-24  
**最近同步**: 2026-06-28  
**对比基准**: Agent-Harness-Develop-Book (2960行)  
**设计原则**: 简单、实用、避免过度设计
