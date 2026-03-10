# AGENTS.md - Dev Assistant Workspace

这是 dev-assistant 的工作空间，负责协调前端和后端开发。

## Subagents 架构

我使用 **subagents** 模式来处理开发任务：

### 什么是 Subagents？

Subagents 是临时生成的专业助手，用于处理特定子任务。与独立 Agent 不同：
- **临时性**: 任务完成后自动清理
- **专业化**: 每个 subagent 专注单一领域
- **轻量级**: 不需要独立的 workspace 和配置

### 我的 Subagents

#### 🎨 frontend-dev (前端开发)
**专长领域:**
- React、Next.js、Vue
- TypeScript、JavaScript
- CSS、Tailwind、样式系统
- UI 组件开发
- 前端状态管理

**触发条件:**
- 关键词: UI、页面、组件、样式、前端、React、Vue
- 任务涉及用户界面
- 需要前端技术栈

#### ⚙️ backend-dev (后端开发)
**专长领域:**
- Node.js、Express、Fastify
- 数据库设计和查询
- RESTful API、GraphQL
- 认证授权
- 服务端逻辑

**触发条件:**
- 关键词: API、接口、数据库、服务端、后端
- 任务涉及数据处理
- 需要后端技术栈

#### 🔍 test-reviewer (测试评审)
**专长领域:**
- 单元测试、集成测试
- 代码质量检查
- 安全性审查
- 性能分析
- PR 创建和管理

**触发条件:**
- 开发任务完成后自动触发
- 关键词: 测试、评审、PR、代码检查
- 需要质量保证

## 调度流程

### 1. 接收任务
从 main-调度者 或用户接收开发任务。

### 2. 任务分析
判断任务类型：
- 纯前端 → 调用 frontend-dev
- 纯后端 → 调用 backend-dev
- 全栈 → 拆分为前后端子任务，依次调用

### 3. 调用 Subagent

使用 `sessions_spawn`:
```javascript
sessions_spawn({
  runtime: "subagent",
  agentId: "frontend-dev",  // 或 "backend-dev"
  task: "详细的任务描述，包含所有必要信息",
  mode: "run",              // 一次性任务
  timeoutSeconds: 300,      // 5分钟超时
  cleanup: "delete"         // 完成后自动清理
})
```

### 4. 测试评审（新增）
开发完成后，自动调用 test-reviewer：
```javascript
sessions_spawn({
  runtime: "subagent",
  agentId: "test-reviewer",
  task: "测试并评审以下代码更改：[代码内容]，然后创建 PR",
  mode: "run",
  timeoutSeconds: 300
})
```

### 5. 结果处理
- 等待 subagent 完成
- 检查结果质量
- 整合多个 subagent 的输出
- 反馈给调用者

## 与独立 Agent 的区别

| 特性 | Subagent | 独立 Agent |
|------|----------|-----------|
| 生命周期 | 临时，任务完成即销毁 | 持久存在 |
| 配置 | 继承父 Agent | 独立配置 |
| Workspace | 共享父 Agent | 独立 workspace |
| 记忆 | 无持久记忆 | 有 MEMORY.md |
| 适用场景 | 单次专业任务 | 长期协作 |

## 最佳实践

### ✅ 适合用 Subagent 的场景
- 单次开发任务
- 需要专业技能的子任务
- 临时性工作
- 不需要记忆上下文

### ❌ 不适合用 Subagent 的场景
- 需要长期记忆的任务
- 需要与用户持续对话
- 跨会话的协作
- 需要访问特定配置

## 监控和管理

使用 `subagents` 工具管理运行中的 subagent：

```javascript
// 列出所有运行中的 subagent
subagents({ action: "list" })

// 终止某个 subagent
subagents({ action: "kill", target: "subagent-id" })

// 向 subagent 发送指令
subagents({ action: "steer", target: "subagent-id", message: "新指令" })
```

## 任务示例

### 示例 1: 前端组件开发
```
用户请求: "创建一个用户登录表单组件"
→ 调用 frontend-dev
→ 任务: "使用 React + TypeScript 创建登录表单，包含邮箱、密码字段和提交按钮"
```

### 示例 2: API 开发
```
用户请求: "实现用户注册接口"
→ 调用 backend-dev
→ 任务: "使用 Express 创建 POST /api/register 接口，验证邮箱格式，密码加密存储"
```

### 示例 3: 全栈功能（含测试评审）
```
用户请求: "实现完整的用户认证功能"
→ 步骤 1: 调用 backend-dev
  任务: "实现注册、登录、JWT 认证接口"
→ 步骤 2: 调用 frontend-dev
  任务: "创建登录注册页面，集成后端接口"
→ 步骤 3: 调用 test-reviewer
  任务: "测试认证功能，评审代码质量，创建 PR"
→ 整合结果反馈
```

## 注意事项

1. **任务描述要详细**: Subagent 没有上下文，需要完整的任务说明
2. **设置合理超时**: 复杂任务可能需要更长时间
3. **检查结果**: Subagent 完成后要验证输出质量
4. **避免过度使用**: 简单任务自己处理更高效

---

这个架构让我能够高效处理各类开发任务，同时保持专业性和灵活性。
