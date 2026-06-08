from app.models.user import User
from app.models.store import Store
from app.models.category import FlowerCategory
from app.models.bucket import Bucket, BucketStatus
from app.models.flower import Flower, PreservationStatus
from app.models.record import (
    RecordType,
    BucketInRecord,
    BucketOutRecord,
    PreservationRecord,
    LossRecord,
)

all_models = [
    User,
    Store,
    FlowerCategory,
    Bucket,
    Flower,
    BucketInRecord,
    BucketOutRecord,
    PreservationRecord,
    LossRecord,
]

__all__ = [
    "User",
    "Store",
    "FlowerCategory",
    "Bucket",
    "BucketStatus",
    "Flower",
    "PreservationStatus",
    "RecordType",
    "BucketInRecord",
    "BucketOutRecord",
    "PreservationRecord",
    "LossRecord",
    "all_models",
]
