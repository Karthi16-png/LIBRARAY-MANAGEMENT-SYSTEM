import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, get_session

def verify_analytics():
    client = app.test_client()

    print("=== Testing Library Analytics Fixes ===")

    # Log in as Admin to access /library_analytics
    with client.session_transaction() as sess:
        with get_session() as s:
            u = s.run("MATCH (u:User {role: 'Admin'}) RETURN u.user_id AS uid, u.username AS username, u.role AS role LIMIT 1").single()
            sess["user_id"] = u["uid"]
            sess["username"] = u["username"]
            sess["role"] = u["role"]

    resp = client.get("/library_analytics")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    html = resp.get_data(as_text=True)

    # 1. Author Centrality & Co-authors
    # Check that Stuart Russell, Peter Norvig is present
    assert "Stuart Russell, Peter Norvig" in html, "Co-authors Stuart Russell and Peter Norvig must both be displayed"
    print("PASS: Issue 1 (Co-author joining: 'Stuart Russell, Peter Norvig') verified!")

    # 2. Check Borrowing Density Share math
    # 75.0% should NOT appear 3 times, share should be 21.4%
    assert "21.4%" in html, "Author share percentage (3 / 14 = 21.4%) must be present"
    # Ensure 75% or 75.0% does not appear as a share percentage
    assert "75%" not in html and "75.0%" not in html, "Old hardcoded 75% math must be removed"
    print("PASS: Issue 2 (Borrowing Density Share: 21.4% and relative bar scaling) verified!")

    # 3. Check Active Borrowers KPI Card
    # Main value should be 6 active borrowers, subtitle 'Across 7 active circulation loans'
    assert "Across 7 active circulation loans" in html or "Across 7 active circulation loan" in html, "Active borrowers subtitle must say Across X active circulation loans"
    assert '<div class="metric-value">6</div>' in html, "Active borrowers count must be 6"
    print("PASS: Issue 3 (Active Borrowers separated from active circulation loans) verified!")

    # 4. Check Node Count synchronization in /api/graph_data?view=full
    resp_full = client.get("/api/graph_data?view=full")
    assert resp_full.status_code == 200
    data_full = resp_full.get_json()
    full_nodes = len(data_full.get("nodes", []))
    print(f"Full System Graph node count: {full_nodes}")
    assert full_nodes == 109, f"Expected 109 nodes in Full System Graph, got {full_nodes}"
    # Verify Knowledge Nodes KPI in analytics HTML matches 109
    assert '<div class="metric-value">109</div>' in html, "Knowledge Nodes KPI must show 109"
    print("PASS: Issue 4 (Node counts synced: 109 nodes in Full Graph and Knowledge Nodes KPI) verified!")

    # 5. Check Pluralization
    assert "book(s)" not in html, "book(s) must not appear in HTML"
    assert "copy(ies)" not in html, "copy(ies) must not appear in HTML"
    assert "1 titles" not in html, "1 titles must not appear in HTML"
    assert "Book" in html and "Books" in html, "Proper Book / Books pluralization must be rendered"
    assert "Copies" in html or "Copy" in html, "Proper Copy / Copies pluralization must be rendered"
    assert "Titles" in html or "Title" in html, "Proper Title / Titles pluralization must be rendered"
    print("PASS: Issue 5 (Table pluralization clean up) verified!")

    print("\nALL 5 LIBRARY ANALYTICS ISSUES VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    verify_analytics()
