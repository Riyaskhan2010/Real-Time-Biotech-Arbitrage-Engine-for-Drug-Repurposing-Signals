"""
Diagnose why EuropePMC and UniProt produce 0 evidence records.
Traces the exact matching path for a real fetched record.
"""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.drug import Drug
from app.models.disease import Disease
from app.models.evidence import Evidence
from app.models.research_source import ResearchSource
from app.models.signal import RepurposingSignal
from app.services.ingestion_service import IngestionService, _parse_query_for_hints
from app.services.ai_service import ai_service

engine = create_engine("sqlite:///./bioarbitrage.db", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
db = Session()

print("="*70)
print("DB ENTITIES AVAILABLE FOR MATCHING")
print("="*70)
drugs    = db.query(Drug).all()
diseases = db.query(Disease).all()
print("Drugs:", [d.name for d in drugs])
print("Diseases:", [d.name for d in diseases])

print("\n" + "="*70)
print("MATCHING TEST — simulate what _process_record does")
print("="*70)

svc = IngestionService()

# Test queries used in production ingestion
test_queries = [
    "metformin alzheimer",
    "aspirin alzheimer",
    "sildenafil pulmonary hypertension",
    "drug repurposing",
    "drug:Metformin disease:Alzheimer's Disease",  # structured format
    "drug:Aspirin disease:Alzheimer's Disease",
    "Metformin Cancer",
    "Aspirin mechanism pathway",
]

for query in test_queries:
    dh, dis_h = _parse_query_for_hints(query)
    drugs_matched    = svc._match_drugs(db, dh)
    diseases_matched = svc._match_diseases(db, dis_h)
    print(f"\n  Query: '{query}'")
    print(f"    drug_hints={dh}  disease_hints={dis_h}")
    print(f"    matched_drugs={[d.name for d in drugs_matched]}")
    print(f"    matched_diseases={[d.name for d in diseases_matched]}")

print("\n" + "="*70)
print("ENTITY EXTRACTOR TEST on EuropePMC/UniProt text")
print("="*70)

# Simulate what a real EuropePMC record looks like
sample_titles = [
    "Effects of aspirin on amyloid-beta in Alzheimer's disease patients",
    "PRKAB1: 5'-AMP-activated protein kinase subunit beta-1",
    "Role of metformin in cancer treatment via AMPK pathway",
    "Sildenafil reduces pulmonary arterial hypertension in clinical trials",
    "TP53 tumor suppressor protein function and disease associations",
]

for title in sample_titles:
    entities = ai_service.extract_entities(title)
    drugs_from_text    = svc._match_drugs(db, entities.get("drugs", []))
    diseases_from_text = svc._match_diseases(db, entities.get("diseases", []))
    print(f"\n  Title: '{title[:70]}'")
    print(f"    extracted_drugs={entities.get('drugs', [])}  matched={[d.name for d in drugs_from_text]}")
    print(f"    extracted_diseases={entities.get('diseases', [])}  matched={[d.name for d in diseases_from_text]}")

print("\n" + "="*70)
print("INGESTION QUERY TERMS (from config)")
print("="*70)
from app.config import settings
print(f"  Query terms: {settings.query_terms_list}")
print(f"  Enabled sources: {settings.enabled_sources_list}")

print("\n" + "="*70)
print("WHAT QUERY VARIANTS DOES _build_search_queries PRODUCE?")
print("="*70)
from app.api.ingestion import _build_search_queries
test_pairs = [
    ("Aspirin", "Alzheimer's Disease"),
    ("Metformin", "Cancer"),
    ("Sildenafil", "Pulmonary Arterial Hypertension"),
]
for drug, disease in test_pairs:
    qs = _build_search_queries(drug, disease, [])
    print(f"\n  {drug} + {disease}:")
    for i, q in enumerate(qs, 1):
        dh, dis_h = _parse_query_for_hints(q)
        drugs_m    = svc._match_drugs(db, dh)
        diseases_m = svc._match_diseases(db, dis_h)
        print(f"    Q{i}: '{q}'")
        print(f"       hints: drug={dh} disease={dis_h}")
        print(f"       match: drugs={[d.name for d in drugs_m]} diseases={[d.name for d in diseases_m]}")

db.close()
print("\nDiagnosis complete.")
