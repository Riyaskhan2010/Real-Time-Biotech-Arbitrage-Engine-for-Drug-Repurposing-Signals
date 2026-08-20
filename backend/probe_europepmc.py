# -*- coding: utf-8 -*-
"""Raw Europe PMC API probe to diagnose zero-record issue."""
import sys, os, asyncio, json
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))
import httpx

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

async def probe(query, **extra):
    params = {"query": query, "format": "json", "pageSize": 3, "resultType": "core", **extra}
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(BASE, params=params)
    print(f"  HTTP {r.status_code}  query={query!r}  params_extra={extra}")
    if r.status_code == 200:
        d = r.json()
        total = d.get("hitCount", d.get("resultList", {}).get("total", "?"))
        items = d.get("resultList", {}).get("result", [])
        print(f"  hitCount={total}  items_in_page={len(items)}")
        if items:
            i = items[0]
            print(f"  First: pmid={i.get('pmid')} doi={i.get('doi')} title={str(i.get('title',''))[:60]}")
            print(f"  Keys in first item: {list(i.keys())[:15]}")
        else:
            # Show raw response structure
            print(f"  Empty result. Raw keys: {list(d.keys())}")
            raw = json.dumps(d, indent=2)[:800]
            print(f"  Raw response:\n{raw}")
    else:
        print(f"  Body: {r.text[:300]}")
    print()

async def main():
    print("=== Europe PMC Raw API Probe ===\n")
    # Try several query styles
    await probe("metformin cancer")
    await probe('"metformin" AND "cancer"')
    await probe("metformin")
    await probe("drug repurposing")
    await probe("aspirin alzheimer", resultType="lite")

asyncio.run(main())
