#!/usr/bin/env node
/**
 * 知识图谱自动记忆召回脚本
 * 
 * 功能：
 * 1. 接收用户查询文本
 * 2. 调用 embedding API 获取向量
 * 3. 从数据库搜索相似实体
 * 4. 返回格式化的记忆上下文
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
  topK: 5
};

// 初始化数据库
let db;
function initDb() {
  db = new Database(CONFIG.dbPath);
  db.pragma('journal_mode = WAL');
}

/**
 * 调用 embedding API (使用 curl)
 */
function getEmbedding(text) {
  const cmd = `curl -s -x ${CONFIG.proxy} "${CONFIG.apiUrl}" \
    -H "Authorization: Bearer ${CONFIG.apiKey}" \
    -H "Content-Type: application/json" \
    -d ${JSON.stringify(JSON.stringify({ model: CONFIG.model, input: [text] }))}`;
  
  const result = execSync(cmd, { encoding: 'utf8' });
  const data = JSON.parse(result);
  return data.data[0].embedding;
}

/**
 * 计算余弦相似度
 */
function cosineSimilarity(a, b) {
  if (!a || !b || a.length !== b.length) return 0;
  
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;
  
  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  
  if (normA === 0 || normB === 0) return 0;
  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

/**
 * 搜索知识图谱并返回格式化结果
 */
async function recallMemories(query, topK = 5) {
  try {
    // 1. 获取查询的 embedding
    const queryEmbedding = getEmbedding(query);
    
    // 2. 从数据库获取所有有 embedding 的实体
    const rows = db.prepare(`
      SELECT node_id, node_type, label, properties, embedding
      FROM knowledge_graph
      WHERE embedding IS NOT NULL
    `).all();
    
    // 3. 计算相似度
    const results = [];
    
    for (const row of rows) {
      const emb = new Float32Array(row.embedding.buffer, row.embedding.byteOffset, row.embedding.length / 4);
      const similarity = cosineSimilarity(queryEmbedding, emb);
      
      let properties = null;
      if (row.properties) {
        try {
          properties = JSON.parse(row.properties);
        } catch (e) {}
      }
      
      results.push({
        node_id: row.node_id,
        node_type: row.node_type,
        label: row.label,
        properties,
        similarity
      });
    }
    
    // 4. 排序并返回 top-k
    results.sort((a, b) => b.similarity - a.similarity);
    const topResults = results.slice(0, topK);
    
    // 5. 格式化输出
    if (topResults.length === 0) {
      return '';
    }
    
    let output = '\n📚 **相关记忆**:\n';
    topResults.forEach((r, i) => {
      output += `\n${i + 1}. [${r.node_type}] ${r.label} (${(r.similarity * 100).toFixed(1)}%)`;
    });
    
    return output;
    
  } catch (error) {
    console.error('记忆召回失败:', error.message);
    return '';
  }
}

/**
 * 主函数 - 直接输出到 stdout
 */
async function main() {
  const query = process.argv.slice(2).join(' ');
  
  if (!query) {
    console.error('用法: node kg-recall.js <查询文本>');
    process.exit(1);
  }
  
  try {
    initDb();
    const result = await recallMemories(query, CONFIG.topK);
    console.log(result);
  } catch (error) {
    console.error('错误:', error.message);
    process.exit(1);
  } finally {
    if (db) db.close();
  }
}

main();