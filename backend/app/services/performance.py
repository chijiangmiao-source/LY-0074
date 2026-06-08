from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bson import ObjectId

from app.models import (
    User,
    EmployeePosition,
    POSITION_LABELS,
    Store,
    Bucket,
    Flower,
    Warning,
    ResponsibilityTrace,
    ResponsibilityTargetType,
    ResponsibilityAction,
)
from app.services.stats_service import (
    build_date_query,
    resolve_date_range,
    get_user_store,
    get_user_store_id,
    get_operator_name,
    BatchRecordLoader,
    calculate_workload_from_records,
    calculate_timeliness_from_warnings,
    calculate_loss_stats_from_records,
    calculate_performance_score,
)


async def calculate_workload(
    user_id: Optional[str],
    date_query: Optional[Dict[str, Any]],
    store_id: Optional[str] = None,
) -> Dict[str, int]:
    if not user_id:
        return {
            "in_bucket_count": 0,
            "out_bucket_count": 0,
            "preservation_count": 0,
            "loss_count": 0,
            "warning_handled_count": 0,
            "inspection_count": 0,
            "total_operations": 0,
        }

    operator_name = await get_operator_name(user_id)
    loader = BatchRecordLoader(date_query, store_id)
    await loader.load_all()

    in_records = loader.get_in_records_for_user(user_id, operator_name)
    out_records = loader.get_out_records_for_user(user_id, operator_name)
    pres_records = loader.get_pres_records_for_user(user_id, operator_name)
    loss_records = loader.get_loss_records_for_user(user_id, operator_name)
    warnings = loader.get_warnings_for_user(user_id)
    status_records = loader.get_status_records_for_user(user_id)

    return calculate_workload_from_records(
        in_records, out_records, pres_records, loss_records, warnings, status_records
    )


