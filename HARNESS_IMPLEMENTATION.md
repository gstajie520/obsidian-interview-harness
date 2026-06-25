# 🎯 Agent Harness 完整实施路线图

> **文档版本**: 2.0  
> **创建日期**: 2025-06-25  
> **当前状态**: Phase 0.5 已完成核心组件  
> **下一步**: 实现面试官 Agent 并打通完整流程

---

## 📊 当前进度总结

### ✅ 已完成（Phase 0 + 0.5）

#### 基础设施
- ✅ 项目目录结构完整
- ✅ 配置文件系统（harness.yaml, knowledge_bases.yaml）
- ✅ MySQL Schema 设计（8张表）
- ✅ 知识库迁移（Java八股文 → 知识库/Java面试，1346题）
- ✅ 文档体系（CLAUDE.md, PLAN.md, AGENTS.md 等）

#### 核心 Harness 组件
- ✅ **Agent Loop** - TAOR 循环引擎（agent_loop.py）
- ✅ **Tool Registry** - 工具注册系统（tool_registry.py）
- ✅ **Context Manager** - 上下文管理与压缩（context_manager.py）
- ✅ **Agent Base** - Agent 基类（base_agent.py）

#### 工具层
- ✅ **题库工具** - question_tools.py（支持多知识库）
- ✅ **记忆工具** - memory_tools.py（MySQL 支持）

#### Prompt 系统
- ✅ **面试官 Prompt** - 详细的评分标准和追问策略（interviewer.md）

#### 备用脚本
- ✅ **interview_harness.py** - 完整的 CLI 工具（可作为参考）

---

## 🎯 实施目标

构建一个**生产级 Agent Harness 面试助手系统**：

### 核心价值
1. **多 Agent 协作** - 6个专业 Agent 各司其职
2. **持久记忆** - 三层记忆系统（短期/中期/长期）
3. **智能调度** - SM-2 遗忘曲线算法
4. **知识关联** - 自动发现题目之间的关联
5. **数据驱动** - 可视化进度，精准识别薄弱点

### 技术特色
- 原生 Agent Loop（深入理解 TAOR 原理）
- 可选 LangChain 集成（学习主流框架）
- MySQL 持久化（生产级数据管理）
- 通用知识库架构（可扩展到任何领域）

---

## 🚀 Phase 1: 面试官 Agent MVP（预计 4-5 小时）

**目标**: 打通完整的面试流程，实现第一个可用的 Agent

### 1.1 实现面试官 Agent（2h）

创建 `.harness/agents/interviewer_agent.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""面试官 Agent - 智能出题和评估"""

from .base_agent import Agent
from .agent_loop import AgentLoop
from .tool_registry import ToolRegistry
from .context_manager import ContextManager
from ..tools import question_tools, memory_tools

class InterviewerAgent(Agent):
    """面试官 Agent"""
    
    def __init__(self, config=None):
        super().__init__('interviewer', config)
        
        # 初始化工具注册表
        self.tool_registry = ToolRegistry()
        self._register_tools()
        
        # 初始化上下文管理器
        self.context_manager = ContextManager(
            max_tokens=128000,
            threshold=0.92,
            model=self.config['llm']['model']
        )
        
        # 初始化 Agent Loop
        self.agent_loop = AgentLoop(
            agent=self,
            tool_registry=self.tool_registry,
            max_rounds=30,
            context_manager=self.context_manager
        )
    
    def _register_tools(self):
        """注册面试官可用的工具"""
        
        @self.tool_registry.register(
            name="get_weak_modules",
            description="获取用户的薄弱模块列表"
        )
        def get_weak_modules(limit: int = 5):
            return memory_tools.get_weak_modules(limit)
        
        @self.tool_registry.register(
            name="get_question_from_module",
            description="从指定模块获取一道题目"
        )
        def get_question_from_module(module: str):
            q = question_tools.get_random_question(module=module)
            if q:
                return {
                    'question_id': q.question_id,
                    'title': q.title,
                    'module': q.module,
                    'content': q.content[:500]  # 不泄露完整答案
                }
            return {'error': '未找到题目'}
        
        @self.tool_registry.register(
            name="evaluate_answer",
            description="评估用户答案并保存记录"
        )
        def evaluate_answer(
            question_id: str,
            user_answer: str,
            score_accuracy: float,
            score_completeness: float,
            score_depth: float,
            score_scenario: float,
            weak_points: list = None
        ):
            scores = {
                'accuracy': score_accuracy,
                'completeness': score_completeness,
                'depth': score_depth,
                'scenario': score_scenario
            }
            
            # 保存学习记录
            record_id = memory_tools.add_learning_record(
                question_id=question_id,
                module='',  # 从 question_id 获取
                user_answer=user_answer,
                scores=scores,
                session_id='test-session',  # 待改进
                weak_points=weak_points or []
            )
            
            # 更新复习调度
            overall_score = sum(scores.values()) / len(scores)
            memory_tools.calculate_next_review(question_id, overall_score)
            
            return {'record_id': record_id, 'status': 'saved'}
    
    async def interview(self, user_input: str) -> str:
        """
        执行面试对话
        
        Args:
            user_input: 用户输入（答案或指令）
        
        Returns:
            面试官的回复
        """
        return await self.agent_loop.run(user_input)
    
    def process(self, input_data):
        """同步接口（兼容基类）"""
        import asyncio
        return asyncio.run(self.interview(input_data))
```

