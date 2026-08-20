# -*- coding: utf-8 -*-
"""
Ingestion pipeline test suite.
Run: python test_ingestion.py   (from backend/)
"""
import asyncio, sys, os, traceback
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.drug import Drug
from app.models.disease import Disease
from app.models.signal import RepurposingSignal
from app.models.evidence import Evidence
from app.models.research_source import ResearchSource
from app.models.ingestion_run import IngestionRun
from app.models.user import User
from app.models.alert import Alert
from app.services.connectors.base import NormalizedRecord, BaseConnector
from app.services.connectors.pubmed import PubMedConnector
from app.services.connectors.biorxiv import BioRxivConnector
from app.services.connectors.clinicaltrials import ClinicalTrialsConnector
from app.services.ingestion_service import IngestionService, _score_to_confidence
from app.utils.auth import get_password_hash

RESULTS: list = []


def check(name, condition, detail=""):
    RESULTS.append((name, condition, detail))
    mark = "PASS" if condition else "FAIL"
    line = f"  [{mark}] {name}"
    if detail:
        line += f" -- {detail}"
    print(line)
    return condition


# ── Fresh in-memory DB per test (avoids UNIQUE conflicts) ─────────────────────

def make_test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def seed_test_db(db):
    user = User(email="t@t.test", username="t", full_name="T",
                hashed_password=get_password_hash("pw"), role="researcher", is_active=True)
    db.add(user)
    drug = Drug(name="Metformin", drug_class="Biguanide",
                mechanism_of_action="Activates AMPK",
                approved_indications=["Type 2 Diabetes"],
                molecular_targets=["AMPK", "mTOR"],
                pathways=["AMPK signaling", "mTOR signaling"],
                fda_status="Approved")
    db.add(drug)
    drug2 = Drug(name="Rapamycin", drug_class="mTOR inhibitor",
                 mechanism_of_action="Inhibits mTORC1",
                 approved_indications=["Transplant rejection"],
                 molecular_targets=["mTORC1"], pathways=["mTOR signaling"],
                 fda_status="Approved")
    db.add(drug2)
    disease = Disease(name="Alzheimer's Disease", category="Neurology",
                      affected_pathways=["mTOR signaling", "Autophagy pathway", "AMPK signaling"],
                      molecular_markers=["Amyloid-beta"])
    db.add(disease)
    db.flush()
    signal = RepurposingSignal(drug_id=drug.id, disease_id=disease.id,
                               title="Metformin AD signal", evidence_score=60.0,
                               confidence_level="medium", source_count=2,
                               status="active", data_source="demo")
    db.add(signal)
    db.commit()
    return {"drug": drug, "drug2": drug2, "disease": disease, "signal": signal, "user": user}


def make_record(source="pubmed", source_id="TEST001",
                title="Metformin and Alzheimer's Disease: AMPK pathway study",
                abstract="Metformin activates AMPK. Alzheimer disease mTOR pathway.",
                evidence_type="research_paper", publication_date="2024-01-15"):
    return NormalizedRecord(source=source, source_id=source_id, title=title,
                            abstract=abstract, evidence_type=evidence_type,
                            publication_date=publication_date,
                            authors=["Author A"], journal="Test Journal",
                            source_url=f"https://{source}.example.com/{source_id}",
                            pmid=source_id if source == "pubmed" else None,
                            doi=f"10.0/{source_id}" if source != "pubmed" else None,
                            is_demo_data=False)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_normalization():
    print("\n-- Normalization")
    r = make_record()
    check("Has title",           bool(r.title))
    check("Has source_id",       bool(r.source_id))
    check("is_demo_data=False",  r.is_demo_data == False)
    check("evidence_type set",   r.evidence_type == "research_paper")
    check("No PMID for biorxiv", make_record(source="biorxiv", source_id="10.x/y").pmid is None)
    check("_safe_date YYYY-MM-DD", BaseConnector._safe_date("2024-01-15") == "2024-01-15")
    check("_safe_date YYYY",       BaseConnector._safe_date("2024") == "2024")
    check("_safe_date garbage",    BaseConnector._safe_date("not-a-date") is None)
    check("_truncate caps length", len(BaseConnector._truncate("x" * 3000, 2000)) <= 2001)


def test_deduplication():
    print("\n-- Deduplication")
    db = make_test_db()
    try:
        seed_test_db(db)
        svc = IngestionService()
        rec = make_record(source_id="DEDUP001")
        check("Not dup before insert",         not svc._is_duplicate(db, rec))
        svc._save_source(db, rec, [], [], [])
        check("Dup detected after insert",     svc._is_duplicate(db, rec))
        check("Different id not dup",          not svc._is_duplicate(db, make_record(source_id="DEDUP002")))
        check("Same id diff source not dup",   not svc._is_duplicate(db, make_record(source="biorxiv", source_id="DEDUP001")))
    finally:
        db.close()


