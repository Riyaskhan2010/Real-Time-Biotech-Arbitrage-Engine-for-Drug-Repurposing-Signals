# -*- coding: utf-8 -*-
"""Find the current working Europe PMC endpoint."""
import asyncio, httpx

TESTS = [
    ("ebi old",       "GET",  "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
     {"query":"metformin","format":"json","pageSize":"2"}),
    ("europepmc.org", "GET",  "https://europepmc.org/webservices/rest/search",
     {"query":"metformin","format":"json","pageSize":"2"}),
    ("www.europepmc", "GET",  "https://www.europepmc.org/webservices/rest/search",
     {"query":"metformin","format":"json","pageSize":"2"}),
    ("ebi v2",        "GET",  "https://www.ebi.ac.uk/europepmc/webservices/rest/v2/search",
     {"query":"metformin","format":"json","pageSize":"2"}),
    ("ebi plus",      "GET",  "https://www.ebi.ac.uk/europepmc/plus/webservices/rest/search",
     {"query":"metformin","format":"json","pageSize":"2"}),
    ("ebi articles",  "GET",  "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
     {"query":"metformin","format":"json","pageSize":"2","resultType":"core","cursorMark":"*"}),
]

async def main():
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
        for label, method, url, params in TESTS:
            try:
                r = await c.get(url, params=params)
                body = r.text[:300]
                print(f"[{label:20}] {r.status_code} final_url={str(r.url)[:70]}")
                print(f"   body[:200]={body[:200]}")
                print()
            except Exception as e:
                print(f"[{label:20}] ERROR: {e}")

asyncio.run(main())
