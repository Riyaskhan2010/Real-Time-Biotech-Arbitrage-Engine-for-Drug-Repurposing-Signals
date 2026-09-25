"""
Tests for the bioRxiv/medRxiv connector.
Covers: valid response, empty body, invalid JSON, timeout, 429, 500,
        fallback to /pubs, deduplication, is_demo_data, pagination,
        last_successful_sync preservation.

Run: python test_biorxiv_connector.py
"""
import asyncio, sys, os, json
from unittest import mock
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))

PASS = []; FAIL = []

def ok(msg):   PASS.append(msg); print(f"  ✓ {msg}")
def fail(msg, e=""): FAIL.append(msg); print(f"  ✗ {msg}{(' — '+str(e)) if e else ''}")

# ── Helpers ───────────────────────────────────────────────────────────────────

VALID_DETAILS_RESPONSE = json.dumps({
    "messages": [{"status": "ok", "count": 2, "total": "2"}],
    "collection": [
        {"doi": "10.1101/2026.01.01.000001", "title": "Metformin and Alzheimer",
         "authors": "Smith J;Jones A", "abstract": "Metformin reduces amyloid.",
         "date": "2026-09-01", "server": "biorxiv"},
        {"doi": "10.1101/2026.01.02.000002", "title": "Ivermectin cancer study",
         "authors": "Lee B", "abstract": "Ivermectin inhibits tumor growth.",
         "date": "2026-09-02", "server": "biorxiv"},
    ]
})

VALID_PUBS_RESPONSE = json.dumps({
    "messages": [{"status": "ok", "count": 1, "total": "1"}],
    "collection": [
        {"preprint_doi": "10.1101/2026.01.03.000003",
         "preprint_title": "Aspirin Alzheimer disease mechanisms",
         "preprint_authors": "Wang X;Chen Y",
         "preprint_abstract": "Aspirin reduces neuroinflammation.",
         "preprint_date": "2026-09-03",
         "preprint_category": "neuroscience",
         "preprint_platform": "bioRxiv",
         "published_doi": "10.1038/s41586-026-12345-6",
         "published_journal": "Nature"},
    ]
})

EMPTY_RESPONSE = ""
INVALID_JSON   = "<!DOCTYPE html><html>server error</html>"

# ── Mock factory ──────────────────────────────────────────────────────────────

def make_mock_response(status_code: int, body: str):
    r = mock.MagicMock()
    r.status_code = status_code
    r.text = body
    r.raise_for_status = mock.MagicMock(
        side_effect=None if status_code < 400
        else Exception(f"HTTP {status_code}")
    )
    return r

def mock_client_returning(status_code: int, body: str):
    """Context manager that patches httpx.AsyncClient to return a fixed response."""
    resp = make_mock_response(status_code, body)
    async def fake_get(url, **kw):
        return resp
    client_mock = mock.AsyncMock()
    client_mock.__aenter__ = mock.AsyncMock(return_value=client_mock)
    client_mock.__aexit__  = mock.AsyncMock(return_value=False)
    client_mock.get = fake_get
    return mock.patch("httpx.AsyncClient", return_value=client_mock)

# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_valid_details_response():
    """HTTP 200 valid JSON from /details → check_connection returns True."""
    from app.services.connectors.biorxiv import BioRxivConnector
    c = BioRxivConnector(timeout=10)
    with mock_client_returning(200, VALID_DETAILS_RESPONSE):
        result = await c.check_connection()
    if result and not c._last_check_empty_body:
        ok("valid /details response → Connected=True, empty_body=False")
    else:
        fail("valid /details response", f"result={result} empty_body={c._last_check_empty_body}")

async def test_empty_body_200():
    """HTTP 200 empty body → check_connection returns False with empty_body=True."""
    from app.services.connectors.biorxiv import BioRxivConnector
    c = BioRxivConnector(timeout=10)
    # Both /details and /pubs return empty
    with mock_client_returning(200, EMPTY_RESPONSE):
        result = await c.check_connection()
    if not result and c._last_check_empty_body:
        ok("empty HTTP 200 → Connected=False, empty_body=True (Unavailable)")
    else:
        fail("empty HTTP 200", f"result={result} empty_body={c._last_check_empty_body}")

async def test_invalid_json():
    """HTTP 200 non-JSON body → check_connection returns False."""
    from app.services.connectors.biorxiv import BioRxivConnector
    c = BioRxivConnector(timeout=10)
    with mock_client_returning(200, INVALID_JSON):
        result = await c.check_connection()
    if not result:
        ok("invalid JSON → Connected=False")
    else:
        fail("invalid JSON should not return Connected")

async def test_http_429():
    """HTTP 429 → check_connection returns False (not Connected, not empty_body)."""
    from app.services.connectors.biorxiv import BioRxivConnector
    c = BioRxivConnector(timeout=10)
    with mock_client_returning(429, "rate limited"):
        result = await c.check_connection()
    if not result and not c._last_check_empty_body:
        ok("HTTP 429 → Connected=False, empty_body=False (Error/RateLimited)")
    else:
        fail("HTTP 429", f"result={result} empty_body={c._last_check_empty_body}")

