from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = "bioarbitrage-dev-secret-key-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DATABASE_URL: str = "sqlite:///./bioarbitrage.db"

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ── Ingestion settings ───────────────────────────────────────────────────
    # All sources use only public/free APIs — no API key required by default.
    # PubMed NCBI API key is optional but increases rate limit from 3→10 req/s.
    NCBI_API_KEY: str = ""                  # optional — https://www.ncbi.nlm.nih.gov/account/
    ELSEVIER_API_KEY: str = ""              # required for Elsevier/Scopus — server-side only, never sent to frontend

    # Max records retrieved per source per query term.
    # Increase this value (e.g. 100) to retrieve more records per run.
    # Each connector paginates until this limit is reached or results exhausted.
    INGESTION_MAX_RECORDS_PER_SOURCE: int = 50

    # HTTP timeout per individual API request (seconds)
    INGESTION_REQUEST_TIMEOUT: int = 20

    INGESTION_ENABLED_SOURCES: str = (
        "pubmed,biorxiv,medrxiv,clinicaltrials,elsevier,europepmc,uniprot"
    )

    # Default background query terms — these drive the scheduled/batch ingestion.
    # Format: comma-separated free-text queries.
    # Users can also trigger on-demand ingestion with custom drug+disease queries
    # via POST /api/ingestion/run  { "drug": "...", "disease": "..." }
    # These default terms are ONLY used when no custom query is provided.
    INGESTION_QUERY_TERMS: str = (
        "drug repurposing,metformin alzheimer,rapamycin aging,"
        "sildenafil neurodegeneration,aspirin alzheimer,"
        "metformin cancer,sildenafil pulmonary hypertension"
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def enabled_sources_list(self) -> List[str]:
        return [s.strip() for s in self.INGESTION_ENABLED_SOURCES.split(",") if s.strip()]

    @property
    def query_terms_list(self) -> List[str]:
        return [t.strip() for t in self.INGESTION_QUERY_TERMS.split(",") if t.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
