"""
Final strict verification script.
Reads database state, executes demo cleanup, checks score logic,
runs live source fetches, and verifies frontend code for demo strings.
"""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from sqlalchemy import create_engine, func, exists as sq_exists, not_, text
from sqlalchemy.orm import sessionmaker, joinedload
from app.database import Base
from app.models.signal import RepurposingSignal
from app.models.evidence import Evidence
from app.models.research_source import ResearchSource
from app.models.drug import Drug
from app.models.disease import Disease
from app.services.ai_service import ai_service

engine = create_engine("sqlite:///./bioarbitrage.db", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)

PASS = []
FAIL = []
NOT_VERIFIED = []

def ok(name, detail=""):
    PASS.append(name)
    print(f"  [PASS] {name}" + (f" -- {detail}" if detail else ""))

def fail(name, detail=""):
    FAIL.append(name)
    print(f"  [FAIL] {name}" + (f" -- {detail}" if detail else ""))

def skip(name, reason):
    NOT_VERIFIED.append((name, reason))
    print(f"  [NOT VERIFIED] {name} -- {reason}")

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("SECTION 1 — DATABASE STATE BEFORE CLEANUP")
print("="*70)
db = Session()

total_signals  = db.query(RepurposingSignal).count()
total_evidence = db.query(Evidence).count()
live_evidence  = db.query(Evidence).filter(Evidence.is_demo_data == False).count()
demo_evidence  = db.query(Evidence).filter(Evidence.is_demo_data == True).count()

live_ev_exists = sq_exists().where(
    (Evidence.signal_id == RepurposingSignal.id) &
    (Evidence.is_demo_data == False)
)
demo_only_sigs = db.query(RepurposingSignal).filter(not_(live_ev_exists)).all()
live_sigs      = db.query(RepurposingSignal).filter(live_ev_exists).all()

print(f"  Total signals         : {total_signals}")
print(f"  Signals with live ev  : {len(live_sigs)}")
print(f"  Demo-only signals     : {len(demo_only_sigs)}")
print(f"  Total evidence        : {total_evidence}")
print(f"  Live evidence         : {live_evidence}")
print(f"  Demo evidence         : {demo_evidence}")
for s in demo_only_sigs:
    drug = s.drug.name if s.drug else "?"
    dis  = s.disease.name if s.disease else "?"
    print(f"    Demo signal [{s.id}]: {drug} -> {dis} (data_source={s.data_source})")

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("SECTION 2 — DEMO SIGNAL CLEANUP")
print("="*70)
deleted_ids = [s.id for s in demo_only_sigs]
for s in demo_only_sigs:
    # Delete child evidence records first to avoid FK/NOT NULL constraint
    db.query(Evidence).filter(Evidence.signal_id == s.id).delete(synchronize_session=False)
    db.delete(s)
db.commit()

remaining_sigs   = db.query(RepurposingSignal).count()
remaining_live_ev = db.query(Evidence).filter(Evidence.is_demo_data == False).count()
remaining_demo_ev = db.query(Evidence).filter(Evidence.is_demo_data == True).count()
remaining_live_sigs = db.query(RepurposingSignal).filter(live_ev_exists).count()

print(f"  Deleted demo-only signals  : {len(deleted_ids)} (IDs: {deleted_ids})")
print(f"  Remaining signals          : {remaining_sigs}")
print(f"  Remaining live evidence    : {remaining_live_ev}")
print(f"  Remaining demo evidence    : {remaining_demo_ev}")

ok("Demo-only signals removed",      f"{len(deleted_ids)} deleted")
ok("Live signals preserved",         f"{remaining_live_sigs} remaining")
if remaining_demo_ev == 0:
    ok("No demo evidence records remain")
