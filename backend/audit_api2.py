"""Read-only extra API audit — ingestion endpoints + rich signal breakdowns."""
import sys, os, httpx, json
sys.path.insert(0, os.path.dirname(__file__))

BASE = "http://localhost:8000"

r = httpx.post(BASE + "/api/auth/token",
               data={"username": "demo_researcher", "password": "demo1234"}, timeout=10)
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

def get(path, params=None):
    r = httpx.get(BASE + path, headers=h, params=params, timeout=15)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text

def section(t):
    print(f"\n{'='*60}\n  {t}\n{'='*60}")

# ── Ingestion endpoints probe ─────────────────────────────────────────────────
section("INGESTION ENDPOINT DISCOVERY")
for path in ["/api/ingestion/runs", "/api/ingestion/history",
             "/api/ingestion/latest", "/api/ingestion/status"]:
    st, d = get(path)
    print(f"  {path:<35} -> HTTP {st}")
    if st == 200 and isinstance(d, (dict, list)):
        if isinstance(d, list):
            print(f"    items={len(d)}")
            for item in d[:2]:
                if isinstance(item, dict):
                    print(f"    run_id={item.get('id')} status={item.get('status')} "
                          f"new={item.get('total_new')} sigs_updated={item.get('signals_updated')}")
                    print(f"    summary: {str(item.get('summary',''))[:100]}")
        elif isinstance(d, dict):
            print(f"    {json.dumps(d, default=str)[:200]}")

# ── Signal 11: Sildenafil -> Pulmonary Arterial Hypertension (richest) ────────
section("SIGNAL 11: Sildenafil -> PAH  (source-breakdown)")
st, d = get("/api/signals/11/source-breakdown")
print(f"  HTTP {st}")
if isinstance(d, dict):
    print(f"  total_evidence_records   = {d.get('total_evidence_records')}")
    print(f"  unique_live_records      = {d.get('unique_live_records')}")
    print(f"  unique_demo_records      = {d.get('unique_demo_records')}")
    print(f"  independent_source_count = {d.get('independent_source_count')}")
    print(f"  has_live_evidence        = {d.get('has_live_evidence')}")
    print(f"  cross_source_duplicates  = {d.get('cross_source_duplicates')}")
    print(f"  duplicates_removed       = {d.get('duplicates_removed')}")
    print()
    print("  Per-source breakdown:")
    for src, info in sorted(d.get("source_breakdown", {}).items()):
        print(f"    {src:<20} count={info['count']} live={info['live']} demo={info['demo']}")
    print()
    print("  Score factors (from real evidence):")
    sf = d.get("score_breakdown_from_evidence", {})
    for k, v in sf.items():
        if isinstance(v, dict) and "score" in v:
            print(f"    {v.get('label', k):<25} {v['score']}/{v['max']}")
    print()
    print(f"  score_explanation: {d.get('score_explanation','')[:160]}")

# ── Signal 4: Metformin -> TNBC ───────────────────────────────────────────────
section("SIGNAL 4: Metformin -> TNBC  (source-breakdown)")
st, d = get("/api/signals/4/source-breakdown")
print(f"  HTTP {st}")
if isinstance(d, dict):
    print(f"  total_evidence_records   = {d.get('total_evidence_records')}")
    print(f"  unique_live_records      = {d.get('unique_live_records')}")
    print(f"  unique_demo_records      = {d.get('unique_demo_records')}")
    print(f"  has_live_evidence        = {d.get('has_live_evidence')}")
    print()
    for src, info in sorted(d.get("source_breakdown", {}).items()):
        print(f"  {src:<20} count={info['count']} live={info['live']} demo={info['demo']}")
    sf = d.get("score_breakdown_from_evidence", {})
    print()
    for k, v in sf.items():
        if isinstance(v, dict) and "score" in v:
            print(f"  {v.get('label', k):<25} {v['score']}/{v['max']}")

