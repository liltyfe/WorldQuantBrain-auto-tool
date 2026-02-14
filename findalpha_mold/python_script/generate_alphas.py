import pandas as pd
from pathlib import Path


# =================配置区域=================

DATA_PATH_FUND = Path(__file__).resolve().parent / 'fundamental6_datafields_20260212_145958.csv'
DATA_PATH_OPT = Path(__file__).resolve().parent / 'option8_datafields_20260213_172143.csv'

SAVED_ALPHAS_PATH_FUND = Path(__file__).resolve().parent / 'alpha_expressions' / 'generated_alphas_fund_4.csv'
SAVED_ALPHAS_PATH_OPT = Path(__file__).resolve().parent / 'alpha_expressions' / 'generated_alphas_opt_5.csv'


# 1. 读取你上传的三个文件
try:
    df_fund = pd.read_csv(DATA_PATH_FUND)
    df_opt = pd.read_csv(DATA_PATH_OPT)
    print("成功读取数据文件！")
except FileNotFoundError:
    print("错误：请确保 CSV 文件在当前目录下。")
    exit()


fund_fields = df_fund['id'].tolist()
opt_fields = df_opt['id'].tolist()

generated_alphas_fun = []

# --- 生成模板 3：成长动量 (Growth) ---
print(f"正在生成成长类 Alpha (共 {len(fund_fields)} 个字段)...")
for field in fund_fields:
    # 跳过无意义的字段
    if field in ['assets', 'cap', 'market_cap', 'enterprise_value']:
        continue
    
    # 逻辑：年度增长 (Year-over-Year Growth)
    # 使用 decay_linear(..., 10) 是为了防止财报数据阶梯状跳变导致 Turnover 过低或过高
    alpha = f"rank(ts_decay_linear(ts_delta({field}, 252), 10))"
    generated_alphas_fun.append(alpha)

print(f"\n==========================================")
print(f"🎉 成功生成 {len(generated_alphas_fun)} 条全新策略！")
print(f"==========================================\n")

generated_alphas_opt = []

# --- 生成模板 4：期权情绪 (Sentiment) ---
print("正在生成期权情绪 Alpha...")
# 定义我们要寻找的时间窗口 (30天, 60天, 90天, 120天...)
windows = ['30', '60', '90', '120', '150', '180']

for w in windows:
    # 构造字段名
    iv_name = f"implied_volatility_call_{w}"
    hv_name = f"historical_volatility_{w}"
    
    # 只有当两个字段都存在于高覆盖率列表中时，才生成 Alpha
    if iv_name in opt_fields and hv_name in opt_fields:
        # 逻辑 A: 差值 (Spread) - 寻找恐慌溢价
        alpha_diff = f"rank({iv_name} - {hv_name})"
        generated_alphas_opt.append(alpha_diff)
        
        # 逻辑 B: 比率 (Ratio) - 寻找相对恐慌
        alpha_ratio = f"rank({iv_name} / {hv_name})"
        generated_alphas_opt.append(alpha_ratio)

# 3. 输出结果
print(f"\n==========================================")
print(f"🎉 成功生成 {len(generated_alphas_opt)} 条全新策略！")
print(f"==========================================\n")

print("--- 策略预览 (前 10 条) ---")
for a in generated_alphas_fun[:10]:
    print(a)

print("\n--- 策略预览 (前 10 条期权类) ---")
for a in generated_alphas_opt[:10]:
    print(a)

# 4. (可选) 保存到文件
pd.DataFrame(generated_alphas_fun, columns=['alpha']).to_csv(SAVED_ALPHAS_PATH_FUND, index=False)
pd.DataFrame(generated_alphas_opt, columns=['alpha']).to_csv(SAVED_ALPHAS_PATH_OPT, index=False)
print(f"\n已将生成的 Alpha 策略保存到 '{SAVED_ALPHAS_PATH_FUND}' 和 '{SAVED_ALPHAS_PATH_OPT}' 文件中！")