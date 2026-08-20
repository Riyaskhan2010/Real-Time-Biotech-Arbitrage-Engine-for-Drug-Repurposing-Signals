"""
Base connector contract for all research source adapters.

Every connector must:
  - implement fetch(query, max_records) → list[NormalizedRecord]
  - implement check_connection() → bool
  - never raise on network failure — return empty list + set status
  - never fabricate identifiers — null fields stay null

IMPORTANT: This is a RESEARCH DECISION-SUPPORT tool.
All ingested records are presented as research metadata only.
Not for clinical use or treatment recommendations.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class NormalizedRecord:
    """
    Common internal representation for all research sources.
    Fields that cannot be populated for a given source remain None.
    No identifiers are fabricated — if unavailable, the field is None.
    """
    # Source provenance (required)
    source: str           # pubmed | biorxiv | medrxiv | clinicaltrials
    source_id: str        # unique ID within source (PMID, DOI, NCT, etc.)
    source_url: Optional[str] = None

    # Content
    title: str = ""
    abstract: Optional[str] = None
    publication_date: Optional[str] = None  # YYYY-MM-DD or YYYY-MM or YYYY
    authors: List[str] = field(default_factory=list)
    journal: Optional[str] = None

    # Identifiers — only populated when genuinely available
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    nct_id: Optional[str] = None

    # Evidence classification
    evidence_type: str = "research_paper"
    # research_paper | preprint | clinical_trial | review_article

    # Extracted entities (populated by ingestion service, not connector)
    extracted_drugs: List[str] = field(default_factory=list)
    extracted_diseases: List[str] = field(default_factory=list)
    extracted_mechanisms: List[str] = field(default_factory=list)

    # Ingestion metadata
    ingested_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    is_demo_data: bool = False


@dataclass
class SourceResult:
    """Result summary for one source after a fetch attempt."""
    source: str
    status: str          # connected | empty | error | timeout | rate_limited | disabled
    records_fetched: int = 0
    records_new: int = 0
    records_duplicate: int = 0
    error_message: Optional[str] = None
    elapsed_seconds: float = 0.0


class BaseConnector(ABC):
    """Abstract base for all research source connectors."""

    SOURCE_NAME: str = "unknown"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    @abstractmethod
    async def fetch(
        self,
        query: str,
        max_records: int = 20,
    ) -> List[NormalizedRecord]:
        """
        Fetch and normalize records for `query`.
        Must return [] (not raise) on any network/API failure.
        Must never fabricate identifiers or content.
        """

    @abstractmethod
    async def check_connection(self) -> bool:
        """
        Lightweight connectivity probe — returns True if source is reachable.
        Must complete within self.timeout seconds.
        """

    @staticmethod
    def _safe_date(raw: Optional[str]) -> Optional[str]:
        """Normalise a date string to YYYY-MM-DD, YYYY-MM, or YYYY.  Returns None if unparseable."""
        if not raw:
            return None
        raw = raw.strip()
        # Map expected data length → format string
        for data_len, fmt in [(10, "%Y-%m-%d"), (7, "%Y-%m"), (4, "%Y")]:
            if len(raw) >= data_len:
                try:
                    return datetime.strptime(raw[:data_len], fmt).strftime(fmt)
                except ValueError:
                    continue
        # Try extracting 4-digit year
        import re
        m = re.search(r"\b(19|20)\d{2}\b", raw)
        return m.group(0) if m else None

    @staticmethod
    def _truncate(text: Optional[str], max_len: int = 2000) -> Optional[str]:
        if text and len(text) > max_len:
            return text[:max_len] + "…"
        return text
