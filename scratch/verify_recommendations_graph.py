import sys
sys.path.insert(0, ".")
from app import app

client = app.test_client()

# 1. Test student login session and /recommendations HTML
with client.session_transaction() as sess:
    sess["user_id"] = 6
    sess["username"] = "student1"
    sess["role"] = "Student"

rec_res = client.get("/recommendations")
assert rec_res.status_code == 200, f"Expected 200, got {rec_res.status_code}"
html = rec_res.get_data(as_text=True)

# Verify subtitle formula and spelling
assert "(Recommended Book)" in html, "Missing '(Recommended Book)' in HTML"
assert "Recommnended" not in html, "Found typo 'Recommnended' in HTML"
assert "[:borrowed]" in html, "Missing '[:borrowed]' in HTML"
assert "[:shared]" in html, "Missing '[:shared]' in HTML"
assert "[:recommends]" in html, "Missing '[:recommends]' in HTML"

# Verify Vis.js layout options in HTML
assert "hierarchical" in html, "Missing hierarchical in HTML"
assert "direction: 'LR'" in html or 'direction: "LR"' in html, "Missing direction LR in HTML"
assert "levelSeparation: 230" in html, "Missing levelSeparation: 230 in HTML"
assert "nodeSpacing: 110" in html, "Missing nodeSpacing: 110 in HTML"
assert "treeSpacing: 130" in html, "Missing treeSpacing: 130 in HTML"
assert "physics:" in html and "enabled: false" in html, "Physics should be disabled"
assert "widthConstraint: { maximum: 145 }" in html, "Missing widthConstraint in HTML"
assert "margin: 10" in html, "Missing margin: 10 in HTML"

print("? recommendations.html tests PASSED")

# 2. Test /api/graph_data?view=recommendations API endpoint
api_res = client.get("/api/graph_data?view=recommendations")
assert api_res.status_code == 200, f"Expected 200, got {api_res.status_code}"
data = api_res.get_json()
nodes = data.get("nodes", [])
edges = data.get("edges", [])

print(f"? /api/graph_data returned {len(nodes)} nodes and {len(edges)} edges")

node_by_id = {n["id"]: n for n in nodes}
levels_present = set(n.get("level") for n in nodes)
print(f"Levels present in nodes: {sorted(list(levels_present))}")

assert 0 in levels_present, "Level 0 (You) missing"
assert 1 in levels_present, "Level 1 (Read / Category) missing"
assert 2 in levels_present, "Level 2 (Peer) missing"
assert 3 in levels_present, "Level 3 (Recommended) missing"

# Verify peer filtering: no staff/admin peers
for n in nodes:
    if n.get("group") == "PeerUser":
        props = n.get("properties", {})
        assert props.get("role") == "Student", f"Found non-student peer: {props}"

# Verify edge directions: only L0 -> L1, L1 -> L2, L2 -> L3
for e in edges:
    src = node_by_id.get(e["from"])
    dst = node_by_id.get(e["to"])
    assert src and dst, f"Edge references missing node: {e}"
    src_lvl = src.get("level")
    dst_lvl = dst.get("level")
    assert dst_lvl == src_lvl + 1, f"Invalid edge flow from L{src_lvl} to L{dst_lvl}: {e}"
    assert e["label"] in ["borrowed", "shared", "recommends"], f"Unexpected edge label: {e['label']}"
    assert e["font"]["background"] == "#0f172a", f"Edge font background mismatch: {e['font']}"

print("? Graph edge flow and levels strictly sequential (L0 -> L1 -> L2 -> L3)!")
print("ALL RECOMMENDATION GRAPH TESTS PASSED!")
