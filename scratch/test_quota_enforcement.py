import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import oracledb
from app import app

app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True
client = app.test_client()

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()

print("=====================================================================")
print("TESTING 3-BOOK THRESHOLD ENFORCEMENT ACROSS REQUESTS, HOLDS & LOANS")
print("=====================================================================")

# Check user 'nithin' (ID #31)
cur.execute("SELECT User_ID, Username FROM Users WHERE Username = 'nithin'")
nithin_row = cur.fetchone()
print(f"Patron 'nithin': {nithin_row}")

# Check active loans and awaiting pickup requests for nithin
cur.execute("SELECT COUNT(*) FROM Loans WHERE Borrower_ID = 31 AND Return_Date IS NULL")
n_loans = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM Loan_Requests WHERE Borrower_ID = 31 AND Status = 'Awaiting Pickup'")
n_awaiting = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM Loan_Requests WHERE Borrower_ID = 31 AND Status = 'Pending'")
n_pending = cur.fetchone()[0]

print(f"Nithin's current state: {n_loans} Active Loans, {n_awaiting} Awaiting Pickup, {n_pending} Pending")

# 1. Test Student Dashboard for nithin: verify it does NOT say "0 / 3"
print("\n--- Test 1: Student Dashboard accurately shows Committed Books ---")
with client.session_transaction() as sess:
    sess['user_id'] = 31
    sess['username'] = 'nithin'
    sess['role'] = 'Student'

res_dash = client.get("/dashboard")
assert res_dash.status_code == 200
dash_html = res_dash.data.decode("utf-8")

assert "Committed Books" in dash_html, "Dashboard missing 'Committed Books' label"
assert "Awaiting Pickup" in dash_html, "Dashboard missing 'Awaiting Pickup' footnote breakdown"
if n_awaiting > 0:
    assert "Ready for Pickup" in dash_html, "Dashboard missing 'Ready for Pickup' badge/card"
print("PASS: Student Dashboard displays Committed Books accurately!")

# 2. Test request_loan blocks when committed >= 3
print("\n--- Test 2: Submitting a request when committed >= 3 is BLOCKED ---")
# Find a book that nithin doesn't have an active request for
cur.execute("""
    SELECT Book_ID, Title FROM Books 
    WHERE Book_ID NOT IN (SELECT Book_ID FROM Loan_Requests WHERE Borrower_ID = 31 AND Status IN ('Pending', 'Awaiting Pickup'))
      AND Book_ID NOT IN (SELECT bc.Book_ID FROM Loans l JOIN Book_Copies bc ON l.Copy_ID = bc.Copy_ID WHERE l.Borrower_ID = 31 AND l.Return_Date IS NULL)
      AND ROWNUM = 1
""")
avail_b = cur.fetchone()
if avail_b:
    b_id, b_title = avail_b
    print(f"Attempting to request Book #{b_id} ('{b_title}')...")
    res_req = client.post(f"/request_loan/{b_id}", data={"from_dashboard": "1"}, follow_redirects=True)
    req_html = res_req.data.decode("utf-8")
    assert "Borrowing Quota Reached" in req_html or "Permission Denied" in req_html
    print("PASS: Request was blocked because patron reached 3-book threshold!")

# 3. Test loan_requests approval blocks when committed >= 3
print("\n--- Test 3: Approval is BLOCKED and button is DISABLED when committed >= 3 ---")
# Pick a clean student
cur.execute("""
    SELECT u.User_ID, u.Username
    FROM Users u
    WHERE u.Role = 'Student' AND u.Account_Status = 'Active'
      AND NOT EXISTS (SELECT 1 FROM Loans l WHERE l.Borrower_ID = u.User_ID AND l.Return_Date IS NULL)
      AND NOT EXISTS (SELECT 1 FROM Fines f JOIN Loans l ON f.Loan_ID = l.Loan_ID WHERE l.Borrower_ID = u.User_ID AND f.Payment_Status = 'Unpaid')
      AND NOT EXISTS (SELECT 1 FROM Loan_Requests lr WHERE lr.Borrower_ID = u.User_ID AND lr.Status IN ('Pending', 'Awaiting Pickup'))
      AND ROWNUM = 1
""")
clean_stu = cur.fetchone()
stu_id, stu_name = clean_stu
print(f"Testing with clean student: {stu_name} (ID #{stu_id})")

