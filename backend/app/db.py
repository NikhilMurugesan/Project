# Boring SQLAlchemy plumbing. SQLite by default so the demo is zero-setup;
# point ALLOCATION_DB_URL at Postgres or anything else if you want.
from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DB_URL = os.environ.get("ALLOCATION_DB_URL", "sqlite:///./allocation.db")

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import for the side effect of registering the models on Base.metadata --
    # without this the create_all below wouldn't know what tables to make.
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
