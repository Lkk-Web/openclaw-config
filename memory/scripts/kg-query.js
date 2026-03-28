#!/usr/bin/env node
/**
 * 知识图谱向量搜索查询脚本
 * 
 * 功能：
 * 1. 将查询文本转换为 embedding
 * 2. 从数据库获取所有实体及其 embedding
 * 3. 计算余弦相似度并返回 top-k 结果
 */

const Database = require('better-sqlite3');
const http = require('http');
const { URL } = require('url');

// 配置
const CONFIG = {
  dbPath: require('os').homedir() + '/.openclaw/memory/snapshot.db',
  apiUrl: process.env.EMBEDDING_BASE_URL ? `${process.env.EMBEDDING_BASE_URL}/v1/embeddings` : 'http://116.63.86.12:3000/v1/embeddings',
  apiKey: process.env.EMBEDDING_API_KEY || '',
  model: 'm3e-large',
  proxy: process.env.USE_PROXY === 'true' ? (process.env.HTTP_PROXY || 'http://localhost:7897') : null,
  topK: 10
};

// 设置代理
if (CONFIG.proxy) {
  process.env.HTTP_PROXY = CONFIG.proxy;
  process.env.HTTPS_PROXY = CONFIG.proxy;
}

// 初始化数据库
let db;
function initDb() {
  db = new Database(CONFIG.dbPath);
  db.pragma('journal_mode = WAL');
}

/**
 * 调用 embedding API
 */
function getEmbedding(text) {
  return new Promise((resolve, reject) => {
    const url = new URL(CONFIG.apiUrl);
    
    const postData = JSON.stringify({
      model: CONFIG.model,
      input: [text]
    });
    
    const headers = {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(postData),
      'Accept': 'application/json'
    };
    
    if (CONFIG.apiKey) {
      headers['Authorization'] = `Bearer ${CONFIG.apiKey}`;
    }
    
    // 如果配置了代理，使用代理
    let options;
    if (CONFIG.proxy) {
      const proxyUrl = new URL(CONFIG.proxy);
      options = {
        hostname: proxyUrl.hostname,
        port: proxyUrl.port || 8080,
        path: url.href,
        method: 'POST',
        headers
      };
    } else {
      // 直接连接
      options = {
        hostname: url.hostname,
        port: url.port || 80,
        path: url.pathname + url.search,
        method: 'POST',
        headers
      };
    }
    
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
 * 解析 embedding blob
 */
function parseEmbedding(buffer) {
  if (!buffer) return null;
  const embedding = [];
  for (let i = 0; i < buffer.length; i += 4) {
    embedding.push(buffer.readFloatLE(i));
  }
  return embedding;
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
 * 搜索知识图谱
 */
async function searchKnowledgeGraph(query, topK = 10) {
  console.log(`\n🔍 查询: "${query}"`);
  console.log('─'.repeat(60));
  
  // 1. 获取查询的 embedding
  console.log('📡 获取查询 embedding...');
  const queryEmbedding = await getEmbedding(query);
  console.log(`   Embedding 维度: ${queryEmbedding.length}`);
  
  // 2. 从数据库获取所有有 embedding 的实体
  console.log('📊 加载知识图谱实体...');
  const rows = db.prepare(`
    SELECT node_id, node_type, label, properties, embedding
    FROM knowledge_graph
    WHERE embedding IS NOT NULL
  `).all();
  console.log(`   总实体数: ${rows.length}`);
  
  // 3. 计算相似度
  console.log('⚡ 计算相似度...');
  const results = [];
  
  for (const row of rows) {
    const embedding = parseEmbedding(row.embedding);
    const similarity = cosineSimilarity(queryEmbedding, embedding);
    
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
      similarity: similarity
    });
  }
  
  // 4. 排序并返回 top-k
  results.sort((a, b) => b.similarity - a.similarity);
  const topResults = results.slice(0, topK);
  
  // 5. 打印结果
  console.log('\n📋 搜索结果:');
  console.log('═'.repeat(60));
  
  topResults.forEach((r, i) => {
    const score = (r.similarity * 100).toFixed(1);
    const type = r.node_type.padEnd(8);
    console.log(`\n${i + 1}. [${type}] ${r.label}`);
    console.log(`   相似度: ${score}%`);
    if (r.properties) {
      // 显示部分属性
      const keys = Object.keys(r.properties).slice(0, 3);
      if (keys.length > 0) {
        const propsStr = keys.map(k => `${k}: ${JSON.stringify(r.properties[k]).substring(0, 50)}`).join(', ');
        console.log(`   属性: ${propsStr}`);
      }
    }
  });
  
  console.log('\n' + '═'.repeat(60));
  
  return topResults;
}

/**
 * 主函数
 */
async function main() {
  const args = process.argv.slice(2);
  const query = args.join(' ');
  const topK = args.includes('--top') ? parseInt(args[args.indexOf('--top') + 1]) || 10 : 10;
  
  if (!query || query === '--help' || query === '-h') {
    console.log(`
知识图谱向量搜索工具

用法: node kg-query.js <查询文本> [选项]

选项:
  --top N     返回前 N 个结果 (默认: 10)
  --help      显示帮助

示例:
  node kg-query.js "代码调试"
  node kg-query.js "API调用" --top 5
    `.trim());
    process.exit(0);
  }
  
  try {
    initDb();
    await searchKnowledgeGraph(query, topK);
  } catch (error) {
    console.error('\n❌ 查询失败:', error.message);
    process.exit(1);
  } finally {
    if (db) db.close();
  }
}

main();