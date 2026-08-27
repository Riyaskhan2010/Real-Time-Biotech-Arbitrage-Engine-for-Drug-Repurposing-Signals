"""
Connector registry for BioArbitrage research source adapters.

Adding a new connector (e.g. Crossref, Semantic Scholar):
  1. Create backend/app/services/connectors/crossref.py
     implementing BaseConnector with fetch() and check_connection().
  2. Import and register it here:
       from .crossref import CrossrefConnector
       register("crossref", CrossrefConnector)
  3. Add its name to INGESTION_ENABLED_SOURCES in .env / Render Dashboard.

That's it. ingestion_service.py discovers connectors automatically via
get_registry() — no changes required there.
"""
from __future__ import annotations

from typing import Dict, Type

from app.services.connectors.base import BaseConnector, NormalizedRecord, SourceResult
from app.services.connectors.pubmed import PubMedConnector
from app.services.connectors.biorxiv import BioRxivConnector, MedRxivConnector
from app.services.connectors.clinicaltrials import ClinicalTrialsConnector
from app.services.connectors.elsevier import ElsevierConnector
from app.services.connectors.europepmc import EuropePMCConnector
from app.services.connectors.uniprot import UniProtConnector

# ── Connector registry ────────────────────────────────────────────────────────
# Maps source name (must match INGESTION_ENABLED_SOURCES value) → connector class.
# ingestion_service._build_connectors() reads this dict — register new connectors
# here and they are picked up automatically on the next server restart.

_REGISTRY: Dict[str, Type[BaseConnector]] = {}


def register(name: str, cls: Type[BaseConnector]) -> None:
    """Register a connector class under the given source name."""
    _REGISTRY[name] = cls


def get_registry() -> Dict[str, Type[BaseConnector]]:
    """Return a copy of the current connector registry."""
    return dict(_REGISTRY)


# ── Register all built-in connectors ─────────────────────────────────────────
register("pubmed",         PubMedConnector)
register("biorxiv",        BioRxivConnector)
register("medrxiv",        MedRxivConnector)
register("clinicaltrials", ClinicalTrialsConnector)
register("elsevier",       ElsevierConnector)
register("europepmc",      EuropePMCConnector)
register("uniprot",        UniProtConnector)


__all__ = [
    "BaseConnector",
    "NormalizedRecord",
    "SourceResult",
    "PubMedConnector",
    "BioRxivConnector",
    "MedRxivConnector",
    "ClinicalTrialsConnector",
    "ElsevierConnector",
    "EuropePMCConnector",
    "UniProtConnector",
    "register",
    "get_registry",
]
