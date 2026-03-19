#!/usr/bin/env python3
"""
Graph Query Skill - 知识图谱快速查询
查询延时 < 200ms，支持模糊搜索和实体类型过滤
"""

import sys
import os
import sqlite3
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# 配置
GRAPHS_DIR = os.path.expanduser("~/.openclaw/memory/graphs")
QUERY_DB = os.path.join(GRAPHS_DIR, "query.db")
DEFAULT_LIMIT = 10
FUZZY_THRESHOLD = 0.7  # 模糊匹配阈值


def get_today_graph_file():
    """获取今日图谱文件路径"""
    today = datetime.now().strftime("%Y-%m-%d")
    graph_file = os.path.join(GRAPHS_DIR, f"graph_{today}.jsonl")
    
    # 如果今日文件不存在，尝试找最新的
    if not os.path.exists(graph_file):
        files = sorted(Path(GRAPHS_DIR).glob("graph_*.jsonl"), reverse=True)
        if files:
            graph_file = str(files[0])
    
    return graph_file


def init_query_db():
    """初始化查询数据库和索引"""
    conn = sqlite3.connect(QUERY_DB)
    cursor = conn.cursor()
    
    # 创建实体表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT UNIQUE NOT NULL,
            entity_type TEXT NOT NULL,
            label TEXT NOT NULL,
            label_lower TEXT,
            properties TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建关系表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_node TEXT NOT NULL,
            to_node TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建索引 - 关键性能优化
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_label ON entities(label)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_label_lower ON entities(label_lower)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_relation_from ON relations(from_node)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_relation_to ON relations(to_node)")
    
    conn.commit()
    return conn


