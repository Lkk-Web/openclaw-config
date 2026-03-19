# SKILL.md - 知识图谱构建 (knowledge-graph)

## 描述
从会话数据中提取实体和关系，构建知识图谱并导出为 graph.jsonl 格式。

## 触发条件
- 关键词: knowledge graph, 知识图谱, 图谱, entity, 关系, 导出图谱
- 用户请求查看或导出知识图谱

## 功能

### 1. 图谱节点类型
- **session**: 会话节点
- **tool**: 工具使用节点
- **keyword**: 关键词节点
- **user_message**: 用户消息节点

### 2. 图谱边类型
- **uses**: 会话使用工具的关系
- **contains**: 会话包含消息的关系

### 3. 导出格式
输出为 JSONL 格式，每行一个节点或边：
```json
{"id": "session_abc123", "type": "session", "label": "会话 abc123", "properties": {"session_id": "abc123..."}}
{"id": "tool_browser", "type": "tool", "label": "browser", "properties": {"usage_count": 5}}
{"from": "session_abc123", "to": "tool_browser", "type": "uses"}
```

## 使用方式

### 导出今日图谱
```
/graph daily
/knowledge-graph today
```

### 导出指定会话图谱
```
/graph session <session_id>
```

### 查看图谱统计
```
/graph stats
/graph info
```

## 实现脚本

### 导出脚本
```bash
~/.openclaw/scripts/snapshot/export-graph.py daily
~/.openclaw/scripts/snapshot/export-graph.py session <session_id>
```

## 输出路径
- 每日图谱: `~/.openclaw/memory/graphs/graph_YYYY-MM-DD.jsonl`
- 会话图谱: `~/.openclaw/memory/graphs/<snapshot_id>.jsonl`

## 数据来源
- SQLite 数据库: `~/.openclaw/memory/snapshot.db`
- sessions 表
- messages 表
- tools 表
- summaries 表

## 依赖
- Python 3
- SQLite3

## 图谱可视化
导出的 JSONL 可用于：
- Gephi
- Cytoscape
- D3.js
- 其他图谱可视化工具