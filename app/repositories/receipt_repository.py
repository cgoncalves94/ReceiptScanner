from collections.abc import Sequence

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.models.receipt import Receipt, ReceiptItem


class ReceiptRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, receipt: Receipt) -> Receipt:
        """Create a new receipt."""
        self.db.add(receipt)
        self.db.commit()
        self.db.refresh(receipt)
        return receipt

    def create_items(self, items: list[ReceiptItem]) -> None:
        """Create multiple receipt items."""
        self.db.add_all(items)
        self.db.commit()

    def get_by_id(self, receipt_id: int) -> Receipt | None:
        """Get a receipt by ID."""
        statement = select(Receipt).where(Receipt.id == receipt_id)
        return self.db.exec(statement).first()

    def list(self, skip: int = 0, limit: int = 100) -> Sequence[Receipt]:
        """List receipts with pagination."""
        statement = select(Receipt).offset(skip).limit(limit)
        return self.db.exec(statement).all()

    def list_with_items(self, skip: int = 0, limit: int = 100) -> Sequence[Receipt]:
        """List receipts with their items."""
        statement = (
            select(Receipt)
            .offset(skip)
            .limit(limit)
            .options(selectinload(Receipt.items))
        )
        return self.db.exec(statement).all()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.db.rollback()
