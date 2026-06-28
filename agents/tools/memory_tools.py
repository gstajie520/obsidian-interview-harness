#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""记忆系统工具：保存学习记录、掌握度和复习计划。

这里属于 Agent Harness 的“中期记忆”：
- 短期记忆在 AgentLoop 的 messages 里，只活在本轮对话。
- 中期记忆写入数据库，跨会话保留学习记录。
- 长期记忆可以放在 Markdown 文件里，后续再扩展。

默认使用 SQLite，开箱即用；如果配置 `database.type: mysql`，会尝试切换
到 MySQL。上层 Agent 调用本文件函数时，不需要关心底层数据库类型。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover - 只在缺少 PyYAML 时触发。
    yaml = None


ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / ".harness" / "config" / "harness.yaml"
SQLITE_PATH = ROOT_DIR / ".harness" / "db" / "learning.db"


def load_config() -> Dict[str, Any]:
    """加载主配置文件；失败时返回空配置。"""
    if yaml is None or not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            loaded = yaml.safe_load(file) or {}
    except Exception:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def get_db_type() -> str:
    """返回数据库类型，默认是 sqlite。"""
    return load_config().get("database", {}).get("type", "sqlite").lower()


_DIALECT = get_db_type()


def _ph(sql: str) -> str:
    """把统一使用的 `?` 占位符转换为当前数据库方言。

    SQLite 使用 `?` 作为参数占位符，MySQL 驱动使用 `%s`。
    业务 SQL 统一写 `?`，这里集中转换，避免到处写分支判断。
    """
    if _DIALECT == "mysql":
        return sql.replace("?", "%s")
    return sql


if _DIALECT == "mysql":
    _TODAY = "CURDATE()"
    _INSERT_IGNORE = "INSERT IGNORE"

    def _days_overdue_expr(column: str) -> str:
        # MySQL 有内置 DATEDIFF 函数，可以直接算两个日期差几天。
        return f"DATEDIFF({_TODAY}, {column})"

else:
    _TODAY = "DATE('now')"
    _INSERT_IGNORE = "INSERT OR IGNORE"

    def _days_overdue_expr(column: str) -> str:
        # SQLite 没有 DATEDIFF，用 JULIANDAY 做日期差。
        return f"JULIANDAY({_TODAY}) - JULIANDAY({column})"


def get_connection() -> Any:
    """获取数据库连接。

    SQLite 会自动创建表；MySQL 需要用户提前建库和建表。
    """
    if _DIALECT == "mysql":
        config = load_config()
        database = config.get("database", {})
        # pymysql 只在真正使用 MySQL 时才导入。这样默认 SQLite 用户不需要
        # 安装 MySQL 依赖也能运行。
        import pymysql
        import pymysql.cursors

        return pymysql.connect(
            host=database.get("host", "localhost"),
            port=int(database.get("port", 3306)),
            user=database.get("user", "root"),
            password=database.get("password", "root"),
            database=database.get("database", "ai_interview"),
            charset=database.get("charset", "utf8mb4"),
            cursorclass=pymysql.cursors.DictCursor,
        )

    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SQLITE_PATH))
    # row_factory 让查询结果能像 dict 一样按列名读取，后面转换更方便。
    conn.row_factory = sqlite3.Row
    _ensure_sqlite_schema(conn)
    return conn


