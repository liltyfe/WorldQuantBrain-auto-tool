import json
import itertools
from pathlib import Path
import pandas as pd


def read_data_fields(data_file):
    """从数据文件读取id字段"""
    try:
        df = pd.read_csv(data_file)
        if 'id' not in df.columns:
            print(f"[错误] 数据文件中没有 'id' 列，可用列: {list(df.columns)}")
            return []
        fields = df['id'].dropna().tolist()
        return fields
    except FileNotFoundError:
        print(f"[错误] 数据文件不存在: {data_file}")
        return []
    except Exception as e:
        print(f"[错误] 读取数据文件失败: {e}")
        return []


def generate_combinations(params, data_files_cache=None, base_path=None):
    """
    生成参数的所有组合
    
    Args:
        params: 参数字典，如 {group_op: [...], ts_op: [...]}
        data_files_cache: 数据文件缓存
        base_path: 基准路径，用于解析相对路径
    
    Returns:
        list: 所有参数组合的列表
    """
    if data_files_cache is None:
        data_files_cache = {}
    
    param_lists = {}
    
    for key, value in params.items():
        if isinstance(value, str) and value.endswith('_datafields'):
            # 这是一个数据文件引用
            data_key = value
            if data_key not in data_files_cache:
                print(f"[错误] 找不到数据文件引用: {data_key}")
                return []
            param_lists[key] = data_files_cache[data_key]
        elif isinstance(value, list):
            param_lists[key] = value
        else:
            param_lists[key] = [value]
    
    # 生成笛卡尔积
    keys = list(param_lists.keys())
    values = list(param_lists.values())
    combinations = list(itertools.product(*values))
    
    result = []
    for combo in combinations:
        result.append(dict(zip(keys, combo)))
    
    return result


def generate_alphas_from_template(template_config, data_files_cache=None, base_path=None):
    """
    根据单个模板配置生成Alpha
    
    Args:
        template_config: 模板配置
        data_files_cache: 数据文件缓存
        base_path: 基准路径
    
    Returns:
        list: Alpha表达式列表
    """
    template = template_config.get('template', '')
    params = template_config.get('params', {})
    name = template_config.get('name', 'unnamed')
    
    print(f"\n[模板] {name}")
    print(f"  模板: {template}")
    
    # 生成所有参数组合
    param_combinations = generate_combinations(params, data_files_cache, base_path)
    print(f"  参数组合数: {len(param_combinations)}")
    
    # 生成Alpha表达式
    alphas = []
    for combo in param_combinations:
        try:
            alpha = template
            for key, value in combo.items():
                placeholder = '{' + key + '}'
                alpha = alpha.replace(placeholder, str(value))
            alphas.append({'expression': alpha})
        except Exception as e:
            print(f"  [警告] 生成Alpha失败: {e}")
            continue
    
    print(f"  成功生成: {len(alphas)} 个Alpha")
    return alphas


def load_config(config_path):
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"[错误] 配置文件不存在: {config_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"[错误] 配置文件解析失败: {e}")
        return None
    except Exception as e:
        print(f"[错误] 加载配置文件失败: {e}")
        return None


def batch_generate(config_path):
    """批量生成Alpha"""
    print("\n" + "="*60)
    print("Alpha 批量生成工具")
    print("="*60)
    
    # 加载配置
    config = load_config(config_path)
    if not config:
        return 0
    
    name = config.get('name', '未命名')
    description = config.get('description', '')
    print(f"\n[配置] {name}")
    if description:
        print(f"      {description}")
    
    # 基准路径
    base_path = Path(config_path).parent
    
    # 加载数据文件
    data_files = config.get('data_files', {})
    data_files_cache = {}
    
    print(f"\n[加载数据文件]")
    for key, data_path in data_files.items():
        full_path = base_path / data_path
        fields = read_data_fields(str(full_path))
        if fields:
            data_files_cache[key] = fields
            print(f"  {key}: {len(fields)} 个字段")
    
    # 处理模板
    templates = config.get('templates', [])
    if not templates:
        print(f"[错误] 配置中没有找到模板")
        return 0
    
    print(f"\n[处理模板]")
    all_alphas = []
    for template_config in templates:
        alphas = generate_alphas_from_template(template_config, data_files_cache, base_path)
        all_alphas.extend(alphas)
    
    # 保存结果
    output_config = config.get('output', {})
    output_file = output_config.get('file', '../alpha_expressions/generated_alphas.json')
    output_path = base_path / output_file
    
    print(f"\n[保存]")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_alphas, f, ensure_ascii=False, indent=2)
    
    print(f"  文件: {output_path}")
    print(f"  总数: {len(all_alphas)} 个Alpha")
    
    # 预览
    if all_alphas:
        print(f"\n--- 前 5 条预览 ---")
        for a in all_alphas[:5]:
            print(f"  {a['expression']}")
        
        if len(all_alphas) > 5:
            print(f"  ... 还有 {len(all_alphas) - 5} 个")
    
    print(f"\n{'='*60}")
    print(f"完成！共生成 {len(all_alphas)} 个 Alpha 表达式")
    print(f"{'='*60}")
    
    return len(all_alphas)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Alpha 批量生成工具 (配置文件模式)")
    print("="*60)
    
    # 输入配置文件路径
    print("\n请输入配置文件路径 (JSON格式):")
    print("  示例: ../alpha_configs/example_batch_config.json")
    config_file = input("配置文件路径: ").strip()
    
    if not config_file:
        print("[错误] 配置文件路径不能为空")
        exit()
    
    config_path = Path(config_file)
    if not config_path.exists():
        print(f"[错误] 配置文件不存在: {config_path}")
        exit()
    
    # 执行批量生成
    count = batch_generate(config_path)
