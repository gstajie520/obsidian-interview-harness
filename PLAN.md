# 🏗️ AI 面试陪练 Agent Harness - 完整实施计划

> **文档版本**: 1.0.0  
> **创建日期**: 2026-06-24  
> **预计总时长**: 12-15 小时  
> **技术栈**: Python + FastAPI + React + SQLite

---

## 📊 项目概览

### 目标
构建一个基于 Agent Harness 理论的智能面试助手系统，具备：
- ✅ 6 个协作 Agent（面试官、监督助手、复习调度器、知识关联器、错题分析师、陪练伙伴）
- ✅ 三层记忆系统（短期、中期、长期）
- ✅ Web UI + Obsidian 双前端
- ✅ 持久化学习数据和自动进化能力

### 技术栈

#### 后端
- **语言**: Python 3.9+
- **框架**: FastAPI（REST API + WebSocket）
- **数据库**: MySQL 8.0+（生产级持久化）
- **ORM**: PyMySQL（数据库驱动）
- **LLM**: OpenAI SDK（兼容 DeepSeek API，默认模型 deepseek-chat，可配置）
- **配置**: PyYAML + python-dotenv

#### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI 库**: Ant Design / Chakra UI
- **状态管理**: Zustand
- **图表**: ECharts / Recharts
- **通信**: Axios + WebSocket

#### 数据存储
- **结构化数据**: MySQL（学习记录、用户画像、复习队列）
- **向量检索**: Chroma（知识关联、题目相似度）
- **文件存储**: Markdown（Obsidian 笔记、会话归档）

#### AI 相关
- **模型**: deepseek-chat（DeepSeek，支持通过配置切换）
- **Prompt 工程**: System Prompt 模板化管理
- **Token 管理**: tiktoken（统计和优化）

#### 部署
- **开发环境**: 本地运行（Windows/Mac/Linux）
- **进程管理**: Python 脚本 + npm
- **一键启动**: start.bat / start.sh

### 核心价值
1. **持久记忆** - 记住所有学习历史，永不遗忘
2. **智能调度** - 基于遗忘曲线自动安排复习
3. **多角色协作** - 6 个 Agent 各司其职
4. **数据驱动** - 可视化进度，精准识别薄弱点
5. **无缝集成** - 与 Obsidian 笔记系统完美融合

---

## 📁 最终文件结构

```
AI-Knowledge/
├── Java八股文/                          # 题库（1346题）
│
├── 学习记录/                            # Agent 生成的记录
│   ├── 每日对话/
│   ├── 周报/
│   ├── 错题本/
│   └── 知识图谱/
│
├── agents/                              # 标准 Python Agents 包（正式实现）
│   ├── core/                            # 通用执行引擎
│   │   ├── base_agent.py                ✅ Agent 基类
│   │   ├── agent_loop.py                ✅ TAOR 循环
│   │   ├── tool_registry.py             ✅ 工具注册
│   │   └── context_manager.py           ✅ 上下文管理
│   │
│   ├── roles/                           # 具体 Agent 角色
│   │   ├── interviewer_agent.py         ✅ 面试官
│   │   ├── supervisor_agent.py          ⏳ 监督助手
│   │   ├── scheduler_agent.py           ⏳ 复习调度器
│   │   ├── linker_agent.py              ⏳ 知识关联器
│   │   ├── analyzer_agent.py            ⏳ 错题分析师
│   │   └── buddy_agent.py               ⏳ 陪练伙伴
│   │
│   ├── tools/                           # Agent 可调用工具
│   │   ├── question_tools.py            ✅ 题库操作
│   │   └── memory_tools.py              ✅ 记忆系统
│   │
│   └── definitions/                     # Agent 角色定义文档
│       ├── interviewer.md               ✅ 面试官
│       ├── supervisor.md                ⏳
│       ├── scheduler.md                 ⏳
│       ├── linker.md                    ⏳
│       ├── analyzer.md                  ⏳
│       └── buddy.md                     ⏳
│
├── .harness/                            # 配置、记忆和数据库
│   ├── config/
│   │   ├── harness.yaml                 ✅ 主配置
│   │   └── agents_config.yaml           ⏳ Agent 配置
│   │
│   ├── db/
│   │   ├── schema.sql                   ✅ 数据库 Schema
│   │   └── learning.db                  ✅ SQLite 数据库
│   │
│   ├── memory/                          # 记忆文件
│   │   ├── USER.md                      ⏳ 用户画像
│   │   ├── LEARNING_PATTERN.md          ⏳ 学习模式
│   │   └── session-archive/             ⏳ 会话归档
│   │
│   └── logs/                            # 日志
│       └── harness.log
│
├── scripts/                             # 工具脚本
│   ├── init_database.py                 ✅ 数据库初始化
│   ├── import_questions.py              ⏳ 导入题库到数据库
│   ├── harness_server.py                ⏳ FastAPI 服务器
│   ├── agent_loop.py                    ⏳ Agent Loop 核心
│   ├── multi_agent_orchestrator.py      ⏳ 多 Agent 编排
│   └── cli_interface.py                 ⏳ 命令行界面
│
├── web_ui/                              # Web 前端
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── requirements.txt                     ✅ Python 依赖
├── README.md                            ✅ 项目首页
├── PLAN.md                              ✅ 本文档
└── CLAUDE.md                            ✅ 项目上下文
```

