"""Remove all fake DOI, PMID, NCT, and source URLs from demo evidence records."""
import sqlite3

DB = (
    "c:/Users/moham/OneDrive/Documents/kiro/"
    "Real-Time Biotech Arbitrage Engine for Drug Repurposing Signals/"
    "backend/bioarbitrage.db"
)

db = sqlite3.connect(DB)

# 1. Wipe fake identifiers from all demo evidence
db.execute("""
    UPDATE evidence
    SET source_url  = NULL,
        doi         = NULL,
        pmid        = NULL,
        nct_id      = NULL,
        source_name = 'Simulated source — no external link'
    WHERE is_demo_data = 1
""")

# 2. Update titles to clearer simulated labels
updates = [
    (1, "[DEMO] AMPK Activation by Metformin — Simulated Preclinical Evidence Record",
        "[Simulated Author A]", "[Simulated Journal — Demo Data]"),
    (2, "[DEMO] Metformin Aging Trial — Simulated Clinical Trial Record",
        "[Simulated Principal Investigator]", "[Simulated Registry Entry — Demo Data]"),
    (3, "[DEMO] Metformin Use and Alzheimer's Risk — Simulated Epidemiological Evidence Record",
        "[Simulated Author C]", "[Simulated Journal — Demo Data]"),
    (4, "[DEMO] Network Medicine Analysis — Simulated Drug Repurposing Candidate Record",
        "[Simulated Author F]", "[Simulated Journal — Demo Data]"),
    (5, "[DEMO] Real-World Observational Study — Simulated Large-Scale Evidence Record",
        "[Simulated Author H]", "[Simulated Journal — Demo Data]"),
    (6, "[DEMO] Doxycycline MMP Inhibition in GBM — Simulated In Vitro Evidence Record",
        "[Simulated Author J]", "[Simulated Journal — Demo Data]"),
]

for eid, title, author, journal in updates:
    db.execute(
        "UPDATE evidence SET title=?, journal=? WHERE id=?",
        (title, journal, eid)
    )

db.commit()
print("Updated all evidence records")

# 3. Verify — ensure nothing fake remains
rows = db.execute(
    "SELECT id, title, source_url, doi, pmid, nct_id, source_name FROM evidence"
).fetchall()

fake_found = False
for row in rows:
    eid, title, url, doi, pmid, nct, sname = row
    issues = []
    if url:  issues.append(f"url={url}")
    if doi:  issues.append(f"doi={doi}")
    if pmid: issues.append(f"pmid={pmid}")
    if nct:  issues.append(f"nct={nct}")
    if issues:
        print(f"  STILL HAS IDS [{eid}]: {issues}")
        fake_found = True
    else:
        print(f"  CLEAN [{eid}] {title[:65]} | {sname}")

if not fake_found:
    print("\nALL FAKE IDENTIFIERS REMOVED FROM DATABASE")

db.close()
