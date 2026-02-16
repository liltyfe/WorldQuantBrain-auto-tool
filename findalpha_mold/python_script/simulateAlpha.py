import queue
import pandas as pd
import requests
import json
import time
import os
import threading
import traceback

from pathlib import Path
from datetime import datetime
from requests.auth import HTTPBasicAuth
from time import sleep
from threading import Semaphore


# =================配置区域=================
API_KEY = "你的_API_KEY_在这里"
API_SECRET = "你的_API_SECRET_在这里"

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

# =================多线程配置=================
MAX_CONCURRENT = 2  # 同时回测的最大数量（你的账号限制）
semaphore = Semaphore(MAX_CONCURRENT)  # PV操作信号量

# 线程安全队列
task_queue = queue.Queue()  # 存储待查询的alpha任务
alpha_expression_queue = queue.Queue()  # 存储待提交的alpha表达式

# 线程状态标志
stop_event = threading.Event()  # 用于优雅停止线程


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


def read_alphas(file_path):
    """
    从 JSON 文件读取 alpha 表达式
    
    Args:
        file_path: JSON 文件路径，格式为 [{"expression": "..."}, ...]
    
    Returns:
        list: alpha 表达式列表
    """
    alpha_list = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and 'expression' in item:
                    alpha_list.append(item['expression'])
                elif isinstance(item, str):
                    alpha_list.append(item)
        elif isinstance(data, dict) and 'expressions' in data:
            alpha_list = data['expressions']
        
        print(f"[成功] 从 {file_path} 读取了 {len(alpha_list)} 个 Alpha 表达式")
    except FileNotFoundError:
        print(f"[警告] 文件不存在: {file_path}")
    except json.JSONDecodeError as e:
        print(f"[错误] JSON 解析失败: {e}")
    except Exception as e:
        print(f"[错误] 读取文件失败: {e}")
    return alpha_list


# =================== 生产者进程 =====================
def submit_alpha_thread(sess, saved_path, elite_path):
    print("[提交线程] 启动")
    while not stop_event.is_set():
        try:
            try:
                alpha_expression = alpha_expression_queue.get(timeout=1)
            except queue.Empty:
                continue
            print(f"[提交线程] 准备提交: {alpha_expression[:50]}...")

            # ============ P操作 ================
            # 申请资源：如果当前已有3个在运行，这里会等待
            semaphore.acquire()
            print(f"[提交线程] P操作成功，剩余槽位: {semaphore._value}")

            print("正在将如下Alpha表达式与setting封装")
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

            sim_resp = sess.post(
                'https://api.worldquantbrain.com/simulations',
                json=simulation_data,
            )

            print(f"[DEBUG] POST /simulations 状态码: {sim_resp.status_code}")
            if sim_resp.status_code not in (200, 201):
                print(f"[错误] 回测请求失败！响应内容:{sim_resp.text[:500]}")
                semaphore.release()  # 回测失败要释放信号量
                alpha_expression_queue.task_done()  # 标记任务完成
                continue

            if 'Location' not in sim_resp.headers:
                print(f"[错误] 响应中没有 Location header!")
                print(f"[DEBUG] 响应 headers: {dict(sim_resp.headers)}")
                semaphore.release()  # 回测失败要释放信号量
                alpha_expression_queue.task_done()  # 标记任务完成
                try:
                    print(f"[DEBUG] 响应 body: {json.dumps(sim_resp.json(), indent=2, ensure_ascii=False)}")
                except Exception:
                    print(f"[DEBUG] 响应 body: {sim_resp.text[:500]}")
                sleep(5)
                continue

            # 加入任务
            task_queue.put({
                'alpha_expression': alpha_expression,
                'sim_progress_url': sim_resp.headers['Location'],
                "saved_path": saved_path,
                "elite_path": elite_path
            })
            
            # 标记表达式队列任务完成
            alpha_expression_queue.task_done()
            
        except Exception as e:
            print(f"[错误] 提交 Alpha 表达式失败: {e}")
            traceback.print_exc()
            try:
                semaphore.release()  # 回测失败要释放信号量
            except :
                pass


