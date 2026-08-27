"""
BioArbitrage — Real-Time Biotech Arbitrage Engine for Drug Repurposing Signals
FastAPI Backend Entry Point

DISCLAIMER: This platform is a research decision-support tool.
It does NOT diagnose patients, prescribe medicines, or provide medical treatment.
"""
import asyncio
import logging
import math
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta

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
    # 1. Verify database is reachable.
    db_ok = verify_database_connection()
    if db_ok:
        db_type = "PostgreSQL" if "postgresql" in settings.DATABASE_URL else "SQLite"
        logger.info("[BioArbitrage] Database connected (%s).", db_type)
    else:
        logger.error(
            "[BioArbitrage] Database connection failed — check DATABASE_URL. "
            "Application will start but all DB-dependent endpoints will fail."
        )

    # 2. Create / migrate schema (idempotent — safe on every restart).
    Base.metadata.create_all(bind=engine)
    _apply_sqlite_migrations()

    # 3. Warn about optional keys.
    if not settings.ELSEVIER_API_KEY:
        logger.warning(
            "[BioArbitrage] ELSEVIER_API_KEY not set — Elsevier/Scopus source disabled."
        )

    # 4. Stale-run cleanup.
    #    On restart, any IngestionRun with status="running" is an orphan left
    #    by a previous crash.  Mark them as failed so the lock is cleared
    #    immediately rather than waiting for the 30-minute timeout.
    _cleanup_stale_runs()

    # 5. Seed or skip.
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

    # 6. Production startup: first-time ingestion (empty DB only).
    if settings.APP_ENV == "production":
        asyncio.create_task(_run_startup_ingestion())

    # 7. Background periodic scheduler.
    #    Runs in all environments when INGESTION_INTERVAL_HOURS > 0.
    #    In development the interval still applies — set to 0 in .env to disable.
    scheduler_task = None
    if settings.INGESTION_INTERVAL_HOURS > 0:
        scheduler_task = asyncio.create_task(_run_periodic_ingestion())
        logger.info(
            "[BioArbitrage] Scheduler started — ingestion every %d hour(s). "
            "Set INGESTION_INTERVAL_HOURS=0 to disable.",
            settings.INGESTION_INTERVAL_HOURS,
        )
    else:
        logger.info(
            "[BioArbitrage] Scheduler disabled (INGESTION_INTERVAL_HOURS=0). "
            "Use POST /api/ingestion/run to trigger ingestion manually."
        )

    # ── yield: FastAPI serves requests here ──────────────────────────────────
    yield

    # ── Shutdown: cancel the scheduler cleanly ────────────────────────────────
    if scheduler_task is not None:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        logger.info("[BioArbitrage] Scheduler stopped.")


# ── Stale-run cleanup ─────────────────────────────────────────────────────────

def _cleanup_stale_runs() -> None:
    """
    On every startup, find IngestionRun rows stuck in status="running" and
    mark them as failed.  These are orphans left by a previous process crash
    (Python exception handling can't fire on SIGKILL / OOM / container restart).

    Without this, the DB-backed lock (30-minute timeout) would block new runs
    for up to 30 minutes after a crash restart.
    """
    from app.database import SessionLocal
    from app.models.ingestion_run import IngestionRun

    db = SessionLocal()
    try:
        stale_cutoff = datetime.now(timezone.utc) - timedelta(minutes=1)
        stale = db.query(IngestionRun).filter(
            IngestionRun.status    == "running",
            IngestionRun.started_at <= stale_cutoff,
        ).all()
        if stale:
            for run in stale:
                run.status      = "failed"
                run.error       = "Process restarted — run was orphaned mid-execution."
                run.finished_at = datetime.now(timezone.utc)
            db.commit()
            logger.warning(
                "[BioArbitrage] Cleaned up %d orphaned ingestion run(s) from previous crash.",
                len(stale),
            )
    except Exception as exc:
        logger.warning("[BioArbitrage] Stale-run cleanup failed: %s", exc)
    finally:
        db.close()


# ── Periodic background scheduler ────────────────────────────────────────────