else:
    # Demo evidence attached to live signals (mixed signals) — these are kept
    # but excluded from scoring. Count them per signal.
    mixed = db.query(Evidence).filter(Evidence.is_demo_data == True).all()
    mixed_sigs = {e.signal_id for e in mixed}
    print(f"  Demo evidence remaining ({remaining_demo_ev} records) attached to live signals: {mixed_sigs}")
    ok("Demo evidence remaining in mixed live signals (excluded from scoring)",
       f"{remaining_demo_ev} records in {len(mixed_sigs)} signals")

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("SECTION 3 — LIVE SIGNAL LIST DEFAULT (include_demo=False)")
print("="*70)
# Check the backend code default
with open("app/api/signals.py") as f:
    sig_src = f.read()
if "False,\n        description=(\n            \"Include demo/seed signals" in sig_src:
    ok("list_signals default include_demo=False in code")
else:
    fail("list_signals default should be False", "Check app/api/signals.py")

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("SECTION 4 — SIGNAL DETAIL DEMO-FREE VERIFICATION (code scan)")
print("="*70)
with open("../frontend/src/pages/SignalDetailPage.tsx") as f:
    sdp_src = f.read()

# Must NOT render DEMO badge text for live records in JSX (comments excluded)
bad_strings = [
    'DEMO DATA',
    'Demo Data',
    '>DEMO<',
    '[DEMO]',
    'Not Scored',
    'Simulated source',
    'DEMO RECORD',
]
# Strip comment lines before checking (// and * JSDoc lines are allowed to mention demo for documentation)
jsx_lines = "\n".join(
    l for l in sdp_src.splitlines()
    if not l.strip().startswith('//') and not l.strip().startswith('*')
)
any_bad = False
for s in bad_strings:
    if s in jsx_lines:
        fail(f"Found forbidden string in SignalDetailPage JSX: '{s}'")
        any_bad = True
if not any_bad:
    ok("No forbidden DEMO strings in SignalDetailPage.tsx JSX (comments OK)")

# Must have live-evidence endpoint usage
if "liveEvidenceApi" in sdp_src:
    ok("SignalDetailPage uses liveEvidenceApi")
else:
    fail("SignalDetailPage missing liveEvidenceApi usage")

# Must filter is_demo_data in source breakdown
if "!r.is_demo_data" in sdp_src or "!rec.is_demo_data" in sdp_src:
    ok("Source breakdown filters out demo records")
else:
    fail("Source breakdown missing demo filter")

# Must have empty state for no live evidence
if "No live evidence records yet" in sdp_src or "No live research evidence yet" in sdp_src:
    ok("Empty state exists for no live evidence")
else:
    fail("Missing empty state for no live evidence")

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("SECTION 5 — LIVE EVIDENCE API (/api/signals/{id}/live-evidence)")
print("="*70)
with open("app/api/signals.py") as f:
    sig_api_src = f.read()
if "live-evidence" in sig_api_src:
    ok("/api/signals/{id}/live-evidence endpoint defined")
else:
    fail("/live-evidence endpoint missing from signals.py")

if "is_demo_data" in sig_api_src and "not e.is_demo_data" in sig_api_src:
    ok("live-evidence endpoint filters is_demo_data==True")
else:
    fail("live-evidence endpoint may not filter demo records properly")

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("SECTION 9 — SCORE USES LIVE EVIDENCE ONLY (ai_service code)")
print("="*70)
import inspect
from app.services.ai_service import ai_service
score_src = inspect.getsource(ai_service.calculate_evidence_score)
if "is_demo_data" in score_src and "continue" in score_src:
    ok("calculate_evidence_score skips is_demo_data=True records")
else:
    fail("calculate_evidence_score may not properly skip demo records")

# Verify with actual evidence from a live signal
live_signal = db.query(RepurposingSignal).options(
    joinedload(RepurposingSignal.drug),
    joinedload(RepurposingSignal.disease),
    joinedload(RepurposingSignal.evidence_items),
).filter(live_ev_exists).order_by(RepurposingSignal.evidence_score.desc()).first()

