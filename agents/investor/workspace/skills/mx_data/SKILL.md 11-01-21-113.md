---
name: mx_data
description: 妙想金融数据查询skill。基于东方财富权威数据库，通过自然语言查询股票、基金、债券、指数的行情数据、财务数据、资金流向等。使用方式：运行 scripts/query.sh 或 scripts/query.py 进行查询。注意：大数据范围查询可能导致返回内容过多，需谨慎使用。
---

# 妙想金融数据 (mx_data)

通过东方财富妙想API查询金融数据。

## 使用前提

1. 在妙想Skills页面获取 apikey
2. 将 apikey 存到环境变量 `MX_APIKEY`
3. 或直接使用提供的 apikey（测试用）

## 查询示例

### 实时行情
```bash
# 查询股票最新价
bash scripts/query.sh "000516最新价"
bash scripts/query.sh "国际医学最新价"
```

### 资金流向
```bash
# 查询主力资金流向
bash scripts/query.sh "000516主力资金流向"
bash scripts/query.sh "东方财富资金流向"
```

### 财务数据
```bash
# 查询财务指标
bash scripts/query.sh "000516财务指标"
bash scripts/query.sh "国际医学市盈率"
```

### 板块数据
```bash
# 查询板块行情
bash scripts/query.sh "医疗服务板块行情"
bash scripts/query.sh "A股整体行情"
```

## 返回数据解读

参考返回的JSON结构：
- `data.dataTableDTOList` - 证券指标数据列表
- `data.dataTableDTOList[].code` - 证券代码
- `data.dataTableDTOList[].table` - 表格数据
- `data.dataTableDTOList[].nameMap` - 列名映射（编码→中文）

**常用指标映射：**
| 编码 | 中文名 |
|------|--------|
| f2 | 最新价 |
| f3 | 涨跌幅 |
| f4 | 涨跌额 |
| f12 | 股票代码 |
| f14 | 股票名称 |

## 注意事项

⚠️ **大数据范围查询限制**：查询3年以上的日线数据可能导致返回内容过多，造成上下文爆炸。请尽量查询：
- 最近N天的行情
- 单只股票的单项指标
- 限定时间范围的数据

## 错误处理

如果返回为空或报错：
- 检查 apikey 是否有效
- 检查网络连接
- 尝试简化查询语句
- 如持续失败，建议到东方财富妙想AI直接查询