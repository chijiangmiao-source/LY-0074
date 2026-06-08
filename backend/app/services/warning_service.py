from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from bson import ObjectId

from app.models import (
    User,
    Bucket,
    Flower,
    Store,
    PreservationStatus,
    LossRecord,
    Warning,
    WarningType,
    WarningSeverity,
    WarningStatus,
)
from app.services.stats_service import calculate_store_loss_rate


LOW_LIQUID_THRESHOLD = 0.3
IN_BUCKET_WARNING_HOURS = 72
HIGH_LOSS_RATE_THRESHOLD = 0.15
MEDIUM_LOSS_RATE_THRESHOLD = 0.08


WARNING_TYPE_LABELS = {
    WarningStatus.PENDING: "待处理",
    WarningStatus.HANDLING: "处理中",
    WarningStatus.RESOLVED: "已解决",
}


def warning_to_response(w: Warning) -> dict:
    store_id = ""
    store_name = ""
    if isinstance(w.store, Store):
        store_id = str(w.store.id)
        store_name = w.store.store_name
    elif w.store:
        store_id = str(w.store)

    bucket_id = ""
    bucket_code = ""
    if isinstance(w.bucket, Bucket):
        bucket_id = str(w.bucket.id)
        bucket_code = w.bucket.bucket_code
    elif w.bucket:
        bucket_id = str(w.bucket)

    flower_id = ""
    flower_name = ""
    flower_code = ""
    if isinstance(w.flower, Flower):
        flower_id = str(w.flower.id)
        flower_name = w.flower.flower_name
        flower_code = w.flower.flower_code
    elif w.flower:
        flower_id = str(w.flower)

    handler_name = ""
    if isinstance(w.handler, User):
        handler_name = w.handler.full_name or w.handler.username
    elif w.handler:
        handler_name = str(w.handler)

    return {
        "warning_id": str(w.id),
        "warning_type": w.warning_type.value,
        "warning_type_label": w.warning_type_label,
        "severity": w.severity.value,
        "store_id": store_id,
        "store_name": store_name,
        "bucket_id": bucket_id,
        "bucket_code": bucket_code,
        "flower_id": flower_id,
        "flower_name": flower_name,
        "flower_code": flower_code,
        "message": w.message,
        "current_value": w.current_value,
        "threshold": w.threshold_value,
        "unit": w.unit,
        "status": w.status.value,
        "status_label": WARNING_TYPE_LABELS.get(w.status, w.status.value),
        "handler": handler_name,
        "handled_at": w.handled_at.isoformat() if w.handled_at else None,
        "handle_note": w.handle_note,
        "created_at": w.created_at.isoformat(),
        "updated_at": w.updated_at.isoformat(),
    }


async def _generate_low_liquid_warnings(
    buckets: List[Bucket],
    now: datetime,
    active_keys: Set[str],
) -> None:
    for bucket in buckets:
        if bucket.capacity <= 0:
            continue
        liquid_ratio = bucket.current_quantity / bucket.capacity
        if liquid_ratio < LOW_LIQUID_THRESHOLD:
            severity = WarningSeverity.HIGH if liquid_ratio < 0.1 else WarningSeverity.MEDIUM
            key = f"{WarningType.LOW_LIQUID.value}:{bucket.id}"
            active_keys.add(key)
            store_ref = bucket.store if isinstance(bucket.store, Store) else None
            existing = await Warning.find_one(
                Warning.warning_type == WarningType.LOW_LIQUID,
                Warning.bucket.id == bucket.id,
                Warning.status != WarningStatus.RESOLVED,
            )
            if not existing:
                w = Warning(
                    warning_type=WarningType.LOW_LIQUID,
                    warning_type_label="液位过低",
                    severity=severity,
                    store=store_ref,
                    bucket=bucket,
                    flower=None,
                    message=f"花桶 {bucket.bucket_code} 液位仅 {liquid_ratio*100:.1f}%，需要及时补充保鲜液",
                    current_value=str(round(bucket.current_quantity, 2)),
                    threshold_value=str(round(bucket.capacity * LOW_LIQUID_THRESHOLD, 2)),
                    unit="L",
                    status=WarningStatus.PENDING,
                    created_at=now,
                    updated_at=now,
                )
                await w.create()
            else:
                existing.severity = severity
                existing.current_value = str(round(bucket.current_quantity, 2))
                existing.message = f"花桶 {bucket.bucket_code} 液位仅 {liquid_ratio*100:.1f}%，需要及时补充保鲜液"
                existing.updated_at = now
                await existing.save()


