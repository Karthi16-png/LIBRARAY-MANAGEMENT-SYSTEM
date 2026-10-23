import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
from datetime import datetime, timedelta
import oracledb
from app import app

app.config["WTF_CSRF_ENABLED"] = False
app.config["TESTING"] = True
client = app.test_client()

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()

print("=====================================================================")
print("TEST SUITE: Hold System, Catalog Mutability, Domain Check, & Timeouts")
print("=====================================================================")

# ---------------------------------------------------------------------------
# TEST 1: Domain Validation in /register
# ---------------------------------------------------------------------------
print("\n--- 1. Testing Domain Validation in /register ---")
res_fake = client.post("/register", data={
    "username": "spoofed_student",
    "email": "hacker@gmail.com",
    "password": "Password@123",
    "role": "Student"
}, follow_redirects=True)
html_fake = res_fake.data.decode("utf-8")
assert "Security Violation: Registration requires a valid institutional email domain" in html_fake, "Failed to block non-institutional email in /register!"
print("PASS: Blocked non-institutional email 'hacker@gmail.com'.")

res_fake2 = client.post("/register", data={
    "username": "spoofed_student",
    "email": "hacker@yahoo.com",
    "password": "Password@123",
    "role": "Student"
}, follow_redirects=True)
html_fake2 = res_fake2.data.decode("utf-8")
assert "Security Violation: Registration requires a valid institutional email domain" in html_fake2
print("PASS: Blocked non-institutional email 'hacker@yahoo.com'.")

# ---------------------------------------------------------------------------
# TEST 2: Kiosk Idle Timeout (@app.before_request)
# ---------------------------------------------------------------------------
print("\n--- 2. Testing Kiosk Idle Session Timeout ---")
with client.session_transaction() as sess:
    sess["user_id"] = 1
    sess["username"] = "admin"
    sess["role"] = "Admin"
    # Simulate activity from 11 minutes (660 seconds) ago
    sess["last_activity"] = datetime.now().timestamp() - 660

res_idle = client.get("/dashboard", follow_redirects=False)
# Should redirect to login
assert res_idle.status_code == 302, f"Expected 302 redirect on idle session, got {res_idle.status_code}"
assert "/login" in res_idle.headers.get("Location", "")
print("PASS: Idle session (> 10 minutes) automatically terminated and redirected to /login.")

# ---------------------------------------------------------------------------
# TEST 3: Catalog Mutability (/edit_book/<book_id>)
# ---------------------------------------------------------------------------
print("\n--- 3. Testing Catalog Mutability (/edit_book) ---")
with client.session_transaction() as sess:
    sess["user_id"] = 1
    sess["username"] = "admin"
    sess["role"] = "Admin"
    sess["last_activity"] = datetime.now().timestamp()

cur.execute("SELECT Book_ID, Title, ISBN, Publication_Year FROM Books WHERE ROWNUM = 1")
b_row = cur.fetchone()
edit_bid, orig_title, orig_isbn, orig_year = b_row[0], b_row[1], b_row[2], b_row[3]

# GET request to prepopulate
res_get = client.get(f"/edit_book/{edit_bid}")
assert res_get.status_code == 200
html_get = res_get.data.decode("utf-8")
assert orig_title in html_get
print("PASS: GET /edit_book prepopulates current metadata.")

# POST update
updated_title = orig_title + " (2nd Edition)"
res_post = client.post(f"/edit_book/{edit_bid}", data={
    "title": updated_title,
    "isbn": orig_isbn,
    "publication_year": "2024"
}, follow_redirects=True)
assert res_post.status_code == 200

cur.execute("SELECT Title, Publication_Year FROM Books WHERE Book_ID = :bid", {"bid": edit_bid})
row_check = cur.fetchone()
assert row_check[0] == updated_title
assert row_check[1] == 2024
print("PASS: POST /edit_book successfully updated database catalog record.")

# Restore original
cur.execute("UPDATE Books SET Title = :t, Publication_Year = :y WHERE Book_ID = :bid", {
    "t": orig_title, "y": orig_year, "bid": edit_bid
})
conn.commit()

# ---------------------------------------------------------------------------
# TEST 4: "Ghost Countdown" Hold System (Loan_Requests & /issue_loan)
# ---------------------------------------------------------------------------
print("\n--- 4. Testing 'Ghost Countdown' Hold System ---")
# Create clean test student
cur.execute("DELETE FROM Users WHERE Username = 'test_hold_student'")
conn.commit()
cur.execute("""
    INSERT INTO Users (Username, Email, Password_Hash, Role, Account_Status)
    VALUES ('test_hold_student', 'hold@vit.edu', 'TestPass@123', 'Student', 'Active')
""")
conn.commit()
cur.execute("SELECT User_ID FROM Users WHERE Username = 'test_hold_student'")
hold_uid = cur.fetchone()[0]

