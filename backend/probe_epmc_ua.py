# -*- coding: utf-8 -*-
"""Test Europe PMC with different User-Agent strings and request headers."""
import asyncio, httpx

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
PARAMS = {"query": "metformin", "format": "json", "pageSize": "3", "resultType": "lite"}

UAS = [
    ("no UA",          None),
    ("python-httpx",   "python-httpx/0.27.0"),
    ("Mozilla",        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
    ("python-urllib",  "Python-urllib/3.12"),
    ("curl",           "curl/8.5.0"),
    ("Java",           "Java/17.0.2"),
]

async def main():
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
        for label, ua in UAS:
            headers = {}
            if ua:
                headers["User-Agent"] = ua
            r = await c.get(BASE, params=PARAMS, headers=headers)
            data = r.json() if r.content else {}
            items = data.get("resultList", {}).get("result", [])
            keys  = list(data.keys())
            print(f"UA={label:20} HTTP={r.status_code} keys={keys} items={len(items)}")

asyncio.run(main())
