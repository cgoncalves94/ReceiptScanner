from collections.abc import Generator

from app.db.session import SessionLocal, engine


def get_db() -> Generator:
    """Database dependency that creates a new session for each request."""
    with SessionLocal(engine) as db:
        try:
            yield db
        finally:
            db.close()