**图例**: ✅ 已完成 | ⏳ 待实现

---

## 🎯 实施阶段

### Phase 0: 基础设施 ✅ 已完成

**耗时**: 1.5 小时

**已完成项**:
- ✅ 项目目录结构
- ✅ 配置文件（harness.yaml）
- ✅ 数据库 Schema（8张表 - **MySQL 版本**）
- ✅ 数据库初始化脚本（支持 MySQL）
- ✅ 题库工具（question_tools.py）
- ✅ 记忆工具（memory_tools.py - 支持 MySQL）
- ✅ Agent 基类（base_agent.py）
- ✅ 面试官 Prompt 模板
- ✅ Python 依赖文件（包含 pymysql）
- ✅ MySQL 配置文档（MYSQL_SETUP.md）

**验证方式**:
```bash
# 1. 配置 MySQL（参考 MYSQL_SETUP.md）
# 2. 初始化数据库
python scripts/init_database_mysql.py

# 3. 测试工具
python -m agents.tools.question_tools
python -m agents.tools.memory_tools
```

---

### Phase 0.5: Agent Loop 核心引擎 ⏳ **优先实现**

> **⚠️ 重要**: 这是核心缺失项，必须先实现才能继续后续开发！
> 参考：`COMPARISON_REPORT_V2.md` - 精准对比分析（避免过度设计）

> **🎓 学习模式**: 提供**原生实现**和 **LangChain/LangGraph** 两种方案
> 参考：`LANGCHAIN_INTEGRATION.md` - 框架集成指南

**耗时**: 4.5 小时（原生） / 6 小时（含 LangChain）

**核心原则**: 只补充必要的核心功能，避免过度设计

**学习路径**: 建议先原生实现理解原理，再引入框架对比学习

---

#### 实现内容（3个核心模块）

##### 1. 工具注册系统 (Tool Registry) - 1.5小时 ⭐⭐⭐⭐⭐

> **关键**: LLM 必须知道有哪些工具可用，才能生成 tool_calls

**文件**: `agents/core/tool_registry.py`

**核心功能**:
- 工具注册（函数 + Schema）
- 自动生成 OpenAI function calling 格式
- 工具调用执行
- 结果返回

**实现要点**:
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
        """生成 OpenAI function calling 格式"""
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
        result = await func(**args) if asyncio.iscoroutinefunction(func) else func(**args)
        return result
```

**工具注册示例**:
```python
# 注册题库工具
registry.register(
    func=get_random_question,
    name='get_random_question',
    description='从题库中随机获取一道题目',
    parameters={
        'type': 'object',
        'properties': {
            'module': {
                'type': 'string',
                'description': '模块名称，如"Java基础"、"JVM"等，不传则随机'
            }
        }
    }
)

