#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent-Harness + Obsidian interview assistant.

This is a local-first harness:
- uploaded materials are copied into raw/interview_uploads/ and kept immutable
- interview cards are generated into 面试题库/
- every session is archived in SQLite with FTS search
- topic weakness is written back into Obsidian-visible Markdown memory
"""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import random
import re
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

try:
    import yaml
except ImportError:  # pragma: no cover - the existing vault already uses PyYAML.
    yaml = None


if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


VAULT_ROOT = Path(__file__).resolve().parents[1]
RAW_UPLOADS = VAULT_ROOT / "raw" / "interview_uploads"
QUESTION_BANK = VAULT_ROOT / "面试题库"
SESSION_NOTES = VAULT_ROOT / "学习记录"
HARNESS_ROOT = VAULT_ROOT / ".harness"
DB_PATH = HARNESS_ROOT / "db" / "interview_harness.db"
MEMORY_MD = HARNESS_ROOT / "memory" / "MEMORY.md"
USER_MD = HARNESS_ROOT / "memory" / "USER.md"


@dataclass
class QuestionCard:
    title: str
    topic: str
    source_path: Path
    prompt: str
    reference: str


def now_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def ensure_dirs() -> None:
    for path in [RAW_UPLOADS, QUESTION_BANK, SESSION_NOTES, HARNESS_ROOT / "db", HARNESS_ROOT / "memory"]:
        path.mkdir(parents=True, exist_ok=True)


def connect_db() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            mode TEXT NOT NULL,
            source TEXT,
            summary TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            ts TEXT NOT NULL,
            role TEXT NOT NULL,
            topic TEXT,
            question TEXT,
            answer TEXT,
            score INTEGER,
            feedback TEXT,
            source_path TEXT,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        );

        CREATE TABLE IF NOT EXISTS topic_stats (
            topic TEXT PRIMARY KEY,
            attempts INTEGER NOT NULL DEFAULT 0,
            avg_score REAL NOT NULL DEFAULT 0,
            weak_count INTEGER NOT NULL DEFAULT 0,
            last_seen TEXT
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS turns_fts
        USING fts5(session_id, topic, question, answer, feedback, content='');
        """
    )
    return conn


def init_command(_: argparse.Namespace) -> None:
    connect_db().close()
    if not MEMORY_MD.exists():
        MEMORY_MD.write_text(
            "# Interview Harness Memory\n\n"
            "## Stable Facts\n"
            "- This vault uses Agent-Harness roles to run interview practice.\n\n"
            "## Weak Topics\n"
            "- No weak topics recorded yet.\n\n"
            "## Review Policy\n"
            "- Score 1-2: answer is missing or incorrect; review tomorrow.\n"
            "- Score 3: partially correct; review in 3 days.\n"
            "- Score 4-5: fluent enough; review in 7 days.\n",
            encoding="utf-8",
        )
    if not USER_MD.exists():
        USER_MD.write_text(
            "# Interview Harness User Profile\n\n"
            "## Goals\n"
            "- Prepare for technical interviews by practicing recall, explanation, and follow-up questions.\n\n"
            "## Preferences\n"
            "- Use Chinese for coaching by default.\n"
            "- Prefer direct feedback over vague encouragement.\n",
            encoding="utf-8",
        )
    print(f"Initialized harness database: {DB_PATH}")


def read_text_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt", ".csv", ".json", ".yaml", ".yml"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        errors = []
        for module_name in ("pypdf", "PyPDF2"):
            try:
                module = __import__(module_name)
                reader = module.PdfReader(str(path))
                pages = [page.extract_text() or "" for page in reader.pages]
                return "\n".join(pages).strip()
            except Exception as exc:
                errors.append(f"{module_name}: {exc}")
        return "[pdf text extraction failed: " + " | ".join(errors) + "]"
    if suffix == ".docx":
        try:
            import zipfile
            import xml.etree.ElementTree as ET

            with zipfile.ZipFile(path) as zf:
                xml = zf.read("word/document.xml")
            root = ET.fromstring(xml)
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            paragraphs = []
            for para in root.findall(".//w:p", ns):
                text = "".join(node.text or "" for node in para.findall(".//w:t", ns))
                if text.strip():
                    paragraphs.append(text)
            return "\n".join(paragraphs)
        except Exception as exc:
            return f"[docx text extraction failed: {exc}]"
    return f"[unsupported file type: {suffix or 'no extension'}]"


