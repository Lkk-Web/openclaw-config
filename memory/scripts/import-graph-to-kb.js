#!/usr/bin/env node
/**
 * 知识图谱向量绑定导入脚本
 * 
 * 功能：
 * 1. 读取所有增量图数据文件
 * 2. 合并去重实体
 * 3. 为每个实体生成 embedding（使用 m3e-large API）
 * 4. 导入到 knowledge_graph 表
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');
const { URL } = require('url');

// 配置
const CONFIG = {
  graphsDir: path.join(process.env.HOME, '.openclaw/memory/graphs'),
  dbPath: path.join(process.env.HOME, '.openclaw/memory/snapshot.db'),
  embeddingApi: {
    url: 'http://116.63.86.12:3000/v1/embeddings',
    model: 'm3e-large',
    dimensions: 1024
  },
  proxy: {
    host: 'localhost',
    port: 7897
  },
  batchSize: 20,  // 每批处理的实体数量
  delayMs: 100    // 批次之间的延迟（毫秒）
};

// 动态加载 better-sqlite3
let db;
function initDb() {
  const Database = require('better-sqlite3');
  db = new Database(CONFIG.dbPath);
  db.pragma('journal_mode = WAL');
  console.log('✓ 数据库连接成功');
}

/**
 * 获取所有增量图文件
 */
function getIncrementalFiles() {
  const files = fs.readdirSync(CONFIG.graphsDir)
    .filter(f => f.startsWith('graph_incremental_') && f.endsWith('.jsonl'))
    .sort();
  
  console.log(`✓ 找到 ${files.length} 个增量文件`);
  return files.map(f => path.join(CONFIG.graphsDir, f));
}

/**
 * 合并所有增量数据，去重
 */
function mergeGraphEntities(files) {
  const entities = new Map();
  
  for (const file of files) {
    const content = fs.readFileSync(file, 'utf-8');
    const lines = content.trim().split('\n');
    
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const entity = JSON.parse(line);
        // 使用 id 作为唯一键
        if (!entities.has(entity.id)) {
          entities.set(entity.id, entity);
        } else {
          // 合并 properties（如果后续的有更多属性）
          const existing = entities.get(entity.id);
          if (entity.properties) {
            existing.properties = { ...existing.properties, ...entity.properties };
          }
        }
      } catch (e) {
        console.warn(`解析失败: ${line.substring(0, 50)}...`);
      }
    }
  }
  
  console.log(`✓ 合并后共 ${entities.size} 个唯一实体`);
  return entities;
}

/**
 * 调用 embedding API（通过代理）
 */
async function getEmbedding(text) {
  return new Promise((resolve, reject) => {
    const url = new URL(CONFIG.embeddingApi.url);
    
    const postData = JSON.stringify({
      model: CONFIG.embeddingApi.model,
      input: text
    });
    
    const options = {
      hostname: CONFIG.proxy.host,
      port: CONFIG.proxy.port,
      path: url.pathname + url.search,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
        'Host': url.hostname
      }
    };
    
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          if (json.data && json.data[0] && json.data[0].embedding) {
            resolve(json.data[0].embedding);
          } else if (json.error) {
            reject(new Error(`API Error: ${json.error.message || JSON.stringify(json.error)}`));
          } else {
            reject(new Error(`Invalid response: ${data.substring(0, 200)}`));
          }
        } catch (e) {
          reject(new Error(`Parse error: ${e.message}`));
        }
      });
    });
    
    req.on('error', reject);
    req.setTimeout(30000, () => {
      req.destroy();
      reject(new Error('Timeout'));
    });
    
    req.write(postData);
    req.end();
  });
}

/**
 * 批量获取 embeddings（带重试）
 */
async function getEmbeddings(texts, maxRetries = 3) {
  const embeddings = new Map();
  
  for (let i = 0; i < texts.length; i++) {
    const { id, text } = texts[i];
    let retries = 0;
    let lastError;
    
    while (retries < maxRetries) {
      try {
        const embedding = await getEmbedding(text);
        embeddings.set(id, embedding);
        
        // 进度显示
        if ((i + 1) % 10 === 0 || i === texts.length - 1) {
          console.log(`  进度: ${i + 1}/${texts.length} embeddings`);
        }
        break;
      } catch (e) {
        lastError = e;
        retries++;
        if (retries < maxRetries) {
          console.warn(`  重试 ${retries}/${maxRetries}: ${id} - ${e.message}`);
          await new Promise(r => setTimeout(r, 1000 * retries));
        }
      }
    }
    
    if (retries === maxRetries) {
      console.error(`✗ 获取 embedding 失败: ${id} - ${lastError.message}`);
      embeddings.set(id, null);
    }
    
    // 添加小延迟避免请求过快
    await new Promise(r => setTimeout(r, 50));
  }
  
  return embeddings;
}

/**
 * 将 embedding 数组转换为 SQLite BLOB
 */
function embeddingToBlob(embedding) {
  if (!embedding || !Array.isArray(embedding)) return null;
  // Float32Array 转换为 Buffer
  const buffer = Buffer.alloc(embedding.length * 4);
  const float32Array = new Float32Array(embedding);
  for (let i = 0; i < embedding.length; i++) {
    buffer.writeFloatLE(float32Array[i], i * 4);
  }
  return buffer;
}

/**
 * 准备实体的文本用于 embedding
 */
