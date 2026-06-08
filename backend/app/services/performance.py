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
    BucketInRecord,
    BucketOutRecord,
    PreservationRecord,
    LossRecord,
    Warning,
    WarningStatus,
    ResponsibilityTrace,
    ResponsibilityTargetType,
    ResponsibilityAction,
    StatusChangeRecord,
    StatusChangeTarget,
)


WARNING_HANDLE_OVERDUE_HOURS = 24


def build_date_query(start_date: Optional[str], end_date: Optional[str]) -> Dict[str, Any]:
    date_query = {}
    if start_date:
        date_query["$gte"] = datetime.fromisoformat(start_date)
    if end_date:
        date_query["$lte"] = datetime.fromisoformat(end_date) + timedelta(days=1)
    return date_query if date_query else None


async def get_user_store(user: User) -> Optional[Store]:
    traces = await ResponsibilityTrace.find(
        ResponsibilityTrace.operator.id == user.id,
        fetch_links=True,
    ).sort("-created_at").limit(5).to_list()
    for t in traces:
        if isinstance(t.store, Store):
            return t.store
    return None


async def calculate_workload(
    operator_name: str,
    user_id: Optional[str],
    date_query: Optional[Dict[str, Any]],
    store_id: Optional[str] = None,
) -> Dict[str, int]:
    in_query = {}
    out_query = {}
    pres_query = {}
    loss_query = {}

    if date_query:
        in_query["created_at"] = date_query
        out_query["created_at"] = date_query
        pres_query["created_at"] = date_query
        loss_query["created_at"] = date_query

    in_query["operator"] = operator_name
    out_query["operator"] = operator_name
    pres_query["operator"] = operator_name
    loss_query["operator"] = operator_name

    if store_id:
        pres_query["store"] = ObjectId(store_id)
        loss_query["store"] = ObjectId(store_id)

    in_count = await BucketInRecord.find(in_query).count()
    out_count = await BucketOutRecord.find(out_query).count()
    pres_count = await PreservationRecord.find(pres_query).count()
    loss_count = await LossRecord.find(loss_query).count()

    warning_query = {}
    if date_query:
        warning_query["handled_at"] = date_query
    if user_id:
        warning_query["handler"] = ObjectId(user_id)
    warning_count = await Warning.find(warning_query).count()

    inspection_count = 0
    if user_id:
        status_query = {}
        status_query["operator"] = ObjectId(user_id)
        if date_query:
            status_query["created_at"] = date_query
        status_query["target_type"] = {
            "$in": [StatusChangeTarget.BUCKET_STATUS, StatusChangeTarget.FLOWER_PRESERVATION]
        }
        inspection_count = await StatusChangeRecord.find(status_query).count()

    total = in_count + out_count + pres_count + loss_count + warning_count + inspection_count

    return {
        "in_bucket_count": in_count,
        "out_bucket_count": out_count,
        "preservation_count": pres_count,
        "loss_count": loss_count,
        "warning_handled_count": warning_count,
        "inspection_count": inspection_count,
        "total_operations": total,
    }


async def calculate_timeliness(
    user_id: Optional[str],
    date_query: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    on_time = 0
    overdue = 0
    handle_hours_list: List[float] = []

    warning_query = {}
    if user_id:
        warning_query["handler"] = ObjectId(user_id)
    if date_query and "handled_at" in date_query:
        warning_query["handled_at"] = date_query["handled_at"]
    warnings = await Warning.find(warning_query, fetch_links=True).to_list()

    for w in warnings:
        if w.handled_at and w.created_at:
            hours = (w.handled_at - w.created_at).total_seconds() / 3600
            handle_hours_list.append(hours)
            if hours <= WARNING_HANDLE_OVERDUE_HOURS:
                on_time += 1
            else:
                overdue += 1

    total = on_time + overdue
    on_time_rate = round(on_time / total * 100, 2) if total > 0 else 100.0
    avg_hours = round(sum(handle_hours_list) / len(handle_hours_list), 2) if handle_hours_list else 0.0

    return {
        "on_time_count": on_time,
        "overdue_count": overdue,
        "on_time_rate": on_time_rate,
        "avg_warning_handle_hours": avg_hours,
    }


async def calculate_loss_stats(
    operator_name: str,
    date_query: Optional[Dict[str, Any]],
    store_id: Optional[str] = None,
) -> Dict[str, Any]:
    loss_query = {}
    loss_query["operator"] = operator_name
    if date_query:
        loss_query["created_at"] = date_query
    if store_id:
        loss_query["store"] = ObjectId(store_id)

    loss_records = await LossRecord.find(loss_query).to_list()
    responsible_qty = sum(r.quantity for r in loss_records)

    all_loss_query = {}
    if date_query:
        all_loss_query["created_at"] = date_query
    if store_id:
        all_loss_query["store"] = ObjectId(store_id)
    all_loss_records = await LossRecord.find(all_loss_query).to_list()
    total_qty = sum(r.quantity for r in all_loss_records)

    loss_rate = round(responsible_qty / total_qty * 100, 2) if total_qty > 0 else 0.0

    return {
        "total_loss_quantity": total_qty,
        "responsible_loss_quantity": responsible_qty,
        "loss_rate": loss_rate,
    }


def calculate_performance_score(
    workload: Dict[str, int],
    timeliness: Dict[str, Any],
    loss: Dict[str, Any],
) -> float:
    workload_score = min(workload["total_operations"] / 50 * 40, 40)
    timeliness_score = timeliness["on_time_rate"] / 100 * 35
    loss_score = max(0, 25 - loss["loss_rate"] * 0.5)
    return round(workload_score + timeliness_score + loss_score, 2)


async def get_employee_performance(
    user: User,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    store_id: Optional[str] = None,
) -> Dict[str, Any]:
    date_query = build_date_query(start_date, end_date)
    operator_name = user.full_name or user.username

    workload = await calculate_workload(operator_name, str(user.id), date_query, store_id)
    timeliness = await calculate_timeliness(str(user.id), date_query)
    loss_stats = await calculate_loss_stats(operator_name, date_query, store_id)
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
    results = []

    for user in users:
        perf = await get_employee_performance(user, start_date, end_date, store_id)
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
) -> ResponsibilityTrace:
    trace = ResponsibilityTrace(
        target_type=target_type,
        target_id=target_id,
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


async def get_performance_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    store_id: Optional[str] = None,
) -> Dict[str, Any]:
    users = await User.find(User.is_active == True).to_list()
    performances = []
    for u in users:
        p = await get_employee_performance(u, start_date, end_date, store_id)
        if store_id and p["store"] and p["store"]["id"] != store_id:
            continue
        if store_id and not p["store"]:
            continue
        performances.append(p)

    total_ops = sum(p["workload"]["total_operations"] for p in performances)
    avg_on_time = round(sum(p["timeliness"]["on_time_rate"] for p in performances) / len(performances), 2) if performances else 0
    total_loss = sum(p["loss"]["responsible_loss_quantity"] for p in performances)

    ps = start_date or (datetime.utcnow() - timedelta(days=30)).isoformat()[:10]
    pe = end_date or datetime.utcnow().isoformat()[:10]

    return {
        "period_start": ps,
        "period_end": pe,
        "total_employees": len(performances),
        "total_operations": total_ops,
        "avg_on_time_rate": avg_on_time,
        "total_loss_quantity": total_loss,
    }