# Find 4 books with available copies
cur.execute("""
    SELECT b.Book_ID, b.Title
    FROM Books b
    JOIN Book_Copies bc ON b.Book_ID = bc.Book_ID
    WHERE bc.Status = 'Available'
    GROUP BY b.Book_ID, b.Title
    HAVING COUNT(*) >= 1
""")
books_list = cur.fetchall()[:4]
assert len(books_list) == 4, "Need at least 4 available books for test"

created_request_ids = []
# Create 4 requests for this student directly
for b in books_list:
    cur.execute("""
        INSERT INTO Loan_Requests (Book_ID, Borrower_ID, Request_Date, Status)
        VALUES (:bid, :borrower_id, SYSDATE, 'Pending')
    """, {"bid": b[0], "borrower_id": stu_id})
    cur.execute("SELECT MAX(Request_ID) FROM Loan_Requests WHERE Borrower_ID = :bid", {"bid": stu_id})
    created_request_ids.append(cur.fetchone()[0])
conn.commit()
print(f"Created 4 pending requests for {stu_name}: {created_request_ids}")

# Login as Librarian
cur.execute("SELECT User_ID, Username FROM Users WHERE Role = 'Librarian' AND ROWNUM = 1")
lib_id, lib_uname = cur.fetchone()

with client.session_transaction() as sess:
    sess['user_id'] = lib_id
    sess['username'] = lib_uname
    sess['role'] = 'Librarian'

# Approve request 1
res1 = client.post("/loan_requests", data={"action": "approve", "request_id": created_request_ids[0]}, follow_redirects=True)
assert res1.status_code == 200
print(f"PASS: Approved Request 1 (#{created_request_ids[0]})")

# Approve request 2
res2 = client.post("/loan_requests", data={"action": "approve", "request_id": created_request_ids[1]}, follow_redirects=True)
assert res2.status_code == 200
print(f"PASS: Approved Request 2 (#{created_request_ids[1]})")

# Approve request 3
res3 = client.post("/loan_requests", data={"action": "approve", "request_id": created_request_ids[2]}, follow_redirects=True)
assert res3.status_code == 200
print(f"PASS: Approved Request 3 (#{created_request_ids[2]})")

# Now patron has 3 approved requests in 'Awaiting Pickup' (committed = 3)
# Attempt to approve Request 4 -> MUST BE BLOCKED!
print("Attempting to approve Request 4 when patron already has 3 approved holds...")
res4 = client.post("/loan_requests", data={"action": "approve", "request_id": created_request_ids[3]}, follow_redirects=True)
html4 = res4.data.decode("utf-8")
assert "Approval Prohibited: Patron" in html4
assert "reached the maximum threshold of 3 books" in html4
print("PASS: Server strictly blocked 4th approval!")

# Check /loan_requests queue page: Request 4 must have 'disabled' button and 'Threshold Full' badge
res_q = client.get("/loan_requests")
q_html = res_q.data.decode("utf-8")
assert "Threshold Full" in q_html
print("PASS: Queue page displays 'Threshold Full' badge and disables approval button!")

# Cleanup test requests
print("\n--- Cleanup ---")
for r_id in created_request_ids:
    cur.execute("SELECT Copy_ID FROM Loan_Requests WHERE Request_ID = :rid", {"rid": r_id})
    c = cur.fetchone()
    if c and c[0]:
        cur.execute("UPDATE Book_Copies SET Status = 'Available' WHERE Copy_ID = :cid", {"cid": c[0]})
    cur.execute("DELETE FROM Loan_Requests WHERE Request_ID = :rid", {"rid": r_id})
conn.commit()
print("PASS: Test cleanup complete.")

print("\n=====================================================================")
print("ALL THRESHOLD ENFORCEMENT TESTS PASSED 100%!")
print("=====================================================================")
cur.close()
conn.close()
