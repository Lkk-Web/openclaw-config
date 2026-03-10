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

3. **test-reviewer (测试评审者)**
   - 角色：测试与代码评审专家
   - 职责：代码测试、评审、PR 管理
   - 创建时间：2026-03-10

### 工作流程

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

