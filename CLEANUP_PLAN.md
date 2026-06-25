# 文档规范化清理方案

> **目标**: 精简文档，保留必要内容，删除过时/重复文档  
> **日期**: 2026-06-25

---

## 📊 当前文档统计

**总计**: 23 个 Markdown 文件（根目录）

---

## 🗂️ 文档分类与处理方案

### ✅ 保留 - 核心文档（7个）

| 文件 | 大小 | 用途 | 处理 |
|------|------|------|------|
| `README.md` | 新建 | 项目首页，快速导航 | ✅ 保留 |
| `CLAUDE.md` | 18KB | 项目完整上下文（开发必读） | ✅ 保留 |
| `AGENTS.md` | 14KB | Agent 架构设计文档 | ✅ 保留 |
| `PLAN.md` | 34KB | 完整实施计划和进度追踪 | ✅ 保留 |
| `ARCHITECTURE_MINDMAP.md` | 17KB | 架构思维导图 | ✅ 保留 |
| `QUICKSTART_FOR_BEGINNERS.md` | 21KB | 新手入门指南 | ✅ 保留 |
| `requirements.txt` | 692B | Python 依赖 | ✅ 保留 |

### ✅ 保留 - 配置指南（2个）

| 文件 | 大小 | 用途 | 处理 |
|------|------|------|------|
| `MYSQL_SETUP.md` | 5.7KB | MySQL 数据库配置指南 | ✅ 保留 |
| `GIT_RULES.md` | 5.6KB | Git 工作流规范 | ✅ 保留 |

### ✅ 保留 - 对比分析（2个）

| 文件 | 大小 | 用途 | 处理 |
|------|------|------|------|
| `COMPARISON_REPORT_V2.md` | 12KB | 与生产级 Agent Harness 对比（最新） | ✅ 保留 |
| `FEATURE_COMPARISON.md` | 12KB | 目录迁移前后功能对比 | ✅ 保留 |

### ✅ 保留 - 实施记录（3个）

| 文件 | 大小 | 用途 | 处理 |
|------|------|------|------|
| `MIGRATION_SUMMARY.md` | 5.8KB | 目录结构迁移总结 | ✅ 保留 |
| `HARNESS_IMPLEMENTATION.md` | 15KB | Agent Harness 实施路线图 | ✅ 保留 |
| `HARNESS_COMPLETION_REPORT.md` | 9.9KB | 实施完成报告 | ✅ 保留 |

### ✅ 归档 - 可选文档（1个）

| 文件 | 大小 | 用途 | 处理 |
|------|------|------|------|
| `LANGCHAIN_INTEGRATION.md` | 9.8KB | LangChain/LangGraph 集成指南 | ✅ 保留<br>（未来可能需要） |

### ❌ 删除 - 重复文档（1个）

| 文件 | 大小 | 原因 | 处理 |
|------|------|------|------|
| `COMPARISON_REPORT.md` | 18KB | V2 版本已覆盖 | ❌ 删除 |

### ❌ 删除 - 过时文档（8个）

| 文件 | 大小 | 原因 | 处理 |
|------|------|------|------|
| `AI 陪练模式.md` | 1.2KB | 指向已删除的 `interview_harness.py` | ❌ 删除 |
| `Agent Harness 面试助手.md` | 1.8KB | 指向已删除的 `interview_harness.py` | ❌ 删除 |
| `使用指南.md` | 4.5KB | 旧版 Obsidian 背题系统指南，已过时 | ❌ 删除 |
| `学习笔记模板.md` | 570B | Obsidian 模板，与新架构无关 | ❌ 删除 |
| `背题进度仪表盘.md` | 3.5KB | Obsidian 仪表盘，与新架构无关 | ❌ 删除 |
| `高频考点.md` | 984B | Obsidian 笔记，与新架构无关 | ❌ 删除 |
| `AI_CONFIG.md` | 3.5KB | 旧版 AI 配置，已被 `.harness/config/harness.yaml` 取代 | ❌ 删除 |
| `CODEX_GOALS.md` | 9.8KB | Codex 命令清单，已被 README.md 取代 | ❌ 删除 |

