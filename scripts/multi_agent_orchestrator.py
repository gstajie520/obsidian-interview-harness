#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多 Agent 协作编排器。

这个文件把面试后处理链路做成“线性编排”：
1. SchedulerAgent：读到期复习并更新复习间隔。
2. AnalyzerAgent：按错题记录生成错因分析。
3. LinkerAgent：基于题目推荐相关题。
4. SupervisorAgent：给出日报/周报建议。
5. BuddyAgent：给出鼓励与状态反馈。

这里不直接在生产线上执行面试提问，面试动作仍由 InterviewerAgent 负责。
它的价值是：把“一个题目结束后要做哪些动作”固定成可复用流程。
后续消息总线（bus）可以直接用 `events` 字段接力，不改外部接口。
"""

from __future__ import annotations

from typing import Any, Optional

from agents.core import MessageBus
from agents.roles import (
    AnalyzerAgent,
    BuddyAgent,
    LinkerAgent,
    SchedulerAgent,
    SupervisorAgent,
)
from agents.tools import question_tools
from agents.tools import memory_tools


class MultiAgentOrchestrator:
    """多 Agent 编排器。

    类似 Java 中的流程编排 Service：每个子 Agent 负责一段业务，
    Orchestrator 负责把这些业务按顺序串起来并保留事件日志。
    """

    def __init__(
        self,
        config: Optional[dict[str, Any]] = None,
        message_bus: Optional[MessageBus] = None,
    ) -> None:
        agent_config = config or {}
        # 默认不走 LLM 的规则方法，保持 deterministic，方便测试。
        llm_cfg = agent_config.get("llm", {"model": "fake-model"})
        self.scheduler = SchedulerAgent(config={"llm": llm_cfg})
        self.analyzer = AnalyzerAgent(config={"llm": llm_cfg})
        self.linker = LinkerAgent(config={"llm": llm_cfg})
        self.supervisor = SupervisorAgent(config={"llm": llm_cfg})
        self.buddy = BuddyAgent(config={"llm": llm_cfg})

        self.message_bus = message_bus or MessageBus()

        self.linker_top_k = int(agent_config.get("linker_top_k", 5))

    def orchestrate_after_answer(
        self,
        record: dict[str, Any],
        include_report: bool = False,
        session_id: Optional[str] = None,
        record_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """执行一次答题后编排。

        返回值包含每个 Agent 的产出以及统一的 `events`。
        这样后续可以直接把 events 写入日志、数据库或消息总线。
        """
        self.message_bus.clear()
        events: list[dict[str, Any]] = []

        events.append(
            self._record_event(
                "orchestrator_start",
                "开始执行编排",
                {"question_id": self._question_id(record)},
            )
        )

        analysis = self._run_analyzer(record, events)
        schedule = self._run_scheduler(record, events)
        relations = self._run_linker(record, events)
        recommendation = self._run_supervisor(include_report, events)
        encouragement = self._run_buddy(record, analysis, events)
        run_id = self._persist_result(
            question_id=self._question_id(record),
            result={
                "status": "ok",
                "question_id": self._question_id(record),
                "analysis": analysis,
                "schedule": schedule,
                "relations": relations,
                "recommendation": recommendation,
                "encouragement": encouragement,
                "events": events,
            },
            session_id=session_id,
            record_id=record_id,
        )

        return {
            "status": "ok",
            "question_id": self._question_id(record),
            "analysis": analysis,
            "schedule": schedule,
            "relations": relations,
            "recommendation": recommendation,
            "encouragement": encouragement,
            "events": events,
            "run_id": run_id,
        }

    def _run_analyzer(
        self,
        record: dict[str, Any],
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """调用错题分析师，记录其是否成功。

        分析失败不应阻断整条链路；记录事件并返回可回退内容。
        """
        question_id = self._question_id(record)
        try:
            analysis = self.analyzer.analyze_wrong_answer(record)
            events.append(self._record_event("analyzer_done", "错题分析完成", analysis))
            self._publish_bus_event("analyzer", "linker", "response", analysis)
            return analysis
        except Exception as exc:
            fallback = {
                "status": "error",
                "question_id": question_id,
                "message": f"错题分析失败: {exc}",
            }
            events.append(
                self._record_event(
                    "analyzer_failed",
                    "错题分析失败",
                    fallback,
                )
            )
            self._publish_bus_event("analyzer", "orchestrator", "error", fallback)
            return fallback

    def _run_scheduler(
        self,
        record: dict[str, Any],
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """按表现更新复习间隔，并补充题目元数据状态。"""
        question_id = self._question_id(record)
        scores = self._to_scores(record)
        performance = self._performance_from_scores(scores)

        schedule = self.scheduler.schedule_next_review(
            question_id=question_id,
            performance=performance,
        )
        events.append(self._record_event("scheduler_done", "复习计划更新", schedule))
        self._publish_bus_event("scheduler", "linker", "response", schedule)
        return schedule

    def _run_linker(
        self,
        record: dict[str, Any],
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """基于当前题目查找候选题并做推荐。"""
        question = self._to_question_payload(record)
        candidates = self._load_all_questions()
        relations = self.linker.find_related_questions(
            question=question,
            candidates=candidates,
            top_k=self.linker_top_k,
        )
        events.append(self._record_event("linker_done", "知识关联完成", relations))
        self._publish_bus_event("linker", "supervisor", "response", relations)
        return relations

    def _run_supervisor(
        self,
        include_report: bool,
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """调用监督助手生成日报/周报。"""
        if include_report:
            recommendation = self.supervisor.generate_weekly_report(limit=3)
            events.append(self._record_event("supervisor_done", "生成周报", recommendation))
            self._publish_bus_event("supervisor", "buddy", "response", recommendation)
            return recommendation

        recommendation = self.supervisor.generate_daily_report(limit=3)
        events.append(self._record_event("supervisor_done", "生成日报", recommendation))
        self._publish_bus_event("supervisor", "buddy", "response", recommendation)
        return recommendation

    def _run_buddy(
        self,
        record: dict[str, Any],
        analysis: dict[str, Any],
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """给出鼓励和追问提示。

        评分高于 3 给鼓励，低于 3 给更高强度提示；
        同时建议是否需要休息。
        """
        scores = self._to_scores(record)
        overall = self._performance_from_scores(scores)

        hint_level = 1
        trigger = "default"
        if overall >= 3:
            trigger = "breakthrough"
            hint_level = 1
        elif overall >= 1:
            hint_level = 2
        else:
            hint_level = 3
        if (
            analysis.get("error_type") in {"detail_missing", "scenario_lack"}
            and overall < 3
        ):
            hint_level = 3

        result = {
            "status": "ok",
            "question_id": self._question_id(record),
            "encouragement": self.buddy.generate_encouragement(
                trigger=trigger,
                consecutive_success=int(self._consecutive_success(record)),
            ),
            "hint": self.buddy.give_hint(
                question_id=self._question_id(record),
                user_answer=str(record.get("user_answer") or ""),
                level=hint_level,
            ),
            "break_suggestion": self.buddy.suggest_break(
                mood=str(record.get("mood") or "normal"),
                consecutive_success=int(self._consecutive_success(record)),
                session_minutes=int(record.get("session_minutes") or 0),
            ),
        }
        self._publish_bus_event("buddy", "orchestrator", "response", result)
        events.append(self._record_event("buddy_done", "陪练建议生成", result))
        return result

    def _load_all_questions(self) -> list[dict[str, Any]]:
        """从题库组装推荐候选题。"""
        candidates: list[dict[str, Any]] = []
        for module in question_tools.get_all_modules():
            for file_path in question_tools.get_questions_in_module(module):
                question = question_tools.parse_question_file(file_path)
                if question is None:
                    continue
                candidates.append(
                    {
                        "question_id": question.question_id,
                        "module": question.module,
                        "title": question.title,
                        "content": question.content,
                    }
                )
        return candidates

    def _to_question_payload(self, record: dict[str, Any]) -> dict[str, Any]:
        """把学习记录映射为 LinkerAgent 期望的题目标识。"""
        question_id = self._question_id(record)
        question = question_tools.get_question_by_id(question_id)
        if question is not None:
            return {
                "question_id": question.question_id,
                "module": question.module,
                "title": question.title,
                "content": question.content,
            }

        return {
            "question_id": question_id,
            "module": str(record.get("module") or "未知模块"),
            "title": str(record.get("question") or "未知题目"),
            "content": "",
        }

    def _to_scores(self, record: dict[str, Any]) -> dict[str, float]:
        """统一从 record 中提取四维评分。"""
        raw_scores = record.get("scores")
        if not isinstance(raw_scores, dict):
            raw_scores = record
        return {
            "accuracy": self._to_float(raw_scores.get("accuracy")),
            "completeness": self._to_float(raw_scores.get("completeness")),
            "depth": self._to_float(raw_scores.get("depth")),
            "scenario": self._to_float(raw_scores.get("scenario")),
        }

    def _performance_from_scores(self, scores: dict[str, float]) -> float:
        """把四维评分转成 SM-2 的 performance。"""
        return sum(scores.values()) / 4

    @staticmethod
    def _consecutive_success(record: dict[str, Any]) -> int:
        """从记录中取连续答对次数，默认 0。"""
        try:
            return int(record.get("consecutive_success") or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _question_id(record: dict[str, Any]) -> str:
        """兼容不同来源字段名。"""
        return str(record.get("question_id") or record.get("id") or "")

    @staticmethod
    def _to_float(value: Any) -> float:
        """安全转 float，失败则按 0 处理。"""
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _record_event(agent_name: str, message: str, payload: dict[str, Any]) -> dict[str, Any]:
        """生成统一事件对象，方便后续日志或消息总线接入。"""
        return {
            "agent": agent_name,
            "message": message,
            "payload": payload,
        }

    def _publish_bus_event(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        payload: dict[str, Any],
    ) -> None:
        """发布并可审计的 Agent 协作事件。"""
        self.message_bus.publish(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            message=payload,
        )

    def _persist_result(
        self,
        question_id: str,
        result: dict[str, Any],
        session_id: Optional[str],
        record_id: Optional[int],
    ) -> int:
        """将一次编排闭环结果落库，供后续 API 与审计使用。"""
        run_id = memory_tools.save_orchestration_run(
            question_id=question_id,
            result=result,
            session_id=session_id,
            record_id=record_id,
        )

        for event in self.message_bus.get_events():
            memory_tools.log_agent_interaction(
                from_agent=str(event.get("from_agent") or ""),
                to_agent=str(event.get("to_agent") or ""),
                message_type=str(event.get("message_type") or "event"),
                content=event.get("payload") or {},
                session_id=session_id,
            )

        return run_id


def run_demo(record: dict[str, Any], include_report: bool = False) -> dict[str, Any]:
    """小工具入口，供手动调试编排链。"""
    orchestrator = MultiAgentOrchestrator()
    return orchestrator.orchestrate_after_answer(record, include_report=include_report)


if __name__ == "__main__":
    sample_record = {
        "question_id": "hashmap-basic",
        "module": "Java集合",
        "question": "HashMap 的底层结构是什么？",
        "user_answer": "数组、链表和红黑树",
        "scores": {
            "accuracy": 4,
            "completeness": 3,
            "depth": 2.5,
            "scenario": 3,
        },
        "weak_points": ["场景化答案欠缺"],
        "consecutive_success": 3,
    }
    print(run_demo(sample_record))