# =================== 消费者进程 =====================
def get_result_thread(sess):
    print("[获取结果线程] 启动")
    while not stop_event.is_set():
        try:
            try:
                task = task_queue.get(timeout=1)
            except queue.Empty:
                continue
            print(f"[获取结果线程] 准备获取: {task['alpha_expression'][:50]}...")

            sim_progress_url = task['sim_progress_url']
            alpha_expression = task['alpha_expression']
            saved_path = task['saved_path']
            elite_path = task['elite_path']

            print(f"[结果线程] 开始处理: {alpha_expression[:50]}...")
            
            # ================== 轮询等待回测完成 ==================
            # 这部分代码从原simulate_alpha函数复制（第185-192行）
            while True:
                sim_progress_resp = sess.get(sim_progress_url)
                retry_after_sec = float(sim_progress_resp.headers.get("Retry-After", 0))
                if retry_after_sec == 0:
                    break
                print(f"\r[结果线程] 等待中... {retry_after_sec}秒", end='', flush=True)
                import time
                time.sleep(retry_after_sec)
            print()
            
            # ================== 处理结果 ==================
            # 这部分代码从原simulate_alpha函数复制（第194-252行）
            sim_result = sim_progress_resp.json()
            sim_status = sim_result.get("status", "UNKNOWN")
            
            if sim_status == "ERROR":
                print(f"[结果线程] 回测失败: status=ERROR")
                task_queue.task_done()
                semaphore.release()  # ================== V操作 ==================
                continue
            
            if "alpha" not in sim_result:
                print(f"[结果线程] 响应中没有alpha字段")
                task_queue.task_done()
                semaphore.release()  # ================== V操作 ==================
                continue
            
            alpha_id = sim_result["alpha"]
            print(f"[结果线程] Alpha ID: {alpha_id}")
            
            # 获取详细信息
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
                print(f"[结果线程] 验证成功 | Sharpe={sharpe} | Fitness={fitness}")
            
            # 保存结果
            from datetime import datetime
            ts = datetime.now(datetime.UTC).isoformat() if hasattr(datetime, 'UTC') else datetime.utcnow().isoformat() + 'Z'
            record = {
                'alpha_id': alpha_id,
                'expression': alpha_expression,
                'sharpe': sharpe,
                'fitness': fitness,
                'returns': returns_,
                'turnover': turnover,
                'timestamp': ts
            }
            
            saved_path.parent.mkdir(parents=True, exist_ok=True)
            with open(saved_path, 'a', encoding='utf-8') as fout:
                fout.write(json.dumps(record, ensure_ascii=False) + '\n')
            print(f"[结果线程] 已保存到 {saved_path}")
            
            # 保存精英alpha
            if sharpe is not None and fitness is not None and sharpe > 1.25 and fitness > 1:
                elite_path.parent.mkdir(parents=True, exist_ok=True)
                if not elite_path.exists():
                    with open(elite_path, 'w', encoding='utf-8') as fout:
                        fout.write(json.dumps({"submitted": 0}, ensure_ascii=False) + '\n')
                with open(elite_path, 'a', encoding='utf-8') as fout:
                    fout.write(json.dumps(record, ensure_ascii=False) + '\n')
                print(f"[结果线程] 精选保存到 {elite_path}")

            # ================== V操作 ==================
            # 释放资源：让下一个alpha可以提交
            semaphore.release()
            print(f"[结果线程] V操作成功，剩余槽位: {semaphore._value}")
            task_queue.task_done()

        except Exception as e:
            print(f"[结果线程] 异常: {e}")
            import traceback
            traceback.print_exc()
            # 确保发生异常时也释放信号量
            try:
                semaphore.release()
            except:
                pass
            try:
                task_queue.task_done()
            except:
                pass


