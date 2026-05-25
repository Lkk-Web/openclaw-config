# AGENTS.md - Your Workspace


## 📈 股票交易记录 (Stock Trading)

### 文件位置
- JSON数据: `/Users/liukangkai/Desktop/github/interview/data/stock/`
- 文档记录: `/Users/liukangkai/Desktop/github/interview/docs/summary/stock/stock.md`
### JSON 数据文件

| 文件 | 用途 | 更新时机 |
|------|------|----------|
| positions.json | 持仓（代码、成本、现价、股数） | 每日收盘/买卖操作 |
| monthly.json | 月度做T目标与收益 | 每次做T后 / 月末 |
| asset-history.json | 每日资产快照 | 每日收盘 |
| other-income.json | 股息/奖金等其他收入 | 有其他收入时 |

### 手续费规则
- 佣金：万0.86，不免5（每笔最低5元）
- 印花税：卖出时0.05%

### 做T净收益计算
```
毛利 = (卖出价 - 买入价) × 股数
买入手续费 = max(买入金额 × 0.000086, 5)
卖出手续费 = max(卖出金额 × 0.000086, 5)
印花税 = 卖出金额 × 0.0005
净收益 = 毛利 - 买入手续费 - 卖出手续费 - 印花税
```

### 记录流程

**每次用户告知操作后：**
1. 读取当前4个JSON文件
2. 根据操作更新对应数据
3. 写回JSON文件
4. 更新 stock.md 文档记录 ** 一定要记录

**场景：**
- "今日无操作" → 更新 positions.json 现价 + asset-history.json
- 有买卖操作 → 更新 positions.json 成本 + monthly.json 做T收益

### 成本价计算
```
新成本价 = (持仓股数×原成本 + 买入股数×买入价格) / 最新持仓股数
```

### 资产计算
```
股票市值 = Σ(每股现价 × 股数)
总资产 = cash + stockValue + loan + other
```
(loan 为负数，如 -36000 表示融资负债)

## Git Commit 规范

**提交信息必须使用英文**，格式遵循：
```
<emoji> <type>: <description>
```

示例风格：
- `📈 feat: update stock record 2026-05-22`
- `🔒 fix: upgrade gh-pages to 5.0.0`
- `🐛 fix: resolve XXX issue`
- `💄 style: update UI styles`

常见 type：`feat`/`fix`/`docs`/`style`/`refactor`/`test`/`chore`

