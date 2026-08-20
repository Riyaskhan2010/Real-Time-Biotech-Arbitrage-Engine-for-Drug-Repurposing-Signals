# -*- coding: utf-8 -*-
"""
Europe PMC connector tests.
Verifies: connection, dynamic queries for multiple drug+disease combinations,
           record structure, dedup, pipeline processing.
"""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from app.services.connectors.europepmc import EuropePMCConnector
from app.services.ingestion_service import ingestion_service

print("=" * 64)
print("EUROPE PMC CONNECTOR TEST")
print("=" * 64)

conn = EuropePMCConnector()

# 1. Connection check
print("\n[1] check_connection()")
async def check():
    ok = await conn.check_connection()
    print("    Connected:", ok)
    return ok

ok = asyncio.run(check())
assert ok, "Europe PMC connection failed — check network"

# 2. Multiple dynamic queries (the examples from the spec)
TEST_QUERIES = [
    ("Metformin + Cancer",                      "metformin cancer"),
    ("Aspirin + Alzheimer's disease",           "aspirin alzheimer"),
    ("Sildenafil + Pulmonary hypertension",     "sildenafil pulmonary hypertension"),
    ("Drug repurposing (general)",              "drug repurposing"),
    ("Rapamycin aging mechanism",               "rapamycin aging mechanism"),
    ("Metformin AMPK pathway",                  "metformin AMPK pathway"),
]

print("\n[2] Dynamic query tests")
async def run_queries():
    for label, query in TEST_QUERIES:
        records = await conn.fetch(query, max_records=3)
        has_title   = all(r.title for r in records)
        has_source  = all(r.source_id for r in records)
        is_live     = all(not r.is_demo_data for r in records)
        pmids_found = sum(1 for r in records if r.pmid)
        dois_found  = sum(1 for r in records if r.doi)
        kw_found    = sum(1 for r in records if r.extracted_mechanisms)
        print(f"    {label}")
        print(f"      records={len(records)} titles_ok={has_title} "
              f"source_ids_ok={has_source} live={is_live} "
              f"pmids={pmids_found} dois={dois_found} keywords={kw_found}")
        if records:
            r = records[0]
            print(f"      Top: [{r.source_id[:30]}] {r.title[:65]}")
            print(f"           date={r.publication_date}  journal={r.journal[:40] if r.journal else None}")
            print(f"           pmid={r.pmid}  doi={r.doi}")
            print(f"           url={r.source_url}")
            print(f"           abstract_chars={(len(r.abstract) if r.abstract else 0)}")
            print(f"           evidence_type={r.evidence_type}")
            print(f"           keywords[:3]={r.extracted_mechanisms[:3]}")
        assert has_title, f"Records missing titles for query {query!r}"
        assert has_source, f"Records missing source_ids for query {query!r}"
        assert is_live, f"Records incorrectly flagged as demo data"

asyncio.run(run_queries())

# 3. Pipeline smoke test
print("\n[3] Full pipeline test (in-memory DB)")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.drug import Drug
from app.models.disease import Disease
from app.models.user import User
from app.models.research_source import ResearchSource
from app.utils.auth import get_password_hash
from app.services.ingestion_service import IngestionService

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
db = sessionmaker(bind=engine)()

db.add(User(email="t@t.t", username="t", full_name="T",
            hashed_password=get_password_hash("pw"), role="researcher", is_active=True))
db.add(Drug(name="Metformin", molecular_targets=["AMPK"],
            pathways=["mTOR signaling"], fda_status="Approved",
            approved_indications=["Type 2 Diabetes"]))
db.add(Drug(name="Sildenafil", molecular_targets=["PDE5"],
            pathways=["cGMP pathway"], fda_status="Approved",
            approved_indications=["Pulmonary arterial hypertension"]))
db.add(Disease(name="Alzheimer's Disease", affected_pathways=["mTOR signaling"]))
db.add(Disease(name="Cancer", affected_pathways=["mTOR signaling"]))
db.commit()

async def pipeline():
    records = await conn.fetch("metformin alzheimer", max_records=5)
    svc = IngestionService()
    outcomes = {}
    for rec in records:
        out = svc._process_record(db, rec)
        outcomes[out] = outcomes.get(out, 0) + 1
    saved = db.query(ResearchSource).filter_by(source_type="europepmc").count()
    print(f"    Records fetched: {len(records)}")
    print(f"    Outcomes: {outcomes}")
    print(f"    Saved to DB: {saved}")

    # Dedup test — process same records again
    records2 = await conn.fetch("metformin alzheimer", max_records=5)
    dup_outcomes = {}
    for rec in records2:
        out = svc._process_record(db, rec)
        dup_outcomes[out] = dup_outcomes.get(out, 0) + 1
    print(f"    Dedup outcomes (re-run): {dup_outcomes}")
    assert dup_outcomes.get("duplicate", 0) > 0 or all(o == "duplicate" for o in dup_outcomes), \
        "Dedup not working — same records inserted twice"

asyncio.run(pipeline())
db.close()

# 4. check_sources includes europepmc
print("\n[4] check_sources() includes europepmc")
async def src_check():
    results = await ingestion_service.check_sources()
    for r in results:
        print(f"    {r['source']:25}  status={r['status']}  enabled={r['enabled']}")
    ep = next((r for r in results if r["source"] == "europepmc"), None)
    print(f"    Europe PMC entry: {ep}")
    assert ep is not None, "europepmc missing from check_sources"
    assert ep["status"] == "connected", f"Expected connected, got {ep['status']}"

asyncio.run(src_check())

print("\n" + "=" * 64)
print("ALL EUROPE PMC TESTS PASSED")
print("=" * 64)
