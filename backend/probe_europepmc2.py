# -*- coding: utf-8 -*-
"""Check exact structure of core result items."""
import sys, os, asyncio, json
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))
import httpx

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

async def main():
    params = {"query": "metformin cancer", "format": "json",
              "pageSize": 2, "resultType": "core"}
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(BASE, params=params)
    d = r.json()
    items = d.get("resultList", {}).get("result", [])
    print(f"Items: {len(items)}")
    for i, item in enumerate(items):
        print(f"\n--- Item {i} ---")
        print(json.dumps(item, indent=2)[:2000])

asyncio.run(main())
