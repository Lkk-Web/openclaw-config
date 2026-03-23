# 每日快照 (Daily Snapshot) 功能技术设计方案

## 1. 需求概述

为 OpenClaw 实现对话历史的长期记忆系统，包含：
- SQLite 持久化：对话历史存储
- memoryFlush 触发器：40K tokens 自动刷盘
- 摘要提取：对话精华自动提取
- 知识图谱：graph.jsonl 实体关系建模

---

## 2. 现有架构分析

### 2.1 当前会话存储机制

```
~/.openclaw/agents/<agentId>/sessions/
├── sessions.json          # 会话索引 (sessionKey → metadata)
├── <sessionId>.jsonl      # 对话历史 (每个会话一个)
└── <sessionId>-topic-<threadId>.jsonl  # Telegram 话题会话
```

### 2.2 现有 memory SQLite 表结构

```sql
-- 现有 chunks 表（用于记忆/嵌入）
CREATE TABLE chunks (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'memory',
  start_line INTEGER NOT NULL,
  end_line INTEGER NOT NULL,
  hash TEXT NOT NULL,
  model TEXT NOT NULL,
  text TEXT NOT NULL,
  embedding TEXT NOT NULL,
  updated_at INTEGER NOT NULL
);

-- 现有 files 表
CREATE TABLE files (
  path TEXT PRIMARY KEY,
  source TEXT NOT NULL DEFAULT 'memory',
  hash TEXT NOT NULL,
  mtime INTEGER NOT NULL,
  size INTEGER NOT NULL
);

-- 现有 meta 表
CREATE TABLE meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
```

### 2.3 JSONL 对话记录格式

```json
{"type":"session","version":3,"id":"...","timestamp":"...","cwd":"..."}
{"type":"message","id":"...","parentId":"...","timestamp":"...","message":{"role":"user","content":[...]}}
{"type":"message","id":"...","parentId":"...","timestamp":"...","message":{"role":"assistant","content":[...]}}
{"type":"tool_use","id":"...","parentId":"...","timestamp":"...","tool":"exec","input":{...}}
{"type":"tool_result","id":"...","parentId":"...","timestamp":"...","tool":"exec","output":"..."}
```

---

## 3. SQLite 表结构设计

### 3.1 总体设计

在现有 `~/.openclaw/memory/main.sqlite` 中新增以下表：

