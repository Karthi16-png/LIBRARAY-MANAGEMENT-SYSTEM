import sys
import os
import json
import re

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app, get_session, format_bridge_node

def test_bridge_formatting():
    print("--- 1. Testing format_bridge_node ---")
    class DummyNode(dict):
        def __init__(self, labels, props, element_id):
            super().__init__(props)
            self.labels = set(labels)
            self.element_id = element_id

    b1 = DummyNode(["Book"], {"book_id": 1, "title": "Designing Data-Intensive Applications"}, "b1")
    b_inter = DummyNode(["Book"], {"book_id": 7, "title": "Computer Networks (5th Ed)"}, "b7")
    cat = DummyNode(["Category"], {"category_id": 1, "name": "Computer Science & AI"}, "c1")
    b2 = DummyNode(["Book"], {"book_id": 2, "title": "Clean Code"}, "b2")

    # Start Book
    f0, s0 = format_bridge_node(b1, 0, 4, "Admin")
    assert f0["group"] == "StartBook", f"Expected StartBook, got {f0['group']}"
    assert "Origin" in f0["label"], f"Expected Origin label, got {f0['label']}"
    print("[PASS] Origin book correctly formatted as StartBook")

    # Intermediate Book
    f1, s1 = format_bridge_node(b_inter, 1, 4, "Admin")
    assert f1["group"] == "IntermediateBook", f"Expected IntermediateBook, got {f1['group']}"
    assert "📖" in f1["label"], f"Expected book icon, got {f1['label']}"
    assert s1["type"] == "Intermediate Book", f"Expected type 'Intermediate Book', got {s1['type']}"
    print(f"[PASS] Intermediate book formatted as group='{f1['group']}', step_type='{s1['type']}'")

    # Category
    f2, s2 = format_bridge_node(cat, 2, 4, "Admin")
    assert f2["group"] == "Category", f"Expected Category, got {f2['group']}"
    assert s2["type"] == "Category", f"Expected Category, got {s2['type']}"
    print("[PASS] Category node correctly formatted")

    # Target Book
    f3, s3 = format_bridge_node(b2, 3, 4, "Admin")
    assert f3["group"] == "TargetBook", f"Expected TargetBook, got {f3['group']}"
    assert "Destination" in f3["label"], f"Expected Destination label, got {f3['label']}"
    print("[PASS] Target book correctly formatted as TargetBook")

def test_routes_and_edge_directions():
    print("\n--- 2. Testing /book_bridge and /api/book_bridge routes ---")
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "Admin"
        sess["logged_in"] = True

    # 1. Test /book_bridge page
    resp = client.get("/book_bridge?book_a=1&book_b=2")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    html = resp.get_data(as_text=True)

    # Check legend
    assert "📖 Intermediate Book" in html, "Legend must contain '📖 Intermediate Book'"
    assert "#64748B" in html or "#64748b" in html, "Legend must use Slate Gray #64748B"
    print("[PASS] HTML contains '📖 Intermediate Book' in legend with #64748B")

    # Check timeline class
    assert "intermediate" in html, "HTML must contain 'intermediate' step class"
    assert "Intermediate Book" in html, "HTML narrative must contain 'Intermediate Book'"
    print("[PASS] HTML contains intermediate step class and narrative badge")

    # Extract JSON embedded in template
    match = re.search(r'<script id="bridge-graph-data" type="application/json">\s*({.*?})\s*</script>', html, re.DOTALL)
    assert match, "Could not find bridge-graph-data JSON in HTML"
    data = json.loads(match.group(1))

    # Verify intermediate book in embedded nodes
    inter_nodes = [n for n in data["nodes"] if n.get("group") == "IntermediateBook"]
    assert len(inter_nodes) >= 1, f"Expected at least 1 IntermediateBook in embedded data, got {len(inter_nodes)}"
    print(f"[PASS] Embedded JSON nodes contain {len(inter_nodes)} IntermediateBook node(s)")

    # Verify edge directions in embedded edges
    cat_node_ids = {n["id"] for n in data["nodes"] if n.get("group") == "Category"}
    book_node_ids = {n["id"] for n in data["nodes"] if n.get("group") in ["StartBook", "TargetBook", "IntermediateBook", "Book"]}

    for e in data["edges"]:
        if "BELONGS_TO" in e.get("label", ""):
            # from must be Book, to must be Category
            assert e["from"] in book_node_ids, f"BELONGS_TO from={e['from']} should be a Book node"
            assert e["to"] in cat_node_ids, f"BELONGS_TO to={e['to']} should be a Category node"
            print(f"[PASS] BELONGS_TO edge correctly points from Book ({e['from']}) to Category ({e['to']})")

    # 2. Test /api/book_bridge endpoint
    api_resp = client.get("/api/book_bridge?book_a=1&book_b=2")
    assert api_resp.status_code == 200, f"Expected 200, got {api_resp.status_code}"
    api_data = api_resp.get_json()
    assert api_data.get("found") is True, "Expected found: True"
    assert any(n.get("group") == "IntermediateBook" for n in api_data.get("nodes", [])), "API response nodes must include IntermediateBook"
    assert any(s.get("type") == "Intermediate Book" for s in api_data.get("steps", [])), "API response steps must include 'Intermediate Book'"

    api_cat_ids = {n["id"] for n in api_data["nodes"] if n.get("group") == "Category"}
    api_book_ids = {n["id"] for n in api_data["nodes"] if n.get("group") in ["StartBook", "TargetBook", "IntermediateBook", "Book"]}

    for e in api_data.get("edges", []):
        if "BELONGS_TO" in e.get("label", ""):
            assert e["from"] in api_book_ids, f"API BELONGS_TO from={e['from']} should be a Book node"
            assert e["to"] in api_cat_ids, f"API BELONGS_TO to={e['to']} should be a Category node"
            print(f"[PASS] API BELONGS_TO edge points from Book ({e['from']}) to Category ({e['to']})")

def test_template_contents():
    print("\n--- 3. Testing templates/book_bridge.html contents ---")
    tmpl_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates", "book_bridge.html"))
    with open(tmpl_path, "r", encoding="utf-8") as f:
        tmpl = f.read()

    assert "IntermediateBook:" in tmpl, "Vis.js options.groups must define IntermediateBook"
    assert "#64748B" in tmpl or "#64748b" in tmpl, "Vis.js options.groups must include Slate Gray #64748B"
    assert ".step-item.intermediate" in tmpl, "CSS must define .step-item.intermediate"
    assert "📖 Intermediate Book" in tmpl, "Canvas footer legend must define 📖 Intermediate Book"
    assert "BELONGS_TO" in tmpl and "e.from = e.to" in tmpl, "renderBridgeNetwork must sanitize inverted BELONGS_TO edges"
    print("[PASS] Template includes IntermediateBook group, CSS styling, canvas legend, and edge direction sanitizer")

if __name__ == "__main__":
    test_bridge_formatting()
    test_routes_and_edge_directions()
    test_template_contents()
    print("\nALL BOOK BRIDGE VERIFICATIONS PASSED SUCCESSFULLY!")
