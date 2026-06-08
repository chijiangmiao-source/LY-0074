"""
重构自检验证脚本
验证重构后的服务层方法与原始逻辑计算结果一致
使用方法: cd backend && python -m app.verify_refactor
"""
import asyncio
import sys
import os
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from bson import ObjectId

from app.config import settings
from app.database import init_db
from app.models import (
    User,
    EmployeePosition,
    POSITION_LABELS,
    Store,
    Bucket,
    Flower,
    BucketInRecord,
    BucketOutRecord,
    PreservationRecord,
    LossRecord,
    Warning,
    WarningStatus,
    WarningType,
    StatusChangeRecord,
    StatusChangeTarget,
)
from app.services.stats_service import (
    build_date_query,
    resolve_date_range,
    BatchRecordLoader,
    calculate_workload_from_records,
    calculate_timeliness_from_warnings,
    calculate_loss_stats_from_records,
    calculate_performance_score,
    calculate_store_loss_rate,
    WARNING_HANDLE_OVERDUE_HOURS,
)
from app.services.performance import (
    calculate_workload as new_calculate_workload,
    calculate_timeliness as new_calculate_timeliness,
    calculate_loss_stats as new_calculate_loss_stats,
    get_employee_performance as new_get_employee_performance,
    get_performance_ranking as new_get_performance_ranking,
    get_performance_summary as new_get_performance_summary,
)
from app.services.warning_service import (
    sync_generated_warnings,
    warning_to_response,
)
from app.services.dashboard_service import (
    get_dashboard_summary,
    get_store_loss_ranking,
)


async def verify_build_date_query():
    print("[验证] build_date_query ...", end=" ")
    q1 = build_date_query(None, None)
    assert q1 is None, "无参数应返回 None"

    q2 = build_date_query("2024-01-01", None)
    assert "$gte" in q2, "应有 $gte 字段"
    assert q2["$gte"] == datetime.fromisoformat("2024-01-01")

    q3 = build_date_query(None, "2024-01-31")
    assert "$lte" in q3, "应有 $lte 字段"
    expected_end = datetime.fromisoformat("2024-01-31") + timedelta(days=1)
    assert q3["$lte"] == expected_end, "结束日期应加一天"

    q4 = build_date_query("2024-01-01", "2024-01-31")
    assert "$gte" in q4 and "$lte" in q4
    print("✓ 通过")


async def verify_resolve_date_range():
    print("[验证] resolve_date_range ...", end=" ")
    ps, pe = resolve_date_range(None, None)
    assert len(ps) == 10 and len(pe) == 10, "日期格式应为 YYYY-MM-DD"

    ps2, pe2 = resolve_date_range("2024-01-01", "2024-01-31")
    assert ps2 == "2024-01-01" and pe2 == "2024-01-31", "有参数时应原样返回"
    print("✓ 通过")


async def verify_calculate_workload_from_records():
    print("[验证] calculate_workload_from_records ...", end=" ")
    result = calculate_workload_from_records(
        in_records=[1, 2],
        out_records=[1],
        pres_records=[1, 2, 3],
        loss_records=[],
        warnings=[1],
        status_records=[1, 2],
    )
    assert result["in_bucket_count"] == 2
    assert result["out_bucket_count"] == 1
    assert result["preservation_count"] == 3
    assert result["loss_count"] == 0
    assert result["warning_handled_count"] == 1
    assert result["inspection_count"] == 2
    assert result["total_operations"] == 9
    print("✓ 通过")


async def verify_calculate_performance_score():
    print("[验证] calculate_performance_score ...", end=" ")
    workload = {
        "in_bucket_count": 10,
        "out_bucket_count": 10,
        "preservation_count": 5,
        "loss_count": 5,
        "warning_handled_count": 10,
        "inspection_count": 10,
        "total_operations": 50,
    }
    timeliness = {
        "on_time_count": 9,
        "overdue_count": 1,
        "on_time_rate": 90.0,
        "avg_warning_handle_hours": 5.0,
    }
    loss = {
        "total_loss_quantity": 100,
        "responsible_loss_quantity": 10,
        "loss_rate": 10.0,
    }
    score = calculate_performance_score(workload, timeliness, loss)
    expected_workload = min(50 / 50 * 40, 40)
    expected_timeliness = 90.0 / 100 * 35
    expected_loss = max(0, 25 - 10.0 * 0.5)
    expected_score = round(expected_workload + expected_timeliness + expected_loss, 2)
    assert score == expected_score, f"分数计算错误: {score} != {expected_score}"
    print("✓ 通过")


