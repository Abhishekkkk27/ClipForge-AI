"""
ClipForge AI — SQLAlchemy database setup
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend import config

config.ensure_directories()

engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite + threading
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables."""
    from backend import models  # noqa: F401  — registers models with Base
    Base.metadata.create_all(bind=engine)
