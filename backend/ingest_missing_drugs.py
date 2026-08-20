"""
Run targeted ingestion for the previously 0-signal drugs.
Uses the new query terms added to INGESTION_QUERY_TERMS.
"""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from sqlalchemy import create_engine, func, exists as sq_exists
from sqlalchemy.orm import sessionmaker, joinedload
from app.database import Base
from app.models.evidence import Evidence
from app.models.signal import RepurposingSignal
from app.models.drug import Drug
from app.services.ingestion_service import ingestion_service
from app.api.ingestion import _build_search_queries

engine = create_engine("sqlite:///./bioarbitrage.db", connect_args={"check_same_thread": False})
db = sessionmaker(bind=engine)()

# Target the missing drugs only
target_queries = [
    "ivermectin cancer",
    "ivermectin glioblastoma",
    "lithium alzheimer",
    "lithium neurodegeneration",
    "thalidomide cancer",
    "thalidomide glioblastoma",
    "thalidomide multiple myeloma",
    # also structured variants for better entity matching
    "drug:Ivermectin disease:Cancer",
    "drug:Ivermectin disease:Glioblastoma",
    "drug:Lithium disease:Alzheimer's Disease",
    "drug:Thalidomide disease:Cancer",
    "drug:Thalidomide disease:Glioblastoma",
    "drug:Thalidomide disease:Multiple Sclerosis",
]

print("="*70)
print("RUNNING TARGETED INGESTION FOR 0-SIGNAL DRUGS")
print(f"Query count: {len(target_queries)}")
print("="*70)

# Before counts
def sig_count_for(drug_name):
    drug = db.query(Drug).filter(Drug.name.ilike(f"%{drug_name}%")).first()
    if not drug:
        return 0, 0
    sigs = db.query(RepurposingSignal).filter(RepurposingSignal.drug_id == drug.id).all()
    live_sigs = 0
    for s in sigs:
        ev_items = db.query(Evidence).filter(Evidence.signal_id == s.id, Evidence.is_demo_data == False).count()
        if ev_items > 0:
            live_sigs += 1
    return len(sigs), live_sigs

print("\nBefore ingestion:")
for drug_name in ["Ivermectin", "Lithium", "Thalidomide"]:
    total, live = sig_count_for(drug_name)
    print(f"  {drug_name:<14} total_signals={total} live_signals={live}")

run = asyncio.run(ingestion_service.run(db, query_terms=target_queries))

print(f"\n  Run status   : {run.status}")
print(f"  Summary      : {run.summary}")
print(f"  Total fetched: {run.total_fetched}")
print(f"  Total new    : {run.total_new}")
print(f"  Sigs updated : {run.signals_updated}")
print(f"  Sigs created : {run.signals_created}")
print("\n  Per-source:")
for sr in (run.source_results or []):
    src     = sr.get("source","?")
    status  = sr.get("status","?")
    fetched = sr.get("records_fetched", 0)
    new_r   = sr.get("records_new", 0)
    matched = sr.get("records_matched", 0)
    if fetched > 0 or status == "connected":
        print(f"    {src:<16} status={status:<12} fetched={fetched:4d} new={new_r:4d} matched={matched:4d}")

print("\nAfter ingestion:")
for drug_name in ["Ivermectin", "Lithium", "Thalidomide"]:
    total, live = sig_count_for(drug_name)
    print(f"  {drug_name:<14} total_signals={total} live_signals={live}")

# Full signal report for target drugs
print("\n" + "="*70)
print("SIGNAL DETAIL FOR TARGET DRUGS")
print("="*70)
for drug_name in ["Ivermectin", "Lithium", "Thalidomide"]:
    drug = db.query(Drug).filter(Drug.name.ilike(f"%{drug_name}%")).first()
    if not drug:
        continue
    sigs = db.query(RepurposingSignal).options(
        joinedload(RepurposingSignal.disease),
        joinedload(RepurposingSignal.evidence_items),
    ).filter(RepurposingSignal.drug_id == drug.id).all()
    print(f"\n  {drug_name} ({len(sigs)} signals):")
    for s in sigs:
        dis = s.disease.name if s.disease else "?"
        live_ev = sum(1 for e in (s.evidence_items or []) if not e.is_demo_data)
        sources = sorted(set(e.data_source for e in (s.evidence_items or []) if not e.is_demo_data))
        print(f"    [{s.id}] -> {dis:<36} live_ev={live_ev:3d} score={s.evidence_score:.0f} sources={sources}")

db.close()
print("\n" + "="*70)
print("TARGETED INGESTION COMPLETE")
print("="*70)
