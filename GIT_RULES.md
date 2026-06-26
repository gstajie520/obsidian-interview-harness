# Git 工作流规则

> **适用场景**: 单人开发项目  
> **更新日期**: 2026-06-26

---

## 📋 基本原则

本项目目前为**单人开发**，采用简化的 Git 工作流，直接在 `main` 分支上提交。

---

## ✅ 提交规范

### 分支策略

- ✅ **直接在 main 分支开发** - 无需创建 feature 分支
- ✅ **每完成一个功能点就提交** - 保持提交频率
- ❌ **不需要 Pull Request** - 直接 commit 和 push

### AI 执行硬规则

AI 编码助手执行 `git commit` 前必须遵守下面规则：

- 必须先读取本文件，再决定提交信息。
- 提交信息必须使用中文约定式提交。
- 提交信息格式必须是：`<type>(<scope>): <中文描述>`。
- `scope` 必须填写，只允许小写英文、数字、点号、短横线或下划线，例如 `agents`、`agent-loop`、`git-rules`。
- subject 必须包含中文，禁止纯英文 subject。
- `git add`、`git commit`、`git reset`、`git config` 等会写入 `.git` 的命令禁止并行执行，只能按顺序单独执行。
- 提交后必须执行 `git status --short` 和 `git log -1 --oneline`，确认工作区状态和提交信息。

### Commit Message 格式

使用中文约定式提交（Conventional Commits）：

```text
<type>(<scope>): <中文描述>

<body>

<footer>
```

#### Type 类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(tool-registry): 实现工具注册系统` |
| `fix` | Bug 修复 | `fix(config): 修复 MySQL 连接配置` |
| `docs` | 文档更新 | `docs(plan): 更新实施计划` |
| `style` | 代码格式（不影响逻辑） | `style(agents): 格式化 Python 代码` |
| `refactor` | 重构 | `refactor(agent-loop): 优化循环状态管理` |
| `test` | 测试 | `test(tool-registry): 添加工具注册测试` |
| `chore` | 构建/工具 | `chore(deps): 更新项目依赖` |
| `perf` | 性能优化 | `perf(db): 优化数据库查询` |

#### 正确示例

```bash
# 简单提交
git commit -m "feat(agent-loop): 实现 Agent Loop 核心循环"

# 详细提交
git commit -m "feat(agent-loop): 实现 TAOR 循环

- 添加 Think -> Act -> Observe -> Reflect 四步循环
- 实现退出条件控制
- 支持工具调用

Related: Phase 0.5"
```

#### 错误示例

```bash
# 缺少 scope
git commit -m "docs: 更新文档"

# subject 为纯英文
git commit -m "refactor(agents): standardize agents project structure"

# 缺少 scope 且 subject 为纯英文
git commit -m "refactor: standardize agents project structure"
```

---

## 🔒 本地强制校验

仓库提供 `.githooks/commit-msg`，用于在 `git commit` 时校验提交信息。

首次克隆或发现 hook 未生效时，执行：

```bash
git config core.hooksPath .githooks
```

校验规则：

- 允许的 type：`feat`、`fix`、`docs`、`style`、`refactor`、`test`、`chore`、`perf`
- 必须填写 scope。
- subject 必须包含中文。

---

## 🔄 工作流程

### 日常开发

```bash
# 1. 查看状态
git status

# 2. 添加修改
git add path/to/file

# 3. 提交
git commit -m "feat(scope): 中文描述"

# 4. 推送（如果有远程仓库）
git push origin main
```

### 分阶段提交

```bash
# Phase 0.5 第一个功能
git add agents/core/tool_registry.py
git commit -m "feat(tool-registry): 实现工具注册系统

- 支持工具注册和 schema 生成
- 实现工具调用执行
- 添加单元测试"

# Phase 0.5 第二个功能
git add agents/core/agent_loop.py
git commit -m "feat(agent-loop): 实现 TAOR 循环

- Think -> Act -> Observe -> Reflect
- 退出条件控制
- 消息历史管理"
```

---

## 📝 提交频率建议

### 推荐提交时机