registry.register(
    func=evaluate_answer,
    name='evaluate_answer',
    description='评估用户回答并打分',
    parameters={
        'type': 'object',
        'properties': {
            'question_id': {'type': 'string', 'description': '题目ID'},
            'user_answer': {'type': 'string', 'description': '用户的回答'},
            'scores': {
                'type': 'object',
                'description': '各维度评分（0-5）',
                'properties': {
                    'accuracy': {'type': 'number'},
                    'completeness': {'type': 'number'},
                    'depth': {'type': 'number'},
                    'scenario': {'type': 'number'}
                }
            }
        },
        'required': ['question_id', 'user_answer', 'scores']
    }
)
```

---

##### 2. Agent Loop (TAOR 闭环) - 2小时 ⭐⭐⭐⭐⭐

> **核心**: Think → Act → Observe → Reflect 循环

**文件**: `agents/core/agent_loop.py`

**核心功能**:
- TAOR 四步循环
- 状态机管理（IDLE, THINKING, EXECUTING, OBSERVING）
- 退出条件控制
- 消息历史管理

**实现要点**:
```python
class AgentLoop:
    def __init__(self, agent, tool_registry, max_rounds=30):
        self.agent = agent
        self.tool_registry = tool_registry
        self.max_rounds = max_rounds
        self.round = 0
        self.messages = []
        self.state = 'IDLE'
    
    async def run(self, user_input: str):
        """运行 TAOR 循环"""
        self.messages.append({'role': 'user', 'content': user_input})
        
        while self.round < self.max_rounds:
            self.round += 1
            
            # 1. Think: 调用 LLM（传入工具 schema）
            self.state = 'THINKING'
            response = await self.agent.llm_client.chat.completions.create(
                model=self.agent.config['llm']['model'],
                messages=[
                    {'role': 'system', 'content': self.agent.system_prompt}
                ] + self.messages,
                tools=self.tool_registry.get_tool_schemas()  # ← 关键
            )
            
            message = response.choices[0].message
            
            # 2. Act: 如果有 tool_calls
            if message.tool_calls:
                self.state = 'EXECUTING'
                
                # 添加 assistant 消息
                self.messages.append({
                    'role': 'assistant',
                    'content': message.content,
                    'tool_calls': [
                        {
                            'id': tc.id,
                            'type': 'function',
                            'function': {
                                'name': tc.function.name,
                                'arguments': tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                })
                
                # 3. Observe: 执行工具并收集结果
                self.state = 'OBSERVING'
                for tool_call in message.tool_calls:
                    result = await self.tool_registry.execute_tool(tool_call)
                    
                    self.messages.append({
                        'role': 'tool',
                        'tool_call_id': tool_call.id,
                        'content': json.dumps(result, ensure_ascii=False)
                    })
            else:
                # 4. Reflect: 没有 tool_calls，返回最终答案
                return message.content
        
        return f"已达到最大轮次（{self.max_rounds}），任务未完成"
    
    def should_exit(self):
        """退出条件"""
        return self.round >= self.max_rounds
```

---

##### 3. 上下文管理 (Context Manager) - 1小时 ⭐⭐⭐⭐

> **目的**: 防止长对话超出 Context Window

**文件**: `agents/core/context_manager.py`

**核心功能**:
- Token 统计（使用 tiktoken）
- 阈值监控（92%）
- 自动压缩（保留最近对话 + 早期摘要）

**实现要点**:
```python
import tiktoken

class ContextManager:
    def __init__(
        self,
        max_tokens=128000,
        threshold=0.92,
        model="deepseek-chat",
    ):
        self.max_tokens = max_tokens
        self.threshold = threshold
        self.encoding = tiktoken.encoding_for_model(model)
    
    def count_tokens(self, messages):
        """统计消息 Token 数"""
        total = 0
        for msg in messages:
            content = str(msg.get('content', ''))
            total += len(self.encoding.encode(content))
        return total
    
    def should_compress(self, messages):
        """判断是否需要压缩"""
        current = self.count_tokens(messages)
        usage_rate = current / self.max_tokens
        return usage_rate > self.threshold
    
    async def compress_if_needed(self, messages, llm_client):
        """检查并压缩"""
        if not self.should_compress(messages):
            return messages
        
        print(f"⚠️  上下文使用率超过 {self.threshold*100}%，触发压缩...")
        return await self.compress(messages, llm_client)
    
    async def compress(self, messages, llm_client):
        """压缩：保留最近10轮，早期对话LLM摘要"""
        if len(messages) <= 20:
            return messages
        
        # 保留最近10轮（20条消息）
        recent = messages[-20:]
        old = messages[:-20]
        
        # LLM 摘要早期对话
        summary_prompt = f"""请将以下对话总结为简短摘要（200字以内）：

{json.dumps(old, ensure_ascii=False)}

摘要："""
        
        summary_response = await llm_client.chat.completions.create(
            model=llm_config.get("model", "deepseek-chat"),
            messages=[{'role': 'user', 'content': summary_prompt}],
            max_tokens=500
        )
        
        summary = summary_response.choices[0].message.content
        
        # 构建压缩后的消息
        compressed = [
            {'role': 'system', 'content': f'[早期对话摘要] {summary}'}
        ] + recent
        
        old_tokens = self.count_tokens(messages)
        new_tokens = self.count_tokens(compressed)
        print(f"✅ 压缩完成：{old_tokens} → {new_tokens} tokens（节省 {old_tokens - new_tokens}）")
        
        return compressed
```

---

#### 可选优化（P1 - 后期补充）

##### 4. 重试机制 - 0.5小时

**文件**: `agents/core/retry_handler.py`

**功能**: 网络抖动、API 限流自动重试

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=30)
)
async def call_llm_with_retry(self, messages, tools):
    """带重试的 LLM 调用"""
    return await self.llm_client.chat.completions.create(
        model=self.model,
        messages=messages,
        tools=tools
    )
```

##### 5. 并行工具执行 - 1小时

**功能**: 多个工具并行执行（性能优化）

```python
async def execute_tools_parallel(self, tool_calls):
    """并行执行多个工具"""
    tasks = [
        asyncio.create_task(self.tool_registry.execute_tool(call))
        for call in tool_calls
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

---

#### 明确不需要的部分（避免过度设计）

根据面试助手场景，以下功能**不需要实现**：

- ❌ **Checkpoint** - 面试不会中断很久
- ❌ **SubAgent 委派** - 单一面试官足够
- ❌ **DAG 工作流** - 面试是线性流程
- ❌ **Agent Teams / Swarm** - 6个Agent是协作，不是对等通信
- ❌ **Plan & Execute** - 不需要复杂规划
- ❌ **Git Worktree 沙箱** - 不修改代码
- ❌ **Bash AST 解析** - 不执行命令

---

#### 验证测试

**测试脚本**: `scripts/test_agent_loop.py`

```python
#!/usr/bin/env python3
"""测试 Agent Loop 核心功能"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from agents.core.base_agent import Agent
from agents.core.tool_registry import ToolRegistry
from agents.core.agent_loop import AgentLoop
from agents.core.context_manager import ContextManager

# 注册测试工具
def mock_tool(arg: str):
    return f"Tool executed with: {arg}"

async def test_tool_registry():
    """测试工具注册"""
    print("测试 1: 工具注册系统")
    
    registry = ToolRegistry()
    registry.register(
        func=mock_tool,
        name='test_tool',
        description='测试工具',
        parameters={'type': 'object', 'properties': {'arg': {'type': 'string'}}}
    )
    
    schemas = registry.get_tool_schemas()
    assert len(schemas) == 1
    assert schemas[0]['function']['name'] == 'test_tool'
    print("✅ 通过\n")

async def test_agent_loop():
    """测试 Agent Loop"""
    print("测试 2: Agent Loop 基础循环")
    
    agent = Agent('test')
    registry = ToolRegistry()
    loop = AgentLoop(agent, registry, max_rounds=5)
    
    result = await loop.run("你好")
    print(f"结果: {result[:50]}...")
    assert loop.round <= 5
    print("✅ 通过\n")

async def test_context_manager():
    """测试上下文管理"""
    print("测试 3: 上下文管理")
    
    manager = ContextManager(max_tokens=1000, threshold=0.5)
    messages = [{'role': 'user', 'content': 'test ' * 200}]
    
    tokens = manager.count_tokens(messages)
    should_compress = manager.should_compress(messages)
    
    print(f"Token 数: {tokens}")
    print(f"需要压缩: {should_compress}")
    print("✅ 通过\n")

if __name__ == '__main__':
    print("=" * 60)
    print("Agent Loop 核心测试")
    print("=" * 60 + "\n")
    
    asyncio.run(test_tool_registry())
    asyncio.run(test_agent_loop())
    asyncio.run(test_context_manager())
    
    print("=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)
```

**运行测试**:
```bash
python scripts/test_agent_loop.py
```

---

**完成标志**:
- [ ] 工具注册系统实现完成
- [ ] Agent Loop 能正常循环
- [ ] 上下文管理能统计和压缩
- [ ] 所有单元测试通过

**完成后**：系统具备完整的执行引擎，可以开始 Phase 1（面试官 Agent）

---

### Phase 1: 面试官 Agent（MVP 核心）

**耗时**: 2-3 小时

#### 1.1 实现面试官 Agent (1小时)

**文件**: `agents/roles/interviewer_agent.py`

**功能需求**:
- 从薄弱模块中选题
- 评估答案（4个维度打分）
- 追问逻辑（最多2次）
- 生成反馈报告
- 更新学习记录

**核心方法**:
```python
class InterviewerAgent(Agent):
    def start_interview(self, mode='weak_module') -> Question
    def evaluate_answer(self, question_id, user_answer) -> EvaluationResult
    def decide_follow_up(self, evaluation) -> Optional[str]
    def generate_feedback(self, evaluation) -> str
    def save_record(self, question_id, evaluation, session_id)
```

**依赖工具**:
- `question_tools.get_random_question()`
- `memory_tools.add_learning_record()`
- `memory_tools.calculate_next_review()`

#### 1.2 题库导入脚本 (30分钟)

**文件**: `scripts/import_questions.py`

**功能**: 将 1346 道题目信息批量导入 `question_metadata` 表

**逻辑**:
```python
1. 遍历 Java八股文/ 下所有 .md 文件
2. 解析题目信息（ID、模块、标题）
3. 批量插入 question_metadata 表
4. 初始化 mastery_level = '⚪'
```

#### 1.3 命令行界面 (30分钟)

**文件**: `scripts/cli_interface.py`

**功能**: 简单的命令行交互界面

**示例流程**:
```
=== AI 面试陪练系统 ===

1. 🎯 开始面试（随机抽题）
2. ⏰ 复习模式（待复习题目）
3. 📊 查看统计
4. 🚪 退出

请选择: 1

[面试官] 正在从你的薄弱模块"分布式"中抽题...
[面试官] 请解释 CAP 定理的含义和应用场景。

你的回答: [用户输入]

[面试官] 评分中...

## 评分结果
- 准确性: 4/5
- 完整性: 3/5
...
```

**实现要点**:
- 简单的菜单循环
- 调用 `InterviewerAgent`
- 实时显示反馈

#### 1.4 验证测试 (30分钟)

**测试清单**:
- [ ] 导入 1346 道题到数据库
- [ ] 随机抽题能正常工作
- [ ] 评分逻辑准确
- [ ] 学习记录能保存
- [ ] 复习时间能计算

---

### Phase 2: FastAPI 服务器

**耗时**: 2-3 小时

#### 2.1 基础 API 服务器 (1.5小时)

**文件**: `scripts/harness_server.py`

**核心接口**:

```python
# 会话管理
POST   /api/session/create       # 创建会话
GET    /api/session/{id}         # 获取会话信息
DELETE /api/session/{id}         # 结束会话

# 面试流程
POST   /api/interview/start      # 开始面试
POST   /api/interview/answer     # 提交答案
GET    /api/interview/feedback   # 获取反馈

# 统计查询
GET    /api/stats/overview       # 总体统计
GET    /api/stats/weak-modules   # 薄弱模块
GET    /api/stats/due-reviews    # 待复习题目

# 题目查询
GET    /api/questions/random     # 随机题目
GET    /api/questions/{id}       # 指定题目
GET    /api/questions/search     # 搜索题目
```

**技术选型**:
```python
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
```

#### 2.2 WebSocket 支持 (1小时)

**文件**: 同上

**功能**: 实时流式返回 AI 回复

**端点**: `ws://localhost:8000/ws/interview`

**消息格式**:
```json
// Client -> Server
{
  "type": "submit_answer",
  "question_id": "HashMap底层原理",
  "answer": "..."
}

// Server -> Client (流式)
{
  "type": "evaluation_chunk",
  "content": "评分中..."
}
{
  "type": "evaluation_complete",
  "scores": {...}
}
```

#### 2.3 测试 API (30分钟)

**工具**: Postman / curl

**测试用例**:
```bash
# 创建会话
curl -X POST http://localhost:8000/api/session/create

# 开始面试
curl -X POST http://localhost:8000/api/interview/start \
  -H "Content-Type: application/json" \
  -d '{"mode": "random"}'

# 查看统计
curl http://localhost:8000/api/stats/overview
```

---

### Phase 3: 其余 5 个 Agent

**耗时**: 4-5 小时

#### 3.1 复习调度器 Agent (1小时)

**文件**: `agents/roles/scheduler_agent.py`

**当前状态**: 已实现最小业务能力：生成每日复习清单、调用 SM-2 更新下次复习时间、通过 `process()` 路由调度动作。

**核心算法**: SuperMemo SM-2

**功能**:
- 计算下次复习时间
- 生成每日复习清单
- 优先级排序

**关键代码**:
```python
def calculate_next_review(self, question_id, performance):
    """SM-2 算法实现"""
    # 见 memory_tools.py 已有实现
```

#### 3.2 监督助手 Agent (1小时)

**文件**: `agents/roles/supervisor_agent.py`

**功能**:
- 生成学习报告（日报、周报）
- 分析学习趋势
- 识别薄弱环节
- 制定学习计划

**输出格式**: Markdown 报告保存到 `学习记录/周报/`

#### 3.3 知识关联器 Agent (1.5小时)

**文件**: `agents/roles/linker_agent.py`  
**工具**: `agents/tools/linker_tools.py`

**功能**:
- 基于 TF-IDF 计算题目相似度
- 构建知识图谱（题目作为节点）
- 推荐相关题目

**技术方案**:
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def find_related_questions(question_id, top_k=5):
    """计算相似题目"""
    # 1. 获取所有题目的文本
    # 2. TF-IDF 向量化
    # 3. 余弦相似度
    # 4. 返回 top_k 相关题
```

#### 3.4 错题分析师 Agent (30分钟)

**文件**: `agents/roles/analyzer_agent.py`

**功能**:
- 分析错误原因（概念混淆/细节遗漏/场景不足/前置缺失）
- 生成对比表
- 推荐补救题目

#### 3.5 陪练伙伴 Agent (30分钟)

**文件**: `agents/roles/buddy_agent.py`

**功能**:
- 友好鼓励
- 提示（3级渐进）
- 通俗解释
- 学习技巧

---

### Phase 4: 多 Agent 编排

**耗时**: 2小时

#### 4.1 Agent 编排器 (1.5小时)

**文件**: `scripts/multi_agent_orchestrator.py`

**架构**:
```python
class AgentOrchestrator:
    def __init__(self):
        self.agents = {
            'interviewer': InterviewerAgent(),
            'supervisor': SupervisorAgent(),
            'scheduler': SchedulerAgent(),
            'linker': LinkerAgent(),
            'analyzer': AnalyzerAgent(),
            'buddy': BuddyAgent()
        }
        self.message_bus = MessageBus()

    def route_task(self, task_type, input_data):
        """将任务路由到对应的 Agent"""
        ...

    def coordinate_agents(self, primary_agent, assisting_agents):
        """协调多个 Agent 协作"""
        ...
```

**消息总线**:
```python
class MessageBus:
    """Agent 之间的通信"""
    def publish(self, from_agent, to_agent, message)
    def subscribe(self, agent, handler)
```

#### 4.2 集成测试 (30分钟)

**场景**: 完整的面试流程

```
1. 用户启动面试
2. Scheduler 推荐待复习题
3. Interviewer 抽题并评估
4. Analyzer 分析错误（如果答错）
5. Linker 推荐相关题
6. Buddy 给予鼓励
7. Supervisor 更新统计
```

---

### Phase 5: Web UI 前端

**耗时**: 5-6 小时

#### 5.1 项目初始化 (30分钟)

```bash
cd web_ui
npm create vite@latest . -- --template react-ts
npm install
npm install antd @ant-design/icons axios zustand
npm install echarts recharts
```

#### 5.2 核心页面 (3小时)

**页面结构**:
```
src/
├── pages/
│   ├── Dashboard.tsx          # 仪表盘
│   ├── Interview.tsx          # 面试界面
│   ├── Review.tsx             # 复习模式
│   └── Stats.tsx              # 统计分析
├── components/
│   ├── QuestionCard.tsx       # 题目卡片
│   ├── ScoreDisplay.tsx       # 评分显示
│   ├── ProgressChart.tsx      # 进度图表
│   └── AgentAvatar.tsx        # Agent 头像
└── api/
    └── harness-api.ts         # API 客户端
```

#### 5.3 实时对话 (1.5小时)

**技术**: WebSocket

```typescript
const ws = new WebSocket('ws://localhost:8000/ws/interview');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'evaluation_chunk') {
    // 流式显示 AI 回复
    appendToResponse(data.content);
  }
};
```

#### 5.4 数据可视化 (1小时)

**图表**:
- 掌握率雷达图（各模块）
- 学习趋势折线图
- 评分分布饼图

**库**: ECharts 或 Recharts

---

### Phase 6: Obsidian 集成

**耗时**: 2-3 小时

#### 6.1 Obsidian 工具 (1小时)

**文件**: `agents/tools/obsidian_tools.py`

**功能**:
- 自动生成学习记录笔记
- 更新仪表盘数据
- 生成周报

**示例**:
```python
def create_session_note(session_data):
    """将会话保存为 Markdown 笔记"""
    note_path = ROOT_DIR / "学习记录" / "每日对话" / f"{date}-面试练习.md"
    
    content = f"""---
date: {date}
agent: interviewer
questions: {len(session_data['questions'])}
avg_score: {session_data['avg_score']}
---

# {date} 面试练习

## 题目列表
{generate_question_list(session_data)}

## 详细记录
{generate_detailed_log(session_data)}
"""
    
    with open(note_path, 'w', encoding='utf-8') as f:
        f.write(content)
```

#### 6.2 ChatGPT MD 插件配置 (1小时)

**步骤**:
1. 在 Obsidian 中安装 ChatGPT MD 插件
2. 配置自定义 API endpoint: `http://localhost:8000/api/chat`
3. 实现兼容接口

**兼容接口**:
```python
@app.post("/api/chat")
async def chat_compatible(request: ChatRequest):
    """
    OpenAI 兼容接口，供 ChatGPT MD 调用
    """
    # 将请求转发给 Agent Orchestrator
    response = orchestrator.route_task('chat', request)
    return OpenAIResponse(...)
```

#### 6.3 自定义插件开发 (可选，后续)

**如果时间充足，可以开发专用插件**:
- 侧边栏显示 Agent 面板
- 快捷命令（Cmd+Shift+I 开始面试）
- 题目悬停预览

---

### Phase 7: 测试和优化

**耗时**: 2小时

#### 7.1 端到端测试 (1小时)

**测试场景**:
1. 新用户首次使用
2. 完整面试流程（10题）
3. 复习模式
4. 错误分析
5. 周报生成

**测试工具**: Pytest

#### 7.2 性能优化 (30分钟)

**优化点**:
- 数据库索引
- LLM 调用缓存
- 前端懒加载

#### 7.3 文档完善 (30分钟)

**文档**:
- 用户手册（README.md）
- API 文档
- 部署指南

---

## 🚀 部署方案

### 本地部署（推荐）

#### 一键启动脚本

**Windows**: `start.bat`
```bat
@echo off
echo Starting AI Interview Harness...

REM 启动后端
start /B python scripts/harness_server.py

REM 等待后端启动
timeout /t 3

REM 启动前端
cd web_ui
start /B npm run dev

REM 打开浏览器
timeout /t 2
start http://localhost:5173

echo System started!
pause
```

**Linux/Mac**: `start.sh`
```bash
#!/bin/bash
echo "Starting AI Interview Harness..."

# 启动后端
python scripts/harness_server.py &

# 等待后端启动
sleep 3

# 启动前端
cd web_ui && npm run dev &

# 打开浏览器
sleep 2
open http://localhost:5173

echo "System started!"
```

### 环境要求

```
Python: >= 3.9
Node.js: >= 18.0
内存: >= 4GB
磁盘: >= 500MB
```

---

## 📊 里程碑检查

### Milestone 1: MVP 可用 ✅

**完成标志**:
- [x] 数据库初始化成功
- [x] 能导入 1346 道题
- [ ] 命令行能完成一次面试
- [ ] 评分和记录能保存

**验证方式**:
```bash
python scripts/cli_interface.py
# 完成一次完整面试流程
```

### Milestone 2: API 服务就绪

**完成标志**:
- [x] FastAPI 服务器能启动
- [x] 基础 REST API 正常工作（会话、统计、题目查询）
- [x] WebSocket 连接稳定（协议骨架已实现，真实 LLM 流式评分待接入）

**验证方式**:
```bash
curl http://localhost:8000/api/stats/overview
# 返回统计数据
```

### Milestone 3: 多 Agent 协作

**完成标志**:
- [ ] 6 个 Agent 全部实现
- [ ] Agent 编排器能协调工作
- [ ] 消息总线通信正常

**验证方式**:
- 日志中能看到 Agent 之间的通信记录

### Milestone 4: Web UI 完成

**完成标志**:
- [ ] 所有页面能正常访问
- [ ] 实时对话流畅
- [ ] 图表显示正确

**验证方式**:
- 在浏览器中完成一次完整流程

### Milestone 5: Obsidian 集成

**完成标志**:
- [ ] 学习记录自动保存为 Markdown
- [ ] 仪表盘数据自动更新
- [ ] ChatGPT MD 插件能调用

**验证方式**:
- 在 Obsidian 中查看自动生成的笔记

---

## 🐛 常见问题和解决方案

### 问题 1: LLM API 调用失败

**症状**: 网络错误、超时

**解决**:
```python
# 添加重试机制
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def call_llm_with_retry(self, message):
    return self.llm_client.chat.completions.create(...)
```

### 问题 2: 数据库锁定

**症状**: `database is locked`

**解决**:
```python
# 使用连接池
import sqlalchemy
engine = sqlalchemy.create_engine(
    'sqlite:///learning.db',
    connect_args={'timeout': 15}
)
```

### 问题 3: 中文编码问题

**症状**: Windows 下中文乱码

**解决**:
```python
# 所有文件开头加上
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

### 问题 4: Web UI CORS 错误

**症状**: 前端无法访问后端 API

**解决**:
```python
# harness_server.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📚 参考资料

### 核心理论
- [Agent Harness 开发指导手册](https://github.com/holny/Agent-Harness-Develop-Book)
- [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [OpenAI: Harness Engineering](https://openai.com/zh-Hans-CN/index/harness-engineering/)

### 技术文档
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [React 官方文档](https://react.dev/)
- [Obsidian Plugin API](https://docs.obsidian.md/)
- [SuperMemo SM-2 算法](https://www.supermemo.com/en/archives1990-2015/english/ol/sm2)

---

## ✅ 下一步行动

### 立即可做

1. **安装 Python 依赖**
```bash
cd D:\ajie\study\AI-Knowledge
pip install -r requirements.txt
```

2. **导入题库到数据库**
```bash
python scripts/import_questions.py
```

3. **开始实现面试官 Agent**
   - 参考 `agents/core/base_agent.py`
   - 参考 `agents/definitions/interviewer.md`

### 建议顺序

**Week 1**: Phase 1-2（MVP + API 服务器）
**Week 2**: Phase 3-4（其余 Agent + 编排）
**Week 3**: Phase 5（Web UI）
**Week 4**: Phase 6-7（Obsidian + 测试优化）

---

## 🎉 结语

这份计划提供了完整的实施路线图。你可以：

1. **按计划逐步实现** - 每个 Phase 都是独立的
2. **交给其他 AI 继续** - 把这份计划给其他 AI，它可以接着做
3. **自己动手实现** - 所有技术细节都已说明

**核心原则**：
- 先做 MVP，快速验证
- 分阶段交付，持续迭代
- 保持代码简洁，避免过度设计

祝你成功！🚀

---

**文档维护**: 每完成一个阶段，更新对应的 ✅ 标记
