import requests
import json
import time
import os
import pandas as pd
import pathlib as Path
from datetime import datetime

from requests.auth import HTTPBasicAuth
from time import sleep


# =================配置区域=================
# 1. 填入你的 API 凭证 (或者从文件读取)
API_KEY = "你的_API_KEY_在这里"
API_SECRET = "你的_API_SECRET_在这里"

toget_dataset_id = 'pv1'

searchScope = {'region': 'USA', 'delay': '1', 'universe': 'TOP3000', 'instrumentType': 'EQUITY'}

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

# 会话有效期（秒）：4小时 = 14400秒，提前 30 分钟刷新以留余量
SESSION_TTL = 3.5 * 3600  # 3.5 小时

# =================核心函数=================

class BrainSession:
    """自动续期的会话包装器，每隔 ~3.5 小时自动重新认证（会话有效期 4 小时）"""

    def __init__(self):
        self._session = requests.Session()
        self._session.auth = HTTPBasicAuth(API_KEY, API_SECRET)
        self._last_auth_time = 0  # epoch, 强制首次认证
        self._authenticate()

    def _authenticate(self):
        """执行认证并刷新计时器"""
        response = self._session.post(f"{BASE_URL}/authentication")
        if response.status_code in (200, 201):
            self._last_auth_time = time.time()
            print(f"[成功] 登录成功， {response.text}")
        else:
            print(f"[失败] 登录失败: {response.status_code} - {response.text}")
            exit()

    def _ensure_valid(self):
        """检查会话是否即将过期，如过期则自动重新认证"""
        elapsed = time.time() - self._last_auth_time
        if elapsed >= SESSION_TTL:
            print(f"[续期] 会话已持续 {elapsed/3600:.1f} 小时，正在重新认证...")
            self._authenticate()

    # ---------- 代理常用 HTTP 方法 ----------
    def get(self, *args, **kwargs):
        self._ensure_valid()
        return self._session.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self._ensure_valid()
        return self._session.post(*args, **kwargs)

    def put(self, *args, **kwargs):
        self._ensure_valid()
        return self._session.put(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._ensure_valid()
        return self._session.delete(*args, **kwargs)

    def patch(self, *args, **kwargs):
        self._ensure_valid()
        return self._session.patch(*args, **kwargs)

    @property
    def auth(self):
        return self._session.auth

    @auth.setter
    def auth(self, value):
        self._session.auth = value


def get_session():
    """建立连接会话并验证身份（自动每 3.5 小时续期）"""
    return BrainSession()


def get_datafields(s, searchScope, dataset_id: str = '', search: str = ''):
    
    instrument_type = searchScope['instrumentType']
    region = searchScope['region']
    delay = searchScope['delay']
    universe = searchScope['universe']
    
    first_json = None
    if len(search) == 0:
        url_template = "https://api.worldquantbrain.com/data-fields?" + \
            f"&instrumentType={instrument_type}" + \
            f"&region={region}&delay={str(delay)}&universe={universe}&dataset.id={dataset_id}&limit=50" + \
            "&offset={x}"
        # 只请求一次 offset=0，同时拿 count 和第一页数据
        first_resp = s.get(url_template.format(x=0), timeout=15)
        first_json = first_resp.json()
        count = first_json['count']
        print(f"[INFO] 共 {count} 条数据，需要 {(count + 49) // 50} 页")
    else:
        url_template = "https://api.worldquantbrain.com/data-fields?" + \
            f"&instrumentType={instrument_type}" + \
            f"&region={region}&delay={str(delay)}&universe={universe}&limit=50" + \
            f"&search={search}" + \
            "&offset={x}"
        count = 100
        
    datafields_list = []
    for x in range(0, count, 50):
        # offset=0 已经请求过了，直接复用，不再重复请求
        if x == 0 and first_json is not None:
            payload = first_json
        else:
            # 遵守限流：每次请求前等待 1.1 秒（API 限制每秒 1 次）
            sleep(1.1)
            url = url_template.format(x=x)
            resp = s.get(url, timeout=15)
            # 如果被限流 (429)，等待后重试
            if resp.status_code == 429:
                wait = float(resp.headers.get('Retry-After', 2))
                print(f"[限流] 等待 {wait}s 后重试 offset={x}")
                sleep(wait)
                resp = s.get(url, timeout=15)
            payload = resp.json()

        if 'results' in payload:
            datafields_list.append(payload['results'])
            print(f"[OK] offset={x} 获取 {len(payload['results'])} 条")
        else:
            print(f"[WARN] offset={x} 响应无 'results'，keys={list(payload.keys())}")
    
    datafields_list_flat = [item for sublist in datafields_list for item in sublist]
    datafields_df = pd.DataFrame(datafields_list_flat)
    print(f"[INFO] 实际获取 {len(datafields_df)} 条 datafields")
    return datafields_df

if __name__ == "__main__":
    sess = get_session()

    dataset = get_datafields(s=sess, searchScope=searchScope, dataset_id=toget_dataset_id)
    dataset = dataset[dataset['type']=="MATRIX"]

    # 保存筛选后的 DataFrame 到脚本同目录（CSV，带时间戳）
    out_dir = os.path.dirname(__file__)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(out_dir, f"{toget_dataset_id}_datafields_{ts}.csv")
    try:
        dataset.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"[SAVED] {toget_dataset_id} ({len(dataset)} rows) -> {csv_path}")
    except Exception as e:
        print(f"[ERROR] 无法保存文件: {e}")


