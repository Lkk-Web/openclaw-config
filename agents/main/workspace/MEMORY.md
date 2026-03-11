# MEMORY.md - 调度者长期记忆

## Agent 架构

### 当前 Agent 列表
1. **main-调度者** (我)
   - 角色：总调度中心
   - 职责：理解需求，分配任务给专业 Agent

2. **dev-assistant (dev-开发者)**
   - 角色：开发协调者
   - 职责：协调前后端开发任务
   - Subagents：frontend-dev, backend-dev, test-reviewer

3. **product-manager (pm-产品经理)**
   - 角色：产品经理
   - 职责：市场分析、竞品调研、功能规划、产品建议
   - 创建时间：2026-03-11

4. **test-reviewer (测试评审者)**
   - 角色：测试与代码评审专家
   - 职责：代码测试、评审、PR 管理
   - 创建时间：2026-03-10

### 工作流程

**接收任务前的确认：**
- 对于调度或问候语，先询问用户指定工程目录
- 确认目录后再调度 dev-assistant

**标准开发流程（三阶段）：**
1. **开发阶段** - dev-assistant 调用 frontend-dev 或 backend-dev
2. **测试评审** - dev-assistant 调用 test-reviewer
3. **提交阶段** - test-reviewer 创建 PR

## 配置要点

### Subagent 配置
位置：`~/.openclaw/openclaw.json`

关键字段：`allowAgents`（不是 allowedAgents）
```json
{
  "agents": {
    "list": [
      {
        "id": "dev-assistant",
        "subagents": {
          "allowAgents": ["frontend-dev", "backend-dev", "test-reviewer"]
        }
      }
    ]
  }
}
```

配置更新后需要重启：`kill -HUP <pid>`

## Skills 管理

### Skills 加载路径
OpenClaw 自动扫描以下路径（无需配置）：
1. `~/.openclaw/skills/` - 用户全局 skills
2. `<repo>/skills/` - 仓库内置 skills

### 为 Agent 添加 Skill

**方法：复制到 Agent workspace**
```bash
# 1. 创建 skills 目录
mkdir -p ~/.openclaw/agents/<agent-id>/workspace/skills

# 2. 复制 skill
cp -r <source-skill-path> ~/.openclaw/agents/<agent-id>/workspace/skills/

# 3. 确保配置中包含路径（通常已配置）
# ~/.openclaw/openclaw.json
{
  "skills": {
    "load": {
      "extraDirs": [
        "~/Users/liukangkai/.openclaw/agents/<agent-id>/workspace/skills"
      ]
    }
  }
}

# 4. 重启生效
openclaw gateway restart
```

**示例：为 main 添加 summarize**
```bash
cp -r ~/Desktop/github/ai/openclaw/skills/summarize \
  ~/.openclaw/agents/main/workspace/skills/
```