if __name__ == "__main__":
    print("\n" + "="*60)
    print("WorldQuant Brain Alpha 批量回测工具")
    print("="*60)
    
    # 1. 输入 alpha 表达式文件路径
    print("\n请输入 Alpha 表达式文件路径 (JSON格式):")
    print("  示例: ../alpha_expressions/news12_MATRIX_alphas.json")
    input_file = input("文件路径: ").strip()
    if not input_file:
        print("[错误] 文件路径不能为空")
        exit()
    
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"[错误] 文件不存在: {input_path}")
        exit()
    
    # 2. 自动生成输出目录
    output_dir = input_path.parent.parent / 'alpha_result' / input_path.stem.replace('_alphas', '')
    
    # 3. 确认
    saved_path = output_dir / 'saved_alphas.jsonl'
    elite_path = output_dir / 'elite_alphas.jsonl'
    
    print("\n" + "-"*60)
    print("配置确认:")
    print(f"  输入文件: {input_path}")
    print(f"  输出目录: {output_dir}")
    print(f"  普通结果: {saved_path}")
    print(f"  精选结果: {elite_path}")
    print("-"*60)
    
    confirm = input("\n确认开始回测? (y/n) [默认: y]: ").strip().lower()
    if confirm and confirm != 'y':
        print("[取消] 用户取消操作")
        exit()
    
    # 4. 登录
    print("\n" + "="*60)
    print("正在登录...")
    print("="*60 + "\n")
    
    sess = get_session()
    
    # 5. 加载 alpha 表达式
    print("\n" + "="*60)
    print("开始加载 Alpha 表达式...")
    print("="*60)
    
    alphas = read_alphas(input_path)
    
    print(f"\n[汇总] 共加载 {len(alphas)} 个 Alpha 表达式")
    
    if len(alphas) == 0:
        print("[错误] 没有找到任何 Alpha 表达式，请检查文件路径")
        exit()
    
    # 6. 填充alpha表达式队列
    for alpha in alphas:
        alpha_expression_queue.put(alpha)
    
    # 7. 创建并启动线程
    print("\n" + "="*60)
    print("启动双线程回测系统...")
    print("="*60 + "\n")

    thread1 = threading.Thread(target=submit_alpha_thread, args=(sess, saved_path, elite_path), name='SubmitThread')
    thread2 = threading.Thread(target=get_result_thread, args=(sess,), name='ResultThread')

    thread1.start()
    thread2.start()

    try:
        # 8. 等待所有Alpha提交完成（可中断版本）
        print("\n[主线程] 等待所有Alpha提交...")
        while alpha_expression_queue.unfinished_tasks > 0 and not stop_event.is_set():
            sleep(0.5)
        
        if not stop_event.is_set():
            print("\n[主线程] 所有Alpha已提交完毕")

            # 9. 等待所有结果获取完成（可中断版本）
            print("[主线程] 等待所有结果处理...")
            while task_queue.unfinished_tasks > 0 and not stop_event.is_set():
                sleep(0.5)
            
            if not stop_event.is_set():
                print("[主线程] 所有结果已处理完毕")

    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("[用户中断] 收到 Ctrl+C，正在停止所有线程...")
        print("="*60 + "\n")
        
        # 设置停止标志，通知线程退出
        stop_event.set()
        
        # 释放所有信号量，避免死锁
        for _ in range(MAX_CONCURRENT):
            try:
                semaphore.release()
            except:
                pass
        
        # 等待线程结束（设置超时，避免永久等待）
        thread1.join(timeout=5)
        thread2.join(timeout=5)
        
        print("\n[主线程] 所有线程已停止，程序退出")
        exit(0)

    # 10. 正常停止线程
    stop_event.set()
    thread1.join()
    thread2.join()
    
    print("\n" + "="*60)
    print("所有回测任务完成！")
    print("="*60)
