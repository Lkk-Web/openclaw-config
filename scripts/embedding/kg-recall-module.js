#!/usr/bin/env node
/**
 * 记忆召回模块 - 可被主调度者调用
 * 
 * 用法: node kg-recall-module.js "<查询文本>"
 * 返回: 格式化记忆字符串或空
 */

const Database = require('better-sqlite3');
const { execSync } = require('child_process');
const os = require('os');

// 配置
const CONFIG = {
  dbPath: os.homedir() + '/.openclaw/memory/snapshot.db',
  apiUrl: 'http://116.63.86.12:3000/v1/embeddings',
  apiKey: process.env.EMBEDDING_API_KEY || '',
  model: 'm3e-large',
  proxy: 'localhost:7897',
  topK: 5,
  minSimilarity: 0.15,  // 最低相似度阈值
  
  // 过滤配置：排除低价值的 tool 标签
  excludeTools: ['exec', 'edit', 'read', 'write', 'memory_search', 'sessions_history', 'process'],
  
  // 只保留这些核心 tool
  allowedTools: ['sessions_list', 'sessions_spawn', 'sessions_send', 'subagents', 'message', 'session_status', 'browser', 'agents_list', 'sessions_yield', 'canvas', 'cron', 'gateway']
};

let db;
function initDb() {
  if (!db) {
    db = new Database(CONFIG.dbPath);
    db.pragma('journal_mode = WAL');
  }
  return db;
}

function getEmbedding(text) {
  try {
    const cmd = `curl -s -x ${CONFIG.proxy} "${CONFIG.apiUrl}" \
      -H "Authorization: Bearer ${CONFIG.apiKey}" \
      -H "Content-Type: application/json" \
      -d ${JSON.stringify(JSON.stringify({ model: CONFIG.model, input: [text] }))}`;
    
    const result = execSync(cmd, { encoding: 'utf8' });
    const data = JSON.parse(result);
    return data.data[0].embedding;
  } catch (e) {
    return null;
  }
}

function cosineSimilarity(a, b) {
  if (!a || !b || a.length !== b.length) return 0;
  let dot = 0, normA = 0, normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  if (normA === 0 || normB === 0) return 0;
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

/**
 * 主函数 - 召回记忆
 */
function recall(query, topK = CONFIG.topK) {
  if (!query || query.trim().length < 2) return '';
  
  try {
    initDb();
    
    // 1. 获取查询 embedding
    const queryEmbedding = getEmbedding(query);
    if (!queryEmbedding) return '';
    
    // 2. 获取实体
    const rows = db.prepare(`
      SELECT node_id, node_type, label, embedding
      FROM knowledge_graph
      WHERE embedding IS NOT NULL
    `).all();
    
    // 3. 计算相似度
    const results = rows.map(r => {
      const emb = new Float32Array(r.embedding.buffer, r.embedding.byteOffset, r.embedding.length / 4);
      return { 
        label: r.label, 
        type: r.node_type, 
        sim: cosineSimilarity(queryEmbedding, emb) 
      };
    })
    // 过滤：只保留 allowedTools + session，排除 excludeTools
    .filter(r => {
      if (r.type === 'session') return true;
      if (r.type === 'tool' && CONFIG.allowedTools.includes(r.label)) return true;
      if (r.type === 'tool' && CONFIG.excludeTools.includes(r.label)) return false;
      return true;
    })
    .filter(r => r.sim >= CONFIG.minSimilarity)
      .sort((a, b) => b.sim - a.sim)
      .slice(0, topK);
    
    if (results.length === 0) return '';
    
    // 4. 格式化
    let output = '\n📚 **相关记忆** (' + query + '):\n';
    results.forEach((r, i) => {
      output += `${i + 1}. [${r.type}] ${r.label} (${(r.sim * 100).toFixed(1)}%)\n`;
    });
    
    return output;
    
  } catch (e) {
    return '';
  } finally {
    if (db) db.close();
    db = null;
  }
}

// 直接执行
const query = process.argv.slice(2).join(' ');
if (query) {
  const result = recall(query);
  process.stdout.write(result);
}