- ✅ **完成一个功能模块** - 如实现完工具注册系统
- ✅ **完成一个 Phase** - 如完成 Phase 0.5
- ✅ **修复一个 Bug** - 每个 bug fix 一次提交
- ✅ **更新文档** - 文档更新后提交
- ✅ **每天结束工作时** - 保存进度

### 避免

- ❌ 修改太多文件一次性提交（难以回溯）
- ❌ 长时间不提交（风险高）
- ❌ 提交信息过于简单（如 `update`）
- ❌ 提交信息缺少 scope（如 `docs: 更新文档`）
- ❌ 使用纯英文 subject（如 `refactor: standardize agents project structure`）

---

## 🔍 常用命令

### 查看历史

```bash
# 查看提交历史
git log --oneline

# 查看某个文件的历史
git log --oneline -- path/to/file

# 查看详细提交内容
git show <commit-hash>
```

### 撤销操作

```bash
# 撤销工作区的修改（未 add）
git checkout -- path/to/file

# 撤销 add（已 add 未 commit）
git reset HEAD path/to/file

# 修改最近一次提交信息
git commit --amend -m "docs(git-rules): 更新提交规范"

# 回退到上一次提交（慎用）
git reset --soft HEAD~1    # 保留修改
git reset --hard HEAD~1    # 丢弃修改
```

### 查看差异

```bash
# 查看工作区变化
git diff

# 查看已 add 的变化
git diff --cached

# 查看与某次提交的差异
git diff <commit-hash>
```

---

## 🏷️ Tag 标记

在重要里程碑打 tag：

```bash
# Phase 0 完成
git tag -a v0.1.0 -m "Phase 0: 基础设施完成"

# Phase 0.5 完成
git tag -a v0.2.0 -m "Phase 0.5: Agent Loop 核心引擎完成"

# Phase 1 完成
git tag -a v0.3.0 -m "Phase 1: 面试官 Agent MVP 完成"

# 推送 tag
git push origin --tags
```

---

## 📦 .gitignore 规则

已配置忽略以下内容：

- ✅ Python 编译文件（`__pycache__`, `*.pyc`）
- ✅ 虚拟环境（`venv/`, `ENV/`）
- ✅ IDE 配置（`.vscode/`, `.idea/`）
- ✅ 数据库文件（`*.db`, `*.sqlite`）
- ✅ 日志文件（`*.log`）
- ✅ 敏感配置（`.env`, `*.local.yaml`）
- ✅ 临时文件（`*.tmp`, `*.bak`）

---

## 🔒 敏感信息处理

### 配置文件安全

```yaml
# harness.yaml - 提交到 Git
llm:
  api_key: "your_api_key"  # 占位符

# harness.local.yaml - 不提交（已在 .gitignore）
llm:
  api_key: "sk-真实的key"  # 实际使用
```

### 如果不小心提交了敏感信息

```bash
# 1. 修改文件，移除敏感信息
# 2. 提交
git add path/to/file
git commit -m "fix(security): 移除敏感信息"

# 3. 如果已经 push，需要修改历史（谨慎）
# 建议直接更换泄露的密钥
```

---

## 📊 分支策略（未来扩展）

当项目需要多人协作时，可以采用：

```text
main            # 主分支（稳定版本）
  ├─ develop    # 开发分支
  │   ├─ feature/agent-loop
  │   ├─ feature/web-ui
  │   └─ bugfix/mysql-connection
  └─ hotfix/critical-bug
```

但**目前单人开发，不需要**。

---

## ✅ 快速参考

```bash
# 日常开发三步走
git add path/to/file
git commit -m "feat(scope): 中文描述"
git push origin main  # 如果有远程仓库

# 查看状态
git status
git log --oneline -5

# 撤销操作
git reset HEAD~1        # 撤销最近一次提交（保留修改）
git checkout -- .       # 放弃所有工作区修改
```

---

## 📝 提交清单

每次提交前检查：

- [ ] 代码能正常运行
- [ ] 删除了调试代码（`print`、`console.log`）
- [ ] 更新了相关文档
- [ ] Commit message 符合 `<type>(<scope>): <中文描述>`
- [ ] 没有提交敏感信息
- [ ] 提交后已执行 `git status --short` 和 `git log -1 --oneline`

---

**维护者**: AI 面试陪练系统开发团队  
**更新日期**: 2026-06-26
