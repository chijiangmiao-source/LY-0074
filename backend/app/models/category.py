from datetime import datetime
from beanie import Document, Indexed
from pydantic import Field
from typing import Optional


class FlowerCategory(Document):
    category_code: Indexed(str, unique=True)
    category_name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "flower_categories"
