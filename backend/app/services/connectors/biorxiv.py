"""
bioRxiv and medRxiv connectors using the official bioRxiv/medRxiv REST API.

API docs: https://api.biorxiv.org/

Two endpoints are supported, with automatic fallback:

PRIMARY — /details/{server}/{start}/{end}/{cursor}/json
  Returns preprints in a date window.
  Has been observed returning HTTP 200 with empty body during server issues.

FALLBACK — /pubs/{server}/{start}/{end}/{cursor}/json
  Returns preprints that have been published in journals within the date range.
  Different field schema (preprint_doi, preprint_title, etc.).
  Has been confirmed working even when /details returns empty.

The connector tries /details first. If it returns empty body it automatically
falls back to /pubs. If both return empty, status = "unavailable" (not "error").

IMPORTANT:
  - Never fabricates records.
  - Never marks Connected unless a real valid JSON response is received.
  - Preserves existing stored records during outages.
  - Retries with exponential backoff on transient errors (timeout, 5xx).
  - Respects API pagination (cursor-based).
  - Deduplication is handled by the ingestion pipeline (source_id = DOI).
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import date, timedelta
from typing import List, Optional

import httpx

from app.services.connectors.base import BaseConnector, NormalizedRecord

logger = logging.getLogger(__name__)

# Official API base URLs
_DETAILS_BASE = "https://api.biorxiv.org/details"
_PUBS_BASE    = "https://api.biorxiv.org/pubs"

_WINDOW_DAYS  = 90    # sliding window per request
_PAGE_SIZE    = 100   # max records per page (API limit)
_MAX_RETRIES  = 3     # max retries per request
_RETRY_SLEEP  = 1.5   # base seconds (multiplied by attempt number)


def _parse_json_safe(text: str) -> Optional[dict]:
    """Return parsed JSON dict or None on any failure. Never raises."""
    if not text or not text.strip():
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def _is_valid_rxiv_response(data: Optional[dict]) -> bool:
    """Return True only when data is a dict with 'collection' or 'messages' key."""
    if not isinstance(data, dict):
        return False
    return "collection" in data or "messages" in data


class _RxivConnector(BaseConnector):
    """
    Shared logic for bioRxiv and medRxiv.

    Tries /details first, falls back to /pubs automatically.
    Uses instance attribute _last_check_empty_body so check_sources()
    can distinguish 'empty body' (unavailable) from hard errors.
    """

    SOURCE_NAME: str = "biorxiv"
    _SERVER:     str = "biorxiv"

    def __init__(self, timeout: int = 20):
        super().__init__(timeout)
        self._last_check_empty_body: bool = False
        self._last_check_error: Optional[str] = None

    # ── Connectivity probe ────────────────────────────────────────────────────

    async def check_connection(self) -> bool:
        """
        Probe both /details and /pubs for the last 30 days.
        Returns True ONLY when a real valid JSON response is received.

        Each probe uses a 5-second HTTP timeout. Two probes run sequentially
        (/details first, /pubs as fallback), so the total time is at most ~10s
        which fits within the 15-second outer asyncio.wait_for in check_sources().

        Sets self._last_check_empty_body = True when HTTP 200 with empty body
        (server reachable but no data), so check_sources() can distinguish
        'unavailable' from 'error'.
        """
        self._last_check_empty_body = False
        self._last_check_error      = None
        end   = date.today()
        start = end - timedelta(days=30)

        # Try /details first (canonical endpoint)
        result = await self._try_details_probe(start, end)
        if result == "connected":
            return True
        if result == "empty":
            self._last_check_empty_body = True
            # Fall through to /pubs before giving up

        # Fall back to /pubs
        result2 = await self._try_pubs_probe(start, end)
        if result2 == "connected":
            # /pubs is working — clear empty-body flag (we have a working endpoint)
            self._last_check_empty_body = False
            return True
        if result2 == "empty":
            self._last_check_empty_body = True
            self._last_check_error = "Both /details and /pubs returned empty responses"
            return False

        # Hard error on both
        self._last_check_error = f"/details: {result}, /pubs: {result2}"
        return False

    async def _try_details_probe(self, start: date, end: date) -> str:
        """/details probe. Returns 'connected', 'empty', or error string.
        Uses 5s timeout so two sequential probes fit within the outer 15s limit.
        """
        url = f"{_DETAILS_BASE}/{self._SERVER}/{start}/{end}/0/json"
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(url)
            if r.status_code == 429:
                return "rate_limited"
            if r.status_code >= 500:
                return f"http_{r.status_code}"
            if r.status_code != 200:
                return f"http_{r.status_code}"
            data = _parse_json_safe(r.text)
            if data is None:
                return "empty"
            if _is_valid_rxiv_response(data):
                logger.info("[%s] /details probe: OK (collection=%d)",
                            self._SERVER, len(data.get("collection", [])))
                return "connected"
            return "empty"
        except httpx.TimeoutException:
            return "timeout"
        except Exception as e:
            return f"exception:{e}"

    async def _try_pubs_probe(self, start: date, end: date) -> str:
        """/pubs probe. Returns 'connected', 'empty', or error string.
        Uses 5s timeout so two sequential probes fit within the outer 15s limit.
        """
        url = f"{_PUBS_BASE}/{self._SERVER}/{start}/{end}/0/json"
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(url)
            if r.status_code == 429:
                return "rate_limited"
            if r.status_code >= 500:
                return f"http_{r.status_code}"
            if r.status_code != 200:
                return f"http_{r.status_code}"
            data = _parse_json_safe(r.text)
            if data is None:
                return "empty"
            if _is_valid_rxiv_response(data):
                logger.info("[%s] /pubs probe: OK (collection=%d)",
                            self._SERVER, len(data.get("collection", [])))
                return "connected"
            return "empty"
        except httpx.TimeoutException:
            return "timeout"
        except Exception as e:
            return f"exception:{e}"

    # ── Main fetch ────────────────────────────────────────────────────────────

    async def fetch(
        self,
        query: str,
        max_records: int = 50,
        since_days: Optional[int] = None,
    ) -> List[NormalizedRecord]:
        """
        Fetch preprints matching `query` keywords.

        Strategy:
          1. Try /details endpoint (primary).
          2. If /details returns empty body, try /pubs (fallback).
          3. Filter results locally by keyword match in title + abstract.
          4. Paginate until max_records reached or window exhausted.

        since_days: restricts the date window for scheduled runs.
        """
        if not query or not query.strip():
            return []

        keywords = [kw.strip().lower() for kw in query.split() if len(kw.strip()) > 2]
        if not keywords:
            return []

        results: List[NormalizedRecord] = []
        end_date = date.today()

        if since_days:
            window     = max(since_days * 2, 7)
            start_date = end_date - timedelta(days=window)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                results = await self._fetch_window_with_fallback(
                    client, start_date, end_date, keywords, need=max_records
                )
        else:
            max_windows = 8   # 8 × 90 days ≈ 2 years
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for _ in range(max_windows):
                    if len(results) >= max_records:
                        break
                    start_date = end_date - timedelta(days=_WINDOW_DAYS)
                    batch = await self._fetch_window_with_fallback(
                        client, start_date, end_date, keywords,
                        need=max_records - len(results),
                    )
                    results.extend(batch)
                    end_date = start_date - timedelta(days=1)

        return results[:max_records]

    async def _fetch_window_with_fallback(
        self,
        client: httpx.AsyncClient,
        start: date,
        end: date,
        keywords: List[str],
        need: int,
    ) -> List[NormalizedRecord]:
        """Try /details; if it returns empty body, fall back to /pubs."""
        # Attempt /details
        details_results = await self._fetch_window(
            client, start, end, keywords, need, use_pubs=False
        )
        # /details returned something — use it
        if details_results:
            return details_results

        # /details returned nothing. Was it an outage (empty body) or just no matches?
        # Try /pubs as a data-availability check.
        logger.info("[%s] /details returned 0 results for %s–%s, trying /pubs fallback",
                    self._SERVER, start, end)
        pubs_results = await self._fetch_window(
            client, start, end, keywords, need, use_pubs=True
        )
        return pubs_results

    async def _fetch_window(
        self,
        client: httpx.AsyncClient,
        start: date,
        end: date,
        keywords: List[str],
        need: int,
        use_pubs: bool = False,
    ) -> List[NormalizedRecord]:
        """
        Fetch one date-window using either /details or /pubs, with pagination
        and bounded retries with exponential backoff.
        """
        collected: List[NormalizedRecord] = []
        cursor = 0
        base   = _PUBS_BASE if use_pubs else _DETAILS_BASE

        while len(collected) < need:
            url      = f"{base}/{self._SERVER}/{start}/{end}/{cursor}/json"
            data     = None
            last_err = None

            for attempt in range(_MAX_RETRIES):
                try:
                    r = await client.get(url)
                    if r.status_code == 429:
                        wait = _RETRY_SLEEP * (2 ** attempt)
                        logger.warning("[%s] 429 rate-limited, waiting %.1fs (attempt %d/%d)",
                                       self._SERVER, wait, attempt + 1, _MAX_RETRIES)
                        await asyncio.sleep(wait)
                        last_err = "rate_limited"
                        continue
                    if r.status_code >= 500:
                        wait = _RETRY_SLEEP * (2 ** attempt)
                        logger.warning("[%s] HTTP %d, retrying in %.1fs (attempt %d/%d)",
                                       self._SERVER, r.status_code, wait, attempt + 1, _MAX_RETRIES)
                        await asyncio.sleep(wait)
                        last_err = f"http_{r.status_code}"
                        continue
                    if r.status_code != 200:
                        logger.warning("[%s] HTTP %d for %s", self._SERVER, r.status_code, url[:70])
                        last_err = f"http_{r.status_code}"
                        break
                    parsed = _parse_json_safe(r.text)
                    if parsed is None:
                        # Empty body or invalid JSON — server-side issue; no retry useful
                        last_err = "empty_response"
                        break
                    data     = parsed
                    last_err = None
                    break
                except httpx.TimeoutException:
                    wait = _RETRY_SLEEP * (attempt + 1)
                    logger.warning("[%s] timeout cursor=%d attempt=%d/%d, retry in %.1fs",
                                   self._SERVER, cursor, attempt + 1, _MAX_RETRIES, wait)
                    last_err = "timeout"
                    await asyncio.sleep(wait)
                except httpx.RemoteProtocolError as e:
                    wait = _RETRY_SLEEP * (attempt + 1) * 1.5
                    logger.warning("[%s] RemoteProtocolError cursor=%d attempt=%d/%d: %s",
                                   self._SERVER, cursor, attempt + 1, _MAX_RETRIES, e)
                    last_err = "remote_protocol"
                    await asyncio.sleep(wait)
                except Exception as e:
                    logger.warning("[%s] Unexpected error cursor=%d: %s", self._SERVER, cursor, e)
                    last_err = str(e)
                    break

            if data is None:
                if last_err:
                    logger.warning("[%s] Giving up on window %s–%s cursor=%d: %s",
                                   self._SERVER, start, end, cursor, last_err)
                break

            articles = data.get("collection", [])
            if not articles:
                break

            normalizer = self._normalize_pubs if use_pubs else self._normalize_details
            for art in articles:
                rec = normalizer(art)
                if rec and self._matches_keywords(rec, keywords):
                    collected.append(rec)
                    if len(collected) >= need:
                        break

            if len(articles) < _PAGE_SIZE:
                break   # last page

            cursor += _PAGE_SIZE
            await asyncio.sleep(0.3)   # rate-limit compliance

        return collected

    # ── Keyword match ─────────────────────────────────────────────────────────

    def _matches_keywords(self, rec: NormalizedRecord, keywords: List[str]) -> bool:
        """Return True if ANY keyword appears in title or abstract."""
        if not keywords:
            return True
        text = ((rec.title or "") + " " + (rec.abstract or "") +
                " " + (rec.journal or "")).lower()
        return any(kw in text for kw in keywords)

    # ── Normalise /details record ─────────────────────────────────────────────

    def _normalize_details(self, art: dict) -> Optional[NormalizedRecord]:
        """
        Normalise a record from the /details endpoint.
        Fields: doi, title, authors, abstract, date, server
        """
        doi   = (art.get("doi") or "").strip() or None
        title = (art.get("title") or "").strip()
        if not title or not doi:
            return None

        abstract    = self._truncate((art.get("abstract") or "").strip() or None)
        pub_date    = self._safe_date(art.get("date") or art.get("published") or None)
        authors_raw = art.get("authors") or ""
        authors     = [a.strip() for a in str(authors_raw).split(";") if a.strip()][:10]
        server_val  = art.get("server") or self._SERVER
        source_url  = f"https://www.{server_val}.org/content/{doi}v1"

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

    # ── Normalise /pubs record ────────────────────────────────────────────────

    def _normalize_pubs(self, art: dict) -> Optional[NormalizedRecord]:
        """
        Normalise a record from the /pubs endpoint.
        The /pubs endpoint has a different schema to /details:
          preprint_doi, preprint_title, preprint_authors, preprint_abstract,
          preprint_date, preprint_category, preprint_platform,
          published_doi, published_journal, published_date
        We use preprint_doi as the canonical source_id for deduplication
        (same DOI as /details would return), so no double-counting occurs.
        """
        doi   = (art.get("preprint_doi") or "").strip() or None
        title = (art.get("preprint_title") or "").strip()
        if not title or not doi:
            return None

        abstract    = self._truncate((art.get("preprint_abstract") or "").strip() or None)
        pub_date    = self._safe_date(
            art.get("preprint_date") or art.get("published_date") or None
        )
        authors_raw = art.get("preprint_authors") or ""
        authors     = [a.strip() for a in str(authors_raw).split(";") if a.strip()][:10]
        platform    = (art.get("preprint_platform") or self._SERVER).lower()
        source_url  = f"https://www.{platform}.org/content/{doi}v1"

        # If the preprint has been published, record the journal
        pub_journal = art.get("published_journal") or ""
        pub_doi     = (art.get("published_doi") or "").strip() or None
        category    = art.get("preprint_category") or ""
        journal_str = (
            f"{pub_journal} (published)" if pub_journal
            else f"{platform.capitalize()} [Preprint]"
        )
        if category:
            journal_str = f"{journal_str} · {category}"

        return NormalizedRecord(
            source=self._SERVER,
            source_id=doi,           # preprint DOI — same as /details, ensures dedup
            doi=doi,
            source_url=source_url,
            title=self._truncate(title, 495),
            abstract=abstract,
            publication_date=pub_date,
            authors=authors,
            journal=self._truncate(journal_str, 250),
            evidence_type="preprint",
            is_demo_data=False,
        )


class BioRxivConnector(_RxivConnector):
    SOURCE_NAME = "biorxiv"
    _SERVER     = "biorxiv"


class MedRxivConnector(_RxivConnector):
    SOURCE_NAME = "medrxiv"
    _SERVER     = "medrxiv"
