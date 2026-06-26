#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""题库工具：读取 Markdown 题目、按模块抽题、搜索题目。

这个文件是 Agent 的“题库入口”。面试官 Agent 不直接遍历文件夹，
而是通过这些函数获取题目，方便以后替换成数据库或向量检索。
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover - 只在缺少 PyYAML 时触发。
    yaml = None


# Path 是 Python 推荐的路径处理方式，比手写字符串拼接更安全。
# `parents[2]` 表示从当前文件向上找两级目录，也就是项目根目录。
ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / ".harness" / "config" / "harness.yaml"
KB_CONFIG_PATH = ROOT_DIR / ".harness" / "config" / "knowledge_bases.yaml"


@dataclass
class Question:
    """一道人为可读的面试题。

    Python 的 dataclass 很适合做“数据载体”。你可以把它类比成 Java 的
    POJO / record：字段清晰，主要用来装数据。
    """

    question_id: str
    file_path: str
    module: str
    title: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换成 dict，便于 JSON 返回或测试断言。"""
        return {
            "question_id": self.question_id,
            "file_path": self.file_path,
            "module": self.module,
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata,
        }


def _load_yaml(path: Path) -> Dict[str, Any]:
    """安全读取 YAML；失败时返回空 dict。"""
    if yaml is None or not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as file:
            loaded = yaml.safe_load(file) or {}
    except Exception:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _resolve_question_base() -> Path:
    """从配置解析题库根目录，失败时使用常见默认目录。"""
    main_cfg = _load_yaml(CONFIG_PATH)
    # 这里的条件表达式读法是：如果 main_cfg 有值，就从配置取默认知识库；
    # 否则使用 "java_interview"。
    default_kb = (
        main_cfg.get("knowledge_base", {}).get("default", "java_interview")
        if main_cfg
        else "java_interview"
    )

    kb_cfg = _load_yaml(KB_CONFIG_PATH)
    kb_item = kb_cfg.get("knowledge_bases", {}).get(default_kb, {})
    rel_path = kb_item.get("path")
    if rel_path:
        resolved = ROOT_DIR / rel_path
        if resolved.exists():
            return resolved

    # 兼容不同阶段留下的题库目录名。
    candidates = [
        ROOT_DIR / "知识库" / "Java面试",
        ROOT_DIR / "Java八股文",
        ROOT_DIR / "面试题库",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


QUESTION_BASE = _resolve_question_base()


def set_knowledge_base(kb_key: str) -> bool:
    """运行时切换知识库目录。

    Args:
        kb_key: `.harness/config/knowledge_bases.yaml` 中的知识库键名。

    Returns:
        找到并切换成功返回 True，否则返回 False。
    """
    global QUESTION_BASE
    # global 表示下面要修改模块级变量 QUESTION_BASE，而不是创建同名局部变量。
    # 一般业务代码要少用 global，这里用于脚本运行时切换知识库，范围很小。

    kb_cfg = _load_yaml(KB_CONFIG_PATH)
    kb_item = kb_cfg.get("knowledge_bases", {}).get(kb_key, {})
    rel_path = kb_item.get("path")
    if not rel_path:
        return False

    resolved = ROOT_DIR / rel_path
    if not resolved.exists():
        return False

    QUESTION_BASE = resolved
    return True


def get_all_modules() -> List[str]:
    """获取题库下的所有模块名。"""
    if not QUESTION_BASE.exists():
        return []

    modules = []
    # iterdir() 会遍历目录下的直接子文件/子目录，不会递归。
    for item in QUESTION_BASE.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            modules.append(item.name)
    return sorted(modules)


def get_questions_in_module(module: str) -> List[str]:
    """获取某个模块下所有 Markdown 题目文件路径。"""
    module_path = QUESTION_BASE / module
    if not module_path.exists():
        return []

    questions = []
    for file_path in module_path.glob("*.md"):
        if not file_path.name.startswith("."):
            questions.append(str(file_path))
    return sorted(questions)


def parse_question_file(file_path: str) -> Optional[Question]:
    """解析一个 Markdown 题目文件。"""
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        return None

    # errors="ignore" 表示遇到少量非法字符时跳过，避免整个导入流程中断。
    content = file_path_obj.read_text(encoding="utf-8", errors="ignore")
    metadata, body = _split_frontmatter(content)

    # 文件名通常就是题目标题；去掉常见完成标记后更适合展示。
    title = file_path_obj.stem.replace("✅", "").strip()
    module = file_path_obj.parent.name
    question_id = str(metadata.get("question_id") or title)

    return Question(
        question_id=question_id,
        file_path=str(file_path_obj),
        module=module,
        title=title,
        content=body,
        metadata=metadata,
    )


def extract_typical_answer(content: str) -> str:
    """从题目正文里提取“典型回答”部分。

    如果没有这个标题，就返回正文前 500 个字符，保证调用方总能拿到
    一段可参考的内容。
    """
    markers = ["# 典型回答", "## 典型回答", "# 参考答案", "## 参考答案"]
    for marker in markers:
        if marker in content:
            answer_section = content.split(marker, 1)[1]
            return answer_section.split("\n#", 1)[0].strip()
    return content[:500].strip()


def get_random_question(
    module: Optional[str] = None,
    exclude_ids: Optional[List[str]] = None,
) -> Optional[Question]:
    """随机获取一道题。

    Args:
        module: 指定模块；传 None 时从所有模块里抽题。
        exclude_ids: 需要排除的题目 ID 列表，避免短时间内重复抽到。
    """
    # 用 set 做排除判断比 list 更快；题量大时差异会明显。
    exclude = set(exclude_ids or [])
    question_files = _collect_question_files(module)
    if not question_files:
        return None

    random.shuffle(question_files)
    for file_path in question_files:
        question = parse_question_file(file_path)
        if question and question.question_id not in exclude:
            return question
    return None


def get_question_by_id(question_id: str) -> Optional[Question]:
    """根据题目 ID 查找题目。"""
    for file_path in _collect_question_files(module=None):
        question = parse_question_file(file_path)
        if question and question.question_id == question_id:
            return question
    return None


def search_questions(
    keyword: str,
    module: Optional[str] = None,
) -> List[Question]:
    """按关键词搜索题目标题和正文。"""
    keyword_lower = keyword.lower()
    results = []

    for file_path in _collect_question_files(module):
        question = parse_question_file(file_path)
        if question is None:
            continue
        haystack = f"{question.title}\n{question.content}".lower()
        if keyword_lower in haystack:
            results.append(question)
    return results


def get_question_stats() -> Dict[str, Any]:
    """获取题库统计信息。"""
    stats: Dict[str, Any] = {
        "total": 0,
        "modules": {},
    }

    for module in get_all_modules():
        count = len(get_questions_in_module(module))
        stats["modules"][module] = count
        stats["total"] += count
    return stats


def _collect_question_files(module: Optional[str]) -> List[str]:
    """收集候选题目文件路径。"""
    if module:
        return get_questions_in_module(module)

    question_files: List[str] = []
    for module_name in get_all_modules():
        question_files.extend(get_questions_in_module(module_name))
    return question_files


def _split_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """拆分 Markdown frontmatter 和正文。

    frontmatter 是 Markdown 文件开头 `---` 包住的 YAML 元数据。
    返回值是 `(metadata, body)`，这是 Python 常见的多返回值写法。
    """
    if not content.startswith("---"):
        return {}, content

    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, content

    try:
        end_index = lines[1:].index("---") + 1
    except ValueError:
        return {}, content

    raw_meta = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :])
    if yaml is None:
        return {}, body

    try:
        metadata = yaml.safe_load(raw_meta) or {}
    except Exception:
        metadata = {}
    return metadata if isinstance(metadata, dict) else {}, body


if __name__ == "__main__":
    # 这个自检入口方便你单独运行本文件：
    # python -m agents.tools.question_tools
    stats = get_question_stats()
    print("题库工具自检")
    print("=" * 40)
    print(f"题库目录: {QUESTION_BASE}")
    print(f"总题数: {stats['total']}")
    print(f"模块数: {len(stats['modules'])}")

    sample = get_random_question()
    if sample:
        print(f"随机题目: [{sample.module}] {sample.title}")
    else:
        print("未找到题目，请检查知识库配置。")
