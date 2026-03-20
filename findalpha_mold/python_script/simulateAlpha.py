import queue
import pandas as pd
import requests
import json
import time
import os
import threading
import traceback
import logging

from pathlib import Path
from datetime import datetime
from requests.auth import HTTPBasicAuth
from time import sleep
from threading import Semaphore


class RefreshLineHandler(logging.StreamHandler):
    """自定义 Handler，在输出日志前清除刷新行"""
    
    def __init__(self, stream=None):
        super().__init__(stream)
        self._has_refresh_line = False
    
    def set_refresh_line_active(self, active):
        """设置是否有活跃的刷新行"""
        self._has_refresh_line = active
    
    def emit(self, record):
        """输出日志前先清除刷新行"""
        if self._has_refresh_line:
            # 清除刷新行
            self.stream.write('\r' + ' ' * 80 + '\r')
            self.stream.flush()
        super().emit(record)


_refresh_line_handler = None

def setup_logging():
    """配置日志系统"""
    global _refresh_line_handler
    
    log_dir = Path(__file__).parent.parent / 'alpha_log'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f'simulate_{datetime.now().strftime("%Y%m%d")}.log'
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    if logger.handlers:
        logger.handlers.clear()
    
    # 禁用 urllib3 和 requests 的 DEBUG 日志（占用大量空间）
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    # 文件日志处理器 - DEBUG 级别，记录所有信息
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_file, 
        encoding='utf-8',
        maxBytes=100*1024*1024,  # 100MB
        backupCount=10  # 保留 10 个备份
    )
    file_handler.setLevel(logging.DEBUG)
    
    # 控制台日志处理器 - DEBUG 级别，显示所有信息
    _refresh_line_handler = RefreshLineHandler()
    _refresh_line_handler.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        '%(asctime)s [%(threadName)s] %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    _refresh_line_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(_refresh_line_handler)
    
    return logger


def set_refresh_line_active(active):
    """设置刷新行状态"""
    global _refresh_line_handler
    if _refresh_line_handler:
        _refresh_line_handler.set_refresh_line_active(active)


def log_separator(title=None):
    """输出分隔线
    
    Args:
        title: 可选的标题文字
    """
    separator = "=" * 60
    if title:
        logger.info(separator)
        logger.info(title)
        logger.info(separator)
    else:
        logger.info(separator)


logger = setup_logging()


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
    if not API_KEY or not API_SECRET:
        raise ValueError("凭据文件缺少 API_KEY 或 API_SECRET")
except FileNotFoundError:
    raise FileNotFoundError(f"找不到凭据文件: {creds_path}. 请创建包含 [\"API_KEY\", \"API_SECRET\"] 的 JSON 文件，或直接在代码中设置 API_KEY/API_SECRET。")
except Exception:
    raise

BASE_URL = "https://api.worldquantbrain.com"
SESSION_TTL = 3.5 * 3600
REQUEST_TIMEOUT = 30
REQUEST_RETRIES = 3
REQUEST_RETRY_SLEEP = 3
RESULT_JSON_RETRIES = 3
RESULT_JSON_RETRY_SLEEP = 2
SUBMIT_TASK_REQUEUE_LIMIT = 2

# =================多线程配置=================
MAX_CONCURRENT = 2  # 同时回测的最大数量（你的账号限制）
semaphore = Semaphore(MAX_CONCURRENT)  # PV操作信号量

# 线程安全队列
task_queue = queue.Queue()  # 存储待查询的alpha任务
alpha_expression_queue = queue.Queue()  # 存储待提交的alpha表达式

# 线程状态标志
stop_event = threading.Event()  # 用于优雅停止线程

# 统计相关
input_json_path = None  # 输入的 JSON 文件路径
previous_simulated_count = 0  # 之前已回测的数量
current_success_count = 0  # 本次成功回测的数量
count_lock = threading.Lock()  # 计数器的线程锁
last_save_time = 0  # 上次保存进度的时间戳
SAVE_INTERVAL = 300  # 每 300 秒（5分钟）保存一次进度

# =================CSV保存配置=================
csv_lock = threading.Lock()  # CSV写入的线程锁


