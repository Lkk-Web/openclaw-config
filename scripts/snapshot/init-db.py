#!/usr/bin/env python3
"""
SQLite 数据库初始化脚本
创建快照所需的 6 张表
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.expanduser("~/.openclaw/memory/snapshot.db")

def init_db():
    """初始化数据库表结构"""
    # 确保目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. snapshots 表 - 快照记录
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT UNIQUE NOT NULL,
            agent_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            token_count INTEGER DEFAULT 0,
            trigger_type TEXT DEFAULT 'manual',
            summary TEXT,
            graph_export_path TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    
    # 2. sessions 表 - 会话记录
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            agent_id TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            message_count INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            cwd TEXT
        )
    """)
    
    # 3. messages 表 - 消息记录
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE NOT NULL,
            session_id TEXT NOT NULL,
            parent_id TEXT,
            role TEXT NOT NULL,
            content TEXT,
            timestamp TEXT NOT NULL,
            token_count INTEGER DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    
    # 4. tools 表 - 工具调用记录
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_id TEXT UNIQUE NOT NULL,
            session_id TEXT NOT NULL,
            message_id TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            arguments TEXT,
            result TEXT,
            is_error INTEGER DEFAULT 0,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    
    # 5. summaries 表 - 摘要记录
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            summary_id TEXT UNIQUE NOT NULL,
            snapshot_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            content TEXT NOT NULL,
            keywords TEXT,
            created_at TEXT NOT NULL,
            model_used TEXT,
            FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id)
        )
    """)
    
    # 6. knowledge_graph 表 - 知识图谱节点
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_graph (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT UNIQUE NOT NULL,
            node_type TEXT NOT NULL,
            label TEXT NOT NULL,
            properties TEXT,
            snapshot_id TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id)
        )
    """)
    
    # 创建索引以提高查询性能
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_agent ON sessions(agent_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tools_session ON tools(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_status ON snapshots(status)")
    
    conn.commit()
    conn.close()
    
    print(f"✅ 数据库初始化完成: {DB_PATH}")
    print("📋 创建的表:")
    print("   - snapshots (快照记录)")
    print("   - sessions (会话记录)")
    print("   - messages (消息记录)")
    print("   - tools (工具调用)")
    print("   - summaries (摘要记录)")
    print("   - knowledge_graph (知识图谱)")

if __name__ == "__main__":
    init_db()