def normalize_title(text: str, fallback: str) -> str:
    text = re.sub(r"^[#\s>\\-]+", "", text).strip()
    text = re.sub(r"[\\/:*?\"<>|]", "_", text)
    text = re.sub(r"\s+", " ", text)
    return (text[:80] or fallback).strip()


def infer_topic(path: Path, title: str) -> str:
    candidates = [path.parent.name, title]
    known = ["Java", "JVM", "MySQL", "Redis", "Spring", "微服务", "并发", "网络", "设计模式", "项目", "算法"]
    text = " ".join(candidates)
    for item in known:
        if item.lower() in text.lower():
            return item
    return path.parent.name if path.parent.name not in {"interview_uploads", now_date()} else "综合面试"


def chunk_material(text: str) -> list[tuple[str, str]]:
    lines = [line.rstrip() for line in text.splitlines()]
    blocks: list[tuple[str, list[str]]] = []
    current_title = ""
    current_body: list[str] = []

    def flush() -> None:
        nonlocal current_title, current_body
        body = "\n".join(current_body).strip()
        if current_title and body:
            blocks.append((current_title, current_body))
        current_title = ""
        current_body = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_body:
                current_body.append("")
            continue
        is_heading = stripped.startswith("#")
        is_question = bool(re.match(r"^(Q[:：]|问题[:：]|面试题[:：]|[-*]\s*(Q|问题)[:：])", stripped, re.I))
        if is_heading or is_question:
            flush()
            current_title = normalize_title(stripped, "未命名题目")
        else:
            current_body.append(stripped)
    flush()

    if blocks:
        return [(title, "\n".join(body).strip()) for title, body in blocks[:80]]

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.strip()) > 80]
    return [(normalize_title(p.splitlines()[0], f"材料片段 {i + 1}"), p) for i, p in enumerate(paragraphs[:80])]


def build_cards(source_path: Path, text: str) -> list[QuestionCard]:
    cards: list[QuestionCard] = []
    for title, body in chunk_material(text):
        topic = infer_topic(source_path, title)
        if title.endswith("?") or title.endswith("？"):
            prompt = title
        else:
            prompt = f"请解释：{title}"
        cards.append(
            QuestionCard(
                title=title,
                topic=topic,
                source_path=source_path,
                prompt=prompt,
                reference=body,
            )
        )
    return cards


def write_card(card: QuestionCard) -> Path:
    topic_dir = QUESTION_BANK / card.topic
    topic_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(f"{card.source_path}:{card.title}".encode("utf-8")).hexdigest()[:8]
    filename = f"{normalize_title(card.title, 'interview-card')}-{digest}.md"
    target = topic_dir / filename
    rel_source = os.path.relpath(card.source_path, target.parent).replace("\\", "/")
    escaped_title = card.title.replace('"', '\\"')
    content = (
        "---\n"
        f"题目: \"{escaped_title}\"\n"
        f"模块: \"{card.topic}\"\n"
        "熟练度: ⚪\n"
        "上次复习:\n"
        "复习次数: 0\n"
        "标签: [interview-harness]\n"
        "来源类型: uploaded\n"
        f"source: \"{rel_source}\"\n"
        "---\n\n"
        f"# {card.title}\n\n"
        "## 面试官提问\n\n"
        f"{card.prompt}\n\n"
        "## 参考材料\n\n"
        f"{card.reference.strip()}\n\n"
        "## 个人答题记录\n\n"
        "- 暂无\n"
    )
    target.write_text(content, encoding="utf-8")
    return target


