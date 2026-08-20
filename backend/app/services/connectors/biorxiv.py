"""
bioRxiv and medRxiv connectors using the official bioRxiv/medRxiv REST API.

API docs: https://api.biorxiv.org/
Endpoints:
  Date-range:   https://api.biorxiv.org/details/{server}/{interval}/{cursor}/json
  DOI lookup:   https://api.biorxiv.org/details/{server}/{doi}/na/json

No API key required — completely open and free.

RETRIEVAL STRATEGY:
  The bioRxiv/medRxiv API does not support full-text keyword search directly.
  It returns articles in date-window slices. We use a sliding 90-day window
  (configurable) and filter results by keyword relevance locally.

  For thorough retrieval we paginate through each window's pages (cursor-based).
  The API returns up to 100 records per page; we page until exhausted or
  max_records is reached.

  This removes the previous hard 14-day restriction — the window now extends
  back as far as needed to accumulate max_records relevant results.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date, timedelta
from typing import List

import httpx

from app.services.connectors.base import BaseConnector, NormalizedRecord

logger = logging.getLogger(__name__)

BIORXIV_BASE = "https://api.biorxiv.org/details"

# Sliding window size per API call; multiple windows are used to hit max_records
_WINDOW_DAYS = 90
_PAGE_SIZE   = 100   # max the API allows per page


class _RxivConnector(BaseConnector):
    """Shared logic for bioRxiv and medRxiv."""

    SOURCE_NAME: str = "biorxiv"
    _SERVER:     str = "biorxiv"

    def __init__(self, timeout: int = 20):
        super().__init__(timeout)

    # ── Connectivity probe ────────────────────────────────────────────────────

    async def check_connection(self) -> bool:
        """
        Check API reachability. Uses a 7-day window — just verifies HTTP 200.
        An empty collection is acceptable; we only need to know the endpoint responds.
        """
        end   = date.today()
        start = end - timedelta(days=7)
        url   = f"{BIORXIV_BASE}/{self._SERVER}/{start}/{end}/0/json"
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                r = await client.get(url)
                if r.status_code != 200:
                    return False
                data = r.json()
                return "collection" in data or "messages" in data
        except Exception:
            return False

    # ── Main fetch ────────────────────────────────────────────────────────────

    async def fetch(self, query: str, max_records: int = 50) -> List[NormalizedRecord]:
        """
        Fetch preprints matching `query` keywords.

        Strategy:
          1. Build query keywords from the query string.
          2. Slide a window back in time, fetching pages until we have
             enough relevant results or have exhausted 2 years of history.
          3. Each page is filtered locally by keyword match in title/abstract.
        """
        if not query or not query.strip():
            return []

        keywords = [kw.strip().lower() for kw in query.split() if len(kw.strip()) > 2]
        if not keywords:
            return []

        results: List[NormalizedRecord] = []
        end_date   = date.today()
        max_windows = 8   # 8 × 90 days ≈ 2 years

        # Share one client across all windows to avoid TCP reconnect overhead
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for _ in range(max_windows):
                if len(results) >= max_records:
                    break
                start_date = end_date - timedelta(days=_WINDOW_DAYS)
                window_results = await self._fetch_window(
                    client, start_date, end_date, keywords,
                    need=max_records - len(results),
                )
                results.extend(window_results)
                end_date = start_date - timedelta(days=1)

        return results[:max_records]

    async def _fetch_window(
        self,
        client: httpx.AsyncClient,
        start: date,
        end: date,
        keywords: List[str],
        need: int,
    ) -> List[NormalizedRecord]:
        """
        Fetch one date-window, paginating through all cursor pages until
        we have enough relevant results or the window is exhausted.
        """
        collected: List[NormalizedRecord] = []
        cursor = 0

        while len(collected) < need:
            url = f"{BIORXIV_BASE}/{self._SERVER}/{start}/{end}/{cursor}/json"
            try:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
            except httpx.TimeoutException:
                logger.warning("[%s] timeout for window %s–%s cursor %d",
                               self._SERVER, start, end, cursor)
                break
            except Exception as e:
                logger.warning("[%s] error for window %s–%s cursor %d: %s",
                               self._SERVER, start, end, cursor, e)
                break

            articles = data.get("collection", [])
            if not articles:
                break  # no more data in this window

            for art in articles:
                rec = self._normalize(art)
                if rec and self._matches_keywords(rec, keywords):
                    collected.append(rec)
                    if len(collected) >= need:
                        break

            # Pagination: each page has _PAGE_SIZE records; stop when fewer returned
            if len(articles) < _PAGE_SIZE:
                break  # last page of this window

            cursor += _PAGE_SIZE
            await asyncio.sleep(0.3)   # gentle rate-limit compliance

        return collected

    # ── Keyword match ─────────────────────────────────────────────────────────

    def _matches_keywords(self, rec: NormalizedRecord, keywords: List[str]) -> bool:
        """Return True if ANY keyword appears in title or abstract."""
        if not keywords:
            return True
        text = ((rec.title or "") + " " + (rec.abstract or "")).lower()
        return any(kw in text for kw in keywords)

    # ── Normalise one article dict ────────────────────────────────────────────

    def _normalize(self, art: dict) -> NormalizedRecord | None:
        doi   = (art.get("doi") or "").strip() or None
        title = (art.get("title") or "").strip()
        if not title or not doi:
            return None

        abstract   = self._truncate((art.get("abstract") or "").strip() or None)
        pub_date   = self._safe_date(art.get("date") or art.get("published") or None)
        authors_raw = art.get("authors") or ""
        authors    = [a.strip() for a in str(authors_raw).split(";") if a.strip()][:10]
        server_val = art.get("server") or self._SERVER
        source_url = f"https://www.{server_val}.org/content/{doi}v1"

        return NormalizedRecord(
            source=self._SERVER,
            source_id=doi,
            doi=doi,
            source_url=source_url,
            title=self._truncate(title, 495),
            abstract=abstract,
            publication_date=pub_date,
            authors=authors,
            journal=f"{server_val.capitalize()} [Preprint]",
            evidence_type="preprint",
            is_demo_data=False,
        )


class BioRxivConnector(_RxivConnector):
    SOURCE_NAME = "biorxiv"
    _SERVER     = "biorxiv"


class MedRxivConnector(_RxivConnector):
    SOURCE_NAME = "medrxiv"
    _SERVER     = "medrxiv"
