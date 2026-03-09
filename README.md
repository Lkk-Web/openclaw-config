# OpenClaw 配置仓库

多机器人 OpenClaw 配置，支持多台电脑同步。

## 架构

```
~/.openclaw/
├── agents/
│   ├── main/              # 调度中心
│   └── dev-assistant/     # 开发助手
└── tools/                 # 公共工具
    ├── feishu/
    └── tavily/
```

## 首次设置

### 1. 克隆仓库

```bash
cd ~
git clone <你的仓库地址> .openclaw
```

### 2. 配置敏感信息

创建 `.env` 文件：

```bash
echo "TAVILY_API_KEY=your-key" > ~/.openclaw/.env
```

### 3. 配置 openclaw.json

复制配置模板并修改：

```bash
cp openclaw.json.example ~/.openclaw/openclaw.json
# 编辑配置文件
```


### 4. 重启 Gateway

```bash
openclaw gateway restart
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

## 快速命令

```bash
# 提交并推送
cd ~/.openclaw && git add . && git commit -m "update" && git push

# 拉取并重启
cd ~/.openclaw && git pull && openclaw gateway restart
```
