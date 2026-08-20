"""
End-to-end test: Dashboard → Signal → Pipeline → Evidence → Score → Monitor
"""
import urllib.request, urllib.parse, json, sys

BASE = "http://localhost:8000"

def get(path, token):
    req = urllib.request.Request(
        f"{BASE}/api{path}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return json.loads(urllib.request.urlopen(req).read())

# 1. Login
data = urllib.parse.urlencode({"username": "demo_researcher", "password": "demo1234"}).encode()
token = json.loads(urllib.request.urlopen(
    urllib.request.Request(f"{BASE}/api/auth/token", data=data)
).read())["access_token"]
print("1. LOGIN OK")

# 2. Dashboard — find high-confidence signal
dash = get("/dashboard", token)
hc = dash["high_confidence_signals"]
assert len(hc) > 0, "No high-confidence signals on dashboard"
sig_id = hc[0]["id"]
print(f"2. DASHBOARD — {dash['stats']['total_signals']} signals, {dash['stats']['high_confidence_signals']} high-conf")
print(f"   Top high-conf: {hc[0]['drug_name']} → {hc[0]['disease_name']} (score={hc[0]['evidence_score']})")

# 3. Signal detail
sig = get(f"/signals/{sig_id}", token)
assert sig["evidence_items"] is not None
assert len(sig["explanation_factors"]) > 0
print(f"3. SIGNAL DETAIL — {sig['drug']['name']} → {sig['disease']['name']}")
print(f"   evidence_items={len(sig['evidence_items'])} factors={len(sig['explanation_factors'])}")
print(f"   ai_explanation present: {bool(sig['ai_explanation'])}")

# 4. Pipeline (detection pipeline + score + graph + monitor connection)
pipe = get(f"/signals/{sig_id}/pipeline", token)
assert len(pipe["pipeline_steps"]) == 6, f"Expected 6 steps, got {len(pipe['pipeline_steps'])}"
assert pipe["enriched_score_breakdown"]["total"]["score"] > 0
assert pipe["relationship_graph"]["drug_node"]["label"] == sig["drug"]["name"]
assert len(pipe["relationship_graph"]["target_nodes"]) > 0
assert len(pipe["relationship_graph"]["pathway_nodes"]) > 0
assert pipe["detection_rationale"]["how_detected"]
assert pipe["evidence_matching"]["support_strength"] in ("strong", "moderate", "weak")
print(f"4. PIPELINE — {len(pipe['pipeline_steps'])} steps")
for s in pipe["pipeline_steps"]:
    print(f"   Step {s['step']}: {s['stage']} → {s['output']}")
print(f"   Score total: {pipe['enriched_score_breakdown']['total']['score']}/100")
for k in ["research_evidence","clinical_evidence","mechanism_match","independent_sources","recency"]:
    f = pipe["enriched_score_breakdown"][k]
    print(f"   {f['label']}: {f['score']}/{f['max']}")
print(f"   Graph drug: {pipe['relationship_graph']['drug_node']['label']}")
print(f"   Graph targets: {len(pipe['relationship_graph']['target_nodes'])}")
print(f"   Evidence matching: {pipe['evidence_matching']['support_strength']}")
print(f"   Disclaimer present: {len(pipe['disclaimer']) > 50}")

# 5. Evidence items
assert all("title" in e for e in sig["evidence_items"])
assert all("evidence_type" in e for e in sig["evidence_items"])
assert all("is_demo_data" in e for e in sig["evidence_items"])
print(f"5. EVIDENCE — {len(sig['evidence_items'])} items, all have title/type/demo flag")
for e in sig["evidence_items"]:
    print(f"   [{e['evidence_type']}] {e['title'][:60]}... demo={e['is_demo_data']}")

# 6. Research monitor connection
mon = get("/research-monitor", token)
drug_name = sig["drug"]["name"]
matched = [r for r in mon["recent_records"]
           if any(s["drug"] == drug_name for s in r.get("matched_signals", []))]
print(f"6. RESEARCH MONITOR — {mon['total_records']} records, {len(matched)} match {drug_name}")
for r in matched:
    print(f"   [{r['id']}] {r['source']} | stage={r['pipeline_stage']}")

# 7. Safety — check no forbidden phrases
forbidden = ["treats alzheimer", "treats the disease", "clinically proven", "prescribe"]
explanation = (sig.get("ai_explanation") or "").lower()
for phrase in forbidden:
    assert phrase not in explanation, f"SAFETY FAIL: found '{phrase}' in explanation"
assert "not a clinical" in pipe["disclaimer"].lower() or "not for clinical" in pipe["disclaimer"].lower() or "not clinical" in pipe["disclaimer"].lower()
print(f"7. SAFETY CHECK — No forbidden clinical claims in explanations or disclaimers")

print("\n=== ALL CHECKS PASSED ===")
print(f"Demo flow: Dashboard → Signal #{sig_id} ({sig['drug']['name']} → {sig['disease']['name']}) → Pipeline (6 steps) → Evidence ({len(sig['evidence_items'])} items) → Score ({pipe['enriched_score_breakdown']['total']['score']}/100) → Research Monitor ({len(matched)} events)")
