"""Read-only live API audit — hits the running backend at localhost:8000."""
import httpx, json, sys

BASE = "http://localhost:8000"

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def get(client, path, params=None, timeout=15):
    r = client.get(BASE + path, params=params, timeout=timeout)
    return r.status_code, r.json() if r.headers.get("content-type","").startswith("application/json") else r.text

# ── Auth ──────────────────────────────────────────────────────────────────────
section("AUTH")
with httpx.Client(timeout=10) as c:
    r = c.post(BASE + "/api/auth/token", data={"username": "demo_researcher", "password": "demo1234"})
    if r.status_code != 200:
        print(f"LOGIN FAILED: {r.status_code} {r.text}")
        sys.exit(1)
    token = r.json()["access_token"]
    print(f"Login OK. Token length={len(token)}")

headers = {"Authorization": f"Bearer {token}"}

with httpx.Client(timeout=15, headers=headers) as c:

    # ── Health ────────────────────────────────────────────────────────────────
    section("HEALTH CHECK")
    st, data = get(c, "/health")
    print(f"  /health → {st} {data}")

    # ── Source status — skipped (probes live APIs, Europe PMC 503 causes timeout) ──
    section("SOURCE STATUS — SKIPPED (live API probe, EBI 503 causes timeout)")
    print("  NOTE: /api/ingestion/source-status calls each external API directly.")
    print("  Europe PMC is currently returning HTTP 503 (EBI server outage), causing timeout.")
    print("  Status verified via check_live_status.py instead (see audit_db output).")

    # ── Dashboard ─────────────────────────────────────────────────────────────
    section("DASHBOARD  (/api/dashboard)")
    st, data = get(c, "/api/dashboard")
    print(f"  HTTP {st}")
    if isinstance(data, dict):
        stats = data.get("stats", {})
        for k, v in stats.items():
            print(f"  {k:<30} {v}")

    # ── Signals list ──────────────────────────────────────────────────────────
    section("SIGNALS LIST  (/api/signals)")
    st, data = get(c, "/api/signals", params={"limit": 20})
    print(f"  HTTP {st}  count={len(data) if isinstance(data, list) else '?'}")
    if isinstance(data, list):
        for s in data:
            print(f"  [{s['id']:2d}] {s.get('drug_name','?'):<16} -> {s.get('disease_name','?'):<36} "
                  f"score={s.get('evidence_score',0):5.1f} live_ev={s.get('live_evidence_count')} "
                  f"unique={s.get('unique_evidence_count')} sources={s.get('source_names')}")

    # ── Signal 1 detail ───────────────────────────────────────────────────────
    section("SIGNAL 1 DETAIL  (/api/signals/1)")
    st, data = get(c, "/api/signals/1")
    print(f"  HTTP {st}")
    if isinstance(data, dict):
        print(f"  drug={data.get('drug',{}).get('name')}  disease={data.get('disease',{}).get('name')}")
        print(f"  score={data.get('evidence_score')}  data_source={data.get('data_source')}")
        ev_items = data.get("evidence_items", [])
        print(f"  evidence_items count={len(ev_items)}")
        live_items = [e for e in ev_items if not e.get("is_demo_data", True)]
        demo_items = [e for e in ev_items if e.get("is_demo_data", True)]
        print(f"    live={len(live_items)}  demo={len(demo_items)}")

    # ── Signal 1 source breakdown ─────────────────────────────────────────────
    section("SIGNAL 1 SOURCE BREAKDOWN  (/api/signals/1/source-breakdown)")
    st, data = get(c, "/api/signals/1/source-breakdown")
    print(f"  HTTP {st}")
    if isinstance(data, dict):
        print(f"  total_evidence_records   = {data.get('total_evidence_records')}")
        print(f"  unique_evidence_records  = {data.get('unique_evidence_records')}")
        print(f"  unique_live_records      = {data.get('unique_live_records')}")
        print(f"  unique_demo_records      = {data.get('unique_demo_records')}")
        print(f"  independent_source_count = {data.get('independent_source_count')}")
        print(f"  has_live_evidence        = {data.get('has_live_evidence')}")
        print(f"  cross_source_duplicates  = {data.get('cross_source_duplicates')}")
        print(f"  duplicates_removed       = {data.get('duplicates_removed')}")
        print(f"  score_explanation: {data.get('score_explanation','')[:120]}")
        print()
        print("  Per-source breakdown:")
        breakdown = data.get("source_breakdown", {})
        for src, info in sorted(breakdown.items()):
            print(f"    {src:<20} count={info.get('count')} live={info.get('live')} demo={info.get('demo')}")
        score_data = data.get("score_breakdown_from_evidence", {})
        print()
        print("  Score factors (from real evidence):")
        for factor, vals in score_data.items():
            if isinstance(vals, dict) and "score" in vals:
                print(f"    {vals.get('label','?'):<25} {vals.get('score')}/{vals.get('max')}")

    # ── Evidence list ─────────────────────────────────────────────────────────
    section("EVIDENCE LIST  (/api/evidence)")
    st, data = get(c, "/api/evidence", params={"limit": 5})
    print(f"  HTTP {st}  (showing 5 of total)")
    if isinstance(data, list):
        for e in data:
            print(f"  id={e['id']} src={e.get('data_source','?'):<15} type={e.get('evidence_type','?'):<20} "
                  f"demo={e.get('is_demo_data')} doi={e.get('doi')} pmid={e.get('pmid')}")
            print(f"    title={str(e.get('title',''))[:70]}")

    section("EVIDENCE FILTER: is_demo=false  (/api/evidence?is_demo=false)")
    st, data = get(c, "/api/evidence", params={"is_demo": "false", "limit": 3})
    print(f"  HTTP {st}  returned {len(data) if isinstance(data,list) else '?'} (showing 3)")
    if isinstance(data, list):
        for e in data:
            print(f"  src={e.get('data_source','?'):<15} demo={e.get('is_demo_data')}  title={str(e.get('title',''))[:60]}")

    section("EVIDENCE FILTER: is_demo=true  (/api/evidence?is_demo=true)")
    st, data = get(c, "/api/evidence", params={"is_demo": "true", "limit": 3})
    print(f"  HTTP {st}  returned {len(data) if isinstance(data,list) else '?'} demo records")
    if isinstance(data, list):
        for e in data:
            print(f"  src={e.get('data_source','?'):<15} demo={e.get('is_demo_data')}  title={str(e.get('title',''))[:60]}")

    section("EVIDENCE SOURCES  (/api/evidence/sources)")
    st, data = get(c, "/api/evidence/sources")
    print(f"  HTTP {st}")
    if isinstance(data, list):
        for s in data:
            print(f"  {s.get('source','?'):<20} count={s.get('count')}")

    # ── Research Monitor ──────────────────────────────────────────────────────
    section("RESEARCH MONITOR  (/api/research-monitor)")
    st, data = get(c, "/api/research-monitor")
    print(f"  HTTP {st}")
    if isinstance(data, dict):
        print(f"  total_records = {data.get('total_records')}")
        print(f"  live_records  = {data.get('live_records')}")
        print(f"  demo_records  = {data.get('demo_records')}")
        print(f"  has_live_data = {data.get('has_live_data')}")
        recs = data.get("recent_records", [])
        live_recs = [r for r in recs if not r.get("is_demo_data", True)]
        print(f"  live record titles (first 5):")
        for r in live_recs[:5]:
            print(f"    [{r.get('source','?')}] {str(r.get('title',''))[:80]}")

    # ── Drugs ─────────────────────────────────────────────────────────────────
    section("DRUGS  (/api/drugs)")
    st, data = get(c, "/api/drugs")
    print(f"  HTTP {st}  count={len(data) if isinstance(data,list) else '?'}")
    if isinstance(data, list):
        for d in data:
            print(f"  [{d['id']}] {d['name']}")

    # ── Diseases ──────────────────────────────────────────────────────────────
    section("DISEASES  (/api/diseases)")
    st, data = get(c, "/api/diseases")
    print(f"  HTTP {st}  count={len(data) if isinstance(data,list) else '?'}")
    if isinstance(data, list):
        for d in data:
            print(f"  [{d['id']}] {d['name']}")

    # ── Ingestion history ────────────────────────────────────────────────────
    section("INGESTION HISTORY  (/api/ingestion/runs)")
    st, data = get(c, "/api/ingestion/runs")
    print(f"  HTTP {st}")
    if isinstance(data, list):
        for run in data[:5]:
            print(f"  run_id={run.get('id')} status={run.get('status')} "
                  f"new={run.get('total_new')} dups={run.get('total_duplicates')} "
                  f"sigs_updated={run.get('signals_updated')} sigs_created={run.get('signals_created')}")
            print(f"    summary: {str(run.get('summary',''))[:100]}")
    else:
        print(f"  {data}")

print("\n=== API AUDIT COMPLETE ===")
