# Agents 项目结构说明

这个目录是 AI 面试陪练系统的正式代码入口。以后新增 Agent、工具或核心能力，
都放在这里，避免把代码分散到 `.harness/` 这样的配置目录里。

## 目录分层

```text
agents/
├── core/          # 通用执行引擎
├── roles/         # 具体 Agent 角色
├── tools/         # Agent 可调用工具
└── definitions/   # Agent 角色定义文档
```

## 每层放什么

- `core/`：放所有 Agent 都会用到的基础能力，例如 `AgentLoop`、`ToolRegistry`、
  `ContextManager`、`Agent` 基类。
- `roles/`：放具体角色实现，例如面试官 Agent。一个角色一个文件，避免所有逻辑
  堆在同一个模块里。
- `tools/`：放可被 LLM 调用的工具函数，例如题库查询、学习记录、复习计划。
- `definitions/`：放 Markdown 形式的角色说明、职责边界、协作规则。

## 新手读代码顺序

如果你有 Java 基础但刚开始学 Python，建议按“业务先行”的顺序读：

```text
1. roles/interviewer_agent.py   先看面试官怎么把工具和循环组装起来
2. tools/question_tools.py      再看题库文件怎么被读取成 Question 对象
3. tools/memory_tools.py        再看学习记录怎么写入数据库
4. core/agent_loop.py           最后看 TAOR 循环如何驱动 LLM 和工具
5. core/tool_registry.py        理解 LLM 返回 tool_call 后怎么执行 Python 函数
```

不要一开始就陷进所有语法细节。先问这段代码在流程中负责哪一步，再看 Python 写法。

## Java 类比

```text
roles/        类似业务 Service，定义“这个 Agent 做什么”
tools/        类似 Repository / Utility，真正读文件或写数据库
core/         类似框架层，提供循环、工具路由、上下文管理
definitions/  类似配置化的角色说明，但它影响 LLM 行为
```

`ToolRegistry` 可以理解成 `Map<String, Function>`：LLM 给出工具名，注册表找到对应函数并执行。

## 推荐导入方式

```python
from agents.roles.interviewer_agent import InterviewerAgent
from agents.core.agent_loop import AgentLoop
from agents.tools import memory_tools
```

`.harness/` 现在只保留配置、数据库和记忆文件。新开发时请只从 `agents/`
导入代码。
