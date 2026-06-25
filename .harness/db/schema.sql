-- Agent Harness 学习数据库 Schema
-- 版本: 1.0.0

-- 1. 学习记录表
CREATE TABLE IF NOT EXISTS learning_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NOT NULL,
    module TEXT NOT NULL,
    attempt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 评分维度（面试官 Agent）
    score_accuracy REAL,        -- 准确性 0-5
    score_completeness REAL,    -- 完整性 0-5
    score_depth REAL,           -- 深度 0-5
    score_scenario REAL,        -- 场景化 0-5
    overall_score REAL,         -- 综合得分 0-5

    -- 答题记录
    user_answer TEXT,
    answer_summary TEXT,
    weak_points TEXT,           -- JSON array
    duration_seconds INTEGER,

    -- 追问记录
    follow_up_questions TEXT,   -- JSON array
    follow_up_answers TEXT,     -- JSON array

    -- 元数据
    session_id TEXT,
    agent_role TEXT,            -- interviewer/scheduler

    FOREIGN KEY (question_id) REFERENCES question_metadata(question_id)
);

-- 2. 问题元数据表
CREATE TABLE IF NOT EXISTS question_metadata (
    question_id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    module TEXT NOT NULL,
    title TEXT,

    -- 掌握情况
    mastery_level TEXT DEFAULT '⚪',  -- 🟢🟡🔴⚪
    total_attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    avg_score REAL DEFAULT 0,

    -- 复习调度（复习调度器 Agent）
    last_review DATE,
    next_review DATE,
    review_interval_days INTEGER DEFAULT 1,
    easiness_factor REAL DEFAULT 2.5,  -- SM-2算法
    repetitions INTEGER DEFAULT 0,

    -- 关联信息（知识关联器 Agent）
    related_questions TEXT,         -- JSON array
    prerequisite_questions TEXT,    -- JSON array: 前置知识
    keywords TEXT,                  -- JSON array

    -- 统计
    first_attempt_date DATE,
    last_attempt_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 知识关联表（知识关联器 Agent）
CREATE TABLE IF NOT EXISTS knowledge_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_a TEXT NOT NULL,
    question_b TEXT NOT NULL,
    relation_type TEXT NOT NULL,    -- compare/progressive/scenario/prerequisite
    strength REAL DEFAULT 0.5,      -- 0.0-1.0
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (question_a) REFERENCES question_metadata(question_id),
    FOREIGN KEY (question_b) REFERENCES question_metadata(question_id),
    UNIQUE(question_a, question_b, relation_type)
);

-- 4. 错误分析表（错题分析师 Agent）
CREATE TABLE IF NOT EXISTS error_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    learning_record_id INTEGER NOT NULL,
    question_id TEXT NOT NULL,

    -- 错误分类
    error_type TEXT,                -- concept_confusion/detail_missing/scenario_lack/prerequisite_gap
    root_cause TEXT,
    missing_knowledge TEXT,         -- JSON array

    -- 改进建议
    remedial_actions TEXT,          -- JSON array
    recommended_questions TEXT,     -- JSON array
    comparison_table TEXT,          -- Markdown

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (learning_record_id) REFERENCES learning_records(id),
    FOREIGN KEY (question_id) REFERENCES question_metadata(question_id)
);

-- 5. 会话记录表
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,

    -- 统计
    total_questions INTEGER DEFAULT 0,
    new_questions INTEGER DEFAULT 0,
    review_questions INTEGER DEFAULT 0,
    avg_score REAL DEFAULT 0,

    -- Agent 参与
    primary_agent TEXT,             -- interviewer/scheduler/supervisor
    assisting_agents TEXT,          -- JSON array

    -- 用户状态（陪练伙伴 Agent）
    user_mood TEXT,                 -- good/neutral/tired
    breaks_taken INTEGER DEFAULT 0,

    -- 元数据
    notes TEXT
);

-- 6. 用户画像表（监督助手 + 陪练伙伴）
CREATE TABLE IF NOT EXISTS user_profile (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    category TEXT,                  -- strength/weakness/preference/pattern
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. 复习队列表（复习调度器 Agent）
CREATE TABLE IF NOT EXISTS review_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NOT NULL,
    scheduled_date DATE NOT NULL,
    priority INTEGER DEFAULT 0,     -- 计算优先级
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (question_id) REFERENCES question_metadata(question_id)
);

-- 8. Agent 协作日志
CREATE TABLE IF NOT EXISTS agent_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    from_agent TEXT NOT NULL,
    to_agent TEXT NOT NULL,
    message_type TEXT NOT NULL,     -- request/response/notification
    content TEXT,                   -- JSON

    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_learning_records_question ON learning_records(question_id);
CREATE INDEX IF NOT EXISTS idx_learning_records_session ON learning_records(session_id);
CREATE INDEX IF NOT EXISTS idx_learning_records_date ON learning_records(attempt_date);
CREATE INDEX IF NOT EXISTS idx_question_metadata_module ON question_metadata(module);
CREATE INDEX IF NOT EXISTS idx_question_metadata_mastery ON question_metadata(mastery_level);
CREATE INDEX IF NOT EXISTS idx_question_metadata_next_review ON question_metadata(next_review);
CREATE INDEX IF NOT EXISTS idx_review_queue_date ON review_queue(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_review_queue_completed ON review_queue(is_completed);
CREATE INDEX IF NOT EXISTS idx_knowledge_relations_qa ON knowledge_relations(question_a);
CREATE INDEX IF NOT EXISTS idx_knowledge_relations_qb ON knowledge_relations(question_b);
