-- Agent Harness 学习数据库 Schema (MySQL)
-- 版本: 1.0.0

-- 创建数据库
CREATE DATABASE IF NOT EXISTS ai_interview
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE ai_interview;

-- 1. 学习记录表
CREATE TABLE IF NOT EXISTS learning_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    question_id VARCHAR(255) NOT NULL,
    module VARCHAR(100) NOT NULL,
    attempt_date DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- 评分维度（面试官 Agent）
    score_accuracy DECIMAL(3,2) DEFAULT 0.00,      -- 准确性 0-5
    score_completeness DECIMAL(3,2) DEFAULT 0.00,  -- 完整性 0-5
    score_depth DECIMAL(3,2) DEFAULT 0.00,         -- 深度 0-5
    score_scenario DECIMAL(3,2) DEFAULT 0.00,      -- 场景化 0-5
    overall_score DECIMAL(3,2) DEFAULT 0.00,       -- 综合得分 0-5

    -- 答题记录
    user_answer TEXT,
    answer_summary TEXT,
    weak_points JSON,                               -- JSON array
    duration_seconds INT DEFAULT 0,

    -- 追问记录
    follow_up_questions JSON,                       -- JSON array
    follow_up_answers JSON,                         -- JSON array

    -- 元数据
    session_id VARCHAR(100),
    agent_role VARCHAR(50) DEFAULT 'interviewer',

    INDEX idx_question_id (question_id),
    INDEX idx_session_id (session_id),
    INDEX idx_attempt_date (attempt_date),
    INDEX idx_module (module)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 问题元数据表
CREATE TABLE IF NOT EXISTS question_metadata (
    question_id VARCHAR(255) PRIMARY KEY,
    file_path VARCHAR(500) NOT NULL,
    module VARCHAR(100) NOT NULL,
    title VARCHAR(255),

    -- 掌握情况
    mastery_level VARCHAR(10) DEFAULT '⚪',         -- 🟢🟡🔴⚪
    total_attempts INT DEFAULT 0,
    correct_attempts INT DEFAULT 0,
    avg_score DECIMAL(3,2) DEFAULT 0.00,

    -- 复习调度（复习调度器 Agent）
    last_review DATE,
    next_review DATE,
    review_interval_days INT DEFAULT 1,
    easiness_factor DECIMAL(3,2) DEFAULT 2.50,     -- SM-2算法
    repetitions INT DEFAULT 0,

    -- 关联信息（知识关联器 Agent）
    related_questions JSON,                         -- JSON array
    prerequisite_questions JSON,                    -- JSON array: 前置知识
    keywords JSON,                                  -- JSON array

    -- 统计
    first_attempt_date DATE,
    last_attempt_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_module (module),
    INDEX idx_mastery_level (mastery_level),
    INDEX idx_next_review (next_review),
    INDEX idx_last_attempt_date (last_attempt_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 知识关联表（知识关联器 Agent）
CREATE TABLE IF NOT EXISTS knowledge_relations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    question_a VARCHAR(255) NOT NULL,
    question_b VARCHAR(255) NOT NULL,
    relation_type VARCHAR(50) NOT NULL,            -- compare/progressive/scenario/prerequisite
    strength DECIMAL(3,2) DEFAULT 0.50,            -- 0.0-1.0
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_question_a (question_a),
    INDEX idx_question_b (question_b),
    INDEX idx_relation_type (relation_type),
    UNIQUE KEY unique_relation (question_a, question_b, relation_type),
    FOREIGN KEY (question_a) REFERENCES question_metadata(question_id) ON DELETE CASCADE,
    FOREIGN KEY (question_b) REFERENCES question_metadata(question_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 错误分析表（错题分析师 Agent）
CREATE TABLE IF NOT EXISTS error_analysis (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    learning_record_id BIGINT NOT NULL,
    question_id VARCHAR(255) NOT NULL,

    -- 错误分类
    error_type VARCHAR(50),                        -- concept_confusion/detail_missing/scenario_lack/prerequisite_gap
    root_cause TEXT,
    missing_knowledge JSON,                        -- JSON array

    -- 改进建议
    remedial_actions JSON,                         -- JSON array
    recommended_questions JSON,                    -- JSON array
    comparison_table TEXT,                         -- Markdown

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_learning_record_id (learning_record_id),
    INDEX idx_question_id (question_id),
    INDEX idx_error_type (error_type),
    FOREIGN KEY (learning_record_id) REFERENCES learning_records(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES question_metadata(question_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 会话记录表
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,

    -- 统计
    total_questions INT DEFAULT 0,
    new_questions INT DEFAULT 0,
    review_questions INT DEFAULT 0,
    avg_score DECIMAL(3,2) DEFAULT 0.00,

    -- Agent 参与
    primary_agent VARCHAR(50),                     -- interviewer/scheduler/supervisor
    assisting_agents JSON,                         -- JSON array

    -- 用户状态（陪练伙伴 Agent）
    user_mood VARCHAR(20),                         -- good/neutral/tired
    breaks_taken INT DEFAULT 0,

    -- 元数据
    notes TEXT,

    INDEX idx_start_time (start_time),
    INDEX idx_primary_agent (primary_agent)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. 用户画像表（监督助手 + 陪练伙伴）
CREATE TABLE IF NOT EXISTS user_profile (
    `key` VARCHAR(100) PRIMARY KEY,
    `value` TEXT NOT NULL,
    category VARCHAR(50),                          -- strength/weakness/preference/pattern
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. 复习队列表（复习调度器 Agent）
CREATE TABLE IF NOT EXISTS review_queue (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    question_id VARCHAR(255) NOT NULL,
    scheduled_date DATE NOT NULL,
    priority INT DEFAULT 0,                        -- 计算优先级
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_question_id (question_id),
    INDEX idx_scheduled_date (scheduled_date),
    INDEX idx_is_completed (is_completed),
    FOREIGN KEY (question_id) REFERENCES question_metadata(question_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Agent 协作日志
CREATE TABLE IF NOT EXISTS agent_interactions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    from_agent VARCHAR(50) NOT NULL,
    to_agent VARCHAR(50) NOT NULL,
    message_type VARCHAR(50) NOT NULL,             -- request/response/notification
    content JSON,                                  -- JSON

    INDEX idx_session_id (session_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_from_agent (from_agent),
    INDEX idx_to_agent (to_agent),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入初始用户画像数据
INSERT INTO user_profile (`key`, `value`, category) VALUES
('total_study_days', '0', 'pattern'),
('avg_daily_questions', '0', 'pattern'),
('best_study_time', 'unknown', 'pattern'),
('learning_style', 'unknown', 'preference')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;