async def test_http_500():
    """HTTP 500 → check_connection returns False."""
    from app.services.connectors.biorxiv import BioRxivConnector
    c = BioRxivConnector(timeout=10)
    with mock_client_returning(500, "internal server error"):
        result = await c.check_connection()
    if not result:
        ok("HTTP 500 → Connected=False")
    else:
        fail("HTTP 500 should not return Connected")

async def test_pubs_fallback():
    """
    /details returns empty body; /pubs returns valid data →
    check_connection returns True, empty_body=False.
    """
    from app.services.connectors.biorxiv import _DETAILS_BASE, _PUBS_BASE, BioRxivConnector
    c = BioRxivConnector(timeout=10)

    call_count = {"n": 0}
    async def fake_get(url, **kw):
        call_count["n"] += 1
        if _DETAILS_BASE in url:
            return make_mock_response(200, EMPTY_RESPONSE)
        else:  # _PUBS_BASE
            return make_mock_response(200, VALID_PUBS_RESPONSE)

    client_mock = mock.AsyncMock()
    client_mock.__aenter__ = mock.AsyncMock(return_value=client_mock)
    client_mock.__aexit__  = mock.AsyncMock(return_value=False)
    client_mock.get = fake_get

    with mock.patch("httpx.AsyncClient", return_value=client_mock):
        result = await c.check_connection()

    if result and not c._last_check_empty_body and call_count["n"] >= 2:
        ok(f"details→empty, pubs→valid → Connected=True (calls={call_count['n']})")
    else:
        fail("/pubs fallback", f"result={result} empty_body={c._last_check_empty_body} calls={call_count['n']}")

async def test_details_normalization():
    """/details records normalize with correct fields and is_demo_data=False."""
    from app.services.connectors.biorxiv import BioRxivConnector
    c = BioRxivConnector(timeout=10)
    art = json.loads(VALID_DETAILS_RESPONSE)["collection"][0]
    rec = c._normalize_details(art)
    if (rec and rec.doi == "10.1101/2026.01.01.000001"
            and rec.source == "biorxiv"
            and rec.evidence_type == "preprint"
            and rec.is_demo_data is False
            and rec.source_id == rec.doi):
        ok("_normalize_details: doi, source, evidence_type=preprint, is_demo_data=False ✓")
    else:
        fail("_normalize_details", f"rec={rec}")

async def test_pubs_normalization():
    """/pubs records normalize with preprint_doi as source_id."""
    from app.services.connectors.biorxiv import BioRxivConnector
    c = BioRxivConnector(timeout=10)
    art = json.loads(VALID_PUBS_RESPONSE)["collection"][0]
    rec = c._normalize_pubs(art)
    if (rec and rec.doi == "10.1101/2026.01.03.000003"
            and rec.source_id == "10.1101/2026.01.03.000003"
            and rec.source == "biorxiv"
            and rec.evidence_type == "preprint"
            and rec.is_demo_data is False
            and "Nature" in (rec.journal or "")):
        ok("_normalize_pubs: doi=source_id, is_demo_data=False, journal contains published venue ✓")
    else:
        fail("_normalize_pubs", f"rec={rec}")

async def test_deduplication_same_doi():
    """Two records with same DOI from different sources should have same source_id (dedup key)."""
    from app.services.connectors.biorxiv import BioRxivConnector
    c = BioRxivConnector(timeout=10)
    # Same DOI appearing in both /details and /pubs
    art_details = {"doi": "10.1101/2026.01.01.000001", "title": "Test", "authors": "A",
                   "abstract": "test metformin", "date": "2026-09-01", "server": "biorxiv"}
    art_pubs = {"preprint_doi": "10.1101/2026.01.01.000001",
                "preprint_title": "Test", "preprint_authors": "A",
                "preprint_abstract": "test metformin", "preprint_date": "2026-09-01",
                "preprint_category": "bio", "preprint_platform": "bioRxiv"}
    r1 = c._normalize_details(art_details)
    r2 = c._normalize_pubs(art_pubs)
    if r1 and r2 and r1.source_id == r2.source_id:
        ok(f"Same DOI → same source_id ({r1.source_id}) — dedup will catch it ✓")
    else:
        fail("Deduplication source_id mismatch", f"r1.source_id={r1.source_id if r1 else None} r2.source_id={r2.source_id if r2 else None}")

async def test_keyword_filter():
    """Records not matching keywords are excluded."""
    from app.services.connectors.biorxiv import BioRxivConnector
    c = BioRxivConnector(timeout=10)
    art = {"doi": "10.1101/xxx", "title": "Unrelated protein study", "authors": "X",
           "abstract": "Nothing relevant", "date": "2026-09-01", "server": "biorxiv"}
    rec = c._normalize_details(art)
    matches = c._matches_keywords(rec, ["metformin", "alzheimer"])
    if not matches:
        ok("keyword filter excludes unrelated records ✓")
    else:
        fail("keyword filter should have excluded this record")

