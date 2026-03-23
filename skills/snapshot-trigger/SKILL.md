# SKILL.md - 每日快照触发器 (snapshot-trigger)

## 描述
监控并触发快照操作，支持手动触发和 40K tokens 阈值自动触发。

## 触发条件
- 关键词: snapshot, 快照, 触发器, 阈值, token, 每日快照
- 用户请求手动执行快照时
- Token 达到阈值时自动触发

## 功能

### 1. 手动快照触发
执行完整的快照流程：
- 初始化 SQLite 数据库
- 导入会话数据
- 生成摘要
- 导出知识图谱

### 2. Token 阈值检测
- 默认阈值: 40,000 tokens
- 支持自定义阈值
- 轮询 session token 文件检测

### 3. 定时任务支持
配置 cron 定时执行快照

## 使用方式

### 手动触发
```
/snapshot
/snapshot full
```

### 检查 token 阈值
```
/snapshot threshold
/snapshot check
```

### 导出图谱
```
/snapshot graph
/snapshot graph daily
```

## 实现脚本

### 主入口
```bash
~/.openclaw/scripts/snapshot/main.sh <command>
```

### 可用命令
- `init` - 初始化数据库
- `import [limit]` - 导入会话
- `summary` - 生成摘要
- `graph` - 导出图谱
- `full` - 完整快照
- `tokens` - 检查 token
- `threshold [n]` - 检查阈值

## 依赖
- Python 3
- SQLite3
- openclaw 工具 (可选)

## 配置文件
- 数据库: `~/.openclaw/memory/snapshot.db`
- 图谱输出: `~/.openclaw/memory/graphs/`