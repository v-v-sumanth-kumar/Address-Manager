"""Database session management and dependency injection."""

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from app.db.database import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session for request-scoped dependency injection.

    Yields:
        SQLAlchemy session that is closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
