# 贡献指南

感谢你对 Obsidian Interview Harness 项目的关注！我们欢迎任何形式的贡献。

[English](#contributing-in-english) | [中文](#中文贡献指南)

---

## 中文贡献指南

### 🎯 贡献方式

你可以通过以下方式为项目做出贡献：

- 🐛 **报告 Bug**：发现问题？请提交 Issue
- ✨ **提出新功能**：有好的想法？分享给我们
- 📝 **改进文档**：发现文档不清晰或有错误
- 💻 **提交代码**：修复 Bug、实现新功能
- 🌍 **翻译**：帮助翻译文档或界面
- 📚 **分享知识库**：贡献面试题库（非私人的）

### 🚀 快速开始

#### 1. Fork 并克隆项目

```bash
# 1. 点击右上角 Fork 按钮，Fork 到你的账号

# 2. 克隆你的 Fork
git clone https://github.com/你的用户名/obsidian-interview-harness.git
cd obsidian-interview-harness

# 3. 添加上游仓库
git remote add upstream https://github.com/gstajie520/obsidian-interview-harness.git
```

#### 2. 创建开发分支

```bash
# 从 main 创建新分支
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/bug-description
```

#### 3. 设置开发环境

```bash
# 安装依赖
pip install -r requirements.txt

# 安装开发工具
pip install pytest pytest-cov black isort mypy pylint

# 配置 API Key（用于本地测试）
cp .harness/config/harness.yaml.example .harness/config/harness.yaml
# 编辑 harness.yaml，填入你的测试 API Key
```

### 📝 开发规范

#### 代码风格

我们遵循 **PEP 8** 规范，并使用以下工具：

```bash
# 代码格式化
black agents/ scripts/ tests/

# 导入排序
isort agents/ scripts/ tests/

# 类型检查
mypy agents/ --ignore-missing-imports

# 代码检查
pylint agents/ --disable=C0111,R0903,W0212
```

#### 命名约定

- **Python 文件**: `snake_case.py`
- **类名**: `PascalCase`（如 `InterviewerAgent`）
- **函数/方法**: `snake_case()`（如 `get_random_question()`）
- **常量**: `UPPER_SNAKE_CASE`（如 `MAX_TOKENS`）
- **私有方法**: `_leading_underscore()`

#### 注释规范

```python
def calculate_next_review(self, score: float) -> int:
    """
    根据 SM-2 算法计算下次复习时间
    
    Args:
        score: 答题得分（0-5）
        
    Returns:
        int: 下次复习的间隔天数
        
    Raises:
        ValueError: 如果 score 超出范围
    """
    # 实现逻辑
    pass
```

#### 提交信息规范

我们使用 **中文约定式提交（Conventional Commits）**：

```bash
# 格式
<type>(<scope>): <中文描述>

<详细描述>（可选）

<关联 Issue>（可选）

# 类型（type）
feat:     新功能
fix:      Bug 修复
docs:     文档更新
style:    代码格式（不影响功能）
refactor: 重构
test:     测试相关
chore:    构建/工具链
perf:     性能优化

# 硬性要求
# 1. scope 必须填写
# 2. subject 必须包含中文，禁止纯英文
# 3. AI 提交前必须先阅读 GIT_RULES.md

# 示例
feat(agent-loop): 添加超时控制机制

- 添加 max_timeout 参数
- 超时后自动退出循环
- 记录超时日志

Closes #123
```

### ✅ 提交前检查清单

在提交 PR 之前，请确保：

- [ ] 代码通过 `black` 格式化
- [ ] 代码通过 `isort` 导入排序
- [ ] 代码通过 `mypy` 类型检查
- [ ] 代码通过 `pylint` 检查（允许少量警告）
- [ ] 添加了单元测试（如果是新功能）
- [ ] 所有测试通过 `pytest tests/`
- [ ] 更新了相关文档
- [ ] 提交信息符合约定式提交规范

### 🧪 编写测试

所有新功能必须包含测试：

```python
# tests/test_your_feature.py
import pytest
from agents.your_module import YourClass

def test_your_feature():
    """测试你的新功能"""
    obj = YourClass()
    result = obj.your_method()
    assert result == expected_value

@pytest.mark.asyncio
async def test_async_feature():
    """测试异步功能"""
    result = await async_function()
    assert result is not None
```

运行测试：

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_your_feature.py -v

# 查看覆盖率
pytest tests/ --cov=agents --cov-report=html
```

### 📤 提交 Pull Request

#### 1. 保持分支更新

```bash
# 拉取上游更新
git fetch upstream
git rebase upstream/main

# 解决冲突（如果有）
git add .
git rebase --continue
```

#### 2. 推送到你的 Fork

```bash
git push origin feature/your-feature-name
```

#### 3. 创建 Pull Request

1. 访问 https://github.com/gstajie520/obsidian-interview-harness
2. 点击 "Pull requests" → "New pull request"
3. 选择你的分支
4. 填写 PR 描述：

```markdown
## 描述
简要描述你的更改

## 更改类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 代码重构
- [ ] 其他（请说明）

## 测试
说明如何测试你的更改

## 相关 Issue
Closes #123
```

#### 4. 等待 Review

- 维护者会尽快 Review 你的 PR
- 根据反馈进行修改
- 所有讨论解决后，PR 会被合并

### 🌟 贡献知识库

如果你想贡献面试题库（非私人的）：

```bash
# 1. 创建新知识库
mkdir -p "知识库/你的领域"

# 2. 按照现有格式添加题目
# 参考：知识库/示例/

# 3. 更新配置
vim .harness/config/knowledge_bases.yaml

# 4. 测试导入
python scripts/import_questions.py --knowledge-base your_kb

# 5. 提交 PR
```

### ❓ 需要帮助？

- 📖 查看 [完整文档](CLAUDE.md)
- 💬 在 [Discussions](https://github.com/gstajie520/obsidian-interview-harness/discussions) 提问
- 🐛 在 [Issues](https://github.com/gstajie520/obsidian-interview-harness/issues) 报告问题

---

## Contributing in English

### 🎯 Ways to Contribute

You can contribute to the project in several ways:

- 🐛 **Report Bugs**: Found an issue? Submit an Issue
- ✨ **Suggest Features**: Have a great idea? Share it with us
- 📝 **Improve Documentation**: Found unclear or incorrect docs
- 💻 **Submit Code**: Fix bugs, implement features
- 🌍 **Translation**: Help translate documentation or UI
- 📚 **Share Knowledge**: Contribute interview question banks (non-private)

### 🚀 Getting Started

#### 1. Fork and Clone

```bash
# 1. Click the Fork button at the top right

# 2. Clone your fork
git clone https://github.com/your-username/obsidian-interview-harness.git
cd obsidian-interview-harness

# 3. Add upstream remote
git remote add upstream https://github.com/gstajie520/obsidian-interview-harness.git
```

#### 2. Create a Branch

```bash
# Create a new branch from main
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

#### 3. Set Up Development Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install pytest pytest-cov black isort mypy pylint

# Configure API Key (for local testing)
cp .harness/config/harness.yaml.example .harness/config/harness.yaml
# Edit harness.yaml and add your test API Key
```

### 📝 Development Standards

#### Code Style

We follow **PEP 8** and use these tools:

```bash
# Format code
black agents/ scripts/ tests/

# Sort imports
isort agents/ scripts/ tests/

# Type checking
mypy agents/ --ignore-missing-imports

# Linting
pylint agents/ --disable=C0111,R0903,W0212
```

#### Commit Message Convention

We use **Conventional Commits**:

```bash
# Format
<type>(<scope>): <short description>

<detailed description> (optional)

<related issue> (optional)

# Types
feat:     New feature
fix:      Bug fix
docs:     Documentation update
style:    Code formatting (no functional change)
refactor: Code refactoring
test:     Test-related
chore:    Build/toolchain

# Example
feat(agent-loop): add timeout control mechanism

- Add max_timeout parameter
- Auto-exit loop on timeout
- Log timeout events

Closes #123
```

### ✅ Pre-Submit Checklist

Before submitting a PR, ensure:

- [ ] Code formatted with `black`
- [ ] Imports sorted with `isort`
- [ ] Passes `mypy` type checking
- [ ] Passes `pylint` (few warnings allowed)
- [ ] Unit tests added (if new feature)
- [ ] All tests pass with `pytest tests/`
- [ ] Documentation updated
- [ ] Commit messages follow Conventional Commits

### 🧪 Writing Tests

All new features must include tests:

```python
# tests/test_your_feature.py
import pytest
from agents.your_module import YourClass

def test_your_feature():
    """Test your new feature"""
    obj = YourClass()
    result = obj.your_method()
    assert result == expected_value

@pytest.mark.asyncio
async def test_async_feature():
    """Test async functionality"""
    result = await async_function()
    assert result is not None
```

Run tests:

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_your_feature.py -v

# View coverage
pytest tests/ --cov=agents --cov-report=html
```

### 📤 Submitting a Pull Request

#### 1. Keep Your Branch Updated

```bash
# Fetch upstream updates
git fetch upstream
git rebase upstream/main

# Resolve conflicts (if any)
git add .
git rebase --continue
```

#### 2. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

#### 3. Create Pull Request

1. Visit https://github.com/gstajie520/obsidian-interview-harness
2. Click "Pull requests" → "New pull request"
3. Select your branch
4. Fill in PR description:

```markdown
## Description
Brief description of your changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Other (please specify)

## Testing
Describe how to test your changes

## Related Issue
Closes #123
```

#### 4. Wait for Review

- Maintainers will review your PR as soon as possible
- Make changes based on feedback
- Once all discussions are resolved, your PR will be merged

### 🌟 Contributing Knowledge Bases

To contribute interview question banks (non-private):

```bash
# 1. Create new knowledge base
mkdir -p "知识库/YourDomain"

# 2. Add questions following existing format
# Reference: 知识库/示例/

# 3. Update configuration
vim .harness/config/knowledge_bases.yaml

# 4. Test import
python scripts/import_questions.py --knowledge-base your_kb

# 5. Submit PR
```

### ❓ Need Help?

- 📖 Read the [full documentation](CLAUDE.md)
- 💬 Ask questions in [Discussions](https://github.com/gstajie520/obsidian-interview-harness/discussions)
- 🐛 Report issues in [Issues](https://github.com/gstajie520/obsidian-interview-harness/issues)

---

## 📜 行为准则 / Code of Conduct

我们致力于为所有人提供友好、安全的贡献环境。请遵守以下原则：

We are committed to providing a friendly, safe environment for everyone. Please follow these principles:

- 🤝 **尊重他人** / Be respectful
- 💬 **建设性沟通** / Communicate constructively
- 🎯 **专注于问题本身** / Focus on the issue, not the person
- 🌈 **包容多样性** / Be inclusive and welcoming
- 📢 **接受批评** / Accept constructive criticism gracefully

---

**感谢你的贡献！/ Thank you for your contribution!** 🎉