### 1.2 创建 CLI 界面（1.5h）

创建 `scripts/cli_interview.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""命令行面试界面"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from .harness.agents.interviewer_agent import InterviewerAgent

async def main():
    print("="*60)
    print("🎓 AI 面试陪练系统 - 命令行版")
    print("="*60)
    print()
    
    # 初始化面试官 Agent
    agent = InterviewerAgent()
    
    print("面试官已准备就绪！输入 'quit' 退出。\n")
    
    # 开始对话
    first_message = "你好！我准备开始面试了，请帮我选一道薄弱模块的题目。"
    response = await agent.interview(first_message)
    print(f"面试官: {response}\n")
    
    # 持续对话
    while True:
        try:
            user_input = input("你: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n面试结束！祝你面试顺利！")
                break
            
            if not user_input:
                continue
            
            response = await agent.interview(user_input)
            print(f"\n面试官: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\n面试被中断。")
            break
        except Exception as e:
            print(f"\n错误: {e}")
            break

if __name__ == '__main__':
    asyncio.run(main())
```

### 1.3 数据库初始化（0.5h）

更新 `scripts/init_database_mysql.py`，确保表结构完整。

### 1.4 题库导入脚本（1h）

创建 `scripts/import_questions.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导入题库到数据库"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from .harness.tools import question_tools, memory_tools

def import_knowledge_base(kb_name='java_interview'):
    """导入指定知识库"""
    
    print(f"开始导入知识库: {kb_name}")
    
    # 获取所有模块
    modules = question_tools.get_all_modules()
    print(f"发现 {len(modules)} 个模块")
    
    total_imported = 0
    
    for module in modules:
        questions = question_tools.get_questions_in_module(module)
        print(f"  {module}: {len(questions)} 道题")
        
        for file_path in questions:
            q = question_tools.parse_question_file(file_path)
            if q:
                # 初始化问题元数据
                memory_tools.init_question_metadata(
                    question_id=q.question_id,
                    file_path=q.file_path,
                    module=q.module,
                    title=q.title
                )
                total_imported += 1
    
    print(f"\n✅ 导入完成！共 {total_imported} 道题")

if __name__ == '__main__':
    import_knowledge_base()
```

---

## 🚀 Phase 2: 监督助手 Agent（预计 2-3 小时）

**目标**: 实现 Agent 协作，监督助手审核面试官的评分

### 2.1 Supervisor Agent（1.5h）

创建 `.harness/agents/supervisor_agent.py`：

```python
class SupervisorAgent(Agent):
    """监督助手 - 审核面试官的评分"""
    
    async def review_evaluation(self, question, user_answer, interviewer_scores):
        """审核评分是否合理"""
        pass
```

### 2.2 Agent 协作编排（1h）

创建 `scripts/multi_agent_orchestrator.py`：

```python
class InterviewOrchestrator:
    """多 Agent 编排器"""
    
    def __init__(self):
        self.interviewer = InterviewerAgent()
        self.supervisor = SupervisorAgent()
    
    async def conduct_interview(self):
        """编排面试流程"""
        # 1. 面试官提问
        # 2. 用户作答
        # 3. 面试官评分
        # 4. 监督助手审核
        # 5. 最终反馈
        pass
```

---

## 🚀 Phase 3: 复习调度 Agent（预计 2-3 小时）

**目标**: 实现 SM-2 智能复习调度

### 3.1 Scheduler Tools（1h）

创建 `.harness/tools/scheduler_tools.py`：

```python
def get_due_reviews(limit=20):
    """获取到期复习题目"""
    pass

def schedule_review_queue():
    """生成今日复习队列"""
    pass
```

### 3.2 Scheduler Agent（1.5h）

创建 `.harness/agents/scheduler_agent.py`：

```python
class SchedulerAgent(Agent):
    """复习调度器 - 基于 SM-2 算法"""
    
    async def generate_daily_plan(self):
        """生成今日学习计划"""
        pass
```

---

## 🚀 Phase 4: 知识关联 Agent（预计 3-4 小时）

**目标**: 自动发现题目之间的关联关系

### 4.1 向量化工具（1.5h）

