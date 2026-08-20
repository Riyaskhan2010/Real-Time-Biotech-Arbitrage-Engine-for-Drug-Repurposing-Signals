# -*- coding: utf-8 -*-
"""
Elsevier disabled root-cause diagnostics.
Checks config loading, connector state, and API connectivity.
NEVER prints the key value — only reports presence/length.
"""
import sys, os, asyncio

sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

print("=" * 60)
print("ELSEVIER DISABLED — ROOT CAUSE DIAGNOSTICS")
print("=" * 60)

# ── 1. Raw .env inspection ───────────────────────────────────────
print("\n[1] .env file")
env_path = os.path.join(os.path.dirname(__file__), ".env")
print("    Path:", env_path)
print("    Exists:", os.path.exists(env_path))

elsevier_line_found = False
elsevier_has_value  = False
if os.path.exists(env_path):
    with open(env_path) as f:
        for lineno, line in enumerate(f, 1):
            stripped = line.strip()
            if stripped.startswith("ELSEVIER_API_KEY"):
                elsevier_line_found = True
                if "=" in stripped:
                    _, _, val = stripped.partition("=")
                    val = val.strip()
                    elsevier_has_value = bool(val and val != '""' and val != "''")
                    print(f"    Line {lineno}: ELSEVIER_API_KEY present, "
                          f"value length={len(val)}, "
                          f"has_value={elsevier_has_value}")
                break
if not elsevier_line_found:
    print("    ELSEVIER_API_KEY line NOT FOUND in .env")

# ── 2. pydantic-settings loading ─────────────────────────────────
print("\n[2] Settings (pydantic-settings)")
from app.config import settings
key_loaded = bool(settings.ELSEVIER_API_KEY)
key_len    = len(settings.ELSEVIER_API_KEY) if settings.ELSEVIER_API_KEY else 0
print("    settings.ELSEVIER_API_KEY loaded:", key_loaded)
print("    Key length:", key_len)
print("    Enabled sources:", settings.enabled_sources_list)
print("    'elsevier' in enabled_sources:", "elsevier" in settings.enabled_sources_list)

# ── 3. Connector _is_configured ──────────────────────────────────
print("\n[3] ElsevierConnector._is_configured")
from app.services.connectors.elsevier import ElsevierConnector
conn = ElsevierConnector()
print("    _api_key empty:", not conn._api_key)
print("    _is_configured:", conn._is_configured)

# ── 4. ingestion_service check_sources logic ─────────────────────
print("\n[4] check_sources() disabled logic in ingestion_service")
from app.services.ingestion_service import ingestion_service
connectors = ingestion_service._build_connectors()
print("    Connectors in dict:", list(connectors.keys()))
el = connectors.get("elsevier")
print("    Elsevier connector present:", el is not None)
if el:
    print("    el._is_configured:", el._is_configured)

# ── 5. Simulate check_sources for elsevier ───────────────────────
print("\n[5] Simulated check_sources() — elsevier branch")
async def sim_check():
    results = await ingestion_service.check_sources()
    for r in results:
        src = r.get("source", "")
        print(f"    {src:20}  status={r.get('status')}  enabled={r.get('enabled')}")
    el_result = next((r for r in results if r["source"] == "elsevier"), None)
    return el_result

el_status = asyncio.run(sim_check())
print("    Elsevier result:", el_status)

# ── 6. Real API connectivity test (if key is present) ────────────
print("\n[6] Elsevier API connectivity")
if not key_loaded:
    print("    SKIP — ELSEVIER_API_KEY is empty or not loaded by pydantic-settings.")
    print("    This is the root cause of 'disabled'.")
    print()
    print("    Diagnosis: The .env file has ELSEVIER_API_KEY=<value> but")
    print("    pydantic-settings is reading it as empty. Possible causes:")
    print("      a) The .env file was modified AFTER the backend started")
    print("         (uvicorn --reload re-reads code but NOT .env on change).")
    print("      b) There is a second .env file at a different path taking precedence.")
    print("      c) The key line has extra whitespace, quotes, or BOM encoding.")
    print("      d) The env variable is overridden by a system environment variable.")
else:
    print("    Key IS loaded by pydantic-settings — testing API...")
    import httpx
    async def test_api():
        headers = {
            "X-ELS-APIKey": conn._api_key,   # key used only here, never returned
            "Accept": "application/json",
        }
        url = "https://api.elsevier.com/content/search/sciencedirect"
        params = {"query": "drug repurposing", "count": 1, "field": "title"}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(url, headers=headers, params=params)
                print(f"    HTTP status: {r.status_code}")
                if r.status_code == 200:
                    data = r.json()
                    total = data.get("search-results", {}).get("opensearch:totalResults", "?")
                    print(f"    Response OK — total results: {total}")
                    return True, r.status_code
                elif r.status_code == 401:
                    print("    401 Unauthorized — API key is invalid or not activated.")
                    return False, r.status_code
                elif r.status_code == 403:
                    print("    403 Forbidden — key may lack ScienceDirect Search API entitlement.")
                    return False, r.status_code
                elif r.status_code == 429:
                    print("    429 Rate Limited.")
                    return False, r.status_code
                else:
                    print(f"    Unexpected status: {r.status_code}")
                    print(f"    Body (first 200 chars): {r.text[:200]}")
                    return False, r.status_code
        except Exception as e:
            print(f"    Exception: {type(e).__name__}: {e}")
            return False, None

    ok, http_status = asyncio.run(test_api())
    print("    API reachable:", ok)

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