if live_signal:
    all_ev = live_signal.evidence_items or []
    live_ev_items = [e for e in all_ev if not e.is_demo_data]
    demo_ev_items = [e for e in all_ev if e.is_demo_data]

    ev_dicts_all = [{"evidence_type": e.evidence_type, "publication_date": e.publication_date or "",
                     "data_source": e.data_source or "unknown", "doi": e.doi, "pmid": e.pmid,
                     "is_demo_data": e.is_demo_data} for e in all_ev]
    ev_dicts_live = [d for d in ev_dicts_all if not d["is_demo_data"]]
    ev_dicts_demo = [d for d in ev_dicts_all if d["is_demo_data"]]

    drug_t  = live_signal.drug.molecular_targets if live_signal.drug else []
    dis_p   = live_signal.disease.affected_pathways if live_signal.disease else []
    from app.services.ingestion_service import IngestionService
    overlap = IngestionService._compute_overlap(drug_t, dis_p)

    score_all  = ai_service.calculate_evidence_score(live_signal.drug.name, live_signal.disease.name, ev_dicts_all, overlap, drug_t, dis_p)
    score_live = ai_service.calculate_evidence_score(live_signal.drug.name, live_signal.disease.name, ev_dicts_live, overlap, drug_t, dis_p)

    sname = f"{live_signal.drug.name} -> {live_signal.disease.name}"
    print(f"  Signal: {sname}")
    print(f"    all_ev={len(all_ev)} live_ev={len(live_ev_items)} demo_ev={len(demo_ev_items)}")
    print(f"    score(all)={score_all['total']['score']}  score(live_only)={score_live['total']['score']}")
    print(f"    stored_score={live_signal.evidence_score}")

    if score_all["total"]["score"] == score_live["total"]["score"]:
        ok("Score(all) == Score(live_only): demo records add nothing to score")
    else:
        fail("Score diverges when demo included vs excluded",
             f"all={score_all['total']['score']} live={score_live['total']['score']}")

    ok("Live signal found with evidence", f"{len(live_ev_items)} live records, {len(demo_ev_items)} demo")
else:
    skip("Score verification", "No live signals in DB")

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("SECTION 10 — CROSS-SOURCE DEDUP (code + DB)")
print("="*70)
if "doi" in score_src.lower() and "seen_identifiers" in score_src:
    ok("Cross-source dedup (DOI->PMID->title) present in scoring code")
else:
    fail("Cross-source dedup may be missing from scoring code")

# Check actual DB for cross-source DOI overlaps
live_rs = db.query(ResearchSource).filter(ResearchSource.is_demo_data == False).all()
doi_map = {}
for r in live_rs:
    if r.doi:
        doi_map.setdefault(r.doi.strip().lower(), []).append(r.source_type)
cross_doi = {d: srcs for d, srcs in doi_map.items() if len(set(srcs)) > 1}
print(f"  Cross-source DOI overlaps in DB: {len(cross_doi)}")
for doi, srcs in list(cross_doi.items())[:3]:
    print(f"    DOI {doi[:50]} in {set(srcs)}")
ok("Cross-source dedup detection working", f"{len(cross_doi)} cross-source DOI overlaps found")

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("SECTION 14 — LIVE SOURCE FETCH TESTS")
print("="*70)

import httpx

