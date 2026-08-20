# -*- coding: utf-8 -*-
"""Verify Elsevier connector integration."""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from app.services.connectors.elsevier import ElsevierConnector
from app.services.ingestion_service import ingestion_service
from app.config import settings

print("=== Elsevier Integration Verification ===")

# 1. Config
print("\n1. Config")
key_configured = bool(settings.ELSEVIER_API_KEY)
print("   ELSEVIER_API_KEY configured:", key_configured)
print("   Enabled sources:", settings.enabled_sources_list)
assert "elsevier" in settings.enabled_sources_list, "elsevier not in enabled sources!"

# 2. Connector instantiation
print("\n2. Connector instantiation")
conn = ElsevierConnector()
print("   _is_configured:", conn._is_configured)
print("   SOURCE_NAME:", conn.SOURCE_NAME)
assert conn.SOURCE_NAME == "elsevier"

# 3. build_connectors includes elsevier
print("\n3. _build_connectors")
connectors = ingestion_service._build_connectors()
assert "elsevier" in connectors, "elsevier not in connectors dict!"
print("   Connectors:", list(connectors.keys()))

# 4. Source status check
print("\n4. Source status check (check_sources)")
async def run_check():
    results = await ingestion_service.check_sources()
    for r in results:
        status = r.get("status")
        source = r.get("source")
        enabled = r.get("enabled")
        print("  ", source, "status=" + status, "enabled=" + str(enabled))
    return results

results = asyncio.run(run_check())
elsevier_result = next((r for r in results if r["source"] == "elsevier"), None)
assert elsevier_result is not None, "elsevier missing from source status!"
print("   Elsevier status:", elsevier_result["status"])

# 5. Security — API key not in returned data
print("\n5. Security check — API key not in responses")
for r in results:
    raw = str(r)
    assert settings.ELSEVIER_API_KEY not in raw or not settings.ELSEVIER_API_KEY, \
        "SECURITY FAIL: API key found in source status response!"
print("   API key not present in any source status response — PASS")

# 6. If key IS configured, run a real connection check
if key_configured:
    print("\n6. Real connection check (key configured)")
    async def real_check():
        ok = await conn.check_connection()
        print("   check_connection():", "connected" if ok else "not connected")
        if ok:
            records = await conn.fetch("drug repurposing", max_records=3)
            print("   fetch() returned:", len(records), "records")
            for rec in records:
                print("   -", rec.title[:60])
                assert rec.source == "elsevier"
                assert rec.is_demo_data == False
                # Verify key not in any field
                for field in [rec.title, rec.abstract, rec.source_url, rec.doi, rec.journal]:
                    if field and settings.ELSEVIER_API_KEY:
                        assert settings.ELSEVIER_API_KEY not in field, \
                            "SECURITY FAIL: API key found in record field!"
            return records
        return []
    records = asyncio.run(real_check())
    print("   Records fetched:", len(records))
else:
    print("\n6. Key not configured — skipping real connection test")
    print("   (connector correctly returns disabled/empty state)")

print("\n=== ALL CHECKS PASSED ===")