---

## 📋 清理执行计划

### 步骤 1: 创建归档目录

```bash
mkdir -p docs/archive
```

### 步骤 2: 删除重复文档

```bash
git rm "COMPARISON_REPORT.md"
```

### 步骤 3: 删除过时文档

```bash
git rm "AI 陪练模式.md"
git rm "Agent Harness 面试助手.md"
git rm "使用指南.md"
git rm "学习笔记模板.md"
git rm "背题进度仪表盘.md"
git rm "高频考点.md"
git rm "AI_CONFIG.md"
git rm "CODEX_GOALS.md"
```

### 步骤 4: 提交清理

```bash
git commit -m "docs: 清理过时和重复的文档

- 删除 COMPARISON_REPORT.md（V2 版本已覆盖）
- 删除 8 个过时文档（旧版 Obsidian 系统、已删除脚本的使用指南）
- 创建 README.md 作为项目首页
- 保留 15 个核心文档

清理后文档结构：
- 核心文档：7 个
- 配置指南：2 个
- 对比分析：2 个
- 实施记录：3 个
- 集成指南：1 个"
```

---

## 📊 清理前后对比

| 项目 | 清理前 | 清理后 | 变化 |
|------|--------|--------|------|
| **Markdown 文档** | 23 个 | 16 个 | -7 个 |
| **文档总大小** | ~212KB | ~175KB | -37KB |
| **文档清晰度** | ⚠️ 混杂 | ✅ 清晰 | 提升 |

---

## ✅ 保留的文档结构

```
AI-Knowledge/
├── README.md                          # 项目首页（新建）
│
├── 核心文档/
│   ├── CLAUDE.md                      # 项目完整上下文
│   ├── AGENTS.md                      # Agent 架构设计
│   ├── PLAN.md                        # 实施计划
│   ├── ARCHITECTURE_MINDMAP.md        # 架构思维导图
│   └── QUICKSTART_FOR_BEGINNERS.md    # 新手入门
│
├── 配置指南/
│   ├── MYSQL_SETUP.md                 # MySQL 配置
│   └── GIT_RULES.md                   # Git 规范
│
├── 对比分析/
│   ├── COMPARISON_REPORT_V2.md        # Agent Harness 对比
│   └── FEATURE_COMPARISON.md          # 功能对比
│
├── 实施记录/
│   ├── MIGRATION_SUMMARY.md           # 迁移总结
│   ├── HARNESS_IMPLEMENTATION.md      # 实施路线图
│   └── HARNESS_COMPLETION_REPORT.md   # 完成报告
│
└── 集成指南/
    └── LANGCHAIN_INTEGRATION.md       # LangChain 集成
```

---

## 🎯 清理收益

1. ✅ **降低认知负担** - 从 23 个文档减少到 16 个
2. ✅ **提升文档质量** - 删除过时内容，避免混淆
3. ✅ **清晰的导航** - README.md 提供完整的文档索引
4. ✅ **便于维护** - 文档职责清晰，更新路径明确
5. ✅ **新人友好** - 一目了然的文档结构

---

## ⚠️ 注意事项

1. **Git 提交分离** - 删除操作单独提交，便于回滚
2. **备份确认** - Git 历史中可恢复所有删除的文件
3. **链接检查** - 确认没有其他文件引用被删除的文档
4. **README 导航** - 新的 README.md 提供完整的文档索引

---

## 📝 执行检查清单

- [ ] 创建 README.md
- [ ] 删除 COMPARISON_REPORT.md（重复）
- [ ] 删除 8 个过时文档
- [ ] 检查是否有其他文件引用被删除的文档
- [ ] 提交清理
- [ ] 更新 CLAUDE.md 的文档索引（如有需要）

---

**清理完成后，项目将拥有清晰、精简、易维护的文档结构！**
