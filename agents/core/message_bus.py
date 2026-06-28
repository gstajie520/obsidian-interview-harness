#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agent 消息总线（最小实现）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, DefaultDict, Dict, List
from collections import defaultdict


MessageHandler = Callable[[dict[str, Any]], None]


@dataclass
class MessageBus:
    """用于记录和分发 Agent 之间的合作事件。

    这个总线先做“同步内存总线”：每次 publish 都立刻分发给订阅方，
    并且把事件放入 `events` 便于后续调试和回放。后续可替换为异步队列或
    外部消息中间件，不会影响调用方接口。
    """

    events: list[dict[str, Any]] = field(default_factory=list)
    _subscribers: DefaultDict[str, List[MessageHandler]] = field(
        default_factory=lambda: defaultdict(list),
    )

    def publish(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        """发布一条事件并通知订阅方。

        返回标准化的事件对象，方便链路里复用。
        """
        event = {
            "from_agent": str(from_agent),
            "to_agent": str(to_agent),
            "message_type": str(message_type),
            "payload": message,
        }
        self.events.append(event)
        self._notify(to_agent, event)
        return event

    def subscribe(self, agent_id: str, handler: MessageHandler) -> None:
        """订阅某个 agent 的事件。

        handler 的参数是事件 dict。为了和 Java 的监听器机制一致，
        这里允许一个 agent 有多个处理器。
        """
        self._subscribers[str(agent_id)].append(handler)

    def get_events(self) -> list[dict[str, Any]]:
        """返回事件快照，避免外部直接修改内部列表。"""
        return [dict(item) for item in self.events]

    def clear(self) -> None:
        """清空事件流和订阅关系。"""
        self.events = []
        self._subscribers.clear()

    def _notify(self, to_agent: str, event: dict[str, Any]) -> None:
        """同步通知订阅方；单个订阅异常不应阻断总线。"""
        for handler in list(self._subscribers.get(str(to_agent), [])):
            try:
                handler(event)
            except Exception:
                # 编排场景不应让某个订阅方崩掉全局流程。
                continue
