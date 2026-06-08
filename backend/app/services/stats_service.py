from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from bson import ObjectId
from collections import defaultdict

from app.models import (
    User,
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
    StatusChangeRecord,
    StatusChangeTarget,
)


WARNING_HANDLE_OVERDUE_HOURS = 24


def build_date_query(
    start_date: Optional[str],
    end_date: Optional[str],
) -> Optional[Dict[str, Any]]:
    date_query = {}
    if start_date:
        date_query["$gte"] = datetime.fromisoformat(start_date)
    if end_date:
        date_query["$lte"] = datetime.fromisoformat(end_date) + timedelta(days=1)
    return date_query if date_query else None


def resolve_date_range(
    start_date: Optional[str],
    end_date: Optional[str],
    default_days: int = 30,
) -> Tuple[str, str]:
    ps = start_date or (datetime.utcnow() - timedelta(days=default_days)).isoformat()[:10]
    pe = end_date or datetime.utcnow().isoformat()[:10]
    return ps, pe


async def get_operator_name(user_id: Optional[str]) -> str:
    if not user_id:
        return ""
    user = await User.get(ObjectId(user_id))
    if not user:
        return ""
    return user.full_name or user.username


async def get_user_store(user: User) -> Optional[Store]:
    traces = await ResponsibilityTrace.find(
        ResponsibilityTrace.operator.id == user.id,
        fetch_links=True,
    ).sort("-created_at").limit(5).to_list()
    for t in traces:
        if isinstance(t.store, Store):
            return t.store
    return None


async def get_user_store_id(user: User) -> Optional[str]:
    store = await get_user_store(user)
    return str(store.id) if store else None


