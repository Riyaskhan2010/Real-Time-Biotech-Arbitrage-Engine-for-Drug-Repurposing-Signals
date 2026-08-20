"""
ClinicalTrials.gov connector using the official REST API v2.

API docs: https://clinicaltrials.gov/data-api/api
Endpoint: https://clinicaltrials.gov/api/v2/studies

No API key required. Completely open and free.

RETRIEVAL STRATEGY:
  Paginate using nextPageToken until all available relevant records are
  fetched or max_records is reached. The API returns up to 1000 records
  per page; we use 50 per page for reliability.

  This removes the previous single-page cap.
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

import httpx

from app.services.connectors.base import BaseConnector, NormalizedRecord

logger = logging.getLogger(__name__)

CT_BASE    = "https://clinicaltrials.gov/api/v2/studies"
_PAGE_SIZE = 50

_FIELDS = (
    "NCTId,BriefTitle,OfficialTitle,BriefSummary,DetailedDescription,"
    "OverallStatus,Phase,Condition,InterventionName,InterventionType,"
    "StartDate,CompletionDate,LastUpdatePostDate,StudyType,LeadSponsorName,"
    "ResponsiblePartyInvestigatorFullName"
)


class ClinicalTrialsConnector(BaseConnector):
    SOURCE_NAME = "clinicaltrials"

    def __init__(self, timeout: int = 20):
        super().__init__(timeout)

    # ── Connectivity probe ────────────────────────────────────────────────────

    async def check_connection(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(CT_BASE, params={"format": "json", "pageSize": 1})
                return r.status_code == 200
        except Exception:
            return False

    # ── Main fetch ────────────────────────────────────────────────────────────

    async def fetch(self, query: str, max_records: int = 50) -> List[NormalizedRecord]:
        """
        Search ClinicalTrials.gov for studies matching `query`.

        Paginates using nextPageToken until max_records is reached or
        all results are exhausted.
        """
        if not query or not query.strip():
            return []

        records: List[NormalizedRecord] = []
        page_token: Optional[str] = None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                while len(records) < max_records:
                    params: dict = {
                        "format":     "json",
                        "query.term": query,
                        "pageSize":   min(_PAGE_SIZE, max_records - len(records)),
                        "fields":     _FIELDS,
                    }
                    if page_token:
                        params["pageToken"] = page_token

                    try:
                        r = await client.get(CT_BASE, params=params)
                        r.raise_for_status()
                        data = r.json()
                    except httpx.TimeoutException:
                        logger.warning("[ClinicalTrials] timeout for query %r", query)
                        break
                    except Exception as e:
                        logger.warning("[ClinicalTrials] fetch error for %r: %s", query, e)
                        break

                    studies = data.get("studies", [])
                    if not studies:
                        break

                    for study in studies:
                        rec = self._normalize(study)
                        if rec:
                            records.append(rec)
                        if len(records) >= max_records:
                            break

                    page_token = data.get("nextPageToken") or None
                    if not page_token:
                        break
                    await asyncio.sleep(0.2)

        except Exception as e:
            logger.warning("[ClinicalTrials] unexpected error for %r: %s", query, e)

        logger.info("[ClinicalTrials] Fetched %d records for query %r", len(records), query)
        return records

    # ── Normalise ─────────────────────────────────────────────────────────────

    def _normalize(self, study: dict) -> Optional[NormalizedRecord]:
        proto = study.get("protocolSection", {})
        ident = proto.get("identificationModule", {})
        desc  = proto.get("descriptionModule", {})
        status= proto.get("statusModule", {})
        design= proto.get("designModule", {})
        cond  = proto.get("conditionsModule", {})
        interv= proto.get("armsInterventionsModule", {})

        nct_id = (ident.get("nctId") or "").strip() or None
        if not nct_id:
            return None

        title = (ident.get("briefTitle") or ident.get("officialTitle") or "").strip()
        if not title:
            return None

        abstract = self._truncate(
            desc.get("briefSummary") or desc.get("detailedDescription") or None
        )
        pub_date = self._safe_date(
            status.get("lastUpdatePostDateStruct", {}).get("date")
            or status.get("startDateStruct", {}).get("date")
        )

        drugs_in_study: List[str] = []
        for interv_item in interv.get("interventions", []):
            if interv_item.get("type", "").lower() == "drug":
                name = (interv_item.get("name") or "").strip()
                if name:
                    drugs_in_study.append(name)

        conditions = cond.get("conditions", [])
        overall_status = status.get("overallStatus", "")
        phase = ", ".join(design.get("phases", [])) if design.get("phases") else ""

        return NormalizedRecord(
            source="clinicaltrials",
            source_id=nct_id,
            nct_id=nct_id,
            source_url=f"https://clinicaltrials.gov/study/{nct_id}",
            title=self._truncate(title, 495),
            abstract=abstract,
            publication_date=pub_date,
            authors=[],
            journal=f"ClinicalTrials.gov [{overall_status}]",
            evidence_type="clinical_trial",
            extracted_drugs=drugs_in_study[:5],
            extracted_diseases=conditions[:5],
            is_demo_data=False,
        )
