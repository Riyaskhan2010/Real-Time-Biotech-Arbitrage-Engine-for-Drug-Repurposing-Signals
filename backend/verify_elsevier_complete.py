# -*- coding: utf-8 -*-
"""
Complete Elsevier verification.
Checks: env loading, connector state, API connectivity (if key present),
        check_sources granular status, ingestion pipeline smoke test.
Never prints the key value.
"""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from app.config import settings
from app.services.connectors.elsevier import ElsevierConnector
from app.services.ingestion_service import ingestion_service

print("=" * 64)
print("ELSEVIER COMPLETE VERIFICATION")
print("=" * 64)

# ── 1. Key state ──────────────────────────────────────────────────
print("\n[1] ELSEVIER_API_KEY in .env")
key_loaded = bool(settings.ELSEVIER_API_KEY)
key_len    = len(settings.ELSEVIER_API_KEY) if settings.ELSEVIER_API_KEY else 0
print(f"    Loaded: {key_loaded}  |  Length: {key_len}")
print(f"    'elsevier' in enabled_sources: {'elsevier' in settings.enabled_sources_list}")

# ── 2. Connector ──────────────────────────────────────────────────
print("\n[2] ElsevierConnector")
conn = ElsevierConnector()
print(f"    _is_configured: {conn._is_configured}")

# ── 3. check_sources granular status ────────────────────────────
print("\n[3] check_sources() — all 5 sources")
async def run_check():
    return await ingestion_service.check_sources()
results = asyncio.run(run_check())
for r in results:
    err = r.get("error", "")
    err_short = (f" — {err[:60]}" if err else "")
    print(f"    {r['source']:25}  status={r['status']:15}  enabled={r['enabled']}{err_short}")

el = next((r for r in results if r["source"] == "elsevier"), None)
print(f"\n    Elsevier full result: {el}")

# ── 4. Real API test (only if key present) ───────────────────────
print("\n[4] Elsevier API connectivity test")
if not key_loaded:
    print("    SKIPPED — key not loaded.")
    print()
    print("  ROOT CAUSE: ELSEVIER_API_KEY= is empty in backend/.env")
    print()
    print("  ACTION REQUIRED:")
    print("    1. Open:  backend/.env")
    print("    2. Change:  ELSEVIER_API_KEY=")
    print("       To:      ELSEVIER_API_KEY=<your-key>")
    print("    3. Save the file.")
    print("    4. Restart the backend:")
    print("         uvicorn main:app --reload --port 8000")
    print("    5. Re-run this script to verify.")
    print()
    print("  Once the key is set and backend restarted, Elsevier will show")
    print("  'Connected' in Settings → Data Sources (if the key is valid).")
else:
    async def run_api_test():
        print("    Running check_connection_detail()...")
        detail = await conn.check_connection_detail()
        print(f"    Result: {detail}")

        if detail.get("ok"):
            print("    Running fetch() for 'drug repurposing alzheimer' (max 5)...")
            records = await conn.fetch("drug repurposing alzheimer", max_records=5)
            print(f"    Records fetched: {len(records)}")
            for i, r in enumerate(records, 1):
                print(f"      {i}. [{r.source_id[:25]}]  {r.title[:65]}")
                print(f"         DOI={r.doi}  date={r.publication_date}  live={not r.is_demo_data}")
                # Security: key must never appear in record fields
                if settings.ELSEVIER_API_KEY:
                    for fv in [r.title, r.abstract, r.doi, r.source_url]:
                        if fv and settings.ELSEVIER_API_KEY in fv:
                            print("         SECURITY FAIL: key in record field!")
                            sys.exit(1)
            return records
        else:
            reason = detail.get("reason")
            code   = detail.get("status_code")
            if reason == "invalid_key":
                print(f"    HTTP {code} — Key is set but rejected by Elsevier.")
                print("    Possible causes:")
                print("      - Key not yet activated (may take minutes after creation)")
                print("      - Key lacks ScienceDirect Search API entitlement")
                print("      - Wrong key pasted (check for leading/trailing spaces)")
            elif reason == "rate_limited":
                print("    HTTP 429 — Rate limited. Try again in a minute.")
            elif reason == "timeout":
                print("    Timeout — Cannot reach api.elsevier.com")
            else:
                print(f"    Error: {reason}")
            return []

    records = asyncio.run(run_api_test())

    if records:
        print("\n[5] Pipeline smoke test (in-memory DB)")
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.database import Base
        from app.models.drug import Drug
        from app.models.disease import Disease
        from app.models.user import User
        from app.utils.auth import get_password_hash
        from app.services.ingestion_service import IngestionService

        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        db = sessionmaker(bind=engine)()
        db.add(User(email="t@t.t", username="t", full_name="T",
                    hashed_password=get_password_hash("pw"), role="researcher", is_active=True))
        db.add(Drug(name="Metformin", molecular_targets=["AMPK"],
                    pathways=["AMPK signaling"], fda_status="Approved",
                    approved_indications=["Type 2 Diabetes"]))
        db.add(Disease(name="Alzheimer's Disease", affected_pathways=["mTOR signaling"]))
        db.commit()

        svc = IngestionService()
        outcomes = {}
        for rec in records:
            out = svc._process_record(db, rec)
            outcomes[out] = outcomes.get(out, 0) + 1
        print(f"    Outcomes: {outcomes}")
        from app.models.research_source import ResearchSource
        saved = db.query(ResearchSource).filter_by(source_type="elsevier").count()
        print(f"    Elsevier records saved to DB: {saved}")
        db.close()

print("\n" + "=" * 64)
print("VERIFICATION COMPLETE")
print("=" * 64)
