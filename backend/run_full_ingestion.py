"""
Run a full live ingestion covering all configured query terms.
- Removes remaining 5 demo evidence records first
- Then runs ingestion so EuropePMC and UniProt records flow into the DB
- Reports before/after DB counts
"""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.evidence import Evidence
from app.models.research_source import ResearchSource
from app.models.signal import RepurposingSignal
from app.services.ingestion_service import ingestion_service
from app.config import settings

engine = create_engine("sqlite:///./bioarbitrage.db", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
db = Session()

# ── Step 1: Remove remaining demo evidence records ───────────────────────────
print("="*70)
print("STEP 1 — REMOVE REMAINING DEMO EVIDENCE")
print("="*70)
demo_ev = db.query(Evidence).filter(Evidence.is_demo_data == True).all()
print(f"  Demo evidence records found: {len(demo_ev)}")
for e in demo_ev:
    print(f"    id={e.id} signal_id={e.signal_id} title={str(e.title or '')[:60]}")
    db.delete(e)
db.commit()
remaining_demo = db.query(Evidence).filter(Evidence.is_demo_data == True).count()
print(f"  Demo evidence after cleanup : {remaining_demo}")
assert remaining_demo == 0, f"Expected 0 demo evidence, got {remaining_demo}"
print("  [PASS] Demo evidence = 0")

# ── Step 2: Show DB state before ingestion ───────────────────────────────────
print("\n" + "="*70)
print("STEP 2 — DB STATE BEFORE INGESTION")
print("="*70)
def ev_by_source():
    rows = db.query(Evidence.data_source, func.count(Evidence.id)).filter(
        Evidence.is_demo_data == False).group_by(Evidence.data_source).all()
    return {str(src or 'unknown'): cnt for src, cnt in rows}

before = ev_by_source()
total_before = sum(before.values())
print(f"  Total live evidence: {total_before}")
for src, cnt in sorted(before.items(), key=lambda x: -x[1]):
    print(f"    {src:<20} {cnt}")

# ── Step 3: Run full production ingestion ────────────────────────────────────
print("\n" + "="*70)
print("STEP 3 — RUNNING FULL PRODUCTION INGESTION")
print(f"  Query terms: {settings.query_terms_list}")
print(f"  Sources: {settings.enabled_sources_list}")
print("="*70)

run = asyncio.run(ingestion_service.run(db))

print(f"\n  Run status    : {run.status}")
print(f"  Summary       : {run.summary}")
print(f"  Total fetched : {run.total_fetched}")
print(f"  Total new     : {run.total_new}")
print(f"  Duplicates    : {run.total_duplicates}")
print(f"  Sigs updated  : {run.signals_updated}")
print(f"  Sigs created  : {run.signals_created}")
print()
print("  Per-source results:")
for sr in (run.source_results or []):
    src     = sr.get("source","?")
    status  = sr.get("status","?")
    fetched = sr.get("records_fetched", 0)
    new_r   = sr.get("records_new", 0)
    matched = sr.get("records_matched", 0)
    print(f"    {src:<16} status={status:<12} fetched={fetched:4d} new={new_r:4d} matched={matched:4d}")

# ── Step 4: DB state after ingestion ─────────────────────────────────────────
print("\n" + "="*70)
print("STEP 4 — DB STATE AFTER INGESTION")
print("="*70)
after = ev_by_source()
total_after = sum(after.values())
print(f"  Total live evidence: {total_after} (+{total_after - total_before})")
for src in ['pubmed', 'clinicaltrials', 'elsevier', 'europepmc', 'uniprot', 'biorxiv', 'medrxiv']:
    before_cnt = before.get(src, 0)
    after_cnt  = after.get(src, 0)
    delta = after_cnt - before_cnt
    status = "PASS" if after_cnt > 0 else ("NEW" if delta > 0 else "NONE")
    print(f"    {src:<16} before={before_cnt:3d} after={after_cnt:3d} delta=+{delta:3d}")

# Check EuropePMC and UniProt specifically
epmc_count = after.get('europepmc', 0)
uni_count  = after.get('uniprot', 0)

print()
if epmc_count > 0:
    print(f"  [PASS] EuropePMC: {epmc_count} live evidence records in DB")
else:
    print(f"  [WARN] EuropePMC: 0 records — may be no matching signals for these query terms")

if uni_count > 0:
    print(f"  [PASS] UniProt: {uni_count} live evidence records in DB")
else:
    print(f"  [WARN] UniProt: 0 records — may be no matching signals for these query terms")

# ResearchSource by source
rs_rows = db.query(ResearchSource.source_type, func.count(ResearchSource.id)).filter(
    ResearchSource.is_demo_data == False).group_by(ResearchSource.source_type).all()
print(f"\n  ResearchSource live records:")
for src, cnt in sorted(rs_rows, key=lambda x: -x[1]):
    print(f"    {str(src or 'unknown'):<20} {cnt}")

# ── Step 5: Signal summary ───────────────────────────────────────────────────
print("\n" + "="*70)
print("STEP 5 — SIGNAL SUMMARY")
print("="*70)
from sqlalchemy import exists as sq_exists, not_
from sqlalchemy.orm import joinedload
live_ev_exists = sq_exists().where(
    (Evidence.signal_id == RepurposingSignal.id) &
    (Evidence.is_demo_data == False)
)
live_sigs = db.query(RepurposingSignal).filter(live_ev_exists).options(
    joinedload(RepurposingSignal.drug), joinedload(RepurposingSignal.disease),
    joinedload(RepurposingSignal.evidence_items)
).all()
demo_sigs = db.query(RepurposingSignal).filter(not_(live_ev_exists)).count()

print(f"  Live signals: {len(live_sigs)}  Demo-only signals: {demo_sigs}")
for s in live_sigs:
    drug = s.drug.name if s.drug else "?"
    dis  = s.disease.name if s.disease else "?"
    live_ev_c = sum(1 for e in (s.evidence_items or []) if not e.is_demo_data)
    src_set   = set(e.data_source for e in (s.evidence_items or []) if not e.is_demo_data)
    print(f"    [{s.id}] {drug:<16} -> {dis:<36} live_ev={live_ev_c:3d} sources={sorted(src_set)}")

db.close()
print("\n" + "="*70)
print("INGESTION COMPLETE")
print("="*70)
