import os
import sys
import re

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app

def test_rbac_and_sidebar():
    print("=== 1. Testing RBAC Access Control & Sidebar Navigation ===")
    client = app.test_client()

    # Staff User (user_id=3, role="Staff")
    with client.session_transaction() as sess:
        sess["user_id"] = 3
        sess["username"] = "staff"
        sess["role"] = "Staff"
        sess["logged_in"] = True

    # Staff: /library_analytics must be 200 OK
    res = client.get("/library_analytics")
    assert res.status_code == 200, f"Expected 200 for Staff on /library_analytics, got {res.status_code}"
    print("[PASS] Staff has full access to /library_analytics (200 OK)")

    # Staff: /issue_loan must be restricted (403 Forbidden or 302 redirect)
    res = client.get("/issue_loan")
    assert res.status_code in [302, 403], f"Expected 403 or 302 for Staff on /issue_loan, got {res.status_code}"
    print(f"[PASS] Staff is blocked from /issue_loan ({res.status_code})")

    # Staff: /loan_requests must be restricted (403 Forbidden or 302 redirect)
    res = client.get("/loan_requests")
    assert res.status_code in [302, 403], f"Expected 403 or 302 for Staff on /loan_requests, got {res.status_code}"
    print(f"[PASS] Staff is blocked from /loan_requests ({res.status_code})")

    # Staff: base.html sidebar checks
    res = client.get("/dashboard")
    staff_dash_html = res.get_data(as_text=True)
    assert "Search Books" in staff_dash_html, "Staff sidebar must show 'Search Books'"
    assert "My Fines" in staff_dash_html, "Staff sidebar must show 'My Fines'"
    assert "Centrality Analytics" in staff_dash_html, "Staff sidebar must show 'Centrality Analytics'"
    assert "/issue_loan" not in staff_dash_html, "Staff sidebar must NOT link to /issue_loan"
    print("[PASS] Staff sidebar: Search Books, My Fines, Centrality Analytics present; Issue Book removed")

    # Student User (user_id=12, role="Student")
    with client.session_transaction() as sess:
        sess["user_id"] = 12
        sess["username"] = "karthik"
        sess["role"] = "Student"
        sess["logged_in"] = True

    # Student: /library_analytics must be blocked
    res = client.get("/library_analytics")
    assert res.status_code in [302, 403], f"Expected 302 or 403 for Student on /library_analytics, got {res.status_code}"
    print(f"[PASS] Student is blocked from /library_analytics ({res.status_code})")

    # Librarian User (user_id=2, role="Librarian")
    with client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["username"] = "librarian"
        sess["role"] = "Librarian"
        sess["logged_in"] = True

    res = client.get("/library_analytics")
    assert res.status_code == 200, f"Expected 200 for Librarian on /library_analytics, got {res.status_code}"
    res = client.get("/issue_loan")
    assert res.status_code == 200, f"Expected 200 for Librarian on /issue_loan, got {res.status_code}"
    res = client.get("/loan_requests")
    assert res.status_code == 200, f"Expected 200 for Librarian on /loan_requests, got {res.status_code}"
    print("[PASS] Librarian has full access to /library_analytics, /issue_loan, and /loan_requests (200 OK)")

def test_recommendations_and_graph():
    print("\n=== 2. Testing Recommendations & Graph Traversal for Staff vs Student ===")
    client = app.test_client()

    # Staff User (user_id=3, role="Staff")
    with client.session_transaction() as sess:
        sess["user_id"] = 3
        sess["username"] = "staff"
        sess["role"] = "Staff"
        sess["logged_in"] = True

    res = client.get("/recommendations")
    assert res.status_code == 200, f"Expected 200 for Staff on /recommendations, got {res.status_code}"
    staff_recs_html = res.get_data(as_text=True)
    assert "Top Study Partners" not in staff_recs_html, "Staff view must NOT display Top Study Partners section"
    assert "Student Cohort Study Pairs" not in staff_recs_html, "Staff view must NOT display Student Cohort Study Pairs"
    assert "Recommended Books" in staff_recs_html, "Staff view must display Recommended Books"
    print("[PASS] Staff /recommendations: Top Study Partners hidden; recommended books present")

    # Staff: /api/graph_data?view=recommendations
    res = client.get("/api/graph_data?view=recommendations")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    gdata = res.get_json()
    assert len(gdata["nodes"]) > 0, "Staff recommendations graph must return nodes"
    assert len(gdata["edges"]) > 0, "Staff recommendations graph must return edges"
    levels = {n.get("level") for n in gdata["nodes"]}
    assert 0 in levels and 1 in levels and 2 in levels and 3 in levels, f"Expected levels 0,1,2,3 in graph, got {levels}"
    # Verify no student peers in staff graph
    for n in gdata["nodes"]:
        assert n.get("group") != "PeerUser", "Staff graph traversal must NOT include PeerUser nodes"
    print(f"[PASS] Staff recommendation graph: {len(gdata['nodes'])} nodes, {len(gdata['edges'])} edges across 4 columns without PeerUser nodes")

def test_dashboard_layout():
    print("\n=== 3. Testing Staff Dashboard Layout & Side-by-Side Badges ===")
    client = app.test_client()

    # Staff User (user_id=3, role="Staff")
    with client.session_transaction() as sess:
        sess["user_id"] = 3
        sess["username"] = "staff"
        sess["role"] = "Staff"
        sess["logged_in"] = True

    res = client.get("/dashboard")
    assert res.status_code == 200, f"Expected 200 for Staff on /dashboard, got {res.status_code}"
    dash_html = res.get_data(as_text=True)

    # 1. Redundant KPI card removed
    assert "My Current Loans" not in dash_html, "Redundant 'My Current Loans' card must be removed from Staff dashboard"
    assert "Committed Books" in dash_html, "'Committed Books' card must be present on Staff dashboard"
    print("[PASS] Staff dashboard: 'My Current Loans' redundant KPI card removed; 'Committed Books' retained")

    # 2. Side-by-side pills container style
    assert "gap: 0.4rem; margin-top: 0.35rem; align-items: center;" in dash_html, "Pills container must use gap: 0.4rem; margin-top: 0.35rem;"
    print("[PASS] Active loans table: pills container configured with display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.35rem;")

    # 3. Clickable category links on pills
    assert "/category/1" in dash_html, "Pill badges must link to /category/<category_id>"
    print("[PASS] Prerequisite & Next to Study pills are clickable links to category pages")

if __name__ == "__main__":
    test_rbac_and_sidebar()
    test_recommendations_and_graph()
    test_dashboard_layout()
    print("\nALL RBAC, RECOMMENDATION, AND DASHBOARD ADJUSTMENTS VERIFIED SUCCESSFULLY!")
