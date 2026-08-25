"""
BioArbitrage — Real-Time Biotech Arbitrage Engine for Drug Repurposing Signals
FastAPI Backend Entry Point

DISCLAIMER: This platform is a research decision-support tool.
It does NOT diagnose patients, prescribe medicines, or provide medical treatment recommendations.
"""
import asyncio
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
from app.api import public as public_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (safe — only creates missing tables)
    Base.metadata.create_all(bind=engine)

    # Apply safe column additions for SQLite (idempotent ALTER TABLE)
    _apply_sqlite_migrations()

    # Warn about missing optional API keys
    if not settings.ELSEVIER_API_KEY:
        print("[BioArbitrage] WARNING: ELSEVIER_API_KEY is not set — "
              "Elsevier/Scopus source will be disabled.")

    # Auto-seed if database is empty (creates demo users, drugs, diseases, signals)
    from app.database import SessionLocal
    from app.models.user import User
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            print("[BioArbitrage] Database is empty — running demo seeder...")
            from app.data.seeder import seed_database
            seed_database(db)
            print("[BioArbitrage] Demo seed complete.")
    finally:
        db.close()

    # ── Production: trigger real ingestion on first startup ───────────────────
    # On Render (APP_ENV=production), after seeding we run a real ingestion pass
    # so the platform immediately starts building live research data from the
    # configured biomedical sources (PubMed, bioRxiv, medRxiv, ClinicalTrials,
    # Europe PMC, UniProt). Elsevier requires ELSEVIER_API_KEY to be set.
    #
    # This runs in the background so the server starts responding immediately.
    # On subsequent deploys, if live evidence already exists this is skipped.
    if settings.APP_ENV == "production":
        asyncio.create_task(_run_startup_ingestion())

    yield


async def _run_startup_ingestion() -> None:
    """
    Background task: run a real ingestion pass on production startup.

    Only runs when:
      - APP_ENV = production
      - No live (non-demo) evidence records exist yet

    This ensures:
      1. First deploy → ingestion runs automatically, populating real data
      2. Subsequent deploys → skipped (live data already present)
      3. Local dev → never runs (APP_ENV defaults to development)

    All sources that don't require API keys run unconditionally.
    Elsevier requires ELSEVIER_API_KEY — it is skipped if not set.
    """
    # Small delay to let the server finish startup before the heavy I/O begins
    await asyncio.sleep(5)

    from app.database import SessionLocal
    from app.models.evidence import Evidence
    from app.services.ingestion_service import ingestion_service

    db = SessionLocal()
    try:
        live_evidence_count = db.query(Evidence).filter(
            Evidence.is_demo_data == False
        ).count()

        if live_evidence_count > 0:
            print(
                f"[BioArbitrage] Production startup: {live_evidence_count} live evidence "
                "records already exist — skipping startup ingestion."
            )
            return

        print(
            "[BioArbitrage] Production startup: no live evidence found — "
            "running startup ingestion from configured biomedical sources..."
        )
        print("[BioArbitrage] Sources: PubMed, bioRxiv, medRxiv, ClinicalTrials.gov, "
              "Europe PMC, UniProt" +
              (", Elsevier/Scopus" if settings.ELSEVIER_API_KEY else
               " (Elsevier skipped — ELSEVIER_API_KEY not set)"))

        run = await ingestion_service.run(db)

        print(
            f"[BioArbitrage] Startup ingestion complete — "
            f"status={run.status}, "
            f"new_records={run.total_new}, "
            f"signals_updated={run.signals_updated}, "
            f"novel_signals={run.signals_created}"
        )
        if run.summary:
            print(f"[BioArbitrage] Summary: {run.summary}")

    except Exception as e:
        print(f"[BioArbitrage] WARNING: Startup ingestion failed: {e}. "
              "Demo data is still available. "
              "Use POST /api/ingestion/run to retry manually.")
    finally:
        db.close()


def _apply_sqlite_migrations():
    """
    Apply any new columns to existing SQLite tables without losing data.
    SQLite does not support DROP COLUMN or complex ALTER TABLE, but
    ADD COLUMN is safe and idempotent.
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
app.include_router(public_api.router)


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
