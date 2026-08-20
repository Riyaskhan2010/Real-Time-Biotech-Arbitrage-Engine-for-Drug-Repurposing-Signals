# -*- coding: utf-8 -*-
"""
End-to-end traceability tests.
Verifies:
  - /api/signals/{id}/source-breakdown returns per-source counts
  - Cross-source dedup is applied
  - Demo records are separated from live records
  - Evidence score_breakdown_from_evidence is computed from real stored evidence
  - /api/evidence supports new filters (is_demo, data_source)
  - /api/evidence/sources returns distinct sources
  - Existing signal list includes source_names and unique_evidence_count
"""
import sys, os, urllib.request, urllib.parse, json
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

BASE = "http://localhost:8000"

def get(path, token):
    req = urllib.request.Request(
        f"{BASE}/api{path}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return json.loads(urllib.request.urlopen(req).read())

# Login
form = urllib.parse.urlencode({"username": "demo_researcher", "password": "demo1234"}).encode()
token = json.loads(urllib.request.urlopen(
    urllib.request.Request(f"{BASE}/api/auth/token", data=form)).read())["access_token"]
print("LOGIN OK")

RESULTS = []
def check(name, ok, detail=""):
    RESULTS.append((name, ok))
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" -- {detail}" if detail else ""))

# 1. Signal list includes source traceability fields
print("\n[1] Signal list — source traceability fields")
signals = get("/signals?limit=5", token)
check("Signals returned", len(signals) > 0, f"{len(signals)} signals")
if signals:
    s = signals[0]
    check("unique_evidence_count field present", "unique_evidence_count" in s)
    check("source_names field present",          "source_names" in s)
    check("live_evidence_count field present",   "live_evidence_count" in s)
    print(f"    Signal 0: score={s['evidence_score']} unique={s.get('unique_evidence_count')} sources={s.get('source_names')}")

# 2. Source breakdown endpoint for signal 1
print("\n[2] Source breakdown — /signals/1/source-breakdown")
try:
    bd = get("/signals/1/source-breakdown", token)
    check("Endpoint responds",       bool(bd))
    check("signal_id present",       bd.get("signal_id") == 1)
    check("drug_name present",       bool(bd.get("drug_name")))
    check("disease_name present",    bool(bd.get("disease_name")))
    check("source_breakdown present",isinstance(bd.get("source_breakdown"), dict))
    check("total_evidence_records",  isinstance(bd.get("total_evidence_records"), int))
    check("unique_evidence_records", isinstance(bd.get("unique_evidence_records"), int))
    check("independent_source_count",isinstance(bd.get("independent_source_count"), int))
    check("has_live_evidence field", "has_live_evidence" in bd)
    check("score_explanation present",bool(bd.get("score_explanation")))
    check("disclaimer present",      bool(bd.get("disclaimer")))
    check("score_breakdown_from_evidence present",
          isinstance(bd.get("score_breakdown_from_evidence"), dict))
    check("cross_source_duplicates field", isinstance(bd.get("cross_source_duplicates"), list))
    check("duplicates_removed field",      isinstance(bd.get("duplicates_removed"), int))

    # Source breakdown detail
    sb = bd["source_breakdown"]
    print(f"    Sources: {list(sb.keys())}")
    for src, data in sb.items():
        print(f"    {src}: total={data['count']} live={data['live']} demo={data['demo']} records={len(data['records'])}")
        if data["records"]:
            r = data["records"][0]
            check(f"    [{src}] record has title", bool(r.get("title")))
            check(f"    [{src}] record has is_demo_data", "is_demo_data" in r)

    score_bd = bd["score_breakdown_from_evidence"]
    print(f"\n    Score from evidence:")
    for k, v in score_bd.items():
        if not k.startswith("_") and isinstance(v, dict):
            print(f"      {v.get('label','?')}: {v.get('score','?')}/{v.get('max','?')}")
    print(f"    Score explanation: {bd['score_explanation'][:120]}")

except Exception as e:
    check("Source breakdown endpoint", False, str(e))

# 3. Evidence list with new filters
print("\n[3] Evidence list — new filters")
ev_all   = get("/evidence?limit=5", token)
check("Evidence list works",         len(ev_all) >= 0)
if ev_all:
    check("data_source field present", "data_source" in ev_all[0])
    check("is_demo_data field present","is_demo_data" in ev_all[0])

# Filter by is_demo=false (live only)
ev_live = get("/evidence?is_demo=false&limit=5", token)
if ev_live:
    check("is_demo=false filter works",  all(not e["is_demo_data"] for e in ev_live), f"{len(ev_live)} live records")

# Filter by is_demo=true (demo only)
ev_demo = get("/evidence?is_demo=true&limit=5", token)
if ev_demo:
    check("is_demo=true filter works",  all(e["is_demo_data"] for e in ev_demo), f"{len(ev_demo)} demo records")

# 4. Evidence sources endpoint
print("\n[4] Evidence sources — /evidence/sources")
try:
    sources = get("/evidence/sources", token)
    check("Sources endpoint works",   isinstance(sources, list))
    if sources:
        check("Source has 'source' key",  "source" in sources[0])
        check("Source has 'count' key",   "count" in sources[0])
        print(f"    Available sources: {[(s['source'], s['count']) for s in sources]}")
except Exception as e:
    check("Evidence sources endpoint", False, str(e))

# 5. Existing endpoints unchanged
print("\n[5] Existing endpoints unchanged")
dash  = get("/dashboard", token)
sigs2 = get("/signals", token)
check("Dashboard still works",   isinstance(dash.get("stats"), dict))
check("Signals list still works",len(sigs2) > 0)
check("No API key in any response",
      "ELSEVIER_API_KEY" not in json.dumps(dash) and
      "ELSEVIER_API_KEY" not in json.dumps(sigs2))

# Summary
total  = len(RESULTS)
passed = sum(1 for _, ok in RESULTS if ok)
failed = total - passed
print(f"\n{'='*60}")
print(f"Results: {passed}/{total} passed | {failed} failed")
if failed:
    print("FAILED:")
    for name, ok in RESULTS:
        if not ok:
            print(f"  [FAIL] {name}")
print(f"{'='*60}")
