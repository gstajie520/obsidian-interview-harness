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

## 推荐导入方式

```python
from agents.roles.interviewer_agent import InterviewerAgent
from agents.core.agent_loop import AgentLoop
from agents.tools import memory_tools
```

`.harness/` 现在只保留配置、数据库和记忆文件。新开发时请只从 `agents/`
导入代码。
