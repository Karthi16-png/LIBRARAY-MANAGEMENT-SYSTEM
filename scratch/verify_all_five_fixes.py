import sys
import os
import re

# Ensure workspace root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, get_session

def run_tests():
    print("=" * 60)
    print("RUNNING VERIFICATION FOR ALL 5 FIXES")
    print("=" * 60)

    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    client = app.test_client()

    # -------------------------------------------------------------
    # 1. UI: Button Icon, Category Card Subtitle, Table Header
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing UI: Single Plus, Category Subtitles, and Table Header...")
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "Admin"
    
    # Check catalog.html for Admin
    res = client.get("/books")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "+ + Register New Book" not in html, "Found double plus in /books for Admin"
    assert "Register New Book" in html, "Missing Register New Book button in /books"
    assert "Click to browse titles, inspect copy availability, and manage loans in this category." in html, "Admin category subtitle mismatch"

    # Check category_books.html for Admin
    res = client.get("/category/1")
    assert res.status_code == 200
    cat_html = res.data.decode("utf-8")
    assert "+ + Register New Book" not in cat_html, "Found double plus in /category/1 for Admin"
    assert "Register New Book" in cat_html, "Missing Register New Book button in /category/1"

    # Check catalog.html for Staff / Student
    with client.session_transaction() as sess:
        sess["user_id"] = 6
        sess["username"] = "student"
        sess["role"] = "Student"
    res = client.get("/books")
    assert res.status_code == 200
    stu_html = res.data.decode("utf-8")
    assert "Click to browse titles, check real-time copy availability, and request loans in this category." in stu_html, "Student category subtitle mismatch"
    assert "+ Register New Book" not in stu_html, "Students should not see Register New Book"

    # Check Table Header in loan_requests.html
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "Admin"
    res = client.get("/loan_requests")
    assert res.status_code == 200
    lr_html = res.data.decode("utf-8")
    assert "Request&nbsp;Timestamp" in lr_html or "Request Timestamp" in lr_html, "Missing Request Timestamp table header"
    print("  [PASS] Single plus, role-scoped category subtitles, and table header verified.")

    # -------------------------------------------------------------
    # 2. /recommendations: Grammar, Librarian Banner, Staff Isolation, Jaccard
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing /recommendations: Grammar, Role Banner, Staff Isolation, and Jaccard Query...")
    # Librarian View Banner
    with client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["username"] = "librarian"
        sess["role"] = "Librarian"
    res = client.get("/recommendations")
    assert res.status_code == 200
    lib_rec_html = res.data.decode("utf-8")
    assert "Librarian View: Global Patron Collaborative Filtering Network" in lib_rec_html, "Missing dynamic Librarian View banner"
    assert "1 Readers" not in lib_rec_html, "Grammar bug: '1 Readers' found in librarian recommendations"

    # Staff Isolation View
    with client.session_transaction() as sess:
        sess["user_id"] = 4
        sess["username"] = "staff"
        sess["role"] = "Staff"
    res = client.get("/recommendations")
    assert res.status_code == 200
    staff_rec_html = res.data.decode("utf-8")
    # Must not say '2 Readers' or aggregate student borrower counts onto staff recommendation cards
    assert "2 Readers" not in staff_rec_html, "Staff view aggregated student loans onto recommendation badges!"
    assert "Curriculum Match" in staff_rec_html or "Topic Match" in staff_rec_html or "Reader" in staff_rec_html, "Missing staff graph match badge"

    # Student Jaccard Study Partners: Strictly borrowed books
    with client.session_transaction() as sess:
        sess["user_id"] = 6
        sess["username"] = "student"
        sess["role"] = "Student"
    res = client.get("/recommendations")
    assert res.status_code == 200
    stu_rec_html = res.data.decode("utf-8")
    assert "Modern Operating Systems (4th Ed)" not in stu_rec_html, "Unread requested book Modern Operating Systems appeared in Jaccard study partners!"
    print("  [PASS] Dynamic Librarian banner, grammar, Staff reader count isolation, and Jaccard query verified.")

    # -------------------------------------------------------------
    # 3. /loan_requests: Blocked Status Button & Backend Stock Guard
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing /loan_requests: Blocked Status Button & Backend Guards...")
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "Admin"
    res = client.get("/loan_requests")
    assert res.status_code == 200
    lr_html = res.data.decode("utf-8")
    # alex_stu (#REQ-3) has unpaid fines and Book 3 has 0 available copies
    assert "Blocked: Fine / 0 Stock" in lr_html or "Blocked:" in lr_html, "Missing Blocked status button for #REQ-3"
    assert "Reject" in lr_html, "Reject button must remain available for blocked requests"

    # Test backend rejection when out of stock
    res_approve = client.post("/loan_requests", data={"request_id": 3, "action": "approve"}, follow_redirects=True)
    post_html = res_approve.data.decode("utf-8")
    assert "Approval Prohibited" in post_html or "Cannot approve" in post_html or "unpaid fines" in post_html or "0 stock" in post_html, "Backend allowed approving blocked request #REQ-3!"
    print("  [PASS] Blocked: Fine / 0 Stock status button and backend approval guard verified.")

    # -------------------------------------------------------------
    # 4. Neo4j Data Consistency: #REQ-4, Fines & Loans
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Neo4j Data Consistency (#REQ-4, #FN-10, #LN-7, #LN-4)...")
    with get_session() as s:
        # 1. #REQ-4 reassigned to marcus_stu
        res = s.run("""
            MATCH (r:LoanRequest {request_id: 4})
            MATCH (u:User {user_id: r.borrower_id})
            RETURN u.username AS username, r.status AS status
        """)
        req4 = res.single()
        assert req4["username"] == "marcus_stu", f"Expected #REQ-4 assigned to marcus_stu, got {req4['username']}"
        assert req4["status"] == "Awaiting Pickup", f"Expected Awaiting Pickup status, got {req4['status']}"

        # 2. #FN-10 removed from future-due loan #LN-1
        res = s.run("""
            MATCH (l:Loan {loan_id: 1})
            OPTIONAL MATCH (l)-[:HAS_FINE]->(f:Fine)
            RETURN l.due_date AS due_date, count(f) AS fine_count
        """)
        ln1 = res.single()
        assert ln1["fine_count"] == 0, f"Future-due Loan #1 still has {ln1['fine_count']} fines attached!"

        # 3. Loan #7 return_date and Fine #7 amount
        res = s.run("""
            MATCH (l:Loan {loan_id: 7})-[:HAS_FINE]->(f:Fine {fine_id: 7})
            RETURN l.due_date AS due_date, l.return_date AS return_date, f.fine_amount AS amt, f.payment_status AS status
        """)
        ln7 = res.single()
        assert ln7["return_date"] == "2026-10-04", f"Loan #7 return_date expected 2026-10-04, got {ln7['return_date']}"
        assert ln7["amt"] == 30.00, f"Fine #7 expected Rs. 30.00, got {ln7['amt']}"
        assert ln7["status"] == "Paid", f"Fine #7 expected Paid, got {ln7['status']}"

        # 4. Loan #4 returned Oct 17 and Fine #1 sync
        res = s.run("""
            MATCH (l:Loan {loan_id: 4})-[:HAS_FINE]->(f:Fine {fine_id: 1})
            MATCH (cp:Copy {copy_id: l.copy_id})
            RETURN l.due_date AS due_date, l.return_date AS return_date,
                   f.fine_amount AS amt, f.payment_status AS status,
                   cp.status AS cp_status
        """)
        ln4 = res.single()
        assert ln4["return_date"] == "2026-10-17", f"Loan #4 expected return_date 2026-10-17, got {ln4['return_date']}"
        assert ln4["amt"] == 110.00, f"Fine #1 expected Rs. 110.00, got {ln4['amt']}"
        assert ln4["status"] == "Paid", f"Fine #1 expected Paid, got {ln4['status']}"
        assert ln4["cp_status"] == "Available", f"Copy #4 expected Available, got {ln4['cp_status']}"
    print("  [PASS] Neo4j data consistency verified: #REQ-4, #FN-10 deleted, #LN-7 (30.00 Paid), #LN-4 (Returned, Copy Available, 110.00 Paid).")

    # -------------------------------------------------------------
    # 5. /api/graph_data: Returned Loan Node Labeling and Filtering
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing /api/graph_data: [Returned] Node Formatting and Personal Subgraph Filtering...")
    # Staff personal view: Loan #14 was returned, so it should not appear as an active loan in staff personal graph
    with client.session_transaction() as sess:
        sess["user_id"] = 4
        sess["username"] = "staff"
        sess["role"] = "Staff"
    res = client.get("/api/graph_data?view=personal")
    assert res.status_code == 200
    staff_graph = res.get_json()
    loan_nodes_staff = [n for n in staff_graph["nodes"] if n.get("group") == "Loan"]
    for ln in loan_nodes_staff:
        assert "[Active]" in ln["label"] or "[Returned]" in ln["label"]
        if ln.get("properties", {}).get("return_date"):
            assert "[Returned]" in ln["label"], f"Node {ln['label']} has return_date but is not labeled [Returned]"
        else:
            assert "[Active]" in ln["label"]

    # Student personal view: Loan #7 and Loan #10 were returned
    with client.session_transaction() as sess:
        sess["user_id"] = 6
        sess["username"] = "student"
        sess["role"] = "Student"
    res = client.get("/api/graph_data?view=personal")
    assert res.status_code == 200
    stu_graph = res.get_json()
    loan_nodes_stu = [n for n in stu_graph["nodes"] if n.get("group") == "Loan"]
    for ln in loan_nodes_stu:
        if ln.get("properties", {}).get("return_date"):
            assert "[Returned]" in ln["label"], f"Node {ln['label']} has return_date but is not labeled [Returned]"
        else:
            assert "[Active]" in ln["label"]

    # Global circulation view (Admin): Check that returned loans are labeled [Returned]
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "Admin"
    res = client.get("/api/graph_data?view=circulation")
    assert res.status_code == 200
    circ_graph = res.get_json()
    loan_nodes_circ = [n for n in circ_graph["nodes"] if n.get("group") == "Loan"]
    returned_count = sum(1 for ln in loan_nodes_circ if "[Returned]" in ln["label"])
    active_count = sum(1 for ln in loan_nodes_circ if "[Active]" in ln["label"])
    assert returned_count > 0, "No loans labeled [Returned] in global circulation graph"
    assert active_count > 0, "No loans labeled [Active] in global circulation graph"
    print(f"  [PASS] Vis.js Loan nodes correctly formatted: {active_count} [Active], {returned_count} [Returned].")

    print("\n" + "=" * 60)
    print("ALL 5 AUDIT REQUIREMENTS VERIFIED AND PASSING WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
