"""
test_submitAlpha.py — 本地测试脚本
用 mock 替代真实网络请求，验证 submitAlpha.py 的核心逻辑：
  1. get_alpha 能正确解析 JSONL 文件
  2. submit_alpha 不会超过设定的提交数量
  3. 切片逻辑正确（跳过头部 + 已提交的 Alpha）
  4. 写回文件后 submited 值正确更新
"""

import json
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

# ──────────────────────────────────────────────
# 为了能 import submitAlpha 中的纯函数，
# 需要先 mock 掉模块级别的凭据读取和全局变量
# ──────────────────────────────────────────────

# 在 submitAlpha 被 import 之前，先准备一个临时凭据文件
_temp_creds = tempfile.NamedTemporaryFile(
    mode='w', suffix='.json', delete=False, dir=os.path.dirname(__file__)
)
json.dump({"API_KEY": "test_key", "API_SECRET": "test_secret"}, _temp_creds)
_temp_creds.close()
_original_creds_name = 'brain_credentials.json'
_temp_creds_basename = os.path.basename(_temp_creds.name)

# Patch os.path.join 只在读取凭据时返回临时文件
_real_join = os.path.join
def _patched_join(*args):
    result = _real_join(*args)
    if result.endswith(_original_creds_name):
        return _temp_creds.name
    return result

with patch('os.path.join', side_effect=_patched_join):
    # 现在可以安全 import
    from submitAlpha import get_alpha, submit_alpha

# 清理临时凭据文件
os.unlink(_temp_creds.name)


# ──────────────────────────────────────────────
# 辅助函数：创建临时 JSONL 文件
# ──────────────────────────────────────────────
def create_temp_jsonl(objs):
    """将对象列表写入临时 .jsonl 文件，返回路径"""
    f = tempfile.NamedTemporaryFile(
        mode='w', suffix='.jsonl', delete=False, encoding='utf-8'
    )
    for obj in objs:
        f.write(json.dumps(obj) + '\n')
    f.close()
    return f.name


def make_mock_session(success_ids=None, fail_ids=None):
    """
    创建一个 mock session:
      - success_ids 中的 alpha_id 提交返回 200
      - fail_ids 中的 alpha_id 提交返回 400
      - 默认全部成功
    """
    success_ids = set(success_ids or [])
    fail_ids = set(fail_ids or [])

    sess = MagicMock()

    def mock_post(url, **kwargs):
        resp = MagicMock()
        resp.headers = {}  # 没有 Retry-After，不会轮询
        alpha_id = url.split('/alphas/')[1].split('/')[0] if '/alphas/' in url else ''
        if alpha_id in fail_ids:
            resp.status_code = 400
            resp.text = f"Mock failure for {alpha_id}"
        else:
            resp.status_code = 200
            resp.text = "OK"
        return resp

    sess.post = MagicMock(side_effect=mock_post)
    sess.get = MagicMock()  # 不应该被调用（没有 Retry-After）
    return sess


# ──────────────────────────────────────────────
# 测试用例
# ──────────────────────────────────────────────

def test_get_alpha_parses_jsonl():
    """测试 get_alpha 能正确解析 JSONL 文件"""
    data = [
        {"submited": 3},
        {"alpha_id": "A1", "expression": "expr1"},
        {"alpha_id": "A2", "expression": "expr2"},
        {"alpha_id": "A3", "expression": "expr3"},
        {"alpha_id": "A4", "expression": "expr4"},
    ]
    path = create_temp_jsonl(data)
    try:
        result = get_alpha(path)
        assert len(result) == 5, f"期望 5 个对象，得到 {len(result)}"
        assert result[0]["submited"] == 3
        assert result[1]["alpha_id"] == "A1"
        assert result[4]["alpha_id"] == "A4"
        print("[PASS] test_get_alpha_parses_jsonl")
    finally:
        os.unlink(path)