def init_csv_file(csv_path):
    """初始化CSV文件，如果不存在则创建并写入表头"""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not csv_path.exists():
        headers = [
            'alpha_id', 'expression', 'pnl', 'bookSize', 'longCount', 
            'shortCount', 'turnover', 'returns', 'drawdown', 'margin', 
            'sharpe', 'fitness', 'startDate',
            'check_LOW_SHARPE', 'check_LOW_FITNESS', 'check_LOW_TURNOVER',
            'check_HIGH_TURNOVER', 'check_CONCENTRATED_WEIGHT',
            'check_LOW_SUB_UNIVERSE_SHARPE', 'check_SELF_CORRELATION',
            'check_MATCHES_COMPETITION', 'saved_time'
        ]
        
        with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            import csv
            writer = csv.writer(f)
            writer.writerow(headers)
        logger.info(f"CSV文件已初始化: {csv_path}")


def save_to_csv(csv_path, alpha_id, alpha_expression, is_data, checks):
    """将Alpha信息保存到CSV文件（线程安全）"""
    from datetime import datetime
    
    # 提取检查结果
    check_results = {}
    check_names = [
        'LOW_SHARPE', 'LOW_FITNESS', 'LOW_TURNOVER', 'HIGH_TURNOVER',
        'CONCENTRATED_WEIGHT', 'LOW_SUB_UNIVERSE_SHARPE',
        'SELF_CORRELATION', 'MATCHES_COMPETITION'
    ]
    
    for check_name in check_names:
        check_results[f'check_{check_name}'] = 'UNKNOWN'
    
    for check in checks:
        name = check.get('name', '')
        if name in check_names:
            check_results[f'check_{name}'] = check.get('result', 'UNKNOWN')
    
    # 构建行数据
    row_data = [
        alpha_id,
        alpha_expression,
        is_data.get('pnl', ''),
        is_data.get('bookSize', ''),
        is_data.get('longCount', ''),
        is_data.get('shortCount', ''),
        is_data.get('turnover', ''),
        is_data.get('returns', ''),
        is_data.get('drawdown', ''),
        is_data.get('margin', ''),
        is_data.get('sharpe', ''),
        is_data.get('fitness', ''),
        is_data.get('startDate', ''),
        check_results['check_LOW_SHARPE'],
        check_results['check_LOW_FITNESS'],
        check_results['check_LOW_TURNOVER'],
        check_results['check_HIGH_TURNOVER'],
        check_results['check_CONCENTRATED_WEIGHT'],
        check_results['check_LOW_SUB_UNIVERSE_SHARPE'],
        check_results['check_SELF_CORRELATION'],
        check_results['check_MATCHES_COMPETITION'],
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ]
    
    # 线程安全写入
    with csv_lock:
        import csv
        with open(csv_path, 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row_data)


# =================核心函数=================

