# -*- coding: utf-8 -*-
"""Final API verification for ingestion endpoints."""
import sys, urllib.request, urllib.parse, json

BASE = "http://localhost:8000"

def get(path, token):
    req = urllib.request.Request(f"{BASE}/api{path}",
                                  headers={"Authorization": f"Bearer {token}"})
    return json.loads(urllib.request.urlopen(req).read())

def post(path, token, data=None):
    body = json.dumps(data or {}).encode()
    req  = urllib.request.Request(f"{BASE}/api{path}", data=body,
                                   headers={"Authorization": f"Bearer {token}",
                                            "Content-Type": "application/json"},
                                   method="POST")
    return json.loads(urllib.request.urlopen(req).read())

# Login
form = urllib.parse.urlencode({"username":"demo_researcher","password":"demo1234"}).encode()
token = json.loads(urllib.request.urlopen(
    urllib.request.Request(f"{BASE}/api/auth/token", data=form)).read())["access_token"]
print("LOGIN OK")

# 1. Source status
ss = get("/ingestion/source-status", token)
print(f"\nSOURCE STATUS ({len(ss)} sources):")
for s in ss:
    print(f"  {s['source']:20} status={s['status']}  enabled={s['enabled']}")

# 2. Running check
running = get("/ingestion/running", token)
print(f"\nRUNNING: {running['running']}")

# 3. Latest run (may be 404 if none yet)
try:
    latest = get("/ingestion/latest", token)
    print(f"\nLATEST RUN: id={latest['id']} status={latest['status']} summary={latest['summary']}")
except urllib.error.HTTPError as e:
    if e.code == 404:
        print("\nLATEST RUN: None yet (404 as expected)")

# 4. Research monitor — live + demo mix
mon = get("/research-monitor", token)
print(f"\nRESEARCH MONITOR:")
print(f"  total_records={mon['total_records']}  live={mon['live_records']}  demo={mon['demo_records']}")
print(f"  has_live_data={mon['has_live_data']}")
for r in mon['recent_records'][:3]:
    mode = r.get('data_mode','demo')
    print(f"  [{mode.upper():4}] {r['source']:15} {r['title'][:50]}")

# 5. Existing endpoints still work
dash = get("/dashboard", token)
sigs = get("/signals", token)
alrt = get("/alerts", token)
print(f"\nEXISTING ENDPOINTS OK:")
print(f"  dashboard signals={dash['stats']['total_signals']}")
print(f"  signals list={len(sigs)}")
print(f"  alerts={len(alrt)}")

print("\n=== ALL CHECKS PASSED ===")
