import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from core.config import DB_PATH, SCHEMA_VERSION


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory = None


def _get_db_url() -> str:
    if os.environ.get("FINCO_TEST_DB"):
        return os.environ["FINCO_TEST_DB"]
    return f"sqlite:///{DB_PATH}"


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            _get_db_url(),
            connect_args={"check_same_thread": False},
            echo=False,
        )

        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA busy_timeout=5000;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()

    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _session_factory


def get_session():
    return get_session_factory()()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        columns_res = conn.execute(text("PRAGMA table_info(transactions)")).fetchall()
        column_names = [col[1] for col in columns_res]
        if "ownership_type" not in column_names:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN ownership_type VARCHAR(20) DEFAULT 'shared'"))
        if "split_ratio" not in column_names:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN split_ratio NUMERIC(5, 2) DEFAULT 0.50"))

        row = conn.execute(
            text("PRAGMA user_version")
        ).fetchone()
        current_version = row[0] if row else 0
        if current_version < SCHEMA_VERSION:
            conn.execute(text(f"PRAGMA user_version = {SCHEMA_VERSION}"))
        conn.commit()
