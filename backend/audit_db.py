"""Read-only database audit script — do not modify any data."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.evidence import Evidence
from app.models.signal import RepurposingSignal
from app.models.research_source import ResearchSource
from app.models.drug import Drug
from app.models.disease import Disease
from sqlalchemy import func

db = SessionLocal()

# ── 1. Evidence table ────────────────────────────────────────────────────────
print("=== EVIDENCE TABLE ===")
total_ev = db.query(Evidence).count()
live_ev  = db.query(Evidence).filter(Evidence.is_demo_data == False).count()
demo_ev  = db.query(Evidence).filter(Evidence.is_demo_data == True).count()
print(f"Total evidence records : {total_ev}")
print(f"  LIVE (is_demo=False) : {live_ev}")
print(f"  DEMO (is_demo=True)  : {demo_ev}")

print()
print("Evidence by data_source (live only):")
rows = (db.query(Evidence.data_source, func.count(Evidence.id))
        .filter(Evidence.is_demo_data == False)
        .group_by(Evidence.data_source).all())
for src, cnt in rows:
    print(f"  {str(src or '(none)'):<22} {cnt}")

print()
print("Evidence by evidence_type (live only):")
rows = (db.query(Evidence.evidence_type, func.count(Evidence.id))
        .filter(Evidence.is_demo_data == False)
        .group_by(Evidence.evidence_type).all())
for et, cnt in rows:
    print(f"  {str(et or '(none)'):<25} {cnt}")

print()
print("Sample live evidence records (first 10):")
samples = (db.query(Evidence)
           .filter(Evidence.is_demo_data == False)
           .limit(10).all())
for e in samples:
    print(f"  id={e.id} src={e.data_source:<15} type={e.evidence_type:<20} doi={e.doi} pmid={e.pmid}")
    print(f"    title={str(e.title or '')[:80]}")

# ── 2. Research sources table ────────────────────────────────────────────────
print()
print("=== RESEARCH SOURCES TABLE ===")
total_rs = db.query(ResearchSource).count()
live_rs  = db.query(ResearchSource).filter(ResearchSource.is_demo_data == False).count()
demo_rs  = db.query(ResearchSource).filter(ResearchSource.is_demo_data == True).count()
print(f"Total research source records : {total_rs}")
print(f"  LIVE : {live_rs}")
print(f"  DEMO : {demo_rs}")

print()
print("ResearchSource by source_type (all):")
rows = (db.query(ResearchSource.source_type, func.count(ResearchSource.id))
        .group_by(ResearchSource.source_type).all())
for st, cnt in rows:
    print(f"  {str(st or '(none)'):<22} {cnt}")

# ── 3. Signals ───────────────────────────────────────────────────────────────
print()
print("=== SIGNALS TABLE ===")
total_sig  = db.query(RepurposingSignal).count()
live_sigs  = db.query(RepurposingSignal).filter(RepurposingSignal.data_source == "live").count()
demo_sigs  = db.query(RepurposingSignal).filter(RepurposingSignal.data_source == "demo").count()
novel_sigs = db.query(RepurposingSignal).filter(RepurposingSignal.is_novel == True).count()
print(f"Total signals        : {total_sig}")
print(f"  data_source=live   : {live_sigs}")
print(f"  data_source=demo   : {demo_sigs}")
print(f"  is_novel=True      : {novel_sigs}")

print()
print("All signals (id | drug | disease | score | conf | data_source | live_ev | demo_ev):")
from sqlalchemy.orm import joinedload
sigs = (db.query(RepurposingSignal)
        .options(
            joinedload(RepurposingSignal.drug),
            joinedload(RepurposingSignal.disease),
            joinedload(RepurposingSignal.evidence_items),
        ).all())
for s in sigs:
    dname = s.drug.name if s.drug else "?"
    disn  = s.disease.name if s.disease else "?"
    live_c = sum(1 for e in (s.evidence_items or []) if not e.is_demo_data)
    demo_c = sum(1 for e in (s.evidence_items or []) if e.is_demo_data)
    print(f"  [{s.id:2d}] {dname:<16} -> {disn:<36} score={s.evidence_score:5.1f} {s.confidence_level:<6} src={s.data_source:<5} live={live_c:3d} demo={demo_c:3d}")

# ── 4. Per-signal source breakdown (live evidence only) ──────────────────────
print()
print("Per-signal live evidence source breakdown:")
for s in sigs:
    live_items = [e for e in (s.evidence_items or []) if not e.is_demo_data]
    if not live_items:
        continue
    dname = s.drug.name if s.drug else "?"
    disn  = s.disease.name if s.disease else "?"
    src_counts = {}
    for e in live_items:
        k = e.data_source or "unknown"
        src_counts[k] = src_counts.get(k, 0) + 1
    print(f"  Signal [{s.id}] {dname} -> {disn}")
    for src, cnt in sorted(src_counts.items()):
        print(f"    {src:<20} {cnt} records")

# ── 5. Drugs and diseases ────────────────────────────────────────────────────
print()
print(f"=== DRUGS  : {db.query(Drug).count()} total ===")
for d in db.query(Drug).all():
    print(f"  [{d.id}] {d.name}")

print()
print(f"=== DISEASES: {db.query(Disease).count()} total ===")
for d in db.query(Disease).all():
    print(f"  [{d.id}] {d.name}")

# ── 6. Deduplication check ───────────────────────────────────────────────────
print()
print("=== DEDUPLICATION CHECK (live evidence) ===")
live_all = db.query(Evidence).filter(Evidence.is_demo_data == False).all()
doi_map  = {}
pmid_map = {}
for e in live_all:
    if e.doi:
        doi_map.setdefault(e.doi.strip().lower(), []).append(e.data_source)
    if e.pmid:
        pmid_map.setdefault(e.pmid.strip(), []).append(e.data_source)

cross_doi  = {k: v for k, v in doi_map.items()  if len(set(v)) > 1}
cross_pmid = {k: v for k, v in pmid_map.items() if len(set(v)) > 1}
print(f"Cross-source DOI duplicates  : {len(cross_doi)}")
print(f"Cross-source PMID duplicates : {len(cross_pmid)}")
for doi, srcs in list(cross_doi.items())[:5]:
    print(f"  DOI {doi[:50]} in sources: {set(srcs)}")
for pmid, srcs in list(cross_pmid.items())[:5]:
    print(f"  PMID {pmid} in sources: {set(srcs)}")

# ── 7. Demo data score impact check ─────────────────────────────────────────
print()
print("=== DEMO DATA SCORE IMPACT ===")
print("Checking calculate_evidence_score demo exclusion logic...")
from app.services.ai_service import ai_service
for s in sigs[:3]:
    ev_dicts = [
        {
            "evidence_type":    e.evidence_type,
            "publication_date": e.publication_date or "",
            "data_source":      e.data_source or "unknown",
            "doi":              e.doi,
            "pmid":             e.pmid,
            "is_demo_data":     e.is_demo_data,
        }
        for e in (s.evidence_items or [])
    ]
    result = ai_service.calculate_evidence_score(
        drug_name=s.drug.name if s.drug else "",
        disease_name=s.disease.name if s.disease else "",
        evidence_items=ev_dicts,
        mechanism_overlap=0.3,
        drug_targets=[],
        disease_pathways=[],
    )
    dedup_total = result.get("_dedup_total", 0)
    raw_total   = result.get("_raw_total", 0)
    cross_dedup = result.get("_cross_source_dedup", 0)
    total_score = result["total"]["score"]
    dname = s.drug.name if s.drug else "?"
    disn  = s.disease.name if s.disease else "?"
    print(f"  Signal [{s.id}] {dname} -> {disn}")
    print(f"    raw_ev={raw_total} dedup_ev={dedup_total} cross_dedup_removed={cross_dedup} computed_score={total_score}")
    print(f"    stored_score={s.evidence_score:.1f}")

db.close()
print()
print("=== AUDIT COMPLETE ===")
