import requests
import json
import time
import os
from pathlib import Path
from requests.auth import HTTPBasicAuth

# =================配置区域=================
creds_path = os.path.join(os.path.dirname(__file__), 'brain_credentials.json')
try:
    with open(creds_path, 'r') as f:
        creds = json.load(f)
        if isinstance(creds, (list, tuple)) and len(creds) >= 2:
            API_KEY, API_SECRET = creds[:2]
        elif isinstance(creds, dict):
            API_KEY = creds.get("API_KEY") or creds.get("api_key")
            API_SECRET = creds.get("API_SECRET") or creds.get("api_secret")
        else:
            raise ValueError("凭据文件格式不正确，请使用 ['API_KEY','API_SECRET'] 或 {API_KEY:..., API_SECRET:...}")
except FileNotFoundError:
    raise FileNotFoundError(f"找不到凭据文件: {creds_path}. 请创建包含 [\"API_KEY\", \"API_SECRET\"] 的 JSON 文件，或直接在代码中设置 API_KEY/API_SECRET。")
except Exception:
    raise

BASE_URL = "https://api.worldquantbrain.com"


# =================核心函数=================

def get_alpha(elite_alpha_path):
    """从文件读取精英 Alpha 表达式"""
    objs = []
    p = Path(elite_alpha_path)
    if p.suffix.lower() in ('.jsonl', '.jl'):
        with p.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    objs.append(json.loads(line))
                except Exception:
                    continue
        return objs
    else:
        return objs


def get_session():
    """建立连接会话并验证身份"""
    sess = requests.Session()
    sess.auth = HTTPBasicAuth(API_KEY, API_SECRET)
    
    response = sess.post(f"{BASE_URL}/authentication")
    if response.status_code in (200, 201):
        print(f"[成功] 登录成功，Token: {response.text}")
    else:
        print(f"[失败] 登录失败: {response.status_code} - {response.text}")
        exit()
    return sess


def submit_alpha(sess, objs, count):
    initial_count = count
    success_count = 0
    submitted_count = 0

    alpha_ids = []
    for obj in objs:
        alpha_id = obj.get("alpha_id")
        if not alpha_id:
            print(f"[警告] 对象缺少 'alpha_id' 字段，跳过: {obj}")
            continue
        alpha_ids.append(alpha_id)

    for alpha_id in alpha_ids:
        if success_count >= initial_count:
            print(f"[完成] 已提交 {success_count} 个 Alpha，达到设定的提交数量上限。")
            return submitted_count
        print(f"[中] 正在提交 Alpha ID: {alpha_id} ...")
        submit_url = f"{BASE_URL}/alphas/{alpha_id}/submit"
        result = sess.post(submit_url)
        while True:
            if "Retry-After" in result.headers:
                wait_time = float(result.headers["Retry-After"])
                print(f"[等待] 提交处理中... 等待 {wait_time} 秒")
                time.sleep(wait_time)
                result = sess.get(submit_url)
            else:
                break
                
        if result.status_code == 200:
            print(f"[成功] Alpha 提交成功！")
            success_count += 1
            submitted_count += 1
        else:
            print(f"[失败] 提交失败: {result.text}")
            submitted_count += 1

    if success_count >= initial_count:
        print(f"[完成] 已提交 {success_count} 个 Alpha，达到设定的提交数量上限。")
        return submitted_count
    else:
        print(f"[未完成] 已提交 {success_count} 个 Alpha，Alpha数量不够，未达到设定的提交数量上限。")
        return submitted_count


# =================主程序=================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("WorldQuant Brain Alpha 提交工具")
    print("="*60)
    
    # 1. 输入精英 Alpha 文件路径
    print("\n请输入精英 Alpha 文件路径 (JSONL格式):")
    print("  示例: ../alpha_result/news12_MATRIX/elite_alphas.jsonl")
    elite_alpha_path = input("文件路径: ").strip()
    if not elite_alpha_path:
        print("[错误] 文件路径不能为空")
        exit()
    
    elite_path = Path(elite_alpha_path)
    if not elite_path.exists():
        print(f"[错误] 文件不存在: {elite_path}")
        exit()
    
    # 2. 输入提交数量
    print("\n请输入要提交的 Alpha 数量:")
    submit_count_str = input("数量 [默认: 1]: ").strip()
    if submit_count_str:
        try:
            submit_count = int(submit_count_str)
            if submit_count <= 0:
                print("[错误] 提交数量必须大于 0")
                exit()
        except ValueError:
            print("[错误] 请输入有效的数字")
            exit()
    else:
        submit_count = 1
    
    # 3. 登录
    print("\n" + "="*60)
    print("正在登录...")
    print("="*60 + "\n")
    
    session = get_session()
    
    # 4. 获取精英 Alpha
    print("\n" + "="*60)
    print("正在读取精英 Alpha...")
    print("="*60)
    
    objs = get_alpha(elite_path)
    if not objs:
        print(f"[错误] 没有找到有效的精英 Alpha 表达式，请检查文件路径和内容。")
        exit()
    
    submitted_count = objs[0].get("submitted", 0) if isinstance(objs[0], dict) else -1
    if submitted_count == -1:
        print(f"[警告] 没有找到 'submitted' 字段，无法确定已提交数量，请检查文件内容。")
        print(f"[提示] 文件第一行应该包含元数据: {{\"submitted\": 0}}")
        exit()
    
    elite_alphas = objs[submitted_count + 1:]
    available_count = len(elite_alphas)
    
    print(f"[信息] 已提交数量: {submitted_count}")
    print(f"[信息] 可提交数量: {available_count}")
    
    if available_count == 0:
        print(f"[错误] 没有可提交的 Alpha，所有 Alpha 已提交完毕。")
        exit()
    
    if submit_count > available_count:
        print(f"[警告] 请求提交 {submit_count} 个，但只有 {available_count} 个可提交")
        confirm = input("是否继续提交所有可用的 Alpha? (y/n): ").strip().lower()
        if confirm != 'y':
            print("[取消] 用户取消操作")
            exit()
        submit_count = available_count
    
    # 5. 确认
    print("\n" + "-"*60)
    print("配置确认:")
    print(f"  文件路径: {elite_path}")
    print(f"  已提交数量: {submitted_count}")
    print(f"  可提交数量: {available_count}")
    print(f"  本次提交: {submit_count}")
    print("-"*60)
    
    confirm = input("\n确认开始提交? (y/n) [默认: y]: ").strip().lower()
    if confirm and confirm != 'y':
        print("[取消] 用户取消操作")
        exit()
    
    # 6. 提交 Alpha
    print("\n" + "="*60)
    print("开始提交 Alpha...")
    print("="*60 + "\n")
    
    actual_submitted_count = submit_alpha(session, elite_alphas, submit_count)
    print(f"\n[结果] 剩余可提交的 Alpha 数量: {available_count - actual_submitted_count}")
    
    # 7. 更新已提交数量并写回文件
    if objs and isinstance(objs[0], dict) and "submitted" in objs[0]:
        objs[0]["submitted"] += actual_submitted_count
        
        with open(elite_path, 'w', encoding='utf-8') as f:
            for obj in objs:
                f.write(json.dumps(obj) + '\n')
        print(f"\n[更新] 已将新的提交数量 ({objs[0]['submitted']}) 更新到文件: {elite_path}")
    else:
        print(f"[警告] 无法更新文件中的提交数量，因首行格式不符合预期。")
    
    print("\n" + "="*60)
    print("提交任务完成！")
    print("="*60)
