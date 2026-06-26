#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""陪练伙伴 Agent。

当前文件先提供标准角色入口，后续会在这里接入分级提示、通俗解释和学习
节奏建议逻辑。
"""

from __future__ import annotations

from typing import Any, Optional

from agents.core.base_agent import Agent


class BuddyAgent(Agent):
    """陪练伙伴：负责提示、解释和学习陪伴。"""

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        # Buddy 以后会偏交互体验；目前先保持和其他 Agent 一致的入口。
        super().__init__("buddy", config)

    def process(self, input_data: Any) -> Any:
        """预留同步入口；具体陪练逻辑在后续阶段实现。"""
        raise NotImplementedError("BuddyAgent 的业务逻辑尚未实现")
