# Alpha Mold

## 使用说明
这份文档对应新的大批量配置文件 `alpha_configs/iqc_massive_batch_config.json`。目标不是少量精选，而是构造一批金融含义明确、可以放心做笛卡尔展开、总量达到上万级的 Alpha 模板，方便你连续一周在服务器上滚动回测。

本次模板仍按 `1模板 / 2模板 / 3模板` 组织：
- `1模板`：一个主字段，适合单因子异常、趋势、事件强弱。
- `2模板`：两个字段，主要是比率、价差、相关性。
- `3模板`：三个字段，主要是“两个字段形成信号 + 一个分组做中性化/组内排序”。

## 历史草稿修正

### 1. `group_rank({variate}/cap, subindustry)`
修正为：`group_rank(divide({field}, cap), subindustry)`

说明：用市值缩放基本面，再在子行业内部排序，避免单纯比绝对规模。

### 2. `{-/+}{variate}/assess`
修正思路：
- `divide({field}, assets)`
- `reverse(divide({field}, assets))`

说明：原始写法中的 `assess` 应改为 `assets`，正负号应拆成明确表达式。

### 3. `rank({variate}/assess)`
修正为：`rank(divide({field}, assets))`

说明：这是典型的资产效率模板，如 `sales/assets`、`income/assets`。

### 4. `rank(decay_linear(ts_delta({field}, 252), 10))`
修正为：`rank(ts_decay_linear(ts_delta({field}, 252), 10))`

说明：`operators.md` 里对应算子名是 `ts_decay_linear`。

### 5. IV vs HV 草稿
修正为：
- `rank(subtract(implied_volatility_call_{window}, historical_volatility_{window}))`
- `rank(divide(implied_volatility_call_{window}, historical_volatility_{window}))`

说明：期权隐波高于历史波动率，通常代表市场在给未来不确定性定更高价格。

### 6. `rank(ts_sum(vec_avg({nws12 field}),60)) > 0.5 ? 1: rank(-ts_delta(close, 2))`
修正为：
`if_else(rank(ts_sum(vec_avg({field}), 60)) > 0.5, 1, rank(reverse(ts_delta(close, 2))))`

说明：用 `if_else` 和 `reverse` 替代不规范写法，更适合 Brain 表达式风格。

## 大规模模板设计

### 1模板

#### A. 基本面相对市值模板
```text
group_rank(divide(ts_backfill({field}, 252), cap), {group})
```

用途：寻找“相对市值便宜”或“相对市值经营量高”的公司。

#### B. 基本面相对企业价值模板
```text
group_rank(divide(ts_backfill({field}, 252), enterprise_value), {group})
```

用途：比纯市值更接近资本结构调整后的估值视角。

#### C. 基本面改善模板
```text
rank(ts_decay_linear(ts_delta(ts_backfill({field}, 252), {lookback}), {decay}))
```

用途：关注盈利、现金流、收入、营运资本等变量的改善速度。

#### D. 基本面时序标准化模板
```text
rank(ts_zscore(ts_backfill({field}, 252), {days}))
```

用途：寻找某个基本面字段相对自身历史的极端状态。

#### E. 新闻矩阵异常模板
```text
rank(ts_zscore({field}, {days}))
```

用途：寻找新闻后价格反应、跳空、相对指数表现等字段的异常期。

#### F. 新闻矩阵变化模板
```text
rank(ts_decay_linear(ts_delta({field}, {lookback}), {decay}))
```

用途：让新闻冲击强度的“变化”进入信号，而不是只看绝对值。

#### G. 新闻向量聚合模板
```text
rank(ts_zscore(vec_avg({field}), {days}))
```

用途：先把向量新闻数据压成标量，再做标准化。

#### H. 新闻向量累计模板
```text
rank(ts_sum(vec_avg({field}), {days}))
```

用途：累计多天新闻压力，适合观察事件持续发酵。

#### I. PV 基础强弱模板
```text
rank(ts_rank({field}, {days}))
```

用途：把价格、成交量、收益率、VWAP 等经典量价字段变成标准时序强弱信号。

