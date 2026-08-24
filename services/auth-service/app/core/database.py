import os
from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    return database_url


engine: Engine | None = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def get_engine() -> Engine:
    global engine
    if engine is None:
        engine = create_engine(get_database_url(), pool_pre_ping=True)
        SessionLocal.configure(bind=engine)
    return engine


def get_db() -> Generator[Session, None, None]:
    get_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