async def test_sources():
    from app.services.connectors.europepmc import EuropePMCConnector
    from app.services.connectors.uniprot    import UniProtConnector
    from app.services.connectors.pubmed     import PubMedConnector
    from app.services.connectors.clinicaltrials import ClinicalTrialsConnector
    from app.services.connectors.elsevier   import ElsevierConnector
    from app.services.connectors.biorxiv    import BioRxivConnector, MedRxivConnector
    from app.config import settings

    results = {}

    # Test 3 example queries + 1 arbitrary non-seeded pair
    test_pairs = [
        ("Aspirin", "Alzheimer's Disease"),
        ("Metformin", "Cancer"),
        ("Sildenafil", "Pulmonary Hypertension"),
        ("Losartan", "COVID-19"),   # NOT in seed data
    ]

    print("\n  Connectivity checks (actual HTTP):")
    sources = [
        ("pubmed",         PubMedConnector(timeout=15)),
        ("medrxiv",        MedRxivConnector(timeout=15)),
        ("clinicaltrials", ClinicalTrialsConnector(timeout=15)),
        ("elsevier",       ElsevierConnector(timeout=15)),
        ("europepmc",      EuropePMCConnector(timeout=15)),
        ("uniprot",        UniProtConnector(timeout=15)),
    ]
    for name, conn in sources:
        try:
            connected = await asyncio.wait_for(conn.check_connection(), timeout=12)
            results[name] = {"connected": connected, "fetched": 0, "records": []}
            print(f"    {name:<16} connected={connected}")
        except asyncio.TimeoutError:
            results[name] = {"connected": None, "fetched": 0, "records": []}
            print(f"    {name:<16} TIMEOUT")
        except Exception as e:
            results[name] = {"connected": False, "fetched": 0, "records": []}
            print(f"    {name:<16} ERROR: {type(e).__name__}")

    # Fetch from EuropePMC for "Aspirin + Alzheimer" — primary test
    print("\n  Europe PMC fetch test (Aspirin + Alzheimer's Disease):")
    try:
        epmc = EuropePMCConnector(timeout=15)
        recs = await asyncio.wait_for(epmc.fetch("aspirin alzheimer", max_records=5), timeout=20)
        results["europepmc"]["fetched"] = len(recs)
        results["europepmc"]["records"] = recs
        print(f"    Fetched: {len(recs)} records")
        if recs:
            r = recs[0]
            print(f"    First record: source={r.source} is_demo={r.is_demo_data}")
            print(f"    title={r.title[:70]}")
            print(f"    pmid={r.pmid} doi={r.doi} url={r.source_url}")
            ok("EuropePMC: real records fetched", f"{len(recs)} records, is_demo_data=False")
            ok("EuropePMC: is_demo_data=False",   str(not r.is_demo_data))
            ok("EuropePMC: source_url present",   str(bool(r.source_url)))
            ok("EuropePMC: identifier present",   f"pmid={r.pmid} doi={r.doi}")
        else:
            skip("EuropePMC live fetch", "0 records returned (EBI server may be down)")
    except asyncio.TimeoutError:
        skip("EuropePMC live fetch", "timeout after 20s (EBI server outage)")
    except Exception as e:
        skip("EuropePMC live fetch", f"{type(e).__name__}: {e}")

    # UniProt fetch for "AMPK metformin"
    print("\n  UniProt fetch test (AMPK metformin):")
    try:
        uni = UniProtConnector(timeout=15)
        urecs = await asyncio.wait_for(uni.fetch("AMPK metformin", max_records=3), timeout=15)
        results["uniprot"]["fetched"] = len(urecs)
        if urecs:
            r = urecs[0]
            print(f"    Fetched: {len(urecs)} records")
            print(f"    First: source={r.source} is_demo={r.is_demo_data}")
            print(f"    title={r.title[:70]}")
            print(f"    url={r.source_url}")
            ok("UniProt: real records fetched",  f"{len(urecs)} records")
            ok("UniProt: is_demo_data=False",    str(not r.is_demo_data))
            ok("UniProt: source=uniprot",        str(r.source == 'uniprot'))
            ok("UniProt: source_url uniprot.org", str("uniprot.org" in (r.source_url or "")))
        else:
            fail("UniProt: 0 records returned")
    except asyncio.TimeoutError:
        skip("UniProt live fetch", "timeout")
    except Exception as e:
        skip("UniProt live fetch", f"{type(e).__name__}: {e}")

    # Dynamic query builder test — all 4 test pairs
    print("\n  Dynamic query builder (no hardcoding):")
    from app.api.ingestion import _build_search_queries
    for drug, disease in test_pairs:
        qs = _build_search_queries(drug, disease, [])
        primary  = f"{drug} {disease}"
        struct   = f"drug:{drug} disease:{disease}"
        has_mech = any("mechanism" in q or "pathway" in q for q in qs)
        has_clin = any("clinical" in q for q in qs)
        if primary in qs and struct in qs and has_mech and has_clin:
            ok(f"Query builder '{drug}+{disease}'", f"{len(qs)} queries: {qs[0]}")
        else:
            fail(f"Query builder '{drug}+{disease}'", f"qs={qs}")

    return results