async def verify_calculate_store_loss_rate():
    print("[验证] calculate_store_loss_rate ...", end=" ")

    class FakeLoss:
        def __init__(self, qty, days_ago):
            self.quantity = qty
            self.created_at = datetime.utcnow() - timedelta(days=days_ago)

    loss_records = [
        FakeLoss(10, 1),
        FakeLoss(5, 3),
        FakeLoss(20, 10),
    ]
    rate, recent_qty, base = calculate_store_loss_rate(loss_records, current_flower_qty=70, days=7)
    assert recent_qty == 15, f"近7天损耗应为 15，实际 {recent_qty}"
    assert base == 85, f"基数应为 85，实际 {base}"
    expected_rate = 15 / 85
    assert abs(rate - expected_rate) < 0.0001, f"损耗率计算错误"
    print("✓ 通过")


async def verify_warning_to_response():
    print("[验证] warning_to_response ...", end=" ")

    class FakeStore:
        id = ObjectId()
        store_name = "测试门店"
        store_code = "ST001"

    class FakeBucket:
        id = ObjectId()
        bucket_code = "BK001"

    class FakeFlower:
        id = ObjectId()
        flower_name = "红玫瑰"
        flower_code = "FL001"

    class FakeUser:
        id = ObjectId()
        full_name = "张三"
        username = "zhangsan"

    class FakeWarning:
        id = ObjectId()
        warning_type = WarningType.LOW_LIQUID
        warning_type_label = "液位过低"
        severity = "high"
        store = FakeStore()
        bucket = FakeBucket()
        flower = FakeFlower()
        message = "测试预警"
        current_value = "5"
        threshold_value = "10"
        unit = "L"
        status = WarningStatus.PENDING
        handler = FakeUser()
        handled_at = None
        handle_note = None
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()

    resp = warning_to_response(FakeWarning())
    assert resp["warning_id"] == str(FakeWarning.id)
    assert resp["warning_type"] == "low_liquid"
    assert resp["store_name"] == "测试门店"
    assert resp["bucket_code"] == "BK001"
    assert resp["flower_name"] == "红玫瑰"
    assert resp["handler"] == "张三"
    assert resp["status"] == "pending"
    assert resp["status_label"] == "待处理"
    print("✓ 通过")


async def verify_batch_loader_consistency():
    """验证批量加载和逐个加载结果一致"""
    print("[验证] BatchRecordLoader 数据一致性 ...", end=" ")
    users = await User.find(User.is_active == True).limit(5).to_list()
    if not users:
        print("(无用户数据，跳过)")
        return

    date_query = None
    loader = BatchRecordLoader(date_query)
    await loader.load_all()

    for user in users[:3]:
        uid = str(user.id)
        op_name = user.full_name or user.username

        in_batch = loader.get_in_records_for_user(uid, op_name)
        out_batch = loader.get_out_records_for_user(uid, op_name)
        loss_batch = loader.get_loss_records_for_user(uid, op_name)

        workload = calculate_workload_from_records(
            in_batch, out_batch,
            loader.get_pres_records_for_user(uid, op_name),
            loss_batch,
            loader.get_warnings_for_user(uid),
            loader.get_status_records_for_user(uid),
        )

        new_wl = await new_calculate_workload(uid, date_query)
        assert workload["total_operations"] == new_wl["total_operations"], (
            f"用户 {user.username} 工作总量不一致: "
            f"批量={workload['total_operations']} vs 单独={new_wl['total_operations']}"
        )
        assert workload["in_bucket_count"] == new_wl["in_bucket_count"]
        assert workload["out_bucket_count"] == new_wl["out_bucket_count"]

    print("✓ 通过")