def init_question_metadata(
    question_id: str,
    file_path: str,
    module: str,
    title: str,
) -> bool:
    """初始化题目元数据；返回是否实际新增。

    这个函数只负责登记“题目基本信息”，不代表用户已经答过题。
    返回 bool 是为了让导入脚本能区分：
    - True：数据库里原来没有这道题，本次真的新增了。
    - False：这道题已经存在，本次被忽略。
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        _ph(
            f"{_INSERT_IGNORE} INTO question_metadata "
            "(question_id, file_path, module, title) VALUES (?, ?, ?, ?)"
        ),
        (question_id, file_path, module, title),
    )
    # rowcount 表示本次 SQL 影响了几行；可以类比 Java JDBC 里
    # executeUpdate() 返回的更新行数。INSERT OR IGNORE 遇到重复主键时
    # 不会插入新行，所以 rowcount 会是 0。
    inserted = int(getattr(cursor, "rowcount", 0) or 0) > 0
    conn.commit()
    conn.close()
    return inserted


def get_question_metadata(question_id: str) -> Optional[Dict[str, Any]]:
    """读取单个题目的元数据。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        _ph("SELECT * FROM question_metadata WHERE question_id = ?"),
        (question_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _row_to_dict(row)


def update_mastery_level(question_id: str, mastery_level: str) -> None:
    """手动更新某道题的掌握状态。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        _ph(
            "UPDATE question_metadata SET mastery_level = ?, "
            "updated_at = CURRENT_TIMESTAMP WHERE question_id = ?"
        ),
        (mastery_level, question_id),
    )
    conn.commit()
    conn.close()


def get_weak_modules(limit: int = 5) -> List[str]:
    """返回已作答题目中平均得分最低的模块，用于优先复习。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        _ph(
            """
            SELECT module, AVG(avg_score) AS avg_score, SUM(total_attempts) AS attempts
            FROM question_metadata
            WHERE total_attempts > 0
            GROUP BY module
            ORDER BY avg_score ASC, attempts DESC
            LIMIT ?
            """
        ),
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    # 这里用列表推导式把多行查询结果转成模块名列表。
    return [_row_to_dict(row)["module"] for row in rows]


def add_learning_record(
    question_id: str,
    module: str,
    user_answer: str,
    scores: Dict[str, float],
    session_id: str,
    weak_points: Optional[List[str]] = None,
    duration_seconds: int = 0,
) -> int:
    """新增一条学习记录，并同步更新题目统计。"""
    conn = get_connection()
    cursor = conn.cursor()

    overall_score = _overall_score(scores)

    # 学习记录可能来自尚未导入元数据的题目，先确保元数据行存在。
    # f-string 是 Python 字符串模板写法，类似 Java 里 String.format，
    # 但更直观：f"hello {name}"。
    cursor.execute(
        _ph(
            f"{_INSERT_IGNORE} INTO question_metadata "
            "(question_id, file_path, module, title) VALUES (?, ?, ?, ?)"
        ),
        (question_id, "", module, question_id),
    )

    cursor.execute(
        _ph(
            """
            INSERT INTO learning_records (
                question_id, module, user_answer,
                score_accuracy, score_completeness, score_depth, score_scenario,
                overall_score, weak_points, duration_seconds, session_id,
                agent_role
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        ),
        (
            question_id,
            module,
            user_answer,
            scores.get("accuracy", 0),
            scores.get("completeness", 0),
            scores.get("depth", 0),
            scores.get("scenario", 0),
            overall_score,
            json.dumps(weak_points or [], ensure_ascii=False),
            duration_seconds,
            session_id,
            "interviewer",
        ),
    )
    record_id = int(cursor.lastrowid or 0)

    cursor.execute(
        _ph(
            f"""
            UPDATE question_metadata
            SET total_attempts = total_attempts + 1,
                correct_attempts = correct_attempts
                    + (CASE WHEN ? >= 3.0 THEN 1 ELSE 0 END),
                avg_score = (
                    SELECT AVG(overall_score)
                    FROM learning_records
                    WHERE question_id = ?
                ),
                mastery_level = ?,
                last_attempt_date = {_TODAY},
                last_review = {_TODAY},
                updated_at = CURRENT_TIMESTAMP
            WHERE question_id = ?
            """
        ),
        (
            overall_score,
            question_id,
            _mastery_from_score(overall_score),
            question_id,
        ),
    )

    conn.commit()
    conn.close()
    return record_id


def calculate_next_review(question_id: str, performance_score: float) -> None:
    """使用 SM-2 算法计算下一次复习日期。

    performance_score 是 0-5 分。小于 3 分表示没掌握，需要明天再复习；
    3 分及以上会逐步拉长复习间隔。
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        _ph(
            f"{_INSERT_IGNORE} INTO question_metadata "
            "(question_id, file_path, module, title) VALUES (?, ?, ?, ?)"
        ),
        (question_id, "", "unknown", question_id),
    )
    cursor.execute(
        _ph(
            "SELECT easiness_factor, repetitions, review_interval_days "
            "FROM question_metadata WHERE question_id = ?"
        ),
        (question_id,),
    )
    row = _row_to_dict(cursor.fetchone()) or {}

    easiness = float(row.get("easiness_factor") or 2.5)
    repetitions = int(row.get("repetitions") or 0)
    interval = int(row.get("review_interval_days") or 1)

    new_easiness = easiness + (
        0.1
        - (5 - performance_score)
        * (0.08 + (5 - performance_score) * 0.02)
    )
    # SM-2 算法要求 easiness 保持在合理范围内，避免间隔过短或过长。
    new_easiness = max(1.3, min(3.0, new_easiness))

    if performance_score < 3:
        new_repetitions = 0
        new_interval = 1
    else:
        new_repetitions = repetitions + 1
        if new_repetitions == 1:
            new_interval = 1
        elif new_repetitions == 2:
            new_interval = 6
        else:
            new_interval = max(1, int(interval * new_easiness))

    next_review = (date.today() + timedelta(days=new_interval)).isoformat()
    cursor.execute(
        _ph(
            """
            UPDATE question_metadata
            SET easiness_factor = ?, repetitions = ?,
                review_interval_days = ?, next_review = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE question_id = ?
            """
        ),
        (
            new_easiness,
            new_repetitions,
            new_interval,
            next_review,
            question_id,
        ),
    )
    conn.commit()
    conn.close()


def get_due_reviews(limit: int = 20) -> List[Dict[str, Any]]:
    """获取已经到期、需要复习的题目。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        _ph(
            f"""
            SELECT
                question_id, module, title,
                mastery_level, last_review, next_review,
                {_days_overdue_expr("next_review")} AS days_overdue
            FROM question_metadata
            WHERE next_review IS NOT NULL AND next_review <= {_TODAY}
            ORDER BY days_overdue DESC, avg_score ASC
            LIMIT ?
            """
        ),
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_dict(row) for row in rows]


def create_session(session_id: str, primary_agent: str) -> str:
    """创建一个学习会话。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        _ph(
            f"{_INSERT_IGNORE} INTO sessions "
            "(session_id, primary_agent) VALUES (?, ?)"
        ),
        (session_id, primary_agent),
    )
    conn.commit()
    conn.close()
    return session_id


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """读取单个学习会话。

    这个函数给 FastAPI 层使用。API 收到 `/api/session/{id}` 请求后，
    不应该自己拼 SQL，而是通过记忆工具层读取数据库，保持分层清晰。
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        _ph("SELECT * FROM sessions WHERE session_id = ?"),
        (session_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _row_to_dict(row)


def delete_session(session_id: str) -> bool:
    """删除学习会话，返回是否真的删除了数据。

    rowcount 的含义和 `init_question_metadata()` 中一样：可以类比
    Java JDBC 的 executeUpdate() 返回值。删除到 1 行表示会话存在。
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        _ph("DELETE FROM sessions WHERE session_id = ?"),
        (session_id,),
    )
    deleted = int(getattr(cursor, "rowcount", 0) or 0) > 0
    conn.commit()
    conn.close()
    return deleted


