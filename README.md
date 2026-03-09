# OpenClaw 配置仓库

多机器人 OpenClaw 配置，支持多台电脑同步。

## 快速部署（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/Lkk-Web/openclaw-config.git ~/.openclaw

# 2. 运行部署脚本
cd ~/.openclaw
bash setup.sh
```

脚本会自动：
- 配置 .env 文件
- 生成 openclaw.json
- 重启 Gateway

## 手动部署

### 1. 克隆仓库

```bash
git clone https://github.com/Lkk-Web/openclaw-config.git ~/.openclaw
```

### 2. 配置 .env

```bash
echo "TAVILY_API_KEY=your-key" > ~/.openclaw/.env
```

### 3. 配置 openclaw.json

```bash
cp openclaw.json.example ~/.openclaw/openclaw.json
# 编辑配置文件，修改用户名和 API keys
```

### 4. 重启 Gateway

```bash
openclaw gateway restart
```


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

## 多台电脑同步

### 推送更改

```bash
cd ~/.openclaw
git add agents/*/workspace/*.md tools/
git commit -m "更新配置"
git push
```

### 拉取更改

```bash
cd ~/.openclaw
git pull
openclaw gateway restart
```

## 注意事项

- `.env` 和 `openclaw.json` 不会同步（包含敏感信息）
- 每台机器需要单独配置这些文件
- `agents/*/sessions/` 不会同步（会话历史）
