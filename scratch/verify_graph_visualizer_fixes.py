import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, get_session

def verify_all():
    client = app.test_client()

    print("=== Testing Verification of Graph Visualizer Fixes ===")

    # 1. Login as karthik (student) and test personal borrowing view
    with client.session_transaction() as sess:
        # Find karthik user_id
        with get_session() as s:
            u = s.run("MATCH (u:User {username: 'karthik'}) RETURN u.user_id AS uid, u.role AS role").single()
            sess["user_id"] = u["uid"]
            sess["username"] = "karthik"
            sess["role"] = u["role"]
            karthik_uid = u["uid"]

    resp = client.get("/api/graph_data?view=personal")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.get_json()
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    groups = {}
    for n in nodes:
        g = n.get("group")
        groups[g] = groups.get(g, 0) + 1

    print("Karthik Personal Subgraph Groups:", groups)
    assert "Author" not in groups, f"Author nodes must NOT be in personal view: {groups}"
    assert "Category" not in groups, f"Category nodes must NOT be in personal view: {groups}"
    assert "Publisher" not in groups, f"Publisher nodes must NOT be in personal view: {groups}"
    assert "User" in groups, "User must be present"
    assert "Book" in groups, "Book must be present"
    assert "Copy" in groups, "Copy must be present"
    assert "Loan" in groups, "Loan must be present"

    # Check that any LoanRequest node in personal view has status in ['Pending', 'Awaiting Pickup']
    for n in nodes:
        if n.get("group") == "LoanRequest":
            status = n.get("properties", {}).get("status")
            assert status in ["Pending", "Awaiting Pickup"], f"LoanRequest status {status} should not be in personal view: {n}"
            print(f"Verified LoanRequest #{n.get('properties', {}).get('request_id')} has status: {status}")

    print("PASS: Issue 1 (Personal Subgraph Scoping & Active-only Requests) verified!")

    # 2. Login as admin and test Global Circulation & Fines view
    with client.session_transaction() as sess:
        with get_session() as s:
            u = s.run("MATCH (u:User {username: 'admin'}) RETURN u.user_id AS uid, u.role AS role").single()
            sess["user_id"] = u["uid"]
            sess["username"] = "admin"
            sess["role"] = u["role"]

    # Test view=personal (which maps to circulation for admin)
    resp_admin = client.get("/api/graph_data?view=personal")
    assert resp_admin.status_code == 200
    data_admin = resp_admin.get_json()
    nodes_admin = data_admin.get("nodes", [])
    edges_admin = data_admin.get("edges", [])

    groups_admin = {}
    for n in nodes_admin:
        g = n.get("group")
        groups_admin[g] = groups_admin.get(g, 0) + 1

    print("Admin Circulation Subgraph Groups (view=personal):", groups_admin)
    print(f"Total admin circulation nodes: {len(nodes_admin)}, edges: {len(edges_admin)}")
    assert "Author" not in groups_admin, f"Author nodes must NOT be in circulation view: {groups_admin}"
    assert "Category" not in groups_admin, f"Category nodes must NOT be in circulation view: {groups_admin}"
    assert "Publisher" not in groups_admin, f"Publisher nodes must NOT be in circulation view: {groups_admin}"
    assert "User" in groups_admin
    assert "Loan" in groups_admin
    assert "Copy" in groups_admin
    assert "Book" in groups_admin
    assert "Fine" in groups_admin
    assert "LoanRequest" in groups_admin

    # Check active requests only in circulation
    for n in nodes_admin:
        if n.get("group") == "LoanRequest":
            status = n.get("properties", {}).get("status")
            assert status in ["Pending", "Awaiting Pickup"], f"Request status {status} should not be in circulation: {n}"

    # Also test view=circulation
    resp_circ = client.get("/api/graph_data?view=circulation")
    assert resp_circ.status_code == 200
    data_circ = resp_circ.get_json()
    assert len(data_circ.get("nodes", [])) == len(nodes_admin)

    # Test full view has Authors/Categories so full graph still works
    resp_full = client.get("/api/graph_data?view=full")
    assert resp_full.status_code == 200
    data_full = resp_full.get_json()
    nodes_full = data_full.get("nodes", [])
    groups_full = {}
    for n in nodes_full:
        g = n.get("group")
        groups_full[g] = groups_full.get(g, 0) + 1
    print(f"Full System Graph nodes: {len(nodes_full)}, Groups: {groups_full}")
    assert "Author" in groups_full and "Category" in groups_full and "Publisher" in groups_full

    print("PASS: Issue 2 (Admin Global Circulation & Fines Scoping) verified!")

    # 3. Check templates/graph_visualizer.html for Vis.js physics and edge options
    with open("templates/graph_visualizer.html", encoding="utf-8") as f:
        html = f.read()

    assert "graph-legend-badge" not in html, "graph-legend-badge should be completely removed"
    assert "barnesHut" in html, "barnesHut solver must be present in graph_visualizer.html"
    assert "gravitationalConstant: -4500" in html, "gravitationalConstant: -4500 must be set"
    assert "springLength: 165" in html, "springLength: 165 must be set"
    assert "curvedCW" in html, "smooth: { type: 'curvedCW' } must be set"
    assert "align: 'top'" in html, "edge font align: 'top' must be set"
    assert "strokeWidth: 3" in html, "edge strokeWidth: 3 must be set"
    assert "#090d16" in html, "edge strokeColor: '#090d16' must be set"

    print("PASS: Issue 3 (Vis.js physics options & edge styling) verified!")

    # 4. Check live count chips in HTML and disabled styling
    assert 'class="pill-count"' in html, "pill-count spans must be present in HTML"
    assert 'id="count-User"' in html
    assert 'id="count-Book"' in html
    assert 'id="count-Author"' in html
    assert 'id="count-Category"' in html
    assert 'id="count-Publisher"' in html
    assert 'id="count-Copy"' in html
    assert 'id="count-Loan"' in html
    assert 'id="count-Fine"' in html
    assert 'id="count-LoanRequest"' in html
    assert ".filter-pill.disabled" in html, ".filter-pill.disabled CSS rule must be present"

    print("PASS: Issue 4 (Legend removed, filter chip counts & auto-dimming) verified!")

    print("\nALL 4 ISSUES VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    verify_all()