async def _run_periodic_ingestion() -> None:
    """
    Background task: run a full ingestion cycle every INGESTION_INTERVAL_HOURS.

    Behaviour:
      - Waits one full interval before the first scheduled run (the startup
        ingestion in _run_startup_ingestion handles the initial population).
      - Uses since_days = interval_hours * 2 (days) as the freshness window so
        each connector only fetches records newer than the last run period,
        with a 2× safety buffer to handle any failed previous cycle.
      - Skips if another run (manual or scheduled) is already in progress
        (DB-backed lock via _ingestion_is_running).
      - Catches asyncio.CancelledError cleanly on shutdown.
      - Never crashes on source failures — all errors are logged and the loop
        continues after the next sleep interval.

    This coroutine is started from lifespan() and cancelled on shutdown.
    """
    from app.database import SessionLocal
    from app.api.ingestion import _ingestion_is_running
    from app.services.ingestion_service import ingestion_service

    interval_seconds = settings.INGESTION_INTERVAL_HOURS * 3600
    # Convert interval to days for the since_days freshness window (2× buffer)
    since_days = max(math.ceil(settings.INGESTION_INTERVAL_HOURS / 12), 1)
    # e.g. 6 hours → since_days=1 (fetches last 2 days with 2× buffer in connectors)
    # e.g. 24 hours → since_days=2

    logger.info(
        "[Scheduler] First run in %d hour(s). "
        "Subsequent runs every %d hour(s) with a %d-day freshness window.",
        settings.INGESTION_INTERVAL_HOURS,
        settings.INGESTION_INTERVAL_HOURS,
        since_days,
    )

    # Wait the full interval before the first scheduled run.
    # The startup ingestion (_run_startup_ingestion) handles first-time population.
    try:
        await asyncio.sleep(interval_seconds)
    except asyncio.CancelledError:
        return   # shutdown before first run — exit cleanly

    while True:
        db = SessionLocal()
        try:
            if _ingestion_is_running(db):
                logger.info(
                    "[Scheduler] Skipping scheduled run — another ingestion is in progress."
                )
            else:
                logger.info(
                    "[Scheduler] Starting scheduled ingestion (since_days=%d).", since_days
                )
                run = await ingestion_service.run(db, since_days=since_days)
                logger.info(
                    "[Scheduler] Scheduled run complete — "
                    "status=%s, new=%d, signals_updated=%d, novel=%d",
                    run.status, run.total_new, run.signals_updated, run.signals_created,
                )
        except asyncio.CancelledError:
            # Shutdown signal received while a run was in progress — exit cleanly.
            # The in-progress run will be cleaned up as stale on next startup.
            logger.info("[Scheduler] Shutdown signal received — stopping scheduler.")
            return
        except Exception as exc:
            # Any other error: log and continue after the next sleep.
            # This ensures a source outage or transient DB error never kills the loop.
            logger.warning("[Scheduler] Scheduled run failed: %s", exc)
        finally:
            db.close()

        # Wait for next interval — catches CancelledError for clean shutdown.
        try:
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("[Scheduler] Shutdown signal received during sleep — stopping.")
            return


# ── Production startup ingestion (first deploy only) ─────────────────────────

async def _run_startup_ingestion() -> None:
    """
    One-shot background task: run a full ingestion pass on the very first
    production deploy (when the database has no live evidence yet).

    Guards:
      - Only fires when APP_ENV = production.
      - Skips immediately if any live evidence already exists.
      - Runs without since_days (full-history) since this is initial population.
      - 8-second delay lets the HTTP server finish binding.
    """
    await asyncio.sleep(8)

    from app.database import SessionLocal
    from app.models.evidence import Evidence
    from app.services.ingestion_service import ingestion_service

    db = SessionLocal()
    try:
        live_count = db.query(Evidence).filter(Evidence.is_demo_data == False).count()
        if live_count > 0:
            logger.info(
                "[BioArbitrage] Startup ingestion skipped — %d live evidence records "
                "already exist.", live_count,
            )
            return

        logger.info(
            "[BioArbitrage] Production first-deploy: no live evidence found — "
            "running full startup ingestion (no date filter)."
        )
        run = await ingestion_service.run(db)   # since_days=None → full history
        logger.info(
            "[BioArbitrage] Startup ingestion complete — "
            "status=%s, new=%d, signals_updated=%d, novel=%d",
            run.status, run.total_new, run.signals_updated, run.signals_created,
        )
    except Exception as exc:
        logger.warning(
            "[BioArbitrage] Startup ingestion failed: %s. "
            "The scheduler will retry in %d hour(s).",
            exc, settings.INGESTION_INTERVAL_HOURS,
        )
    finally:
        db.close()


# ── SQLite schema migrations ──────────────────────────────────────────────────

def _apply_sqlite_migrations() -> None:
    """Idempotent ALTER TABLE additions for SQLite only."""
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
        "name":              "BioArbitrage API",
        "version":           "1.0.0",
        "env":               settings.APP_ENV,
        "status":            "running",
        "docs":              "/docs",
        "scheduler_hours":   settings.INGESTION_INTERVAL_HOURS,
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
    db_ok   = verify_database_connection()
    db_type = "postgresql" if "postgresql" in settings.DATABASE_URL else "sqlite"
    return {
        "status":           "healthy" if db_ok else "degraded",
        "database":         "connected" if db_ok else "unreachable",
        "database_type":    db_type,
        "env":              settings.APP_ENV,
        "demo_seeding":     settings.demo_seeding_enabled,
        "sources":          settings.enabled_sources_list,
        "scheduler_hours":  settings.INGESTION_INTERVAL_HOURS,
    }
