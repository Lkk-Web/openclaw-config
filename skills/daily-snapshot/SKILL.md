# Daily Snapshot Skill - 每日快照

自动将 OpenClaw 会话数据快照到本地 SQLite 数据库，包括会话消息、工具调用、知识图谱等。

## 功能说明

1. **数据库初始化** - 创建 6 张表存储快照数据
2. **会话导入** - 从 JSONL 文件导入会话和消息
3. **摘要生成** - 使用 LLM 为高 token 会话生成摘要
4. **图谱导出** - 导出知识图谱到 JSONL 格式
5. **Token 检查** - 检查会话 token 使用情况

## 环境配置

在使用前，需要配置以下环境变量：

### 必需的环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `CASS_BASE_URL` | CASS API 基础地址 | `https://cass.example.com` |
| `CASS_API_KEY` | CASS API 密钥 | 你的 API Key |

### 配置方式

**方式 1: 创建配置文件**

```bash
cp ~/.openclaw/skills/daily-snapshot/config.env.example ~/.openclaw/skills/daily-snapshot/config.env
# 编辑 config.env，填入你的 API 配置
source ~/.openclaw/skills/daily-snapshot/config.env
```

**方式 2: 在 shell 中设置**

```bash
export CASS_BASE_URL="https://cass.example.com"
export CASS_API_KEY="your-api-key"
```

## 使用方式

### 手动触发

```bash
# 完整快照流程（导入 + 摘要 + 图谱）
python3 ~/.openclaw/skills/daily-snapshot/script.py full

# 仅初始化数据库
python3 ~/.openclaw/skills/daily-snapshot/script.py init

# 导入最近 N 个会话
python3 ~/.openclaw/skills/daily-snapshot/script.py import 20

# 检查 token 使用情况
python3 ~/.openclaw/skills/daily-snapshot/script.py tokens

# 导出知识图谱
python3 ~/.openclaw/skills/daily-snapshot/script.py graph
```

### 定时任务

**一键配置定时任务（每日 4 点执行）：**

```bash
bash ~/.openclaw/skills/daily-snapshot/cron-setup.sh
```

**手动配置 cron：**

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每日 4:00 执行）
0 4 * * * /bin/bash -c "source ~/.openclaw/skills/daily-snapshot/config.env && python3 ~/.openclaw/skills/daily-snapshot/script.py full"
```

## 一键部署

在新电脑上部署步骤：

```bash
# 1. 复制整个 skill 目录
cp -r daily-snapshot ~/.openclaw/skills/

# 2. 配置环境变量
cp config.env.example config.env
# 编辑 config.env 填入 API Key

# 3. 安装 Python 依赖
pip3 install -r requirements.txt

# 4. 一键配置定时任务
bash cron-setup.sh
```

## 文件结构

```
~/.openclaw/skills/daily-snapshot/
├── SKILL.md              # 本文件
├── script.py             # 主入口脚本
├── config.env.example    # 环境变量模板
├── cron-setup.sh        # 定时任务配置脚本
└── requirements.txt     # Python 依赖
```

## 数据库表结构

| 表名 | 说明 |
|------|------|
| `snapshots` | 快照记录 |
| `sessions` | 会话记录 |
| `messages` | 消息记录 |
| `tools` | 工具调用记录 |
| `summaries` | 摘要记录 |
| `knowledge_graph` | 知识图谱节点 |

数据库位置：`~/.openclaw/memory/snapshot.db`

## 注意事项

1. 首次使用前必须配置 `CASS_API_KEY` 和 `CASS_BASE_URL`
2. 定时任务执行时需要确保环境变量已加载
3. 建议先运行 `init` 初始化数据库