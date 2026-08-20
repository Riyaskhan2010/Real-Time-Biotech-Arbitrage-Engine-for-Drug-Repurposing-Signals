# -*- coding: utf-8 -*-
"""Check exact structure of UniProt result items (no fields param)."""
import asyncio, httpx, json

async def main():
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
        # Human TP53 — P04637 — gold standard test
        r = await c.get("https://rest.uniprot.org/uniprotkb/P04637",
                        params={"format": "json"},
                        headers={"Accept": "application/json"})
        data = r.json()
        print("=== P04637 entry top-level keys ===")
        print(list(data.keys()))
        # Show comments summary
        comments = data.get("comments", [])
        ctypes = list({c.get("commentType") for c in comments})
        print(f"Comment types: {ctypes}")
        # Show genes
        genes = data.get("genes", [])
        print(f"Genes: {[g.get('geneName',{}).get('value') for g in genes]}")
        # Show organism
        org = data.get("organism", {})
        print(f"Organism: {org.get('scientificName')} / {org.get('commonName')}")
        # Show protein desc
        pd = data.get("proteinDescription", {})
        rn = pd.get("recommendedName", {})
        fn = rn.get("fullName", {})
        print(f"Protein: {fn.get('value')}")
        # Show sequence
        seq = data.get("sequence", {})
        print(f"Sequence length key: {seq.get('length')} | value key: {'value' in seq}")

        # Now test search with valid fields only
        print("\n=== Search with valid fields only ===")
        valid_fields = "accession,reviewed,id,protein_name,gene_names,organism_name,function,cc_disease,cc_subcellular_location,go"
        r2 = await c.get("https://rest.uniprot.org/uniprotkb/search",
                         params={"query":"TP53","format":"json","size":"2","fields":valid_fields},
                         headers={"Accept":"application/json"})
        print(f"HTTP: {r2.status_code}")
        if r2.status_code == 200:
            d2 = r2.json()
            results = d2.get("results",[])
            print(f"Results: {len(results)}")
            if results:
                print(f"Keys: {list(results[0].keys())}")

asyncio.run(main())
