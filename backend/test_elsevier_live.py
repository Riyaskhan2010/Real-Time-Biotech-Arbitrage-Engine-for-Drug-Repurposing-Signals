# -*- coding: utf-8 -*-
"""
Elsevier live connectivity and ingestion test.
Run AFTER adding ELSEVIER_API_KEY to backend/.env and restarting the backend.

Usage:
    python test_elsevier_live.py

Never prints the API key value.
"""
import sys, os, asyncio

sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

# ── Force fresh settings load (important: run after updating .env) ────────────
# Remove any cached settings module so pydantic-settings re-reads .env
for mod in list(sys.modules.keys()):
    if "app.config" in mod or "app.services" in mod:
        del sys.modules[mod]

from app.config import settings

print("=" * 60)
print("ELSEVIER LIVE CONNECTIVITY TEST")
print("=" * 60)

# ── Step 1: Key presence ──────────────────────────────────────────────────────
print("\n[1] Key presence")
key_present = bool(settings.ELSEVIER_API_KEY)
key_len     = len(settings.ELSEVIER_API_KEY)
print("    Key loaded from .env:", key_present)
print("    Key length:", key_len)

if not key_present:
    print()
    print("  ISSUE: ELSEVIER_API_KEY is still empty in backend/.env")
    print()
    print("  To fix:")
    print("    1. Open backend/.env")
    print("    2. Find the line:  ELSEVIER_API_KEY=")
    print("    3. Add your key:   ELSEVIER_API_KEY=<your-key-here>")
    print("    4. Save the file")
    print("    5. Restart the backend: uvicorn main:app --reload --port 8000")
    print("    6. Re-run this script")
    print()
    sys.exit(1)

# ── Step 2: Connector ─────────────────────────────────────────────────────────
print("\n[2] Connector configuration")
from app.services.connectors.elsevier import ElsevierConnector
conn = ElsevierConnector()
print("    _is_configured:", conn._is_configured)
assert conn._is_configured, "Key present in settings but connector not configured — import error?"

# ── Step 3: Real API check_connection() ──────────────────────────────────────
print("\n[3] check_connection() — lightweight probe")
async def do_check():
    return await conn.check_connection()

connected = asyncio.run(do_check())
print("    Connected:", connected)

if not connected:
    print()
    print("  API probe returned False. Possible causes:")
    print("    - 401/403: Key is invalid or lacks ScienceDirect Search entitlement.")
    print("    - Network: Cannot reach api.elsevier.com.")
    print("    - Rate limit: Too many requests.")
    print("  Run with verbose logging to see HTTP status:")
    print("    python -c \"import logging; logging.basicConfig(level=logging.DEBUG)\" then re-run")
    sys.exit(1)

# ── Step 4: Real fetch() ──────────────────────────────────────────────────────
print("\n[4] fetch() — real article metadata")
async def do_fetch():
    return await conn.fetch("drug repurposing alzheimer", max_records=5)

records = asyncio.run(do_fetch())
print("    Records fetched:", len(records))
for r in records:
    assert r.source == "elsevier"
    assert r.is_demo_data == False
    assert r.source_id, "Missing source_id"
    # Confirm key not in any record field
    if settings.ELSEVIER_API_KEY:
        for field_val in [r.title, r.abstract, r.doi, r.source_url, r.journal]:
            if field_val:
                assert settings.ELSEVIER_API_KEY not in field_val, \
                    "SECURITY: API key leaked into record field!"
    print("    +", r.title[:70])
    print("      source_id:", r.source_id[:30])
    print("      doi:", r.doi)
    print("      date:", r.publication_date)
    print("      LIVE badge:", not r.is_demo_data)

# ── Step 5: Run through ingestion pipeline ───────────────────────────────────
print("\n[5] Pipeline processing (in-memory test DB)")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.drug import Drug
from app.models.disease import Disease
from app.services.ingestion_service import IngestionService
from app.utils.auth import get_password_hash
from app.models.user import User

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
db = Session()

user = User(email="t@t.t", username="t", full_name="T",
            hashed_password=get_password_hash("pw"), role="researcher", is_active=True)
db.add(user)
drug = Drug(name="Metformin", molecular_targets=["AMPK"], pathways=["mTOR signaling"],
            fda_status="Approved", approved_indications=["Type 2 Diabetes"])
db.add(drug)
disease = Disease(name="Alzheimer's Disease", affected_pathways=["mTOR signaling"])
db.add(disease)
db.commit()

svc = IngestionService()
outcomes = {"duplicate": 0, "new_matched": 0, "new_novel": 0, "new_unmatched": 0}
for rec in records:
    out = svc._process_record(db, rec)
    outcomes[out] = outcomes.get(out, 0) + 1
    print(f"    [{rec.source_id[:20]}] outcome={out}")

print("    Outcomes:", outcomes)
db.close()

# ── Step 6: check_sources with key present ───────────────────────────────────
print("\n[6] check_sources() with configured key")
async def do_check_sources():
    return await svc.check_sources()

src_results = asyncio.run(do_check_sources())
for r in src_results:
    print(f"    {r['source']:25} status={r.get('status')}  enabled={r.get('enabled')}")

el = next((r for r in src_results if r["source"] == "elsevier"), None)
print("\n    Elsevier entry:", el)

print("\n" + "=" * 60)
print("ALL ELSEVIER LIVE TESTS PASSED")
print("=" * 60)
print()
print("Next steps:")
print("  1. Restart backend if still running with empty key")
print("  2. Open http://localhost:5173 → Settings → Data Sources")
print("  3. Elsevier (ScienceDirect) should now show: Connected")
print("  4. Dashboard → Research Monitor → Run Live Ingestion")
print("  5. Elsevier records will appear with LIVE badge")
