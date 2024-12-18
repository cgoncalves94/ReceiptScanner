from datetime import datetime

from pydantic import BaseModel, Field


class CategoryInfo(BaseModel):
    """Category information from AI analysis."""

    name: str
    description: str


class ItemData(BaseModel):
    """Item data from AI analysis."""

    name: str
    price: float
    quantity: float = Field(default=1.0)
    currency: str
    category_name: str
    category_description: str


class ReceiptData(BaseModel):
    """Receipt data from AI analysis."""

    store_name: str
    total_amount: float
    currency: str
    image_path: str
    date: datetime | None


class AnalysisResult(BaseModel):
    """Complete result of receipt analysis."""

    receipt: ReceiptData
    items: list[ItemData]
    category_names: list[str]
