"""
Europe PMC connector using the official Europe PMC REST API v6.

API:  https://www.ebi.ac.uk/europepmc/webservices/rest/search
Docs: https://europepmc.org/RestfulWebService

No API key required — completely free and open.

v6 NOTES (confirmed by live probing August 2026):
  - The endpoint REQUIRES follow_redirects=True in httpx.
  - The Accept: application/json header must be sent explicitly.
  - Sort is specified inline in the query string as sort_date:y.
  - Pagination uses nextCursorMark returned in each response.

RETRIEVAL STRATEGY:
  Paginate using nextCursorMark until all available relevant records are
  fetched or max_records is reached. Each page returns up to 25 records
  (configurable). The provider's documented page-size limit is 1000;
  we use 25 for reliability and add a short inter-page delay.

  This removes the previous single-page limit and retrieves ALL available
  relevant records from the API.
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

import httpx

from app.services.connectors.base import BaseConnector, NormalizedRecord

logger = logging.getLogger(__name__)

_BASE_URL  = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
_PAGE_SIZE = 25    # records per page (provider allows up to 1000)

_PUBTYPE_MAP = {
    "Journal Article":             "research_paper",
    "Review":                      "review_article",
    "Meta-Analysis":               "meta_analysis",
    "Clinical Trial":              "clinical_trial",
    "Preprint":                    "preprint",
    "Case Reports":                "research_paper",
    "Randomized Controlled Trial": "clinical_trial",
    "Systematic Review":           "review_article",
    "Book Chapter":                "review_article",
    "Letter":                      "research_paper",
    "Editorial":                   "research_paper",
}

_HEADERS = {
    "Accept":     "application/json",
    "User-Agent": "BioArbitrage/1.0 (bioarbitrage.research; research-support-tool)",
}


class EuropePMCConnector(BaseConnector):
    """
    Europe PMC research connector — v6 API with full pagination.
    No API key required. Supports any drug/disease/protein/gene query.
    """
    SOURCE_NAME = "europepmc"

    def __init__(self, timeout: int = 20):
        super().__init__(timeout)

    # ── Connectivity probe ────────────────────────────────────────────────────

    async def check_connection(self) -> bool:
        try:
            params = {
                "query":      "drug repurposing",
                "format":     "json",
                "pageSize":   "1",
                "resultType": "lite",
            }
            async with httpx.AsyncClient(
                timeout=min(self.timeout, 10),
                follow_redirects=True,
            ) as client:
                r = await client.get(_BASE_URL, params=params, headers=_HEADERS)
                if r.status_code != 200:
                    return False
                items = r.json().get("resultList", {}).get("result", [])
                return len(items) > 0
        except Exception:
            return False

    # ── Main fetch ────────────────────────────────────────────────────────────

    async def fetch(self, query: str, max_records: int = 50) -> List[NormalizedRecord]:
        """
        Search Europe PMC for articles matching `query`.

        Paginates through all available results using nextCursorMark until
        max_records is reached or the API returns no further pages.

        All metadata fields are extracted: PMID, PMCID, DOI, authors, journal,
        abstract, keywords (from keywordList and MeSH), article type,
        open-access status, and source URL.
        """
        if not query or not query.strip():
            return []

        # sort_date:y appended in query string per v6 documentation
        epmc_query = f"{query.strip()} sort_date:y"

        records: List[NormalizedRecord] = []
        cursor_mark = "*"   # initial cursor

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
            ) as client:
                while len(records) < max_records:
                    params = {
                        "query":       epmc_query,
                        "format":      "json",
                        "pageSize":    str(_PAGE_SIZE),
                        "resultType":  "core",
                        "cursorMark":  cursor_mark,
                    }
                    try:
                        r = await client.get(_BASE_URL, params=params, headers=_HEADERS)
                        r.raise_for_status()
                    except httpx.TimeoutException:
                        logger.warning("[EuropePMC] Timeout for query %r (cursor=%s)",
                                       query, cursor_mark)
                        break
                    except httpx.HTTPStatusError as e:
                        logger.warning("[EuropePMC] HTTP %d for query %r",
                                       e.response.status_code, query)
                        break

                    data = r.json()
                    result_list = data.get("resultList", {})
                    items = result_list.get("result", []) if isinstance(result_list, dict) else []

                    if not isinstance(items, list) or not items:
                        break

                    for item in items:
                        rec = self._normalize(item)
                        if rec:
                            records.append(rec)
                        if len(records) >= max_records:
                            break

                    # Advance cursor; stop if no next cursor returned
                    next_cursor = data.get("nextCursorMark") or ""
                    if not next_cursor or next_cursor == cursor_mark:
                        break
                    cursor_mark = next_cursor
                    await asyncio.sleep(0.2)   # gentle rate-limit compliance

        except Exception as e:
            logger.warning("[EuropePMC] fetch failed for %r: %s", query, type(e).__name__)

        logger.info("[EuropePMC] Fetched %d records for query %r", len(records), query)
        return records

    # ── Normalise one result item ─────────────────────────────────────────────

    def _normalize(self, item: dict) -> Optional[NormalizedRecord]:
        """
        Normalise a Europe PMC v6 result item into a NormalizedRecord.
        Extracts all available metadata; never fabricates identifiers.
        """
        # ── Identifiers ───────────────────────────────────────────────────────
        pmid    = str(item.get("pmid")  or "").strip() or None
        pmcid   = str(item.get("pmcid") or "").strip() or None
        doi     = str(item.get("doi")   or "").strip() or None
        epmc_id = str(item.get("id")    or "").strip() or None
        source_db = str(item.get("source") or "MED").strip()

        source_id = pmid or doi or pmcid or epmc_id
        if not source_id:
            return None

        # ── Title ─────────────────────────────────────────────────────────────
        title = str(item.get("title") or "").strip().rstrip(".")
        if not title:
            return None

        # ── Abstract ──────────────────────────────────────────────────────────
        abstract = self._truncate(str(item.get("abstractText") or "").strip() or None)

        # ── Authors ───────────────────────────────────────────────────────────
        authors: List[str] = []
        author_list_raw = item.get("authorList") or {}
        if isinstance(author_list_raw, dict):
            for a in author_list_raw.get("author", [])[:12]:
                if isinstance(a, dict):
                    name = (a.get("fullName") or a.get("lastName") or "").strip()
                    if name:
                        authors.append(name)
        if not authors:
            author_string = str(item.get("authorString") or "").strip().rstrip(".")
            if author_string:
                authors = [a.strip() for a in author_string.replace(";", ",").split(",") if a.strip()][:12]

        # ── Publication date ──────────────────────────────────────────────────
        ji = item.get("journalInfo") or {}
        raw_date = (
            ji.get("printPublicationDate")
            or ji.get("dateOfPublication")
            or str(item.get("firstPublicationDate") or "")
            or str(item.get("pubYear") or "")
        )
        pub_date = self._safe_date(raw_date.strip() if raw_date else None)

        # ── Journal ───────────────────────────────────────────────────────────
        ji_journal = ji.get("journal") or {}
        journal = (
            ji_journal.get("title")
            or ji.get("journalTitle")
            or item.get("journalTitle")
        )
        if journal:
            journal = journal.strip() or None

        # ── Article type → evidence_type ─────────────────────────────────────
        pub_types_raw = item.get("pubTypeList") or {}
        if isinstance(pub_types_raw, dict):
            pub_type_list = pub_types_raw.get("pubType", [])
        elif isinstance(pub_types_raw, list):
            pub_type_list = pub_types_raw
        else:
            pub_type_list = []
        if not pub_type_list:
            flat_pt = item.get("pubType", "")
            if flat_pt:
                pub_type_list = [flat_pt]

        evidence_type = "research_paper"
        for pt in pub_type_list:
            pt_str = str(pt).strip() if pt else ""
            mapped = _PUBTYPE_MAP.get(pt_str)
            if mapped:
                evidence_type = mapped
                break

        # ── Keywords: keywordList + MeSH fallback ─────────────────────────────
        keyword_list: List[str] = []
        kw_raw = item.get("keywordList") or {}
        if isinstance(kw_raw, dict):
            keyword_list = [
                k.strip() for k in kw_raw.get("keyword", [])
                if isinstance(k, str) and k.strip()
            ]
        if not keyword_list:
            mesh_raw = item.get("meshHeadingList") or {}
            if isinstance(mesh_raw, dict):
                skip_terms = {"humans", "animals", "male", "female", "adult",
                              "aged", "middle aged"}
                for mh in mesh_raw.get("meshHeading", [])[:10]:
                    if isinstance(mh, dict):
                        dn = str(mh.get("descriptorName") or "").strip()
                        if dn and dn.lower() not in skip_terms:
                            keyword_list.append(dn)

        # ── Open access ───────────────────────────────────────────────────────
        is_open_access = item.get("isOpenAccess", "N") == "Y"

        # ── PMCID stored as a keyword for downstream use ──────────────────────
        # Also store it in extracted_mechanisms so pipeline can use it
        extra_keywords = []
        if pmcid:
            extra_keywords.append(f"PMCID:{pmcid}")
        if is_open_access:
            extra_keywords.append("open_access")

        # ── Source URL ────────────────────────────────────────────────────────
        source_url: Optional[str] = None
        full_text_raw = item.get("fullTextUrlList") or {}
        if isinstance(full_text_raw, dict):
            for u in full_text_raw.get("fullTextUrl", []):
                if isinstance(u, dict) and u.get("documentStyle") == "html":
                    href = u.get("url", "")
                    if href:
                        source_url = href
                        break
        if not source_url and doi:
            source_url = f"https://doi.org/{doi}"
        elif not source_url and pmcid:
            clean_id = pmcid.lstrip("PMC")
            source_url = f"https://europepmc.org/article/PMC/{clean_id}"
        elif not source_url and pmid:
            source_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        elif not source_url and epmc_id:
            source_url = f"https://europepmc.org/article/{source_db}/{epmc_id}"

        return NormalizedRecord(
            source="europepmc",
            source_id=source_id,
            pmid=pmid,
            pmcid=pmcid,
            doi=doi,
            source_url=source_url,
            title=self._truncate(title, 495),
            abstract=abstract,
            publication_date=pub_date,
            authors=authors,
            journal=journal,
            evidence_type=evidence_type,
            extracted_mechanisms=(keyword_list + extra_keywords)[:14],
            is_demo_data=False,
        )