```sql
-- ============================================
-- 对话会话快照表
-- ============================================
CREATE TABLE IF NOT EXISTS conversation_snapshots (
  id TEXT PRIMARY KEY,                      -- 快照唯一 ID (UUID)
  agent_id TEXT NOT NULL,                   -- Agent ID
  session_key TEXT NOT NULL,                -- 会话键 (如 agent:main:wecom:direct:xxx)
  session_id TEXT NOT NULL,                 -- 会话 ID (UUID)
  created_at INTEGER NOT NULL,              -- 创建时间戳 (毫秒)
  trigger_type TEXT NOT NULL,               -- 触发类型: 'auto' | 'manual' | 'daily' | 'threshold'
  token_count INTEGER NOT NULL,             -- 触发时的 token 数
  message_count INTEGER NOT NULL,           -- 会话消息数
  time_range_start INTEGER NOT NULL,        -- 对话时间范围起始
  time_range_end INTEGER NOT NULL,          -- 对话时间范围结束
  raw_jsonl_path TEXT,                      -- 原始 JSONL 文件路径 (可选保留)
  status TEXT DEFAULT 'pending',            -- 状态: pending | processing | completed | failed
  error_message TEXT                        -- 错误信息 (如果失败)
);

-- 索引
CREATE INDEX idx_snapshots_agent_id ON conversation_snapshots(agent_id);
CREATE INDEX idx_snapshots_session_key ON conversation_snapshots(session_key);
CREATE INDEX idx_snapshots_created_at ON conversation_snapshots(created_at);
CREATE INDEX idx_snapshots_status ON conversation_snapshots(status);

-- ============================================
-- 对话摘要表
-- ============================================
CREATE TABLE IF NOT EXISTS conversation_summaries (
  id TEXT PRIMARY KEY,                      -- 摘要 ID (UUID)
  snapshot_id TEXT NOT NULL,                -- 关联的快照 ID
  summary_text TEXT NOT NULL,               -- 摘要内容 (JSON 格式)
  key_topics TEXT,                          -- 关键主题 (JSON 数组)
  decisions TEXT,                           -- 决策要点 (JSON 数组)
  action_items TEXT,                        -- 行动项 (JSON 数组)
  entities TEXT,                            -- 实体列表 (JSON 数组)
  model_used TEXT NOT NULL,                 -- 使用的 LLM 模型
  prompt_tokens INTEGER,                    -- 摘要 prompt tokens
  completion_tokens INTEGER,                -- 摘要 completion tokens
  created_at INTEGER NOT NULL,              -- 创建时间戳
  FOREIGN KEY (snapshot_id) REFERENCES conversation_snapshots(id)
);

CREATE INDEX idx_summaries_snapshot_id ON conversation_summaries(snapshot_id);
CREATE INDEX idx_summaries_created_at ON conversation_summaries(created_at);

-- ============================================
-- 知识图谱实体表
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_entities (
  id TEXT PRIMARY KEY,                      -- 实体 ID (UUID)
  entity_type TEXT NOT NULL,                -- 实体类型
  entity_name TEXT NOT NULL,                -- 实体名称
  entity_attributes TEXT,                   -- 实体属性 (JSON 对象)
  first_seen_at INTEGER NOT NULL,           -- 首次出现时间
  last_seen_at INTEGER NOT NULL,            -- 最后出现时间
  occurrence_count INTEGER DEFAULT 1,       -- 出现次数
  source_snapshot_ids TEXT,                 -- 来源快照 IDs (JSON 数组)
  embedding TEXT,                           -- 实体嵌入向量 (可选)
  UNIQUE(entity_type, entity_name)          -- 同一类型下名称唯一
);

CREATE INDEX idx_entities_type ON knowledge_entities(entity_type);
CREATE INDEX idx_entities_name ON knowledge_entities(entity_name);
CREATE INDEX idx_entities_last_seen ON knowledge_entities(last_seen_at);

-- ============================================
-- 知识图谱关系表
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_relations (
  id TEXT PRIMARY KEY,                      -- 关系 ID (UUID)
  source_entity_id TEXT NOT NULL,           -- 源实体 ID
  target_entity_id TEXT NOT NULL,           -- 目标实体 ID
  relation_type TEXT NOT NULL,              -- 关系类型
  relation_strength REAL DEFAULT 1.0,       -- 关系强度 (0-1)
  context TEXT,                             -- 关系上下文描述
  first_seen_at INTEGER NOT NULL,           -- 首次发现时间
  last_seen_at INTEGER NOT NULL,            -- 最后更新时间
  occurrence_count INTEGER DEFAULT 1,       -- 出现次数
  source_snapshot_ids TEXT,                 -- 来源快照 IDs (JSON 数组)
  FOREIGN KEY (source_entity_id) REFERENCES knowledge_entities(id),
  FOREIGN KEY (target_entity_id) REFERENCES knowledge_entities(id)
);

CREATE INDEX idx_relations_source ON knowledge_relations(source_entity_id);
CREATE INDEX idx_relations_target ON knowledge_relations(target_entity_id);
CREATE INDEX idx_relations_type ON knowledge_relations(relation_type);

-- ============================================
-- 图谱导出记录表
-- ============================================
CREATE TABLE IF NOT EXISTS graph_exports (
  id TEXT PRIMARY KEY,                      -- 导出 ID
  snapshot_id TEXT,                         -- 关联的快照 ID (可选)
  file_path TEXT NOT NULL,                  -- 导出文件路径
  format_version TEXT NOT NULL,             -- 格式版本
  entity_count INTEGER,                     -- 实体数量
  relation_count INTEGER,                   -- 关系数量
  created_at INTEGER NOT NULL               -- 创建时间
);

CREATE INDEX idx_exports_created_at ON graph_exports(created_at);

-- ============================================
-- 配置表
-- ============================================
CREATE TABLE IF NOT EXISTS snapshot_config (
  key TEXT PRIMARY KEY,                     -- 配置键
  value TEXT NOT NULL,                      -- 配置值 (JSON)
  description TEXT,                         -- 配置描述
  updated_at INTEGER NOT NULL               -- 更新时间
);
```