def update_session_stats(session_id: str, stats: Dict[str, Any]) -> None:
    """更新会话结束后的统计数据。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        _ph(
            """
            UPDATE sessions
            SET total_questions = ?, new_questions = ?,
                review_questions = ?, avg_score = ?,
                end_time = CURRENT_TIMESTAMP
            WHERE session_id = ?
            """
        ),
        (
            stats.get("total", 0),
            stats.get("new", 0),
            stats.get("review", 0),
            stats.get("avg_score", 0),
            session_id,
        ),
    )
    conn.commit()
    conn.close()


def log_agent_interaction(
    from_agent: str,
    to_agent: str,
    message_type: str,
    content: Any,
    session_id: Optional[str] = None,
) -> None:
    """记录一条 Agent 协作事件，作为多 Agent 编排的审计日志。"""
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_orchestration_tables(cursor)
    cursor.execute(
        _ph(
            """
            INSERT INTO agent_interactions
            (session_id, from_agent, to_agent, message_type, content)
            VALUES (?, ?, ?, ?, ?)
            """
        ),
        (
            session_id,
            from_agent,
            to_agent,
            message_type,
            json.dumps(content, ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()


def get_agent_interactions(
    session_id: Optional[str] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """读取 Agent 协作事件。"""
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_orchestration_tables(cursor)
    if session_id:
        cursor.execute(
            _ph(
                """
                SELECT session_id, from_agent, to_agent, message_type,
                    content, timestamp
                FROM agent_interactions
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """
            ),
            (session_id, limit),
        )
    else:
        cursor.execute(
            _ph(
                """
                SELECT session_id, from_agent, to_agent, message_type,
                    content, timestamp
                FROM agent_interactions
                ORDER BY timestamp DESC
                LIMIT ?
                """
            ),
            (limit,),
        )
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_dict(row) or {} for row in rows]


def save_orchestration_run(
    question_id: str,
    result: Dict[str, Any],
    session_id: Optional[str] = None,
    record_id: Optional[int] = None,
) -> int:
    """保存一次编排闭环结果。"""
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_orchestration_tables(cursor)
    payload = {
        "question_id": question_id,
        "analysis_error_type": result.get("analysis", {}).get("error_type"),
        "schedule_status": result.get("schedule", {}).get("status"),
        "recommendation_type": result.get("recommendation", {}).get("report_type"),
        "encouragement_status": result.get("encouragement", {}).get("status"),
        "include_report": result.get("recommendation", {}).get("status")
        == "ok",
    }
    cursor.execute(
        _ph(
            """
            INSERT INTO orchestration_runs
            (session_id, question_id, learning_record_id,
             report_type, payload, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """
        ),
        (
            session_id,
            question_id,
            record_id,
            result.get("recommendation", {}).get("report_type") or "",
            json.dumps(payload, ensure_ascii=False),
            "ok",
        ),
    )
    run_id = int(cursor.lastrowid or 0)
    conn.commit()
    conn.close()
    return run_id


def get_orchestration_runs(
    session_id: Optional[str] = None,
    question_id: Optional[str] = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """查询编排历史，支持按会话/题目筛选。"""
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_orchestration_tables(cursor)
    if session_id and question_id:
        cursor.execute(
            _ph(
                """
                SELECT *
                FROM orchestration_runs
                WHERE session_id = ? AND question_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """
            ),
            (session_id, question_id, limit),
        )
    elif session_id:
        cursor.execute(
            _ph(
                """
                SELECT *
                FROM orchestration_runs
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """
            ),
            (session_id, limit),
        )
    elif question_id:
        cursor.execute(
            _ph(
                """
                SELECT *
                FROM orchestration_runs
                WHERE question_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """
            ),
            (question_id, limit),
        )
    else:
        cursor.execute(
            _ph(
                """
                SELECT *
                FROM orchestration_runs
                ORDER BY created_at DESC
                LIMIT ?
                """
            ),
            (limit,),
        )
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_dict(row) or {} for row in rows]


def get_learning_stats() -> Dict[str, Any]:
    """获取整体学习统计。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT mastery_level FROM question_metadata")
    levels = [
        (_row_to_dict(row) or {}).get("mastery_level", "new")
        for row in cursor.fetchall()
    ]

    cursor.execute(
        f"SELECT COUNT(*) AS recent_count FROM learning_records "
        f"WHERE DATE(attempt_date) = {_TODAY}"
    )
    today_row = _row_to_dict(cursor.fetchone()) or {}
    conn.close()

    total = len(levels)
    mastered = _count_levels(levels, {"mastered", "green"})
    reviewing = _count_levels(levels, {"reviewing", "yellow"})
    learning = _count_levels(levels, {"learning", "red"})
    untouched = _count_levels(levels, {"new", "untouched", ""})

    return {
        "total": total,
        "mastered": mastered,
        "reviewing": reviewing,
        "learning": learning,
        "untouched": untouched,
        "today_count": int(today_row.get("recent_count", 0) or 0),
        "mastery_rate": mastered / total if total > 0 else 0,
    }


def _ensure_sqlite_schema(conn: sqlite3.Connection) -> None:
    """SQLite 首次使用时自动建表。"""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name='question_metadata'"
    )
    if cursor.fetchone():
        return
    conn.executescript(_DEFAULT_SQLITE_SCHEMA)
    conn.commit()


