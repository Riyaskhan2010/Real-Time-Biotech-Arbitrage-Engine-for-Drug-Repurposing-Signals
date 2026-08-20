"""
Diagnostic script — Steps 1-5 from the investigation task.
Read-only: does NOT modify any data.
"""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, joinedload
from app.database import Base
from app.models.drug import Drug
from app.models.disease import Disease
from app.models.evidence import Evidence
from app.models.research_source import ResearchSource
from app.models.signal import RepurposingSignal
from app.services.ingestion_service import IngestionService, _parse_query_for_hints
from app.services.ai_service import ai_service
from app.config import settings

engine = create_engine("sqlite:///./bioarbitrage.db", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
db = Session()
svc = IngestionService()

TARGET_DRUGS = ["Ivermectin", "Lithium", "Thalidomide"]

# ─────────────────────────────────────────────────────────────────────────────
# STEPS 1 + 2 — DB INSPECTION
# ─────────────────────────────────────────────────────────────────────────────
print("="*70)
print("STEPS 1+2 — DATABASE INSPECTION")
print("="*70)

all_drugs = db.query(Drug).all()
print("\nAll drugs in DB:")
for d in all_drugs:
    sig_count = db.query(RepurposingSignal).filter(RepurposingSignal.drug_id == d.id).count()
    print(f"  [{d.id}] {d.name:<16} signals={sig_count}")

all_diseases = db.query(Disease).all()
print("\nAll diseases in DB:")
for d in all_diseases:
    print(f"  [{d.id}] {d.name}")

for drug_name in TARGET_DRUGS:
    drug = db.query(Drug).filter(Drug.name.ilike(f"%{drug_name}%")).first()
    print(f"\n{'='*60}")
    print(f"DRUG: {drug_name}")
    print(f"{'='*60}")
    if not drug:
        print("  NOT FOUND in DB")
        continue

    print(f"  Drug ID   : {drug.id}")
    print(f"  Drug name : {drug.name}")
    print(f"  Targets   : {drug.molecular_targets}")
    print(f"  Pathways  : {drug.pathways}")

    # Evidence directly attached to this drug's signals
    drug_signals = db.query(RepurposingSignal).options(
        joinedload(RepurposingSignal.disease),
        joinedload(RepurposingSignal.evidence_items),
    ).filter(RepurposingSignal.drug_id == drug.id).all()

    print(f"\n  Signals in DB: {len(drug_signals)}")
    for sig in drug_signals:
        dis_name = sig.disease.name if sig.disease else "?"
        live_ev = sum(1 for e in (sig.evidence_items or []) if not e.is_demo_data)
        demo_ev = sum(1 for e in (sig.evidence_items or []) if e.is_demo_data)
        sources = set(e.data_source for e in (sig.evidence_items or []) if not e.is_demo_data)
        print(f"    Signal [{sig.id}] -> {dis_name}")
        print(f"      status={sig.status} score={sig.evidence_score:.0f} live_ev={live_ev} demo_ev={demo_ev}")
        print(f"      sources={sorted(sources)}")

    # ResearchSource records mentioning this drug
    rs_records = db.query(ResearchSource).filter(
        ResearchSource.is_demo_data == False
    ).all()
    drug_rs = [r for r in rs_records if drug_name.lower() in
               " ".join((r.extracted_drugs or [])).lower() or
               drug_name.lower() in (r.title or "").lower()]
    print(f"\n  ResearchSource records mentioning '{drug_name}' (live): {len(drug_rs)}")
    for r in drug_rs[:5]:
        print(f"    [{r.source_type}] {str(r.title or '')[:70]}")
        print(f"      extracted_drugs={r.extracted_drugs}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — TRACE MATCHING LOGIC
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*70}")
print("STEP 3 — ENTITY MATCHING TRACE")
print("="*70)

test_queries = [
    "ivermectin cancer",
    "ivermectin covid",
    "ivermectin disease",
    "ivermectin onchocerciasis",
    "lithium disease",
    "lithium neurodegeneration",
    "lithium alzheimer",
    "lithium bipolar",
    "thalidomide cancer",
    "thalidomide multiple myeloma",
    "thalidomide disease",
    # structured variants
    "drug:Ivermectin disease:Cancer",
    "drug:Lithium disease:Alzheimer's Disease",
    "drug:Thalidomide disease:Cancer",
    "drug:Thalidomide disease:Glioblastoma",
    "drug:Thalidomide disease:Multiple Sclerosis",
    "drug:Ivermectin disease:Glioblastoma",
]

print("\n  Drug matching test results:")
for query in test_queries:
    dh, dis_h = _parse_query_for_hints(query)
    drugs_m    = svc._match_drugs(db, dh)
    diseases_m = svc._match_diseases(db, dis_h)
    status = "MATCH" if drugs_m and diseases_m else ("DRUG_ONLY" if drugs_m else ("DIS_ONLY" if diseases_m else "NO_MATCH"))
    print(f"  [{status:<10}] '{query}'")
    if drugs_m or diseases_m:
        print(f"             drugs={[d.name for d in drugs_m]}  diseases={[d.name for d in diseases_m]}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — AI ENTITY EXTRACTOR TEST
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*70}")
print("STEP 4 — AI ENTITY EXTRACTOR ON REALISTIC TITLES")
print("="*70)

sample_titles = [
    "Ivermectin as a potential anticancer agent in glioblastoma",
    "Ivermectin repurposing for COVID-19 treatment: a systematic review",
    "Ivermectin inhibits tumor growth in triple-negative breast cancer",
    "Lithium treatment in Alzheimer's disease: neuroprotective effects",
    "Lithium and glycogen synthase kinase 3 beta in neurodegeneration",
    "Thalidomide for multiple myeloma: efficacy and safety",
    "Thalidomide combined therapy in glioblastoma multiforme",
    "Anti-angiogenic effects of thalidomide in cancer therapy",
]

for title in sample_titles:
    entities = ai_service.extract_entities(title)
    drugs_m    = svc._match_drugs(db, entities.get("drugs", []))
    diseases_m = svc._match_diseases(db, entities.get("diseases", []))
    status = "MATCH" if drugs_m and diseases_m else ("DRUG_ONLY" if drugs_m else ("DIS_ONLY" if diseases_m else "NO_MATCH"))
    print(f"  [{status:<10}] {title[:65]}")
    print(f"             extracted: drugs={entities.get('drugs',[])}  diseases={entities.get('diseases',[])}")
    print(f"             matched:   drugs={[d.name for d in drugs_m]}  diseases={[d.name for d in diseases_m]}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — CHECK WHAT ai_service.extract_entities KNOWS
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*70}")
print("STEP 5 — KNOWN DRUG LIST IN ENTITY EXTRACTOR")
print("="*70)

import inspect
extractor_src = inspect.getsource(ai_service._heuristic_extract_entities)
# Find KNOWN_DRUGS list
import re
known_drugs_match = re.search(r'KNOWN_DRUGS\s*=\s*\[([^\]]+)\]', extractor_src)
if known_drugs_match:
    print("  KNOWN_DRUGS list found:")
    print(f"  {known_drugs_match.group(1)[:300]}")
else:
    # Print relevant lines
    lines = [l for l in extractor_src.splitlines() if 'drug' in l.lower() or 'known' in l.lower()]
    print("  Relevant lines in extractor:")
    for l in lines[:20]:
        print(f"    {l}")

# Check whether ivermectin, lithium, thalidomide are in the extractor
for name in ["ivermectin", "lithium", "thalidomide"]:
    present = name.lower() in extractor_src.lower()
    print(f"\n  '{name}' in entity extractor: {present}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5b — LIVE SOURCE FETCH CHECK (small sample)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*70}")
print("STEP 5b — LIVE SOURCE FETCH (3 records per drug per key source)")
print("="*70)

async def check_sources_for_drugs():
    from app.services.connectors.europepmc import EuropePMCConnector
    from app.services.connectors.pubmed     import PubMedConnector
    from app.services.connectors.clinicaltrials import ClinicalTrialsConnector

    connectors = [
        ("PubMed",        PubMedConnector(timeout=15)),
        ("EuropePMC",     EuropePMCConnector(timeout=15)),
        ("ClinicalTrials",ClinicalTrialsConnector(timeout=15)),
    ]

    drug_queries = {
        "Ivermectin":   ["ivermectin cancer", "ivermectin glioblastoma", "ivermectin oncology"],
        "Lithium":      ["lithium alzheimer neurodegeneration", "lithium GSK3 brain"],
        "Thalidomide":  ["thalidomide cancer", "thalidomide multiple myeloma"],
    }

    for drug_name, queries in drug_queries.items():
        print(f"\n  {drug_name}:")
        for conn_name, conn in connectors:
            for q in queries[:1]:  # just first query per source
                try:
                    recs = await asyncio.wait_for(conn.fetch(q, max_records=3), timeout=15)
                    # Check how many would match
                    matched_any = 0
                    for rec in recs:
                        dh, dis_h = _parse_query_for_hints(q)
                        text_ents = ai_service.extract_entities(f"{rec.title} {rec.abstract or ''}")
                        all_drug_hints = list(dict.fromkeys(
                            rec.extracted_drugs + text_ents.get("drugs", []) + dh
                        ))
                        all_dis_hints = list(dict.fromkeys(
                            rec.extracted_diseases + text_ents.get("diseases", []) + dis_h
                        ))
                        drugs_m = svc._match_drugs(db, all_drug_hints)
                        diseases_m = svc._match_diseases(db, all_dis_hints)
                        if drugs_m and diseases_m:
                            matched_any += 1
                    print(f"    [{conn_name:<16}] query='{q}' fetched={len(recs)} would_match={matched_any}")
                    if recs:
                        r = recs[0]
                        print(f"      sample_title={r.title[:60]}")
                except asyncio.TimeoutError:
                    print(f"    [{conn_name:<16}] TIMEOUT")
                except Exception as e:
                    print(f"    [{conn_name:<16}] ERROR: {type(e).__name__}: {e}")

asyncio.run(check_sources_for_drugs())

db.close()
print(f"\n{'='*70}")
print("DIAGNOSIS COMPLETE")
print("="*70)
