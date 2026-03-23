#!/usr/bin/env node

/**
 * Knowledge Graph Import Script
 * 将 graphs 目录中的数据导入到 knowledge_graph 表
 */

const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');

const GRAPH_DIR = path.join(process.env.HOME || process.env.USERPROFILE, '.openclaw/memory/graphs');
const DB_PATH = path.join(process.env.HOME || process.env.USERPROFILE, '.openclaw/memory/snapshot.db');

function main() {
  console.log('🔷 Knowledge Graph Import Tool');
  console.log('================================\n');

  const db = new Database(DB_PATH);

  // 获取所有 jsonl 文件
  const files = fs.readdirSync(GRAPH_DIR)
    .filter(f => f.endsWith('.jsonl'))
    .sort()
    .reverse(); // 最新的优先

  if (files.length === 0) {
    console.log('❌ 没有找到图数据文件');
    db.close();
    return;
  }

  console.log(`📂 发现 ${files.length} 个图数据文件\n`);

  const insertStmt = db.prepare(`
    INSERT OR IGNORE INTO knowledge_graph (node_id, node_type, label, properties, created_at)
    VALUES (?, ?, ?, ?, ?)
  `);

  let totalImported = 0;
  let totalDuplicates = 0;

  for (const file of files) {
    const filePath = path.join(GRAPH_DIR, file);
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n').filter(line => line.trim());

    console.log(`📄 处理 ${file} (${lines.length} 条)...`);

    const transaction = db.transaction(() => {
      for (const line of lines) {
        try {
          const node = JSON.parse(line);
          const result = insertStmt.run(
            node.id,
            node.type || 'unknown',
            node.label || node.id,
            node.properties ? JSON.stringify(node.properties) : null,
            new Date().toISOString()
          );
          if (result.changes > 0) {
            totalImported++;
          } else {
            totalDuplicates++;
          }
        } catch (e) {
          // 跳过解析错误的行
        }
      }
    });

    transaction();
  }

  console.log('\n========================================');
  console.log(`✅ 导入完成! 新增: ${totalImported}, 跳过(已存在): ${totalDuplicates}`);

  const total = db.prepare('SELECT COUNT(*) as count FROM knowledge_graph').get();
  console.log(`📊 知识图谱共有 ${total.count} 个实体`);

  db.close();
}

main();