def test_submit_respects_count_limit():
    """测试 submit_alpha 不会超过设定的提交数量"""
    objs = [
        {"alpha_id": f"ALPHA_{i}", "expression": f"expr_{i}"}
        for i in range(10)
    ]
    sess = make_mock_session()

    for limit in [1, 3, 5, 10]:
        result = submit_alpha(sess, objs, count=limit)
        assert result == limit, f"limit={limit} 时期望提交 {limit}，实际 {result}"

    print("[PASS] test_submit_respects_count_limit")


def test_submit_count_exceeds_available():
    """测试 count 大于可用 Alpha 数量时不会崩溃"""
    objs = [
        {"alpha_id": "A1", "expression": "expr1"},
        {"alpha_id": "A2", "expression": "expr2"},
    ]
    sess = make_mock_session()

    result = submit_alpha(sess, objs, count=100)
    assert result == 2, f"只有 2 个 Alpha，期望提交 2，实际 {result}"
    print("[PASS] test_submit_count_exceeds_available")


def test_submit_with_failures():
    """测试部分提交失败时，成功计数正确"""
    objs = [
        {"alpha_id": "A1"},
        {"alpha_id": "A2"},
        {"alpha_id": "A3"},
        {"alpha_id": "A4"},
        {"alpha_id": "A5"},
    ]
    # A2 和 A4 会失败
    sess = make_mock_session(fail_ids={"A2", "A4"})

    result = submit_alpha(sess, objs, count=5)
    # A1 成功, A2 失败, A3 成功, A4 失败, A5 成功 → 3 个成功
    assert result == 3, f"期望 3 个成功，实际 {result}"
    print("[PASS] test_submit_with_failures")


def test_submit_stops_at_limit_even_with_failures():
    """测试即使有失败，达到 count 后也会停止"""
    objs = [
        {"alpha_id": "A1"},  # 成功 → success_count=1
        {"alpha_id": "A2"},  # 失败
        {"alpha_id": "A3"},  # 成功 → success_count=2
        {"alpha_id": "A4"},  # 成功 → success_count=3, 达到上限
        {"alpha_id": "A5"},  # 不应该被提交
    ]
    sess = make_mock_session(fail_ids={"A2"})

    result = submit_alpha(sess, objs, count=3)
    assert result == 3, f"期望 3 个成功，实际 {result}"

    # 验证 A5 没有被提交（post 调用次数应该是 4: A1, A2, A3, A4）
    post_calls = sess.post.call_args_list
    submitted_urls = [str(c) for c in post_calls]
    assert not any("A5" in url for url in submitted_urls), \
        "A5 不应该被提交，但发现了 A5 的请求"
    print("[PASS] test_submit_stops_at_limit_even_with_failures")


def test_slice_logic():
    """测试切片逻辑：objs[submited_count + 1:] 跳过头部和已提交的"""
    all_objs = [
        {"submited": 3},            # objs[0] 头部
        {"alpha_id": "A1"},         # objs[1] 已提交
        {"alpha_id": "A2"},         # objs[2] 已提交
        {"alpha_id": "A3"},         # objs[3] 已提交
        {"alpha_id": "A4"},         # objs[4] 未提交 ← 应从这里开始
        {"alpha_id": "A5"},         # objs[5] 未提交
    ]

    submited_count = all_objs[0].get("submited", 0)
    elite_alphas = all_objs[submited_count + 1:]

    assert len(elite_alphas) == 2, f"期望 2 个未提交 Alpha，得到 {len(elite_alphas)}"
    assert elite_alphas[0]["alpha_id"] == "A4"
    assert elite_alphas[1]["alpha_id"] == "A5"
    print("[PASS] test_slice_logic")


