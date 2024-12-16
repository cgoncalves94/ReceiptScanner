from collections.abc import Sequence

from sqlmodel import Session, select

from app.models import Receipt, ReceiptItem
from app.schemas import ReceiptCreate, ReceiptUpdate


class ReceiptRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, receipt_in: ReceiptCreate) -> Receipt:
        """Create a new receipt."""
        db_obj = Receipt.model_validate(receipt_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def create_many_items(self, *, items: list[ReceiptItem]) -> None:
        """Create multiple receipt items."""
        self.db.add_all(items)
        self.db.commit()

    def get(self, *, receipt_id: int) -> Receipt | None:
        """Get a receipt by ID."""
        statement = select(Receipt).filter_by(id=receipt_id)
        return self.db.exec(statement).first()

    def get_with_items(self, *, receipt_id: int) -> Receipt | None:
        """Get a receipt with its items by ID."""
        statement = select(Receipt).filter_by(id=receipt_id)
        result = self.db.exec(statement).first()
        if result:
            _ = result.items
        return result

    def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[Receipt]:
        """List receipts with pagination."""
        statement = select(Receipt).offset(skip).limit(limit)
        return self.db.exec(statement).all()

    def list_with_items(self, *, skip: int = 0, limit: int = 100) -> Sequence[Receipt]:
        """List receipts with their items."""
        statement = select(Receipt).offset(skip).limit(limit)
        results = self.db.exec(statement).all()
        for result in results:
            _ = result.items
        return results

    def update(self, *, db_obj: Receipt, receipt_in: ReceiptUpdate) -> Receipt:
        """Update a receipt."""
        receipt_data = receipt_in.model_dump(exclude_unset=True)
        db_obj.sqlmodel_update(receipt_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, *, receipt_id: int) -> None:
        """Delete a receipt."""
        db_obj = self.get(receipt_id=receipt_id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.db.rollback()
