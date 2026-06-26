#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agent 基类：统一加载配置、Prompt 和 LLM 客户端。

具体的面试官、复习调度器等 Agent 都可以继承这个类。它只提供公共能力：
- 读取 `.harness/config/harness.yaml`
- 优先读取 `agents/definitions/{agent_name}.md`
- 创建 OpenAI 兼容客户端
- 保存简单的短期对话历史
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:  # pragma: no cover - 只在缺少 PyYAML 的环境触发。
    yaml = None


ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / ".harness" / "config" / "harness.yaml"

DEFAULT_LLM_CONFIG: Dict[str, Any] = {
    "provider": "deepseek",
    "model": "deepseek-chat",
    "model_env": "DEEPSEEK_MODEL",
    "temperature": 0.7,
    "max_tokens": 2000,
    "api_key": None,
    "api_key_env": "DEEPSEEK_API_KEY",
    "base_url": "https://api.deepseek.com",
    "base_url_env": "DEEPSEEK_BASE_URL",
}

DEFAULT_CONFIG: Dict[str, Any] = {
    "llm": dict(DEFAULT_LLM_CONFIG),
}


class _MissingLLMClient:
    """OpenAI SDK 不可用时的占位客户端。

    这样导入和单元测试不会因为本地没有安装 openai 包而失败。真正调用
    LLM 时会抛出清晰错误，提醒安装依赖或注入假的测试客户端。
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        self.chat = self
        self.completions = self

    def create(self, *_: Any, **__: Any) -> Any:
        raise RuntimeError(f"LLM 客户端不可用: {self.reason}")


@dataclass
class AgentResponse:
    """Agent 返回值的简单包装。"""

    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转成普通 dict，方便 JSON 序列化。"""
        return {
            "content": self.content,
            "metadata": self.metadata,
        }


class Agent:
    """所有 Agent 的基础类。"""

    def __init__(
        self,
        agent_name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.agent_name = agent_name
        self.config = self._merge_config(config or self.load_config())
        self.system_prompt = self.load_system_prompt()
        self.llm_client = self._init_llm_client()

        # 短期记忆：只保存当前进程内的对话历史。
        self.conversation_history: list[Dict[str, str]] = []

    def load_config(self) -> Dict[str, Any]:
        """加载主配置文件；失败时返回默认配置。"""
        if yaml is None or not CONFIG_PATH.exists():
            return dict(DEFAULT_CONFIG)

        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as file:
                loaded = yaml.safe_load(file) or {}
        except Exception:
            return dict(DEFAULT_CONFIG)

        return loaded if isinstance(loaded, dict) else dict(DEFAULT_CONFIG)

    def load_system_prompt(self) -> str:
        """加载当前 Agent 的 system prompt。"""
        agent_config = {}
        agents_config = self.config.get("agents", {})
        if isinstance(agents_config, dict):
            agent_config = agents_config.get(self.agent_name, {}) or {}

        # 先尊重配置文件；找不到时再回退到标准 agents/definitions 目录。
        prompt_candidates = []
        configured_prompt = agent_config.get("prompt_template")
        if configured_prompt:
            prompt_candidates.append(ROOT_DIR / str(configured_prompt))

        prompt_candidates.extend(
            [
                ROOT_DIR
                / "agents"
                / "definitions"
                / f"{self.agent_name}.md",
            ]
        )

        for prompt_file in prompt_candidates:
            if prompt_file.exists():
                return prompt_file.read_text(encoding="utf-8")

        return f"你是一个名为 {self.agent_name} 的 AI 面试助手。"

    def add_message(self, role: str, content: str) -> None:
        """把一条消息加入短期历史。"""
        self.conversation_history.append(
            {
                "role": role,
                "content": content,
            }
        )

    def clear_history(self) -> None:
        """清空短期对话历史。"""
        self.conversation_history = []

    def call_llm(
        self,
        user_message: str,
        temperature: Optional[float] = None,
    ) -> str:
        """进行一次普通 LLM 调用，不包含工具循环。

        复杂的多轮工具调用应使用 `AgentLoop`；这个方法保留给简单问答和
        兼容旧代码使用。
        """
        self.add_message("user", user_message)
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.conversation_history,
        ]
        llm_config = self.config.get("llm", {})

        response = self.llm_client.chat.completions.create(
            model=llm_config.get("model") or DEFAULT_LLM_CONFIG["model"],
            messages=messages,
            temperature=temperature or llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 2000),
        )
        assistant_message = self._extract_content(response)
        self.add_message("assistant", assistant_message)
        return assistant_message

    def process(self, input_data: Any) -> Any:
        """子类可以覆盖这个方法来实现自己的入口。"""
        raise NotImplementedError("子类需要实现 process()")

    def get_tool_call_prompt(self, tool_name: str, **kwargs: Any) -> str:
        """生成一段便于调试的工具调用文本。"""
        params = ", ".join(f"{key}={value}" for key, value in kwargs.items())
        return f"[调用工具] {tool_name}({params})"

    def _init_llm_client(self) -> Any:
        """创建 OpenAI 兼容客户端；失败时返回占位客户端。"""
        llm_config = self.config.get("llm", {})
        try:
            from openai import OpenAI
        except Exception as exc:
            return _MissingLLMClient(f"openai 包未安装或不可用: {exc}")

        try:
            return OpenAI(
                api_key=llm_config.get("api_key"),
                base_url=llm_config.get("base_url"),
            )
        except Exception as exc:
            return _MissingLLMClient(str(exc))

    @staticmethod
    def _extract_content(response: Any) -> str:
        """从 OpenAI 兼容响应中提取 assistant 文本。"""
        choices = getattr(response, "choices", None)
        if choices:
            message = getattr(choices[0], "message", None)
            return str(getattr(message, "content", "") or "")
        if isinstance(response, dict):
            choices = response.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                return str(message.get("content", "") or "")
        return str(response or "")

    @staticmethod
    def _merge_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """把配置文件与默认配置合并，避免缺字段时报错。"""
        merged = dict(DEFAULT_CONFIG)
        merged.update(config)
        merged["llm"] = {
            **DEFAULT_LLM_CONFIG,
            **(config.get("llm", {}) if isinstance(config, dict) else {}),
        }
        merged["llm"] = Agent._apply_llm_env_overrides(merged["llm"])
        return merged

    @staticmethod
    def _apply_llm_env_overrides(llm_config: Dict[str, Any]) -> Dict[str, Any]:
        """允许用环境变量覆盖 YAML 里的 LLM 配置。

        初学者可以这样理解：YAML 是默认设置，环境变量是“临时开关”。
        例如把 `DEEPSEEK_MODEL` 设为 `deepseek-reasoner` 后，代码不需要改，
        下次启动就会自动使用新模型。
        """
        resolved = dict(llm_config)
        env_fields = {
            "model": "model_env",
            "api_key": "api_key_env",
            "base_url": "base_url_env",
        }

        for target_key, env_key in env_fields.items():
            env_name = str(resolved.get(env_key) or "").strip()
            if not env_name:
                continue
            env_value = os.getenv(env_name)
            if env_value:
                resolved[target_key] = env_value

        # 配置写成 null 或空字符串时，回退到 DeepSeek 的默认可用值。
        if not resolved.get("model"):
            resolved["model"] = DEFAULT_LLM_CONFIG["model"]
        if not resolved.get("base_url"):
            resolved["base_url"] = DEFAULT_LLM_CONFIG["base_url"]

        return resolved
