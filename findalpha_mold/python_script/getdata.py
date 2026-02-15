import requests
import json
import time
import os
import pandas as pd
from pathlib import Path
from datetime import datetime

from requests.auth import HTTPBasicAuth
from time import sleep


# =================配置区域=================
API_KEY = "你的_API_KEY_在这里"
API_SECRET = "你的_API_SECRET_在这里"

searchScope = {'region': 'USA', 'delay': '1', 'universe': 'TOP3000', 'instrumentType': 'EQUITY'}

# 优先从脚本所在目录读取凭据文件，避免因不同工作目录导致找不到文件
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
SESSION_TTL = 3.5 * 3600


# =================核心函数=================

class BrainSession:
    """自动续期的会话包装器，每隔 ~3.5 小时自动重新认证（会话有效期 4 小时）"""

    def __init__(self):
        self._session = requests.Session()
        self._session.auth = HTTPBasicAuth(API_KEY, API_SECRET)
        self._last_auth_time = 0
        self._authenticate()

    def _authenticate(self):
        response = self._session.post(f"{BASE_URL}/authentication")
        if response.status_code in (200, 201):
            self._last_auth_time = time.time()
            print(f"[成功] 登录成功， {response.text}")
        else:
            print(f"[失败] 登录失败: {response.status_code} - {response.text}")
            exit()

    def _ensure_valid(self):
        elapsed = time.time() - self._last_auth_time
        if elapsed >= SESSION_TTL:
            print(f"[续期] 会话已持续 {elapsed/3600:.1f} 小时，正在重新认证...")
            self._authenticate()

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
        if x == 0 and first_json is not None:
            payload = first_json
        else:
            sleep(1.1)
            url = url_template.format(x=x)
            resp = s.get(url, timeout=15)
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
    print("\n" + "="*60)
    print("WorldQuant Brain 数据字段获取工具")
    print("="*60)
    
    # 1. 输入数据集 ID
    print("\n请输入数据集 ID:")
    print("  常用数据集: news12, fundamental6, option8, model16, etc.")
    dataset_id = input("数据集 ID: ").strip()
    if not dataset_id:
        print("[错误] 数据集 ID 不能为空")
        exit()
    
    # 2. 选择字段类型
    print("\n请选择字段类型:")
    print("  [1] MATRIX  - 矩阵类型字段")
    print("  [2] VECTOR  - 向量类型字段")
    print("  [3] ALL     - 所有字段")
    type_choice = input("请输入选项 (1/2/3) [默认: 3]: ").strip()
    
    type_map = {'1': 'MATRIX', '2': 'VECTOR', '3': 'ALL', '': 'ALL'}
    field_type = type_map.get(type_choice, 'ALL')
    
    # 3. 确认
    csv_path = Path(__file__).resolve().parent.parent / 'Data' / f'{dataset_id}_{field_type}.csv'
    
    print("\n" + "-"*60)
    print("配置确认:")
    print(f"  数据集 ID: {dataset_id}")
    print(f"  字段类型: {field_type}")
    print(f"  输出路径: {csv_path}")
    print("-"*60)
    
    confirm = input("\n确认开始获取? (y/n) [默认: y]: ").strip().lower()
    if confirm and confirm != 'y':
        print("[取消] 用户取消操作")
        exit()
    
    print("\n" + "="*60)
    print("开始获取数据...")
    print("="*60 + "\n")
    
    sess = get_session()
    
    dataset = get_datafields(s=sess, searchScope=searchScope, dataset_id=dataset_id)
    
    if field_type != 'ALL':
        before_count = len(dataset)
        dataset = dataset[dataset['type'] == field_type]
        after_count = len(dataset)
        print(f"\n[过滤] 类型={field_type}: {before_count} -> {after_count} 条")
    
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        dataset.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n{'='*60}")
        print(f"[完成] 已保存 {len(dataset)} 条数据到 {csv_path}")
        print(f"{'='*60}")
    except Exception as e:
        print(f"[错误] 无法保存文件: {e}")