def rebuild_index():
    """重建索引 - 从 graph.jsonl 导入数据"""
    print("🔄 正在重建图谱索引...")
    start_time = time.time()
    
    graph_file = get_today_graph_file()
    if not os.path.exists(graph_file):
        return f"❌ 图谱文件不存在: {graph_file}"
    
    conn = init_query_db()
    cursor = conn.cursor()
    
    # 清空现有数据
    cursor.execute("DELETE FROM entities")
    cursor.execute("DELETE FROM relations")
    
    # 导入数据
    entities_count = 0
    relations_count = 0
    
    with open(graph_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                
                # 判断是节点还是边
                if 'id' in data and 'type' in data:
                    # 节点
                    node_id = data.get('id')
                    entity_type = data.get('type')
                    label = data.get('label', '')
                    properties = json.dumps(data.get('properties', {}), ensure_ascii=False)
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO entities (node_id, entity_type, label, properties, label_lower)
                        VALUES (?, ?, ?, ?, ?)
                    """, (node_id, entity_type, label, properties, label.lower()))
                    entities_count += 1
                    
                elif 'from' in data and 'to' in data:
                    # 边
                    from_node = data.get('from')
                    to_node = data.get('to')
                    relation_type = data.get('type')
                    
                    cursor.execute("""
                        INSERT INTO relations (from_node, to_node, relation_type)
                        VALUES (?, ?, ?)
                    """, (from_node, to_node, relation_type))
                    relations_count += 1
                    
            except json.JSONDecodeError:
                continue
    
    conn.commit()
    conn.close()
    
    elapsed = time.time() - start_time
    return f"✅ 索引重建完成: {entities_count} 实体, {relations_count} 关系, 耗时 {elapsed:.2f}s"


def query_entities(entity_type=None, keyword=None, limit=DEFAULT_LIMIT):
    """查询实体 - 核心查询函数"""
    conn = sqlite3.connect(QUERY_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    start_time = time.time()
    
    # 构建查询
    if keyword:
        # 模糊搜索
        keyword_lower = keyword.lower()
        if entity_type:
            cursor.execute("""
                SELECT * FROM entities 
                WHERE entity_type = ? AND label_lower LIKE ?
                ORDER BY label
                LIMIT ?
            """, (entity_type, f"%{keyword_lower}%", limit))
        else:
            cursor.execute("""
                SELECT * FROM entities 
                WHERE label_lower LIKE ?
                ORDER BY label
                LIMIT ?
            """, (f"%{keyword_lower}%", limit))
    elif entity_type:
        # 按类型查询
        cursor.execute("""
            SELECT * FROM entities 
            WHERE entity_type = ?
            ORDER BY node_id DESC
            LIMIT ?
        """, (entity_type, limit))
    else:
        # 查询所有（默认查最近）
        cursor.execute("""
            SELECT * FROM entities 
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
    
    results = cursor.fetchall()
    elapsed = time.time() - start_time
    
    conn.close()
    
    return results, elapsed


def query_relations(node_id=None, limit=DEFAULT_LIMIT):
    """查询关系"""
    conn = sqlite3.connect(QUERY_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    start_time = time.time()
    
    if node_id:
        cursor.execute("""
            SELECT * FROM relations 
            WHERE from_node = ? OR to_node = ?
            LIMIT ?
        """, (node_id, node_id, limit))
    else:
        cursor.execute("""
            SELECT * FROM relations 
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
    
    results = cursor.fetchall()
    elapsed = time.time() - start_time
    
    conn.close()
    return results, elapsed


def format_results(entities, relations, query_time):
    """格式化结果为 LLM 可用的上下文"""
    output = []
    output.append(f"## 📊 图谱查询结果")
    output.append(f"查询耗时: {query_time*1000:.1f}ms")
    output.append("")
    
    if not entities and not relations:
        output.append("*未找到相关图谱数据*")
        return "\n".join(output)
    
    # 实体结果
    if entities:
        output.append("### 相关实体")
        for i, row in enumerate(entities, 1):
            entity_type = row['entity_type']
            label = row['label']
            props = json.loads(row['properties']) if row['properties'] else {}
            
            # 格式化摘要
            if entity_type == 'session':
                summary = props.get('session_id', '')[:12] + "..."
            elif entity_type == 'tool':
                summary = "工具"
            else:
                summary = ""
            
            output.append(f"{i}. `[{entity_type}]` {label} {summary}")
        output.append("")
    
    # 关系结果
    if relations:
        output.append("### 相关关系")
        for row in relations:
            from_node = row['from_node']
            to_node = row['to_node']
            rel_type = row['relation_type']
            output.append(f"- `{from_node[:16]}...` --[{rel_type}]--> `{to_node}`")
        output.append("")
    
    return "\n".join(output)


def handle_query(args):
    """处理查询请求"""
    # 确保索引存在
    if not os.path.exists(QUERY_DB):
        rebuild_msg = rebuild_index()
        print(rebuild_msg)
    
    entity_type = None
    keyword = None
    limit = DEFAULT_LIMIT
    
    # 解析参数
    for arg in args:
        if arg in ['session', 'tool', 'keyword', 'user_message']:
            entity_type = arg
        elif arg == 'relates' and len(args) > 1:
            # 关系查询
            node_id = args[1]
            relations, t = query_relations(node_id, limit)
            entities = []
            return format_results(entities, relations, t)
        elif arg == 'rebuild':
            return rebuild_index()
        elif arg == 'stats':
            return show_stats()
        else:
            keyword = arg
    
    # 执行查询
    entities, t = query_entities(entity_type, keyword, limit)
    relations, t2 = query_relations(limit=5)
    
    return format_results(entities, relations, t + t2)


def show_stats():
    """显示图谱统计信息"""
    conn = sqlite3.connect(QUERY_DB)
    cursor = conn.cursor()
    
    cursor.execute("SELECT entity_type, COUNT(*) as cnt FROM entities GROUP BY entity_type")
    type_counts = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM relations")
    rel_count = cursor.fetchone()[0]
    
    conn.close()
    
    output = ["## 📈 图谱统计"]
    for row in type_counts:
        output.append(f"- {row[0]}: {row[1]}")
    output.append(f"- 关系总数: {rel_count}")
    
    return "\n".join(output)


def check_skill_trigger(user_input):
    """检查是否触发图谱查询技能"""
    triggers = [
        "query-graph", "/kg", "kg ", "查询图谱", 
        "图谱查询", "search graph", "find entity",
        "图谱搜索", "搜索图谱"
    ]
    user_lower = user_input.lower()
    return any(t in user_lower for t in triggers)


if __name__ == "__main__":
    # 从参数获取输入
    user_input = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    
    # 如果没有直接输入，尝试从 stdin 读取
    if not user_input:
        try:
            user_input = input("请输入查询: ")
        except:
            user_input = "stats"
    
    # 解析命令
    parts = user_input.split()
    
    # 执行
    if check_skill_trigger(user_input) or parts[0] in ['/kg', 'query-graph']:
        # 去掉命令前缀
        args = [p for p in parts if not p.startswith('/') and p != 'query-graph']
        result = handle_query(args)
        print(result)
    else:
        print("未识别为图谱查询命令")