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

