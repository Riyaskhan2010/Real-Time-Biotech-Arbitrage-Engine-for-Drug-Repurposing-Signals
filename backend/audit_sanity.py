"""Sanity check for all upgraded modules."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

print("Checking imports...")
from app.config import settings
from app.services.connectors.pubmed import PubMedConnector
from app.services.connectors.biorxiv import BioRxivConnector, MedRxivConnector
from app.services.connectors.clinicaltrials import ClinicalTrialsConnector
from app.services.connectors.elsevier import ElsevierConnector
from app.services.connectors.europepmc import EuropePMCConnector
from app.services.connectors.uniprot import UniProtConnector
from app.services.connectors.base import NormalizedRecord
from app.services.ingestion_service import ingestion_service, _parse_query_for_hints
from app.api.ingestion import _build_search_queries
from app.api.dashboard import _build_real_signal_trend, _to_list_item
from app.services.ai_service import ai_service
print("All imports OK")

# NormalizedRecord has pmcid
rec = NormalizedRecord(source='europepmc', source_id='test123', title='Test')
assert hasattr(rec, 'pmcid'), 'pmcid missing from NormalizedRecord'
print("NormalizedRecord.pmcid: OK")

# _parse_query_for_hints — unstructured
drug_hints, disease_hints = _parse_query_for_hints('metformin alzheimer')
assert len(drug_hints) > 0
assert len(disease_hints) > 0
print(f"_parse_query_for_hints unstructured: drugs={drug_hints} diseases={disease_hints}")

# _parse_query_for_hints — structured
drug_hints2, disease_hints2 = _parse_query_for_hints('drug:Metformin disease:Alzheimer')
assert 'Metformin' in drug_hints2, f"Expected Metformin in {drug_hints2}"
assert 'Alzheimer' in disease_hints2, f"Expected Alzheimer in {disease_hints2}"
print(f"_parse_query_for_hints structured: drugs={drug_hints2} diseases={disease_hints2}")

# _build_search_queries
queries = _build_search_queries('Aspirin', "Alzheimer's Disease", [])
assert "Aspirin Alzheimer's Disease" in queries, f"Missing primary query in {queries}"
assert "drug:Aspirin disease:Alzheimer's Disease" in queries, f"Missing structured query in {queries}"
print(f"_build_search_queries ({len(queries)} queries): {queries}")

# Config values
assert settings.INGESTION_MAX_RECORDS_PER_SOURCE == 50, f"max_records={settings.INGESTION_MAX_RECORDS_PER_SOURCE}"
assert settings.INGESTION_REQUEST_TIMEOUT == 20, f"timeout={settings.INGESTION_REQUEST_TIMEOUT}"
print(f"Config: max_records={settings.INGESTION_MAX_RECORDS_PER_SOURCE} timeout={settings.INGESTION_REQUEST_TIMEOUT}")
print(f"Enabled sources: {settings.enabled_sources_list}")
print(f"Query terms ({len(settings.query_terms_list)}): {settings.query_terms_list}")

# Verify UniProt _parse_query_hints
from app.services.connectors.uniprot import _parse_query_hints, _extract_next_cursor
d, dis = _parse_query_hints('metformin cancer')
print(f"UniProt _parse_query_hints: drugs={d} diseases={dis}")
d2, dis2 = _parse_query_hints('drug:Metformin disease:Cancer')
assert 'Metformin' in d2
assert 'Cancer' in dis2
print(f"UniProt structured hints: drugs={d2} diseases={dis2}")

# _extract_next_cursor
cursor = _extract_next_cursor('<https://rest.uniprot.org/uniprotkb/search?cursor=abc123&size=25>; rel="next"')
assert cursor == 'abc123', f"cursor={cursor}"
print(f"UniProt cursor extraction: {cursor}")

# EuropePMC pagination param present in connector
import inspect
src = inspect.getsource(EuropePMCConnector.fetch)
assert 'cursorMark' in src
assert 'nextCursorMark' in src
print("EuropePMC: cursorMark pagination present")

# PubMed pagination
src_pm = inspect.getsource(PubMedConnector._collect_pmids)
assert 'retstart' in src_pm
print("PubMed: retstart pagination present")

# ClinicalTrials pagination
src_ct = inspect.getsource(ClinicalTrialsConnector.fetch)
assert 'nextPageToken' in src_ct
print("ClinicalTrials: nextPageToken pagination present")

# Elsevier pagination
src_el = inspect.getsource(ElsevierConnector.fetch)
assert 'start' in src_el
assert 'totalResults' in src_el or 'total_available' in src_el
print("Elsevier: offset pagination present")

# bioRxiv sliding window
src_bx = inspect.getsource(BioRxivConnector.fetch)
assert 'max_windows' in src_bx
print("bioRxiv: sliding window present")

# Ingestion service rescore
src_is = inspect.getsource(ingestion_service._rescore_all_signals)
assert 'calculate_evidence_score' in src_is
print("IngestionService._rescore_all_signals: present")

# ingestion service query context matching
src_proc = inspect.getsource(ingestion_service._process_record)
assert 'drug_hints' in src_proc
assert 'disease_hints' in src_proc
print("IngestionService._process_record: query hints present")

print()
print("=== All sanity checks PASSED ===")