class BrainSession:
    """自动续期的会话包装器，每隔 ~3.5 小时自动重新认证（会话有效期 4 小时）"""

    def __init__(self):
        self._session = requests.Session()
        self._session.auth = HTTPBasicAuth(str(API_KEY), str(API_SECRET))
        self._last_auth_time = 0
        self._authenticate()

    def _authenticate(self):
        last_error = None
        for attempt in range(1, REQUEST_RETRIES + 1):
            try:
                response = self._session.post(f"{BASE_URL}/authentication", timeout=REQUEST_TIMEOUT)
                if response.status_code in (200, 201):
                    self._last_auth_time = time.time()
                    logger.info(f"登录成功， {response.text}")
                    return
                logger.error(f"登录失败: {response.status_code} - {response.text}")
                last_error = RuntimeError(f"auth status {response.status_code}")
            except requests.exceptions.RequestException as exc:
                last_error = exc
                logger.warning(f"登录请求异常，第 {attempt}/{REQUEST_RETRIES} 次: {exc}")

            if attempt < REQUEST_RETRIES:
                wait_time = min(REQUEST_RETRY_SLEEP * attempt, 10)
                sleep(wait_time)

        logger.error(f"登录重试后仍失败: {last_error}")
        exit()

    def _ensure_valid(self):
        elapsed = time.time() - self._last_auth_time
        if elapsed >= SESSION_TTL:
            logger.info(f"会话已持续 {elapsed/3600:.1f} 小时，正在重新认证...")
            self._authenticate()

    def _request_with_retry(self, method_name, *args, **kwargs):
        self._ensure_valid()
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)

        request_method = getattr(self._session, method_name)
        for attempt in range(1, REQUEST_RETRIES + 1):
            try:
                return request_method(*args, **kwargs)
            except requests.exceptions.RequestException as exc:
                if attempt >= REQUEST_RETRIES:
                    raise
                wait_time = min(REQUEST_RETRY_SLEEP * attempt, 10)
                logger.warning(
                    f"{method_name.upper()} 请求异常，第 {attempt}/{REQUEST_RETRIES} 次重试，"
                    f"{wait_time}s 后重试: {exc}"
                )
                sleep(wait_time)

    def get(self, *args, **kwargs):
        return self._request_with_retry('get', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._request_with_retry('post', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._request_with_retry('put', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._request_with_retry('delete', *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self._request_with_retry('patch', *args, **kwargs)

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
    从 JSON 文件读取 alpha 表达式，跳过已回测的
    
    Args:
        file_path: JSON 文件路径，格式为 [{"simulated numbers": N}, {"expression": "..."}, ...]
    
    Returns:
        list: alpha 表达式列表
    """
    global input_json_path, previous_simulated_count
    input_json_path = file_path
    
    alpha_list = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list) and len(data) > 0:
            # 检查第一个元素是否是统计信息
            first_item = data[0]
            if isinstance(first_item, dict) and 'simulated numbers' in first_item:
                previous_simulated_count = first_item.get('simulated numbers', 0)
                logger.info(f"读取到历史回测数量: {previous_simulated_count}")
                # 从第二个元素开始读取表达式
                data = data[1:]
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and 'expression' in item:
                    alpha_list.append(item['expression'])
                elif isinstance(item, str):
                    alpha_list.append(item)
        elif isinstance(data, dict) and 'expressions' in data:
            alpha_list = data['expressions']
        
        # 跳过已回测的 alpha
        if previous_simulated_count > 0 and previous_simulated_count < len(alpha_list):
            logger.info(f"跳过前 {previous_simulated_count} 个已回测的 Alpha 表达式")
            alpha_list = alpha_list[previous_simulated_count:]
        elif previous_simulated_count >= len(alpha_list) and len(alpha_list) > 0:
            logger.warning(f"所有 {len(alpha_list)} 个 Alpha 表达式都已回测完成")
            alpha_list = []
        
        logger.info(f"从 {file_path} 读取了 {len(alpha_list)} 个 Alpha 表达式（已跳过已回测的）")
    except FileNotFoundError:
        logger.warning(f"文件不存在: {file_path}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}")
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
    return alpha_list


def update_simulated_count():
    """更新并写回统计信息到 JSON 文件"""
    global input_json_path, previous_simulated_count, current_success_count
    
    if not input_json_path:
        logger.warning("没有记录输入文件路径，无法更新统计信息")
        return
    
    try:
        # 读取现有数据
        with open(input_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_count = previous_simulated_count + current_success_count
        
        # 构建新的数据
        new_data = []
        # 添加统计信息
        new_data.append({"simulated numbers": total_count})
        
        if isinstance(data, list) and len(data) > 0:
            # 如果第一个元素是统计信息，跳过它
            first_item = data[0]
            if isinstance(first_item, dict) and 'simulated numbers' in first_item:
                data = data[1:]
            # 添加表达式
            new_data.extend(data)
        
        # 写回文件
        with open(input_json_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"统计信息已更新！历史: {previous_simulated_count}, 本次: {current_success_count}, 总计: {total_count}")
        
    except Exception as e:
        logger.error(f"更新统计信息失败: {e}")
        logger.error(traceback.format_exc())


def increment_success_count():
    """增加成功回测计数器（线程安全），定期保存进度"""
    global current_success_count, last_save_time
    with count_lock:
        current_success_count += 1
        
        # 检查是否需要定期保存进度
        current_time = time.time()
        if current_time - last_save_time >= SAVE_INTERVAL:
            last_save_time = current_time
            logger.debug(f"定期保存进度... 本次成功: {current_success_count}")
            update_simulated_count()


def parse_json_with_retry(response, context, refresh_func=None):
    """解析响应 JSON，失败时短暂重试，必要时刷新响应后再试"""
    for attempt in range(1, RESULT_JSON_RETRIES + 1):
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError as exc:
            if attempt >= RESULT_JSON_RETRIES:
                logger.error(f"{context} JSON 解析失败，已达重试上限: {exc}")
                logger.debug(f"{context} 响应文本预览: {response.text[:300]!r}")
                raise
            wait_time = RESULT_JSON_RETRY_SLEEP * attempt
            logger.warning(
                f"{context} JSON 解析失败，第 {attempt}/{RESULT_JSON_RETRIES} 次重试，"
                f"{wait_time}s 后重试"
            )
            sleep(wait_time)
            if refresh_func is not None:
                response = refresh_func()

# =================== 生产者进程 =====================
def submit_alpha_thread(sess, saved_path, elite_path):
    logger.info("启动")
    while not stop_event.is_set():
        acquired = False
        queue_item_done = False
        idx = None
        alpha_expression = None
        submit_attempt = 0
        try:
            try:
                item = alpha_expression_queue.get(timeout=1)
                if isinstance(item, tuple) and len(item) == 3:
                    idx, alpha_expression, submit_attempt = item
                else:
                    idx, alpha_expression = item
                    submit_attempt = 0
            except queue.Empty:
                continue
            
            # 检查是否需要停止
            if stop_event.is_set():
                alpha_expression_queue.task_done()
                break
            
            logger.debug(f"准备提交 [序号 {idx}]: {alpha_expression}")

            # ============ P操作 ================
            # 申请资源：如果当前已有3个在运行，这里会等待
            # 不带超时，因为我们需要等待槽位释放，不跳过任何 Alpha
            # 但会定期检查 stop_event，确保可以响应停止信号
            while not stop_event.is_set():
                try:
                    acquired = semaphore.acquire(timeout=1)
                    if acquired:
                        break
                except:
                    pass
            
            if stop_event.is_set():
                alpha_expression_queue.task_done()
                break
                
            logger.debug(f"P操作成功 [序号 {idx}]，剩余槽位: {semaphore._value}")

            # 再次检查停止标志
            if stop_event.is_set():
                semaphore.release()
                alpha_expression_queue.task_done()
                break

            logger.debug("正在将如下Alpha表达式与setting封装")
            logger.debug(alpha_expression)
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

            # 检查停止标志
            if stop_event.is_set():
                semaphore.release()
                alpha_expression_queue.task_done()
                break

            sim_resp = sess.post(
                'https://api.worldquantbrain.com/simulations',
                json=simulation_data,
            )

            logger.debug(f"POST /simulations 状态码: {sim_resp.status_code}")
            if sim_resp.status_code not in (200, 201):
                logger.error(f"回测请求失败！响应内容:{sim_resp.text[:500]}")
                semaphore.release()  # 回测失败要释放信号量
                acquired = False
                alpha_expression_queue.task_done()  # 标记任务完成
                queue_item_done = True
                if submit_attempt < SUBMIT_TASK_REQUEUE_LIMIT:
                    retry_attempt = submit_attempt + 1
                    logger.warning(
                        f"提交失败 [序号 {idx}]，将重入队列重试 ({retry_attempt}/{SUBMIT_TASK_REQUEUE_LIMIT})"
                    )
                    alpha_expression_queue.put((idx, alpha_expression, retry_attempt))
                continue

            if 'Location' not in sim_resp.headers:
                logger.error("响应中没有 Location header!")
                logger.debug(f"响应 headers: {dict(sim_resp.headers)}")
                semaphore.release()  # 回测失败要释放信号量
                acquired = False
                alpha_expression_queue.task_done()  # 标记任务完成
                queue_item_done = True
                try:
                    logger.debug(
                        f"响应 body: {json.dumps(parse_json_with_retry(sim_resp, '提交回测响应'), indent=2, ensure_ascii=False)}"
                    )
                except Exception:
                    logger.debug(f"响应 body: {sim_resp.text[:500]}")
                if submit_attempt < SUBMIT_TASK_REQUEUE_LIMIT:
                    retry_attempt = submit_attempt + 1
                    logger.warning(
                        f"缺少 Location [序号 {idx}]，将重入队列重试 ({retry_attempt}/{SUBMIT_TASK_REQUEUE_LIMIT})"
                    )
                    alpha_expression_queue.put((idx, alpha_expression, retry_attempt))
                sleep(5)
                continue

            # 检查停止标志
            if stop_event.is_set():
                semaphore.release()
                alpha_expression_queue.task_done()
                break

            # 加入任务
            task_queue.put({
                'idx': idx,
                'alpha_expression': alpha_expression,
                'sim_progress_url': sim_resp.headers['Location'],
                "saved_path": saved_path,
                "elite_path": elite_path
            })
            
            # 标记表达式队列任务完成
            alpha_expression_queue.task_done()
            queue_item_done = True
            
        except Exception as e:
            if stop_event.is_set():
                break
            logger.error(f"提交 Alpha 表达式失败: {e}")
            logger.error(traceback.format_exc())
            if acquired:
                try:
                    semaphore.release()  # 回测失败要释放信号量
                    acquired = False
                except Exception:
                    pass
            if idx is not None and alpha_expression is not None and submit_attempt < SUBMIT_TASK_REQUEUE_LIMIT:
                retry_attempt = submit_attempt + 1
                logger.warning(
                    f"提交异常 [序号 {idx}]，将重入队列重试 ({retry_attempt}/{SUBMIT_TASK_REQUEUE_LIMIT})"
                )
                alpha_expression_queue.put((idx, alpha_expression, retry_attempt))
            if not queue_item_done:
                try:
                    alpha_expression_queue.task_done()
                except Exception:
                    pass


# =================== 消费者进程 =====================
def get_result_thread(sess):
    logger.info("启动")
    while not stop_event.is_set():
        try:
            try:
                task = task_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            # 检查是否需要停止
            if stop_event.is_set():
                task_queue.task_done()
                break
            
            idx = task['idx']
            logger.debug(f"准备获取 [序号 {idx}]: {task['alpha_expression']}")

            sim_progress_url = task['sim_progress_url']
            alpha_expression = task['alpha_expression']
            saved_path = task['saved_path']
            elite_path = task['elite_path']

            logger.debug(f"开始处理 [序号 {idx}]: {alpha_expression}")
            
            # ================== 轮询等待回测完成 ==================
            # 这部分代码从原simulate_alpha函数复制（第185-192行）
            total_wait_sec = 0.0
            import sys
            from datetime import datetime
            MAX_WAIT_SEC = 1800  # 最大等待 30 分钟，超时则跳过
            timed_out = False  # 标记是否超时
            sim_progress_resp = None
            
            while True:
                # 检查停止标志
                if stop_event.is_set():
                    set_refresh_line_active(False)
                    task_queue.task_done()
                    try:
                        semaphore.release()
                    except:
                        pass
                    break
                
                sim_progress_resp = sess.get(sim_progress_url)
                retry_after_sec = float(sim_progress_resp.headers.get("Retry-After", 0))
                if retry_after_sec == 0:
                    set_refresh_line_active(False)
                    break
                
                total_wait_sec += retry_after_sec
                
                # 检查是否超时
                if total_wait_sec > MAX_WAIT_SEC:
                    logger.error(f"回测超时 [序号 {idx}]！已等待 {total_wait_sec:.1f} 秒，超过最大 {MAX_WAIT_SEC} 秒，跳过此 Alpha")
                    set_refresh_line_active(False)
                    task_queue.task_done()
                    try:
                        semaphore.release()
                    except:
                        pass
                    timed_out = True
                    break
                
                # 标记有活跃的刷新行
                set_refresh_line_active(True)
                
                # 分段 sleep，每 1 秒检查一次停止标志，并刷新控制台
                sleep_interval = 1
                remaining = retry_after_sec
                while remaining > 0 and not stop_event.is_set():
                    # 控制台同一行刷新（模拟 logging 格式）
                    elapsed = total_wait_sec - remaining
                    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f'\r{now_str} [ResultThread] INFO - 等待中... 累计 {elapsed:.1f}秒 / {total_wait_sec:.1f}秒', end='', flush=True)
                    
                    time.sleep(min(sleep_interval, remaining))
                    remaining -= sleep_interval
                
                # 检查是否因为停止而退出
                if stop_event.is_set():
                    set_refresh_line_active(False)
                    task_queue.task_done()
                    try:
                        semaphore.release()
                    except:
                        pass
                    break
            
            # 清除刷新行状态
            set_refresh_line_active(False)
            
            # 记录最终累计等待时间到日志
            if total_wait_sec > 0:
                logger.info(f"等待完成 [序号 {idx}]，累计等待 {total_wait_sec:.1f}秒")
            
            # ================== 处理结果 ==================
            # 这部分代码从原simulate_alpha函数复制（第194-252行）
            
            # 如果因为停止标志退出，结束线程
            if stop_event.is_set():
                break

            # 单个任务超时时仅跳过该任务，不退出结果线程
            if timed_out:
                logger.warning(f"跳过超时任务 [序号 {idx}]，继续处理后续任务")
                continue

            if sim_progress_resp is None:
                logger.error(f"回测进度响应为空 [序号 {idx}]，跳过该任务")
                task_queue.task_done()
                semaphore.release()
                continue
            
            sim_result = parse_json_with_retry(
                sim_progress_resp,
                f"回测进度结果 [序号 {idx}]",
                refresh_func=lambda: sess.get(sim_progress_url),
            )
            if not isinstance(sim_result, dict):
                logger.error(f"回测结果格式异常 [序号 {idx}]，类型: {type(sim_result)}")
                task_queue.task_done()
                semaphore.release()
                continue
            sim_status = sim_result.get("status", "UNKNOWN")
            
            # 再次检查停止标志
            if stop_event.is_set():
                task_queue.task_done()
                try:
                    semaphore.release()
                except:
                    pass
                break
            
            if sim_status == "ERROR":
                logger.error("回测失败: status=ERROR")
                task_queue.task_done()
                semaphore.release()  # ================== V操作 ==================
                continue
            
            alpha_id = sim_result.get("alpha")
            if not alpha_id:
                logger.error("响应中没有alpha字段")
                task_queue.task_done()
                semaphore.release()  # ================== V操作 ==================
                continue

            logger.info(f"Alpha ID: {alpha_id}")
            
            # 再次检查停止标志
            if stop_event.is_set():
                task_queue.task_done()
                semaphore.release()
                break
            
            # 获取详细信息
            sharpe = None
            fitness = None
            returns_ = None
            turnover = None
            is_data = {}
            logger.debug(f"开始获取 Alpha 详情 [序号 {idx}]，alpha_id={alpha_id}")
            verify_resp = sess.get(f"{BASE_URL}/alphas/{alpha_id}")
            if verify_resp.status_code == 200:
                alpha_detail = parse_json_with_retry(
                    verify_resp,
                    f"Alpha详情 [序号 {idx}]",
                    refresh_func=lambda: sess.get(f"{BASE_URL}/alphas/{alpha_id}"),
                )
                if isinstance(alpha_detail, dict):
                    is_data = alpha_detail.get("is", {})
                    if not isinstance(is_data, dict):
                        is_data = {}
                else:
                    is_data = {}
                sharpe = is_data.get("sharpe")
                fitness = is_data.get("fitness")
                returns_ = is_data.get("returns")
                turnover = is_data.get("turnover")
                logger.info(f"验证成功 | Sharpe={sharpe} | Fitness={fitness}")
            else:
                logger.warning(
                    f"获取 Alpha 详情失败 [序号 {idx}]，状态码 {verify_resp.status_code}，"
                    f"将按基础记录保存"
                )
            
            # 再次检查停止标志
            if stop_event.is_set():
                task_queue.task_done()
                semaphore.release()
                break
            
            # 保存结果
            from datetime import datetime, timezone
            ts = datetime.now(timezone.utc).isoformat()
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
            logger.info(f"已保存到 {saved_path}")
            
            # 保存到CSV
            csv_path = Path(saved_path).parent / 'alphas_detailed.csv'
            checks = is_data.get('checks', [])
            save_to_csv(csv_path, alpha_id, alpha_expression, is_data, checks)
            logger.info(f"已保存到CSV: {csv_path}")
            
            # 保存精英alpha
            if sharpe is not None and fitness is not None and sharpe > 1.25 and fitness > 1:
                elite_path.parent.mkdir(parents=True, exist_ok=True)
                if not elite_path.exists():
                    with open(elite_path, 'w', encoding='utf-8') as fout:
                        fout.write(json.dumps({"submitted": 0}, ensure_ascii=False) + '\n')
                with open(elite_path, 'a', encoding='utf-8') as fout:
                    fout.write(json.dumps(record, ensure_ascii=False) + '\n')
                logger.info(f"精选保存到 {elite_path}")
            
            # 增加成功回测计数
            increment_success_count()

            # ================== V操作 ==================
            # 释放资源：让下一个alpha可以提交
            semaphore.release()
            logger.debug(f"V操作成功，剩余槽位: {semaphore._value}")
            task_queue.task_done()

        except Exception as e:
            set_refresh_line_active(False)
            if stop_event.is_set():
                break
            logger.error(f"异常: {e}")
            logger.error(traceback.format_exc())
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
    log_separator("WorldQuant Brain Alpha 批量回测工具")
    
    # 1. 输入 alpha 表达式文件路径
    print("\n请输入 Alpha 表达式文件路径 (JSON格式):")
    print("  示例: ../alpha_expressions/news12_MATRIX_alphas.json")
    input_file = input("文件路径: ").strip()
    if not input_file:
        logger.error("文件路径不能为空")
        exit()
    
    input_path = Path(input_file)
    if not input_path.exists():
        logger.error(f"文件不存在: {input_path}")
        exit()
    
    # 2. 自动生成输出目录
    output_dir = input_path.parent.parent / 'alpha_result' / input_path.stem.replace('_alphas', '')
    
    # 3. 初始化CSV文件
    csv_path = output_dir / 'alphas_detailed.csv'
    init_csv_file(csv_path)
    
    # 4. 确认
    saved_path = output_dir / 'saved_alphas.jsonl'
    elite_path = output_dir / 'elite_alphas.jsonl'
    
    print("\n" + "-"*60)
    print("配置确认:")
    print(f"  输入文件: {input_path}")
    print(f"  输出目录: {output_dir}")
    print(f"  普通结果: {saved_path}")
    print(f"  详细CSV: {csv_path}")
    print(f"  精选结果: {elite_path}")
    print("-"*60)
    
    confirm = input("\n确认开始回测? (y/n) [默认: y]: ").strip().lower()
    if confirm and confirm != 'y':
        logger.info("用户取消操作")
        exit()
    
    # 4. 登录
    log_separator("正在登录...")
    
    sess = get_session()
    
    # 5. 加载 alpha 表达式
    log_separator("开始加载 Alpha 表达式...")
    
    alphas = read_alphas(input_path)
    
    logger.info(f"共加载 {len(alphas)} 个 Alpha 表达式")
    
    # 初始化上次保存时间
    last_save_time = time.time()
    
    if len(alphas) == 0:
        logger.error("没有找到任何 Alpha 表达式，请检查文件路径")
        exit()
    
    # 6. 填充alpha表达式队列（包含原始序号）
    for idx, alpha in enumerate(alphas):
        alpha_expression_queue.put((idx, alpha))
    
    # 7. 创建并启动线程
    log_separator("启动双线程回测系统...")

    thread1 = threading.Thread(target=submit_alpha_thread, args=(sess, saved_path, elite_path), name='SubmitThread')
    thread2 = threading.Thread(target=get_result_thread, args=(sess,), name='ResultThread')

    thread1.start()
    thread2.start()

    try:
        # 8. 等待所有Alpha提交完成（可中断版本）
        logger.info("等待所有Alpha提交...")
        while alpha_expression_queue.unfinished_tasks > 0 and not stop_event.is_set():
            sleep(0.5)
        
        if not stop_event.is_set():
            logger.info("所有Alpha已提交完毕")

            # 9. 等待所有结果获取完成（可中断版本）
            logger.info("等待所有结果处理...")
            while task_queue.unfinished_tasks > 0 and not stop_event.is_set():
                sleep(0.5)
            
            if not stop_event.is_set():
                logger.info("所有结果已处理完毕")

    except KeyboardInterrupt:
        log_separator("收到 Ctrl+C，正在停止所有线程...")
        
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
        
        # 更新统计信息
        update_simulated_count()
        
        logger.info("所有线程已停止，程序退出")
        exit(0)

    # 10. 正常停止线程
    stop_event.set()
    thread1.join()
    thread2.join()
    
    # 更新统计信息
    update_simulated_count()
    
    log_separator("所有回测任务完成！")
