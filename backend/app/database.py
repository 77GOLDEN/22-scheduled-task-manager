"""Database engine and session factory (SQLAlchemy 2.x style)."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import DATABASE_URL

# SQLite needs check_same_thread=False because FastAPI serves requests
# from multiple threads. Postgres doesn't need it.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and always closes it.

    STUDY NOTE: the `finally: db.close()` is the important part -
    leaked connections are one of the most common beginner production bugs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
