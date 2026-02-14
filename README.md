# WorldQuant Brain Python Toolkit

用于 WorldQuant Brain 平台的 Alpha 策略搜索、回测和提交工具集。

## 功能特性

- **自动搜索 Alpha**：基于 fundamental6 数据集自动生成并回测 Alpha 策略
- **批量提交**：支持批量提交高质量的 Alpha 到 WorldQuant Brain 平台
- **单 Alpha 操作**：支持单个 Alpha 的回测和提交
- **自动续期**：会话自动续期机制，避免长时间运行中断
- **结果管理**：自动保存回测结果，区分普通 Alpha 和高质量 Alpha

## 项目结构

```
findalpha_mold/
├── alpha_result/
├── brain_credentials.json        # API 凭证（已排除在版本控制外）
├── findAlpha.py                  # 自动搜索和回测 Alpha
├── submitAlpha.py                # 批量提交 Alpha
├── link.py                       # 单个 Alpha 操作
└── test_submitAlpha.py           # 测试脚本
```

## 安装依赖

```bash
pip install requests pandas
```

## 配置

1. 在项目目录下创建 `brain_credentials.json` 文件
2. 填入你的 WorldQuant Brain API 凭证：

```json
["your_api_key", "your_api_secret"]
```

或使用对象格式：

```json
{
  "API_KEY": "your_api_key",
  "API_SECRET": "your_api_secret"
}
```

**注意**：`brain_credentials.json` 已在 `.gitignore` 中，不会被提交到版本控制系统。

## 使用方法

### 1. 自动搜索 Alpha

运行 `findAlpha.py` 自动搜索和回测 Alpha：

```bash
python findAlpha.py
```

该脚本会：
- 获取 fundamental6 数据集的所有数据字段
- 为每个数据字段生成正负两个 Alpha 表达式
- 逐个回测并保存结果
- 高质量 Alpha（Sharpe > 1.25 且 Fitness > 1）会额外保存到 `elite_alphas.jsonl`

### 2. 批量提交 Alpha

运行 `submitAlpha.py` 批量提交高质量的 Alpha：

```bash
python submitAlpha.py
```

该脚本会：
- 从 `elite_alphas.jsonl` 读取 Alpha
- 跳过已提交的 Alpha
- 提交指定数量的 Alpha（默认为 1，可在代码中修改 `submit_count`）
- 更新已提交数量到文件

### 3. 单个 Alpha 操作

运行 `link.py` 进行单个 Alpha 的回测和提交：

```bash
python link.py
```

修改 `my_alpha` 变量来测试不同的 Alpha 表达式。

### 4. 运行测试

运行测试脚本验证 `submitAlpha.py` 的逻辑：

```bash
python test_submitAlpha.py
```

## API 限制

- 请求频率限制：每秒 1 次
- 会话有效期：4 小时（脚本会在 3.5 小时时自动续期）
- 回测时间：根据 Alpha 复杂度，通常需要数秒到数分钟

## 回测参数

默认回测设置：

| 参数 | 值 | 说明 |
|------|-----|------|
| instrumentType | EQUITY | 股票 |
| region | USA | 美国市场 |
| universe | TOP3000 | 前 3000 只股票 |
| delay | 1 | 延迟 1 天 |
| decay | 0 | 无衰减 |
| neutralization | SUBINDUSTRY | 子行业中性化 |
| truncation | 0.08 | 截断 8% |
| pasteurization | ON | 开启巴氏消毒 |
| unitHandling | VERIFY | 单位验证 |
| nanHandling | ON | 处理缺失值 |
| language | FASTEXPR | 快速表达式 |

## 输出文件格式

### saved_alphas.jsonl

每行一个 JSON 对象，包含：

```json
{
  "alpha_id": "alpha_id",
  "expression": "alpha_expression",
  "sharpe": 1.5,
  "fitness": 1.2,
  "returns": 0.1,
  "turnover": 0.05,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### elite_alphas.jsonl

格式与 `saved_alphas.jsonl` 相同，但第一行包含元数据：

```json
{"submited": 3}
```

表示已提交了 3 个 Alpha。

## 安全注意事项

- **不要**将 `brain_credentials.json` 提交到版本控制系统
- 建议使用私有仓库托管代码
- 定期更换 API 密钥
- 提交 Alpha 前仔细检查策略表现

## 故障排除

### 登录失败

检查 `brain_credentials.json` 文件格式是否正确。

### 请求被限流

脚本已自动处理 429 错误，会等待 `Retry-After` 时间后重试。

### 会话过期

脚本会在 3.5 小时时自动续期，无需手动干预。

## 许可证

本项目仅供学习和研究使用。

## 联系方式

如有问题或建议，请提交 Issue。
