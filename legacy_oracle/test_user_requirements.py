import oracledb
from app import app

app.config["WTF_CSRF_ENABLED"] = False
app.config["TESTING"] = True

def run_suite():
    client = app.test_client()
    conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
    cur = conn.cursor()

    print("=====================================================================")
    print("TEST SUITE: Zero Fine, Borrowing Block for Overdue/Unpaid, Brand Cleanup")
    print("=====================================================================")

    # -------------------------------------------------------------------------
    # TEST 1: Removal of 'Oracle Database 21c Engine' & Top-Left '21c' Badge
    # -------------------------------------------------------------------------
    print("\n--- 1. Testing Removal of 'Oracle Database 21c Engine' & '21c' ---")
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "Admin"

    res_dash = client.get("/dashboard")
    assert res_dash.status_code == 200
    html_dash = res_dash.data.decode("utf-8")

    assert "Oracle Database 21c Engine" not in html_dash, "Found 'Oracle Database 21c Engine' in dashboard!"
    assert "21c Engine" not in html_dash, "Found '21c Engine' in dashboard!"
    assert '<span class="brand-badge">21c</span>' not in html_dash, "Found top-left '21c' brand badge in layout!"
    assert "brand-badge" not in html_dash, "Found brand-badge in layout!"
    assert "VITCC LIBRARY" in html_dash, "Missing VITCC LIBRARY title in layout"
    print("PASS: 'Oracle Database 21c Engine' and top-left '21c' badge are completely removed.")

    # -------------------------------------------------------------------------
    # TEST 2: 'Zero Fine' text in Fine Status for Admin, Librarian, Student, Staff
    # -------------------------------------------------------------------------
    print("\n--- 2. Testing 'Zero Fine' Text (Instead of 'Zero Outstanding Fine') ---")
    assert "Zero Outstanding Fine" not in html_dash, "Found 'Zero Outstanding Fine' in Admin dashboard!"
    assert "Zero Outstanding Fines" not in html_dash, "Found 'Zero Outstanding Fines' in Admin dashboard!"
    assert "Zero Fine" in html_dash, "Expected 'Zero Fine' in Admin active loans ledger!"
    print("PASS: Admin Dashboard displays 'Zero Fine' for loans without fines.")

    # Check Student Dashboard & Ledgers
    cur.execute("""
        SELECT u.User_ID, u.Username
        FROM Users u
        WHERE u.Role = 'Student'
          AND NVL((SELECT SUM(f.Fine_Amount) FROM Fines f JOIN Loans l ON f.Loan_ID = l.Loan_ID WHERE l.Borrower_ID = u.User_ID AND f.Payment_Status = 'Unpaid'), 0) = 0
          AND ROWNUM = 1
    """)
    clean_student = cur.fetchone()
    stu_id = clean_student[0]
    stu_name = clean_student[1]

    with client.session_transaction() as sess:
        sess["user_id"] = stu_id
        sess["username"] = stu_name
        sess["role"] = "Student"

    res_stu = client.get("/dashboard")
    assert res_stu.status_code == 200
    html_stu = res_stu.data.decode("utf-8")
    assert "Zero Outstanding Fine" not in html_stu, "Found 'Zero Outstanding Fine' in Student dashboard!"
    assert "Zero Outstanding Fines" not in html_stu, "Found 'Zero Outstanding Fines' in Student dashboard!"
    assert "Zero Fine" in html_stu, "Expected 'Zero Fine' in Student stats / ledger!"

    res_fines = client.get("/my_fines")
    assert res_fines.status_code == 200
    html_fines = res_fines.data.decode("utf-8")
    assert "Zero Outstanding Fine" not in html_fines, "Found 'Zero Outstanding Fine' in /my_fines!"
    assert "Zero Outstanding Fines" not in html_fines, "Found 'Zero Outstanding Fines' in /my_fines!"
    print(f"PASS: Student view ({stu_name}) and /my_fines displays 'Zero Fine'.")

    # Check Staff Dashboard
    cur.execute("SELECT u.User_ID, u.Username FROM Users u WHERE u.Role = 'Staff' AND ROWNUM = 1")
    staff = cur.fetchone()
    staff_id = staff[0]
    staff_name = staff[1]

    with client.session_transaction() as sess:
        sess["user_id"] = staff_id
        sess["username"] = staff_name
        sess["role"] = "Staff"

    res_staff = client.get("/dashboard")
    assert res_staff.status_code == 200
    html_staff = res_staff.data.decode("utf-8")
    assert "Zero Outstanding Fine" not in html_staff, "Found 'Zero Outstanding Fine' in Staff dashboard!"
    assert "Zero Outstanding Fines" not in html_staff, "Found 'Zero Outstanding Fines' in Staff dashboard!"
    assert "Zero Fine" in html_staff, "Expected 'Zero Fine' in Staff dashboard!"
    print(f"PASS: Staff view ({staff_name}) displays 'Zero Fine'.")

    # -------------------------------------------------------------------------
    # TEST 3: Borrowing Block for Overdue Loans and Unpaid Fines
    # -------------------------------------------------------------------------
    print("\n--- 3. Testing Borrowing Block for Overdue Loans & Unpaid Fines ---")

    # Pick an available copy and category
    cur.execute("""
        SELECT bc.Copy_ID, bc.Book_ID, b.Category_ID
        FROM Book_Copies bc
        JOIN Books b ON bc.Book_ID = b.Book_ID
        WHERE bc.Status = 'Available'
        ORDER BY bc.Copy_ID
    """)
    avail_row = cur.fetchone()
    test_copy_id = avail_row[0]
    test_book_id = avail_row[1]
    test_cat_id = avail_row[2]

    temp_uid = None
    temp_lid = None
    temp_fid = None
    temp_rid = None

    # Clean up test user if previously left over
    cur.execute("DELETE FROM Users WHERE Username = 'test_delinquent'")
    conn.commit()

    # Create a temporary student user for isolated testing (omit User_ID so IDENTITY assigns natively)
    cur.execute("""
        INSERT INTO Users (Username, Email, Password_Hash, Role, Account_Status)
        VALUES (:p_uname, :p_email, :p_pwd, :p_role, :p_status)
    """, {
        "p_uname": "test_delinquent",
        "p_email": "test_delinquent@vit.ac.in",
        "p_pwd": "TestPass@123",
        "p_role": "Student",
        "p_status": "Active"
    })
    conn.commit()

    cur.execute("SELECT User_ID FROM Users WHERE Username = 'test_delinquent'")
    temp_uid = cur.fetchone()[0]

    try:
        # Scenario A: Patron has an OVERDUE loan
        # Insert overdue loan for temp user (due 5 days ago, return_date NULL)
        cur.execute("SELECT NVL(MAX(Loan_ID), 0) + 1 FROM Loans")
        temp_lid = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO Loans (Loan_ID, Copy_ID, Borrower_ID, Issued_By, Issue_Date, Due_Date, Return_Date)
            VALUES (:p_lid, :p_cid, :p_bid, 1, SYSDATE - 19, SYSDATE - 5, NULL)
        """, {"p_lid": temp_lid, "p_cid": test_copy_id, "p_bid": temp_uid})
        cur.execute("UPDATE Book_Copies SET Status = 'Borrowed' WHERE Copy_ID = :p_cid", {"p_cid": test_copy_id})
        conn.commit()

        # Try to request loan as student with overdue loan
        with client.session_transaction() as sess:
            sess["user_id"] = temp_uid
            sess["username"] = "test_delinquent"
            sess["role"] = "Student"

        # 1. Check category page shows Borrowing Blocked banner and badge
        res_cat = client.get(f"/category/{test_cat_id}")
        html_cat = res_cat.data.decode("utf-8")
        assert "Borrowing Blocked" in html_cat, "Expected 'Borrowing Blocked' banner on category page for overdue user!"
        assert "overdue" in html_cat.lower(), "Expected overdue explanation in block banner!"

        # 2. Try POST /request_loan
        res_req = client.post(f"/request_loan/{test_book_id}", follow_redirects=True)
        html_req = res_req.data.decode("utf-8")
        assert "Permission Denied" in html_req or "overdue" in html_req.lower(), "Overdue borrower was not blocked from requesting a loan!"
        print("PASS: Patron with overdue loan is blocked from submitting loan requests.")

        # 3. Check Admin /issue_loan blocks issuing to this borrower
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "Admin"

        # Pick another available copy
        cur.execute("SELECT Copy_ID FROM Book_Copies WHERE Status = 'Available' AND ROWNUM = 1")
        another_copy = cur.fetchone()[0]

        res_issue = client.post("/issue_loan", data={
            "copy_id": str(another_copy),
            "borrower_id": str(temp_uid),
            "due_in_days": "14"
        }, follow_redirects=True)
        html_issue = res_issue.data.decode("utf-8")
        assert "Borrowing Prohibited" in html_issue and "overdue" in html_issue.lower(), "Admin was able to issue loan to patron with overdue loans!"
        print("PASS: Admin is blocked from directly issuing books to patron with overdue loans.")

        # Scenario B: Return the overdue book, but an UNPAID FINE remains
        # Process return and insert unpaid fine
        cur.execute("UPDATE Loans SET Return_Date = SYSDATE WHERE Loan_ID = :p_lid", {"p_lid": temp_lid})
        cur.execute("UPDATE Book_Copies SET Status = 'Available' WHERE Copy_ID = :p_cid", {"p_cid": test_copy_id})
        cur.execute("SELECT NVL(MAX(Fine_ID), 0) + 1 FROM Fines")
        temp_fid = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO Fines (Fine_ID, Loan_ID, Fine_Amount, Payment_Status)
            VALUES (:p_fid, :p_lid, 50.00, 'Unpaid')
        """, {"p_fid": temp_fid, "p_lid": temp_lid})
        conn.commit()

        # Try requesting loan as student with unpaid fine
        with client.session_transaction() as sess:
            sess["user_id"] = temp_uid
            sess["username"] = "test_delinquent"
            sess["role"] = "Student"

        # 1. Check category page shows Borrowing Blocked banner and badge
        res_cat2 = client.get(f"/category/{test_cat_id}")
        html_cat2 = res_cat2.data.decode("utf-8")
        assert "Borrowing Blocked" in html_cat2, "Expected 'Borrowing Blocked' on category page for user with unpaid fine!"
        assert "fine" in html_cat2.lower() or "50.00" in html_cat2, "Expected unpaid fine explanation in block banner!"

        # 2. Try POST /request_loan
        res_req2 = client.post(f"/request_loan/{test_book_id}", follow_redirects=True)
        html_req2 = res_req2.data.decode("utf-8")
        assert "Permission Denied" in html_req2 and "fine" in html_req2.lower(), "Borrower with unpaid fine was not blocked from requesting loan!"
        print("PASS: Patron with unpaid fine is blocked from submitting loan requests.")

        # 3. Check Admin /issue_loan blocks issuing to borrower with unpaid fine
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "Admin"

        res_issue2 = client.post("/issue_loan", data={
            "copy_id": str(another_copy),
            "borrower_id": str(temp_uid),
            "due_in_days": "14"
        }, follow_redirects=True)
        html_issue2 = res_issue2.data.decode("utf-8")
        assert ("Borrowing Prohibited" in html_issue2 or "Transaction Blocked" in html_issue2 or "Failed to issue" in html_issue2) and "fine" in html_issue2.lower(), "Admin was able to issue loan to patron with unpaid fine!"
        print("PASS: Admin is blocked from directly issuing books to patron with unpaid fine.")

        # 4. Check Loan Requests Queue blocks approval for borrower with unpaid fine
        # Insert a pending request for this user directly
        cur.execute("SELECT NVL(MAX(Request_ID), 0) + 1 FROM Loan_Requests")
        temp_rid = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO Loan_Requests (Request_ID, Book_ID, Borrower_ID, Request_Date, Status)
            VALUES (:p_rid, :p_bid, :p_uid, SYSDATE, 'Pending')
        """, {"p_rid": temp_rid, "p_bid": test_book_id, "p_uid": temp_uid})
        conn.commit()

        # Check loan requests page shows warning badge and disabled approve button
        res_queue = client.get("/loan_requests")
        html_queue = res_queue.data.decode("utf-8")
        assert f"#REQ-{temp_rid}" in html_queue
        assert "Unpaid Fine: Rs. 50.00" in html_queue, "Missing Unpaid Fine badge in loan requests queue!"

        # Attempt to approve
        res_appr = client.post("/loan_requests", data={
            "request_id": str(temp_rid),
            "action": "approve"
        }, follow_redirects=True)
        html_appr = res_appr.data.decode("utf-8")
        assert "Approval Prohibited" in html_appr and "fine" in html_appr.lower(), "Librarian/Admin was able to approve request for patron with unpaid fine!"
        print("PASS: Loan Requests queue blocks approval and warns of unpaid fines.")

        # Clean up pending request
        cur.execute("DELETE FROM Loan_Requests WHERE Request_ID = :p_rid", {"p_rid": temp_rid})
        conn.commit()

    finally:
        # Clean up test records
        cur.execute("BEGIN DBMS_APPLICATION_INFO.SET_CLIENT_INFO('ALLOW_DELETE'); END;")
        if temp_lid:
            cur.execute("DELETE FROM Fines WHERE Loan_ID = :p_lid", {"p_lid": temp_lid})
        cur.execute("BEGIN DBMS_APPLICATION_INFO.SET_CLIENT_INFO(NULL); END;")
        if temp_lid:
            cur.execute("DELETE FROM Loans WHERE Loan_ID = :p_lid", {"p_lid": temp_lid})
        cur.execute("UPDATE Book_Copies SET Status = 'Available' WHERE Copy_ID = :p_cid", {"p_cid": test_copy_id})
        if temp_uid:
            cur.execute("DELETE FROM Users WHERE User_ID = :p_uid", {"p_uid": temp_uid})
        conn.commit()

    conn.close()
    print("\n=====================================================================")
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=====================================================================")

if __name__ == "__main__":
    run_suite()
