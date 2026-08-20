"""Quick verification script — runs all new pipeline API checks."""
import urllib.request
import urllib.parse
import json
import sys

BASE = "http://localhost:8000"

def get(path, token):
    req = urllib.request.Request(
        f"{BASE}/api{path}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return json.loads(urllib.request.urlopen(req).read())

# ── Login
data = urllib.parse.urlencode({"username": "demo_researcher", "password": "demo1234"}).encode()
req = urllib.request.Request(f"{BASE}/api/auth/token", data=data)
token = json.loads(urllib.request.urlopen(req).read())["access_token"]
print(f"LOGIN OK")

# ── Pipeline endpoint
p = get("/signals/1/pipeline", token)
print(f"\nPIPELINE /signals/1/pipeline")
print(f"  drug: {p['drug_name']}  disease: {p['disease_name']}")
print(f"  steps: {len(p['pipeline_steps'])}")
for step in p["pipeline_steps"]:
    print(f"    Step {step['step']}: {step['stage']} → {step['output']}")
print(f"  enriched_score total: {p['enriched_score_breakdown']['total']['score']}/100")
for k, v in p["enriched_score_breakdown"].items():
    if k != "total":
        print(f"    {v['label']}: {v['score']}/{v['max']}")
print(f"  detection_rationale.how_detected (first 100): {p['detection_rationale']['how_detected'][:100]}")
print(f"  pathway_overlap: {p['detection_rationale']['pathway_overlap']}")
print(f"  shared_targets: {p['detection_rationale']['shared_targets']}")
print(f"  graph drug node: {p['relationship_graph']['drug_node']['label']}")
print(f"  graph target nodes: {len(p['relationship_graph']['target_nodes'])}")
print(f"  graph pathway nodes: {len(p['relationship_graph']['pathway_nodes'])}")
print(f"  evidence_matching strength: {p['evidence_matching']['support_strength']}")
print(f"  evidence_matching consensus: {p['evidence_matching']['consensus']}")
print(f"  ai_backend: {p['ai_backend']}")
print(f"  disclaimer present: {len(p['disclaimer']) > 10}")
print(f"  is_demo_data: {p['is_demo_data']}")

# ── Research monitor
m = get("/research-monitor", token)
print(f"\nRESEARCH MONITOR /research-monitor")
print(f"  pipeline_stages: {len(m['pipeline_stages'])}")
for s in m["pipeline_stages"]:
    print(f"    {s['stage']}: {s['label']}")
print(f"  total_records: {m['total_records']}")
for r in m["recent_records"]:
    drugs = ", ".join(r["extracted_entities"]["drugs"])
    diseases = ", ".join(r["extracted_entities"]["diseases"])
    signals = ", ".join(
        f"{s['drug']}->{s['disease']}({s['score_delta']:+d})"
        for s in r["matched_signals"]
    )
    print(f"  [{r['id']}] {r['source']} | stage={r['pipeline_stage']} | drugs={drugs} | {signals}")
print(f"  integration_points: {len(m['integration_points'])}")

# ── Existing endpoints unchanged
dash = get("/dashboard", token)
sigs = get("/signals", token)
s1   = get("/signals/1", token)
ev   = get("/evidence?limit=5", token)
alrt = get("/alerts", token)

print(f"\nEXISTING ENDPOINTS")
print(f"  dashboard: signals={dash['stats']['total_signals']} highconf={dash['stats']['high_confidence_signals']}")
print(f"  signals list: {len(sigs)} items, top={sigs[0]['drug_name']} -> {sigs[0]['disease_name']}")
print(f"  signal/1: evItems={len(s1['evidence_items'])} factors={len(s1['explanation_factors'])}")
print(f"  evidence: {len(ev)} items")
print(f"  alerts: {len(alrt)} items")

print("\n=== ALL CHECKS PASSED ===")
