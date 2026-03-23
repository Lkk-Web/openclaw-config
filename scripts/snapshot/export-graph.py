#!/usr/bin/env python3
"""
知识图谱导出脚本
从数据库导出图谱数据到 graph.jsonl 格式
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime
from collections import defaultdict

DB_PATH = os.path.expanduser("~/.openclaw/memory/snapshot.db")
GRAPH_OUTPUT_DIR = os.path.expanduser("~/.openclaw/memory/graphs")

def export_to_jsonl(snapshot_id, output_path=None):
    """导出图谱到 JSONL 格式"""
    if not os.path.exists(DB_PATH):
        print("❌ 数据库不存在")
        return False

    os.makedirs(GRAPH_OUTPUT_DIR, exist_ok=True)

    if output_path is None:
        output_path = os.path.join(GRAPH_OUTPUT_DIR, f"{snapshot_id}.jsonl")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 获取会话和消息数据
    cursor.execute("""
        SELECT session_id, message_id, role, content, timestamp, token_count
        FROM messages
        WHERE session_id IN (
            SELECT session_id FROM snapshots WHERE snapshot_id = ?
        )
        ORDER BY timestamp
    """, (snapshot_id,))

    messages = cursor.fetchall()

    # 提取实体和关系
    nodes = []
    edges = []
    entities = set()

    # 工具相关实体
    tool_usage = defaultdict(int)
    cursor.execute("""
        SELECT tool_name, COUNT(*) as count
        FROM tools
        WHERE session_id IN (
            SELECT session_id FROM snapshots WHERE snapshot_id = ?
        )
        GROUP BY tool_name
    """, (snapshot_id,))

    for tool_name, count in cursor.fetchall():
        tool_node = {
            "id": f"tool_{tool_name}",
            "type": "tool",
            "label": tool_name,
            "properties": {"usage_count": count}
        }
        nodes.append(tool_node)

    # 关键词实体
    cursor.execute("""
        SELECT keywords FROM summaries WHERE snapshot_id = ?
    """, (snapshot_id,))

    for (keywords,) in cursor.fetchall():
        if keywords:
            for kw in keywords.split(","):
                kw = kw.strip()
                if kw and kw not in entities:
                    entities.add(kw)
                    nodes.append({
                        "id": f"keyword_{kw}",
                        "type": "keyword",
                        "label": kw,
                        "properties": {}
                    })

    # 会话节点
    session_ids = set()
    for msg in messages:
        session_id = msg[0]
        if session_id and session_id not in session_ids:
            session_ids.add(session_id)
            nodes.append({
                "id": f"session_{session_id[:8]}",
                "type": "session",
                "label": f"会话 {session_id[:8]}",
                "properties": {"session_id": session_id}
            })

    # 创建边（关系）
    # 会话 -> 工具使用关系
    for session_id in session_ids:
        cursor.execute("""
            SELECT DISTINCT tool_name FROM tools WHERE session_id = ?
        """, (session_id,))

        for (tool_name,) in cursor.fetchall():
            edges.append({
                "from": f"session_{session_id[:8]}",
                "to": f"tool_{tool_name}",
                "type": "uses"
            })

    conn.close()

    # 写入 JSONL 文件
    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入节点
        for node in nodes:
            f.write(json.dumps(node, ensure_ascii=False) + "\n")

        # 写入边
        for edge in edges:
            f.write(json.dumps(edge, ensure_ascii=False) + "\n")

    print(f"✅ 图谱导出完成: {output_path}")
    print(f"   - 节点数: {len(nodes)}")
    print(f"   - 边数: {len(edges)}")

    return True

def generate_graph_from_messages(snapshot_id, session_id=None):
    """从消息生成图谱数据"""
    if not os.path.exists(DB_PATH):
        print("❌ 数据库不存在")
        return []

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if session_id:
        query = """
            SELECT message_id, role, content, timestamp
            FROM messages
            WHERE session_id = ?
            ORDER BY timestamp
        """
        cursor.execute(query, (session_id,))
    else:
        query = """
            SELECT message_id, role, content, timestamp
            FROM messages
            ORDER BY timestamp DESC
            LIMIT 1000
        """
        cursor.execute(query)

    messages = cursor.fetchall()
    conn.close()

    # 实体提取
    entities = []

    # 从消息内容中提取实体
    for msg in messages:
        msg_id, role, content, timestamp = msg
        if not content:
            continue

        # 用户实体
        if role == "user":
            entities.append({
                "id": f"user_msg_{msg_id[:8]}",
                "type": "user_message",
                "label": content[:50] + "..." if len(content) > 50 else content,
                "properties": {"timestamp": timestamp, "session_id": session_id}
            })

        # 工具调用实体
        if "toolCall" in content or "Tool:" in content:
            # 提取工具名
            import re
            tools = re.findall(r'\[Tool: (\w+)\]', content)
            for tool in tools:
                entities.append({
                    "id": f"tool_{tool}_{msg_id[:8]}",
                    "type": "tool_usage",
                    "label": tool,
                    "properties": {"timestamp": timestamp}
                })

    return entities

def export_daily_snapshot(output_dir=None):
    """导出每日快照图谱"""
    if output_dir is None:
        output_dir = GRAPH_OUTPUT_DIR

    os.makedirs(output_dir, exist_ok=True)

    from datetime import datetime, timedelta
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = os.path.join(output_dir, f"graph_{today}.jsonl")

    if not os.path.exists(DB_PATH):
        print("❌ 数据库不存在")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 获取今日消息
    today_start = f"{today}T00:00:00"

    cursor.execute("""
        SELECT session_id, message_id, role, content, timestamp, token_count
        FROM messages
        WHERE timestamp >= ?
        ORDER BY timestamp
    """, (today_start,))

    messages = cursor.fetchall()

    if not messages:
        print("⚠️ 今日没有消息")
        conn.close()
        return False

    # 生成图谱数据
    nodes = []
    edges = []

    sessions = set()
    tools_used = {}

    for msg in messages:
        session_id, msg_id, role, content, timestamp, tokens = msg
        sessions.add(session_id)

        # 提取工具使用
        import re
        tool_matches = re.findall(r'\[Tool: (\w+)\]', content or "")
        for tool in tool_matches:
            if tool not in tools_used:
                tools_used[tool] = []
            tools_used[tool].append(session_id)

    # 创建会话节点
    for sid in sessions:
        nodes.append({
            "id": f"session_{sid[:8]}",
            "type": "session",
            "label": f"会话 {sid[:8]}",
            "properties": {"session_id": sid}
        })

    # 创建工具节点和边
    for tool, sids in tools_used.items():
        tool_id = f"tool_{tool}"
        nodes.append({
            "id": tool_id,
            "type": "tool",
            "label": tool,
            "properties": {"usage_count": len(sids)}
        })

        for sid in sids:
            edges.append({
                "from": f"session_{sid[:8]}",
                "to": tool_id,
                "type": "uses"
            })

    conn.close()

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        for node in nodes:
            f.write(json.dumps(node, ensure_ascii=False) + "\n")
        for edge in edges:
            f.write(json.dumps(edge, ensure_ascii=False) + "\n")

    print(f"✅ 每日图谱导出完成: {output_path}")
    print(f"   - 会话数: {len(sessions)}")
    print(f"   - 工具数: {len(tools_used)}")
    print(f"   - 节点数: {len(nodes)}")
    print(f"   - 边数: {len(edges)}")

    return True

def export_incremental():
    """增量导出图谱（自上次导出后）"""
    os.makedirs(GRAPH_OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(DB_PATH):
        print("❌ 数据库不存在")
        return False

    # 增量状态文件：记录上次导出到哪个时间点了
    last_export_file = os.path.join(GRAPH_OUTPUT_DIR, ".last_incremental_export")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查是否有消息
    cursor.execute("SELECT COUNT(*) FROM messages")
    msg_count = cursor.fetchone()[0]
    if msg_count == 0:
        print("⚠️ 数据库中没有消息，请先运行导入")
        conn.close()
        return False

    # 读取上次导出时间点
    last_time = None
    if os.path.exists(last_export_file):
        with open(last_export_file, 'r') as f:
            last_time = f.read().strip()
        print(f"📎 上次导出时间点: {last_time}")
    else:
        print("📎 首次增量导出（全量）")

    # 查询增量消息（时间戳大于上次导出时间）
    if last_time:
        cursor.execute("""
            SELECT session_id, message_id, role, content, timestamp, token_count
            FROM messages
            WHERE timestamp > ?
            ORDER BY timestamp
        """, (last_time,))
    else:
        # 首次导出，获取所有消息
        cursor.execute("""
            SELECT session_id, message_id, role, content, timestamp, token_count
            FROM messages
            ORDER BY timestamp
        """)

    messages = cursor.fetchall()

    if not messages:
        print("⚠️ 没有新增消息")
        conn.close()
        return False

    # 记录本次导出的最新消息时间，用于下次增量（timestamp 在第 4 列）
    max_timestamp = max(msg[4] for msg in messages if msg[4])
    print(f"📥 找到 {len(messages)} 条新消息")
    print(f"📎 本次导出最新时间: {max_timestamp}")

    # 获取涉及的会话
    session_ids = set(msg[0] for msg in messages if msg[0])
    print(f"📥 涉及 {len(session_ids)} 个新会话")

    # 生成图谱
    nodes = []
    edges = []
    tools_used = {}

    for msg in messages:
        session_id, msg_id, role, content, timestamp, tokens = msg

        # 会话节点
        if session_id:
            sid = session_id[:8]
            if not any(n.get("id") == f"session_{sid}" for n in nodes):
                nodes.append({
                    "id": f"session_{sid}",
                    "type": "session",
                    "label": f"会话 {sid}",
                    "properties": {"session_id": session_id}
                })

        # 提取工具
        import re
        tool_matches = re.findall(r'\[Tool: (\w+)\]', content or "")
        for tool in tool_matches:
            if tool not in tools_used:
                tools_used[tool] = set()
            if session_id:
                tools_used[tool].add(session_id)

    # 创建工具节点和边
    for tool, sids in tools_used.items():
        tool_id = f"tool_{tool}"
        nodes.append({
            "id": tool_id,
            "type": "tool",
            "label": tool,
            "properties": {"usage_count": len(sids)}
        })

        for sid in sids:
            edges.append({
                "from": f"session_{sid[:8]}",
                "to": tool_id,
                "type": "uses"
            })

    # 记录本次导出的时间点，供下次增量使用
    if max_timestamp:
        with open(last_export_file, 'w') as f:
            f.write(max_timestamp)
    
    conn.close()

    # 写入文件
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(GRAPH_OUTPUT_DIR, f"graph_incremental_{timestamp}.jsonl")

    with open(output_path, 'w', encoding='utf-8') as f:
        for node in nodes:
            f.write(json.dumps(node, ensure_ascii=False) + "\n")
        for edge in edges:
            f.write(json.dumps(edge, ensure_ascii=False) + "\n")

    print(f"✅ 增量图谱导出完成: {output_path}")
    print(f"   - 会话数: {len(session_ids)}")
    print(f"   - 工具数: {len(tools_used)}")
    print(f"   - 节点数: {len(nodes)}")
    print(f"   - 边数: {len(edges)}")

    return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "daily":
            export_daily_snapshot()
        elif sys.argv[1] == "incremental":
            export_incremental()
        elif sys.argv[1] == "session" and len(sys.argv) > 2:
            session_id = sys.argv[2]
            snapshot_id = f"snap_{session_id[:8]}"
            export_to_jsonl(snapshot_id)
        else:
            print("Usage:")
            print("  python export-graph.py daily           - 导出今日图谱")
            print("  python export-graph.py session <id>   - 导出指定会话图谱")
    else:
        print("Usage:")
        print("  python export-graph.py daily           - 导出今日图谱")
        print("  python export-graph.py session <id>   - 导出指定会话图谱")