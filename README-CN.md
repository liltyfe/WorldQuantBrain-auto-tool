# WorldQuant Brain Python 工具集

本项目提供一组轻量级 Python 脚本，用于在 WorldQuant Brain 平台完成以下流程：

- 获取数据字段（DataFields）
- 批量生成 Alpha 表达式
- 回测 Alpha 并保存结果
- 提交筛选后的优质 Alpha

项目以脚本交互为主（CLI + `input()`），适合快速实验与小规模自动化。

## 一、项目结构

```text
findalpha_mold/
  Data/                       # 数据字段 CSV（输入）
  alpha_configs/              # 批量生成配置
  alpha_expressions/          # 生成的表达式（运行产物）
  alpha_log/                  # 回测日志（运行产物）
  alpha_result/               # 回测/提交结果（运行产物）
  python_script/              # 核心脚本
```

核心脚本说明：

- `findalpha_mold/python_script/getdata.py`：拉取数据字段并保存为 CSV
- `findalpha_mold/python_script/generate_alphas.py`：单模板生成 Alpha 表达式
- `findalpha_mold/python_script/generate_alphas_batch.py`：基于 JSON 配置批量生成表达式
- `findalpha_mold/python_script/simulateAlpha.py`：批量回测表达式并落盘结果
- `findalpha_mold/python_script/submitAlpha.py`：提交优质 Alpha
- `findalpha_mold/python_script/inspect_alpha_packet.py`：检查浏览器导出的 HAR/JSON 数据包并生成字段清单

## 二、环境要求

- Python 3.10+（推荐 3.11+）
- 依赖包：
  - `requests`
  - `pandas`

建议安装方式：

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install requests pandas
```

可选开发工具：

```bash
python -m pip install pytest ruff
```

## 三、凭证配置

在 `findalpha_mold/python_script/` 下创建：

`brain_credentials.json`

支持两种格式：

```json
["API_KEY", "API_SECRET"]
```

或

```json
{
  "API_KEY": "your_api_key",
  "API_SECRET": "your_api_secret"
}
```

注意：请勿将凭证提交到仓库。

## 四、快速开始（推荐流程）

建议先进入脚本目录再执行：

```bash
cd findalpha_mold/python_script
```

### 1）获取数据字段

```bash
python getdata.py
```

脚本会交互式询问数据集与字段类型，结果保存到 `findalpha_mold/Data/`。

### 2）生成 Alpha 表达式

单模板模式：

```bash
python generate_alphas.py
```

批量配置模式：

```bash
python generate_alphas_batch.py
```

### 3）批量回测 Alpha

```bash
python simulateAlpha.py
```

常见输出：

- `saved_alphas.jsonl`：全部回测结果
- `elite_alphas.jsonl`：筛选后的优质 Alpha
- `alphas_detailed.csv`：详细指标表
- `findalpha_mold/alpha_log/`：运行日志

### 4）提交优质 Alpha

```bash
python submitAlpha.py
```

### 5）检查平台导出的原始数据包

如果你没有可用的官方 API，但已经在浏览器中登录平台，可以先在开发者工具的 `Network` 面板导出 `HAR` 文件，再离线检查其中的回测响应。

```bash
python inspect_alpha_packet.py --input ../Data/sample.har
```

常见输出：

- `raw_responses/`：提取出的原始响应 JSON/TXT
- `field_inventory.csv`：逐字段清单，便于 Excel 筛选
- `field_summary.csv`：按字段路径聚合后的简表
- `response_index.json`：响应索引

## 五、批量生成配置说明

`generate_alphas_batch.py` 读取 JSON 配置文件（示例见 `findalpha_mold/alpha_configs/example_batch_config.json`）。

典型配置项：

- `templates`：模板列表
- `params`：模板参数（支持列表笛卡尔积）
- `data_files`：外部数据字段文件映射
- `output.file`：输出表达式文件路径

请控制参数组合规模，避免一次生成过多表达式导致后续回测压力过大。

## 六、检查与质量保障命令

### 编译检查（烟雾测试）

```bash
python -m compileall findalpha_mold/python_script
```

### Lint（安装 ruff 后）

```bash
ruff check findalpha_mold/python_script
ruff format --check findalpha_mold/python_script
```

### 测试（若后续新增 pytest 用例）

```bash
python -m pytest
python -m pytest path/to/test_file.py
python -m pytest path/to/test_file.py::test_name
python -m pytest path/to/test_file.py::TestClass::test_method
```

## 七、常见问题

1. 登录失败

- 检查 `brain_credentials.json` 路径是否正确
- 检查 JSON 格式是否符合上述两种格式之一

2. 回测或接口请求被限流

- 这是正常现象，脚本会按 `Retry-After` 等待重试（已实现的接口）

3. 生成或提交阶段没有可用 Alpha

- 确认上一步产物文件存在且内容有效
- 确认 `elite_alphas.jsonl` 不是空文件

4. CSV 读取报错（缺少列）

- 检查输入 CSV 是否包含脚本要求的列（如 `id`）

## 八、安全与提交规范

- 不要提交任何密钥、令牌、会话信息
- 不要在日志中输出敏感信息
- `alpha_result/`、`alpha_log/`、`alpha_expressions/` 通常为运行产物

## 九、当前局限

- 目前仓库尚未提交自动化测试文件
- 尚未提交统一的 lint/type-check 配置
- 部分历史文档可能与当前目录结构不完全一致

欢迎在不破坏现有脚本行为的前提下逐步完善。
