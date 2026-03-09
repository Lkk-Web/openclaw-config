# OpenClaw 多机器人配置指南

在 OpenClaw 中区分不同机器人，每个机器人有独立的记忆、skills 和配置。

## 方案对比

| 方案 | 适用场景 | 隔离程度 | 配置复杂度 |
|------|---------|---------|-----------|
| 多 Agent | 完全独立的机器人 | 完全隔离 | 简单 |
| 配置路由 | 同一机器人不同渠道 | 部分隔离 | 中等 |

## 方案 1：多 Agent（推荐）

每个 Agent 有完全独立的：
- Workspace（工作空间）
- Memory（记忆文件）
- Skills（技能目录）
- Sessions（会话历史）
- 配置

### 创建新 Agent

```bash
# 创建开发助手
openclaw agents add dev-assistant

# 创建客服机器人
openclaw agents add customer-service

# 创建内容创作助手
openclaw agents add content-creator
```

### 目录结构

```
~/.openclaw/agents/
├── main/
│   ├── workspace/
│   │   ├── MEMORY.md
│   │   ├── IDENTITY.md
│   │   ├── USER.md
│   │   └── tools/
│   └── sessions/
├── dev-assistant/
│   ├── workspace/
│   └── sessions/
└── customer-service/
    ├── workspace/
    └── sessions/
```


### 为每个 Agent 配置独立身份

**dev-assistant/workspace/IDENTITY.md:**
```markdown
# IDENTITY.md

- **Name:** DevBot
- **Creature:** 全栈开发专家
- **Vibe:** 技术、专业、高效
- **Emoji:** 💻
```

**customer-service/workspace/IDENTITY.md:**
```markdown
# IDENTITY.md

- **Name:** 小助手
- **Creature:** 客服机器人
- **Vibe:** 友好、耐心、热情
- **Emoji:** 🤝
```

### 配置不同的 Skills

每个 Agent 的 workspace 下可以有独立的 skills：

```bash
# 开发助手的 skills
~/.openclaw/agents/dev-assistant/workspace/tools/
├── tavily/
├── code-review/
└── git-helper/

# 客服的 skills
~/.openclaw/agents/customer-service/workspace/tools/
├── faq/
└── ticket-system/
```


## 方案 2：配置路由（同一 Agent）

通过配置将不同渠道路由到不同行为。

### 在 openclaw.json 中配置

```json
{
  "agents": {
    "list": [
      {
        "id": "dev-bot",
        "workspace": "/path/to/dev-workspace",
        "model": {
          "primary": "cass-claude/claude-opus-4-6"
        }
      },
      {
        "id": "customer-bot",
        "workspace": "/path/to/customer-workspace",
        "model": {
          "primary": "cass-gpt/gpt-5.2-chat"
        }
      }
    ]
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "agent": "dev-bot"
    },
    "feishu": {
      "enabled": true,
      "accounts": {
        "main": {
          "agent": "customer-bot"
        }
      }
    }
  }
}
```


## 实战示例

### 场景：开发团队 + 客服团队

**1. 创建两个 Agent**

```bash
openclaw agents add dev-team
openclaw agents add support-team
```

**2. 配置开发团队机器人**

```bash
# 编辑 ~/.openclaw/agents/dev-team/workspace/IDENTITY.md
# 添加开发相关的 skills 到 workspace/tools/
```

**3. 配置客服团队机器人**

```bash
# 编辑 ~/.openclaw/agents/support-team/workspace/IDENTITY.md
# 添加客服相关的 skills 到 workspace/tools/
```

**4. 渠道绑定**

在 `openclaw.json` 中配置不同渠道使用不同 Agent。

## 最佳实践

1. **命名规范**：使用清晰的 Agent ID（如 `dev-bot`, `support-bot`）
2. **独立 workspace**：每个 Agent 有独立的工作目录
3. **Skills 隔离**：不同 Agent 只加载需要的 skills
4. **记忆分离**：MEMORY.md 完全独立，避免混淆

## 相关文档

- [OpenClaw Agents 文档](https://docs.openclaw.ai/agents)
- [Skills 开发指南](https://docs.openclaw.ai/skills)

