"""
Database engine configuration.

Local development : SQLite  (DATABASE_URL = sqlite:///./bioarbitrage.db)
Production/Render : PostgreSQL (DATABASE_URL = postgresql://user:pass@host/db)
                    or SQLite on persistent disk (sqlite:////data/bioarbitrage.db)

Never hard-code credentials here.  Set DATABASE_URL via environment variable.
"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

_url = settings.DATABASE_URL
_is_sqlite = _url.startswith("sqlite")

if _is_sqlite:
    # SQLite: disable same-thread check (FastAPI uses a thread pool for sync deps)
    engine = create_engine(
        _url,
        connect_args={"check_same_thread": False},
        # Single writer — no pool needed for SQLite
        pool_pre_ping=True,
    )

    # Enable WAL mode so reads don't block the writer and concurrent
    # connections (multiple API workers) work correctly with SQLite.
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

else:
    # PostgreSQL (or any other RDBMS): use a proper connection pool.
    # pool_size + max_overflow should comfortably cover ≥10 concurrent users.
    engine = create_engine(
        _url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,       # discard stale connections silently
        pool_recycle=1800,        # recycle connections every 30 min
        pool_timeout=30,
    )


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields one DB session per request, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_database_connection() -> bool:
    """
    Probe the database at startup.
    Returns True on success, False on failure (never raises).
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("[Database] Connection probe failed: %s", e)
        return False