#### J. 尾部风险 Beta 模板
```text
rank(ts_regression(returns, if_else(group_mean(returns, 1, market) < 0, group_mean(returns, 1, market), 0), {lookback}, 0, 2))
```

用途：来自 `paper/` 的尾部风险思路，衡量个股在市场下跌阶段的脆弱程度。

### 2模板

#### K. 基本面比率模板
```text
rank(divide(ts_backfill({numerator}, 252), ts_backfill({denominator}, 252)))
```

用途：构造资产周转、现金流收益率、盈利回报率、估值类比率。

#### L. 基本面比率时序模板
```text
rank(ts_rank(divide(ts_backfill({numerator}, 252), ts_backfill({denominator}, 252)), {days}))
```

用途：同一比率相对自身历史的位置。

#### M. Winsorize 后的基本面比率模板
```text
rank(winsorize(divide(ts_backfill({numerator}, 252), ts_backfill({denominator}, 252)), std={std}))
```

用途：先截断极端值，再排序，减少异常值污染。

#### N. 新闻字段与收益相关性模板
```text
rank(ts_corr({field}, returns, {days}))
```

用途：看新闻事件变量和股票收益的滚动关系是否在加强。

#### O. 新闻向量与收益相关性模板
```text
rank(ts_corr(vec_avg({field}), returns, {days}))
```

用途：适合度量向量事件特征是否逐渐变成收益驱动变量。

#### P. 期权 IV-HV 差值模板
```text
rank(ts_zscore(subtract(implied_volatility_call_{window}, historical_volatility_{window}), {days}))
```

用途：看期权市场相对历史波动是否显著高估未来风险。

#### Q. 期权 IV-HV 比率模板
```text
rank(ts_zscore(divide(implied_volatility_call_{window}, historical_volatility_{window}), {days}))
```

用途：比差值更强调相对倍数。

#### R. Put-Call 隐波差模板
```text
rank(ts_zscore(subtract(implied_volatility_put_{window}, implied_volatility_call_{window}), {days}))
```

用途：提取看跌保护溢价，通常对应风险厌恶上升。

### 3模板

#### S. 行业内相对质量模板
```text
group_zscore(divide(ts_backfill({numerator}, 252), ts_backfill({denominator}, 252)), {group})
```

用途：先做财务比率，再在行业内标准化，减少结构性行业差异。

#### T. 组内相对模板
```text
{group_op}({ts_op}({field}, {days}), {group})
```

用途：把新闻矩阵字段或量价字段放回行业内部比较，减少全市场共同因子的干扰。

## 大批量配置概览

新配置文件：`findalpha_mold/alpha_configs/iqc_massive_batch_config.json`

当前按静态参数展开估算，总表达式数量为：`13875`

数据来源：
- 基本面：`fundamental_large_fields.csv`、`fundamental_ratio_large_numerators.csv`、`fundamental_ratio_large_denominators.csv`
- 新闻：直接使用 `news12_MATRIX.csv`、`news12_VECTOR.csv`
- 量价：`pv_core_fields.csv`
- 期权：`option_window_ivhv.csv`、`option_window_parkinson.csv`

设计原则：
- 基本面部分只保留语义清晰字段，避免 574 个字段无差别硬乘。
- 新闻部分使用原始全量 `news12_MATRIX.csv` 和 `news12_VECTOR.csv`，因为它们本身就是事件特征库，适合大规模展开。
- 期权部分按期限展开，保留 call/historical、put/historical、put/call、parkinson/historical 四种风险溢价视角。
- 尾部风险部分来自 `paper/` 的思路，用少量但高质量模板补充宏观风险维度。

## Alpha 表达式解释

### A. `group_rank(divide(ts_backfill(sales, 252), cap), subindustry)`
解释：销售额相对市值越高，可能意味着市场对收入定价偏低。放到子行业内比较，可以减少行业估值结构差异。

### B. `group_rank(divide(ts_backfill(cashflow_op, 252), enterprise_value), industry)`
解释：经营现金流相对企业价值越高，越接近现金流收益率视角，通常比单看利润更稳健。

