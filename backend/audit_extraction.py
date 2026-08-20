# -*- coding: utf-8 -*-
"""
Entity extraction audit script.
Run: python audit_extraction.py   (from backend/)
"""
import os, sys, sqlite3, json
sys.path.insert(0, os.path.dirname(__file__))

DB = os.path.join(os.path.dirname(__file__), "bioarbitrage.db")
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

print("=" * 70)
print("AUDIT: Entity Extraction Quality")
print("=" * 70)

# 1. Drug names in DB
print("\n--- DRUGS IN DATABASE ---")
drugs = conn.execute("SELECT id, name, generic_name FROM drugs ORDER BY name").fetchall()
for d in drugs:
    print(f"  [{d['id']}] {d['name']}  (generic: {d['generic_name']})")

# 2. Disease names in DB
print("\n--- DISEASES IN DATABASE ---")
diseases = conn.execute("SELECT id, name FROM diseases ORDER BY name").fetchall()
for d in diseases:
    print(f"  [{d['id']}] {d['name']}")

# 3. Live research source records — what's been ingested
print("\n--- LIVE RESEARCH SOURCE RECORDS (sample) ---")
live = conn.execute(
    "SELECT id, source_type, title, extracted_drugs, extracted_diseases, "
    "extracted_mechanisms, is_processed "
    "FROM research_sources WHERE is_demo_data=0 ORDER BY id LIMIT 20"
).fetchall()

zero_drug_zero_disease = 0
has_drugs = 0
has_diseases = 0
has_both = 0

for r in live:
    drugs_json    = json.loads(r['extracted_drugs']    or '[]')
    diseases_json = json.loads(r['extracted_diseases'] or '[]')
    mechs_json    = json.loads(r['extracted_mechanisms'] or '[]')
    
    if not drugs_json and not diseases_json:
        zero_drug_zero_disease += 1
    if drugs_json:
        has_drugs += 1
    if diseases_json:
        has_diseases += 1
    if drugs_json and diseases_json:
        has_both += 1
    
    print(f"\n  [{r['source_type'].upper()}] {r['title'][:70]}")
    print(f"    Drugs:     {drugs_json or '[]'}")
    print(f"    Diseases:  {diseases_json or '[]'}")
    print(f"    Mechanisms:{mechs_json[:3] if mechs_json else '[]'}")

total_live = conn.execute("SELECT COUNT(*) FROM research_sources WHERE is_demo_data=0").fetchone()[0]
print(f"\n--- SUMMARY (of {total_live} live records, sample of {len(live)}) ---")
print(f"  Records with 0 drugs AND 0 diseases: {zero_drug_zero_disease}/{len(live)}")
print(f"  Records with extracted drugs:        {has_drugs}/{len(live)}")
print(f"  Records with extracted diseases:     {has_diseases}/{len(live)}")
print(f"  Records with both:                   {has_both}/{len(live)}")

# 4. Show the heuristic keyword lists vs real drug names in DB
print("\n--- HEURISTIC vs DB MISMATCH ANALYSIS ---")
heuristic_drugs = {
    "metformin", "rapamycin", "sirolimus", "sildenafil", "doxycycline",
    "lithium", "naltrexone", "thalidomide", "ivermectin", "aspirin",
    "ibuprofen", "temozolomide", "bevacizumab", "pembrolizumab",
}
heuristic_diseases = {
    "alzheimer", "glioblastoma", "diabetes", "cancer", "multiple sclerosis",
    "parkinson", "hypertension", "breast cancer", "pancreatic", "obesity",
}
db_drugs = {d['name'].lower() for d in conn.execute("SELECT name FROM drugs").fetchall()}
db_diseases = {d['name'].lower() for d in conn.execute("SELECT name FROM diseases").fetchall()}

print("  Drugs in heuristic list but not in DB canonical names:")
for d in sorted(heuristic_drugs):
    if not any(d in dbn for dbn in db_drugs):
        print(f"    '{d}' (not a canonical DB name — but may still match via LIKE)")
    else:
        print(f"    '{d}' OK")

print("\n  DB drugs NOT in heuristic keyword list:")
for dbn in sorted(db_drugs):
    if not any(h in dbn or dbn in h for h in heuristic_drugs):
        print(f"    '{dbn}' (MISSING from heuristic)")

# 5. Sample titles to see what text is being searched
print("\n--- SAMPLE TITLES OF 0-ENTITY RECORDS ---")
samples = conn.execute(
    "SELECT title, abstract FROM research_sources WHERE is_demo_data=0 "
    "AND (extracted_drugs='[]' OR extracted_drugs IS NULL) "
    "AND (extracted_diseases='[]' OR extracted_diseases IS NULL) LIMIT 10"
).fetchall()
for s in samples:
    print(f"  Title: {s['title'][:80]}")
    if s['abstract']:
        print(f"  Abstr: {s['abstract'][:120]}")
    print()

conn.close()
print("=" * 70)
print("Audit complete.")