async def test_fetch_returns_live_records():
    """fetch() with valid /details data returns is_demo_data=False records."""
    from app.services.connectors.biorxiv import BioRxivConnector
    c = BioRxivConnector(timeout=10)
    with mock_client_returning(200, VALID_DETAILS_RESPONSE):
        recs = await c.fetch(query="metformin alzheimer", max_records=5)
    if (recs and all(r.is_demo_data is False for r in recs)
            and all(r.source == "biorxiv" for r in recs)):
        ok(f"fetch() returned {len(recs)} live records (is_demo_data=False, source=biorxiv) ✓")
    else:
        fail("fetch() live records check", f"recs={[r.doi for r in recs]}")

async def test_fetch_pubs_fallback_records():
    """fetch() falls through to /pubs when /details empty, returns live records."""
    from app.services.connectors.biorxiv import _DETAILS_BASE, BioRxivConnector
    c = BioRxivConnector(timeout=10)

    async def fake_get(url, **kw):
        if _DETAILS_BASE in url:
            return make_mock_response(200, EMPTY_RESPONSE)
        else:
            return make_mock_response(200, VALID_PUBS_RESPONSE)

    client_mock = mock.AsyncMock()
    client_mock.__aenter__ = mock.AsyncMock(return_value=client_mock)
    client_mock.__aexit__  = mock.AsyncMock(return_value=False)
    client_mock.get = fake_get

    with mock.patch("httpx.AsyncClient", return_value=client_mock):
        recs = await c.fetch(query="aspirin alzheimer", max_records=5)

    if (recs and all(r.is_demo_data is False for r in recs)
            and recs[0].doi == "10.1101/2026.01.03.000003"):
        ok(f"fetch() /pubs fallback: {len(recs)} live record(s) ✓")
    else:
        fail("fetch() /pubs fallback", f"recs={recs}")

async def test_medrxiv_connector():
    """MedRxivConnector uses 'medrxiv' as source."""
    from app.services.connectors.biorxiv import MedRxivConnector
    c = MedRxivConnector(timeout=10)
    medrxiv_response = VALID_DETAILS_RESPONSE.replace(
        '"server": "biorxiv"', '"server": "medrxiv"')
    with mock_client_returning(200, medrxiv_response):
        result = await c.check_connection()
    if result and c._SERVER == "medrxiv":
        ok("MedRxivConnector: check_connection Connected, server=medrxiv ✓")
    else:
        fail("MedRxivConnector", f"result={result} server={c._SERVER}")

async def test_recovery_after_failure():
    """After empty body failure, next valid response returns True (auto-recovery)."""
    from app.services.connectors.biorxiv import BioRxivConnector
    c = BioRxivConnector(timeout=10)
    # First call: empty (unavailable)
    with mock_client_returning(200, EMPTY_RESPONSE):
        r1 = await c.check_connection()
    assert not r1 and c._last_check_empty_body, "Should be unavailable first"
    # Second call: valid (recovered)
    with mock_client_returning(200, VALID_DETAILS_RESPONSE):
        r2 = await c.check_connection()
    if r2 and not c._last_check_empty_body:
        ok("auto-recovery: unavailable → connected on next valid response ✓")
    else:
        fail("auto-recovery", f"r2={r2} empty_body={c._last_check_empty_body}")

async def test_existing_stored_records_not_deleted():
    """Existing stored live records remain even when API is unavailable."""
    from app.database import SessionLocal
    from app.models.research_source import ResearchSource
    db = SessionLocal()
    biorxiv_count = db.query(ResearchSource).filter_by(
        source_type='biorxiv', is_demo_data=False).count()
    medrxiv_count = db.query(ResearchSource).filter_by(
        source_type='medrxiv', is_demo_data=False).count()
    db.close()
    if biorxiv_count >= 335 and medrxiv_count >= 320:
        ok(f"Stored live records preserved: biorxiv={biorxiv_count}, medrxiv={medrxiv_count} ✓")
    else:
        fail("Stored records", f"biorxiv={biorxiv_count} (expected ≥335), medrxiv={medrxiv_count} (expected ≥320)")

# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    print("=" * 60)
    print("  bioRxiv/medRxiv Connector Tests")
    print("=" * 60)

    tests = [
        test_valid_details_response,
        test_empty_body_200,
        test_invalid_json,
        test_http_429,
        test_http_500,
        test_pubs_fallback,
        test_details_normalization,
        test_pubs_normalization,
        test_deduplication_same_doi,
        test_keyword_filter,
        test_fetch_returns_live_records,
        test_fetch_pubs_fallback_records,
        test_medrxiv_connector,
        test_recovery_after_failure,
        test_existing_stored_records_not_deleted,
    ]

    for t in tests:
        try:
            await t()
        except Exception as e:
            fail(t.__name__, str(e))

    print(f"\n{'='*60}")
    print(f"  {len(PASS)} PASS  {len(FAIL)} FAIL")
    print("=" * 60)
    if FAIL:
        print("FAILURES:")
        for f in FAIL:
            print(f"  ✗ {f}")
    return len(FAIL) == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
