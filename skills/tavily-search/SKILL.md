---
name: tavily-search
description: Search the web using Tavily API. Use when user asks to search for information, latest news, or research topics using Tavily.
---

# Tavily Search

使用 Tavily API 进行网络搜索。

## 使用方法

### 基础搜索

```bash
bash scripts/search.sh "搜索关键词"
```

### 指定结果数量

```bash
bash scripts/search.sh "搜索关键词" 10
```

## 前置条件

确保 `TAVILY_API_KEY` 已配置在 `~/.openclaw/.env` 文件中。

## 示例

搜索 React 19 新特性：

```bash
bash scripts/search.sh "React 19 new features" 5
```
