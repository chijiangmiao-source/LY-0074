from datetime import datetime
from beanie import Document, Indexed
from pydantic import Field
from typing import Optional


class Store(Document):
    store_code: Indexed(str, unique=True)
    store_name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    manager: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "stores"
