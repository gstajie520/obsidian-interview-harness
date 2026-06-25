"""兼容层：.harness.agents 转发到 agents.core 和 agents.roles

旧版代码可能会通过 `.harness.agents` 导入，这里提供转发。
正式实现位于根目录 `agents/` 包。
"""

from agents.core.agent_loop import AgentLoop, AgentState, DEFAULT_LLM_MODEL
from agents.core.base_agent import Agent
from agents.core.context_manager import ContextManager
from agents.core.tool_registry import ToolRegistry
from agents.roles.interviewer_agent import InterviewerAgent

__all__ = [
    "AgentLoop",
    "AgentState",
    "DEFAULT_LLM_MODEL",
    "Agent",
    "ContextManager",
    "ToolRegistry",
    "InterviewerAgent",
]
