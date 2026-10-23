import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
import oracledb
from app import app

app.config["WTF_CSRF_ENABLED"] = False
app.config["TESTING"] = True
client = app.test_client()

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()

# Find a book that has at least 1 Available copy
cur.execute("""
    SELECT b.Book_ID, b.Title, b.Category_ID, bc.Copy_ID
    FROM Books b
    JOIN Book_Copies bc ON b.Book_ID = bc.Book_ID
    WHERE bc.Status = 'Available'
    FETCH FIRST 1 ROWS ONLY
""")
book_row = cur.fetchone()
print("TEST BOOK:", book_row)
test_bid = book_row[0]
test_title = book_row[1]
test_cat_id = book_row[2]

# Let's find an active Student with 0 active loans
cur.execute("SELECT User_ID, Username, Role FROM Users WHERE User_ID = 120")
stu = cur.fetchone()
print("STUDENT:", stu)
stu_id = stu[0]
stu_name = stu[1]

# Clean up any existing loan requests for this student and book
cur.execute("DELETE FROM Loan_Requests WHERE Borrower_ID = :p_uid AND Book_ID = :bid", {"p_uid": stu_id, "bid": test_bid})
cur.execute("UPDATE Book_Copies SET Status = 'Available' WHERE Book_ID = :bid", {"bid": test_bid})
conn.commit()

# TEST PART 1: Student requests book
print("\n--- 1. Student Requests Book ---")
with client.session_transaction() as sess:
    sess["user_id"] = stu_id
    sess["username"] = stu_name
    sess["role"] = "Student"
    sess["last_activity"] = datetime.now().timestamp()

res = client.post(f"/request_loan/{test_bid}", data={"category_id": test_cat_id}, follow_redirects=True)
print("Request response status:", res.status_code)

cur.execute("SELECT Request_ID, Status FROM Loan_Requests WHERE Borrower_ID = :p_uid AND Book_ID = :bid ORDER BY Request_ID DESC", {"p_uid": stu_id, "bid": test_bid})
req = cur.fetchone()
print("Created Request in DB:", req)
req_id = req[0]

# Student views dashboard
res_dash = client.get("/dashboard")
dash_html = res_dash.data.decode("utf-8", errors="ignore")
print("Dashboard has 'Awaiting Approval':", "Awaiting Approval" in dash_html)
print("Dashboard has 'Rejected':", "Rejected" in dash_html)

# TEST PART 2: Admin approves request
print("\n--- 2. Admin Approves Request ---")
with client.session_transaction() as sess:
    sess["user_id"] = 1
    sess["username"] = "admin"
    sess["role"] = "Admin"
    sess["last_activity"] = datetime.now().timestamp()

res_appr = client.post("/loan_requests", data={"request_id": str(req_id), "action": "approve"}, follow_redirects=True)
cur.execute("SELECT Status FROM Loan_Requests WHERE Request_ID = :rid", {"rid": req_id})
appr_status = cur.fetchone()[0]
print("Request Status in DB after approval:", appr_status)

# Student views dashboard after approval
with client.session_transaction() as sess:
    sess["user_id"] = stu_id
    sess["username"] = stu_name
    sess["role"] = "Student"
    sess["last_activity"] = datetime.now().timestamp()

res_dash_appr = client.get("/dashboard")
dash_appr_html = res_dash_appr.data.decode("utf-8", errors="ignore")
print("Student dashboard after Admin Approve:")
print("  Contains 'Approved & Issued':", "Approved & Issued" in dash_appr_html)
print("  Contains 'Awaiting Pickup':", "Awaiting Pickup" in dash_appr_html)
print("  Contains 'Approved':", "Approved" in dash_appr_html)
print("  Contains 'Rejected':", "Rejected" in dash_appr_html)

# Check what the badge actually says
import re
badges = re.findall(r'<span class="badge badge-[^"]*">(.*?)</span>', dash_appr_html)
print("  All badges on student dashboard:", badges)

# TEST PART 3: Admin rejects request & Student tries to re-request
print("\n--- 3. Testing Rejection & Re-request ---")
# Reset
cur.execute("DELETE FROM Loan_Requests WHERE Request_ID = :rid", {"rid": req_id})
cur.execute("UPDATE Book_Copies SET Status = 'Available' WHERE Book_ID = :bid", {"bid": test_bid})
conn.commit()

# Student requests
with client.session_transaction() as sess:
    sess["user_id"] = stu_id
    sess["username"] = stu_name
    sess["role"] = "Student"
    sess["last_activity"] = datetime.now().timestamp()
client.post(f"/request_loan/{test_bid}", data={"category_id": test_cat_id}, follow_redirects=True)

cur.execute("SELECT Request_ID, Status FROM Loan_Requests WHERE Borrower_ID = :p_uid AND Book_ID = :bid ORDER BY Request_ID DESC", {"p_uid": stu_id, "bid": test_bid})
req2 = cur.fetchone()
req2_id = req2[0]
print("New Request ID:", req2_id)

# Admin rejects
with client.session_transaction() as sess:
    sess["user_id"] = 1
    sess["username"] = "admin"
    sess["role"] = "Admin"
    sess["last_activity"] = datetime.now().timestamp()
client.post("/loan_requests", data={"request_id": str(req2_id), "action": "reject"}, follow_redirects=True)

cur.execute("SELECT Status FROM Loan_Requests WHERE Request_ID = :rid", {"rid": req2_id})
print("Request Status in DB after rejection:", cur.fetchone()[0])

cur.execute("SELECT Copy_ID, Status FROM Book_Copies WHERE Book_ID = :bid", {"bid": test_bid})
print("Copy statuses after rejection in DB:", cur.fetchall())

# Now Student tries to view category page to request again
with client.session_transaction() as sess:
    sess["user_id"] = stu_id
    sess["username"] = stu_name
    sess["role"] = "Student"
    sess["last_activity"] = datetime.now().timestamp()

res_cat = client.get(f"/category/{test_cat_id}")
cat_html = res_cat.data.decode("utf-8", errors="ignore")
print("On category page after rejection:")
print("  Has 'Request Physical Loan':", "Request Physical Loan" in cat_html)
print("  Has 'Currently Out of Stock':", "Currently Out of Stock" in cat_html)
print("  Has 'Request Pending Approval':", "Request Pending Approval" in cat_html)
print("  Has 'Borrowing Blocked':", "Borrowing Blocked" in cat_html)

# Try submitting the request again
res_re_req = client.post(f"/request_loan/{test_bid}", data={"category_id": test_cat_id}, follow_redirects=True)
re_html = res_re_req.data.decode("utf-8", errors="ignore")
alerts = re.findall(r'class="alert[^"]*">(.*?)</div>', re_html, re.DOTALL)
print("Flash alerts on re-request:", alerts)

cur.execute("SELECT Request_ID, Status FROM Loan_Requests WHERE Borrower_ID = :p_uid AND Book_ID = :bid AND Status = 'Pending'", {"p_uid": stu_id, "bid": test_bid})
print("New pending request in DB:", cur.fetchall())

# Cleanup
cur.execute("DELETE FROM Loan_Requests WHERE Borrower_ID = :p_uid AND Book_ID = :bid", {"p_uid": stu_id, "bid": test_bid})
cur.execute("UPDATE Book_Copies SET Status = 'Available' WHERE Book_ID = :bid", {"bid": test_bid})
conn.commit()
conn.close()