def upload_command(args: argparse.Namespace) -> None:
    init_command(args)
    source_paths = [Path(p).expanduser().resolve() for p in args.paths]
    imported = 0
    generated = 0
    date_dir = RAW_UPLOADS / now_date()
    date_dir.mkdir(parents=True, exist_ok=True)

    for source in source_paths:
        if not source.exists():
            print(f"Skipped missing path: {source}")
            continue
        files = [source]
        if source.is_dir():
            files = [p for p in source.rglob("*") if p.is_file()]
        for file_path in files:
            target = date_dir / file_path.name
            if target.exists():
                target = date_dir / f"{file_path.stem}-{now_stamp()}{file_path.suffix}"
            shutil.copy2(file_path, target)
            imported += 1
            text = read_text_file(target)
            if text.startswith("[") and "failed:" in text or text.startswith("[unsupported file type:"):
                print(f"Copied but skipped card generation for {file_path.name}: {text}")
                continue
            cards = build_cards(target, text)
            for card in cards:
                write_card(card)
                generated += 1

    print(f"Imported raw files: {imported}")
    print(f"Generated interview cards: {generated}")
    print(f"Question bank: {QUESTION_BANK}")


def parse_frontmatter(content: str) -> tuple[dict, str]:
    if not content.startswith("---\n"):
        return {}, content
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, content
    frontmatter = content[4:end]
    body = content[end + 5 :]
    if yaml is None:
        return {}, body
    try:
        return yaml.safe_load(frontmatter) or {}, body
    except Exception:
        return {}, body


def iter_question_files() -> Iterable[Path]:
    for base in [QUESTION_BANK, VAULT_ROOT / "Java八股文"]:
        if not base.exists():
            continue
        yield from (p for p in base.rglob("*.md") if p.is_file())


def load_question(path: Path) -> tuple[dict, str]:
    content = path.read_text(encoding="utf-8", errors="ignore")
    return parse_frontmatter(content)


def choose_question(topic: str | None, weak_first: bool = True) -> Path | None:
    files = list(iter_question_files())
    if topic:
        files = [p for p in files if topic.lower() in str(p).lower()]
    if not files:
        return None
    if weak_first:
        weak = []
        for path in files:
            meta, _ = load_question(path)
            if meta.get("熟练度") in {"🔴", "🟡", "⚪", None, ""}:
                weak.append(path)
        if weak:
            files = weak
    return random.choice(files)


def extract_reference(body: str) -> str:
    for marker in ["# 典型回答", "## 参考材料", "## 参考答案", "## 答案"]:
        if marker in body:
            return body.split(marker, 1)[1].split("\n#", 1)[0].strip()
    return body.strip()[:1600]


def update_question_progress(path: Path, score: int) -> None:
    if yaml is None:
        return
    content = path.read_text(encoding="utf-8", errors="ignore")
    meta, body = parse_frontmatter(content)
    if not meta:
        return
    if score >= 4:
        mastery = "🟢"
    elif score == 3:
        mastery = "🟡"
    else:
        mastery = "🔴"
    meta["熟练度"] = mastery
    meta["上次复习"] = now_date()
    meta["复习次数"] = int(meta.get("复习次数") or 0) + 1
    new_content = "---\n" + yaml.dump(meta, allow_unicode=True, sort_keys=False) + "---\n\n" + body
    path.write_text(new_content, encoding="utf-8")


