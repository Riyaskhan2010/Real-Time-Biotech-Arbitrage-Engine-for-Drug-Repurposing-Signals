"""
UniProt connector using the official UniProt REST API.

API:  https://rest.uniprot.org/uniprotkb/search
Docs: https://www.uniprot.org/help/api

No API key required — completely free and open.

RETRIEVAL STRATEGY:
  UniProt is a protein/gene/biological-target database. Queries are
  constructed from drug names, disease names, gene names, or protein names.

  The connector paginates through all available results using the Link header
  (next-page cursor) until max_records is reached or results are exhausted.

  Evidence type: "protein_annotation"
  Scoring: protein_annotation records count toward Research Evidence.

ENTITY MATCHING FIX:
  Previously UniProt records went unmatched because entity extraction
  couldn't find drug names in protein text. The connector now carries
  the original query terms as `extracted_drugs` / `extracted_diseases`
  directly on the NormalizedRecord. The ingestion service uses these
  pre-populated fields for drug/disease matching, bypassing the need
  for heuristic text extraction on protein descriptions.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import httpx

from app.services.connectors.base import BaseConnector, NormalizedRecord

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://rest.uniprot.org/uniprotkb/search"

_HEADERS = {
    "Accept":     "application/json",
    "User-Agent": "BioArbitrage/1.0 (bioarbitrage.research; research-support-tool)",
}

_PAGE_SIZE = 25   # records per API page


class UniProtConnector(BaseConnector):
    """
    UniProt protein/gene database connector.
    Returns curated biological annotations as research context.
    No API key required. Paginates via Link header cursor.
    """
    SOURCE_NAME = "uniprot"

    def __init__(self, timeout: int = 20):
        super().__init__(timeout)

    # ── Connectivity probe ────────────────────────────────────────────────────

    async def check_connection(self) -> bool:
        try:
            params = {"query": "TP53", "format": "json", "size": "1"}
            async with httpx.AsyncClient(
                timeout=min(self.timeout, 10),
                follow_redirects=True,
            ) as client:
                r = await client.get(_SEARCH_URL, params=params, headers=_HEADERS)
                if r.status_code != 200:
                    return False
                return len(r.json().get("results", [])) > 0
        except Exception:
            return False

    # ── Main fetch ────────────────────────────────────────────────────────────

    async def fetch(self, query: str, max_records: int = 25) -> List[NormalizedRecord]:
        """
        Search UniProt for proteins/genes related to `query`.

        The query is passed directly to UniProt full-text search, which
        searches protein names, gene names, functions, disease associations,
        and keywords. Any drug name, disease name, gene, or protein works.

        FIX: We parse drug/disease hints from the query and carry them
        on each NormalizedRecord.extracted_drugs / .extracted_diseases so
        the ingestion pipeline can match without relying on heuristic
        entity extraction of protein description text.
        """
        if not query or not query.strip():
            return []

        # Parse query hints for entity matching
        drug_hints, disease_hints = _parse_query_hints(query)

        records: List[NormalizedRecord] = []
        params = {
            "query":  query.strip(),
            "format": "json",
            "size":   str(_PAGE_SIZE),
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
            ) as client:
                while len(records) < max_records:
                    r = await client.get(_SEARCH_URL, params=params, headers=_HEADERS)
                    r.raise_for_status()
                    data = r.json()
                    results = data.get("results", [])
                    if not isinstance(results, list) or not results:
                        break

                    for entry in results:
                        rec = self._normalize(entry, drug_hints, disease_hints)
                        if rec:
                            records.append(rec)
                        if len(records) >= max_records:
                            break

                    # Pagination via Link header
                    next_cursor = _extract_next_cursor(r.headers.get("Link", ""))
                    if not next_cursor or len(records) >= max_records:
                        break
                    params = {
                        "query":  query.strip(),
                        "format": "json",
                        "size":   str(_PAGE_SIZE),
                        "cursor": next_cursor,
                    }

        except httpx.TimeoutException:
            logger.warning("[UniProt] Timeout for query %r", query)
        except Exception as e:
            logger.warning("[UniProt] fetch failed for %r: %s", query, type(e).__name__)

        logger.info("[UniProt] Fetched %d records for query %r", len(records), query)
        return records

    # ── Normalise one entry ───────────────────────────────────────────────────

    def _normalize(
        self,
        entry: dict,
        drug_hints: List[str],
        disease_hints: List[str],
    ) -> Optional[NormalizedRecord]:
        """
        Normalise a UniProt entry into a NormalizedRecord.
        drug_hints / disease_hints are propagated from the original query
        so the ingestion service can match without text-based extraction.
        """
        accession = (entry.get("primaryAccession") or "").strip()
        if not accession:
            return None

        entry_name = (entry.get("uniProtkbId") or "").strip()

        # ── Protein name ──────────────────────────────────────────────────────
        protein_desc = entry.get("proteinDescription") or {}
        recommended_name = protein_desc.get("recommendedName") or {}
        full_name_obj = recommended_name.get("fullName") or {}
        protein_full = (full_name_obj.get("value") or "").strip()
        title = protein_full or entry_name or accession
        if not title:
            return None

        # ── Gene names ────────────────────────────────────────────────────────
        gene_names: List[str] = []
        for g in entry.get("genes", []):
            primary = (g.get("geneName") or {}).get("value", "").strip()
            if primary:
                gene_names.append(primary)
            for syn in g.get("synonyms", []):
                v = (syn.get("value") or "").strip()
                if v and v not in gene_names:
                    gene_names.append(v)

        # ── Organism ──────────────────────────────────────────────────────────
        organism = entry.get("organism") or {}
        org_scientific = (organism.get("scientificName") or "").strip()
        org_common     = (organism.get("commonName")     or "").strip()
        org_display    = org_common or org_scientific or None

        # ── Abstract: FUNCTION + DISEASE + SUBCELLULAR LOCATION ──────────────
        abstract_parts: List[str] = []
        disease_names:  List[str] = []

        for comment in entry.get("comments", []):
            ctype = comment.get("commentType", "")

            if ctype == "FUNCTION":
                for txt in comment.get("texts", [])[:1]:
                    val = (txt.get("value") or "").strip()
                    if val:
                        abstract_parts.append(f"Function: {val[:500]}")

            elif ctype == "DISEASE":
                d_info = comment.get("disease") or {}
                dn = (d_info.get("diseaseName") or "").strip()
                if dn:
                    disease_names.append(dn)
                    abstract_parts.append(f"Associated disease: {dn}")
                for txt in comment.get("texts", [])[:1]:
                    val = (txt.get("value") or "").strip()
                    if val and len(abstract_parts) < 6:
                        abstract_parts.append(val[:300])

            elif ctype == "SUBCELLULAR LOCATION":
                locs: List[str] = []
                for loc in comment.get("subcellularLocations", [])[:3]:
                    loc_name = (loc.get("location") or {}).get("value", "").strip()
                    if loc_name:
                        locs.append(loc_name)
                if locs:
                    abstract_parts.append(f"Location: {', '.join(locs)}")

        abstract = self._truncate(" | ".join(abstract_parts) if abstract_parts else None)

        # ── Keywords ──────────────────────────────────────────────────────────
        kw_objects: List[str] = []
        for kw in entry.get("keywords", [])[:10]:
            name = (kw.get("name") or "").strip()
            if name:
                kw_objects.append(name)

        # ── GO terms ──────────────────────────────────────────────────────────
        go_terms: List[str] = []
        for xref in entry.get("uniProtKBCrossReferences", []):
            if xref.get("database") == "GO":
                for prop in xref.get("properties", []):
                    if prop.get("key") == "GoTerm":
                        term = (prop.get("value") or "").strip()
                        if ":" in term:
                            term = term.split(":", 1)[1].strip()
                        if term and term not in go_terms:
                            go_terms.append(term)
                        if len(go_terms) >= 8:
                            break

        # ── Sequence length ───────────────────────────────────────────────────
        seq_len = None
        seq = entry.get("sequence") or {}
        if isinstance(seq, dict):
            seq_len = seq.get("length")

        # ── Review status ─────────────────────────────────────────────────────
        entry_type = entry.get("entryType", "")
        is_reviewed = "reviewed" in entry_type.lower()

        # ── Combined keywords for pipeline ────────────────────────────────────
        all_keywords = list(dict.fromkeys(
            gene_names + disease_names + kw_objects[:6] + go_terms[:4]
        ))

        # ── Display title ──────────────────────────────────────────────────────
        display_title = title
        if gene_names:
            display_title = f"{gene_names[0]}: {title}"
        if org_display and org_display.lower() not in ("human", "homo sapiens"):
            display_title = f"{display_title} [{org_display}]"

        # ── Journal = review status + length ──────────────────────────────────
        journal_str = "UniProt/Swiss-Prot (reviewed)" if is_reviewed else "UniProt/TrEMBL (automated)"
        if seq_len:
            journal_str += f" · {seq_len} aa"

        # ── KEY FIX: carry query-derived drug/disease hints ───────────────────
        # These allow ingestion service to match UniProt records to signals
        # without relying on heuristic text extraction of protein descriptions.
        # Merge with any diseases found in the entry itself.
        merged_diseases = list(dict.fromkeys(disease_hints + disease_names[:3]))

        return NormalizedRecord(
            source="uniprot",
            source_id=accession,
            doi=None,
            pmid=None,
            source_url=f"https://www.uniprot.org/uniprot/{accession}",
            title=self._truncate(display_title, 495),
            abstract=abstract,
            publication_date=None,
            authors=[org_scientific] if org_scientific else [],
            journal=journal_str,
            evidence_type="protein_annotation",
            extracted_drugs=drug_hints,           # ← propagated from query
            extracted_diseases=merged_diseases,    # ← query hints + entry diseases
            extracted_mechanisms=all_keywords[:12],
            is_demo_data=False,
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_query_hints(query: str) -> Tuple[List[str], List[str]]:
    """
    Parse the ingestion query string into drug and disease hint lists.
    Supports structured "drug:X disease:Y" format and unstructured free text.

    For unstructured queries, splits into individual tokens so each word
    is tried independently against the Drug/Disease DB tables using ilike.
    Also generates 2- and 3-word combinations for multi-word names.
    """
    drug_hints: List[str]    = []
    disease_hints: List[str] = []

    lower = query.lower()

    if "drug:" in lower or "disease:" in lower:
        tokens = query.split()
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t.lower().startswith("drug:"):
                val = t[5:]
                while i + 1 < len(tokens) and not tokens[i + 1].lower().startswith(("drug:", "disease:")):
                    i += 1
                    val += " " + tokens[i]
                if val.strip():
                    drug_hints.append(val.strip())
            elif t.lower().startswith("disease:"):
                val = t[8:]
                while i + 1 < len(tokens) and not tokens[i + 1].lower().startswith(("drug:", "disease:")):
                    i += 1
                    val += " " + tokens[i]
                if val.strip():
                    disease_hints.append(val.strip())
            i += 1
        return drug_hints, disease_hints

    # Unstructured: split into individual tokens + combinations
    stop_words = {
        "and", "or", "the", "of", "in", "for", "with", "a", "an",
        "drug", "disease", "therapy", "treatment", "mechanism",
        "pathway", "clinical", "trial", "repurposing", "aging",
        "research", "study", "evidence",
    }
    raw_tokens = [t.strip().strip(".,;:'\"") for t in query.split() if len(t.strip()) >= 3]
    individual = [t for t in raw_tokens if t.lower() not in stop_words]

    combos: List[str] = list(individual)
    for length in (2, 3):
        for j in range(len(raw_tokens) - length + 1):
            combo = " ".join(raw_tokens[j: j + length])
            if combo not in combos:
                combos.append(combo)

    candidates = list(dict.fromkeys(combos))
    return candidates, candidates


def _extract_next_cursor(link_header: str) -> Optional[str]:
    """
    Parse the 'Link' response header to extract the next-page cursor.
    UniProt returns: Link: <https://…?cursor=XYZ&…>; rel="next"
    """
    if not link_header:
        return None
    for part in link_header.split(","):
        part = part.strip()
        if 'rel="next"' in part:
            # Extract URL between < and >
            url_part = part.split(";")[0].strip()
            if url_part.startswith("<") and url_part.endswith(">"):
                url = url_part[1:-1]
                parsed = urlparse(url)
                qs = parse_qs(parsed.query)
                cursors = qs.get("cursor", [])
                if cursors:
                    return cursors[0]
    return None
