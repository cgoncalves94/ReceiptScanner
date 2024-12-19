from datetime import datetime

from pydantic import BaseModel


class ReceiptData(BaseModel):
    """Receipt data extracted from analysis."""

    store_name: str
    total_amount: float
    currency: str
    image_path: str
    date: datetime | None


class ItemData(BaseModel):
    """Item data extracted from analysis."""

    name: str
    price: float
    quantity: float
    currency: str
    category_name: str
    category_description: str


class AnalysisResult(BaseModel):
    """Complete result of receipt analysis."""

    receipt: ReceiptData
    items: list[ItemData]
    category_names: list[str]