def record_turn(
    conn: sqlite3.Connection,
    session_id: str,
    topic: str,
    question: str,
    answer: str,
    score: int,
    feedback: str,
    source_path: Path,
) -> None:
    cursor = conn.execute(
        """
        INSERT INTO turns(session_id, ts, role, topic, question, answer, score, feedback, source_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (session_id, datetime.now().isoformat(timespec="seconds"), "candidate", topic, question, answer, score, feedback, str(source_path)),
    )
    turn_rowid = cursor.lastrowid
    conn.execute(
        "INSERT INTO turns_fts(rowid, session_id, topic, question, answer, feedback) VALUES (?, ?, ?, ?, ?, ?)",
        (turn_rowid, session_id, topic, question, answer, feedback),
    )
    row = conn.execute("SELECT attempts, avg_score, weak_count FROM topic_stats WHERE topic = ?", (topic,)).fetchone()
    weak_inc = 1 if score <= 2 else 0
    if row:
        attempts, avg_score, weak_count = row
        attempts += 1
        avg_score = ((avg_score * (attempts - 1)) + score) / attempts
        weak_count += weak_inc
        conn.execute(
            "UPDATE topic_stats SET attempts=?, avg_score=?, weak_count=?, last_seen=? WHERE topic=?",
            (attempts, avg_score, weak_count, now_date(), topic),
        )
    else:
        conn.execute(
            "INSERT INTO topic_stats(topic, attempts, avg_score, weak_count, last_seen) VALUES (?, ?, ?, ?, ?)",
            (topic, 1, float(score), weak_inc, now_date()),
        )
    conn.commit()


def refresh_memory(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT topic, attempts, avg_score, weak_count, last_seen FROM topic_stats ORDER BY weak_count DESC, avg_score ASC, last_seen DESC LIMIT 20"
    ).fetchall()
    lines = [
        "# Interview Harness Memory",
        "",
        "## Stable Facts",
        "- The interview assistant uses uploaded Obsidian files and Java八股文 cards as the question source.",
        "- Session history is stored in `.harness/db/interview_harness.db` with FTS search.",
        "",
        "## Weak Topics",
    ]
    if rows:
        for topic, attempts, avg_score, weak_count, last_seen in rows:
            lines.append(f"- {topic}: attempts={attempts}, avg_score={avg_score:.2f}, weak_count={weak_count}, last_seen={last_seen}")
    else:
        lines.append("- No weak topics recorded yet.")
    lines.extend(
        [
            "",
            "## Review Policy",
            "- Score 1-2: ask the topic again soon and require the candidate to rebuild the answer structure.",
            "- Score 3: ask a follow-up question and schedule a 3-day review.",
            "- Score 4-5: keep the topic in rotation but prioritize weaker modules.",
        ]
    )
    MEMORY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_session_note(session_id: str, entries: list[dict]) -> Path:
    path = SESSION_NOTES / f"面试练习-{session_id}.md"
    lines = [
        "---",
        f"title: 面试练习 {session_id}",
        "tags: [interview-harness, study-session]",
        f"created: {now_date()}",
        "---",
        "",
        f"# 面试练习 {session_id}",
        "",
    ]
    for i, entry in enumerate(entries, 1):
        lines.extend(
            [
                f"## {i}. {entry['topic']} - {entry['title']}",
                "",
                f"- Score: {entry['score']}/5",
                f"- Source: `{entry['source']}`",
                "",
                "### Question",
                "",
                entry["question"],
                "",
                "### Answer",
                "",
                entry["answer"] or "(empty)",
                "",
                "### Supervisor Feedback",
                "",
                entry["feedback"],
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def practice_command(args: argparse.Namespace) -> None:
    conn = connect_db()
    session_id = now_stamp()
    conn.execute(
        "INSERT INTO sessions(id, started_at, mode, source) VALUES (?, ?, ?, ?)",
        (session_id, datetime.now().isoformat(timespec="seconds"), "interview", args.topic or "mixed"),
    )
    conn.commit()

    entries: list[dict] = []
    print(f"Interview Harness session: {session_id}")
    print("Roles: 主控Agent -> 面试官Agent -> 监督Agent -> 记忆复盘Agent")
    print("Input `q` as answer to stop.\n")

    for round_no in range(1, args.count + 1):
        question_path = choose_question(args.topic)
        if not question_path:
            print("No question found. Upload materials first or check topic name.")
            break
        meta, body = load_question(question_path)
        title = str(meta.get("题目") or question_path.stem)
        topic = str(meta.get("模块") or question_path.parent.name)
        reference = extract_reference(body)
        question = title if title.endswith(("?", "？")) else f"请回答：{title}"

        print("=" * 72)
        print(f"Round {round_no}/{args.count} | Topic: {topic}")
        print(f"Interviewer: {question}")
        print("-" * 72)
        answer = input("Candidate answer> ").strip()
        if answer.lower() == "q":
            break
        print("\nReference excerpt:")
        print(reference[: args.reference_chars])
        print("-" * 72)
        score_raw = input("Supervisor score (1-5, default 3)> ").strip()
        score = int(score_raw) if score_raw in {"1", "2", "3", "4", "5"} else 3
        feedback = input("Supervisor feedback / weak point> ").strip() or "No explicit feedback."

        update_question_progress(question_path, score)
        record_turn(conn, session_id, topic, question, answer, score, feedback, question_path)
        entries.append(
            {
                "topic": topic,
                "title": title,
                "question": question,
                "answer": answer,
                "score": score,
                "feedback": feedback,
                "source": str(question_path.relative_to(VAULT_ROOT)),
            }
        )
        print("Recorded.\n")

    refresh_memory(conn)
    note = append_session_note(session_id, entries) if entries else None
    conn.execute("UPDATE sessions SET summary=? WHERE id=?", (f"completed_turns={len(entries)}", session_id))
    conn.commit()
    conn.close()
    print(f"Completed turns: {len(entries)}")
    if note:
        print(f"Session note: {note}")
    print(f"Memory updated: {MEMORY_MD}")


def search_command(args: argparse.Namespace) -> None:
    conn = connect_db()
    rows = conn.execute(
        """
        SELECT t.session_id, t.ts, t.topic, t.question, t.score, t.feedback
        FROM turns_fts f
        JOIN turns t ON t.rowid = f.rowid
        WHERE turns_fts MATCH ?
        ORDER BY t.ts DESC
        LIMIT ?
        """,
        (args.query, args.limit),
    ).fetchall()
    for session_id, ts, topic, question, score, feedback in rows:
        print(f"[{ts}] {session_id} | {topic} | score={score}")
        print(f"Q: {question}")
        print(f"Feedback: {feedback}\n")
    conn.close()


def stats_command(_: argparse.Namespace) -> None:
    conn = connect_db()
    rows = conn.execute(
        "SELECT topic, attempts, avg_score, weak_count, last_seen FROM topic_stats ORDER BY weak_count DESC, avg_score ASC"
    ).fetchall()
    if not rows:
        print("No stats yet.")
        return
    for topic, attempts, avg_score, weak_count, last_seen in rows:
        print(f"{topic}: attempts={attempts}, avg_score={avg_score:.2f}, weak_count={weak_count}, last_seen={last_seen}")
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent-Harness + Obsidian interview assistant")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="initialize harness memory and SQLite archive")
    p_init.set_defaults(func=init_command)

    p_upload = sub.add_parser("upload", help="copy user files into raw/ and generate Obsidian interview cards")
    p_upload.add_argument("paths", nargs="+", help="files or directories to upload")
    p_upload.set_defaults(func=upload_command)

    p_practice = sub.add_parser("practice", help="start an interview practice session")
    p_practice.add_argument("--topic", help="topic/module filter, e.g. Redis or JVM")
    p_practice.add_argument("--count", type=int, default=5, help="number of interview rounds")
    p_practice.add_argument("--reference-chars", type=int, default=900, help="reference excerpt length")
    p_practice.set_defaults(func=practice_command)

    p_search = sub.add_parser("search", help="search historical interview turns")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=10)
    p_search.set_defaults(func=search_command)

    p_stats = sub.add_parser("stats", help="show weak topic statistics")
    p_stats.set_defaults(func=stats_command)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
