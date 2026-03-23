# SKILL.md - 图谱查询 (graph-query)

## 描述
快速查询知识图谱，返回与当前对话相关的上下文信息。支持实体搜索、关系查询、模糊匹配，查询延时 < 200ms。

## 触发条件
- 关键词: query-graph, /kg, 查询图谱, 图谱查询, search graph, find entity
- 用户请求查询知识图谱时
- 对话中需要相关上下文时

## 功能

### 1. 快速查询（图优先)
- 默认查询今日图谱数据
- 使用 SQLite 索引加速查询
- 目标延时: < 200ms

### 2. 实体类型查询
支持按类型过滤:
- `session` - 会话节点
- `tool` - 工具使用节点
- `keyword` - 关键词节点
- `user_message` - 用户消息节点

### 3. 模糊搜索
- 支持 LABEL 模糊匹配
- 支持关键词包含搜索
- 自动联想相关实体

### 4. 关系查询
查询实体间的关联关系:
- `uses` - 会话使用工具
- `contains` - 会话包含消息
- 其他自定义关系

## 使用方式

### 基本查询
```
/kg
/query-graph
图谱查询
```

### 按类型查询
```
/kg session
/kg tool
/kg keyword
```

### 模糊搜索
```
/kg browser
/kg exec
/kg "测试"
```

### 组合查询
```
/kg session browser
/kg tool exec
```

### 关系查询
```
/kg relates <entity_id>
```

## 输出格式

返回 LLM 可直接使用的上下文:
```
## 图谱上下文

### 相关实体
1. [session] 会话 abc123 - 用户执行了浏览器操作
2. [tool] browser - 使用了 5 次

### 相关关系
- 会话 abc123 → uses → browser
```

## 实现细节

### 索引优化
```sql
CREATE INDEX idx_entity_type ON entities(entity_type);
CREATE INDEX idx_entity_label ON entities(label);
CREATE INDEX idx_entity_label_fts ON entities(label_fts);
```

### 性能指标
- 单次查询: < 50ms
- 模糊查询: < 100ms
- 关系查询: < 150ms

## 数据源
- 每日图谱: `~/.openclaw/memory/graphs/graph_YYYY-MM-DD.jsonl`
- 索引缓存: `~/.openclaw/memory/graphs/query.db`

## 依赖
- Python 3
- SQLite3