#!/usr/bin/env node

/**
 * Knowledge Graph Query Script
 * 支持向量相似度搜索
 * 
 * 用法:
 *   node kg-query.js search <关键词>     - 向量搜索
 *   node kg-query.js entity <nodeId>     - 查看实体详情
 */

const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

// 配置
const CONFIG = {
  dbPath: path.join(process.env.HOME || process.env.USERPROFILE, '.openclaw/memory/snapshot.db'),
  apiUrl: process.env.EMBEDDING_BASE_URL ? `${process.env.EMBEDDING_BASE_URL}/v1/embeddings` : 'http://116.63.86.12:3000/v1/embeddings',
  apiKey: process.env.EMBEDDING_API_KEY || '',
  model: 'm3e-large',
  proxy: process.env.HTTP_PROXY || 'http://localhost:7897',
  topK: 10
};

// 设置代理
if (CONFIG.proxy) {
  process.env.HTTP_PROXY = CONFIG.proxy;
  process.env.HTTPS_PROXY = CONFIG.proxy;
}

// 计算余弦相似度
function cosineSimilarity(a, b) {
  if (a.length !== b.length) return 0;
  
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

// 获取查询的 embedding
async function getQueryEmbedding(text) {
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  };
  if (CONFIG.apiKey) {
    headers['Authorization'] = `Bearer ${CONFIG.apiKey}`;
  }
  
  const response = await fetch(CONFIG.apiUrl, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      model: CONFIG.model,
      input: [text]  // 需要数组格式
    })
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.data[0].embedding;
}

// 搜索命令
async function search(query, topK = CONFIG.topK) {
  console.log(`🔍 搜索: "${query}"\n`);
  
  // 获取查询的 embedding
  const queryEmbedding = await getQueryEmbedding(query);
  
  // 连接数据库
  const db = new Database(CONFIG.dbPath);
  
  // 获取所有有 embedding 的实体
  const entities = db.prepare(`
    SELECT id, node_id, label, node_type, properties, embedding
    FROM knowledge_graph 
    WHERE embedding IS NOT NULL AND embedding != ''
  `).all();
  
  if (entities.length === 0) {
    console.log('❌ 没有带 embedding 的实体，请先运行 kg-embeddings.js');
    db.close();
    return;
  }
  
  // 计算相似度
  const results = entities.map(entity => {
    try {
      // 读取 embedding - 支持多种格式
      let embeddingArray;
      if (Buffer.isBuffer(entity.embedding)) {
        // 从 Buffer 读取 Float32Array
        embeddingArray = new Float32Array(entity.embedding.buffer, entity.embedding.byteOffset, entity.embedding.length / 4);
      } else if (typeof entity.embedding === 'string') {
        // 从 JSON 字符串读取
        embeddingArray = JSON.parse(entity.embedding);
      } else if (Array.isArray(entity.embedding)) {
        // 已经是数组
        embeddingArray = entity.embedding;
      } else {
        throw new Error(`Unknown embedding format: ${typeof entity.embedding}`);
      }
      
      const similarity = cosineSimilarity(queryEmbedding, embeddingArray);
      return {
        ...entity,
        similarity: similarity,
        embedding: undefined // 不显示完整 embedding
      };
    } catch (e) {
      console.error(`Error processing entity ${entity.node_id}: ${e.message}`);
      return {
        ...entity,
        similarity: -1,
        embedding: undefined,
        error: e.message
      };
    }
  });
  
  // 排序并取 topK
  results.sort((a, b) => b.similarity - a.similarity);
  const topResults = results.slice(0, topK);
  
  // 显示结果
  console.log(`📊 找到 ${entities.length} 个实体，显示 top ${topK}:\n`);
  console.log('┌─────┬──────────────┬────────────────────────────┬──────────┬────────────');
  console.log('│ #   │ node_id      │ label                      │ type     │ 相似度    ');
  console.log('├─────┼──────────────┼────────────────────────────┼──────────┼────────────');
  
  topResults.forEach((r, i) => {
    const label = r.label.length > 26 ? r.label.substring(0, 23) + '...' : r.label;
    console.log(`│ ${String(i + 1).padStart(3)} │ ${r.node_id.substring(0, 12).padEnd(12)} │ ${label.padEnd(26)} │ ${r.node_type.padEnd(8)} │ ${r.similarity.toFixed(4)}   `);
  });
  
  console.log('└─────┴──────────────┴────────────────────────────┴──────────┴────────────\n');
  
  db.close();
}

// 查看实体详情
function showEntity(nodeId) {
  console.log(`📋 实体详情: ${nodeId}\n`);
  
  const db = new Database(CONFIG.dbPath);
  
  const entity = db.prepare(`
    SELECT * FROM knowledge_graph WHERE node_id = ?
  `).get(nodeId);
  
  if (!entity) {
    console.log('❌ 未找到该实体');
    db.close();
    return;
  }
  
  console.log(`  node_id:    ${entity.node_id}`);
  console.log(`  label:      ${entity.label}`);
  console.log(`  node_type:  ${entity.node_type}`);
  console.log(`  properties: ${entity.properties || '(无)'}`);
  console.log(`  created_at: ${entity.created_at}`);
  
  if (entity.embedding && entity.embedding.length > 0) {
    const dim = entity.embedding.length / 4; // Float32
    console.log(`  embedding:  ${dim}维 (已存储)`);
  } else {
    console.log(`  embedding:  (未生成)`);
  }
  
  db.close();
}

// 主函数
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  
  if (!command) {
    console.log(`
🔷 Knowledge Graph Query Tool

用法:
  node kg-query.js search <关键词>   - 向量搜索相似实体
  node kg-query.js entity <nodeId>   - 查看实体详情

示例:
  node kg-query.js search "人工智能"
  node kg-query.js entity "node_123"
`);
    process.exit(0);
  }
  
  if (command === 'search') {
    const query = args.slice(1).join(' ');
    if (!query) {
      console.error('❌ 请输入搜索关键词');
      process.exit(1);
    }
    await search(query);
  } else if (command === 'entity') {
    const nodeId = args[1];
    if (!nodeId) {
      console.error('❌ 请输入 node_id');
      process.exit(1);
    }
    showEntity(nodeId);
  } else {
    console.error(`❌ 未知命令: ${command}`);
    console.log('可用命令: search, entity');
    process.exit(1);
  }
}

main().catch(console.error);