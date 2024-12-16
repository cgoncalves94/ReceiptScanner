from collections.abc import Generator

from fastapi import Depends
from sqlmodel import Session

from app.db.session import SessionLocal, engine
from app.services import CategoryService, ReceiptService


def get_db() -> Generator:
    """Database dependency that creates a new session for each request."""
    with SessionLocal(engine) as db:
        try:
            yield db
        finally:
            db.close()


def get_receipt_service(db: Session = Depends(get_db)) -> ReceiptService:
    """Get a ReceiptService instance."""
    return ReceiptService(db)


def get_category_service(db: Session = Depends(get_db)) -> CategoryService:
    """Get a CategoryService instance."""
    return CategoryService(db)
