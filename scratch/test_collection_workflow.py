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
print("TESTING FULL STUDENT COLLECTION & DESK HANDOVER WORKFLOW")
print("=====================================================================")

# 1. Pick an active clean student with 0 active loans and 0 fines
cur.execute("""
    SELECT u.User_ID, u.Username
    FROM Users u
    WHERE u.Role = 'Student'
      AND u.Account_Status = 'Active'
      AND NOT EXISTS (SELECT 1 FROM Loans l WHERE l.Borrower_ID = u.User_ID AND l.Return_Date IS NULL)
      AND NOT EXISTS (SELECT 1 FROM Fines f JOIN Loans l ON f.Loan_ID = l.Loan_ID WHERE l.Borrower_ID = u.User_ID AND f.Payment_Status = 'Unpaid')
      AND NOT EXISTS (SELECT 1 FROM Loan_Requests lr WHERE lr.Borrower_ID = u.User_ID AND lr.Status IN ('Pending', 'Awaiting Pickup'))
      AND ROWNUM = 1
""")
stu_row = cur.fetchone()
assert stu_row is not None, "No clean student found for test"
stu_id, stu_username = stu_row
print(f"Test Student: {stu_username} (ID #{stu_id})")

# 2. Pick a book with available copies
cur.execute("""
    SELECT b.Book_ID, b.Title, bc.Copy_ID
    FROM Books b
    JOIN Book_Copies bc ON b.Book_ID = bc.Book_ID
    WHERE bc.Status = 'Available' AND ROWNUM = 1
""")
book_row = cur.fetchone()
assert book_row is not None, "No book with available copies found"
test_book_id, test_book_title, test_copy_id = book_row
print(f"Test Book: '{test_book_title}' (Book ID #{test_book_id}, Available Copy #{test_copy_id})")

# 3. Student requests the book
print("\n--- Step 1: Student submits loan request ---")
with client.session_transaction() as sess:
    sess['user_id'] = stu_id
    sess['username'] = stu_username
    sess['role'] = 'Student'

res_req = client.post(f"/request_loan/{test_book_id}", data={"from_dashboard": "1"}, follow_redirects=True)
assert res_req.status_code == 200

cur.execute("SELECT Request_ID, Status FROM Loan_Requests WHERE Borrower_ID = :bid AND Book_ID = :book_id AND Status = 'Pending'", {"bid": stu_id, "book_id": test_book_id})
created_req = cur.fetchone()
assert created_req is not None, "Pending request was not created"
req_id = created_req[0]
print(f"PASS: Created Request #{req_id} with Status = 'Pending'")

# 4. Librarian visits /loan_requests and approves the request
print("\n--- Step 2: Librarian approves request ---")
cur.execute("SELECT User_ID, Username FROM Users WHERE Role = 'Librarian' AND ROWNUM = 1")
lib_user = cur.fetchone()
lib_id, lib_username = lib_user

with client.session_transaction() as sess:
    sess['user_id'] = lib_id
    sess['username'] = lib_username
    sess['role'] = 'Librarian'

res_appr = client.post("/loan_requests", data={"action": "approve", "request_id": req_id}, follow_redirects=True)
assert res_appr.status_code == 200

cur.execute("SELECT Status, Copy_ID FROM Loan_Requests WHERE Request_ID = :rid", {"rid": req_id})
appr_row = cur.fetchone()
assert appr_row[0] == "Awaiting Pickup", f"Expected 'Awaiting Pickup', got {appr_row[0]}"
assigned_copy = appr_row[1]
assert assigned_copy is not None, "Expected Copy_ID to be assigned on approval"
print(f"PASS: Request #{req_id} approved -> Status = 'Awaiting Pickup', Assigned Copy #{assigned_copy}")

# 5. Check Librarian /loan_requests page contains "Circulation Desk: Ready for Physical Collection"
print("\n--- Step 3: Verify Collection Desk in /loan_requests ---")
res_queue = client.get("/loan_requests")
assert res_queue.status_code == 200
queue_html = res_queue.data.decode("utf-8")
assert "Circulation Desk: Ready for Physical Collection" in queue_html
assert f"#REQ-{req_id}" in queue_html
assert f"Copy #{assigned_copy}" in queue_html
assert stu_username in queue_html
assert "Hand Over &amp; Confirm Collection" in queue_html
print(f"PASS: Librarian Collection Desk shows Request #{req_id} for {stu_username} with Copy #{assigned_copy}")

# 6. Check Student Dashboard displays "Approved - Ready for Pickup" with Copy ID
print("\n--- Step 4: Verify Student Dashboard before collection ---")
with client.session_transaction() as sess:
    sess['user_id'] = stu_id
    sess['username'] = stu_username
    sess['role'] = 'Student'

