# MySQL 数据库配置指南

## 📋 前置要求

### 1. 安装 MySQL

**Windows:**
- 下载安装 [MySQL Community Server](https://dev.mysql.com/downloads/mysql/)
- 或使用 XAMPP / WAMP 集成环境

**Mac:**
```bash
brew install mysql
brew services start mysql
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
```

### 2. 验证 MySQL 是否运行

```bash
mysql --version
```

---

## 🔧 配置步骤

### 第一步：登录 MySQL

```bash
mysql -u root -p
```

### 第二步：创建数据库和用户（可选）

```sql
-- 创建数据库
CREATE DATABASE ai_interview CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建专用用户（推荐）
CREATE USER 'ai_interview_user'@'localhost' IDENTIFIED BY 'your_strong_password';

-- 授予权限
GRANT ALL PRIVILEGES ON ai_interview.* TO 'ai_interview_user'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 退出
EXIT;
```

### 第三步：修改配置文件

编辑 `.harness/config/harness.yaml`:

```yaml
database:
  type: "mysql"
  host: "localhost"
  port: 3306
  database: "ai_interview"
  user: "ai_interview_user"      # 或使用 "root"
  password: "your_strong_password"  # 修改为实际密码
  charset: "utf8mb4"
  pool_size: 10
  pool_recycle: 3600
```

⚠️ **安全提示**：
- 不要在生产环境使用 root 用户
- 使用强密码
- 不要将密码提交到 Git

### 第四步：安装 Python 依赖

```bash
pip install pymysql cryptography
```

### 第五步：初始化数据库

```bash
python scripts/init_database_mysql.py
```

**成功输出**:
```
============================================================
🚀 Agent Harness - 数据库初始化 (MySQL)
============================================================
📡 连接 MySQL: localhost:3306
📖 读取 schema: D:\ajie\study\AI-Knowledge\.harness\db\schema_mysql.sql
🏗️  创建数据库和表...
✅ 数据库初始化完成！

📊 已创建 8 张表:
   - learning_records: 0 条记录
   - question_metadata: 0 条记录
   - knowledge_relations: 0 条记录
   - error_analysis: 0 条记录
   - sessions: 0 条记录
   - user_profile: 4 条记录
   - review_queue: 0 条记录
   - agent_interactions: 0 条记录

📍 数据库: ai_interview @ localhost
============================================================
```

---

## 🔍 常见问题

### 问题 1: 无法连接到 MySQL

**错误**: `Can't connect to MySQL server`

**解决**:
1. 检查 MySQL 是否启动
   ```bash
   # Windows
   net start MySQL
   
   # Mac
   brew services start mysql
   
   # Linux
   sudo systemctl start mysql
   ```

2. 检查端口是否正确（默认 3306）

3. 检查防火墙设置

### 问题 2: 访问被拒绝

**错误**: `Access denied for user 'xxx'@'localhost'`

**解决**:
1. 检查用户名和密码是否正确
2. 确认用户有权限访问数据库
   ```sql
   SHOW GRANTS FOR 'ai_interview_user'@'localhost';
   ```

### 问题 3: 字符集问题

**错误**: `Incorrect string value`

**解决**:
确保数据库和表使用 `utf8mb4` 字符集:
```sql
ALTER DATABASE ai_interview CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 问题 4: Python 模块未安装

**错误**: `No module named 'pymysql'`

**解决**:
```bash
pip install pymysql cryptography
```

---

## 🔐 环境变量配置（推荐）

为了安全，可以使用环境变量存储密码：

### 1. 创建 `.env` 文件

```bash
# .env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=ai_interview
MYSQL_USER=ai_interview_user
MYSQL_PASSWORD=your_strong_password
```

### 2. 修改 `harness.yaml`

```yaml
database:
  type: "mysql"
  host: "${MYSQL_HOST}"
  port: "${MYSQL_PORT}"
  database: "${MYSQL_DATABASE}"
  user: "${MYSQL_USER}"
  password: "${MYSQL_PASSWORD}"
  charset: "utf8mb4"
```

### 3. 在代码中加载环境变量

```python
from dotenv import load_dotenv
import os

load_dotenv()

# 在 load_config() 中替换环境变量
```

---

## 📊 数据库管理工具

推荐使用以下工具管理数据库：

- **MySQL Workbench** - 官方图形化工具
- **DBeaver** - 跨平台通用工具
- **phpMyAdmin** - Web 界面
- **Navicat** - 商业工具（功能强大）

---

## 🔄 从 SQLite 迁移到 MySQL

如果你之前使用了 SQLite，可以迁移数据：

### 方法 1: 使用工具

使用 [sqlite3-to-mysql](https://github.com/techouse/sqlite3-to-mysql):

```bash
pip install sqlite3-to-mysql
sqlite3mysql --sqlite-file .harness/db/learning.db --mysql-database ai_interview
```

### 方法 2: 手动导出导入

```bash
# 1. 从 SQLite 导出数据
sqlite3 .harness/db/learning.db .dump > backup.sql

# 2. 清理 SQL（删除 SQLite 特有语法）

# 3. 导入到 MySQL
mysql -u ai_interview_user -p ai_interview < backup.sql
```

---

## ✅ 验证配置

运行测试脚本验证配置是否正确：

```bash
python .harness/tools/memory_tools.py
```

**预期输出**:
```
记忆系统工具测试
==================================================

学习统计:
  总题数: 0
  已掌握: 0
  掌握率: 0.0%
  今日学习: 0 题

薄弱模块: []

待复习题目: 0 道

==================================================
```

---

## 📝 MySQL vs SQLite 对比

| 特性 | SQLite | MySQL |
|------|--------|-------|
| **并发** | 低（写锁） | 高（行锁） |
| **性能** | 小数据快 | 大数据快 |
| **部署** | 零配置 | 需安装服务 |
| **网络访问** | 不支持 | 支持 |
| **数据量** | < 1GB | TB 级别 |
| **适用场景** | 单机开发 | **生产环境** |

---

## 🎯 下一步

配置完成后，继续实施计划：

1. ✅ 数据库配置完成
2. ⏳ 运行 `python scripts/import_questions.py` 导入题库
3. ⏳ 开始实现面试官 Agent

参考 `PLAN.md` 继续后续步骤！
