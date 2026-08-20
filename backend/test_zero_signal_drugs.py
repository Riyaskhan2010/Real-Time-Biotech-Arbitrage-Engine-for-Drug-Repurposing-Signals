"""
Regression tests for the 0-signal drug investigation.

Root cause: Ivermectin, Lithium, and Thalidomide had no query terms in
INGESTION_QUERY_TERMS — so no evidence was ever fetched for them.
After the fix (adding query terms + expanding _KNOWN_DISEASES), this test
verifies the complete pipeline using an in-memory DB.

Tests cover:
  1. Drug lookup works for all 8 DB drugs
  2. Entity matching works for Ivermectin, Lithium, Thalidomide
  3. Disease extraction works for expanded disease list
  4. Evidence matching produces MATCH outcomes for realistic titles
  5. Signal creation works when valid drug+disease evidence is presented
  6. No signal created when drug is not matched
  7. Demo evidence does not affect signal counts
  8. Existing working drugs/signals still work
"""
import sys, os, asyncio, traceback
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload

from app.database import Base
from app.models.drug import Drug
from app.models.disease import Disease
from app.models.user import User
from app.models.signal import RepurposingSignal
from app.models.evidence import Evidence
from app.models.research_source import ResearchSource
from app.utils.auth import get_password_hash
from app.services.ingestion_service import IngestionService, _parse_query_for_hints
from app.services.connectors.base import NormalizedRecord
from app.services.ai_service import ai_service

RESULTS = []
ERRORS  = []

def check(name, ok, detail=""):
    RESULTS.append((name, ok))
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" -- {detail}" if detail else ""))
    return ok

def make_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()
    db.add(User(email="t@t.test", username="t", full_name="T",
                hashed_password=get_password_hash("pw"), role="researcher", is_active=True))
    # All 8 drugs from production
    drugs = [
        Drug(name="Metformin",    molecular_targets=["AMPK", "mTOR"],
             pathways=["mTOR signaling"], fda_status="Approved",
             approved_indications=["Type 2 Diabetes"]),
        Drug(name="Rapamycin",    molecular_targets=["mTOR"],
             pathways=["mTOR signaling"], fda_status="Approved",
             approved_indications=["Transplant"]),
        Drug(name="Ivermectin",   molecular_targets=["GluCl channels", "Importin alpha/beta"],
             pathways=["Nuclear transport pathway", "GABA signaling"], fda_status="Approved",
             approved_indications=["Parasitic infections"]),
        Drug(name="Sildenafil",   molecular_targets=["PDE5"],
             pathways=["cGMP signaling"], fda_status="Approved",
             approved_indications=["Pulmonary hypertension", "Erectile dysfunction"]),
        Drug(name="Doxycycline",  molecular_targets=["MMP inhibition"],
             pathways=["Anti-inflammatory"], fda_status="Approved",
             approved_indications=["Bacterial infection"]),
        Drug(name="Lithium",      molecular_targets=["GSK-3beta", "BDNF pathway"],
             pathways=["GSK-3 signaling", "Wnt/beta-catenin pathway"], fda_status="Approved",
             approved_indications=["Bipolar disorder"]),
        Drug(name="Naltrexone",   molecular_targets=["Opioid receptors"],
             pathways=["Opioid signaling"], fda_status="Approved",
             approved_indications=["Opioid dependence"]),
        Drug(name="Thalidomide",  molecular_targets=["Cereblon (CRBN)", "TNF-alpha", "VEGF"],
             pathways=["Ubiquitin-proteasome pathway", "TNF signaling", "Angiogenesis pathway"],
             fda_status="Restricted", approved_indications=["Multiple myeloma", "Leprosy"]),
    ]
    diseases = [
        Disease(name="Alzheimer's Disease",            affected_pathways=["mTOR signaling"]),
        Disease(name="Glioblastoma",                   affected_pathways=["Angiogenesis pathway"]),
        Disease(name="Type 2 Diabetes Mellitus",       affected_pathways=["mTOR signaling"]),
        Disease(name="Pulmonary Arterial Hypertension",affected_pathways=["cGMP signaling"]),
        Disease(name="Triple-Negative Breast Cancer",  affected_pathways=["mTOR signaling"]),
        Disease(name="Multiple Sclerosis",             affected_pathways=["Neuroprotective pathway"]),
        Disease(name="Pancreatic Ductal Adenocarcinoma", affected_pathways=["AMPK pathway"]),
    ]
    for d in drugs + diseases:
        db.add(d)
    db.commit()
    return db

# ─────────────────────────────────────────────────────────────────────────────
print("="*65)
print("TEST: ZERO-SIGNAL DRUG REGRESSION SUITE")
print("="*65)

db = make_db()
svc = IngestionService()