---

## 4. memoryFlush 触发逻辑设计

### 4.1 触发时机

| 触发类型 | 条件 | 优先级 |
|---------|------|-------|
| **阈值触发** | 会话 token 数 ≥ 40K | 高 |
| **每日触发** | 每日固定时间（如凌晨 4:00） | 中 |
| **手动触发** | 用户发送 `/snapshot` 命令 | 高 |
| **空闲触发** | 会话空闲超过 N 小时 | 低 |

### 4.2 阈值检测逻辑

```typescript
// 伪代码: 阈值检测
interface MemoryFlushConfig {
  thresholdTokens: number;      // 默认 40000
  checkIntervalMs: number;      // 默认 60000 (1分钟)
  dailyAtHour: number;          // 默认 4 (凌晨4点)
  idleMinutes: number;          // 默认 120
}

function shouldTriggerFlush(session: Session): FlushTrigger | null {
  // 1. 阈值触发
  if (session.totalTokens >= config.thresholdTokens) {
    return {
      type: 'threshold',
      tokenCount: session.totalTokens
    };
  }

  // 2. 每日触发
  const now = new Date();
  const targetHour = config.dailyAtHour;
  if (now.getHours() === targetHour && now.getMinutes() === 0) {
    return { type: 'daily' };
  }

  // 3. 空闲触发
  const idleMs = Date.now() - session.lastActivityAt;
  if (idleMs >= config.idleMinutes * 60 * 1000) {
    return { type: 'idle' };
  }

  return null;
}
```

### 4.3 触发流程

```
┌─────────────────────────────────────────────────────────────┐
│                    memoryFlush 触发流程                       │
└─────────────────────────────────────────────────────────────┘

[触发条件满足]
       │
       ▼
┌──────────────────┐
│  1. 创建快照记录   │  ──→ 写入 conversation_snapshots 表
│  status='pending' │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  2. 导出对话数据   │  ──→ 从 JSONL 读取对话内容
│  status='processing'
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  3. 调用 LLM      │  ──→ 提取摘要和实体
│  提取摘要          │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  4. 存储摘要      │  ──→ 写入 conversation_summaries 表
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  5. 提取实体关系  │  ──→ 写入 knowledge_entities/relations 表
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  6. 导出 graph   │  ──→ 生成 graph.jsonl
│  .jsonl          │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  7. 更新快照状态  │  ──→ status='completed'
│  完成            │
└──────────────────┘
```

---

## 5. 摘要提取流程设计

### 5.1 摘要 Prompt 设计

```prompt
## 对话摘要提取

请分析以下对话历史，提取关键信息并以 JSON 格式返回。

### 对话历史
```
{{CONVERSATION_HISTORY}}
```

### 输出要求

请返回以下 JSON 结构（严格 JSON 格式，不要有额外文本）：

```json
{
  "summary": "100-200字的中文摘要，概括本次对话的核心内容",
  "key_topics": ["主题1", "主题2", "主题3"],
  "decisions": ["决定1（如果有）", "决定2（如果有）"],
  "action_items": ["行动项1（如果有）", "行动项2（如果有）"],
  "entities": [
    {"type": "person", "name": "人物名"},
    {"type": "project", "name": "项目名"},
    {"type": "file", "name": "文件名"},
    {"type": "tool", "name": "工具名"},
    {"type": "command", "name": "命令"},
    {"type": "concept", "name": "概念名"}
  ]
}
```

注意：
- summary 必须用中文撰写
- 只返回实际存在的内容，空列表用 []
- entities 中的 type 可选值: person, project, file, tool, command, concept, location, organization
```

### 5.2 摘要存储格式

```json
{
  "id": "summary-uuid",
  "snapshot_id": "snapshot-uuid",
  "summary_text": JSON.stringify({
    "summary": "摘要内容...",
    "key_topics": ["主题1", "主题2"],
    "decisions": ["决定1"],
    "action_items": ["行动项1"]
  }),
  "key_topics": "[\"主题1\", \"主题2\"]",
  "decisions": "[\"决定1\"]",
  "action_items": "[\"行动项1\"]",
  "entities": "[{\"type\":\"person\",\"name\":\"张明\"}]",
  "model_used": "cass-gpt/MiniMax-M2.5",
  "prompt_tokens": 1500,
  "completion_tokens": 300,
  "created_at": 1773892423000
}
```

