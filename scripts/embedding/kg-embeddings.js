#!/usr/bin/env node

/**
 * Knowledge Graph Embeddings Generator
 * 为 knowledge_graph 表中的实体生成 embedding
 * 
 * 使用 m3e-large 模型生成 embedding
 * 配置: http://116.63.86.12:3000/v1/embeddings
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
  batchSize: 32,
  proxy: process.env.HTTP_PROXY || 'http://localhost:7897',
  
  // 过滤配置：增量保存时排除低价值工具
  excludeTools: ['exec', 'edit', 'read', 'write', 'memory_search', 'sessions_history', 'process']
};

// 设置代理
if (CONFIG.proxy) {
  process.env.HTTP_PROXY = CONFIG.proxy;
  process.env.HTTPS_PROXY = CONFIG.proxy;
}

// 获取 embedding
async function getEmbedding(text) {
  const headers = {
    'Content-Type': 'application/json'
  };
  if (CONFIG.apiKey) {
    headers['Authorization'] = `Bearer ${CONFIG.apiKey}`;
  }
  
  const response = await fetch(CONFIG.apiUrl, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      model: CONFIG.model,
      input: text
    })
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.data[0].embedding;
}

// 批量获取 embedding
async function getBatchEmbeddings(texts) {
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
      input: texts  // 需要数组格式
    })
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.data;
}

// 主函数
async function main() {
  console.log('🔷 Knowledge Graph Embeddings Generator');
  console.log('========================================\n');

  // 连接数据库
  const db = new Database(CONFIG.dbPath);
  
  // 检查是否已有 embedding 字段
  try {
    db.prepare('SELECT embedding FROM knowledge_graph LIMIT 1').get();
  } catch (e) {
    console.error('❌ embedding 字段不存在，请先添加: ALTER TABLE knowledge_graph ADD COLUMN embedding BLOB;');
    process.exit(1);
  }

  // 获取没有 embedding 的实体（排除低价值工具）
  const excludeList = CONFIG.excludeTools.map(t => `'${t}'`).join(',');
  const entities = db.prepare(`
    SELECT id, node_id, label, node_type 
    FROM knowledge_graph 
    WHERE (embedding IS NULL OR embedding = '')
      AND NOT (node_type = 'tool' AND label IN (${excludeList}))
    ORDER BY id
  `).all();

  if (entities.length === 0) {
    console.log('✅ 所有实体已有 embedding，无需处理');
    db.close();
    return;
  }

  console.log(`📊 共 ${entities.length} 个实体需要生成 embedding\n`);

  // 批量处理
  let processed = 0;
  let failed = 0;
  
  const updateStmt = db.prepare('UPDATE knowledge_graph SET embedding = ? WHERE id = ?');

  for (let i = 0; i < entities.length; i += CONFIG.batchSize) {
    const batch = entities.slice(i, i + CONFIG.batchSize);
    const texts = batch.map(e => e.label);
    
    try {
      const embeddings = await getBatchEmbeddings(texts);
      
      // 更新数据库
      const transaction = db.transaction(() => {
        for (let j = 0; j < batch.length; j++) {
          const embedding = embeddings[j].embedding;
          // 转换为 Float32Array 并创建 Buffer
          const float32Array = new Float32Array(embedding);
          const embeddingBuffer = Buffer.from(float32Array.buffer, float32Array.byteOffset, float32Array.byteLength);
          updateStmt.run(embeddingBuffer, batch[j].id);
        }
      });
      
      transaction();
      processed += batch.length;
      console.log(`  ✅ 处理进度: ${processed}/${entities.length}`);
      
    } catch (e) {
      console.error(`  ❌ 批次处理失败: ${e.message}`);
      failed += batch.length;
    }
  }

  console.log('\n========================================');
  console.log(`✅ 完成! 成功: ${processed}, 失败: ${failed}`);
  
  // 统计
  const total = db.prepare('SELECT COUNT(*) as count FROM knowledge_graph').get();
  const withEmbedding = db.prepare('SELECT COUNT(*) as count FROM knowledge_graph WHERE embedding IS NOT NULL AND embedding != ""').get();
  console.log(`📈 统计: ${withEmbedding.count}/${total.count} 个实体有 embedding`);

  db.close();
}

main().catch(console.error);