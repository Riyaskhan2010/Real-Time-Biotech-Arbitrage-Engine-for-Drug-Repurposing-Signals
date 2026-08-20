"""
PubMed connector using the NCBI E-utilities API (free, public).

API docs: https://www.ncbi.nlm.nih.gov/books/NBK25499/

Rate limits:
  - Without API key: 3 requests/second
  - With NCBI_API_KEY: 10 requests/second

No API key is required. Set NCBI_API_KEY in .env to increase rate limit.

RETRIEVAL STRATEGY:
  1. esearch — get total hit count and first batch of PMIDs.
  2. Paginate esearch until all PMIDs (up to max_records) are collected.
  3. efetch — retrieve full XML records in batches of 20.
  4. Parse XML: title, abstract, authors, journal, pub-date, DOI, PMID.

  This removes the previous single-page cap and retrieves ALL available
  relevant records up to max_records.
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Optional
from xml.etree import ElementTree as ET

import httpx

from app.services.connectors.base import BaseConnector, NormalizedRecord
from app.config import settings

logger = logging.getLogger(__name__)

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
EINFO_URL   = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi"

_FETCH_BATCH = 20   # PMIDs per efetch request (safe max)


class PubMedConnector(BaseConnector):
    SOURCE_NAME = "pubmed"

    def __init__(self, timeout: int = 20):
        super().__init__(timeout)
        self._api_key = settings.NCBI_API_KEY or None

    def _base_params(self) -> dict:
        p = {"retmode": "json"}
        if self._api_key:
            p["api_key"] = self._api_key
        return p

    # ── Connectivity probe ────────────────────────────────────────────────────

    async def check_connection(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(EINFO_URL, params={"retmode": "json"})
                return r.status_code == 200
        except Exception:
            return False

    # ── Main fetch ────────────────────────────────────────────────────────────

    async def fetch(self, query: str, max_records: int = 50) -> List[NormalizedRecord]:
        """
        Search PubMed for articles matching `query`.

        Paginates through esearch results to collect up to max_records PMIDs,
        then fetches full records in batches. Rate-limited to comply with
        NCBI's 3 req/s (10 with API key) limit.
        """
        if not query or not query.strip():
            return []
        try:
            pmids = await self._collect_pmids(query, max_records)
            if not pmids:
                return []
            return await self._fetch_details_batched(pmids)
        except Exception as e:
            logger.warning("[PubMed] fetch failed for %r: %s", query, e)
            return []

    # ── Collect PMIDs via paginated esearch ───────────────────────────────────

    async def _collect_pmids(self, query: str, max_records: int) -> List[str]:
        """
        Run esearch and paginate through all result pages to collect up to
        max_records PMIDs. NCBI allows retmax up to 10000; we use 100 per
        page to stay conservative and avoid timeouts.
        """
        all_pmids: List[str] = []
        page_size = 100
        retstart  = 0

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            while len(all_pmids) < max_records:
                params = {
                    **self._base_params(),
                    "db":       "pubmed",
                    "term":     query,
                    "retmax":   min(page_size, max_records - len(all_pmids)),
                    "retstart": retstart,
                    "sort":     "relevance",
                }
                try:
                    r = await client.get(ESEARCH_URL, params=params)
                    r.raise_for_status()
                    data = r.json()
                except Exception as e:
                    logger.warning("[PubMed] esearch error for %r: %s", query, e)
                    break

                result = data.get("esearchresult", {})
                batch  = result.get("idlist", [])
                if not batch:
                    break

                all_pmids.extend(batch)
                total_available = int(result.get("count", 0))

                # Stop if we have enough or there are no more results
                if len(all_pmids) >= max_records or len(all_pmids) >= total_available:
                    break

                retstart += len(batch)
                # Respect NCBI rate limit: 3 req/s without key, 10 with key
                delay = 0.12 if self._api_key else 0.4
                await asyncio.sleep(delay)

        return all_pmids[:max_records]

    # ── Fetch full records in batches ─────────────────────────────────────────

    async def _fetch_details_batched(self, pmids: List[str]) -> List[NormalizedRecord]:
        """Fetch full XML records in batches of _FETCH_BATCH PMIDs each."""
        records: List[NormalizedRecord] = []
        for i in range(0, len(pmids), _FETCH_BATCH):
            batch = pmids[i: i + _FETCH_BATCH]
            batch_records = await self._fetch_details(batch)
            records.extend(batch_records)
            if len(pmids) > _FETCH_BATCH:
                delay = 0.12 if self._api_key else 0.4
                await asyncio.sleep(delay)
        return records

    async def _fetch_details(self, pmids: List[str]) -> List[NormalizedRecord]:
        if not pmids:
            return []
        params = {
            **self._base_params(),
            "db":      "pubmed",
            "id":      ",".join(pmids),
            "rettype": "xml",
            "retmode": "xml",
        }
        params.pop("retmode", None)
        params["retmode"] = "xml"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(EFETCH_URL, params=params)
                r.raise_for_status()
                xml_text = r.text
        except Exception as e:
            logger.warning("[PubMed] efetch error for %d PMIDs: %s", len(pmids), e)
            return []

        return self._parse_pubmed_xml(xml_text)

    # ── XML parsing ───────────────────────────────────────────────────────────

    def _parse_pubmed_xml(self, xml_text: str) -> List[NormalizedRecord]:
        records: List[NormalizedRecord] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.warning("[PubMed] XML parse error: %s", e)
            return records

        for article in root.findall(".//PubmedArticle"):
            try:
                rec = self._parse_article(article)
                if rec:
                    records.append(rec)
            except Exception as e:
                logger.debug("[PubMed] skipping article: %s", e)

        return records

    def _parse_article(self, article: ET.Element) -> Optional[NormalizedRecord]:
        medline = article.find("MedlineCitation")
        if medline is None:
            return None

        pmid_el = medline.find("PMID")
        pmid = pmid_el.text.strip() if pmid_el is not None and pmid_el.text else None
        if not pmid:
            return None

        art = medline.find("Article")
        if art is None:
            return None

        title_el = art.find("ArticleTitle")
        title = "".join(title_el.itertext()).strip() if title_el is not None else ""
        if not title:
            return None

        abstract_parts = []
        for ab in art.findall(".//AbstractText"):
            text  = "".join(ab.itertext()).strip()
            label = ab.get("Label")
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
        abstract = " ".join(abstract_parts) or None

        pub_date = None
        for date_el_path in [".//PubDate", ".//ArticleDate", ".//PubMedPubDate"]:
            date_el = art.find(date_el_path) or medline.find(date_el_path)
            if date_el is not None:
                year  = (date_el.findtext("Year")  or "").strip()
                month = (date_el.findtext("Month") or "").strip()
                day   = (date_el.findtext("Day")   or "").strip()
                if year:
                    month_map = {
                        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                        "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                        "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
                    }
                    m = month_map.get(month[:3].capitalize(), month.zfill(2)) if month else ""
                    raw = year
                    if m:
                        raw = f"{year}-{m}"
                        if day:
                            raw = f"{year}-{m}-{day.zfill(2)}"
                    pub_date = self._safe_date(raw)
                    break

        authors: List[str] = []
        for author_el in art.findall(".//Author"):
            last = (author_el.findtext("LastName") or "").strip()
            fore = (author_el.findtext("ForeName") or author_el.findtext("Initials") or "").strip()
            if last:
                authors.append(f"{last} {fore}".strip())

        journal_el = art.find(".//Journal/Title") or art.find(".//Journal/ISOAbbreviation")
        journal = journal_el.text.strip() if journal_el is not None and journal_el.text else None

        doi = None
        for aid in article.findall(".//ArticleId"):
            if aid.get("IdType") == "doi" and aid.text:
                doi = aid.text.strip()

        return NormalizedRecord(
            source="pubmed",
            source_id=pmid,
            pmid=pmid,
            doi=doi,
            source_url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            title=self._truncate(title, 495),
            abstract=self._truncate(abstract),
            publication_date=pub_date,
            authors=authors[:10],
            journal=journal,
            evidence_type="research_paper",
            is_demo_data=False,
        )
