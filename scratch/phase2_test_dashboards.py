import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import app

def test_phase2_dashboards():
    print("=================================================================")
    print("PHASE 2: DASHBOARD SECTION VERIFICATION ACROSS ALL 4 ROLES")
    print("=================================================================")
    app.app.config["TESTING"] = True
    app.app.config["WTF_CSRF_ENABLED"] = False
    client = app.app.test_client()

    # 1. Admin Dashboard
    print("\n--- 1. Testing Admin Dashboard ---")
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "Admin"
        sess["last_activity"] = time.time()

    resp = client.get("/dashboard")
    assert resp.status_code == 200, f"Admin dashboard failed with status {resp.status_code}"
    html = resp.get_data(as_text=True)
    assert "Total Titles" in html
    assert "Active Loans" in html
    assert "Overdue Loans" in html
    assert "Disciplinary Fines" in html
    assert "Currently Active Book Loans" in html
    assert "Overdue Borrowers Watchlist" in html
    assert "Disciplinary Fines &amp; Liabilities Ledger" in html or "Disciplinary Fines" in html
    assert "Manage Users" in html, "Admin dashboard missing Manage Users action"
    assert "Issue Book" in html
    assert "Loan Requests" in html
    print("[PASS] Admin dashboard completely verified with all operational ledgers & administrative controls.")

    # 2. Librarian Dashboard
    print("\n--- 2. Testing Librarian Dashboard ---")
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = 2
        sess["username"] = "librarian"
        sess["role"] = "Librarian"
        sess["last_activity"] = time.time()

    resp = client.get("/dashboard")
    assert resp.status_code == 200, f"Librarian dashboard failed with status {resp.status_code}"
    html = resp.get_data(as_text=True)
    assert "Total Titles" in html
    assert "Active Loans" in html
    assert "Overdue Loans" in html
    assert "Currently Active Book Loans" in html
    assert "Overdue Borrowers Watchlist" in html
    assert "Issue Book" in html
    # Librarian must NOT have Manage Users button in quick actions
    assert "url_for('manage_users')" not in html and 'href="/manage_users"' not in html, "Librarian dashboard wrongly exposed Manage Users link!"
    print("[PASS] Librarian dashboard verified: Full circulation management active, Manage Users cleanly hidden.")

    # 3. Staff Dashboard
    print("\n--- 3. Testing Staff (Faculty) Dashboard ---")
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = 3
        sess["username"] = "staff"
        sess["role"] = "Staff"
        sess["last_activity"] = time.time()

    resp = client.get("/dashboard")
    assert resp.status_code == 200, f"Staff dashboard failed with status {resp.status_code}"
    html = resp.get_data(as_text=True)
    assert "Committed Books" in html
    assert "My Checked Out Books" in html
    assert "My Loan Requests" in html
    assert "Active Borrowers Ledger" not in html, "Staff dashboard leaked administrative borrowers ledger!"
    assert "Overdue Borrowers Watchlist" not in html, "Staff dashboard leaked administrative overdue watchlist!"
    print("[PASS] Staff dashboard verified: Personal quota and borrowings cleanly isolated.")

    # 4. Student Dashboard
    print("\n--- 4. Testing Student Dashboard ---")
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = 6
        sess["username"] = "student"
        sess["role"] = "Student"
        sess["last_activity"] = time.time()

    resp = client.get("/dashboard")
    assert resp.status_code == 200, f"Student dashboard failed with status {resp.status_code}"
    html = resp.get_data(as_text=True)
    assert "Committed Books" in html
    assert "My Active Loans" in html
    assert "My Loan Requests" in html
    assert "Active Borrowers Ledger" not in html, "Student dashboard leaked administrative borrowers ledger!"
    assert "Overdue Borrowers Watchlist" not in html, "Student dashboard leaked administrative overdue watchlist!"
    print("[PASS] Student dashboard verified: Personal quota, requests, and borrowings cleanly isolated.")

    print("\n=================================================================")
    print("PHASE 2 VERIFICATION COMPLETED: 100% PASSING")
    print("=================================================================")

if __name__ == "__main__":
    test_phase2_dashboards()