---

## 6. 知识图谱结构设计

### 6.1 实体类型定义

| 类型 (entity_type) | 说明 | 示例 |
|-------------------|------|------|
| `person` | 人物 | "张明"、"李华" |
| `project` | 项目 | "OpenClaw"、"Star-Office-UI" |
| `file` | 文件 | "MEMORY.md"、"openclaw.json" |
| `tool` | 工具 | "exec"、"read"、"browser" |
| `command` | 命令 | "/snapshot"、"/compact" |
| `concept` | 概念 | "会话管理"、"memoryFlush" |
| `location` | 地点 | "上海"、"GitHub" |
| `organization` | 组织 | "Anthropic"、"OpenAI" |
| `model` | 模型 | "gpt-5.3-codex"、"MiniMax-M2.5" |
| `channel` | 渠道 | "telegram"、"wecom"、"discord" |

### 6.2 关系类型定义

| 关系类型 (relation_type) | 说明 | 示例 |
|------------------------|------|------|
| `used` | 使用 | person → tool |
| `created` | 创建 | person → file |
| `contains` | 包含 | project → file |
| `depends_on` | 依赖 | file → file |
| `mentioned_in` | 提及于 | concept → file |
| `belongs_to` | 属于 | person → organization |
| `works_on` | 工作于 | person → project |
| `communicates_via` | 通过...沟通 | person → channel |
| `triggered_by` | 触发 | command → concept |
| `similar_to` | 类似 | concept → concept |

### 6.3 graph.jsonl 格式

```jsonl
{"type":"entity","id":"ent-001","entity_type":"person","name":"张明","attributes":{"role":"开发者","id":"ou_123456"},"first_seen_at":1773892423000,"last_seen_at":1773892423000}
{"type":"entity","id":"ent-002","entity_type":"project","name":"OpenClaw","attributes":{"version":"2.0","language":"TypeScript"},"first_seen_at":1773892423000,"last_seen_at":1773892423000}
{"type":"entity","id":"ent-003","entity_type":"tool","name":"exec","attributes":{"category":"tooling","purpose":"执行shell命令"},"first_seen_at":1773892423000,"last_seen_at":1773892423000}
{"type":"relation","id":"rel-001","source_id":"ent-001","target_id":"ent-002","relation_type":"works_on","strength":1.0,"context":"张明是 OpenClaw 的核心开发者","first_seen_at":1773892423000,"last_seen_at":1773892423000}
{"type":"relation","id":"rel-002","source_id":"ent-001","target_id":"ent-003","relation_type":"used","strength":0.9,"context":"在开发过程中频繁使用 exec 工具","first_seen_at":1773892423000,"last_seen_at":1773892423000}
```

### 6.4 图谱文件输出

```typescript
// 输出路径: ~/.openclaw/memory/graphs/<agentId>/<date>.jsonl
// 例如: ~/.openclaw/memory/graphs/main/2026-03-19.jsonl
```

---

## 7. API 设计

### 7.1 核心 API

| API | 方法 | 说明 |
|-----|------|------|
| `/snapshot/trigger` | POST | 手动触发快照 |
| `/snapshot/status` | GET | 获取快照状态 |
| `/snapshot/list` | GET | 列出快照历史 |
| `/snapshot/:id` | GET | 获取快照详情 |
| `/summary/:sessionKey` | GET | 获取会话摘要 |
| `/graph/export` | GET | 导出知识图谱 |
| `/graph/query` | POST | 查询图谱 |

### 7.2 API 详细定义

