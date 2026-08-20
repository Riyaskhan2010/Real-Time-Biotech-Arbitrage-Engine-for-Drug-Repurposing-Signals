# -*- coding: utf-8 -*-
"""Probe UniProt REST API to find the working endpoint and parameter set."""
import asyncio, httpx

TESTS = [
    # Standard search
    ("fields param",   "https://rest.uniprot.org/uniprotkb/search",
     {"query":"TP53","format":"json","size":"3",
      "fields":"accession,reviewed,id,protein_name,gene_names,organism_name,sequence_length"}),
    # Minimal — no fields
    ("no fields",      "https://rest.uniprot.org/uniprotkb/search",
     {"query":"TP53","format":"json","size":"3"}),
    # Tab-separated (TSV) format
    ("tsv format",     "https://rest.uniprot.org/uniprotkb/search",
     {"query":"TP53","format":"tsv","size":"3",
      "fields":"accession,gene_names,protein_name"}),
    # Direct accession lookup
    ("accession",      "https://rest.uniprot.org/uniprotkb/P04637",
     {"format":"json"}),
    # Older endpoint
    ("old search",     "https://www.uniprot.org/uniprot/",
     {"query":"TP53 AND organism_id:9606","format":"json"}),
    # Reviewed only
    ("reviewed only",  "https://rest.uniprot.org/uniprotkb/search",
     {"query":"TP53 AND reviewed:true","format":"json","size":"3"}),
]

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "BioArbitrage/1.0 (research-support-tool)",
}

async def main():
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
        for label, url, params in TESTS:
            try:
                r = await c.get(url, params=params, headers=HEADERS)
                body = r.text[:300]
                print(f"\n[{label}]  HTTP={r.status_code}  url={str(r.url)[:80]}")
                if r.status_code == 200:
                    try:
                        data = r.json()
                        keys = list(data.keys())[:6]
                        results = data.get("results", [])
                        print(f"  JSON keys={keys}  results={len(results)}")
                        if results:
                            first = results[0]
                            acc = first.get("primaryAccession","?")
                            gn = first.get("genes",[])
                            print(f"  First: acc={acc}  genes_count={len(gn)}")
                    except Exception:
                        print(f"  NOT JSON: {body[:150]}")
                else:
                    print(f"  Error body: {body[:200]}")
            except Exception as e:
                print(f"[{label}]  EXCEPTION: {type(e).__name__}: {str(e)[:80]}")

asyncio.run(main())
