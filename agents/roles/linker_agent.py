#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识关联器 Agent。

当前文件先提供标准角色入口，后续会在这里接入关键词抽取、相似度计算和
知识图谱构建逻辑。
"""

from __future__ import annotations

from typing import Any, Optional

from agents.core.base_agent import Agent


class LinkerAgent(Agent):
    """知识关联器：负责发现题目之间的关系。"""

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        # 先保留标准 Agent 骨架，方便未来接入向量检索或知识图谱工具。
        super().__init__("linker", config)

    def process(self, input_data: Any) -> Any:
        """预留同步入口；具体关联逻辑在后续阶段实现。"""
        raise NotImplementedError("LinkerAgent 的业务逻辑尚未实现")