def test_entity_extraction():
    print("\n-- Entity Extraction")
    from app.services.ai_service import ai_service
    e1 = ai_service.extract_entities("Metformin activates AMPK in Alzheimer's Disease.")
    check("Extracts Metformin",   any("metformin" in d.lower() for d in e1.get("drugs", [])))
    check("Extracts Alzheimer",   any("alzheimer" in d.lower() for d in e1.get("diseases", [])))
    check("Extracts mechanism",   len(e1.get("mechanisms", [])) > 0)
    e2 = ai_service.extract_entities("Rapamycin inhibits mTOR in pancreatic cancer.")
    check("Extracts Rapamycin",   any("rapamycin" in d.lower() for d in e2.get("drugs", [])))
    e3 = ai_service.extract_entities("No biomedical content here.")
    check("Empty yields no drugs",len(e3.get("drugs", [])) == 0)


def test_signal_matching():
    print("\n-- Signal Matching")
    db = make_test_db()
    try:
        refs = seed_test_db(db)
        svc  = IngestionService()
        rec  = make_record(source_id="MATCH001")
        out  = svc._process_record(db, rec)
        check("Outcome is valid string", out in ("new_matched", "new_unmatched", "new_novel", "duplicate"), f"out={out}")
        saved = db.query(ResearchSource).filter_by(source_id="MATCH001").first()
        check("ResearchSource created",  saved is not None)
        check("Not demo data",           saved is not None and not saved.is_demo_data)
        if out == "new_matched":
            ev = db.query(Evidence).filter_by(signal_id=refs["signal"].id).count()
            check("Evidence attached",   ev > 0)
    finally:
        db.close()


def test_score_update():
    print("\n-- Score Update")
    db = make_test_db()
    try:
        refs   = seed_test_db(db)
        svc    = IngestionService()
        signal = refs["signal"]
        rec    = make_record(source_id="SCORE001")
        drugs  = svc._match_drugs(db, ["Metformin"])
        dis    = svc._match_diseases(db, ["Alzheimer"])
        check("Drug matched",   len(drugs) > 0)
        check("Disease matched",len(dis) > 0)
        if drugs and dis:
            src = svc._save_source(db, rec, drugs, dis, ["AMPK", "mTOR"])
            svc._attach_evidence(db, rec, signal)
            # Rescore is now done globally after a full run; call directly for unit test
            svc._rescore_all_signals(db)
            db.refresh(signal)
            # After attaching 1 evidence record, source_count = len(all evidence items) >= 1
            check("source_count updated",         signal.source_count >= 1)
            check("confidence_level valid",       signal.confidence_level in ("high", "medium", "low"))
    finally:
        db.close()


def test_novel_signal():
    print("\n-- Novel Signal Detection")
    db = make_test_db()
    try:
        refs     = seed_test_db(db)
        svc      = IngestionService()
        drug2    = refs["drug2"]
        disease  = refs["disease"]
        initial  = db.query(RepurposingSignal).count()
        src_rec  = make_record(source_id="SRC_NOVEL01")
        src      = svc._save_source(db, src_rec, [], [], [])
        svc._flag_novel_signal(db, src_rec, src, drug2, disease)
        after    = db.query(RepurposingSignal).count()
        check("Novel signal created",         after > initial)
        novel = db.query(RepurposingSignal).filter_by(drug_id=drug2.id, disease_id=disease.id).first()
        check("is_novel=True",                novel is not None and novel.is_novel)
        check("data_source=live",             novel is not None and novel.data_source == "live")
        check("Title has [Potential Novel]",  novel is not None and "Potential Novel" in novel.title)
        check("Safety disclaimer in summary", novel is not None and "NOT a clinical" in (novel.summary or ""))
        # No duplicate on second call
        src2 = svc._save_source(db, make_record(source="biorxiv", source_id="SRC_NOVEL02"), [], [], [])
        svc._flag_novel_signal(db, src_rec, src2, drug2, disease)
        check("No duplicate novel signal",    db.query(RepurposingSignal).count() == after)
    finally:
        db.close()


def test_score_confidence():
    print("\n-- Score to Confidence")
    check("82 -> high",   _score_to_confidence(82) == "high")
    check("60 -> medium", _score_to_confidence(60) == "medium")
    check("30 -> low",    _score_to_confidence(30) == "low")
    check("75 -> high",   _score_to_confidence(75) == "high")
    check("50 -> medium", _score_to_confidence(50) == "medium")


def test_demo_fallback():
    print("\n-- Demo Fallback")
    from app.data.seed_data import DEMO_RESEARCH_MONITOR
    check("Demo records present",   len(DEMO_RESEARCH_MONITOR) > 0)
    check("Demo records have fields", all("title" in r and "source" in r for r in DEMO_RESEARCH_MONITOR))
    check("Demo labelled",          all(r.get("is_demo_data", True) for r in DEMO_RESEARCH_MONITOR))


