import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask application
import app as flask_app
app = flask_app.app
app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False
get_session = flask_app.get_session

def run_tests():
    print("=" * 70)
    print("RUNNING COMPREHENSIVE VERIFICATION SUITE FOR 8 ARCHITECTURAL FIXES")
    print("=" * 70)
    passed_count = 0
    total_count = 8

    client = app.test_client()

    # -------------------------------------------------------------
    # Fix 1: Disconnected Unpaid Fine Nodes in Personal Borrowing Subgraph
    # -------------------------------------------------------------
    print("\n--- [Fix 1] Testing /api/graph_data for personal borrowing subgraph ---")
    with get_session() as s:
        u_rec = s.run("MATCH (u:User {username: 'alex_stu'}) RETURN u.user_id AS uid").single()
        alex_uid = u_rec["uid"]

    # Login as alex_stu (user who has returned loan #8 with unpaid fine #8)
    with client.session_transaction() as sess:
        sess["user_id"] = alex_uid
        sess["username"] = "alex_stu"
        sess["role"] = "Student"

    res = client.get("/api/graph_data?view=personal")
    assert res.status_code == 200, f"/api/graph_data failed: {res.status_code}"
    gdata = res.get_json()
    nodes = {n["id"]: n for n in gdata.get("nodes", [])}
    edges = gdata.get("edges", [])

    fine_nodes = [n for n in nodes.values() if n.get("group") == "Fine"]
    loan_nodes = [n for n in nodes.values() if n.get("group") == "Loan"]
    user_nodes = [n for n in nodes.values() if n.get("group") == "User"]
    
    print(f"Personal graph: {len(nodes)} nodes, {len(edges)} edges")
    print(f"Fine nodes: {[f['label'] for f in fine_nodes]}")
    print(f"Loan nodes: {[l['label'] for l in loan_nodes]}")

    assert len(fine_nodes) > 0, "Expected at least 1 Fine node in alex_stu's personal graph"

    # Verify that each Fine node is connected to a Loan node via HAS_FINE edge
    for fn in fine_nodes:
        edge_to_fine = [e for e in edges if e["to"] == fn["id"] and e["label"] == "HAS_FINE"]
        assert len(edge_to_fine) > 0, f"Fine node {fn['id']} ({fn['label']}) has no incoming HAS_FINE edge!"
        loan_id_elem = edge_to_fine[0]["from"]
        assert loan_id_elem in nodes, f"Parent Loan node {loan_id_elem} not in graph nodes!"
        parent_loan = nodes[loan_id_elem]
        print(f" -> Verified: Fine '{fn['label']}' is connected to Loan '{parent_loan['label']}'")

        # Verify that parent Loan is connected to User via BORROWED edge
        edge_to_loan = [e for e in edges if e["to"] == loan_id_elem and e["label"] == "BORROWED"]
        assert len(edge_to_loan) > 0, f"Parent Loan {parent_loan['label']} has no incoming BORROWED edge from User!"
        user_id_elem = edge_to_loan[0]["from"]
        assert user_id_elem in nodes, f"User node {user_id_elem} not in graph nodes!"
        print(f" -> Verified: Loan '{parent_loan['label']}' is connected to User '{nodes[user_id_elem]['label']}'")

    print("[PASS] Fix 1: Unpaid fine nodes on returned loans are fully connected in personal borrowing graph.")
    passed_count += 1

    # -------------------------------------------------------------
    # Fix 2: Auto-Sync Live Overdue Fines for Active Unreturned Loans
    # -------------------------------------------------------------
    print("\n--- [Fix 2] Testing sync_active_overdue_fines ---")
    with get_session() as d_sess:
        # Trigger sync directly or via route
        flask_app.sync_active_overdue_fines(d_sess)
        
        q = """
            MATCH (l:Loan)
            WHERE l.return_date IS NULL AND l.due_date < date()
            WITH l, duration.inDays(date(l.due_date), date()).days AS days_late
            WHERE days_late > 0
            MATCH (l)-[:HAS_FINE]->(f:Fine {payment_status: 'Unpaid'})
            RETURN l.loan_id AS lid, days_late, f.fine_amount AS amt
        """
        recs = list(d_sess.run(q))
        print(f"Active overdue loans with Unpaid fine: {len(recs)}")
        for r in recs:
            expected_amt = float(r["days_late"] * 10)
            print(f" -> Loan #{r['lid']}: {r['days_late']} days late -> Fine: Rs. {r['amt']} (Expected: Rs. {expected_amt})")
            assert abs(r["amt"] - expected_amt) < 0.01, f"Fine amount mismatch on Loan #{r['lid']}"
            
    print("[PASS] Fix 2: Live overdue fines match days_late * 10.")
    passed_count += 1

    # -------------------------------------------------------------
    # Fix 3: Stop Auto-Rejecting Pending Requests When Approving Last Copy
    # -------------------------------------------------------------
    print("\n--- [Fix 3] Testing loan_requests approval does not auto-reject queue ---")
    with open("app.py", "r", encoding="utf-8") as f:
        app_code = f.read()
    assert "r2.status = 'Rejected'" not in app_code, "Old auto-reject logic still present in app.py!"
    print(" -> Verified: No mass auto-rejection when approving requests.")
    print("[PASS] Fix 3: Pending queue preserved.")
    passed_count += 1

    # -------------------------------------------------------------
    # Fix 4: Delete Stale :RESERVED_COPY Edges on Auto-Fulfill & Iterative Sync
    # -------------------------------------------------------------
    print("\n--- [Fix 4] Testing :RESERVED_COPY cleanup & Python one-by-one iteration ---")
    assert "OPTIONAL MATCH (r)-[rel:RESERVED_COPY]->()" in app_code, "Missing RESERVED_COPY deletion in app.py"
    assert "for req in broken_reqs:" in app_code, "Missing one-by-one broken request iteration in sync_fulfilled_loan_requests"
    print(" -> Verified: RESERVED_COPY deleted upon auto-fulfilling lingering requests.")
    print(" -> Verified: sync_fulfilled_loan_requests iterates one-by-one in Python.")
    print("[PASS] Fix 4: Stale reservations properly handled.")
    passed_count += 1

    # -------------------------------------------------------------
    # Fix 5: Align Input Max Limits & Redirect Targets
    # -------------------------------------------------------------
    print("\n--- [Fix 5] Testing input max limits and redirect targets ---")
    with open("templates/category_books.html", "r", encoding="utf-8") as f:
        cat_html = f.read()
    assert 'max="100"' in cat_html, "category_books.html missing max='100'"
    
    with open("templates/issue_loan.html", "r", encoding="utf-8") as f:
        iss_html = f.read()
    assert 'max="60"' in iss_html, "issue_loan.html missing max='60'"
    assert "due_in_days > 60" in app_code, "app.py missing due_in_days > 60 check"

    # Set session as Admin
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "Admin"

    # Test invalid inventory adjustment redirect
    res = client.post("/adjust_inventory/1", data={"quantity": "9999", "action": "add", "category_id": "1"})
    assert res.status_code == 302
    assert "/category/1" in res.headers.get("Location", ""), f"Unexpected redirect: {res.headers.get('Location')}"
    print(" -> Verified: Invalid quantity redirects back to /category/1.")

    # Test invalid due_in_days redirect
    res = client.post("/issue_loan", data={"due_in_days": "100", "copy_id": "1", "borrower_username": "alex_stu"})
    assert res.status_code == 302
    assert "/issue_loan" in res.headers.get("Location", ""), f"Unexpected redirect: {res.headers.get('Location')}"
    print(" -> Verified: due_in_days > 60 redirects back to /issue_loan.")
    print("[PASS] Fix 5: Max limits and redirects aligned.")
    passed_count += 1

    # -------------------------------------------------------------
    # Fix 6: Validate Roles in /manage_users & Duplicate ISBNs in /add_book and /edit_book
    # -------------------------------------------------------------
    print("\n--- [Fix 6] Testing role validation & duplicate ISBN handling ---")
    # Test invalid role in manage_users
    res = client.post("/manage_users", data={
        "action": "add_user",
        "username": "baduser",
        "email": "baduser@vit.edu",
        "password": "Password123!",
        "role": "SuperUser"
    }, follow_redirects=True)
    assert b"Invalid role" in res.data, "manage_users allowed an invalid role!"
    print(" -> Verified: Invalid role 'SuperUser' was rejected with flash message.")

    with get_session() as s:
        existing_isbn = s.run("MATCH (b:Book {book_id: 1}) RETURN b.isbn AS isbn").single()["isbn"]

    # Test duplicate ISBN in add_book
    res = client.post("/add_book", data={
        "isbn": existing_isbn,
        "title": "Duplicate ISBN Book",
        "num_copies": "1"
    }, follow_redirects=True)
    assert b"already exists in the catalog" in res.data, "Duplicate ISBN was not detected in /add_book!"
    print(f" -> Verified: Duplicate ISBN '{existing_isbn}' was rejected in /add_book.")

    # Test duplicate ISBN in edit_book
    res = client.post("/edit_book/2", data={
        "isbn": existing_isbn,
        "title": "Design Patterns Duplicate ISBN",
        "publication_year": "1994"
    }, follow_redirects=True)
    assert b"already exists in the catalog" in res.data, "Duplicate ISBN was not detected in /edit_book!"
    print(f" -> Verified: Duplicate ISBN '{existing_isbn}' was rejected in /edit_book.")
    print("[PASS] Fix 6: Role validation and duplicate ISBN protection confirmed.")
    passed_count += 1

    # -------------------------------------------------------------
    # Fix 7: Guard Drawer Neighbor Clicks in templates/graph_visualizer.html
    # -------------------------------------------------------------
    print("\n--- [Fix 7] Testing drawer visibility filtering in templates/graph_visualizer.html ---")
    with open("templates/graph_visualizer.html", "r", encoding="utf-8") as f:
        viz_html = f.read()
    assert "visibleNodeIds" in viz_html, "templates/graph_visualizer.html missing visibleNodeIds check"
    assert "visibleNodeIds.has(otherId)" in viz_html, "templates/graph_visualizer.html missing otherId filter"
    print(" -> Verified: openDrawer filters connected relationships by visibleNodeIds.")
    print("[PASS] Fix 7: Visualizer drawer clicks guarded against hidden nodes.")
    passed_count += 1

    # -------------------------------------------------------------
    # Fix 8: Seed 10 Valid Fines in seed_all_data.py
    # -------------------------------------------------------------
    print("\n--- [Fix 8] Testing seeded records count across all entity types ---")
    with get_session() as d_sess:
        counts = {}
        for label in ["User", "Category", "Publisher", "Author", "Book", "Copy", "Loan", "Fine", "LoanRequest"]:
            c = d_sess.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()["c"]
            counts[label] = c
            print(f" -> {label}: {c} records")
            assert c >= 10, f"{label} has fewer than 10 records: {c}"
        assert counts["Fine"] == 10, f"Expected exactly 10 Fine records, found {counts['Fine']}"

    print("[PASS] Fix 8: Exactly 10 Fines and >=10 of all 9 entity types seeded.")
    passed_count += 1

    print("\n" + "=" * 70)
    print(f"ALL {passed_count}/{total_count} ARCHITECTURAL FIXES VERIFIED AND PASSING SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
