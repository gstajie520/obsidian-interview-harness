#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""错题分析师 Agent。

AnalyzerAgent 负责把“一条低分答题记录”转成更容易执行的补救建议。
当前版本先不用 LLM，而是用可测试、可解释的规则完成四类错因判断：
- 概念混淆
- 细节遗漏
- 场景不足
- 前置知识缺失
"""

from __future__ import annotations

import json
from typing import Any, Optional

from agents.core.base_agent import Agent


ERROR_TYPES: dict[str, dict[str, str]] = {
    "concept_confusion": {
        "name": "概念混淆",
        "suggestion": "先把两个容易混的概念拆开，对比定义、触发条件和关键区别。",
    },
    "detail_missing": {
        "name": "细节遗漏",
        "suggestion": "把遗漏的关键数字、条件和步骤整理成一张细节卡片，再复述一遍。",
    },
    "scenario_lack": {
        "name": "场景不足",
        "suggestion": "补一个真实业务场景，说明这个知识点什么时候用、为什么这么用。",
    },
    "prerequisite_gap": {
        "name": "前置知识缺失",
        "suggestion": "先回到前置知识，按“定义 -> 核心机制 -> 再回答本题”的顺序复盘。",
    },
}

DIMENSION_TO_ERROR_TYPE: dict[str, str] = {
    "accuracy": "concept_confusion",
    "completeness": "detail_missing",
    "depth": "prerequisite_gap",
    "scenario": "scenario_lack",
}

ERROR_KEYWORDS: dict[str, list[str]] = {
    "concept_confusion": ["混淆", "搞混", "概念", "区别", "分不清", "理解错误", "误解"],
    "detail_missing": ["遗漏", "细节", "忘记", "没有提到", "阈值", "参数", "步骤", "条件", "数字"],
    "scenario_lack": ["场景", "项目", "什么时候用", "何时使用", "案例", "实战", "落地", "应用"],
    "prerequisite_gap": ["前置", "基础", "不扎实", "底层", "依赖", "先掌握"],
}

SCORE_DIMENSIONS: tuple[str, ...] = ("accuracy", "completeness", "depth", "scenario")


class AnalyzerAgent(Agent):
    """错题分析师：负责识别错误模式并给出补救方向。"""

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        # 保留标准 Agent 形态。当前分析逻辑先用确定性规则实现，未来可以再
        # 让 LLM 基于这些结构化结果生成更自然的讲解。
        super().__init__("analyzer", config)

    def analyze_wrong_answer(self, record: dict[str, Any]) -> dict[str, Any]:
        """分析一条错题记录，返回错因、证据和补救动作。

        record 可以理解成 Java 里的 DTO。常用字段：
        - question_id/module/question/user_answer：题目上下文
        - scores：四维评分 dict，例如 {"accuracy": 2, "depth": 1}
        - weak_points：面试官识别出的薄弱点列表
        """
        scores = self._normalize_scores(record)
        weak_points = self._normalize_weak_points(record.get("weak_points"))
        lowest_dimension, lowest_score = self._find_lowest_score(scores)
        error_type = self._classify_error_type(weak_points, lowest_dimension)
        error_info = ERROR_TYPES[error_type]
        evidence = self._build_evidence(weak_points, lowest_dimension, lowest_score)
        remedial_actions = self._build_remedial_actions(error_type)

        result: dict[str, Any] = {
            "status": "analyzed",
            "question_id": record.get("question_id"),
            "module": record.get("module"),
            "error_type": error_type,
            "error_type_name": error_info["name"],
            "lowest_dimension": lowest_dimension,
            "lowest_score": lowest_score,
            "scores": scores,
            "evidence": evidence,
            "suggestion": error_info["suggestion"],
            "remedial_actions": remedial_actions,
        }
        result["markdown"] = self._render_markdown(result)
        return result

    def process(self, input_data: Any) -> Any:
        """同步入口，用 action 路由到具体分析能力。

        目前支持：
        - {"action": "analyze_wrong_answer", "record": {...}}

        如果调用方直接传一条错题记录且没有 action，也会按错题分析处理。
        """
        if not isinstance(input_data, dict):
            return {
                "status": "error",
                "message": "错题分析输入必须是 dict，类似 Java 里的 DTO。",
            }

        data = input_data
        action = str(data.get("action") or "analyze_wrong_answer")

        if action == "analyze_wrong_answer":
            record = data.get("record") if isinstance(data.get("record"), dict) else data
            return self.analyze_wrong_answer(record)

        return {
            "status": "error",
            "message": f"不支持的错题分析动作: {action}",
        }

    def _normalize_scores(self, record: dict[str, Any]) -> dict[str, float]:
        """把不同来源的评分统一成四维评分 dict。

        有些调用方会传 record["scores"]，数据库记录则可能把 accuracy 等字段
        放在最外层。这里统一处理，避免上层调用方必须关心这些差异。
        """
        raw_scores = record.get("scores")
        if not isinstance(raw_scores, dict):
            raw_scores = record

        return {
            dimension: self._to_float(raw_scores.get(dimension))
            for dimension in SCORE_DIMENSIONS
        }

    def _normalize_weak_points(self, raw_value: Any) -> list[str]:
        """把 weak_points 统一成字符串列表。

        memory_tools 存数据库时可能会把列表转成 JSON 字符串，所以这里也能
        读 JSON 字符串。这样 Analyzer 以后接数据库记录时不用再做转换。
        """
        if isinstance(raw_value, list):
            return [str(item).strip() for item in raw_value if str(item).strip()]

        if isinstance(raw_value, str):
            text = raw_value.strip()
            if not text:
                return []
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                return [text]
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [text]

        return []

    def _find_lowest_score(self, scores: dict[str, float]) -> tuple[str, float]:
        """找出最低分维度，作为没有关键词时的兜底判断依据。"""
        lowest_dimension = min(SCORE_DIMENSIONS, key=lambda dimension: scores[dimension])
        return lowest_dimension, scores[lowest_dimension]

    def _classify_error_type(
        self,
        weak_points: list[str],
        lowest_dimension: str,
    ) -> str:
        """根据薄弱点关键词判断错因；没有命中时按最低分维度兜底。"""
        text = " ".join(weak_points)
        keyword_scores = {
            error_type: sum(1 for keyword in keywords if keyword in text)
            for error_type, keywords in ERROR_KEYWORDS.items()
        }
        best_error_type, best_score = max(
            keyword_scores.items(),
            key=lambda item: item[1],
        )
        if best_score > 0:
            return best_error_type
        return DIMENSION_TO_ERROR_TYPE[lowest_dimension]

    def _build_evidence(
        self,
        weak_points: list[str],
        lowest_dimension: str,
        lowest_score: float,
    ) -> list[str]:
        """组装“为什么这么判断”的证据，方便用户学习规则。"""
        evidence = [
            f"最低评分维度: {lowest_dimension}={lowest_score:.1f}",
        ]
        evidence.extend(f"薄弱点: {point}" for point in weak_points)
        if len(evidence) == 1:
            evidence.append("没有提供薄弱点文本，因此使用最低评分维度兜底判断。")
        return evidence

    def _build_remedial_actions(self, error_type: str) -> list[dict[str, Any]]:
        """为不同错因生成可执行补救动作。"""
        actions: dict[str, list[dict[str, Any]]] = {
            "concept_confusion": [
                {
                    "type": "comparison_table",
                    "title": "生成易混概念对比表",
                    "steps": ["分别写定义", "对比触发条件", "补一句面试记忆口诀"],
                },
                {
                    "type": "repeat_answer",
                    "title": "用自己的话重答一遍",
                    "steps": ["先说区别", "再说共同点", "最后说使用场景"],
                },
            ],
            "detail_missing": [
                {
                    "type": "detail_card",
                    "title": "整理关键细节卡片",
                    "steps": ["写出关键数字", "写出触发条件", "写出容易遗漏的边界"],
                },
                {
                    "type": "short_recall",
                    "title": "间隔 10 分钟后快速回忆",
                    "steps": ["合上答案", "复述 3 个关键点", "漏掉的点再标红"],
                },
            ],
            "scenario_lack": [
                {
                    "type": "scenario_practice",
                    "title": "补一个真实业务场景",
                    "steps": ["描述业务背景", "说明为什么用它", "补充不用它会怎样"],
                },
                {
                    "type": "tradeoff_summary",
                    "title": "补充优缺点取舍",
                    "steps": ["写优点", "写缺点", "写适用边界"],
                },
            ],
            "prerequisite_gap": [
                {
                    "type": "prerequisite_review",
                    "title": "回补前置知识",
                    "steps": ["先学前置概念", "再画核心流程", "最后回到原题重答"],
                },
                {
                    "type": "dependency_chain",
                    "title": "画知识依赖链",
                    "steps": ["列出不懂的名词", "按先后顺序排序", "逐个补齐"],
                },
            ],
        }
        return actions[error_type]

    def _render_markdown(self, result: dict[str, Any]) -> str:
        """把分析结果渲染成 Markdown，后续可直接导出到 Obsidian。"""
        evidence_lines = [f"- {item}" for item in result["evidence"]]
        action_lines = [
            f"- {index}. {action['title']}"
            for index, action in enumerate(result["remedial_actions"], start=1)
        ]
        return "\n".join(
            [
                "# 错题分析",
                "",
                f"- 题目 ID: {result.get('question_id') or '未知'}",
                f"- 模块: {result.get('module') or '未分类'}",
                f"- 错误类型: {result['error_type_name']}",
                "",
                "## 证据",
                *evidence_lines,
                "",
                "## 补救建议",
                result["suggestion"],
                "",
                "## 下一步动作",
                *action_lines,
            ]
        )

    def _to_float(self, value: Any) -> float:
        """安全地把外部输入转成 float，无法转换时按 0 分处理。"""
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