# ── Signal 1 evidence detail: traceable records ───────────────────────────────
section("SIGNAL 1 EVIDENCE RECORDS (live, first 8)")
st, d = get("/api/evidence", params={"signal_id": 1, "is_demo": "false", "limit": 8})
print(f"  HTTP {st}  count={len(d) if isinstance(d, list) else '?'}")
if isinstance(d, list):
    for e in d:
        print(f"  id={e['id']:3d} src={str(e.get('data_source','?')):<15} "
              f"type={str(e.get('evidence_type','?')):<20} "
              f"doi={e.get('doi')} pmid={e.get('pmid')} nct={e.get('nct_id')}")
        print(f"    title={str(e.get('title',''))[:75]}")
        print(f"    authors={e.get('authors',[])} date={e.get('publication_date')} url={e.get('source_url','')[:60]}")

# ── Signal 11 evidence detail: traceable records ──────────────────────────────
section("SIGNAL 11 EVIDENCE RECORDS (live, first 8)")
st, d = get("/api/evidence", params={"signal_id": 11, "is_demo": "false", "limit": 8})
print(f"  HTTP {st}  count={len(d) if isinstance(d, list) else '?'}")
if isinstance(d, list):
    for e in d:
        print(f"  id={e['id']:3d} src={str(e.get('data_source','?')):<15} "
              f"type={str(e.get('evidence_type','?')):<20} "
              f"doi={e.get('doi')} pmid={e.get('pmid')} nct={e.get('nct_id')}")
        print(f"    title={str(e.get('title',''))[:75]}")

# ── Evidence from UniProt in DB? ──────────────────────────────────────────────
section("UNIPROT EVIDENCE IN DB")
st, d = get("/api/evidence", params={"data_source": "uniprot", "limit": 5})
print(f"  HTTP {st}  count={len(d) if isinstance(d, list) else '?'}")
if isinstance(d, list) and len(d) == 0:
    print("  NO UniProt evidence records currently in evidence table.")
    print("  (UniProt records ARE stored in ResearchSource table but need signal match)")
elif isinstance(d, list):
    for e in d:
        print(f"  id={e['id']} src={e.get('data_source')} type={e.get('evidence_type')} title={str(e.get('title',''))[:60]}")

# ── Europe PMC evidence in DB? ────────────────────────────────────────────────
section("EUROPE PMC EVIDENCE IN DB")
st, d = get("/api/evidence", params={"data_source": "europepmc", "limit": 5})
print(f"  HTTP {st}  count={len(d) if isinstance(d, list) else '?'}")
if isinstance(d, list) and len(d) == 0:
    print("  NO EuropePMC evidence in evidence table.")
    print("  (EBI server has been returning HTTP 503 — records could not be ingested)")
elif isinstance(d, list):
    for e in d:
        print(f"  id={e['id']} src={e.get('data_source')} title={str(e.get('title',''))[:60]}")

# ── ResearchSource table counts by source ────────────────────────────────────
section("RESEARCH SOURCES IN DB (via /api/research-monitor)")
st, d = get("/api/research-monitor")
print(f"  HTTP {st}")
if isinstance(d, dict):
    print(f"  total={d.get('total_records')} live={d.get('live_records')} demo={d.get('demo_records')}")
    # Show source breakdown
    recs = d.get("recent_records", [])
    src_counts = {}
    for r in recs:
        k = r.get("source_type", r.get("source", "unknown"))
        src_counts[k] = src_counts.get(k, 0) + 1
    print("  Source type counts in monitor (recent 20 live + 5 demo):")
    for k, v in sorted(src_counts.items()):
        print(f"    {k:<20} {v}")

# ── Dashboard stats ───────────────────────────────────────────────────────────
section("DASHBOARD STATS DETAIL")
st, d = get("/api/dashboard")
print(f"  HTTP {st}")
if isinstance(d, dict):
    stats = d.get("stats", {})
    for k, v in stats.items():
        print(f"  {k:<32} {v}")
    print()
    print(f"  recent_signals count  = {len(d.get('recent_signals', []))}")
    print(f"  high_conf_signals cnt = {len(d.get('high_confidence_signals', []))}")
    # Check signal trend
    trend = d.get("signal_trend", [])
    print(f"  signal_trend points   = {len(trend)}")
    if trend:
        print(f"  first point: {trend[0]}")
        print(f"  last  point: {trend[-1]}")

print("\n=== API AUDIT 2 COMPLETE ===")
