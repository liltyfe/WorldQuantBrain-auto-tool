import requests
import json
import time
import os
from requests.auth import HTTPBasicAuth

# =================配置区域=================
# 1. 填入你的 API 凭证 (或者从文件读取)
API_KEY = "你的_API_KEY_在这里"
API_SECRET = "你的_API_SECRET_在这里"

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

# =================核心函数=================

def get_session():
    """建立连接会话并验证身份"""
    sess = requests.Session()
    # 设置 Basic Auth
    sess.auth = HTTPBasicAuth(API_KEY, API_SECRET)
    
    # 验证是否登录成功 (对应截图 1)
    response = sess.post(f"{BASE_URL}/authentication")
    if response.status_code == 200:
        print(f"[成功] 登录成功，Token: {response.json().get('token')}")
    else:
        print(f"[失败] 登录失败: {response.status_code} - {response.text}")
        exit()
    return sess

def simulate_alpha(sess, alpha_expression):
    """发起回测 (对应截图 2 和 3)"""
    
    # 构造回测参数 (对应截图 2)
    simulation_data = {
        "type": "REGULAR",
        "settings": {
            "instrumentType": "EQUITY",
            "region": "USA",
            "universe": "TOP3000",
            "delay": 1,
            "decay": 0,
            "neutralization": "INDUSTRY",
            "truncation": 0.08,
            "pasteurization": "ON",
            "unitHandling": "VERIFY",
            "nanHandling": "OFF",
            "language": "FASTEXPR",
            "visualization": False,
        },
        # 这里填入你的 Alpha 表达式
        "regular": alpha_expression 
    }

    print(f"[中] 正在发送回测请求: {alpha_expression}")
    
    # 发送回测请求 (对应截图 3)
    sim_resp = sess.post(f"{BASE_URL}/simulations", json=simulation_data)
    
    if sim_resp.status_code != 201:
        print(f"[错误] 回测请求失败: {sim_resp.text}")
        return None

    # 获取查询进度的 URL (从 Location Header 中获取)
    sim_progress_url = sim_resp.headers['Location']
    
    # 轮询等待回测完成 (对应截图 3 的 while 循环)
    while True:
        sim_progress_resp = sess.get(sim_progress_url)
        
        # 获取 Retry-After 时间，如果头部没有该字段，说明完成了
        retry_after_sec = float(sim_progress_resp.headers.get("Retry-After", 0))
        
        if retry_after_sec == 0:
            print("[完成] 回测结束！")
            break
        
        print(f"[等待] 回测进行中... 等待 {retry_after_sec} 秒")
        time.sleep(retry_after_sec)

    # 获取最终结果
    result_json = sim_progress_resp.json()
    
    # 打印关键指标
    alpha_id = result_json.get("alpha")
    pnl = result_json.get("pnl")
    sharpe = result_json.get("sharpe")
    print(f"Alpha ID: {alpha_id}")
    print(f"Sharpe: {sharpe}")
    
    return alpha_id

def submit_alpha(sess, alpha_id):
    """提交 Alpha (对应截图 4)"""
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
        return True
    else:
        print(f"[失败] 提交失败: {result.text}")
        return False

# =================主程序=================

if __name__ == "__main__":
    # 1. 登录
    session = get_session()
    
    # 2. 定义你想跑的 Alpha (使用之前的稳健动量策略)
    my_alpha = "group_neutralize(rank(ts_rank(returns(60), 250) / ts_mean(abs(returns(1)), 60)), industry)"
    
    # 3. 回测
    alpha_id = simulate_alpha(session, my_alpha)
    
    # 4. 提交 (警告：只有当你确认 Alpha 表现好时再取消注释)
    # if alpha_id:
    #     user_input = input("是否要正式提交这个 Alpha? (y/n): ")
    #     if user_input.lower() == 'y':
    #         submit_alpha(session, alpha_id)