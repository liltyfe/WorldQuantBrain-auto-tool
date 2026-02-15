import json
from pathlib import Path
import pandas as pd


def generate_alphas(template, data_file, output_file, placeholder='{field}'):
    """
    根据模板和数据文件批量生成 alpha 表达式
    
    Args:
        template: alpha 表达式模板，如 "rank(ts_decay_linear(ts_delta({field}, 252), 10))"
        data_file: 数据文件路径，包含 id 字段的 CSV 文件
        output_file: 输出文件路径
        placeholder: 占位符，默认为 {field}
    
    Returns:
        生成的 alpha 数量
    """
    try:
        df = pd.read_csv(data_file)
        if 'id' not in df.columns:
            print(f"[错误] 数据文件中没有 'id' 列，可用列: {list(df.columns)}")
            return 0
        fields = df['id'].dropna().tolist()
        print(f"[成功] 从 {data_file} 读取了 {len(fields)} 个字段")
    except FileNotFoundError:
        print(f"[错误] 数据文件不存在: {data_file}")
        return 0
    except Exception as e:
        print(f"[错误] 读取数据文件失败: {e}")
        return 0
    
    if placeholder not in template:
        print(f"[错误] 模板中没有找到占位符 '{placeholder}'")
        print(f"[提示] 请在模板中使用 '{placeholder}' 作为可变字段的位置")
        return 0
    
    alphas = []
    for field in fields:
        alpha = template.replace(placeholder, str(field))
        alphas.append({"expression": alpha})
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(alphas, f, ensure_ascii=False, indent=2)
    
    print(f"[保存] 已将 {len(alphas)} 个 alpha 保存到 {output_path}")
    
    print(f"\n--- 前 5 条预览 ---")
    for a in alphas[:5]:
        print(a['expression'])
    
    return len(alphas)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Alpha 表达式批量生成工具")
    print("="*60)
    
    # 1. 输入数据文件路径
    print("\n请输入数据文件路径 (CSV格式，包含 id 列):")
    print("  示例: ../Data/news12_MATRIX.csv")
    data_file = input("数据文件路径: ").strip()
    if not data_file:
        print("[错误] 数据文件路径不能为空")
        exit()
    
    # 2. 输入 alpha 模板
    print("\n请输入 Alpha 表达式模板:")
    print("  使用 {field} 作为可变字段占位符")
    print("  示例: rank(ts_decay_linear(ts_delta({field}, 252), 10))")
    template = input("模板: ").strip()
    if not template:
        print("[错误] 模板不能为空")
        exit()
    
    # 3. 输入占位符（可选）
    print("\n请输入占位符 [默认: {field}]:")
    placeholder = input("占位符: ").strip()
    if not placeholder:
        placeholder = '{field}'
    
    # 4. 检查占位符是否在模板中
    if placeholder not in template:
        print(f"\n[警告] 模板中没有找到占位符 '{placeholder}'")
        print(f"  模板: {template}")
        print(f"  占位符: {placeholder}")
        confirm = input("是否继续? (y/n): ").strip().lower()
        if confirm != 'y':
            print("[取消] 用户取消操作")
            exit()
    
    # 5. 自动生成输出文件名
    data_path = Path(data_file)
    output_name = data_path.stem + '_alphas.json'
    output_path = data_path.parent.parent / 'alpha_expressions' / output_name
    
    # 6. 确认
    print("\n" + "-"*60)
    print("配置确认:")
    print(f"  数据文件: {data_file}")
    print(f"  模板: {template}")
    print(f"  占位符: {placeholder}")
    print(f"  输出文件: {output_path}")
    print("-"*60)
    
    confirm = input("\n确认开始生成? (y/n) [默认: y]: ").strip().lower()
    if confirm and confirm != 'y':
        print("[取消] 用户取消操作")
        exit()
    
    print("\n" + "="*60)
    print("开始生成 Alpha 表达式...")
    print("="*60 + "\n")
    
    count = generate_alphas(
        template=template,
        data_file=data_file,
        output_file=output_path,
        placeholder=placeholder
    )
    
    print(f"\n{'='*60}")
    print(f"完成！共生成 {count} 个 Alpha 表达式")
    print(f"{'='*60}")
