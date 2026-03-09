# Tavily Search API 配置指南

Tavily 是一个专为 AI 应用优化的搜索 API。本指南帮助你在 OpenClaw 中配置和使用 Tavily。

## 快速开始

### 1. 获取 API Key

访问 [Tavily](https://tavily.com) 注册账号并获取 API key。

### 2. 配置到 OpenClaw

在 `~/.openclaw/.env` 文件中添加：

```bash
TAVILY_API_KEY=tvly-your-api-key-here
```

### 3. 重启 Gateway

```bash
openclaw gateway restart
```

## 使用 Tavily 搜索

### 方法 1：使用 tavily-search skill（推荐）

```bash
cd tools/tavily/tavily-search
source ~/.openclaw/.env
bash scripts/search.sh "搜索关键词" 5
```

**示例：**

```bash
# 搜索 React 19 新特性
bash scripts/search.sh "React 19 features" 3

# 搜索最新科技新闻
bash scripts/search.sh "latest tech news 2026" 10
```

**返回结果示例：**

```json
{
  "query": "React 19 features",
  "results": [
    {
      "url": "https://example.com/article",
      "title": "React 19 新特性",
      "content": "文章摘要...",
      "score": 0.92
    }
  ]
}
```

### 方法 2：通过 Agent 调用

在对话中直接请求搜索，Agent 会自动调用 Tavily skill。

## 配置迁移

本目录包含配置迁移 skill，可以快速在多台机器间同步配置。

### 从源机器导出

```bash
export TAVILY_API_KEY=$(grep TAVILY_API_KEY ~/.openclaw/.env | cut -d= -f2)
echo $TAVILY_API_KEY
```

### 导入到目标机器

```bash
cd tavily-skill/tavily-config-migrate
TAVILY_API_KEY=tvly-your-key-here bash scripts/migrate.sh
```

## 目录结构

```
tavily/
├── README.md                           # 本文档
├── tavily-search/                      # Tavily 搜索 skill
│   ├── SKILL.md                        # Skill 说明
│   └── scripts/
│       └── search.sh                   # 搜索脚本
├── tavily-config-migrate.skill         # 配置迁移 skill 包
└── tavily-skill/                       # 解压后的迁移 skill
    └── tavily-config-migrate/
        ├── SKILL.md
        └── scripts/
            └── migrate.sh
```

## 当前配置状态

✅ Tavily API Key 已配置
✅ tavily-search skill 已创建并测试通过

配置文件位置：`~/.openclaw/.env`

## 相关资源

- [Tavily 官网](https://tavily.com)
- [Tavily API 文档](https://docs.tavily.com)
- [OpenClaw 文档](https://docs.openclaw.ai)
