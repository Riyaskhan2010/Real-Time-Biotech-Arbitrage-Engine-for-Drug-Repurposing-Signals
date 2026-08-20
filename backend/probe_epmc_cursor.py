# -*- coding: utf-8 -*-
"""Test Europe PMC v6 with cursorMark and different parameter combinations."""
import asyncio, httpx, json

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

TESTS = [
    # v6 may require cursorMark
    {"query":"metformin","format":"json","pageSize":"5","resultType":"lite","cursorMark":"*"},
    {"query":"metformin","format":"json","pageSize":"5","cursorMark":"*"},
    # Try the sort in query string (documented method)
    {"query":"metformin sort_date:y","format":"json","pageSize":"5","resultType":"lite"},
    # Try page parameter instead
    {"query":"metformin","format":"json","pageSize":"5","resultType":"lite","page":"1"},
    # Try with explicit fields
    {"query":"p53","format":"json","pageSize":"3","resultType":"lite"},
    # Try no resultType at all
    {"query":"p53","format":"json","pageSize":"3"},
    # Try XML format
    {"query":"p53","format":"xml","pageSize":"3","resultType":"lite"},
    # Try HTTPS with different accept header (some APIs require it)
    # Done via headers arg
]

async def main():
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
        for i, params in enumerate(TESTS):
            try:
                headers = {"Accept": "application/json"}
                r = await c.get(BASE, params=params, headers=headers)
                print(f"\n[test {i}] params={params}")
                print(f"  HTTP={r.status_code} len={len(r.content)} content-type={r.headers.get('content-type','')[:40]}")
                if r.content:
                    body = r.text[:400]
                    try:
                        data = r.json()
                        keys = list(data.keys())
                        print(f"  JSON keys: {keys}")
                        rl = data.get("resultList",{})
                        items = rl.get("result",[]) if isinstance(rl,dict) else []
                        print(f"  resultList.result count: {len(items)}")
                        if items:
                            print(f"  First item keys: {list(items[0].keys())[:8]}")
                            print(f"  First pmid: {items[0].get('pmid')} title: {str(items[0].get('title',''))[:50]}")
                    except Exception:
                        print(f"  NOT JSON: {body[:200]}")
            except Exception as e:
                print(f"[test {i}] ERROR: {e}")

asyncio.run(main())