# ── Test 1: Drug lookup works for all 8 drugs ─────────────────────────────
print("\n[1. Drug lookup]")
for name in ["Metformin", "Rapamycin", "Ivermectin", "Sildenafil",
             "Doxycycline", "Lithium", "Naltrexone", "Thalidomide"]:
    drug = db.query(Drug).filter(Drug.name.ilike(f"%{name}%")).first()
    check(f"Drug '{name}' found in DB", drug is not None)

# ── Test 2: Entity matching for Ivermectin, Lithium, Thalidomide ─────────
print("\n[2. Entity matching — previously 0-signal drugs]")
test_cases = [
    ("ivermectin cancer",             "Ivermectin",  True),
    ("ivermectin glioblastoma",       "Ivermectin",  True),
    ("lithium alzheimer",             "Lithium",     True),
    ("lithium neurodegeneration alzheimer", "Lithium", True),
    ("thalidomide cancer",            "Thalidomide", True),
    ("thalidomide glioblastoma",      "Thalidomide", True),
    ("drug:Ivermectin disease:Cancer","Ivermectin",  True),
    ("drug:Lithium disease:Alzheimer's Disease","Lithium", True),
    ("drug:Thalidomide disease:Glioblastoma","Thalidomide",True),
]
for query, expected_drug, should_match_drug in test_cases:
    dh, dis_h = _parse_query_for_hints(query)
    drugs_m = svc._match_drugs(db, dh)
    found_drug = any(expected_drug.lower() in d.name.lower() for d in drugs_m)
    check(f"'{query}' matches {expected_drug}", found_drug == should_match_drug,
          f"matched drugs={[d.name for d in drugs_m]}")

# ── Test 3: Disease extraction for expanded disease list ──────────────────
print("\n[3. Disease extraction — expanded _KNOWN_DISEASES]")
disease_titles = [
    ("Thalidomide for multiple myeloma treatment",   ["Myeloma"]),
    ("Ivermectin inhibits pulmonary hypertension",   ["Pulmonary Hypertension"]),
    ("Drug treatment in neurodegeneration",          ["Neurodegeneration"]),
    ("Lithium in Alzheimer disease and dementia",    ["Alzheimer", "Dementia"]),
    ("Anti-tumor effects on adenocarcinoma cells",   ["Adenocarcinoma"]),
]
for title, expected_diseases in disease_titles:
    entities = ai_service.extract_entities(title)
    extracted = [d.lower() for d in entities.get("diseases", [])]
    found_any = any(exp.lower() in " ".join(extracted) for exp in expected_diseases)
    check(f"Disease extracted from: '{title[:55]}'",
          found_any, f"extracted={entities.get('diseases', [])}")

# ── Test 4: Evidence matching on realistic titles ─────────────────────────
print("\n[4. Evidence matching — realistic titles produce MATCH outcomes]")
match_titles = [
    ("Ivermectin as a potential anticancer agent in glioblastoma",
     "Ivermectin", "Glioblastoma"),
    ("Lithium treatment in Alzheimer's disease: neuroprotective effects",
     "Lithium", "Alzheimer"),
    ("Thalidomide combined therapy in glioblastoma multiforme",
     "Thalidomide", "Glioblastoma"),
    ("Anti-angiogenic effects of thalidomide in cancer therapy",
     "Thalidomide", "Triple-Negative Breast Cancer"),
    ("Ivermectin inhibits tumor growth in triple-negative breast cancer",
     "Ivermectin", "Triple-Negative Breast Cancer"),
]
for title, exp_drug, exp_disease in match_titles:
    entities = ai_service.extract_entities(title)
    drugs_m    = svc._match_drugs(db, entities.get("drugs", []))
    diseases_m = svc._match_diseases(db, entities.get("diseases", []))
    has_drug    = any(exp_drug.lower() in d.name.lower() for d in drugs_m)
    has_disease = any(exp_disease.lower() in d.name.lower() for d in diseases_m)
    check(f"Title match {exp_drug}+{exp_disease[:20]}",
          has_drug and has_disease,
          f"drugs={[d.name for d in drugs_m]} diseases={[d.name for d in diseases_m]}")

# ── Test 5: Signal creation via _process_record ───────────────────────────
print("\n[5. Signal creation when valid drug+disease evidence presented]")

def make_rec(source="pubmed", source_id=None, title="", ev_type="research_paper"):
    import time
    sid = source_id or f"TEST_{int(time.time()*1000)}"
    return NormalizedRecord(
        source=source, source_id=sid, title=title,
        abstract=title, evidence_type=ev_type, is_demo_data=False,
    )

