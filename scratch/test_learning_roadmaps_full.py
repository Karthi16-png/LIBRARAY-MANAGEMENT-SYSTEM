import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app

def run_learning_roadmaps_verification():
    print("=== STARTING FULL LEARNING ROADMAPS VERIFICATION ===")
    client = app.app.test_client()

    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Admin User"
        sess["role"] = "Admin"
        sess["email"] = "admin@vit.ac.in"

    # Test 1: GET /learning_paths
    resp = client.get("/learning_paths")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    html = resp.get_data(as_text=True)
    print("[PASS] GET /learning_paths returned HTTP 200")

    # Assert critical UI elements and JavaScript data are present in HTML
    assert "Academic Learning Roadmaps &amp; Prerequisite Hierarchy" in html or "Academic Learning Roadmaps" in html
    assert "roadmap-canvas" in html
    assert "rawNodes" in html
    assert "rawEdges" in html
    assert "filterTrack('software_ai'" in html
    assert "filterTrack('data'" in html
    assert "filterTrack('systems'" in html
    assert "View in Category / Borrow" in html
    print("[PASS] HTML contains updated filter tracks, canvas, and deep-link markup")

    # Test 2: GET /api/learning_paths
    api_resp = client.get("/api/learning_paths")
    assert api_resp.status_code == 200, f"API expected 200, got {api_resp.status_code}"
    data = api_resp.get_json()
    assert data.get("status") == "success", f"API status was not success: {data}"
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    print(f"[PASS] API returned {len(nodes)} nodes and {len(edges)} edges")
    assert len(nodes) == 9, f"Expected 9 nodes, got {len(nodes)}"
    assert len(edges) == 7, f"Expected 7 edges, got {len(edges)}"

    # Check node properties
    for node in nodes:
        assert "book_id" in node
        assert "title" in node
        assert "category_id" in node
        assert node["category_id"] is not None and node["category_id"] > 0
        assert "category_name" in node
        assert "authors" in node
        assert "available_copies" in node
        assert "total_copies" in node
    print("[PASS] All 9 API nodes contain complete category, stock, and author metadata")

    # Check edges
    edge_pairs = set((e["source"], e["target"]) for e in edges)
    expected_pairs = {
        (2, 3), # Clean Code -> CLRS
        (3, 4), # CLRS -> AI
        (3, 9), # CLRS -> TAOCP
        (2, 8), # Clean Code -> DDD
        (6, 7), # OS -> Networks
        (7, 1), # Networks -> DDIA
        (5, 1)  # DB Concepts -> DDIA
    }
    assert edge_pairs == expected_pairs, f"Edge mismatch! Found {edge_pairs}, expected {expected_pairs}"
    print(f"[PASS] All 7 canonical prerequisite edges perfectly verified: {edge_pairs}")

    # Test 3: Verify track classification
    tracks = set(e["track"] for e in edges)
    print(f"[PASS] Active curriculum tracks: {tracks}")
    assert "Software Engineering" in tracks
    assert "Artificial Intelligence" in tracks
    assert "Theoretical CS" in tracks
    assert "Systems & Infrastructure" in tracks
    assert "Data Engineering" in tracks

    # Test 4: Verify student completion status rendering with student session
    with client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["user_name"] = "Alice Student"
        sess["role"] = "Student"
        sess["email"] = "alice@vit.ac.in"

    student_resp = client.get("/learning_paths")
    assert student_resp.status_code == 200
    student_html = student_resp.get_data(as_text=True)
    print("[PASS] Student session access to /learning_paths verified (HTTP 200)")

    print("\n=== ALL LEARNING ROADMAPS TESTS PASSED (100%) ===")

if __name__ == "__main__":
    run_learning_roadmaps_verification()
