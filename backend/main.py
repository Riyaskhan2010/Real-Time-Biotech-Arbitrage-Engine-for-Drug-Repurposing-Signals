"""
BioArbitrage — Real-Time Biotech Arbitrage Engine for Drug Repurposing Signals
FastAPI Backend Entry Point

DISCLAIMER: This platform is a research decision-support tool.
It does NOT diagnose patients, prescribe medicines, or provide medical treatment recommendations.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base
from app.api import auth, dashboard, signals, drugs, diseases, evidence, alerts
from app.api import research_monitor
from app.api import ingestion


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (safe — only creates missing tables)
    Base.metadata.create_all(bind=engine)

    # Apply safe column additions for SQLite (idempotent ALTER TABLE)
    _apply_sqlite_migrations()

    # Warn about missing optional API keys
    if not settings.ELSEVIER_API_KEY:
        print("[BioArbitrage] WARNING: ELSEVIER_API_KEY is not set in backend/.env — "
              "Elsevier/Scopus source will be disabled. "
              "Add your Elsevier Developer API key to backend/.env and restart the server.")

    # Auto-seed if database is empty
    from app.database import SessionLocal
    from app.models.user import User
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            print("Database is empty — running demo seeder...")
            from app.data.seeder import seed_database
            seed_database(db)
    finally:
        db.close()

    yield


def _apply_sqlite_migrations():
    """
    Apply any new columns to existing SQLite tables without losing data.
    SQLite does not support DROP COLUMN or complex ALTER TABLE, but
    ADD COLUMN is safe and idempotent via 'IF NOT EXISTS' workaround.
    """
    from sqlalchemy import text
    with engine.connect() as conn:
        _add_column_if_missing(conn, "evidence", "pmcid", "VARCHAR(50)")
        conn.commit()


def _add_column_if_missing(conn, table: str, column: str, col_type: str):
    """Add a column to a SQLite table only if it does not already exist."""
    from sqlalchemy import text
    try:
        result = conn.execute(text(f"PRAGMA table_info({table})"))
        existing = [row[1] for row in result.fetchall()]
        if column not in existing:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
            print(f"[Migration] Added column {table}.{column}")
    except Exception as e:
        print(f"[Migration] Warning: could not add {table}.{column}: {e}")


app = FastAPI(
    title="BioArbitrage API",
    description=(
        "Research intelligence platform for drug repurposing signal detection. "
        "Research decision-support tool only — not for clinical use."
    ),
    version="1.0.0-mvp",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(signals.router)
app.include_router(drugs.router)
app.include_router(diseases.router)
app.include_router(evidence.router)
app.include_router(alerts.router)
app.include_router(research_monitor.router)
app.include_router(ingestion.router)


@app.get("/")
def root():
    return {
        "name": "BioArbitrage API",
        "version": "1.0.0-mvp",
        "status": "running",
        "disclaimer": (
            "Research decision-support tool only. "
            "Not for clinical use, diagnosis, or treatment recommendations."
        ),
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy", "env": settings.APP_ENV}
