import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))
from sqlalchemy import create_engine, func, exists as sq_exists, not_
from sqlalchemy.orm import sessionmaker, joinedload
from app.models.drug import Drug
from app.models.disease import Disease
from app.models.evidence import Evidence
from app.models.research_source import ResearchSource
from app.models.signal import RepurposingSignal

engine = create_engine("sqlite:///./bioarbitrage.db", connect_args={"check_same_thread": False})
db = sessionmaker(bind=engine)()

live_ev_exists = sq_exists().where(
    (Evidence.signal_id == RepurposingSignal.id) &
    (Evidence.is_demo_data == False)
)

print()
print(f"{'Drug':<16} {'Evidence':>10} {'Live Ev':>8} {'Demo Ev':>8} {'Signals':>8}")
print("-"*54)
for drug in db.query(Drug).all():
    sigs = db.query(RepurposingSignal).options(
        joinedload(RepurposingSignal.evidence_items)
    ).filter(RepurposingSignal.drug_id == drug.id).all()
    live_ev  = sum(sum(1 for e in (s.evidence_items or []) if not e.is_demo_data) for s in sigs)
    demo_ev  = sum(sum(1 for e in (s.evidence_items or []) if e.is_demo_data) for s in sigs)
    total_ev = live_ev + demo_ev
    print(f"{drug.name:<16} {total_ev:>10} {live_ev:>8} {demo_ev:>8} {len(sigs):>8}")

print()
print("Evidence by source (live only):")
rows = db.query(Evidence.data_source, func.count(Evidence.id)).filter(
    Evidence.is_demo_data == False).group_by(Evidence.data_source).all()
for src, cnt in sorted(rows, key=lambda x: -x[1]):
    print(f"  {str(src or 'unknown'):<20} {cnt}")

print()
ev_total  = db.query(Evidence).count()
ev_live   = db.query(Evidence).filter(Evidence.is_demo_data == False).count()
ev_demo   = db.query(Evidence).filter(Evidence.is_demo_data == True).count()
sig_total = db.query(RepurposingSignal).count()
sig_live  = db.query(RepurposingSignal).filter(live_ev_exists).count()
sig_demo  = db.query(RepurposingSignal).filter(not_(live_ev_exists)).count()
rs_total  = db.query(ResearchSource).filter(ResearchSource.is_demo_data == False).count()

print(f"Total evidence  : {ev_total}  live={ev_live}  demo={ev_demo}")
print(f"Total signals   : {sig_total}  live={sig_live}  demo-only={sig_demo}")
print(f"ResearchSources : {rs_total} (live)")
db.close()
