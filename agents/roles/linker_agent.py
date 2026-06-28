#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识关联器 Agent。

LinkerAgent 负责发现题目之间的关系。当前版本先实现轻量规则：
- 同模块加权
- 关键词重合
- 标题相似度
- 根据标题/正文关键词识别 compare/scenario/prerequisite/progressive

这版不引入 sklearn，便于初学者先看懂业务流程；后续再把
`calculate_similarity()` 替换成 TF-IDF + 余弦相似度即可。
"""

from __future__ import annotations

import re
from typing import Any, Optional

from agents.core.base_agent import Agent


RELATION_LABELS: dict[str, str] = {
    "compare": "对比型",
    "progressive": "递进型",
    "scenario": "场景型",
    "prerequisite": "前置型",
}

# 这些词对排序价值不大，类似 Java 里做搜索前先过滤 stop words。
STOP_WORDS: set[str] = {
    "java",
    "的",
    "和",
    "与",
    "及",
    "或",
    "怎么",
    "如何",
    "什么",
    "原理",
    "底层",
    "机制",
    "知识",
}

COMPARE_KEYWORDS: tuple[str, ...] = ("区别", "对比", "比较", " vs ", " versus ", "不同")
SCENARIO_KEYWORDS: tuple[str, ...] = ("场景", "项目", "业务", "选择", "使用", "实战", "如何")
PREREQUISITE_KEYWORDS: tuple[str, ...] = ("前置", "基础", "入门", "先掌握", "依赖")
PROGRESSIVE_KEYWORDS: tuple[str, ...] = ("扩容", "优化", "源码", "流程", "调优", "深入")


class LinkerAgent(Agent):
    """知识关联器：负责发现题目之间的关系。"""

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        # 保留标准 Agent 形态。当前关联逻辑是确定性代码，未来可以接入
        # 向量检索、知识图谱或 LLM 解释推荐原因。
        super().__init__("linker", config)

    def extract_keywords(
        self,
        title: str,
        content: str = "",
        max_keywords: int = 8,
    ) -> list[str]:
        """从标题和正文抽取关键词。

        返回 list[str] 是为了保持顺序：标题词优先，正文高频词补充。
        可以类比 Java 里先用 LinkedHashMap 去重，再取前 N 个 key。
        """
        ordered_keywords: list[str] = []
        for keyword in self._tokenize(title) + self._tokenize(content):
            if keyword in STOP_WORDS or keyword in ordered_keywords:
                continue
            ordered_keywords.append(keyword)
            if len(ordered_keywords) >= max_keywords:
                break
        return ordered_keywords

    def calculate_similarity(
        self,
        source: dict[str, Any],
        candidate: dict[str, Any],
    ) -> dict[str, Any]:
        """计算两道题的轻量相似度。

        这里故意返回 dict，而不是只返回 float，方便调用方看到分数来源。
        这对学习和调试更友好：知道“为什么推荐”，比只看到排序更重要。
        """
        source_keywords = set(
            self.extract_keywords(
                self._text(source, "title"),
                self._text(source, "content"),
            )
        )
        candidate_keywords = set(
            self.extract_keywords(
                self._text(candidate, "title"),
                self._text(candidate, "content"),
            )
        )
        shared_keywords = sorted(source_keywords & candidate_keywords)
        title_overlap = self._title_overlap(source, candidate)
        same_module = self._text(source, "module") == self._text(candidate, "module")
        relation_type = self.detect_relation_type(source, candidate)

        score = 0.0
        if same_module:
            score += 0.35
        score += min(len(shared_keywords) * 0.12, 0.36)
        score += title_overlap * 0.20
        if relation_type != "progressive":
            # 明确关系类型能让推荐更可解释，但不能盖过真正的关键词相似。
            score += 0.09

        return {
            "score": round(score, 4),
            "same_module": same_module,
            "shared_keywords": shared_keywords,
            "title_overlap": round(title_overlap, 4),
            "relation_type": relation_type,
        }

    def detect_relation_type(
        self,
        source: dict[str, Any],
        candidate: dict[str, Any],
    ) -> str:
        """判断候选题和当前题之间的关系类型。"""
        text = self._combined_text(candidate)
        if self._contains_any(text, COMPARE_KEYWORDS):
            return "compare"
        if self._contains_any(text, PREREQUISITE_KEYWORDS):
            return "prerequisite"
        if self._contains_any(text, SCENARIO_KEYWORDS):
            return "scenario"
        if self._contains_any(text, PROGRESSIVE_KEYWORDS):
            return "progressive"

        # 模块不同但候选题明显更基础时，优先看作前置题。
        if self._text(source, "module") != self._text(candidate, "module"):
            candidate_title = self._text(candidate, "title")
            if "基础" in candidate_title or "入门" in candidate_title:
                return "prerequisite"
        return "progressive"

    def find_related_questions(
        self,
        question: dict[str, Any],
        candidates: list[dict[str, Any]],
        top_k: int = 5,
    ) -> dict[str, Any]:
        """从候选题中推荐相关题。

        question/candidates 都是 dict，类似 Java 里的 DTO。为了避免把当前题
        自己推荐给自己，会用 question_id 做一次排除。
        """
        scored_items = []
        source_id = self._question_id(question)
        for candidate in candidates:
            if self._question_id(candidate) == source_id:
                continue
            similarity = self.calculate_similarity(question, candidate)
            if similarity["score"] <= 0:
                continue
            scored_items.append(
                {
                    **candidate,
                    "score": similarity["score"],
                    "relation_type": similarity["relation_type"],
                    "relation_name": RELATION_LABELS[similarity["relation_type"]],
                    "shared_keywords": similarity["shared_keywords"],
                    "reason": self._build_reason(similarity),
                }
            )

        # Python 的 sorted(..., key=...) 类似 Java Stream sorted + Comparator。
        # 这里先按分数降序，再按 question_id 保持同分时结果稳定。
        ranked_items = sorted(
            scored_items,
            key=lambda item: (-float(item["score"]), self._question_id(item)),
        )
        limited_items = ranked_items[: max(int(top_k), 0)]
        return {
            "status": "ok",
            "source_question_id": source_id,
            "items": limited_items,
            "count": len(limited_items),
        }

    def process(self, input_data: Any) -> Any:
        """同步入口，用 action 路由到具体关联能力。

        目前支持：
        - {"action": "extract_keywords", "title": "...", "content": "..."}
        - {"action": "find_related_questions", "question": {...}, "candidates": [...]}
        """
        if not isinstance(input_data, dict):
            return {
                "status": "error",
                "message": "知识关联输入必须是 dict，类似 Java 里的 DTO。",
            }

        action = str(input_data.get("action") or "find_related_questions")
        if action == "extract_keywords":
            return {
                "status": "ok",
                "keywords": self.extract_keywords(
                    title=self._text(input_data, "title"),
                    content=self._text(input_data, "content"),
                    max_keywords=int(input_data.get("max_keywords") or 8),
                ),
            }

        if action == "find_related_questions":
            question = input_data.get("question")
            candidates = input_data.get("candidates")
            if not isinstance(question, dict) or not isinstance(candidates, list):
                return {
                    "status": "error",
                    "message": "find_related_questions 需要 question=dict 且 candidates=list。",
                }
            valid_candidates = [
                candidate for candidate in candidates if isinstance(candidate, dict)
            ]
            return self.find_related_questions(
                question=question,
                candidates=valid_candidates,
                top_k=int(input_data.get("top_k") or 5),
            )

        return {
            "status": "error",
            "message": f"不支持的知识关联动作: {action}",
        }

    def _tokenize(self, text: str) -> list[str]:
        """把中英文混合文本拆成关键词。

        简化规则：
        - 英文/数字连续串转小写，例如 HashMap -> hashmap。
        - 中文按空格保留词组，例如“负载因子”不会被拆散。
        - 对没有空格的中文短句，再补充 2-6 字的片段，便于标题匹配。
        """
        normalized_text = str(text or "").strip()
        if not normalized_text:
            return []

        tokens: list[str] = []
        for raw_part in re.split(r"[\s,，。；;：:、（）()\[\]【】]+", normalized_text):
            part = raw_part.strip()
            if not part:
                continue
            if re.fullmatch(r"[A-Za-z0-9_+-]+", part):
                tokens.append(part.lower())
                continue
            tokens.append(part.lower())
            tokens.extend(self._split_mixed_token(part))
        return self._deduplicate(tokens)

    def _split_mixed_token(self, token: str) -> list[str]:
        """补充混合词中的英文和中文片段。"""
        parts: list[str] = []
        parts.extend(match.lower() for match in re.findall(r"[A-Za-z0-9_+-]+", token))

        chinese_chunks = re.findall(r"[\u4e00-\u9fff]{2,6}", token)
        for chunk in chinese_chunks:
            parts.append(chunk)
        return parts

    def _title_overlap(
        self,
        source: dict[str, Any],
        candidate: dict[str, Any],
    ) -> float:
        """计算标题关键词交集比例。"""
        source_tokens = set(self._tokenize(self._text(source, "title")))
        candidate_tokens = set(self._tokenize(self._text(candidate, "title")))
        if not source_tokens or not candidate_tokens:
            return 0.0
        return len(source_tokens & candidate_tokens) / len(source_tokens | candidate_tokens)

    def _build_reason(self, similarity: dict[str, Any]) -> str:
        """生成推荐原因，便于前端或 CLI 直接展示。"""
        reasons: list[str] = []
        if similarity["same_module"]:
            reasons.append("同模块")
        shared_keywords = similarity["shared_keywords"]
        if shared_keywords:
            reasons.append(f"共享关键词: {', '.join(shared_keywords[:3])}")
        relation_type = str(similarity["relation_type"])
        reasons.append(f"关系类型: {RELATION_LABELS[relation_type]}")
        return "；".join(reasons)

    def _combined_text(self, question: dict[str, Any]) -> str:
        """合并标题和正文，供规则判断使用。"""
        return f" {self._text(question, 'title')} {self._text(question, 'content')} ".lower()

    def _contains_any(self, text: str, keywords: tuple[str, ...]) -> bool:
        """判断文本是否包含任意关键词。"""
        return any(keyword.lower() in text for keyword in keywords)

    def _question_id(self, question: dict[str, Any]) -> str:
        """兼容 question_id/id 两种字段名。"""
        return self._text(question, "question_id") or self._text(question, "id")

    def _text(self, data: dict[str, Any], key: str) -> str:
        """安全读取字符串字段，避免 None 传播到业务逻辑里。"""
        return str(data.get(key) or "").strip()

    def _deduplicate(self, items: list[str]) -> list[str]:
        """按出现顺序去重。"""
        result: list[str] = []
        for item in items:
            normalized_item = item.strip().lower()
            if not normalized_item or normalized_item in result:
                continue
            result.append(normalized_item)
        return result
