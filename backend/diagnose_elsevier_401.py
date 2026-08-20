# -*- coding: utf-8 -*-
"""
Elsevier 401 deep diagnostic.
Tests multiple endpoints and auth methods.
NEVER prints the API key value.
"""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

import httpx
from app.config import settings

print("=" * 68)
print("ELSEVIER 401 DIAGNOSTIC")
print("=" * 68)

KEY = settings.ELSEVIER_API_KEY
print(f"\nKey loaded:   {bool(KEY)}")
print(f"Key length:   {len(KEY)}")
print(f"Key is ASCII: {KEY.isascii() if KEY else 'n/a'}")
print(f"Key stripped == key: {KEY.strip() == KEY if KEY else 'n/a'}")

if not KEY:
    print("\nNo key — cannot test. Add ELSEVIER_API_KEY to backend/.env")
    sys.exit(1)

TESTS = [
    # ── ScienceDirect Search v2 ───────────────────────────────────────────────
    {
        "name": "ScienceDirect Search v2 — X-ELS-APIKey header",
        "url":  "https://api.elsevier.com/content/search/sciencedirect",
        "headers": {"X-ELS-APIKey": KEY, "Accept": "application/json"},
        "params": {"query": "metformin", "count": 1},
    },
    {
        "name": "ScienceDirect Search v2 — apiKey query param",
        "url":  "https://api.elsevier.com/content/search/sciencedirect",
        "headers": {"Accept": "application/json"},
        "params": {"query": "metformin", "count": 1, "apiKey": KEY},
    },
    # ── Scopus Search (different product, same key) ───────────────────────────
    {
        "name": "Scopus Search — X-ELS-APIKey header",
        "url":  "https://api.elsevier.com/content/search/scopus",
        "headers": {"X-ELS-APIKey": KEY, "Accept": "application/json"},
        "params": {"query": "metformin AND alzheimer", "count": 1},
    },
    {
        "name": "Scopus Search — apiKey query param",
        "url":  "https://api.elsevier.com/content/search/scopus",
        "headers": {"Accept": "application/json"},
        "params": {"query": "metformin AND alzheimer", "count": 1, "apiKey": KEY},
    },
]

async def run():
    results = []
    async with httpx.AsyncClient(timeout=15) as client:
        for t in TESTS:
            print(f"\n--- {t['name']}")
            print(f"    URL:    {t['url']}")
            print(f"    Auth:   {'X-ELS-APIKey header' if 'X-ELS-APIKey' in t['headers'] else 'apiKey query param'}")
            # Confirm key NOT in printed params (remove before display)
            safe_params = {k: v for k, v in t["params"].items() if k != "apiKey"}
            print(f"    Params: {safe_params}")
            try:
                r = await client.get(t["url"], headers=t["headers"], params=t["params"])
                print(f"    HTTP:   {r.status_code}")
                # Show sanitised error body — never print key
                body = r.text[:400] if r.status_code != 200 else "(200 OK — body omitted)"
                if KEY in body:
                    body = body.replace(KEY, "[KEY_REDACTED]")
                print(f"    Body:   {body}")
                results.append({"name": t["name"], "status": r.status_code,
                                 "ok": r.status_code == 200})
            except Exception as e:
                print(f"    Error:  {type(e).__name__}: {e}")
                results.append({"name": t["name"], "status": None, "ok": False})

    print("\n" + "=" * 68)
    print("SUMMARY")
    print("=" * 68)
    any_ok = False
    for res in results:
        mark = "PASS" if res["ok"] else "FAIL"
        print(f"  [{mark}] {res['name']} — HTTP {res['status']}")
        if res["ok"]:
            any_ok = True

    print()
    if any_ok:
        print(">>> At least one endpoint works. Connector should use that endpoint/auth.")
    else:
        all_401 = all(r["status"] == 401 for r in results if r["status"])
        if all_401:
            print(">>> All endpoints return 401.")
            print(">>> The application code and auth method are CORRECT.")
            print(">>> The issue is on the Elsevier account/entitlement side:")
            print("    1. Log into https://dev.elsevier.com/")
            print("    2. Go to My API Keys -> select your key")
            print("    3. Check: Is the key status 'Active'?")
            print("    4. Check entitlements — ScienceDirect Search AND/OR Scopus Search")
            print("       must be listed.")
            print("    5. If you just created the key, wait 5-10 minutes and retry.")
            print("    6. If the key was created under an institutional account,")
            print("       the institution must enable API access.")
        else:
            print(">>> Mixed results — see per-endpoint output above.")

asyncio.run(run())
