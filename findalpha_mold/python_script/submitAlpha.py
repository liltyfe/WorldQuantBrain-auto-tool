import requests
import json
import time
import json as _json
import os
from pathlib import Path
from requests.auth import HTTPBasicAuth

# =================配置区域=================
# 优先从脚本所在目录读取凭据文件，避免因不同工作目录导致找不到文件
creds_path = os.path.join(os.path.dirname(__file__), 'brain_credentials.json')
try:
    with open(creds_path, 'r') as f:
        creds = json.load(f)
        # 支持两种格式：["API_KEY", "API_SECRET"] 或 {"API_KEY":..., "API_SECRET":...}
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

# 默认使用相对于项目的相对路径（基于本文件位置）。
# 如需使用其它文件，请直接改为绝对路径或在运行前覆盖该变量。
elite_alpha_path = Path(__file__).resolve().parent / 'alpha_result' / 'fund6_subindustry' / 'elite_alphas.jsonl'
submit_count = 1  # 提交的 Alpha 数量，默认为 1

# =================核心函数=================

def get_alpha(elite_alpha_path):
    """从文件读取精英 Alpha 表达式"""
    # - JSONL 文件（每行一个 JSON 对象） -> 返回第一个对象（默认）或所有对象
    objs = []
    p = Path(elite_alpha_path)
    if p.suffix.lower() in ('.jsonl', '.jl'):
        with p.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    objs.append(_json.loads(line))
                except Exception:
                    # 如果某一行不是有效 JSON，则跳过或可根据需要抛出
                    continue
        # 默认返回第一个对象以便与原来的单表达式用法兼容
        return objs
    else:
        return objs  # 如果不是 JSONL 文件，返回空列表

def get_session():
    """建立连接会话并验证身份"""
    sess = requests.Session()
    # 设置 Basic Auth
    sess.auth = HTTPBasicAuth(API_KEY, API_SECRET)
    
    # 验证是否登录成功 (对应截图 1)
    response = sess.post(f"{BASE_URL}/authentication")
    if response.status_code in (200, 201):
        print(f"[成功] 登录成功，Token: {response.text}")
    else:
        print(f"[失败] 登录失败: {response.status_code} - {response.text}")
        exit()
    return sess


def submit_alpha(sess, objs, count=submit_count):
    initial_count = count  # 保存初始值，用于计算已成功提交数量
    success_count = 0  # 记录成功提交的数量
    submitted_count = 0  # 记录已提交的数量


    # 解析alpha_ids参数，支持单字符串或列表
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
        # 轮询等待提交结果
        while True:
            if "Retry-After" in result.headers:
                wait_time = float(result.headers["Retry-After"])
                print(f"[等待] 提交处理中... 等待 {wait_time} 秒")
                time.sleep(wait_time)
                result = sess.get(submit_url) # 注意这里通常是 get 查询状态
            else:
                break
                
        if result.status_code == 200:
            print(f"[成功] Alpha 提交成功！")
            success_count += 1
            submitted_count += 1
        else:
            print(f"[失败] 提交失败: {result.text}")
            submitted_count += 1  # 即使失败也算作已处理一个 Alpha，继续提交下一个

    if success_count >= initial_count:
        print(f"[完成] 已提交 {success_count} 个 Alpha，达到设定的提交数量上限。")
        return submitted_count
    else:
        print(f"[未完成] 已提交 {success_count} 个 Alpha，Alpha数量不够，未达到设定的提交数量上限。")
        return submitted_count


# =================主程序=================


if __name__ == "__main__":
    # 1. 登录
    session = get_session()
    
    # 2. 获取精英 Alpha 表达式
    objs = get_alpha(elite_alpha_path)
    if not objs:
        print(f"[错误] 没有找到有效的精英 Alpha 表达式，请检查文件路径和内容。")
        exit()
    submitted_count = objs[0].get("submitted", 0) if isinstance(objs[0], dict) else -1
    if submitted_count == -1:
        print(f"[警告] 没有找到 'submitted' 字段，无法确定已提交数量，请检查文件内容。")
        exit()
    elite_alphas = objs[submitted_count + 1:]  # 跳过头部元数据(objs[0])和已提交的N个Alpha
    # 3. 提交 Alpha
    actual_submitted_count = submit_alpha(session, elite_alphas, submit_count)
    print(f"[结果] 剩余可提交的 Alpha 数量: {len(elite_alphas) - actual_submitted_count}")

    # 4. 更新已提交数量并写回文件
    if objs and isinstance(objs[0], dict) and "submitted" in objs[0]:
        objs[0]["submitted"] += actual_submitted_count
        
        # 将更新后的数据写回文件
        with open(elite_alpha_path, 'w', encoding='utf-8') as f:
            for obj in objs:
                f.write(json.dumps(obj) + '\n')
        print(f"[更新] 已将新的提交数量 ({objs[0]['submitted']}) 更新到文件: {elite_alpha_path}")
    else:
        print(f"[警告] 无法更新文件中的提交数量，因首行格式不符合预期。")



