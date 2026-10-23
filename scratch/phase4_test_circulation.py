import sys
import os
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import app

def test_phase4_circulation():
    print("=================================================================")
    print("PHASE 4: CIRCULATION WORKFLOWS (REQUESTS, LOANS, RETURNS & FINES)")
    print("=================================================================")
    app.app.config["TESTING"] = True
    app.app.config["WTF_CSRF_ENABLED"] = False
    client = app.app.test_client()

    # 1. Role Guard on /request_loan
    print("\n--- 1. Testing Role Restrictions on /request_loan ---")
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "Admin"
        sess["last_activity"] = time.time()

    resp = client.post("/request_loan/2", follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Only Students and Staff may request book loans" in html
    print("[PASS] Admin correctly prevented from requesting loans.")

    # 2. Student Loan Request Submission & Workflow
    print("\n--- 2. Testing Student Request Creation & Approval Lifecycle ---")
    # Clean up any lingering test requests for student (user_id: 11 Marcus or test user)
    test_uid = 11 # Marcus (Student)
    test_bid = 8  # Domain-Driven Design (Category 1)

    with app.get_session() as s:
        # Clear existing test requests/loans for this book & user
        s.run("""
            MATCH (u:User {user_id: $uid})-[r:REQUESTED]->(req:LoanRequest)-[:FOR_BOOK]->(b:Book {book_id: $bid})
            OPTIONAL MATCH (req)-[rel:RESERVED_COPY]->()
            DETACH DELETE req
        """, uid=test_uid, bid=test_bid)

    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = test_uid
        sess["username"] = "marcus"
        sess["role"] = "Student"
        sess["last_activity"] = time.time()

    resp = client.post(f"/request_loan/{test_bid}", data={"from_dashboard": "1"}, follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "submitted! Awaiting Librarian approval" in html or "Loan request for" in html
    print("[PASS] Student loan request successfully created.")

    # Fetch created request_id
    with app.get_session() as s:
        rec = s.run("""
            MATCH (u:User {user_id: $uid})-[:REQUESTED]->(r:LoanRequest {status: 'Pending'})-[:FOR_BOOK]->(b:Book {book_id: $bid})
            RETURN r.request_id AS rid
        """, uid=test_uid, bid=test_bid).single()
        assert rec is not None, "Pending LoanRequest node not found in Neo4j"
        test_rid = rec["rid"]
    print(f"[PASS] Pending LoanRequest node #{test_rid} verified in Neo4j AuraDB.")

    # Duplicate request prevention
    resp = client.post(f"/request_loan/{test_bid}", data={"from_dashboard": "1"}, follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "already have an active request" in html
    print("[PASS] Duplicate request rejected cleanly.")

    # 3. Librarian Approval of Request
    print("\n--- 3. Testing Librarian Approval (/loan_requests) ---")
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = 2
        sess["username"] = "librarian"
        sess["role"] = "Librarian"
        sess["last_activity"] = time.time()

    resp = client.post("/loan_requests", data={"request_id": test_rid, "action": "approve"}, follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "approved!" in html or "reserved" in html
    print(f"[PASS] Request #{test_rid} approved by Librarian. Copy successfully reserved.")

    # Verify status in DB is 'Awaiting Pickup' and copy is 'Reserved'
    with app.get_session() as s:
        rec = s.run("""
            MATCH (r:LoanRequest {request_id: $rid})
            MATCH (r)-[:RESERVED_COPY]->(cp:Copy)
            RETURN r.status AS status, cp.copy_id AS cid, cp.status AS cp_status
        """, rid=test_rid).single()
        assert rec["status"] == "Awaiting Pickup"
        assert rec["cp_status"] == "Reserved"
        reserved_cid = rec["cid"]
    print(f"[PASS] AuraDB state: Request #{test_rid} is 'Awaiting Pickup', Copy #{reserved_cid} is 'Reserved'.")

    # 4. Physical Handover / Confirm Pickup
    print("\n--- 4. Testing Physical Handover / Confirm Pickup ---")
    resp = client.post("/loan_requests", data={"request_id": test_rid, "action": "confirm_pickup"}, follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Collection Confirmed!" in html or "issued to" in html
    print(f"[PASS] Handover confirmed: Book issued to Marcus.")

    # Verify Loan node and copy status 'Borrowed'
    with app.get_session() as s:
        rec = s.run("""
            MATCH (u:User {user_id: $uid})-[:BORROWED]->(l:Loan)-[:FOR_COPY]->(cp:Copy {copy_id: $cid})
            WHERE l.return_date IS NULL
            RETURN l.loan_id AS lid, cp.status AS cp_status
        """, uid=test_uid, cid=reserved_cid).single()
        assert rec is not None, "Active loan not found in AuraDB"
        assert rec["cp_status"] == "Borrowed"
        test_lid = rec["lid"]
    print(f"[PASS] Loan #{test_lid} active in AuraDB; Copy #{reserved_cid} status is 'Borrowed'.")

    # 5. Book Return Workflow
    print("\n--- 5. Testing Book Return Workflow (/return_book) ---")
    resp = client.post(f"/return_book/{test_lid}", follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "returned successfully" in html or "returned" in html

    # Verify Loan has return_date and Copy is restored to Available
    with app.get_session() as s:
        rec = s.run("""
            MATCH (l:Loan {loan_id: $lid})-[:FOR_COPY]->(cp:Copy {copy_id: $cid})
            RETURN l.return_date AS ret_date, cp.status AS cp_status
        """, lid=test_lid, cid=reserved_cid).single()
        assert rec["ret_date"] is not None, "Return date was not set"
        assert rec["cp_status"] == "Available", f"Expected Available, got {rec['cp_status']}"
    print(f"[PASS] Loan #{test_lid} closed with return_date; Copy #{reserved_cid} restored to 'Available'.")

    # 6. Fine Payment / Waive Workflow
    print("\n--- 6. Testing Disciplinary Fine Payment & Waive (/pay_fine) ---")
    # Create a test fine on the returned loan
    with app.get_session() as s:
        fid = app.next_id(s, "Fine", "fine_id")
        s.run("""
            MATCH (l:Loan {loan_id: $lid})
            CREATE (f:Fine {
                fine_id: $fid, loan_id: $lid,
                fine_amount: 50.0, payment_status: 'Unpaid',
                payment_date: null, collected_by: null
            })
            CREATE (l)-[:HAS_FINE]->(f)
        """, fid=fid, lid=test_lid)

    # Pay fine
    resp = client.post(f"/pay_fine/{fid}", data={"payment_action": "Paid"}, follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "marked as Paid" in html or "Paid!" in html

    with app.get_session() as s:
        rec = s.run("MATCH (f:Fine {fine_id: $fid}) RETURN f.payment_status AS status, f.payment_date AS pdate", fid=fid).single()
        assert rec["status"] == "Paid"
        assert rec["pdate"] is not None

        # Clean up test fine and loan
        s.run("MATCH (l:Loan {loan_id: $lid}) OPTIONAL MATCH (l)-[:HAS_FINE]->(f:Fine) DETACH DELETE l, f", lid=test_lid)
        s.run("MATCH (r:LoanRequest {request_id: $rid}) DETACH DELETE r", rid=test_rid)
    print(f"[PASS] Fine #{fid} successfully settled and cleaned up.")

    print("\n=================================================================")
    print("PHASE 4 VERIFICATION COMPLETED: 100% PASSING")
    print("=================================================================")

if __name__ == "__main__":
    test_phase4_circulation()
