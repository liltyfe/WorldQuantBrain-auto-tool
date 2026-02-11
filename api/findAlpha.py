import requests
import json
import time
import os
import pandas as pd
from datetime import datetime

from requests.auth import HTTPBasicAuth
from time import sleep


# =================配置区域=================
# 1. 填入你的 API 凭证 (或者从文件读取)
API_KEY = "你的_API_KEY_在这里"
API_SECRET = "你的_API_SECRET_在这里"

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

    fundamental6 = get_datafields(s=sess, searchScope=searchScope, dataset_id='fundamental6')
    fundamental6 = fundamental6[fundamental6['type']=="MATRIX"]
    # fundamental6.head()
    alpha_list = []
    for _, row in fundamental6.iterrows():
        datafield_id = row['id']
        for i in range(2): 
            is_inverse = '-'
            if (i == 0):
                is_inverse = ''
            print("正在将如下Alpha表达式与setting封装")
            alpha_expression = f'{is_inverse}{datafield_id}/assets'
            print(alpha_expression)
            simulation_data = {
                'type': 'REGULAR',
                'settings': {
                    'instrumentType': 'EQUITY',
                    'region': 'USA',
                    'universe': 'TOP3000',
                    'delay': 1,
                    'decay': 0,
                    'neutralization': 'SUBINDUSTRY',
                    'truncation': 0.08,
                    'pasteurization': 'ON',
                    'unitHandling': 'VERIFY',
                    'nanHandling': 'ON',
                    'language': 'FASTEXPR',
                    'visualization': False,
                },
                'regular': alpha_expression
            }
            alpha_list.append(simulation_data)
    
    print(f'there are {len(alpha_list)} Alphas to simulate')

    for i, alpha in enumerate(alpha_list, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(alpha_list)}] 正在回测: {alpha.get('regular', '?')}")
        print(f"{'='*60}")

        sim_resp = sess.post(
            'https://api.worldquantbrain.com/simulations',
            json=alpha,
        )

        # ===== 调试：检查 POST 响应 =====
        print(f"[DEBUG] POST /simulations 状态码: {sim_resp.status_code}")
        if sim_resp.status_code not in (200, 201):
            print(f"[错误] 回测请求失败！响应内容:")
            try:
                print(json.dumps(sim_resp.json(), indent=2, ensure_ascii=False))
            except Exception:
                print(sim_resp.text[:500])
            sleep(5)
            continue

        # ===== 调试：检查 Location header =====
        if 'Location' not in sim_resp.headers:
            print(f"[错误] 响应中没有 Location header!")
            print(f"[DEBUG] 响应 headers: {dict(sim_resp.headers)}")
            try:
                print(f"[DEBUG] 响应 body: {json.dumps(sim_resp.json(), indent=2, ensure_ascii=False)}")
            except Exception:
                print(f"[DEBUG] 响应 body: {sim_resp.text[:500]}")
            sleep(5)
            continue

        try:
            sim_progress_url = sim_resp.headers['Location']
            print(f"[DEBUG] 轮询地址: {sim_progress_url}")
            while True:
                sim_progress_resp = sess.get(sim_progress_url)
                retry_after_sec = float(sim_progress_resp.headers.get("Retry-After", 0))
                if retry_after_sec == 0:  # simulation done!
                    break
                print(f"\r[等待] 回测进行中... 等待 {retry_after_sec} 秒", end='', flush=True)
                sleep(retry_after_sec)
            print()  # 换行

            # ===== 调试：打印完整回测结果 =====
            sim_result = sim_progress_resp.json()
            sim_status = sim_result.get("status", "UNKNOWN")
            print(f"[DEBUG] 回测完成，status={sim_status}，keys: {list(sim_result.keys())}")

            if sim_status == "ERROR":
                print(f"[错误] 回测失败！status=ERROR，完整响应:")
                print(json.dumps(sim_result, indent=2, ensure_ascii=False))
                sleep(2)
                continue

            if "alpha" not in sim_result:
                print(f"[错误] 回测完成但响应中没有 'alpha' 字段:")
                print(json.dumps(sim_result, indent=2, ensure_ascii=False))
                continue

            alpha_id = sim_result["alpha"]
            print(f"[成功] Alpha ID: {alpha_id}")

            # ===== 验证：通过 GET /alphas/{id} 获取详细指标 =====
            sharpe = None
            fitness = None
            returns_ = None
            turnover = None
            verify_resp = sess.get(f"{BASE_URL}/alphas/{alpha_id}")
            if verify_resp.status_code == 200:
                alpha_detail = verify_resp.json()
                is_data = alpha_detail.get("is", {})
                sharpe = is_data.get("sharpe")
                fitness = is_data.get("fitness")
                returns_ = is_data.get("returns")
                turnover = is_data.get("turnover")
                print(f"[验证] 平台确认存在 | Sharpe={sharpe} | Fitness={fitness} | Returns={returns_} | Turnover={turnover}")
            else:
                print(f"[警告] GET /alphas/{alpha_id} 返回 {verify_resp.status_code}: {verify_resp.text[:200]}")

            # 保存已成功测试的 alpha 到本地（JSON Lines 格式）
            ts = datetime.now(datetime.UTC).isoformat() if hasattr(datetime, 'UTC') else datetime.utcnow().isoformat() + 'Z'
            record = {
                'alpha_id': alpha_id,
                'expression': alpha.get('regular') if isinstance(alpha, dict) else None,
                'sharpe': sharpe,
                'fitness': fitness,
                'returns': returns_,
                'turnover': turnover,
                'timestamp': ts
            }
            save_path = os.path.join(os.path.dirname(__file__), 'saved_alphas.jsonl')
            with open(save_path, 'a', encoding='utf-8') as fout:
                fout.write(json.dumps(record, ensure_ascii=False) + '\n')
            print(f"[保存] 已将 alpha 保存到 {save_path}")

            # 高质量 alpha 额外保存（Sharpe > 1.25 且 Fitness > 1）
            if sharpe is not None and fitness is not None and sharpe > 1.25 and fitness > 1:
                elite_path = os.path.join(os.path.dirname(__file__), 'elite_alphas.jsonl')
                with open(elite_path, 'a', encoding='utf-8') as fout:
                    fout.write(json.dumps(record, ensure_ascii=False) + '\n')
                print(f"[精选] Sharpe={sharpe}, Fitness={fitness} >>> 已额外保存到 {elite_path}")

        except Exception as e:
            print(f"[异常] 回测过程出错: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            sleep(10)