async def calculate_timeliness(
    user_id: Optional[str],
    date_query: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if not user_id:
        return {
            "on_time_count": 0,
            "overdue_count": 0,
            "on_time_rate": 100.0,
            "avg_warning_handle_hours": 0.0,
        }

    loader = BatchRecordLoader(date_query)
    await loader.load_all()
    warnings = loader.get_warnings_for_user(user_id)
    return calculate_timeliness_from_warnings(warnings)


async def calculate_loss_stats(
    user_id: Optional[str],
    date_query: Optional[Dict[str, Any]],
    store_id: Optional[str] = None,
) -> Dict[str, Any]:
    if not user_id:
        return {
            "total_loss_quantity": 0,
            "responsible_loss_quantity": 0,
            "loss_rate": 0.0,
        }

    operator_name = await get_operator_name(user_id)
    loader = BatchRecordLoader(date_query, store_id)
    await loader.load_all()

    user_loss = loader.get_loss_records_for_user(user_id, operator_name)
    return calculate_loss_stats_from_records(user_loss, loader.loss_records)


async def _build_employee_performance_from_loader(
    user: User,
    loader: BatchRecordLoader,
    store_id: Optional[str] = None,
) -> Dict[str, Any]:
    user_id = str(user.id)
    operator_name = user.full_name or user.username

    in_records = loader.get_in_records_for_user(user_id, operator_name)
    out_records = loader.get_out_records_for_user(user_id, operator_name)
    pres_records = loader.get_pres_records_for_user(user_id, operator_name)
    loss_records = loader.get_loss_records_for_user(user_id, operator_name)
    warnings = loader.get_warnings_for_user(user_id)
    status_records = loader.get_status_records_for_user(user_id)

    workload = calculate_workload_from_records(
        in_records, out_records, pres_records, loss_records, warnings, status_records
    )
    timeliness = calculate_timeliness_from_warnings(warnings)
    loss_stats = calculate_loss_stats_from_records(loss_records, loader.loss_records)
    score = calculate_performance_score(workload, timeliness, loss_stats)

    user_store = store_id
    if not user_store:
        s = await get_user_store(user)
        if s:
            user_store = str(s.id)

    store_info = None
    if user_store:
        store = await Store.get(ObjectId(user_store))
        if store:
            store_info = {
                "id": str(store.id),
                "store_name": store.store_name,
                "store_code": store.store_code,
            }

    return {
        "user": {
            "id": str(user.id),
            "username": user.username,
            "full_name": user.full_name,
            "position": user.position.value if isinstance(user.position, EmployeePosition) else user.position,
            "position_label": POSITION_LABELS.get(user.position, "其他") if user.position else "其他",
        },
        "store": store_info,
        "workload": workload,
        "timeliness": timeliness,
        "loss": loss_stats,
        "score": score,
    }


async def get_employee_performance(
    user: User,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    store_id: Optional[str] = None,
) -> Dict[str, Any]:
    date_query = build_date_query(start_date, end_date)
    loader = BatchRecordLoader(date_query, store_id)
    await loader.load_all()
    return await _build_employee_performance_from_loader(user, loader, store_id)


async def get_performance_ranking(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    store_id: Optional[str] = None,
    position: Optional[str] = None,
    sort_by: str = "score",
) -> List[Dict[str, Any]]:
    query = {"is_active": True}
    if position:
        query["position"] = EmployeePosition(position)

    users = await User.find(query).to_list()

    date_query = build_date_query(start_date, end_date)
    loader = BatchRecordLoader(date_query, store_id)
    await loader.load_all()

    results = []
    for user in users:
        perf = await _build_employee_performance_from_loader(user, loader, store_id)
        if store_id and not perf["store"]:
            continue
        if store_id and perf["store"] and perf["store"]["id"] != store_id:
            continue
        results.append(perf)

    reverse = True
    key_func = lambda x: x.get("score", 0)
    if sort_by == "total_operations":
        key_func = lambda x: x["workload"]["total_operations"]
    elif sort_by == "on_time_rate":
        key_func = lambda x: x["timeliness"]["on_time_rate"]
    elif sort_by == "loss_rate":
        key_func = lambda x: x["loss"]["loss_rate"]
        reverse = False

    results.sort(key=key_func, reverse=reverse)

    for i, r in enumerate(results):
        r["rank"] = i + 1

    return results


ACTION_LABEL_MAP = {
    ResponsibilityAction.ASSIGN: "责任分配",
    ResponsibilityAction.IN_BUCKET: "入桶操作",
    ResponsibilityAction.OUT_BUCKET: "回桶操作",
    ResponsibilityAction.PRESERVATION: "补液操作",
    ResponsibilityAction.LOSS: "损耗处理",
    ResponsibilityAction.WARNING_HANDLE: "预警处置",
    ResponsibilityAction.INSPECTION: "巡检记录",
    ResponsibilityAction.TRANSFER: "责任转交",
    ResponsibilityAction.COMPLETE: "完成处理",
}

TARGET_TYPE_LABEL_MAP = {
    ResponsibilityTargetType.BUCKET: "花桶",
    ResponsibilityTargetType.FLOWER: "花材",
    ResponsibilityTargetType.WARNING: "预警",
    ResponsibilityTargetType.STORE: "门店",
}


def trace_to_response(trace: ResponsibilityTrace) -> Dict[str, Any]:
    data = trace.model_dump(by_alias=True)
    data["_id"] = str(trace.id)
    data["batch_no"] = trace.batch_no
    data["target_type_label"] = TARGET_TYPE_LABEL_MAP.get(trace.target_type, trace.target_type.value)
    data["action_label"] = ACTION_LABEL_MAP.get(trace.action, trace.action.value)
    data["operator_position_label"] = POSITION_LABELS.get(trace.operator_position, "") if trace.operator_position else ""

    if isinstance(trace.store, Store):
        data["store"] = {"id": str(trace.store.id), "store_name": trace.store.store_name, "store_code": trace.store.store_code}
    elif trace.store:
        data["store"] = {"id": str(trace.store), "store_name": "", "store_code": ""}
    else:
        data["store"] = None

    if isinstance(trace.bucket, Bucket):
        data["bucket"] = {"id": str(trace.bucket.id), "bucket_code": trace.bucket.bucket_code}
    elif trace.bucket:
        data["bucket"] = {"id": str(trace.bucket), "bucket_code": ""}
    else:
        data["bucket"] = None

    if isinstance(trace.flower, Flower):
        data["flower"] = {"id": str(trace.flower.id), "flower_name": trace.flower.flower_name, "flower_code": trace.flower.flower_code}
    elif trace.flower:
        data["flower"] = {"id": str(trace.flower), "flower_name": "", "flower_code": ""}
    else:
        data["flower"] = None

    if isinstance(trace.warning, Warning):
        data["warning"] = {
            "id": str(trace.warning.id),
            "warning_type": trace.warning.warning_type.value if hasattr(trace.warning.warning_type, 'value') else str(trace.warning.warning_type),
            "message": trace.warning.message,
        }
    elif trace.warning:
        data["warning"] = {"id": str(trace.warning), "warning_type": "", "message": ""}
    else:
        data["warning"] = None

    if isinstance(trace.operator, User):
        data["operator"] = {
            "id": str(trace.operator.id),
            "username": trace.operator.username,
            "full_name": trace.operator.full_name,
            "position": trace.operator.position.value if isinstance(trace.operator.position, EmployeePosition) else trace.operator.position,
            "position_label": POSITION_LABELS.get(trace.operator.position, ""),
        }
    elif trace.operator:
        data["operator"] = {"id": str(trace.operator), "username": "", "full_name": "", "position": "", "position_label": ""}
    else:
        data["operator"] = None

    return data


async def get_responsibility_trace(
    target_type: ResponsibilityTargetType,
    target_id: str,
) -> Dict[str, Any]:
    traces = await ResponsibilityTrace.find(
        ResponsibilityTrace.target_type == target_type,
        ResponsibilityTrace.target_id == target_id,
        fetch_links=True,
    ).sort("created_at").to_list()

    target_info = {}
    if target_type == ResponsibilityTargetType.BUCKET:
        bucket = await Bucket.get(ObjectId(target_id), fetch_links=True)
        if bucket:
            store_name = bucket.store.store_name if isinstance(bucket.store, Store) else ""
            target_info = {
                "id": str(bucket.id),
                "bucket_code": bucket.bucket_code,
                "capacity": bucket.capacity,
                "current_quantity": bucket.current_quantity,
                "status": bucket.status.value if hasattr(bucket.status, 'value') else str(bucket.status),
                "store_name": store_name,
                "responsible_person": bucket.responsible_person,
            }
    elif target_type == ResponsibilityTargetType.FLOWER:
        flower = await Flower.get(ObjectId(target_id), fetch_links=True)
        if flower:
            store_name = flower.store.store_name if isinstance(flower.store, Store) else ""
            bucket_code = flower.bucket.bucket_code if isinstance(flower.bucket, Bucket) else ""
            target_info = {
                "id": str(flower.id),
                "flower_code": flower.flower_code,
                "flower_name": flower.flower_name,
                "batch_no": flower.batch_no,
                "current_quantity": flower.current_quantity,
                "preservation_status": flower.preservation_status.value if hasattr(flower.preservation_status, 'value') else str(flower.preservation_status),
                "store_name": store_name,
                "bucket_code": bucket_code,
            }
    elif target_type == ResponsibilityTargetType.WARNING:
        warning = await Warning.get(ObjectId(target_id), fetch_links=True)
        if warning:
            store_name = warning.store.store_name if isinstance(warning.store, Store) else ""
            target_info = {
                "id": str(warning.id),
                "warning_type": warning.warning_type.value if hasattr(warning.warning_type, 'value') else str(warning.warning_type),
                "warning_type_label": warning.warning_type_label,
                "severity": warning.severity.value if hasattr(warning.severity, 'value') else str(warning.severity),
                "message": warning.message,
                "status": warning.status.value if hasattr(warning.status, 'value') else str(warning.status),
                "store_name": store_name,
            }

    return {
        "target_type": target_type.value,
        "target_type_label": TARGET_TYPE_LABEL_MAP.get(target_type, target_type.value),
        "target_id": target_id,
        "target_info": target_info,
        "traces": [trace_to_response(t) for t in traces],
        "total": len(traces),
    }


async def add_responsibility_trace(
    target_type: ResponsibilityTargetType,
    target_id: str,
    action: ResponsibilityAction,
    user: Optional[User] = None,
    operator_name: Optional[str] = None,
    remark: Optional[str] = None,
    store: Optional[Store] = None,
    bucket: Optional[Bucket] = None,
    flower=None,
    warning: Optional[Warning] = None,
    batch_no: Optional[str] = None,
) -> ResponsibilityTrace:
    trace = ResponsibilityTrace(
        target_type=target_type,
        target_id=target_id,
        batch_no=batch_no,
        store=store,
        bucket=bucket,
        flower=flower,
        warning=warning,
        action=action,
        action_label=ACTION_LABEL_MAP.get(action, action.value),
        operator=user,
        operator_name=operator_name or (user.full_name or user.username if user else None),
        operator_position=user.position if user else None,
        remark=remark,
    )
    await trace.create()
    return trace


async def get_responsibility_trace_by_batch(batch_no: str) -> Dict[str, Any]:
    if not batch_no:
        return {
            "batch_no": "",
            "target_type": "batch",
            "target_type_label": "批次",
            "target_id": "",
            "target_info": {},
            "traces": [],
            "total": 0,
        }

    traces = await ResponsibilityTrace.find(
        ResponsibilityTrace.batch_no == batch_no,
        fetch_links=True,
    ).sort("created_at").to_list()

    batch_flowers = await Flower.find(Flower.batch_no == batch_no).to_list()
    flower_infos = []
    for f in batch_flowers:
        flower_infos.append({
            "id": str(f.id),
            "flower_code": f.flower_code,
            "flower_name": f.flower_name,
            "current_quantity": f.current_quantity,
        })

    target_info = {
        "batch_no": batch_no,
        "flower_count": len(flower_infos),
        "flowers": flower_infos,
    }

    return {
        "batch_no": batch_no,
        "target_type": "batch",
        "target_type_label": "批次",
        "target_id": batch_no,
        "target_info": target_info,
        "traces": [trace_to_response(t) for t in traces],
        "total": len(traces),
    }


async def get_performance_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    store_id: Optional[str] = None,
) -> Dict[str, Any]:
    ps, pe = resolve_date_range(start_date, end_date)

    users = await User.find(User.is_active == True).to_list()

    date_query = build_date_query(start_date, end_date)
    loader = BatchRecordLoader(date_query, store_id)
    await loader.load_all()

    performances = []
    for u in users:
        p = await _build_employee_performance_from_loader(u, loader, store_id)
        if store_id and p["store"] and p["store"]["id"] != store_id:
            continue
        if store_id and not p["store"]:
            continue
        performances.append(p)

    total_ops = sum(p["workload"]["total_operations"] for p in performances)
    avg_on_time = round(sum(p["timeliness"]["on_time_rate"] for p in performances) / len(performances), 2) if performances else 0
    total_loss = sum(p["loss"]["responsible_loss_quantity"] for p in performances)

    return {
        "period_start": ps,
        "period_end": pe,
        "total_employees": len(performances),
        "total_operations": total_ops,
        "avg_on_time_rate": avg_on_time,
        "total_loss_quantity": total_loss,
    }
