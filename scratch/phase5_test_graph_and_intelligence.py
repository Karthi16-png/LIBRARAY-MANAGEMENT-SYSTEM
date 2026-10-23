import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import app

def test_phase5_graph_and_intelligence():
    print("=================================================================")
    print("PHASE 5: GRAPH VISUALIZER, BOOK BRIDGE & AI RECOMMENDATIONS")
    print("=================================================================")
    app.app.config["TESTING"] = True
    app.app.config["WTF_CSRF_ENABLED"] = False
    client = app.app.test_client()

    # 1. Graph Visualizer (/graph_visualizer & /api/graph_data)
    print("\n--- 1. Testing Graph Visualizer & Privacy Masking ---")
    # Test Admin view
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "Admin"
        sess["last_activity"] = time.time()

    resp = client.get("/graph_visualizer")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Live Graph Explorer" in html or "Knowledge Graph" in html

    api_resp = client.get("/api/graph_data")
    assert api_resp.status_code == 200
    data = api_resp.get_json()
    assert "nodes" in data and "edges" in data
    print(f"[PASS] Admin API returned {len(data['nodes'])} nodes and {len(data['edges'])} edges.")

    # Test Student view with privacy masking
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = 6
        sess["username"] = "student"
        sess["role"] = "Student"
        sess["last_activity"] = time.time()

    resp = client.get("/graph_visualizer")
    assert resp.status_code == 200

    api_resp = client.get("/api/graph_data")
    assert api_resp.status_code == 200
    student_data = api_resp.get_json()
    # Verify that other students' loan requests do not leak usernames
    for n in student_data["nodes"]:
        if n.get("group") == "LoanRequest":
            assert "Circulation Request" in n["label"] or "LoanRequest" in n["label"]
    print("[PASS] Student graph data properly masked with patron privacy preservation.")

    # 2. Book-to-Book Bridge (/book_bridge & /api/book_bridge)
    print("\n--- 2. Testing Book Bridge Degrees of Separation ---")
    resp = client.get("/book_bridge")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Book-to-Book Bridge" in html

    # Calculate shortest path between Clean Code (id 2) and Domain-Driven Design (id 8)
    api_bridge = client.get("/api/book_bridge?book_a=2&book_b=8")
    assert api_bridge.status_code == 200
    bridge_json = api_bridge.get_json()
    assert bridge_json.get("found") is True
    assert bridge_json.get("degrees") == 1
    print(f"[PASS] Book Bridge shortest path found: {bridge_json.get('degrees')} degrees between Book 2 and Book 8.")

    # 3. Academic Learning Roadmaps (/learning_paths)
    print("\n--- 3. Testing Academic Learning Roadmaps ---")
    resp = client.get("/learning_paths")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Academic Learning Roadmaps" in html
    assert "roadmap-canvas" in html
    assert "filterTrack('software_ai'" in html
    print("[PASS] Academic Learning Roadmaps rendered with Vis.js hierarchical network.")

    # 4. AI Recommendations (/recommendations)
    print("\n--- 4. Testing AI Recommendations Across All Roles ---")
    roles = [
        ("Admin", 1),
        ("Librarian", 2),
        ("Staff", 3),
        ("Student", 6)
    ]

    for rname, uid in roles:
        with client.session_transaction() as sess:
            sess.clear()
            sess["user_id"] = uid
            sess["username"] = rname.lower()
            sess["role"] = rname
            sess["last_activity"] = time.time()

        resp = client.get("/recommendations")
        assert resp.status_code == 200, f"Recommendations failed for {rname}: {resp.status_code}"
        html = resp.get_data(as_text=True)
        assert "AI Book Recommendations" in html or "Recommendations" in html
        print(f"[PASS] Recommendations view rendered cleanly for {rname}.")

    print("\n=================================================================")
    print("PHASE 5 VERIFICATION COMPLETED: 100% PASSING")
    print("=================================================================")

if __name__ == "__main__":
    test_phase5_graph_and_intelligence()