```typescript
// POST /snapshot/trigger
interface TriggerSnapshotRequest {
  agentId: string;
  sessionKey?: string;  // 可选，不指定则对所有活跃会话触发
}

interface TriggerSnapshotResponse {
  snapshotIds: string[];
  status: 'triggered' | 'queued';
}

// GET /snapshot/list
interface ListSnapshotsRequest {
  agentId: string;
  limit?: number;       // 默认 20
  offset?: number;
  status?: 'pending' | 'processing' | 'completed' | 'failed';
}

interface ListSnapshotsResponse {
  snapshots: Snapshot[];
  total: number;
}

// GET /graph/export
interface ExportGraphRequest {
  agentId: string;
  format?: 'jsonl' | 'json';  // 默认 jsonl
  since?: number;             // 时间戳过滤
}

interface ExportGraphResponse {
  filePath: string;
  entityCount: number;
  relationCount: number;
}
```

---

## 8. 与现有架构兼容性

### 8.1 兼容性设计

1. **数据库兼容**
   - 复用现有 `~/.openclaw/memory/main.sqlite`
   - 新增表使用独立前缀避免冲突
   - 现有 chunks、files、meta 表保持不变

2. **会话存储兼容**
   - 不修改现有 sessions.json 和 JSONL 格式
   - 快照功能作为独立层，不影响正常会话流程

3. **配置兼容**
   - 通过 openclaw.json 配置新功能
   - 默认值确保向后兼容

### 8.2 配置项

```json5
{
  "snapshot": {
    "enabled": true,
    "thresholdTokens": 40000,
    "checkIntervalMs": 60000,
    "dailyAtHour": 4,
    "idleMinutes": 120,
    "outputPath": "~/.openclaw/memory/graphs/{agentId}/{date}.jsonl",
    "retention": {
      "snapshots": 30,      // 保留30天快照
      "summaries": 90,      // 保留90天摘要
      "graphFiles": 365     // 保留365天图谱文件
    },
    "model": {
      "provider": "cass-codex",
      "modelId": "gpt-5.3-codex"
    }
  }
}
```

---

## 9. 文件结构

```
~/.openclaw/
├── memory/
│   ├── main.sqlite                 # 现有数据库
│   ├── graphs/                     # 新增: 图谱导出目录
│   │   └── {agentId}/
│   │       ├── 2026-03-19.jsonl
│   │       └── 2026-03-20.jsonl
│   └── snapshots/                  # 新增: 快照备份(可选)
│       └── {agentId}/
│           └── {sessionId}/
│               └── snapshot.json
└── agents/
    └── {agentId}/
        └── sessions/
            ├── sessions.json       # 现有会话索引
            └── {sessionId}.jsonl   # 现有对话历史
```

---

## 10. 实现优先级

| 阶段 | 功能 | 描述 |
|-----|------|------|
| **Phase 1** | 基础快照 | SQLite 表结构、阈值触发、JSONL 读取 |
| **Phase 2** | 摘要提取 | LLM 调用、摘要存储 |
| **Phase 3** | 知识图谱 | 实体关系提取、graph.jsonl 生成 |
| **Phase 4** | 增强功能 | 每日触发、查询 API、图谱检索 |

---

## 11. 验收标准

- [ ] SQLite 表结构设计完成
- [ ] memoryFlush 触发时机明确（40K阈值、每日、手动）
- [ ] 摘要提取 Prompt 和存储格式明确
- [ ] 知识图谱数据模型完整（10种实体类型、10种关系类型）
- [ ] graph.jsonl 格式规范确定
- [ ] 与现有 OpenClaw 架构兼容
- [ ] 配置项设计合理

---

## 12. 附录

### A. Token 计数估算

```typescript
// 估算公式 (近似)
function estimateTokens(text: string): number {
  // 中文: 字符数 / 2
  // 英文: 字符数 / 4
  const chineseChars = (text.match(/[\u4e00-\u9fa5]/g) || []).length;
  const otherChars = text.length - chineseChars;
  return Math.ceil(chineseChars / 2 + otherChars / 4);
}
```

### B. 实体去重逻辑

```typescript
// 实体合并策略
function mergeEntity(existing: Entity, newEntity: Entity): Entity {
  return {
    ...existing,
    occurrence_count: existing.occurrence_count + 1,
    last_seen_at: Math.max(existing.last_seen_at, newEntity.last_seen_at),
    source_snapshot_ids: union(
      existing.source_snapshot_ids,
      newEntity.source_snapshot_ids
    )
  };
}
```