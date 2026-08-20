# -*- coding: utf-8 -*-
"""Identify which Europe PMC parameter causes empty response."""
import asyncio, httpx, json

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

TESTS = [
    ("no sort",         {"query":"metformin","format":"json","pageSize":"3","resultType":"core"}),
    ("sort date:desc",  {"query":"metformin","format":"json","pageSize":"3","resultType":"core","sort":"date:desc"}),
    ("sort CITED desc", {"query":"metformin","format":"json","pageSize":"3","resultType":"core","sort":"CITED desc"}),
    ("sort FIRST_PDATE desc", {"query":"metformin","format":"json","pageSize":"3","resultType":"core","sort":"FIRST_PDATE desc"}),
    ("lite no sort",    {"query":"metformin","format":"json","pageSize":"3","resultType":"lite"}),
    ("lite sort date",  {"query":"metformin","format":"json","pageSize":"3","resultType":"lite","sort":"date:desc"}),
]

async def run():
    async with httpx.AsyncClient(timeout=20) as c:
        for label, params in TESTS:
            r = await c.get(BASE, params=params)
            data = r.json()
            keys = list(data.keys())[:5]
            items = data.get("resultList",{}).get("result",[])
            hit = data.get("hitCount","?")
            print(f"[{label:30}] HTTP={r.status_code} keys={keys} hitCount={hit} items={len(items)}")

asyncio.run(run())