创建 `.harness/tools/linker_tools.py`：

```python
import chromadb

def build_question_embeddings():
    """构建题目向量索引"""
    pass

def find_similar_questions(question_id, top_k=5):
    """查找相似题目"""
    pass
```

### 4.2 Linker Agent（1.5h）

创建 `.harness/agents/linker_agent.py`。

---

## 🚀 Phase 5: 错题分析 Agent（预计 2-3 小时）

**目标**: 深度分析错题，生成学习报告

### 5.1 Analyzer Agent（2h）

创建 `.harness/agents/analyzer_agent.py`。

---

## 🚀 Phase 6: 陪练伙伴 Agent（预计 2-3 小时）

**目标**: 每日总结和学习建议

### 6.1 Buddy Agent（2h）

创建 `.harness/agents/buddy_agent.py`。

---

## 🚀 Phase 7: FastAPI 服务器（预计 3-4 小时）

**目标**: 提供 REST API 和 WebSocket 接口

### 7.1 API 服务器（2h）

创建 `scripts/harness_server.py`：

```python
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Interview Harness")

@app.post("/api/interview/start")
async def start_interview():
    pass

@app.websocket("/ws/interview")
async def interview_websocket(websocket: WebSocket):
    pass
```

### 7.2 WebSocket 实时对话（1.5h）

实现实时面试对话。

---

## 🚀 Phase 8: Web UI（预计 8-10 小时）

**目标**: React 前端界面

### 8.1 前端脚手架（1h）

```bash
cd web_ui
npm create vite@latest . -- --template react-ts
npm install antd zustand axios echarts
```

### 8.2 核心组件（6h）

- 面试对话界面
- 进度仪表盘
- 错题本
- 知识图谱可视化

---

## 📈 优先级建议

### 🔥 立即实施（MVP）
1. ✅ Phase 1.1-1.3：面试官 Agent + CLI（今天完成）
2. Phase 1.4：题库导入
3. 测试完整流程

### 🎯 核心功能
4. Phase 2：监督助手 Agent
5. Phase 3：复习调度 Agent

### 🌟 高级功能
6. Phase 4：知识关联 Agent
7. Phase 5：错题分析 Agent
8. Phase 6：陪练伙伴 Agent

### 🎨 可视化
9. Phase 7：FastAPI 服务器
10. Phase 8：Web UI

---

## 🛠️ 快速开始（今天就能跑起来）

### Step 1: 安装依赖

```bash
pip install -r requirements.txt
```

### Step 2: 配置数据库

编辑 `.harness/config/harness.yaml`，修改 MySQL 密码：

```yaml
database:
  password: "your_actual_password"
```

### Step 3: 初始化数据库

```bash
python scripts/init_database_mysql.py
```

### Step 4: 导入题库

```bash
python scripts/import_questions.py
```

### Step 5: 开始面试

```bash
python scripts/cli_interview.py
```

---

## 📊 里程碑

### Milestone 1: MVP（今天）
- ✅ 核心 Harness 组件完成
- ⏳ 面试官 Agent 实现
- ⏳ CLI 界面可用
- ⏳ 数据库持久化

### Milestone 2: 多 Agent（本周）
- 6 个 Agent 全部实现
- Agent 协作流程打通

### Milestone 3: Web UI（下周）
- FastAPI 服务器
- React 前端
- 完整的可视化

---

## 🎯 成功标准

### Phase 1 完成标准
- [ ] 运行 CLI，能正常开始面试
- [ ] Agent 能调用工具获取题目
- [ ] 用户回答后，Agent 能给出评分
- [ ] 评分结果保存到数据库
- [ ] 能看到下一题

### 最终系统标准
- [ ] 6 个 Agent 全部正常工作
- [ ] 多 Agent 协作流程顺畅
- [ ] 数据持久化稳定
- [ ] Web UI 美观易用
- [ ] 学习数据可视化
- [ ] 智能复习调度有效

---

## 💡 技术亮点

1. **原生 Agent Loop** - 深入理解 TAOR 循环原理
2. **工具注册系统** - 灵活的函数调用机制
3. **上下文管理** - 自动压缩，防止超窗口
4. **多 Agent 协作** - 清晰的职责分工
5. **生产级持久化** - MySQL + 完整 Schema
6. **通用知识库** - 可扩展到任何领域

---

## 📚 参考资源

- **理论基础**: `Agent-Harness-Develop-Book/`
- **对比分析**: `COMPARISON_REPORT_V2.md`
- **Agent 设计**: `AGENTS.md`
- **详细计划**: `PLAN.md`
- **MySQL 配置**: `MYSQL_SETUP.md`
- **LangChain 集成**: `LANGCHAIN_INTEGRATION.md`

---

**开始构建吧！🚀**