# Pick an available copy
cur.execute("""
    SELECT bc.Copy_ID, bc.Book_ID 
    FROM Book_Copies bc 
    WHERE bc.Status = 'Available' AND ROWNUM = 1
""")
c_row = cur.fetchone()
hold_cid = c_row[0]
hold_bid = c_row[1]

# Create Pending Loan Request
cur.execute("SELECT NVL(MAX(Request_ID), 0) + 1 FROM Loan_Requests")
hold_rid = cur.fetchone()[0]
cur.execute("""
    INSERT INTO Loan_Requests (Request_ID, Book_ID, Borrower_ID, Request_Date, Status)
    VALUES (:rid, :bid, :p_uid, SYSDATE, 'Pending')
""", {"rid": hold_rid, "bid": hold_bid, "p_uid": hold_uid})
conn.commit()

# Count initial loans
cur.execute("SELECT COUNT(*) FROM Loans WHERE Borrower_ID = :p_uid", {"p_uid": hold_uid})
initial_loans = cur.fetchone()[0]

# 1. Librarian Approves the Request
with client.session_transaction() as sess:
    sess["user_id"] = 1
    sess["username"] = "admin"
    sess["role"] = "Admin"
    sess["last_activity"] = datetime.now().timestamp()

res_appr = client.post("/loan_requests", data={
    "request_id": str(hold_rid),
    "action": "approve"
}, follow_redirects=True)
assert res_appr.status_code == 200

# Verify:
# A. No loan was inserted!
cur.execute("SELECT COUNT(*) FROM Loans WHERE Borrower_ID = :p_uid", {"p_uid": hold_uid})
assert cur.fetchone()[0] == initial_loans, "Loan was prematurely inserted into Loans table!"

# B. Loan_Requests is 'Awaiting Pickup'
cur.execute("SELECT Status FROM Loan_Requests WHERE Request_ID = :rid", {"rid": hold_rid})
req_status = cur.fetchone()[0]
assert req_status == "Awaiting Pickup", f"Expected 'Awaiting Pickup', got {req_status}"

# C. Book_Copies is 'Reserved'
cur.execute("SELECT Status FROM Book_Copies WHERE Copy_ID = :cid", {"cid": hold_cid})
copy_status = cur.fetchone()[0]
assert copy_status == "Reserved", f"Expected 'Reserved', got {copy_status}"
print("PASS: Approval set Request to 'Awaiting Pickup' and Copy to 'Reserved' WITHOUT inserting loan.")

# 2. Student arrives at desk -> Librarian issues physical loan via /issue_loan
res_desk = client.post("/issue_loan", data={
    "copy_id": str(hold_cid),
    "borrower_username": "test_hold_student",
    "due_in_days": "14"
}, follow_redirects=True)
assert res_desk.status_code == 200

# Verify:
# A. Loan now exists in Loans table
cur.execute("SELECT Loan_ID, Copy_ID, Return_Date FROM Loans WHERE Borrower_ID = :p_uid AND Return_Date IS NULL", {"p_uid": hold_uid})
active_loan = cur.fetchone()
assert active_loan is not None, "Loan was not created on physical desk scan!"
desk_lid = active_loan[0]

# B. Copy is now 'Borrowed'
cur.execute("SELECT Status FROM Book_Copies WHERE Copy_ID = :cid", {"cid": hold_cid})
assert cur.fetchone()[0] == "Borrowed"

# C. Loan_Requests 'Awaiting Pickup' request was fulfilled
cur.execute("SELECT Status FROM Loan_Requests WHERE Request_ID = :rid", {"rid": hold_rid})
assert cur.fetchone()[0] == "Fulfilled", "Request was not fulfilled!"
print("PASS: Physical desk checkout issued loan and fulfilled 'Awaiting Pickup' request.")

# Clean up
cur.execute("DELETE FROM Loans WHERE Loan_ID = :lid", {"lid": desk_lid})
cur.execute("DELETE FROM Loan_Requests WHERE Request_ID = :rid", {"rid": hold_rid})
cur.execute("UPDATE Book_Copies SET Status = 'Available' WHERE Copy_ID = :cid", {"cid": hold_cid})
cur.execute("DELETE FROM Users WHERE User_ID = :p_uid", {"p_uid": hold_uid})
conn.commit()

conn.close()
print("\n=====================================================================")
print("ALL ARCHITECTURAL VULNERABILITY FIXES VERIFIED SUCCESSFULLY!")
print("=====================================================================")
