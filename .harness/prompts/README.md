"""兼容层：.harness.prompts 转发到 agents.definitions

旧版代码可能会尝试读取 `.harness/prompts/*.md`，这里提供说明文件。
正式的 Agent 定义文档位于 `agents/definitions/`。
"""

# 这个目录现在为空，prompts 已迁移到 agents/definitions/
# 如果有旧代码读取此目录下的文件，应该改为读取 agents/definitions/