async def _generate_wilted_warnings(
    flowers: List[Flower],
    now: datetime,
    active_keys: Set[str],
) -> None:
    for flower in flowers:
        if flower.preservation_status == PreservationStatus.WILTED:
            key = f"{WarningType.WILTED.value}:{flower.id}"
            active_keys.add(key)
            store_ref = flower.store if isinstance(flower.store, Store) else None
            bucket_ref = flower.bucket if isinstance(flower.bucket, Bucket) else None
            existing = await Warning.find_one(
                Warning.warning_type == WarningType.WILTED,
                Warning.flower.id == flower.id,
                Warning.status != WarningStatus.RESOLVED,
            )
            if not existing:
                w = Warning(
                    warning_type=WarningType.WILTED,
                    warning_type_label="花材萎蔫",
                    severity=WarningSeverity.HIGH,
                    store=store_ref,
                    bucket=bucket_ref,
                    flower=flower,
                    message=f"花材 {flower.flower_name}({flower.flower_code}) 已萎蔫，需要及时处理",
                    current_value="wilted",
                    threshold_value="fresh/normal",
                    unit="",
                    status=WarningStatus.PENDING,
                    created_at=now,
                    updated_at=now,
                )
                await w.create()


async def _generate_long_in_bucket_warnings(
    flowers: List[Flower],
    now: datetime,
    active_keys: Set[str],
) -> None:
    for flower in flowers:
        if not flower.in_bucket_date or not flower.bucket:
            continue
        hours_in_bucket = (now - flower.in_bucket_date).total_seconds() / 3600
        if hours_in_bucket > IN_BUCKET_WARNING_HOURS:
            severity = WarningSeverity.MEDIUM if hours_in_bucket < 120 else WarningSeverity.HIGH
            key = f"{WarningType.LONG_IN_BUCKET.value}:{flower.id}"
            active_keys.add(key)
            store_ref = flower.store if isinstance(flower.store, Store) else None
            bucket_ref = flower.bucket if isinstance(flower.bucket, Bucket) else None
            existing = await Warning.find_one(
                Warning.warning_type == WarningType.LONG_IN_BUCKET,
                Warning.flower.id == flower.id,
                Warning.status != WarningStatus.RESOLVED,
            )
            if not existing:
                w = Warning(
                    warning_type=WarningType.LONG_IN_BUCKET,
                    warning_type_label="入桶时间过长",
                    severity=severity,
                    store=store_ref,
                    bucket=bucket_ref,
                    flower=flower,
                    message=f"花材 {flower.flower_name} 已入桶 {hours_in_bucket:.1f} 小时，超过建议时长",
                    current_value=str(round(hours_in_bucket, 1)),
                    threshold_value=str(IN_BUCKET_WARNING_HOURS),
                    unit="小时",
                    status=WarningStatus.PENDING,
                    created_at=now,
                    updated_at=now,
                )
                await w.create()
            else:
                existing.severity = severity
                existing.current_value = str(round(hours_in_bucket, 1))
                existing.message = f"花材 {flower.flower_name} 已入桶 {hours_in_bucket:.1f} 小时，超过建议时长"
                existing.updated_at = now
                await existing.save()


async def _generate_high_loss_warnings(
    stores: List[Store],
    now: datetime,
    active_keys: Set[str],
) -> None:
    for store in stores:
        loss_records = await LossRecord.find(LossRecord.store.id == store.id).to_list()
        store_flowers = await Flower.find(Flower.store.id == store.id).to_list()
        current_qty = sum(f.current_quantity for f in store_flowers)

        loss_rate, recent_loss_qty, base_total = calculate_store_loss_rate(
            loss_records, current_qty, days=7
        )

        if base_total <= 0:
            continue

        if loss_rate >= MEDIUM_LOSS_RATE_THRESHOLD:
            severity = WarningSeverity.HIGH if loss_rate >= HIGH_LOSS_RATE_THRESHOLD else WarningSeverity.MEDIUM
            key = f"{WarningType.HIGH_LOSS.value}:{store.id}"
            active_keys.add(key)
            existing = await Warning.find_one(
                Warning.warning_type == WarningType.HIGH_LOSS,
                Warning.store.id == store.id,
                Warning.status != WarningStatus.RESOLVED,
            )
            if not existing:
                w = Warning(
                    warning_type=WarningType.HIGH_LOSS,
                    warning_type_label="损耗过高",
                    severity=severity,
                    store=store,
                    bucket=None,
                    flower=None,
                    message=f"门店 {store.store_name} 近7天损耗率 {loss_rate*100:.1f}%（损耗{recent_loss_qty}枝 / 总库存{base_total}枝），超过阈值",
                    current_value=str(round(loss_rate * 100, 1)),
                    threshold_value=str(round(MEDIUM_LOSS_RATE_THRESHOLD * 100, 1)),
                    unit="%",
                    status=WarningStatus.PENDING,
                    created_at=now,
                    updated_at=now,
                )
                await w.create()
            else:
                existing.severity = severity
                existing.current_value = str(round(loss_rate * 100, 1))
                existing.message = f"门店 {store.store_name} 近7天损耗率 {loss_rate*100:.1f}%（损耗{recent_loss_qty}枝 / 总库存{base_total}枝），超过阈值"
                existing.updated_at = now
                await existing.save()


