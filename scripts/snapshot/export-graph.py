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

    # 只记录用户问答会话，排除工具调用相关内容
    # 工具相关实体不再导出

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
    # 只记录用户问答关系，排除工具调用
    # 同一会话内的问答关系
    user_sessions = set()
    for msg in messages:
        session_id, message_id, role, content, timestamp, token_count = msg
        
        # 跳过工具调用相关的内容
        if content and ("toolCall" in content or "[Tool:" in content or "tool_call" in content):
            continue
        
        # 用户消息节点
        if role == "user" and session_id:
            user_sessions.add(session_id)
    
    # 创建同一会话内的问答关系边
    for session_id in user_sessions:
        edges.append({
            "from": f"session_{session_id[:8]}",
            "to": f"session_{session_id[:8]}",
            "type": "qa_session"
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

    # 从消息内容中提取实体（只记录用户问答，排除工具调用）
    for msg in messages:
        msg_id, role, content, timestamp = msg
        if not content:
            continue

        # 跳过工具调用相关的内容
        if "toolCall" in content or "[Tool:" in content or "tool_call" in content:
            continue

        # 用户消息实体
        if role == "user":
            entities.append({
                "id": f"user_msg_{msg_id[:8]}",
                "type": "user_message",
                "label": content[:50] + "..." if len(content) > 50 else content,
                "properties": {"timestamp": timestamp, "session_id": session_id}
            })
        
        # 助手消息实体
        if role == "assistant":
            entities.append({
                "id": f"assistant_msg_{msg_id[:8]}",
                "type": "assistant_message",
                "label": content[:50] + "..." if len(content) > 50 else content,
                "properties": {"timestamp": timestamp, "session_id": session_id}
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

    # 生成图谱数据（只记录用户问答，排除工具调用）
    nodes = []
    edges = []

    sessions = set()

    for msg in messages:
        session_id, msg_id, role, content, timestamp, tokens = msg
        sessions.add(session_id)
        
        # 跳过工具调用相关的内容
        if content and ("toolCall" in content or "[Tool:" in content or "tool_call" in content):
            continue

    # 创建会话节点
    for sid in sessions:
        nodes.append({
            "id": f"session_{sid[:8]}",
            "type": "session",
            "label": f"会话 {sid[:8]}",
            "properties": {"session_id": sid}
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
    print(f"   - 节点数: {len(nodes)}")
    print(f"   - 边数: {len(edges)}")
    print(f"   (已排除工具调用)")

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
    
    # 获取每个会话的核心用户问答作为摘要（只显示用户消息）
    session_summaries = {}
    for sid in session_ids:
        # 只获取 role='user' 的用户消息，排除系统消息和工具调用
        cursor.execute("""
            SELECT content FROM messages 
            WHERE session_id = ? 
            AND role = 'user' 
            AND content NOT LIKE 'Conversation info%'
            AND content NOT LIKE 'Sender (untrusted%'
            AND content NOT LIKE '%[Internal task completion%'
            AND content NOT LIKE '%[Tool: %'
            AND content IS NOT NULL
            AND content != ''
            ORDER BY timestamp LIMIT 1
        """, (sid,))
        result = cursor.fetchone()
        
        if result and result[0]:
            # 提取实际文本内容
            content = result[0]
            import re
            text_match = re.search(r'(?:text|text\":\")([^\"]+)', content)
            if text_match:
                summary = text_match.group(1)[:80]
            else:
                summary = content[:80].replace('\n', ' ').strip()
            if len(content) > 80:
                summary += "..."
            session_summaries[sid] = summary
        else:
            # 没有用户消息时标记为非用户会话
            session_summaries[sid] = None
    
    # 过滤出有用户问答的会话
    user_sessions = {sid: summary for sid, summary in session_summaries.items() if summary}
    
    # 显示核心用户会话
    print(f"\n📋 核心用户会话:")
    if user_sessions:
        for i, sid in enumerate(sorted(user_sessions.keys())[:5]):
            summary = user_sessions[sid]
            # 获取该会话的消息数
            cursor.execute("SELECT COUNT(*) FROM messages WHERE session_id = ?", (sid,))
            result = cursor.fetchone()
            msg_count = result[0] if result else 0
            # 清理元数据前缀
            import re
            summary = re.sub(r'^\[Internal.*?\]\s*', '', summary)
            # 获取前60字符
            if summary and len(summary) > 60:
                summary = summary[:60] + "..."
            print(f"   • {sid[:12]}... | {msg_count}条消息 | 用户请求：{summary}")
        if len(user_sessions) > 5:
            print(f"   ... 等共 {len(user_sessions)} 个用户会话")
    else:
        print("   (无核心用户会话)")

    # 生成图谱（只记录用户问答会话，排除工具调用）
    nodes = []
    edges = []

    # 记录已添加的会话
    added_sessions = set()
    
    for msg in messages:
        session_id, msg_id, role, content, timestamp, tokens = msg

        # 跳过工具调用相关的内容
        if content and ("toolCall" in content or "[Tool:" in content or "tool_call" in content):
            continue

        # 只创建有用户问答的会话节点
        if session_id and session_id in user_sessions:
            sid = session_id[:8]
            if sid not in added_sessions:
                added_sessions.add(sid)
                nodes.append({
                    "id": f"session_{sid}",
                    "type": "session",
                    "label": f"会话 {sid}",
                    "properties": {"session_id": session_id, "summary": user_sessions.get(session_id, "")}
                })
    
    # 移除工具统计信息输出
    print(f"   - 工具数: 0 (已排除)")

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
    print(f"   - 用户会话数: {len(user_sessions)}")
    print(f"   - 节点数: {len(nodes)}")
    print(f"   - 边数: {len(edges)}")
    print(f"   (已排除工具调用相关内容)")

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