### C. `rank(ts_decay_linear(ts_delta(ts_backfill(return_equity, 252), 126), 10))`
解释：如果 ROE 在过去半年持续改善，市场往往不会一次性完全定价，这种改善速度本身就可以形成 Alpha。

### D. `rank(ts_zscore(ts_backfill(working_capital, 252), 252))`
解释：营运资本相对自身一年历史的位置偏高或偏低，可能反映库存、应收、流动性结构的变化。

### E. `rank(ts_zscore(news_indx_perf, 20))`
解释：新闻后的相对指数表现如果显著异常，说明事件定价强度正在变化，适合寻找过度反应或延续反应。

### F. `rank(ts_decay_linear(ts_delta(news_open_gap, 5), 10))`
解释：连续几次新闻驱动跳空的变化方向，可以反映市场对事件情绪是强化还是钝化。

### G. `rank(ts_zscore(vec_avg(nws12_afterhsz_30_min), 60))`
解释：新闻后 30 分钟反应若相对历史显著异常，说明短期事件冲击可能还没有被价格完全吸收。

### H. `rank(ts_sum(vec_avg(nws12_afterhsz_maxup), 20))`
解释：把多天新闻后的最大上行幅度做累加，适合观察利好事件是否在持续堆积。

### I. `rank(ts_rank(vwap, 60))`
解释：VWAP 在过去 60 天中的相对位置，是最基础的价格强弱模板之一，常用于趋势或均值回归前的筛选。

### J. `rank(ts_regression(returns, if_else(group_mean(returns, 1, market) < 0, group_mean(returns, 1, market), 0), 252, 0, 2))`
解释：这是下行市场 Beta。数值越高，股票在市场下跌时越脆弱，也越可能承载尾部风险溢价。

### K. `rank(divide(ts_backfill(sales, 252), ts_backfill(assets, 252)))`
解释：这是典型的资产周转率思路，用来衡量资产使用效率，属于最经典的质量类基本面因子之一。

### L. `rank(ts_rank(divide(ts_backfill(cashflow_op, 252), ts_backfill(enterprise_value, 252)), 126))`
解释：经营现金流收益率如果处在自己历史高位，通常意味着基本面改善，或者市场暂时低估了公司质量。

### M. `rank(winsorize(divide(ts_backfill(income, 252), ts_backfill(equity, 252)), std=4))`
解释：先对极端值做截断，再观察盈利对股东资本的回报，可以减少异常样本对排序的污染。

### N. `rank(ts_corr(news_indx_perf, returns, 60))`
解释：如果新闻后的相对指数表现和日收益的滚动相关性持续变强，说明这个新闻变量正在变成真实的价格驱动因素。

### O. `rank(ts_corr(vec_avg(nws12_afterhsz_maxdown), returns, 60))`
解释：如果“新闻后最大下跌幅度”和日收益之间的相关性升高，说明市场开始持续放大负面事件的影响。

### P. `rank(ts_zscore(subtract(implied_volatility_call_120, historical_volatility_120), 252))`
解释：长期 Call 隐波如果持续高于已实现波动，说明市场正在为未来不确定性重新定价。

### Q. `rank(ts_zscore(divide(implied_volatility_call_60, historical_volatility_60), 120))`
解释：隐含波动率相对历史波动率的倍数偏高，代表期权市场愿意支付更高的风险保险价格。

### R. `rank(ts_zscore(subtract(implied_volatility_put_60, implied_volatility_call_60), 120))`
解释：Put 隐波相对 Call 隐波偏高，通常代表下行保护需求更强，也意味着市场风险厌恶在上升。

### S. `group_zscore(divide(ts_backfill(income, 252), ts_backfill(equity, 252)), sector)`
解释：这是更接近 ROE 的横截面变体，但这里强调的是行业内相对位置，而不是绝对高低。

### T. `group_rank(ts_zscore(news_indx_perf, 20), industry)`
解释：把新闻事件冲击放到行业内部比较，有助于识别“同业里谁对新闻更敏感”，同样也可以类比用于量价字段的组内比较。

> 以上内容整理于2026-3-23日，由于 GPT5.4 high 模型整理

---
