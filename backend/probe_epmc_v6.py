# -*- coding: utf-8 -*-
"""Probe Europe PMC v6 API to find working endpoint and response structure."""
import asyncio, httpx

ENDPOINTS = [
    # Old REST API
    ("old search", "GET", "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
     {"query":"metformin","format":"json","pageSize":"3","resultType":"lite"}),
    # New REST API v6 / search
    ("v6 search", "GET", "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
     {"query":"metformin","format":"json","pageSize":"3"}),
    # Annotation/articles endpoint
    ("articles", "GET", "https://www.ebi.ac.uk/europepmc/webservices/rest/articles",
     {"query":"metformin","format":"json","pageSize":"3"}),
    # Check what the base URL returns
    ("base", "GET", "https://www.ebi.ac.uk/europepmc/webservices/rest/",
     {}),
    # Try POST search
    ("POST search", "POST", "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
     None),
]

async def run():
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
        for label, method, url, params in ENDPOINTS:
            try:
                if method == "POST":
                    r = await c.post(url,
                        json={"query":"metformin","pageSize":3,"resultType":"lite"},
                        headers={"Content-Type":"application/json","Accept":"application/json"})
                else:
                    r = await c.get(url, params=params)
                print(f"[{label:15}] {r.status_code} len={len(r.content)}")
                if r.content and len(r.content) > 0:
                    try:
                        data = r.json()
                        print(f"  JSON keys: {list(data.keys())[:8]}")
                        # Try to find results at various paths
                        for path in ["resultList","results","articles","entries","records"]:
                            v = data.get(path)
                            if v is not None:
                                items = v.get("result",[]) if isinstance(v,dict) else v
                                print(f"  [{path}] type={type(v).__name__} len={len(items) if isinstance(items,list) else '?'}")
                    except Exception as e:
                        print(f"  Not JSON: {r.text[:100]}")
                else:
                    print(f"  Empty body")
            except Exception as e:
                print(f"[{label:15}] ERROR: {e}")

asyncio.run(run())
