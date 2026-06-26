#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""复习调度器 Agent。

当前文件先提供标准角色入口，后续会在这里接入 SM-2 复习计划、到期题目
排序和每日复习清单生成逻辑。
"""

from __future__ import annotations

from typing import Any, Optional

from agents.core.base_agent import Agent


class SchedulerAgent(Agent):
    """复习调度器：负责复习时间和优先级规划。"""

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        # 目前先继承 Agent 的通用能力：配置、Prompt、LLM 客户端。
        # 后续真正实现调度算法时，只需要在这个类里继续加方法。
        super().__init__("scheduler", config)

    def process(self, input_data: Any) -> Any:
        """预留同步入口；具体调度逻辑在后续阶段实现。"""
        raise NotImplementedError("SchedulerAgent 的业务逻辑尚未实现")