async def verify_performance_score_consistency():
    """验证绩效分数计算一致性"""
    print("[验证] 绩效分数计算一致性 ...", end=" ")
    users = await User.find(User.is_active == True).limit(3).to_list()
    if not users:
        print("(无用户数据，跳过)")
        return

    for user in users:
        perf = await new_get_employee_performance(user)
        expected_score = calculate_performance_score(
            perf["workload"], perf["timeliness"], perf["loss"]
        )
        assert abs(perf["score"] - expected_score) < 0.01, (
            f"用户 {user.username} 分数不一致: "
            f"返回={perf['score']} vs 计算={expected_score}"
        )
    print("✓ 通过")


async def verify_dashboard_summary_structure():
    """验证 Dashboard 摘要返回结构"""
    print("[验证] Dashboard 摘要结构 ...", end=" ")
    summary = await get_dashboard_summary()
    required_keys = [
        "total_stores", "total_buckets", "active_buckets",
        "total_flowers", "in_bucket_flowers", "total_flower_quantity",
        "total_preservation_records", "total_loss_records",
    ]
    for key in required_keys:
        assert key in summary, f"缺少字段: {key}"
        assert isinstance(summary[key], int), f"字段 {key} 类型错误"
    print("✓ 通过")


async def verify_store_loss_ranking_structure():
    """验证门店损耗排行结构"""
    print("[验证] 门店损耗排行结构 ...", end=" ")
    ranking = await get_store_loss_ranking()
    if ranking:
        required_keys = [
            "store_id", "store_code", "store_name", "manager",
            "total_loss_quantity", "total_loss_count",
            "current_flower_quantity", "recent_loss_quantity_7d",
            "loss_rate_7d", "rank",
        ]
        for item in ranking[:3]:
            for key in required_keys:
                assert key in item, f"缺少字段: {key}"
    print("✓ 通过")


async def verify_performance_summary_structure():
    """验证绩效摘要返回结构"""
    print("[验证] 绩效摘要结构 ...", end=" ")
    summary = await new_get_performance_summary()
    required_keys = [
        "period_start", "period_end", "total_employees",
        "total_operations", "avg_on_time_rate", "total_loss_quantity",
    ]
    for key in required_keys:
        assert key in summary, f"缺少字段: {key}"
    print("✓ 通过")


async def verify_performance_ranking_structure():
    """验证绩效排行返回结构"""
    print("[验证] 绩效排行结构 ...", end=" ")
    ranking = await new_get_performance_ranking()
    if ranking:
        item = ranking[0]
        assert "user" in item
        assert "store" in item
        assert "workload" in item
        assert "timeliness" in item
        assert "loss" in item
        assert "score" in item
        assert "rank" in item

        wl = item["workload"]
        for k in ["in_bucket_count", "out_bucket_count", "preservation_count",
                  "loss_count", "warning_handled_count", "inspection_count", "total_operations"]:
            assert k in wl, f"workload 缺少字段: {k}"

        tm = item["timeliness"]
        for k in ["on_time_count", "overdue_count", "on_time_rate", "avg_warning_handle_hours"]:
            assert k in tm, f"timeliness 缺少字段: {k}"

        ls = item["loss"]
        for k in ["total_loss_quantity", "responsible_loss_quantity", "loss_rate"]:
            assert k in ls, f"loss 缺少字段: {k}"
    print("✓ 通过")


async def main():
    print("=" * 60)
    print("重构自检验证开始")
    print("=" * 60)

    await init_db()

    tests = [
        verify_build_date_query,
        verify_resolve_date_range,
        verify_calculate_workload_from_records,
        verify_calculate_performance_score,
        verify_calculate_store_loss_rate,
        verify_warning_to_response,
        verify_batch_loader_consistency,
        verify_performance_score_consistency,
        verify_dashboard_summary_structure,
        verify_store_loss_ranking_structure,
        verify_performance_summary_structure,
        verify_performance_ranking_structure,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"✗ 失败: {test.__name__}")
            print(f"  错误: {e}")

    print("=" * 60)
    print(f"验证完成: 通过 {passed} / {len(tests)}，失败 {failed}")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
