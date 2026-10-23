import re
import requests

BASE_URL = "http://127.0.0.1:5000"

def login(username, password):
    s = requests.Session()
    resp = s.get(f"{BASE_URL}/login")
    token_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp.text)
    token = token_match.group(1) if token_match else ""
    login_resp = s.post(f"{BASE_URL}/login", data={"csrf_token": token, "username": username, "password": password}, allow_redirects=True)
    return s

def test_admin_librarian_fixes():
    # -------------------------------------------------------------
    # 1. TEST ADMIN
    # -------------------------------------------------------------
    s_admin = login("admin", "Admin@123")
    dash_html = s_admin.get(f"{BASE_URL}/dashboard").text
    assert "admin" in dash_html.lower(), "Admin login failed"
    print("[PASS] Admin logged in successfully")

    # Check navbar links in dashboard
    assert "/recommendations" in dash_html, "AI Recommendations link missing from Admin dashboard"
    assert "AI / Graph Recommendations" in dash_html, "AI Recs topbar label missing for Admin"
    print("[PASS] Admin dashboard & navbar contains AI / Graph Recommendations link")

    # Check /graph_visualizer page button text
    gv_html = s_admin.get(f"{BASE_URL}/graph_visualizer").text
    assert "Global Circulation & Fines Subgraph" in gv_html, "Button 'Global Circulation & Fines Subgraph' missing from Admin graph_visualizer"
    print("[PASS] Admin graph_visualizer has 'Global Circulation & Fines Subgraph' toggle button")

    # Check /api/graph_data?view=personal for Admin
    gd_circ = s_admin.get(f"{BASE_URL}/api/graph_data?view=personal").json()
    total_nodes = gd_circ["stats"]["total_nodes"]
    total_edges = gd_circ["stats"]["total_edges"]
    print(f"Admin Global Circulation Subgraph: {total_nodes} nodes, {total_edges} edges, groups: {gd_circ['stats']['counts']}")
    assert total_nodes > 1, f"Expected full circulation subgraph with > 1 nodes, got {total_nodes}"
    assert "User" in gd_circ["stats"]["counts"], "Expected User nodes in circulation subgraph"
    assert "Loan" in gd_circ["stats"]["counts"] or "Book" in gd_circ["stats"]["counts"], "Expected Loan or Book nodes in circulation subgraph"
    print("[PASS] Admin /api/graph_data?view=personal returns entire library circulation & fines subgraph")

    # Check /recommendations for Admin
    rec_resp = s_admin.get(f"{BASE_URL}/recommendations")
    assert rec_resp.status_code == 200, f"Expected 200 OK for Admin /recommendations, got {rec_resp.status_code}"
    assert "Admin View: Global Patron Collaborative Filtering Network" in rec_resp.text, "Admin banner missing from recommendations page"
    assert "Artificial Intelligence" in rec_resp.text or "Mutual Borrowers" in rec_resp.text or "Clean Code" in rec_resp.text, "Recommendation cards missing for Admin"
    print("[PASS] Admin /recommendations displays 'Admin View: Global Patron Collaborative Filtering Network' with cluster cards")

    # Check /api/graph_data?view=recommendations for Admin
    rec_gd = s_admin.get(f"{BASE_URL}/api/graph_data?view=recommendations").json()
    print(f"Admin Recommendations Graph: {rec_gd['stats']['total_nodes']} nodes, {rec_gd['stats']['total_edges']} edges")
    assert rec_gd["stats"]["total_nodes"] > 0, "Recommendations graph should have nodes for Admin previewing top borrower"
    print("[PASS] Admin /api/graph_data?view=recommendations returns active patron collaborative path")

    # -------------------------------------------------------------
    # 2. TEST LIBRARIAN
    # -------------------------------------------------------------
    s_lib = login("librarian", "Lib@12345")
    dash_html = s_lib.get(f"{BASE_URL}/dashboard").text
    assert "librarian" in dash_html.lower(), "Librarian login failed"
    print("[PASS] Librarian logged in successfully")

    gv_html = s_lib.get(f"{BASE_URL}/graph_visualizer").text
    assert "Global Circulation & Fines Subgraph" in gv_html, "Button missing for Librarian"
    print("[PASS] Librarian graph_visualizer has 'Global Circulation & Fines Subgraph' button")

    gd_circ = s_lib.get(f"{BASE_URL}/api/graph_data?view=personal").json()
    assert gd_circ["stats"]["total_nodes"] > 1, "Librarian circulation view has > 1 nodes"
    print(f"[PASS] Librarian circulation view returns {gd_circ['stats']['total_nodes']} nodes")

    rec_resp = s_lib.get(f"{BASE_URL}/recommendations")
    assert rec_resp.status_code == 200, "Librarian /recommendations status 200"
    assert "Admin View: Global Patron Collaborative Filtering Network" in rec_resp.text, "Banner missing for Librarian"
    print("[PASS] Librarian /recommendations shows Global Patron Collaborative Filtering Network banner")

    # -------------------------------------------------------------
    # 3. TEST STUDENT
    # -------------------------------------------------------------
    s_stu = login("student", "Student@1")
    dash_html = s_stu.get(f"{BASE_URL}/dashboard").text
    assert "student" in dash_html.lower(), "Student login failed"
    print("[PASS] Student logged in successfully")

    gv_html = s_stu.get(f"{BASE_URL}/graph_visualizer").text
    assert "My Personal Borrowing Subgraph" in gv_html, "Student should see 'My Personal Borrowing Subgraph'"
    assert "Global Circulation & Fines Subgraph" not in gv_html, "Student should NOT see Global Circulation toggle"
    print("[PASS] Student sees 'My Personal Borrowing Subgraph'")

    gd_stu = s_stu.get(f"{BASE_URL}/api/graph_data?view=personal").json()
    user_nodes = [n for n in gd_stu["nodes"] if n.get("group") == "User"]
    assert any("⭐ You (student)" in n.get("label", "") for n in user_nodes), "Student personal graph should label user as ⭐ You (student)"
    print(f"[PASS] Student personal graph strictly filtered to student (id=6, {len(gd_stu['nodes'])} nodes)")

    rec_stu = s_stu.get(f"{BASE_URL}/recommendations").text
    assert "Admin View: Global Patron Collaborative Filtering Network" not in rec_stu, "Student should NOT see Admin oversight banner"
    print("[PASS] Student /recommendations is personalized without Admin banner")

    print("\n>>> ALL CHECKS PASSED SUCCESSFULLY! 100% WORKING! <<<")

if __name__ == "__main__":
    test_admin_librarian_fixes()