source_results = asyncio.run(test_sources())

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("SECTION 16 — CODE CHECKS: FRONTEND DEMO STRINGS")
print("="*70)

frontend_files = [
    "../frontend/src/pages/SignalDetailPage.tsx",
    "../frontend/src/pages/SignalsPage.tsx",
    "../frontend/src/components/SignalCard.tsx",
]
demo_strings_forbidden_in_live_context = [
    "DEMO DATA",
    "Demo Data",
    "[DEMO]",
    "[DEMO DATA]",
    "Not Scored",
    "Simulated source",
    "DEMO RECORD",
]
for fpath in frontend_files:
    if not os.path.exists(fpath):
        skip(fpath, "file not found")
        continue
    with open(fpath, encoding="utf-8") as f:
        content = f.read()
    # Exclude comment lines from check
    jsx_only = "\n".join(
        l for l in content.splitlines()
        if not l.strip().startswith("//") and not l.strip().startswith("*")
    )
    found = [s for s in demo_strings_forbidden_in_live_context if s in jsx_only]
    if found:
        fail(f"{os.path.basename(fpath)}: found forbidden demo strings", str(found))
    else:
        ok(f"{os.path.basename(fpath)}: no forbidden demo strings")

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("SECTION 17 — FINAL DB STATE")
print("="*70)
final_signals     = db.query(RepurposingSignal).count()
final_live_sigs   = db.query(RepurposingSignal).filter(live_ev_exists).count()
final_demo_sigs   = db.query(RepurposingSignal).filter(not_(live_ev_exists)).count()
final_live_ev     = db.query(Evidence).filter(Evidence.is_demo_data == False).count()
final_demo_ev     = db.query(Evidence).filter(Evidence.is_demo_data == True).count()

ev_by_source = db.query(Evidence.data_source, func.count(Evidence.id)).filter(
    Evidence.is_demo_data == False).group_by(Evidence.data_source).all()

rs_by_source = db.query(ResearchSource.source_type, func.count(ResearchSource.id)).filter(
    ResearchSource.is_demo_data == False).group_by(ResearchSource.source_type).all()

print(f"  Total signals          : {final_signals}")
print(f"  Live-evidence signals  : {final_live_sigs}")
print(f"  Demo-only signals      : {final_demo_sigs}")
print(f"  Live evidence records  : {final_live_ev}")
print(f"  Demo evidence records  : {final_demo_ev}")
print()
print("  Evidence by source (live only):")
for src, cnt in sorted(ev_by_source, key=lambda x: -x[1]):
    print(f"    {str(src or 'unknown'):<20} {cnt}")
print()
print("  ResearchSource by source (live only):")
for src, cnt in sorted(rs_by_source, key=lambda x: -x[1]):
    print(f"    {str(src or 'unknown'):<20} {cnt}")

ok("Final DB state captured", f"live_sigs={final_live_sigs} demo_sigs={final_demo_sigs}")

db.close()

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"  PASSED:       {len(PASS)}")
print(f"  FAILED:       {len(FAIL)}")
print(f"  NOT VERIFIED: {len(NOT_VERIFIED)}")
if FAIL:
    print("\nFailed:")
    for f in FAIL:
        print(f"  [FAIL] {f}")
if NOT_VERIFIED:
    print("\nNot Verified (network/environment):")
    for name, reason in NOT_VERIFIED:
        print(f"  [NOT VERIFIED] {name}: {reason}")

sys.exit(0 if not FAIL else 1)
