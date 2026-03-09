# OpenClaw 多 Agent 配置部署指南

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/Lkk-Web/openclaw-config.git ~/.openclaw

# 运行部署脚本
cd ~/.openclaw
bash setup.sh
```

## 手动配置步骤

### 1. 配置环境变量 (.env)

创建 `~/.openclaw/.env` 文件：

```bash
TAVILY_API_KEY=your-tavily-api-key
```

### 2. 配置 OpenClaw (openclaw.json)

复制模板并修改：

```bash
cp openclaw.json.example openclaw.json
```

编辑 `openclaw.json`，替换以下内容：
- `YOUR_USERNAME` → 你的系统用户名
- API keys 和 baseUrl


### 3. 架构说明

```
~/.openclaw/
├── agents/
│   ├── main/              # 调度中心
│   │   └── workspace/
│   └── dev-assistant/     # 开发助手
│       └── workspace/
└── tools/                 # 公共工具（符号链接）
    ├── feishu/
    └── tavily/
```

### 4. 重启 Gateway

```bash
openclaw gateway restart
```

## 配置说明

### 必需配置

1. **API Keys** - 在 openclaw.json 中配置模型 API
2. **TAVILY_API_KEY** - 在 .env 中配置搜索 API
3. **用户名路径** - 修改 workspace 路径中的用户名

### 可选配置

- Telegram bot token
- 飞书应用配置

## 推送到远程

```bash
cd ~/.openclaw
git push origin main
```

如果遇到网络问题，可以配置代理或使用 SSH。