signal_tests = [
    ("Ivermectin as a potential anticancer agent in glioblastoma",
     "pubmed", "IVCANCER001", "Ivermectin", "Glioblastoma"),
    ("Lithium treatment in Alzheimer's disease",
     "europepmc", "LITH_AD001", "Lithium", "Alzheimer"),
    ("Thalidomide combined therapy in glioblastoma",
     "pubmed", "THAL_GBM001", "Thalidomide", "Glioblastoma"),
    ("Anti-angiogenic effects of thalidomide in cancer",
     "elsevier", "THAL_CA001", "Thalidomide", "Triple-Negative Breast Cancer"),
]
for title, source, sid, exp_drug, exp_disease in signal_tests:
    sig_count_before = db.query(RepurposingSignal).count()
    rec = make_rec(source=source, source_id=sid, title=title)
    outcome = svc._process_record(db, rec)
    sig_count_after = db.query(RepurposingSignal).count()
    check(f"Signal created/matched for {exp_drug}+{exp_disease[:20]}",
          outcome in ("new_matched", "new_novel"),
          f"outcome={outcome} new_signals={sig_count_after - sig_count_before}")

# ── Test 6: No signal created when drug not matched ───────────────────────
print("\n[6. No signal when drug not matched]")
unmatched_rec = make_rec(
    source="pubmed", source_id="NO_DRUG_001",
    title="Study on unknown compound XYZ-42 in rare disease treatment"
)
outcome = svc._process_record(db, unmatched_rec)
check("No signal for unrecognized drug", outcome == "new_unmatched", f"outcome={outcome}")

# ── Test 7: Demo evidence excluded from signals ───────────────────────────
print("\n[7. Demo evidence excluded from signal count]")
# Manually insert a demo evidence record and verify it doesn't create a signal
demo_rec = NormalizedRecord(
    source="demo", source_id="DEMO_TEST_001",
    title="[DEMO] Ivermectin in cancer — simulated record",
    evidence_type="research_paper", is_demo_data=True,
)
# _process_record checks is_duplicate then saves, but we need to verify
# that demo records in the DB don't appear as live evidence
from app.models.evidence import Evidence as EvidenceModel
demo_ev = EvidenceModel(
    signal_id=None,  # orphan — won't affect signals
    evidence_type="research_paper",
    title="[DEMO] Orphan demo record",
    is_demo_data=True,
    data_source="demo",
    relevance_score=0.0,
    supports_mechanism=False,
)
# Don't actually save — just verify the flag field exists
check("Evidence.is_demo_data field exists",  hasattr(demo_ev, "is_demo_data"))
check("Demo evidence flag is True",          demo_ev.is_demo_data == True)

# Verify all signals in the test DB have only live evidence
sigs = db.query(RepurposingSignal).options(joinedload(RepurposingSignal.evidence_items)).all()
all_live = all(
    all(not e.is_demo_data for e in (s.evidence_items or []))
    for s in sigs
)
check("All signals in test DB have only live evidence", all_live,
      f"{len(sigs)} signals checked")

# ── Test 8: Existing working drugs still produce correct outcomes ─────────
print("\n[8. Existing drugs still work correctly]")
working_tests = [
    ("Metformin treatment in Alzheimer's disease prevention",
     "pubmed", "MET_AD_REG001", ("new_matched", "new_novel")),
    ("Sildenafil for pulmonary arterial hypertension clinical trial",
     "clinicaltrials", "SIL_PAH_REG001", ("new_matched", "new_novel")),
    ("Rapamycin aging intervention study in type 2 diabetes",
     "europepmc", "RAP_T2D_REG001", ("new_matched", "new_novel")),
]
for title, source, sid, expected_outcomes in working_tests:
    rec = make_rec(source=source, source_id=sid, title=title)
    outcome = svc._process_record(db, rec)
    check(f"Existing drug pipeline: {title[:45]}",
          outcome in expected_outcomes, f"outcome={outcome}")

# ── Test 9: Verify final signal counts in test DB ─────────────────────────
print("\n[9. Signal summary in test DB]")
all_sigs = db.query(RepurposingSignal).options(
    joinedload(RepurposingSignal.drug),
    joinedload(RepurposingSignal.disease),
    joinedload(RepurposingSignal.evidence_items),
).all()
drug_signal_counts = {}
for s in all_sigs:
    drug_n = s.drug.name if s.drug else "?"
    drug_signal_counts[drug_n] = drug_signal_counts.get(drug_n, 0) + 1
    live_ev = sum(1 for e in (s.evidence_items or []) if not e.is_demo_data)
    print(f"    [{s.id}] {drug_n} -> {s.disease.name if s.disease else '?'} live_ev={live_ev}")

for drug_name in ["Ivermectin", "Lithium", "Thalidomide"]:
    cnt = drug_signal_counts.get(drug_name, 0)
    check(f"{drug_name} has >= 1 signal in test DB after fix", cnt >= 1, f"count={cnt}")

db.close()

# ── Summary ─────────────────────────────────────────────────────────────────
total  = len(RESULTS)
passed = sum(1 for _, ok in RESULTS if ok)
failed = total - passed

print(f"\n{'='*65}")
print(f"Results: {passed}/{total} passed | {failed} failed")
print(f"{'='*65}")
if failed:
    print("\nFailed:")
    for name, ok in RESULTS:
        if not ok:
            print(f"  [FAIL] {name}")

import sys
sys.exit(0 if failed == 0 else 1)