class BatchRecordLoader:
    def __init__(
        self,
        date_query: Optional[Dict[str, Any]] = None,
        store_id: Optional[str] = None,
    ):
        self.date_query = date_query
        self.store_id = store_id
        self.store_oid = ObjectId(store_id) if store_id else None

        self.in_records: List[BucketInRecord] = []
        self.out_records: List[BucketOutRecord] = []
        self.pres_records: List[PreservationRecord] = []
        self.loss_records: List[LossRecord] = []
        self.warnings: List[Warning] = []
        self.status_records: List[StatusChangeRecord] = []

        self._in_by_user: Dict[str, List[BucketInRecord]] = defaultdict(list)
        self._out_by_user: Dict[str, List[BucketOutRecord]] = defaultdict(list)
        self._pres_by_user: Dict[str, List[PreservationRecord]] = defaultdict(list)
        self._loss_by_user: Dict[str, List[LossRecord]] = defaultdict(list)
        self._warning_by_user: Dict[str, List[Warning]] = defaultdict(list)
        self._status_by_user: Dict[str, List[StatusChangeRecord]] = defaultdict(list)

        self._in_by_store: Dict[str, List[BucketInRecord]] = defaultdict(list)
        self._out_by_store: Dict[str, List[BucketOutRecord]] = defaultdict(list)
        self._pres_by_store: Dict[str, List[PreservationRecord]] = defaultdict(list)
        self._loss_by_store: Dict[str, List[LossRecord]] = defaultdict(list)

        self._loaded = False

    async def load_all(self):
        if self._loaded:
            return

        in_query: Dict[str, Any] = {}
        out_query: Dict[str, Any] = {}
        pres_query: Dict[str, Any] = {}
        loss_query: Dict[str, Any] = {}
        warning_query: Dict[str, Any] = {}
        status_query: Dict[str, Any] = {}

        if self.date_query:
            in_query["created_at"] = self.date_query
            out_query["created_at"] = self.date_query
            pres_query["created_at"] = self.date_query
            loss_query["created_at"] = self.date_query
            status_query["created_at"] = self.date_query

        if self.store_oid:
            pres_query["store"] = self.store_oid
            loss_query["store"] = self.store_oid

        self.in_records = await BucketInRecord.find(in_query, fetch_links=True).to_list()
        self.out_records = await BucketOutRecord.find(out_query, fetch_links=True).to_list()
        self.pres_records = await PreservationRecord.find(pres_query, fetch_links=True).to_list()
        self.loss_records = await LossRecord.find(loss_query, fetch_links=True).to_list()

        if self.date_query and "created_at" in self.date_query:
            warning_query["handled_at"] = self.date_query["created_at"]
        elif self.date_query and "$gte" in self.date_query:
            warning_query["created_at"] = self.date_query
        self.warnings = await Warning.find(warning_query, fetch_links=True).to_list()

        status_query["target_type"] = {
            "$in": [StatusChangeTarget.BUCKET_STATUS, StatusChangeTarget.FLOWER_PRESERVATION]
        }
        self.status_records = await StatusChangeRecord.find(status_query, fetch_links=True).to_list()

        self._build_indexes()
        self._loaded = True

    def _build_indexes(self):
        for r in self.in_records:
            uid = self._get_user_id(r)
            if uid:
                self._in_by_user[uid].append(r)
            sid = self._get_store_id_from_bucket(r.bucket)
            if sid:
                self._in_by_store[sid].append(r)

        for r in self.out_records:
            uid = self._get_user_id(r)
            if uid:
                self._out_by_user[uid].append(r)
            sid = self._get_store_id_from_bucket(r.bucket)
            if sid:
                self._out_by_store[sid].append(r)

        for r in self.pres_records:
            uid = self._get_user_id(r)
            if uid:
                self._pres_by_user[uid].append(r)
            sid = self._get_store_id(r.store)
            if sid:
                self._pres_by_store[sid].append(r)

        for r in self.loss_records:
            uid = self._get_user_id(r)
            if uid:
                self._loss_by_user[uid].append(r)
            sid = self._get_store_id(r.store)
            if sid:
                self._loss_by_store[sid].append(r)

        for w in self.warnings:
            uid = self._get_link_id(w.handler)
            if uid:
                self._warning_by_user[uid].append(w)

        for s in self.status_records:
            uid = self._get_link_id(s.operator)
            if uid:
                self._status_by_user[uid].append(s)

    @staticmethod
    def _get_user_id(record) -> Optional[str]:
        if hasattr(record, "operator_id") and record.operator_id:
            if hasattr(record.operator_id, "id"):
                return str(record.operator_id.id)
            return str(record.operator_id)
        return None

    @staticmethod
    def _get_link_id(link) -> Optional[str]:
        if not link:
            return None
        if hasattr(link, "id"):
            return str(link.id)
        return str(link)

    @staticmethod
    def _get_store_id(link) -> Optional[str]:
        if not link:
            return None
        if hasattr(link, "id"):
            return str(link.id)
        return str(link)

    @staticmethod
    def _get_store_id_from_bucket(bucket_link) -> Optional[str]:
        if not bucket_link:
            return None
        if isinstance(bucket_link, Bucket) and bucket_link.store:
            return BatchRecordLoader._get_store_id(bucket_link.store)
        return None

    @staticmethod
    def _match_operator_name(records: List, operator_name: str) -> List:
        if not operator_name:
            return []
        matched = []
        for r in records:
            if hasattr(r, "operator") and r.operator == operator_name:
                matched.append(r)
        return matched

    def get_in_records_for_user(
        self,
        user_id: str,
        operator_name: Optional[str] = None,
    ) -> List[BucketInRecord]:
        result = list(self._in_by_user.get(user_id, []))
        if not result and operator_name:
            result = self._match_operator_name(self.in_records, operator_name)
        return result

    def get_out_records_for_user(
        self,
        user_id: str,
        operator_name: Optional[str] = None,
    ) -> List[BucketOutRecord]:
        result = list(self._out_by_user.get(user_id, []))
        if not result and operator_name:
            result = self._match_operator_name(self.out_records, operator_name)
        return result

    def get_pres_records_for_user(
        self,
        user_id: str,
        operator_name: Optional[str] = None,
    ) -> List[PreservationRecord]:
        result = list(self._pres_by_user.get(user_id, []))
        if not result and operator_name:
            result = self._match_operator_name(self.pres_records, operator_name)
        return result

    def get_loss_records_for_user(
        self,
        user_id: str,
        operator_name: Optional[str] = None,
    ) -> List[LossRecord]:
        result = list(self._loss_by_user.get(user_id, []))
        if not result and operator_name:
            result = self._match_operator_name(self.loss_records, operator_name)
        return result

    def get_warnings_for_user(self, user_id: str) -> List[Warning]:
        return list(self._warning_by_user.get(user_id, []))

    def get_status_records_for_user(self, user_id: str) -> List[StatusChangeRecord]:
        return list(self._status_by_user.get(user_id, []))

    def get_loss_records_for_store(self, store_id: str) -> List[LossRecord]:
        return list(self._loss_by_store.get(store_id, []))


def calculate_workload_from_records(
    in_records: List,
    out_records: List,
    pres_records: List,
    loss_records: List,
    warnings: List,
    status_records: List,
) -> Dict[str, int]:
    return {
        "in_bucket_count": len(in_records),
        "out_bucket_count": len(out_records),
        "preservation_count": len(pres_records),
        "loss_count": len(loss_records),
        "warning_handled_count": len(warnings),
        "inspection_count": len(status_records),
        "total_operations": (
            len(in_records)
            + len(out_records)
            + len(pres_records)
            + len(loss_records)
            + len(warnings)
            + len(status_records)
        ),
    }


def calculate_timeliness_from_warnings(
    warnings: List[Warning],
) -> Dict[str, Any]:
    on_time = 0
    overdue = 0
    handle_hours_list: List[float] = []

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


def calculate_loss_stats_from_records(
    user_loss_records: List[LossRecord],
    all_loss_records: List[LossRecord],
) -> Dict[str, Any]:
    responsible_qty = sum(r.quantity for r in user_loss_records)
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


def calculate_store_loss_rate(
    loss_records: List[LossRecord],
    current_flower_qty: int,
    days: int = 7,
) -> Tuple[float, int, int]:
    now = datetime.utcnow()
    recent = [r for r in loss_records if (now - r.created_at).days <= days]
    recent_loss_qty = sum(r.quantity for r in recent)
    base_total = current_flower_qty + recent_loss_qty
    loss_rate = recent_loss_qty / base_total if base_total > 0 else 0
    return loss_rate, recent_loss_qty, base_total