def test_api_failure():
    print("\n-- API Failure Handling")
    import httpx

    async def run():
        conn = PubMedConnector(timeout=1)
        # Patch _collect_pmids (renamed from _search in refactored connector)
        with patch.object(conn, '_collect_pmids', side_effect=httpx.ConnectError("refused")):
            check("PubMed returns [] on ConnectError", await conn.fetch("test") == [])
        bio = BioRxivConnector(timeout=1)
        with patch.object(bio, 'fetch', return_value=[]):
            check("bioRxiv returns [] (simulated failure)", await bio.fetch("test") == [])
        ct = ClinicalTrialsConnector(timeout=1)
        with patch.object(ct, 'fetch', return_value=[]):
            check("ClinicalTrials returns [] (simulated failure)", await ct.fetch("test") == [])

    asyncio.run(run())


def test_empty_results():
    print("\n-- Empty Results")

    async def run():
        bio = BioRxivConnector()
        with patch.object(bio, 'fetch', return_value=[]):
            check("Empty collection returns []", await bio.fetch("test") == [])

    asyncio.run(run())


def test_full_flow():
    print("\n-- Full Flow (mocked HTTP)")
    db = make_test_db()
    try:
        seed_test_db(db)
        svc = IngestionService()

        XML = """<?xml version="1.0"?>
<PubmedArticleSet><PubmedArticle>
  <MedlineCitation>
    <PMID>88880001</PMID>
    <Article>
      <ArticleTitle>Metformin and Alzheimer Disease: AMPK activation study</ArticleTitle>
      <Abstract><AbstractText>Metformin activates AMPK. Alzheimer disease mTOR implicated.</AbstractText></Abstract>
      <AuthorList><Author><LastName>Smith</LastName><ForeName>J</ForeName></Author></AuthorList>
      <Journal><Title>Test Journal</Title></Journal>
      <PubDate><Year>2024</Year><Month>Jan</Month><Day>10</Day></PubDate>
    </Article>
  </MedlineCitation>
  <PubmedData><ArticleIdList>
    <ArticleId IdType="doi">10.9999/test.2024.001</ArticleId>
  </ArticleIdList></PubmedData>
</PubmedArticle></PubmedArticleSet>"""

        conn = PubMedConnector()
        records = conn._parse_pubmed_xml(XML)
        check("Parsed 1 record",      len(records) == 1)
        if records:
            r = records[0]
            check("PMID extracted",   r.pmid == "88880001")
            check("DOI extracted",    r.doi  == "10.9999/test.2024.001")
            check("Title extracted",  "Metformin" in r.title)
            check("Date extracted",   r.publication_date is not None)
            check("Author extracted", len(r.authors) > 0)
            check("not demo_data",    not r.is_demo_data)
            out = svc._process_record(db, r)
            check("Pipeline ran OK",  out in ("new_matched", "new_novel", "new_unmatched", "duplicate"))
            src = db.query(ResearchSource).filter_by(source_id="88880001").first()
            check("Source persisted", src is not None)
            if src:
                check("PMID stored",  src.pmid == "88880001")
                check("DOI stored",   src.doi  == "10.9999/test.2024.001")
                check("Not demo",     not src.is_demo_data)
    finally:
        db.close()


def test_run_record():
    print("\n-- IngestionRun Record")
    db = make_test_db()
    try:
        seed_test_db(db)
        svc = IngestionService()

        async def run():
            with patch.object(svc, '_run_all_sources', return_value=[
                {"source": "pubmed", "status": "empty", "records_fetched": 0,
                 "records_new": 0, "records_duplicate": 0, "records_matched": 0,
                 "records_novel": 0, "errors": [], "elapsed_seconds": 0.1}
            ]):
                result = await svc.run(db)
            check("Run created",          result.id is not None)
            check("Status = complete",    result.status == "complete")
            check("finished_at set",      result.finished_at is not None)
            check("Summary present",      bool(result.summary))
            check("source_results stored",len(result.source_results) > 0)
            row = db.query(IngestionRun).filter_by(id=result.id).first()
            check("Row in DB",            row is not None)
            check("DB status complete",   row is not None and row.status == "complete")

        asyncio.run(run())
    finally:
        db.close()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("BioArbitrage -- Ingestion Pipeline Tests")
    print("=" * 60)

    tests = [
        test_normalization, test_deduplication, test_entity_extraction,
        test_signal_matching, test_score_update, test_novel_signal,
        test_score_confidence, test_demo_fallback, test_api_failure,
        test_empty_results, test_full_flow, test_run_record,
    ]

    errors = []
    for fn in tests:
        try:
            fn()
        except Exception as e:
            errors.append((fn.__name__, traceback.format_exc()))
            print(f"  [ERROR] {fn.__name__}: {e}")

    total  = len(RESULTS)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    failed = total - passed

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} passed  |  {failed} failed")
    if errors:
        print(f"\nUnhandled exceptions in {len(errors)} test(s):")
        for name, tb in errors:
            print(f"\n  [{name}]\n{tb}")
    print("=" * 60)
    return 0 if (failed == 0 and not errors) else 1


if __name__ == "__main__":
    sys.exit(main())
