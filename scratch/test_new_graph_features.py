import requests
from scratch.test_admin_librarian_fixes import login, BASE_URL

def test_new_features():
    print("==================================================")
    print("TESTING ADVANCED GRAPH FEATURES (DA-3 ASSESSMENT)")
    print("==================================================")

    # -------------------------------------------------------------
    # 1. TEST /book_bridge (HTML & Dynamic API)
    # -------------------------------------------------------------
    s_stu = login("student", "Student@1")
    print("\n[TEST 1] Testing /book_bridge route as Student:")
    resp_bridge = s_stu.get(f"{BASE_URL}/book_bridge")
    assert resp_bridge.status_code == 200, f"Expected 200 for /book_bridge, got {resp_bridge.status_code}"
    assert "The \"Book-to-Book Bridge\" Shortest Path Traversal" in resp_bridge.text, "Title missing in book_bridge.html"
    assert "vis-network.min.js" in resp_bridge.text, "Vis.js script missing in book_bridge.html"
    assert "Degrees" in resp_bridge.text, "Degrees metric missing in book_bridge.html"
    assert "bridge-network-canvas" in resp_bridge.text, "Canvas element missing"
    print("  -> /book_bridge rendered successfully (HTTP 200)")

    # Test /book_bridge with specific books
    resp_custom = s_stu.get(f"{BASE_URL}/book_bridge?book_a=1&book_b=5")
    assert resp_custom.status_code == 200
    assert "2 Degrees" in resp_custom.text, "Expected 2 Degrees for Book 1 & 5 bridge"
    print("  -> Verified 2-degree bridge between Book 1 and Book 5 (Database Systems category bridge)")

    resp_cross = s_stu.get(f"{BASE_URL}/book_bridge?book_a=1&book_b=4")
    assert resp_cross.status_code == 200
    assert "6 Degrees" in resp_cross.text, "Expected 6 Degrees for Book 1 & 4 bridge"
    print("  -> Verified 6-degree reader circulation bridge between Book 1 and Book 4")

    # Test /api/book_bridge JSON endpoint
    api_resp = s_stu.get(f"{BASE_URL}/api/book_bridge?book_a=1&book_b=5").json()
    assert api_resp["found"] is True, "API shortest path should be found"
    assert api_resp["degrees"] == 2, f"Expected 2 degrees, got {api_resp['degrees']}"
    assert len(api_resp["nodes"]) == 3, f"Expected 3 nodes (Book, Cat, Book), got {len(api_resp['nodes'])}"
    assert len(api_resp["edges"]) == 2, f"Expected 2 edges, got {len(api_resp['edges'])}"
    print(f"  -> /api/book_bridge JSON returned {len(api_resp['nodes'])} nodes and {len(api_resp['edges'])} edges")

    # -------------------------------------------------------------
    # 2. TEST /library_analytics (Staff, Librarian, Admin access)
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing /library_analytics route:")
    # Student should be blocked
    resp_stu_analytics = s_stu.get(f"{BASE_URL}/library_analytics", allow_redirects=False)
    assert resp_stu_analytics.status_code == 302, f"Student should be redirected, got {resp_stu_analytics.status_code}"
    print("  -> Student correctly blocked from /library_analytics (HTTP 302 redirect)")

    # Staff should have access
    s_stf = login("staff", "Staff@123")
    resp_stf_analytics = s_stf.get(f"{BASE_URL}/library_analytics")
    assert resp_stf_analytics.status_code == 200, f"Staff should have access to /library_analytics, got {resp_stf_analytics.status_code}"
    assert "Author Centrality & Graph Influencer Analytics" in resp_stf_analytics.text
    assert "Top Authors by Graph Degree Centrality" in resp_stf_analytics.text
    assert "Most Connected Books (Degree Centrality)" in resp_stf_analytics.text
    assert "Andrew Tanenbaum" in resp_stf_analytics.text or "Peter Norvig" in resp_stf_analytics.text
    print("  -> Staff access confirmed: displays Author Centrality and Influential Books tables")

    # Admin should have access
    s_adm = login("admin", "Admin@123")
    resp_adm_analytics = s_adm.get(f"{BASE_URL}/library_analytics")
    assert resp_adm_analytics.status_code == 200
    assert "Knowledge Nodes" in resp_adm_analytics.text
    assert "Average Degree" in resp_adm_analytics.text
    print("  -> Admin access confirmed: displays Executive graph metrics and Category Density")

    # Librarian should have access
    s_lib = login("librarian", "Lib@12345")
    resp_lib_analytics = s_lib.get(f"{BASE_URL}/library_analytics")
    assert resp_lib_analytics.status_code == 200
    print("  -> Librarian access confirmed")

    # -------------------------------------------------------------
    # 3. TEST NAVBAR & SIDEBAR LINKS
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Navigation Links in base.html:")
    dash_adm = s_adm.get(f"{BASE_URL}/dashboard").text
    assert "/book_bridge" in dash_adm, "Book Bridge link missing in Admin navigation"
    assert "/library_analytics" in dash_adm, "Library Analytics link missing in Admin navigation"
    print("  -> Admin base navigation contains Book Bridge and Library Analytics links")

    dash_stu = s_stu.get(f"{BASE_URL}/dashboard").text
    assert "/book_bridge" in dash_stu, "Book Bridge link missing in Student navigation"
    assert "/library_analytics" not in dash_stu, "Library Analytics link should not be visible to Student in navigation"
    print("  -> Student base navigation includes Book Bridge and hides Centrality Analytics")

    print("\n>>> ALL ADVANCED GRAPH FEATURE TESTS PASSED 100%! <<<")

if __name__ == "__main__":
    test_new_features()