async def sync_generated_warnings() -> Set[str]:
    now = datetime.utcnow()
    buckets = await Bucket.find(fetch_links=True).to_list()
    flowers = await Flower.find(fetch_links=True).to_list()
    stores = await Store.find(Store.is_active == True).to_list()

    active_keys: Set[str] = set()

    await _generate_low_liquid_warnings(buckets, now, active_keys)
    await _generate_wilted_warnings(flowers, now, active_keys)
    await _generate_long_in_bucket_warnings(flowers, now, active_keys)
    await _generate_high_loss_warnings(stores, now, active_keys)

    return active_keys


async def get_warnings(
    store_id: Optional[str] = None,
    warning_type: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    await sync_generated_warnings()

    query = {}
    if status:
        query["status"] = WarningStatus(status)
    else:
        query["status"] = {"$in": [WarningStatus.PENDING, WarningStatus.HANDLING]}

    warnings = await Warning.find(query, fetch_links=True).sort("-severity", "-created_at").to_list()

    result = []
    for w in warnings:
        w_data = warning_to_response(w)
        if store_id and w_data["store_id"] != store_id:
            continue
        if warning_type and w_data["warning_type"] != warning_type:
            continue
        result.append(w_data)

    return result


async def handle_warning(
    warning_id: str,
    status: WarningStatus,
    note: Optional[str],
    current_user: User,
) -> Dict[str, Any]:
    from app.services.performance import add_responsibility_trace
    from app.models.performance import ResponsibilityTargetType, ResponsibilityAction

    w = await Warning.get(ObjectId(warning_id), fetch_links=True)
    if not w:
        raise ValueError("预警不存在")

    w.status = status
    w.handler = current_user
    w.handle_note = note
    w.handled_at = datetime.utcnow()
    w.updated_at = datetime.utcnow()
    await w.save()
    await w.fetch_all_links()

    store = w.store if isinstance(w.store, Store) else None
    bucket = w.bucket if isinstance(w.bucket, Bucket) else None
    flower = w.flower if isinstance(w.flower, Flower) else None
    status_label = WARNING_TYPE_LABELS.get(status, status.value)

    flower_batch = flower.batch_no if flower and hasattr(flower, 'batch_no') else None
    await add_responsibility_trace(
        target_type=ResponsibilityTargetType.WARNING,
        target_id=str(w.id),
        batch_no=flower_batch,
        action=ResponsibilityAction.WARNING_HANDLE,
        user=current_user,
        remark=f"更新预警状态为{status_label}，备注：{note or '无'}",
        store=store,
        bucket=bucket,
        flower=flower,
        warning=w,
    )
    if bucket:
        await add_responsibility_trace(
            target_type=ResponsibilityTargetType.BUCKET,
            target_id=str(bucket.id),
            batch_no=flower_batch,
            action=ResponsibilityAction.WARNING_HANDLE,
            user=current_user,
            remark=f"处理预警[{w.warning_type_label}]，状态：{status_label}",
            store=store,
            bucket=bucket,
            flower=flower,
            warning=w,
        )
    if flower:
        await add_responsibility_trace(
            target_type=ResponsibilityTargetType.FLOWER,
            target_id=str(flower.id),
            batch_no=flower_batch,
            action=ResponsibilityAction.WARNING_HANDLE,
            user=current_user,
            remark=f"处理预警[{w.warning_type_label}]，状态：{status_label}",
            store=store,
            bucket=bucket,
            flower=flower,
            warning=w,
        )

    return warning_to_response(w)