def test_writeback_updates_submited():
    """测试写回文件后 submited 值正确累加"""
    original_data = [
        {"submited": 3},
        {"alpha_id": "A1"},
        {"alpha_id": "A2"},
        {"alpha_id": "A3"},
        {"alpha_id": "A4"},
        {"alpha_id": "A5"},
    ]
    path = create_temp_jsonl(original_data)

    try:
        # 模拟主程序流程
        objs = get_alpha(path)
        submited_count = objs[0].get("submited", 0)
        elite_alphas = objs[submited_count + 1:]

        sess = make_mock_session()
        actual_submitted = submit_alpha(sess, elite_alphas, count=2)

        # 更新并写回
        objs[0]["submited"] += actual_submitted
        with open(path, 'w', encoding='utf-8') as f:
            for obj in objs:
                f.write(json.dumps(obj) + '\n')

        # 重新读取并验证
        objs_after = get_alpha(path)
        assert objs_after[0]["submited"] == 5, \
            f"期望 submited=5 (3+2)，实际 {objs_after[0]['submited']}"
        # 数据行数不变
        assert len(objs_after) == 6, f"期望 6 行，实际 {len(objs_after)}"
        print("[PASS] test_writeback_updates_submited")
    finally:
        os.unlink(path)


def test_empty_objs():
    """测试空列表不会崩溃"""
    sess = make_mock_session()
    result = submit_alpha(sess, [], count=5)
    assert result == 0, f"空列表期望返回 0，实际 {result}"
    print("[PASS] test_empty_objs")


def test_objs_missing_alpha_id():
    """测试缺少 alpha_id 的对象被跳过"""
    objs = [
        {"alpha_id": "A1"},
        {"expression": "no_id"},  # 没有 alpha_id
        {"alpha_id": "A3"},
    ]
    sess = make_mock_session()
    result = submit_alpha(sess, objs, count=5)
    assert result == 2, f"期望 2 个成功（跳过无 alpha_id 的），实际 {result}"
    print("[PASS] test_objs_missing_alpha_id")


def test_real_file_integration():
    """集成测试：使用实际的 elite_alphas.jsonl 文件验证切片和计数"""
    real_path = Path(__file__).resolve().parent.parent / 'alpha_result' / 'fund6_subindustry' / 'elite_alphas.jsonl'
    if not real_path.exists():
        print("[SKIP] test_real_file_integration — 文件不存在")
        return

    objs = get_alpha(str(real_path))
    assert len(objs) > 1, "文件应该至少有头部 + 1 个 Alpha"

    submited_count = objs[0].get("submited", 0)
    total_alphas = len(objs) - 1  # 减去头部
    elite_alphas = objs[submited_count + 1:]

    print(f"  文件总 Alpha 数: {total_alphas}")
    print(f"  已提交数 (submited): {submited_count}")
    print(f"  剩余可提交数: {len(elite_alphas)}")

    assert submited_count <= total_alphas, \
        f"submited ({submited_count}) 不应超过总 Alpha 数 ({total_alphas})"
    assert len(elite_alphas) == total_alphas - submited_count, \
        f"切片后数量不匹配: {len(elite_alphas)} != {total_alphas} - {submited_count}"

    # 模拟提交 count=3（不会真正发请求）
    sess = make_mock_session()
    result = submit_alpha(sess, elite_alphas, count=3)
    expected = min(3, len(elite_alphas))
    assert result == expected, f"期望提交 {expected}，实际 {result}"

    print("[PASS] test_real_file_integration")


# ──────────────────────────────────────────────
# 运行全部测试
# ──────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_get_alpha_parses_jsonl,
        test_submit_respects_count_limit,
        test_submit_count_exceeds_available,
        test_submit_with_failures,
        test_submit_stops_at_limit_even_with_failures,
        test_slice_logic,
        test_writeback_updates_submited,
        test_empty_objs,
        test_objs_missing_alpha_id,
        test_real_file_integration,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"结果: {passed} 通过, {failed} 失败, 共 {len(tests)} 个测试")
    if failed == 0:
        print("所有测试通过！可以放心运行正式提交。")
    else:
        print("有测试失败，请检查后再运行正式提交。")
        sys.exit(1)