res_stu_dash = client.get("/dashboard")
assert res_stu_dash.status_code == 200
stu_html = res_stu_dash.data.decode("utf-8")
assert "Approved – Ready for Pickup" in stu_html or "Approved &ndash; Ready for Pickup" in stu_html
assert f"Copy #{assigned_copy}" in stu_html
assert "Collect at Desk" in stu_html
print(f"PASS: Student Dashboard informs student: Copy #{assigned_copy} &bull; Collect at Desk")

# 7. Student visits desk: Librarian clicks "Hand Over & Confirm Collection"
print("\n--- Step 5: Librarian confirms collection at Circulation Desk ---")
with client.session_transaction() as sess:
    sess['user_id'] = lib_id
    sess['username'] = lib_username
    sess['role'] = 'Librarian'

res_collect = client.post("/loan_requests", data={"action": "confirm_pickup", "request_id": req_id}, follow_redirects=True)
assert res_collect.status_code == 200
collect_html = res_collect.data.decode("utf-8")
assert "Collection Confirmed!" in collect_html
print("PASS: Handover action processed successfully!")

# 8. Verify database state
print("\n--- Step 6: Verify Database Records After Collection ---")
# A. Loan_Requests is 'Fulfilled'
cur.execute("SELECT Status, Copy_ID FROM Loan_Requests WHERE Request_ID = :rid", {"rid": req_id})
final_req = cur.fetchone()
assert final_req[0] == "Fulfilled", f"Expected 'Fulfilled', got {final_req[0]}"
print(f"  -> Loan_Requests #{req_id} Status is 'Fulfilled'")

# B. Book_Copies is 'Borrowed'
cur.execute("SELECT Status FROM Book_Copies WHERE Copy_ID = :cid", {"cid": assigned_copy})
copy_status = cur.fetchone()[0]
assert copy_status == "Borrowed", f"Expected 'Borrowed', got {copy_status}"
print(f"  -> Book_Copies #{assigned_copy} Status is 'Borrowed'")

# C. Loans table has new active loan
cur.execute("""
    SELECT Loan_ID, Copy_ID, Borrower_ID, Issue_Date, Due_Date, Return_Date
    FROM Loans 
    WHERE Borrower_ID = :bid AND Copy_ID = :cid AND Return_Date IS NULL
""", {"bid": stu_id, "cid": assigned_copy})
loan_row = cur.fetchone()
assert loan_row is not None, "Active loan record was not created in Loans table"
loan_id, l_cid, l_bid, l_issue, l_due, l_ret = loan_row
print(f"  -> Loans table recorded Loan #{loan_id}: Issue Date = {l_issue}, Due Date = {l_due}")

# D. Audit_Logs recorded collection event
cur.execute("""
    SELECT Action_Type, Target_User, Performed_By, Details
    FROM Audit_Logs
    WHERE Action_Type = 'BOOK_COLLECTED' AND Target_User = :u
    ORDER BY Log_ID DESC
""", {"u": stu_username})
audit_row = cur.fetchone()
assert audit_row is not None, "Audit_Logs record missing"
print(f"  -> Audit_Logs verified: {audit_row[0]} for {audit_row[1]} by {audit_row[2]}")

# 9. Verify Student Dashboard after collection: shows active loan and collected badge
print("\n--- Step 7: Verify Student Dashboard after collection ---")
with client.session_transaction() as sess:
    sess['user_id'] = stu_id
    sess['username'] = stu_username
    sess['role'] = 'Student'

res_stu_dash2 = client.get("/dashboard")
stu_html2 = res_stu_dash2.data.decode("utf-8")
assert "Collected &amp; Issued" in stu_html2 or "Collected & Issued" in stu_html2
assert f"#LN-{loan_id}" in stu_html2
assert "Active Loan" in stu_html2
print(f"PASS: Student Dashboard displays active Loan #LN-{loan_id} with collection date and due date!")

# Clean up test artifacts
print("\n--- Cleanup ---")
cur.execute("DELETE FROM Loans WHERE Loan_ID = :lid", {"lid": loan_id})
cur.execute("UPDATE Book_Copies SET Status = 'Available' WHERE Copy_ID = :cid", {"cid": assigned_copy})
cur.execute("DELETE FROM Loan_Requests WHERE Request_ID = :rid", {"rid": req_id})
conn.commit()
print("PASS: Cleanup completed.")

print("\n=====================================================================")
print("ALL TESTS PASSED! FULL COLLECTION WORKFLOW VERIFIED END-TO-END!")
print("=====================================================================")
cur.close()
conn.close()
