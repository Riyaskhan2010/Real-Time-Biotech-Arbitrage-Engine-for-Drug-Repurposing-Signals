"""
BioArbitrage — Real-Time Biotech Arbitrage Engine for Drug Repurposing Signals
FastAPI Backend Entry Point

DISCLAIMER: This platform is a research decision-support tool.
It does NOT diagnose patients, prescribe medicines, or provide medical treatment.
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine, verify_database_connection
from app.api import auth, dashboard, signals, drugs, diseases, evidence, alerts
from app.api import research_monitor, ingestion
from app.api import public as public_api

logger = logging.getLogger(__name__)


# ── Startup / shutdown ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Verify database is reachable before doing anything else.
    #    Server still starts even if DB is temporarily down — requests will
    #    fail at the endpoint level, which is the correct behaviour.
    db_ok = verify_database_connection()
    if db_ok:
        db_type = "PostgreSQL" if "postgresql" in settings.DATABASE_URL else "SQLite"
        logger.info("[BioArbitrage] Database connected (%s).", db_type)
    else:
        logger.error(
            "[BioArbitrage] Database connection failed — check DATABASE_URL. "
            "Application will start but all DB-dependent endpoints will fail."
        )

    # 2. Create / migrate schema (idempotent — safe to run on every restart).
    Base.metadata.create_all(bind=engine)
    _apply_sqlite_migrations()

    # 3. Warn about optional keys.
    if not settings.ELSEVIER_API_KEY:
        logger.warning(
            "[BioArbitrage] ELSEVIER_API_KEY not set — Elsevier/Scopus source disabled."
        )

    # 4. Seed or skip — controlled by ENABLE_DEMO_SEED / APP_ENV.
    #    Production (APP_ENV=production or ENABLE_DEMO_SEED=false):
    #      → only create user accounts, no demo research data.
    #    Development (default):
    #      → full demo seed when DB is empty.
    from app.database import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            if settings.demo_seeding_enabled:
                logger.info("[BioArbitrage] Empty DB + demo seeding enabled — running full demo seed.")
                from app.data.seeder import seed_database
                seed_database(db)
                logger.info("[BioArbitrage] Demo seed complete.")
            else:
                logger.info(
                    "[BioArbitrage] Production startup — creating user accounts only "
                    "(ENABLE_DEMO_SEED=false / APP_ENV=production). "
                    "No demo research data will be created."
                )
                from app.data.seeder import seed_users_only
                seed_users_only(db)
    finally:
        db.close()

    # 5. Production startup ingestion.
    #    Runs as a background task so the server is immediately responsive.
    #    Skipped automatically when live evidence already exists.
    if settings.APP_ENV == "production":
        asyncio.create_task(_run_startup_ingestion())

    yield
    # (shutdown — nothing to clean up currently)


# ── Production startup ingestion ──────────────────────────────────────────────

async def _run_startup_ingestion() -> None:
    """
    Background task: run one real ingestion pass on first production deploy.

    Guards:
      - Only fires when APP_ENV = production.
      - Checks live evidence count before running — skips if data already exists.
      - Small delay so the HTTP server is fully up before heavy I/O starts.
      - Never raises — all errors are logged and ignored.

    Sources used: PubMed, bioRxiv, medRxiv, ClinicalTrials.gov, Europe PMC,
                  UniProt, and Elsevier (if ELSEVIER_API_KEY is set).
    """
    await asyncio.sleep(8)          # let the server finish binding

    from app.database import SessionLocal
    from app.models.evidence import Evidence
    from app.services.ingestion_service import ingestion_service

    db = SessionLocal()
    try:
        live_count = db.query(Evidence).filter(Evidence.is_demo_data == False).count()
        if live_count > 0:
            logger.info(
                "[BioArbitrage] Startup ingestion skipped — %d live evidence records "
                "already exist in the database.", live_count
            )
            return

        source_list = settings.enabled_sources_list
        elsevier_note = (
            ", Elsevier/Scopus" if settings.ELSEVIER_API_KEY else
            " (Elsevier skipped — ELSEVIER_API_KEY not set)"
        )
        logger.info(
            "[BioArbitrage] Production startup: no live evidence found. "
            "Running ingestion from: %s%s",
            ", ".join(s for s in source_list if s != "elsevier"),
            elsevier_note,
        )

        run = await ingestion_service.run(db)
        logger.info(
            "[BioArbitrage] Startup ingestion complete — "
            "status=%s, new_records=%d, signals_updated=%d, novel_signals=%d",
            run.status, run.total_new, run.signals_updated, run.signals_created,
        )
        if run.summary:
            logger.info("[BioArbitrage] Summary: %s", run.summary)

    except Exception as exc:
        logger.warning(
            "[BioArbitrage] Startup ingestion failed: %s. "
            "Use POST /api/ingestion/run to retry manually.", exc
        )
    finally:
        db.close()


# ── SQLite schema migrations ──────────────────────────────────────────────────

def _apply_sqlite_migrations() -> None:
    """
    Idempotent ALTER TABLE additions for SQLite.
    PostgreSQL handles this through create_all / proper migrations.
    """
    if "sqlite" not in settings.DATABASE_URL:
        return
    with engine.connect() as conn:
        _add_column_if_missing(conn, "evidence", "pmcid", "VARCHAR(50)")
        conn.commit()


def _add_column_if_missing(conn, table: str, column: str, col_type: str) -> None:
    from sqlalchemy import text
    try:
        result = conn.execute(text(f"PRAGMA table_info({table})"))
        existing = [row[1] for row in result.fetchall()]
        if column not in existing:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
            logger.info("[Migration] Added column %s.%s", table, column)
    except Exception as exc:
        logger.warning("[Migration] Could not add %s.%s: %s", table, column, exc)


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="BioArbitrage API",
    description=(
        "Research intelligence platform for drug repurposing signal detection. "
        "Research decision-support tool only — not for clinical use."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

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
        "name":    "BioArbitrage API",
        "version": "1.0.0",
        "env":     settings.APP_ENV,
        "status":  "running",
        "docs":    "/docs",
        "disclaimer": (
            "Research decision-support tool only. "
            "Not for clinical use, diagnosis, or treatment recommendations."
        ),
    }


@app.get("/health")
def health():
    """
    Health endpoint — confirms application and database availability.
    Does NOT expose credentials or secrets.
    """
    db_ok = verify_database_connection()
    db_type = "postgresql" if "postgresql" in settings.DATABASE_URL else "sqlite"
    return {
        "status":        "healthy" if db_ok else "degraded",
        "database":      "connected" if db_ok else "unreachable",
        "database_type": db_type,
        "env":           settings.APP_ENV,
        "demo_seeding":  settings.demo_seeding_enabled,
        "sources":       settings.enabled_sources_list,
    }
