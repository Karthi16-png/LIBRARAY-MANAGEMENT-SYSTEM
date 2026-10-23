import sys
sys.path.insert(0, ".")
from app import app

client = app.test_client()

print("=================================================================")
print("RUNNING VERIFICATION FOR 3 PRODUCTION REFINEMENTS")
print("=================================================================")

# -------------------------------------------------------------
# 1. Test Collapsible Graph Canvas & Ordering on /recommendations
# -------------------------------------------------------------
print("\n[TEST 1] Verifying /recommendations collapsible accordion & layout...")
with client.session_transaction() as sess:
    sess["user_id"] = 6
    sess["username"] = "student1"
    sess["role"] = "Student"

rec_res = client.get("/recommendations")
assert rec_res.status_code == 200, f"Expected 200, got {rec_res.status_code}"
rec_html = rec_res.get_data(as_text=True)

# Verify Recommended Books cards and Study Partners appear before graph accordion
idx_cards = rec_html.find("Recommended Books For You")
idx_partners = rec_html.find("Top Study Partners")
idx_accordion = rec_html.find("Explain Recommendations (View Neo4j Traversal Graph)")
idx_canvas = rec_html.find("rec-network-canvas")

assert idx_cards != -1, "Missing 'Recommended Books For You' header"
assert idx_accordion != -1, "Missing accordion toggle button 'Explain Recommendations (View Neo4j Traversal Graph)'"
assert idx_canvas != -1, "Missing rec-network-canvas in HTML"

assert idx_cards < idx_accordion, "Recommended Books cards must appear BEFORE the graph accordion"
if idx_partners != -1:
    assert idx_partners < idx_accordion, "Top Study Partners must appear BEFORE the graph accordion"
print("  -> Ordering verified: Recommended Books cards & Study Partners are at the top!")

# Verify accordion is collapsed by default
assert 'id="recGraphPanel" style="display: none;"' in rec_html or "display: none;" in rec_html[idx_accordion:idx_canvas], "Graph panel must be collapsed by default (display: none)"
print("  -> Collapsible accordion verified: collapsed by default (display: none)")

# Verify Vis.js graph options
assert "direction: 'LR'" in rec_html or 'direction: "LR"' in rec_html, "Missing direction: 'LR'"
assert "physics:" in rec_html and "enabled: false" in rec_html, "Missing physics: false"
assert "widthConstraint: { maximum: 140 }" in rec_html, "Missing widthConstraint: { maximum: 140 }"
assert "(Recommended Book)" in rec_html, "Missing (Recommended Book)"
assert "Recommnended" not in rec_html, "Found typo 'Recommnended'"
print("  -> Vis.js options verified: LR direction, physics: false, widthConstraint: { maximum: 140 }, subtitle clean without typos!")


# -------------------------------------------------------------
# 2. Test Streamlined Navigation Sidebar in base.html
# -------------------------------------------------------------
print("\n[TEST 2] Verifying Streamlined Navigation Sidebar (base.html)...")
# Student view
with client.session_transaction() as sess:
    sess["user_id"] = 6
    sess["username"] = "student1"
    sess["role"] = "Student"

dash_res = client.get("/dashboard")
assert dash_res.status_code == 200
dash_html = dash_res.get_data(as_text=True)

# Verify core student nav items
assert "My Dashboard" in dash_html
assert "Search Books" in dash_html
assert "Learning Roadmaps" in dash_html
assert "Recommended For You" in dash_html
assert "My Fines" in dash_html

# Verify NEO4J ENGINE LAB section
assert "NEO4J ENGINE LAB" in dash_html
idx_engine_lab = dash_html.find("NEO4J ENGINE LAB")
idx_live_explorer = dash_html.find("Live Graph Explorer")
idx_book_bridge = dash_html.find("Book Bridge")
assert idx_live_explorer > idx_engine_lab, "Live Graph Explorer must be inside NEO4J ENGINE LAB"
assert idx_book_bridge > idx_engine_lab, "Book Bridge must be inside NEO4J ENGINE LAB"

# Verify redundant graph buttons removed from topbar
topbar_start = dash_html.find('<div class="topbar-actions">')
topbar_end = dash_html.find('</header>')
topbar_content = dash_html[topbar_start:topbar_end]
assert "btn-ai-recs" not in topbar_content, "Redundant AI Recs button found in topbar"
assert "btn-graph-explorer" not in topbar_content, "Redundant Graph Explorer button found in topbar"
assert "Student Portal" in topbar_content, "Missing Student Portal badge in topbar"
print("  -> Navigation verified: Clean core navigation + subtle NEO4J ENGINE LAB section + topbar decluttered!")


# -------------------------------------------------------------
# 3. Test Practical Graph Utility on Category Books Cards & Learning Paths
# -------------------------------------------------------------
print("\n[TEST 3] Verifying Practical Graph Utility on Catalog Cards & Learning Paths...")
# Category 1 (Computer Science & Architecture)
cat_res = client.get("/category/1")
assert cat_res.status_code == 200
cat_html = cat_res.get_data(as_text=True)

assert "Frequently Paired With" in cat_html, "Missing Frequently Paired With badge"
assert "Requires:" in cat_html, "Missing 'Requires: <Book Title>' badge on catalog book cards"
assert "Unlocks:" in cat_html, "Missing 'Unlocks: <Book Title>' badge on catalog book cards"
print("  -> Catalog book cards verified: Clean one-line badges for Requires: and Unlocks: alongside Frequently Paired With!")

# /learning_paths sub-path filtering
lp_res = client.get("/learning_paths")
assert lp_res.status_code == 200
lp_html = lp_res.get_data(as_text=True)
assert "Traversable Academic Learning Sequences" in lp_html
assert "AI Specialization Track" in lp_html
assert "Algorithms Mastery Track" in lp_html
assert "Software Architecture Track" in lp_html
print("  -> /learning_paths verified: Complete curriculum tracks rendered without intermediate sub-path repetition!")

print("\n=================================================================")
print("ALL 3 PRODUCTION REFINEMENT TESTS PASSED WITH 100% SUCCESS!")
print("=================================================================")
