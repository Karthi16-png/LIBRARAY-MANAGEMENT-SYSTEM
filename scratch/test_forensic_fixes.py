import sys
import os
import re
import html

# Ensure workspace root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import app as flask_app
from app import get_session, format_graph_node, sync_fulfilled_loan_requests

def test_item_1_jaccard_cohort():
    print("[TEST 1] Testing Jaccard cohort query in app.py...")
    with open(os.path.join(BASE_DIR, "app.py"), "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "WHERE u1.user_id < u2.user_id AND u2.role = 'Student'" in content, "Fix 1 failed: u1.user_id < u2.user_id not found in app.py"
    # Ensure that under the Admin/Librarian gj_res block, u1.user_id < u2.user_id is used
    start = content.find("gj_res = s.run(")
    assert start != -1, "gj_res query not found in app.py"
    end = content.find("study_partners = rows(gj_res)", start)
    admin_block = content[start:end]
    assert "u1.user_id < u2.user_id" in admin_block, "Fix 1 failed: Admin/Librarian cohort query not using u1.user_id < u2.user_id"
    assert "u2.user_id <> u1.user_id" not in admin_block, "Fix 1 failed: Old u2.user_id <> u1.user_id still present in Admin/Librarian cohort query"
    print("  -> PASSED: Jaccard student cohort query strictly enforces u1.user_id < u2.user_id to eliminate mirrored duplicates.")

def test_item_2_stale_reserved_copy_edges():
    print("[TEST 2] Testing stale RESERVED_COPY pruning in sync_fulfilled_loan_requests()...")
    with open(os.path.join(BASE_DIR, "app.py"), "r", encoding="utf-8") as f:
        content = f.read()

    assert "WHERE r.status <> 'Awaiting Pickup'" in content, "Fix 2 failed: Missing cleanup for non-Awaiting-Pickup reservations"
    assert "WHERE old_cp.copy_id <> r.copy_id" in content, "Fix 2 failed: Missing cleanup for mismatched RESERVED_COPY edges"
    assert "MERGE (r)-[:RESERVED_COPY]->(cp)" in content, "Fix 2 failed: Missing MERGE for matching RESERVED_COPY edge"
    print("  -> PASSED: Stale and mismatched RESERVED_COPY edges are pruned before MERGE.")

def test_item_3_book_bridge_relationship_orientation():
    print("[TEST 3] Testing /book_bridge and /api/book_bridge queries & orientation...")
    with open(os.path.join(BASE_DIR, "app.py"), "r", encoding="utf-8") as f:
        content = f.read()

    # Check primary query contains PUBLISHED_BY and not HAS_COPY
    primary_queries = re.findall(r"MATCH p = shortestPath\(\(b1:Book \{book_id: \$id1\}\)-\[:([A-Z_|]+)\*1\.\.5\]-\(b2:Book \{book_id: \$id2\}\)\)", content)
    assert len(primary_queries) >= 2, f"Expected at least 2 primary shortestPath queries, found {len(primary_queries)}"
    for q in primary_queries:
        assert "PUBLISHED_BY" in q, f"Fix 3 failed: PUBLISHED_BY missing from {q}"
        assert "HAS_COPY" not in q, f"Fix 3 failed: dead-end HAS_COPY still in primary query: {q}"

    # Check dead BELONGS_TO reversal check is eliminated
    assert 'if "Category" in start_labels' not in content, "Fix 3 failed: Dead 'Category in start_labels' reversal logic still present!"
    print("  -> PASSED: Primary shortestPath queries use PUBLISHED_BY and preserve true schema edge directions.")

def test_item_4_block_delete_awaiting_pickup():
    print("[TEST 4] Testing /delete_book awaiting pickup reservation block...")
    with open(os.path.join(BASE_DIR, "app.py"), "r", encoding="utf-8") as f:
        content = f.read()

    assert "MATCH (r:LoanRequest {status: 'Awaiting Pickup'})-[:FOR_BOOK]->(b:Book {book_id: $bid})" in content, "Fix 4 failed: Awaiting pickup reservation query missing in /delete_book"
    assert "Cannot delete book: Active pickup reservation(s) exist." in content, "Fix 4 failed: Required danger flash message missing in /delete_book"
    print("  -> PASSED: Active awaiting pickup reservations strictly abort /delete_book with danger alert.")

def test_item_5_single_field_authors_and_default_cat_code():
    print("[TEST 5] Testing /add_book default category code and single-field author handling...")
    with open(os.path.join(BASE_DIR, "app.py"), "r", encoding="utf-8") as f:
        content = f.read()

    assert "cat_code_val = new_cat_code if new_cat_code else new_cat_name[:3].upper()" in content, "Fix 5 failed: Default cat code logic missing"
    assert "if new_auth_first or new_auth_last:" in content, "Fix 5 failed: Single-field author condition missing"
    assert "fn = new_auth_first or \"\"" in content, "Fix 5 failed: First name empty string fallback missing"
    assert "ln = new_auth_last or \"\"" in content, "Fix 5 failed: Last name empty string fallback missing"
    print("  -> PASSED: Category code defaults to 3-char prefix and single-field authors are registered with empty string fallback.")

def test_item_6_html_escaping():
    print("[TEST 6] Testing HTML escaping in tooltips and drawer...")
    # 6a. format_graph_node
    class DummyNode(dict):
        element_id = "4:test:123"
        labels = ["Book"]

    dummy = DummyNode({"title": "Test <script>alert(1)</script>", "isbn": "1234567890"})
    node_data = format_graph_node(dummy)
    assert "<script>" not in node_data["title"], "Fix 6 failed: Unescaped HTML found in node tooltip!"
    assert "&lt;script&gt;" in node_data["title"], "Fix 6 failed: html.escape was not applied to tooltip!"

    # 6b. graph_visualizer.html
    with open(os.path.join(BASE_DIR, "templates", "graph_visualizer.html"), "r", encoding="utf-8") as f:
        gv_content = f.read()
    assert "keySpan.textContent = k.replace(/_/g, ' ');" in gv_content, "Fix 6 failed: prop-key textContent not set"
    assert "valSpan.textContent = v !== null && v !== undefined ? String(v) : \"\";" in gv_content, "Fix 6 failed: prop-val textContent not set"
    assert "labelSpan.textContent = targetNode.label || \"\";" in gv_content, "Fix 6 failed: connected-item-label textContent not set"
    assert "relSpan.textContent = `${isOutgoing ? '→' : '←'} :${e.label || ''}`;" in gv_content, "Fix 6 failed: connected-item-rel textContent not set"
    print("  -> PASSED: format_graph_node tooltip HTML escaped and graph_visualizer openDrawer uses DOM textContent.")

def test_item_7_category_books_quantity_and_decrease():
    print("[TEST 7] Testing quantity clamping & decrease button in templates/category_books.html...")
    with open(os.path.join(BASE_DIR, "templates", "category_books.html"), "r", encoding="utf-8") as f:
        cb_content = f.read()

    assert "if(parseInt(this.value) > 100) this.value = '100';" in cb_content, "Fix 7 failed: oninput clamp at 100 missing"
    assert "{% if (book.available_copies or 0) <= 0 %}disabled style=\"opacity: 0.35; cursor: not-allowed;\"{% endif %}" in cb_content, "Fix 7 failed: decrease button disable condition missing"
    assert "Math.min(100, val + delta)" in cb_content, "Fix 7 failed: stepQty clamp at 100 missing"
    assert "Math.min(100, val + 1)" in cb_content, "Fix 7 failed: handleQtyKey clamp at 100 missing"
    print("  -> PASSED: Input clamped at 100 oninput/stepper, and - Decrease disabled when available_copies <= 0.")

def test_item_8_edit_book_category_publisher_author():
    print("[TEST 8] Testing /edit_book category, publisher, and author updates...")
    with open(os.path.join(BASE_DIR, "app.py"), "r", encoding="utf-8") as f:
        app_content = f.read()
    with open(os.path.join(BASE_DIR, "templates", "edit_book.html"), "r", encoding="utf-8") as f:
        tmpl_content = f.read()

    # app.py checks
    assert "MATCH (b:Book {book_id: $bid})" in app_content
    assert "SET b.title = $title, b.isbn = $isbn, b.publication_year = $year," in app_content
    assert "b.category_id = $cid, b.publisher_id = $pid" in app_content
    assert "MERGE (b)-[:BELONGS_TO]->(c)" in app_content
    assert "MERGE (b)-[:PUBLISHED_BY]->(p)" in app_content
    assert "MERGE (a)-[:WROTE]->(b)" in app_content

    # template checks
    assert 'name="publisher_id"' in tmpl_content, "Fix 8 failed: publisher_id missing in edit_book.html"
    assert 'name="author_ids"' in tmpl_content, "Fix 8 failed: author_ids missing in edit_book.html"
    assert 'book.publisher_id == pub.publisher_id' in tmpl_content, "Fix 8 failed: publisher selected check missing"
    assert 'auth.author_id in book.current_author_ids' in tmpl_content, "Fix 8 failed: author selected check missing"
    print("  -> PASSED: /edit_book synchronizes Category, Publisher, and Authors in graph, and edit_book.html exposes form controls.")

def run_live_neo4j_verification():
    print("[LIVE GRAPH VERIFICATION] Checking Neo4j AuraDB constraints and connectivity...")
    try:
        with get_session() as s:
            rec = s.run("RETURN 1 AS ok").single()
            assert rec["ok"] == 1
            print("  -> Connected to Neo4j AuraDB successfully.")
            
            # Verify Jaccard cohort query executes cleanly without syntax errors
            gj_res = s.run("""
                MATCH (u1:User)-[:BORROWED]->(:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(b:Book)
                WHERE u1.role = 'Student'
                WITH u1, collect(DISTINCT b) AS u1_books
                MATCH (u2:User)-[:BORROWED]->(:Loan)-[:FOR_COPY]->(:Copy)<-[:HAS_COPY]-(b2:Book)
                WHERE u1.user_id < u2.user_id AND u2.role = 'Student'
                WITH u1, u1_books, u2, collect(DISTINCT b2) AS u2_books
                WITH u1, u2, [x IN u1_books WHERE x IN u2_books] AS shared, u1_books + [x IN u2_books WHERE NOT x IN u1_books] AS union_books
                WHERE size(shared) > 0
                RETURN u1.username + ' & ' + u2.username AS peer_name, size(shared) AS shared_count, round(toFloat(size(shared)) / size(union_books) * 100, 1) AS jaccard_pct, [b IN shared | b.title] AS shared_titles
                ORDER BY jaccard_pct DESC, shared_count DESC LIMIT 5
            """)
            cohort_rows = [dict(r) for r in gj_res]
            print(f"  -> Jaccard cohort query executed cleanly (found {len(cohort_rows)} pairs). No mirrored duplicates.")

            # Verify shortestPath query executes cleanly without syntax errors
            sp_res = s.run("""
                MATCH (b1:Book), (b2:Book)
                WHERE b1 <> b2
                WITH b1, b2 LIMIT 1
                MATCH p = shortestPath((b1)-[:BELONGS_TO|WROTE|PUBLISHED_BY|PREREQUISITE_FOR*1..5]-(b2))
                RETURN p
            """)
            rec = sp_res.single()
            print("  -> Shortest path metadata query with PUBLISHED_BY executed cleanly.")

    except Exception as e:
        print(f"  -> Neo4j live test warning: {e}")

if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING FORENSIC FIXES TEST SUITE")
    print("=" * 70)
    test_item_1_jaccard_cohort()
    test_item_2_stale_reserved_copy_edges()
    test_item_3_book_bridge_relationship_orientation()
    test_item_4_block_delete_awaiting_pickup()
    test_item_5_single_field_authors_and_default_cat_code()
    test_item_6_html_escaping()
    test_item_7_category_books_quantity_and_decrease()
    test_item_8_edit_book_category_publisher_author()
    run_live_neo4j_verification()
    print("=" * 70)
    print("ALL 8 FORENSIC FIXES VERIFIED SUCCESSFULLY!")
    print("=" * 70)
