"""
Application configuration via environment variables.

Local development:
  Copy backend/.env.example → backend/.env and fill in values.

Production (Render):
  Set all required variables in Render Dashboard → Environment.
  Never commit .env or credentials to source control.

Required for production:
  DATABASE_URL   — PostgreSQL connection string (set in Render Dashboard)
  SECRET_KEY     — strong random string (set in Render Dashboard)
  ALLOWED_ORIGINS — frontend Render URL
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    SECRET_KEY: str = "bioarbitrage-dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Database ─────────────────────────────────────────────────────────────
    # Development default: SQLite file next to main.py
    # Production (Render PostgreSQL): set DATABASE_URL in Render Dashboard
    #   Example: postgresql://user:password@host:5432/dbname
    # Production (Render SQLite persistent disk): sqlite:////data/bioarbitrage.db
    DATABASE_URL: str = "sqlite:///./bioarbitrage.db"

    # ── Demo seeding ─────────────────────────────────────────────────────────
    # Controls whether the auto-seeder runs on empty database.
    #
    # Development (default true):
    #   ENABLE_DEMO_SEED=true  → seed_database() runs when DB is empty
    #
    # Production (must be false):
    #   ENABLE_DEMO_SEED=false → no demo data ever created automatically
    #   An empty production DB stays empty until live ingestion populates it.
    #
    # This flag is the single authoritative control for demo seeding.
    # Setting APP_ENV=production also disables seeding as a safety backstop,
    # but ENABLE_DEMO_SEED=false is the explicit, recommended way.
    ENABLE_DEMO_SEED: bool = True

    # ── AI / LLM ─────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Comma-separated list of allowed frontend origins.
    # Production: set to your Render frontend URL.
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ── Ingestion ────────────────────────────────────────────────────────────
    # PubMed NCBI API key — optional.
    # Without key: 3 req/s limit.  With key: 10 req/s limit.
    # Free registration: https://www.ncbi.nlm.nih.gov/account/
    NCBI_API_KEY: str = ""

    # Elsevier/Scopus API key — required for Elsevier source.
    # Server-side only — never sent to frontend or logged.
    # Free registration: https://dev.elsevier.com/
    ELSEVIER_API_KEY: str = ""

    # Max records fetched per source per query term per run.
    # Increase for broader coverage; decrease for faster runs.
    INGESTION_MAX_RECORDS_PER_SOURCE: int = 50

    # HTTP timeout per individual API request (seconds).
    INGESTION_REQUEST_TIMEOUT: int = 20

    # Comma-separated list of enabled source connectors.
    INGESTION_ENABLED_SOURCES: str = (
        "pubmed,biorxiv,medrxiv,clinicaltrials,elsevier,europepmc,uniprot"
    )

    # Comma-separated default query terms for background/startup ingestion.
    # Users can override per-run via POST /api/ingestion/run { query_terms: [...] }
    # or use POST /api/ingestion/search for dynamic drug+disease queries.
    INGESTION_QUERY_TERMS: str = (
        "drug repurposing,metformin alzheimer,rapamycin aging,"
        "sildenafil neurodegeneration,aspirin alzheimer,"
        "metformin cancer,sildenafil pulmonary hypertension"
    )

    # ── Scheduler ────────────────────────────────────────────────────────────
    # How often the background scheduler triggers a full ingestion cycle.
    #
    # Default: 6 hours.
    # Rationale:
    #   - PubMed indexes new articles once per day (overnight batch).
    #   - bioRxiv/medRxiv post preprints continuously but are a free public API.
    #   - ClinicalTrials.gov updates its search index weekly.
    #   - 6 hours = 4 runs/day → same-day discovery of new publications
    #     without excessive API pressure on any of the 7 sources.
    #   - Reduce to 1–2 hours only if NCBI_API_KEY is set (raises PubMed
    #     rate limit from 3 req/s to 10 req/s).
    #
    # Set to 0 to disable the scheduler entirely (manual-only mode).
    INGESTION_INTERVAL_HOURS: int = 6

    # ── Derived properties ───────────────────────────────────────────────────

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def enabled_sources_list(self) -> List[str]:
        return [s.strip() for s in self.INGESTION_ENABLED_SOURCES.split(",") if s.strip()]

    @property
    def query_terms_list(self) -> List[str]:
        return [t.strip() for t in self.INGESTION_QUERY_TERMS.split(",") if t.strip()]

    @property
    def demo_seeding_enabled(self) -> bool:
        """
        True when demo seeding should run on empty database.
        Both ENABLE_DEMO_SEED and APP_ENV are checked — production is
        always safe even if ENABLE_DEMO_SEED is accidentally left as true.
        """
        if self.APP_ENV == "production":
            return False
        return self.ENABLE_DEMO_SEED

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
