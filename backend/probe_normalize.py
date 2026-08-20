# -*- coding: utf-8 -*-
"""Test _normalize against a real API item to confirm field parsing."""
import sys, os, asyncio, json
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

import httpx

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

async def main():
    # Step 1: fetch real items
    params = {"query": "metformin cancer", "format": "json",
              "pageSize": 3, "resultType": "core", "sort": "date:desc"}
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(BASE, params=params)
    data = r.json()
    items = data.get("resultList", {}).get("result", [])
    print(f"Raw items from API: {len(items)}")

    # Step 2: run through the CURRENT connector _normalize
    # Force reimport to pick up latest file on disk
    if "app.services.connectors.europepmc" in sys.modules:
        del sys.modules["app.services.connectors.europepmc"]
    from app.services.connectors.europepmc import EuropePMCConnector
    conn = EuropePMCConnector()

    print("\nNormalization test:")
    for i, item in enumerate(items):
        rec = conn._normalize(item)
        if rec:
            print(f"  [{i}] PASS  pmid={rec.pmid} doi={rec.doi} title={rec.title[:60]}")
            print(f"        date={rec.publication_date} journal={rec.journal}")
            print(f"        authors={rec.authors[:2]} keywords={rec.extracted_mechanisms[:3]}")
            print(f"        abstract_chars={len(rec.abstract) if rec.abstract else 0}")
            print(f"        source_url={rec.source_url}")
        else:
            print(f"  [{i}] FAIL (returned None) — item keys: {list(item.keys())[:10]}")

    # Step 3: full fetch()
    print("\nFull fetch() test:")
    records = await conn.fetch("metformin cancer", max_records=5)
    print(f"  Records returned: {len(records)}")
    for r in records:
        print(f"  + {r.title[:65]}")

asyncio.run(main())
