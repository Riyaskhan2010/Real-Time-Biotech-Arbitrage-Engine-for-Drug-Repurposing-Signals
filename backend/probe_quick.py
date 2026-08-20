# -*- coding: utf-8 -*-
import asyncio, httpx, traceback

async def main():
    hdrs = {"Accept": "application/json", "User-Agent": "BioArbitrage/1.0"}

    # EuropePMC — test with cursorMark
    print("=== EuropePMC with cursorMark ===")
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
        r = await c.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={"query":"metformin sort_date:y","format":"json","pageSize":"3",
                    "resultType":"core","cursorMark":"*"},
            headers=hdrs)
        print(f"HTTP {r.status_code}")
        if r.status_code != 200:
            print("Body:", r.text[:300])
        else:
            data = r.json()
            items = data.get("resultList",{}).get("result",[])
            print(f"items={len(items)} hitCount={data.get('hitCount','?')}")

    # EuropePMC — test WITHOUT cursorMark (like the probe_epmc_ua.py that worked)
    print("\n=== EuropePMC WITHOUT cursorMark ===")
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
        r = await c.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={"query":"metformin sort_date:y","format":"json","pageSize":"3",
                    "resultType":"core"},
            headers=hdrs)
        print(f"HTTP {r.status_code}")
        data = r.json()
        items = data.get("resultList",{}).get("result",[])
        print(f"items={len(items)} hitCount={data.get('hitCount','?')}")
        if items:
            print("First PMID:", items[0].get("pmid"))

    # UniProt — find NameError
    print("\n=== UniProt NameError trace ===")
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    from app.services.connectors.uniprot import UniProtConnector
    u = UniProtConnector()
    try:
        recs = await u.fetch("alzheimer", max_records=2)
        print(f"records={len(recs)}")
    except Exception:
        traceback.print_exc()

asyncio.run(main())