def _ensure_orchestration_tables(cursor: Any) -> None:
    """确保编排相关日志表存在（延迟创建，兼容旧库）。"""
    if _DIALECT == "mysql":
        # MySQL 初始化通常走 schema.sql，避免在运行时动态建表。
        return
    if not isinstance(cursor, sqlite3.Cursor):
        return
    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='agent_interactions'
        """
    )
    if cursor.fetchone():
        return
    cursor.executescript(_ORCHESTRATION_TABLES_SCHEMA)


def _row_to_dict(row: Any) -> Optional[Dict[str, Any]]:
    """把 sqlite3.Row 或 MySQL dict 统一转为普通 dict。"""
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    # sqlite3.Row 可以直接交给 dict() 转换成普通字典。
    return dict(row)


def _overall_score(scores: Dict[str, float]) -> float:
    """计算四维评分的平均分。"""
    if not scores:
        return 0.0
    values = [float(value) for value in scores.values()]
    return sum(values) / len(values)


def _mastery_from_score(score: float) -> str:
    """根据平均分转换为掌握状态。"""
    if score >= 4:
        return "mastered"
    if score >= 3:
        return "reviewing"
    if score > 0:
        return "learning"
    return "new"


def _count_levels(levels: List[str], expected: set[str]) -> int:
    """统计某些掌握状态的数量。"""
    return sum(1 for level in levels if str(level or "").lower() in expected)


_DEFAULT_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS question_metadata (
    question_id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    module TEXT NOT NULL,
    title TEXT,
    mastery_level TEXT DEFAULT 'new',
    total_attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    avg_score REAL DEFAULT 0.0,
    last_review TEXT,
    next_review TEXT,
    review_interval_days INTEGER DEFAULT 1,
    easiness_factor REAL DEFAULT 2.5,
    repetitions INTEGER DEFAULT 0,
    related_questions TEXT,
    keywords TEXT,
    first_attempt_date TEXT,
    last_attempt_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learning_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NOT NULL,
    module TEXT NOT NULL,
    attempt_date TEXT DEFAULT CURRENT_TIMESTAMP,
    score_accuracy REAL DEFAULT 0.0,
    score_completeness REAL DEFAULT 0.0,
    score_depth REAL DEFAULT 0.0,
    score_scenario REAL DEFAULT 0.0,
    overall_score REAL DEFAULT 0.0,
    user_answer TEXT,
    weak_points TEXT,
    duration_seconds INTEGER DEFAULT 0,
    session_id TEXT,
    agent_role TEXT DEFAULT 'interviewer'
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    start_time TEXT DEFAULT CURRENT_TIMESTAMP,
    end_time TEXT,
    total_questions INTEGER DEFAULT 0,
    new_questions INTEGER DEFAULT 0,
    review_questions INTEGER DEFAULT 0,
    avg_score REAL DEFAULT 0.0,
    primary_agent TEXT,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_lr_question ON learning_records(question_id);
CREATE INDEX IF NOT EXISTS idx_lr_session ON learning_records(session_id);
CREATE INDEX IF NOT EXISTS idx_qm_module ON question_metadata(module);
CREATE INDEX IF NOT EXISTS idx_qm_next_review ON question_metadata(next_review);
"""

_ORCHESTRATION_TABLES_SCHEMA = """
CREATE TABLE IF NOT EXISTS agent_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    from_agent TEXT NOT NULL,
    to_agent TEXT NOT NULL,
    message_type TEXT NOT NULL,
    content TEXT
);

CREATE INDEX IF NOT EXISTS idx_ai_session ON agent_interactions(session_id);

CREATE TABLE IF NOT EXISTS orchestration_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    question_id TEXT NOT NULL,
    learning_record_id INTEGER,
    report_type TEXT,
    payload TEXT,
    status TEXT DEFAULT 'ok',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_orch_session ON orchestration_runs(session_id);
CREATE INDEX IF NOT EXISTS idx_orch_question ON orchestration_runs(question_id);
"""


if __name__ == "__main__":
    print(f"记忆工具自检，当前数据库: {_DIALECT}")
    print("=" * 40)
    stats = get_learning_stats()
    print(f"总题数: {stats['total']}")
    print(f"掌握率: {stats['mastery_rate'] * 100:.1f}%")
    print(f"今日学习: {stats['today_count']} 题")
    print(f"薄弱模块: {get_weak_modules(3)}")
    print(f"待复习数量: {len(get_due_reviews(5))}")
