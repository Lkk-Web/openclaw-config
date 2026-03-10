# OpenClaw 配置仓库

多机器人 OpenClaw 配置，支持多台电脑同步。

## 快速部署（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/Lkk-Web/openclaw-config.git ~/.openclaw

## 架构

```
~/.openclaw/
├── agents/
│   ├── main/              # 调度中心
│   │   └── workspace/
│   └── dev-assistant/     # 开发助手
│       └── workspace/
└── tools/                 # 公共工具
    ├── feishu/
    └── tavily/
```

## workspace核心配置文件

### AGENTS.md - 工作空间指南
**职责：** Agent 的操作手册和行为准则

- 定义 Agent 的启动流程（读取 SOUL.md、USER.md、memory 文件）
- 规定记忆管理规则（MEMORY.md 和 daily notes）
- 设定安全红线（数据保护、命令执行规范）
- 区分内部操作和外部操作的边界
- 群聊参与规范（何时发言、何时静默）
- 工具使用说明和平台格式规范
- Heartbeat 机制和主动性指导

### SOUL.md - 核心身份
**职责：** 定义 Agent 的核心身份和职责

- Agent 名称和角色定位
- 系统账号和工作目录
- 核心职责描述
- 路由规则（如调度者的任务分配规则）
- 行为准则

### IDENTITY.md - 身份信息
**职责：** Agent 的详细身份卡片

- 名称、生物类型、风格、表情符号
- User ID（Feishu 等平台的唯一标识）
- 专业领域和技能描述
- 自我介绍模板
- 调度方式和会话 Key
- 任务处理规范（幂等性机制）

### USER.md - 用户信息
**职责：** 记录用户相关信息

- 用户的名称和偏好
- 时区和联系方式
- 协作成员的 User ID
- 如何称呼和 @ 其他成员

### TOOLS.md - 本地工具配置
**职责：** 环境特定的工具配置

- 摄像头名称和位置
- SSH 主机和别名
- TTS 偏好语音
- 设备昵称
- 其他环境特定的配置

### HEARTBEAT.md - 定期任务
**职责：** 定义 Agent 的主动检查任务

- 定期执行的任务列表
- 检查频率和时间间隔
- 状态记录位置（如 `memory/heartbeat-state.json`）
- 保持会话活跃的策略

## 📝 记忆系统

### MEMORY.md
- **仅在主会话中加载**（安全考虑）
- 长期记忆，经过筛选的重要信息
- 决策、经验、教训的沉淀

### memory/YYYY-MM-DD.md
- 每日原始日志
- 当天发生的事件记录
- 定期整理后更新到 MEMORY.md

### memory/heartbeat-state.json
- Heartbeat 任务的执行状态
- 上次检查时间戳
- 用于避免重复检查

## 🔄 文件关系

```
启动时读取顺序：
1. SOUL.md      → 了解自己的核心身份
2. USER.md      → 了解服务对象
3. MEMORY.md    → 加载长期记忆（仅主会话）
4. memory/今天.md + memory/昨天.md → 获取近期上下文

运行时参考：
- AGENTS.md    → 行为准则和操作规范
- TOOLS.md     → 工具配置
- HEARTBEAT.md → 定期任务清单
- IDENTITY.md  → 身份和调度信息
```

## 🎯 多 Agent 协作

当前配置了两个 Agent：

- **main-调度者** (`ou_edfb0099ca13e5bc24f6aeab4b5db439`)
  - 任务分配、进度汇报、流程流转
  
- **dev-开发者** (`ou_2599ca0ea18341649c15bb0df3545765`)
  - 前端开发、后端开发

调度方式：
```javascript
sessions_send(
  sessionKey: "agent:dev-assistant:feishu:group:oc_c6fd1358a5ef9c3fad809293283eeeb1",
  message: "任务内容",
  timeoutSeconds: 30
)
```

## 📚 相关文档

- [OpenClaw 官方文档](https://docs.openclaw.ai)
- [多机器人配置指南](docs/multi-bot-setup.md)
- [Skills 开发指南](https://docs.openclaw.ai/skills)
