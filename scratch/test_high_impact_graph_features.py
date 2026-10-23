import urllib.request
import urllib.parse
import http.cookiejar
import json
import re

BASE_URL = "http://127.0.0.1:5000"

class TestClient:
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))

    def get(self, path):
        req = urllib.request.Request(f"{BASE_URL}{path}")
        try:
            resp = self.opener.open(req)
            return resp.getcode(), resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8")

    def post(self, path, data):
        data_encoded = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(f"{BASE_URL}{path}", data=data_encoded)
        try:
            resp = self.opener.open(req)
            return resp.getcode(), resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8")


def login(username, password):
    client = TestClient()
    code, html = client.get("/login")
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    csrf = m.group(1) if m else ""
    code, html = client.post("/login", {
        "username": username,
        "password": password,
        "csrf_token": csrf
    })
    return client


def test_high_impact_features():
    print("==================================================================")
    print("TESTING 3 HIGH-IMPACT NEO4J GRAPH FEATURES")
    print("==================================================================")

    student = login("student", "Student@1")
    admin = login("admin", "Admin@123")

    # -------------------------------------------------------------
    # 1. TEST FEATURE 1: Academic Learning Roadmap ([:PREREQUISITE_FOR])
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Academic Learning Roadmap (/learning_paths)...")
    code, html = student.get("/learning_paths")
    assert code == 200, f"Expected 200 for /learning_paths, got {code}"
    assert "Academic Learning Roadmaps" in html, "Missing Title in learning_paths.html"
    assert "vis-network.min.js" in html, "Missing Vis.js in learning_paths.html"
    assert "roadmap-canvas" in html, "Missing canvas element in learning_paths.html"
    assert "UD" in html or "Hierarchical" in html, "Missing hierarchical layout in learning_paths.html"
    assert "Curriculum Volumes" in html, "Missing Curriculum Volumes KPI"
    assert "Learning Pathways" in html, "Missing Learning Pathways KPI"
    print("  -> /learning_paths rendered successfully (HTTP 200)")

    # Test /api/learning_paths
    code, raw_json = student.get("/api/learning_paths")
    assert code == 200, f"Expected 200 for /api/learning_paths, got {code}"
    data = json.loads(raw_json)
    assert data["status"] == "success", f"Expected success status, got {data.get('status')}"
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    assert len(nodes) >= 7, f"Expected at least 7 roadmap nodes, got {len(nodes)}"
    assert len(edges) >= 7, f"Expected at least 7 prerequisite edges, got {len(edges)}"
    print(f"  -> /api/learning_paths verified: {len(nodes)} nodes, {len(edges)} prerequisite relationships")

    # Verify admin can access roadmap
    a_code, _ = admin.get("/learning_paths")
    assert a_code == 200, "Admin should be able to view /learning_paths"
    print("  -> Admin access to /learning_paths verified")

    # -------------------------------------------------------------
    # 2. TEST RECOMMENDATIONS (Jaccard and Explanation Box Removed)
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Recommendations (verifying clean UI without Jaccard/Explanation)...")
    code, html = student.get("/recommendations")
    assert code == 200, f"Expected 200 for /recommendations, got {code}"
    assert "Jaccard" not in html, "Jaccard should not be present in recommendations"
    assert "How the Neo4j Recommendation Algorithm Traverses the Graph" not in html, "Explanation box should be removed"
    assert "Multi-Hop Recommendation Path" in html, "Graph canvas header should be present"
    print("  -> Student view: Clean recommendations UI verified (Jaccard and explanation box removed)")

    # Verify admin view
    code, a_html = admin.get("/recommendations")
    assert code == 200, f"Expected 200 for admin /recommendations, got {code}"
    assert "Jaccard" not in a_html, "Jaccard should not be present in admin recommendations"
    assert "How the Neo4j Recommendation Algorithm Traverses the Graph" not in a_html, "Explanation box should be removed"
    print("  -> Admin view: Verified clean recommendations without Jaccard")

    # -------------------------------------------------------------
    # 3. TEST FEATURE 3: Frequently Borrowed Together Badge (/category/<id>)
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Frequently Borrowed Together Badge (/category/1)...")
    code, cat_html = student.get("/category/1")
    assert code == 200, f"Expected 200 for /category/1, got {code}"
    assert "Frequently Paired With:" in cat_html, "Missing 'Frequently Paired With' badge in Category 1"
    assert "frequently-paired-badge" in cat_html, "Missing CSS class frequently-paired-badge"
    print("  -> Category 1: 'Frequently Paired With' badge verified on co-borrowed textbooks")

    code, cat10_html = student.get("/category/10")
    assert code == 200, f"Expected 200 for /category/10, got {code}"
    assert "Frequently Paired With:" in cat10_html, "Missing 'Frequently Paired With' badge in Category 10"
    print("  -> Category 10 (Data Architecture & Databases): 'Frequently Paired With' badge verified on co-borrowed textbooks")

    # -------------------------------------------------------------
    # 4. TEST NAVIGATION LINKS
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Navigation Links in base.html...")
    assert "Learning Roadmaps" in html, "Missing Learning Roadmaps in sidebar"
    assert "Roadmaps" in html, "Missing Roadmaps button in topbar"
    print("  -> Learning Roadmaps links present in sidebar and topbar")

    print("\n==================================================================")
    print(">>> ALL 3 HIGH-IMPACT GRAPH FEATURES VERIFIED SUCCESSFULLY! <<<")
    print("==================================================================")


if __name__ == "__main__":
    test_high_impact_features()
