"""
Elsevier connector — uses Scopus Search API.

API:  https://api.elsevier.com/content/search/scopus
Docs: https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl

Authentication: X-ELS-APIKey header (never logged or returned to frontend).

RETRIEVAL STRATEGY:
  Scopus Search API supports offset-based pagination via the 'start' param.
  Each page returns up to 25 records. We page until max_records is reached
  or no further results are available (totalResults exhausted).

  This removes the previous single-page cap.
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

import httpx

from app.services.connectors.base import BaseConnector, NormalizedRecord
from app.config import settings

logger = logging.getLogger(__name__)

_SCOPUS_SEARCH_URL = "https://api.elsevier.com/content/search/scopus"
_PAGE_SIZE = 25


class ElsevierConnector(BaseConnector):
    SOURCE_NAME = "elsevier"

    def __init__(self, timeout: int = 20):
        super().__init__(timeout)
        self._api_key: str = settings.ELSEVIER_API_KEY or ""

    @property
    def _is_configured(self) -> bool:
        return bool(self._api_key)

    def _headers(self) -> dict:
        return {
            "X-ELS-APIKey": self._api_key,
            "Accept":       "application/json",
        }

    # ── Connectivity probe ────────────────────────────────────────────────────

    async def check_connection(self) -> bool:
        detail = await self.check_connection_detail()
        return detail.get("ok", False)

    async def check_connection_detail(self) -> dict:
        if not self._is_configured:
            return {"ok": False, "status_code": None, "reason": "not_configured"}
        try:
            params = {"query": "drug repurposing", "count": 1, "field": "dc:title"}
            async with httpx.AsyncClient(timeout=min(self.timeout, 10)) as client:
                r = await client.get(_SCOPUS_SEARCH_URL, headers=self._headers(), params=params)
                if r.status_code == 200:
                    return {"ok": True, "status_code": 200, "reason": "connected"}
                if r.status_code in (401, 403):
                    return {"ok": False, "status_code": r.status_code, "reason": "invalid_key"}
                if r.status_code == 429:
                    return {"ok": False, "status_code": 429, "reason": "rate_limited"}
                return {"ok": False, "status_code": r.status_code, "reason": f"http_{r.status_code}"}
        except httpx.TimeoutException:
            return {"ok": False, "status_code": None, "reason": "timeout"}
        except Exception as e:
            logger.warning("[Elsevier/Scopus] Connection check failed: %s", type(e).__name__)
            return {"ok": False, "status_code": None, "reason": "error"}

    # ── Main fetch ────────────────────────────────────────────────────────────

    async def fetch(self, query: str, max_records: int = 50) -> List[NormalizedRecord]:
        """
        Search Scopus for articles matching `query`.

        Paginates using 'start' offset until max_records is reached or
        totalResults is exhausted. Never exposes the API key.
        """
        if not self._is_configured or not query or not query.strip():
            return []

        records: List[NormalizedRecord] = []
        start = 0
        total_available = None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                while len(records) < max_records:
                    page_count = min(_PAGE_SIZE, max_records - len(records))
                    params = {
                        "query": f"TITLE-ABS-KEY({query})",
                        "count": page_count,
                        "start": start,
                        "field": (
                            "dc:title,prism:doi,prism:publicationName,"
                            "prism:coverDate,dc:creator,dc:description,"
                            "eid,prism:url"
                        ),
                        "sort": "-coverDate",
                    }
                    try:
                        r = await client.get(
                            _SCOPUS_SEARCH_URL,
                            headers=self._headers(),
                            params=params,
                        )
                        if r.status_code == 429:
                            logger.warning("[Elsevier/Scopus] Rate limited for query %r", query)
                            break
                        if r.status_code in (401, 403):
                            logger.warning("[Elsevier/Scopus] Auth error %d for query %r",
                                           r.status_code, query)
                            break
                        r.raise_for_status()
                    except httpx.TimeoutException:
                        logger.warning("[Elsevier/Scopus] Timeout for query %r", query)
                        break
                    except Exception as e:
                        logger.warning("[Elsevier/Scopus] fetch error: %s", type(e).__name__)
                        break

                    data    = r.json()
                    sr      = data.get("search-results", {})
                    entries = sr.get("entry", [])
                    if not isinstance(entries, list) or not entries:
                        break

                    # Get total results on first page
                    if total_available is None:
                        try:
                            total_available = int(
                                sr.get("opensearch:totalResults", 0)
                            )
                        except (TypeError, ValueError):
                            total_available = 0

                    for entry in entries:
                        rec = self._normalize_entry(entry)
                        if rec:
                            records.append(rec)
                        if len(records) >= max_records:
                            break

                    start += len(entries)
                    # Stop if we've paged through all available results
                    if total_available is not None and start >= total_available:
                        break

                    await asyncio.sleep(0.3)

        except Exception as e:
            logger.warning("[Elsevier/Scopus] unexpected error: %s", type(e).__name__)

        logger.info("[Elsevier/Scopus] Fetched %d records for query %r", len(records), query)
        return records

    # ── Normalise ─────────────────────────────────────────────────────────────

    def _normalize_entry(self, entry: dict) -> Optional[NormalizedRecord]:
        doi = (entry.get("prism:doi") or "").strip() or None
        eid = (entry.get("eid") or "").strip() or None

        if not doi and not eid:
            raw_id = (entry.get("dc:identifier") or "").strip()
            if raw_id.upper().startswith("SCOPUS_ID:"):
                eid = raw_id
            elif raw_id.upper().startswith("DOI:"):
                doi = raw_id[4:].strip()

        source_id = doi or eid
        if not source_id:
            return None

        title = (entry.get("dc:title") or "").strip()
        if not title:
            return None

        abstract_raw = (entry.get("dc:description") or "").strip() or None
        abstract     = self._truncate(abstract_raw)
        pub_date     = self._safe_date(
            entry.get("prism:coverDate") or entry.get("prism:coverDisplayDate")
        )
        journal  = (entry.get("prism:publicationName") or "").strip() or None
        authors: List[str] = []
        creator = (entry.get("dc:creator") or "").strip()
        if creator:
            authors = [creator]

        source_url: Optional[str] = None
        if doi:
            source_url = f"https://doi.org/{doi}"
        elif eid:
            source_url = f"https://www.scopus.com/record/display.uri?eid={eid}&origin=inward"

        return NormalizedRecord(
            source="elsevier",
            source_id=source_id,
            doi=doi,
            source_url=source_url,
            title=self._truncate(title, 495),
            abstract=abstract,
            publication_date=pub_date,
            authors=authors,
            journal=journal,
            evidence_type="research_paper",
            is_demo_data=False,
        )