function prepareEntityText(entity) {
  const parts = [entity.label];
  
  if (entity.properties) {
    // 添加有意义的属性
    const meaningfulProps = Object.entries(entity.properties)
      .filter(([k, v]) => {
        if (!v) return false;
        if (typeof v === 'string' && v.length > 500) return false; // 跳过过长的属性
        return true;
      })
      .map(([k, v]) => `${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`);
    
    if (meaningfulProps.length > 0) {
      parts.push(meaningfulProps.join(', '));
    }
  }
  
  return parts.join(' | ');
}

/**
 * 导入实体到数据库
 */
async function importEntities(entities, embeddings) {
  const insertStmt = db.prepare(`
    INSERT OR REPLACE INTO knowledge_graph 
    (node_id, node_type, label, properties, snapshot_id, created_at, embedding)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `);
  
  const now = new Date().toISOString();
  let imported = 0;
  let skipped = 0;
  
  const insertMany = db.transaction((items) => {
    for (const item of items) {
      try {
        insertStmt.run(
          item.node_id,
          item.node_type,
          item.label,
          item.properties,
          item.snapshot_id,
          item.created_at,
          item.embedding
        );
        imported++;
      } catch (e) {
        console.warn(`插入失败: ${item.node_id} - ${e.message}`);
        skipped++;
      }
    }
  });
  
  const items = [];
  for (const [id, entity] of entities) {
    const embedding = embeddings.get(id);
    
    items.push({
      node_id: entity.id,
      node_type: entity.type,
      label: entity.label,
      properties: entity.properties ? JSON.stringify(entity.properties) : null,
      snapshot_id: null, // 不关联特定快照
      created_at: now,
      embedding: embeddingToBlob(embedding)
    });
  }
  
  insertMany(items);
  
  console.log(`✓ 导入完成: ${imported} 成功, ${skipped} 跳过`);
  return { imported, skipped };
}

/**
 * 验证导入结果
 */
function verifyImport() {
  const stats = {
    total: 0,
    withEmbedding: 0,
    byType: {}
  };
  
  const rows = db.prepare(`
    SELECT node_type, COUNT(*) as count, 
           SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as with_emb
    FROM knowledge_graph
    GROUP BY node_type
  `).all();
  
  console.log('\n验证结果:');
  console.log('='.repeat(50));
  
  for (const row of rows) {
    stats.byType[row.node_type] = {
      total: row.count,
      withEmbedding: row.with_emb
    };
    stats.total += row.count;
    stats.withEmbedding += row.with_emb;
    
    console.log(`  ${row.node_type}: ${row.count} 个实体, ${row.with_emb} 个有 embedding`);
  }
  
  console.log('='.repeat(50));
  console.log(`  总计: ${stats.total} 个实体, ${stats.withEmbedding} 个有 embedding`);
  console.log(`  覆盖率: ${(stats.withEmbedding / stats.total * 100).toFixed(1)}%`);
  
  // 测试向量搜索功能
  console.log('\n测试向量搜索...');
  testVectorSearch();
  
  return stats;
}

/**
 * 测试向量搜索
 */
async function testVectorSearch() {
  try {
    // 获取一个示例 embedding
    const row = db.prepare('SELECT embedding FROM knowledge_graph WHERE embedding IS NOT NULL LIMIT 1').get();
    if (!row || !row.embedding) {
      console.log('  ⚠ 没有可用的 embedding 数据');
      return;
    }
    
    // 解析 embedding
    const buffer = row.embedding;
    const embedding = [];
    for (let i = 0; i < buffer.length; i += 4) {
      embedding.push(buffer.readFloatLE(i));
    }
    
    // 使用余弦相似度搜索
    const results = db.prepare(`
      SELECT node_id, node_type, label,
             vec_distance_cosine(embedding, ?) as distance
      FROM knowledge_graph
      WHERE embedding IS NOT NULL
      ORDER BY distance ASC
      LIMIT 5
    `).all(Buffer.from(buffer));
    
    console.log('  ✓ 向量搜索测试成功');
    console.log(`  找到 ${results.length} 个相似结果`);
    
  } catch (e) {
    console.log(`  ⚠ 向量搜索测试失败: ${e.message}`);
    console.log('  提示: 可能需要安装 sqlite-vec 扩展');
  }
}

/**
 * 主函数
 */
async function main() {
  console.log('=== 知识图谱向量绑定导入 ===\n');
  
  try {
    // 1. 初始化数据库
    console.log('1. 初始化数据库...');
    initDb();
    
    // 2. 获取增量文件
    console.log('\n2. 读取增量文件...');
    const files = getIncrementalFiles();
    
    // 3. 合并实体
    console.log('\n3. 合并实体...');
    const entities = mergeGraphEntities(files);
    
    // 4. 准备文本用于 embedding
    console.log('\n4. 准备 embedding 文本...');
    const texts = [];
    for (const [id, entity] of entities) {
      texts.push({
        id,
        text: prepareEntityText(entity)
      });
    }
    
    // 5. 获取 embeddings
    console.log('\n5. 生成 embeddings...');
    const embeddings = await getEmbeddings(texts);
    
    // 6. 导入数据库
    console.log('\n6. 导入数据库...');
    await importEntities(entities, embeddings);
    
    // 7. 验证
    console.log('\n7. 验证导入结果...');
    verifyImport();
    
    console.log('\n✅ 导入完成！');
    
  } catch (error) {
    console.error('\n❌ 导入失败:', error.message);
    console.error(error.stack);
    process.exit(1);
  } finally {
    if (db) db.close();
  }
}

main();