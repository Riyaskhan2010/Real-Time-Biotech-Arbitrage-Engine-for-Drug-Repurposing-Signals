# -*- coding: utf-8 -*-
"""Check live /api/ingestion/source-status endpoint."""
import urllib.request, urllib.parse, json

BASE = "http://localhost:8000"
data = urllib.parse.urlencode({"username": "demo_researcher", "password": "demo1234"}).encode()
token = json.loads(urllib.request.urlopen(
    urllib.request.Request(f"{BASE}/api/auth/token", data=data)).read())["access_token"]

h = {"Authorization": f"Bearer {token}"}
req = urllib.request.Request(f"{BASE}/api/ingestion/source-status", headers=h)
results = json.loads(urllib.request.urlopen(req).read())

print("Source status from live backend:")
for r in results:
    err = r.get("error", "")[:60] if r.get("error") else ""
    print(f"  {r['source']:25}  status={r['status']:15}  enabled={r['enabled']}  {err}")
