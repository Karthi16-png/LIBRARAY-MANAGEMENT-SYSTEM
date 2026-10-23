import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import oracledb
from app import app

app.config["WTF_CSRF_ENABLED"] = False
app.config["TESTING"] = True
client = app.test_client()

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()

print("=====================================================================")
print("TEST SUITE: Multi-fine, Fine Append, FK Indexes, & Quota Loophole")
print("=====================================================================")

# ---------------------------------------------------------------------------
# TEST 1: Multiple Fines for Single Loan & Unique Constraint Dropped
# ---------------------------------------------------------------------------
print("\n--- 1. Testing Multiple Fines for Single Loan ---")
# Pick or create a loan
cur.execute("SELECT Loan_ID FROM Loans WHERE ROWNUM = 1")
test_lid = cur.fetchone()[0]

cur.execute("SELECT NVL(MAX(Fine_ID), 0) + 1 FROM Fines")
f1_id = cur.fetchone()[0]
f2_id = f1_id + 1

cur.execute("""
    INSERT INTO Fines (Fine_ID, Loan_ID, Fine_Amount, Payment_Status)
    VALUES (:fid, :lid, 25.00, 'Unpaid')
""", {"fid": f1_id, "lid": test_lid})

# Insert second fine for same loan
cur.execute("""
    INSERT INTO Fines (Fine_ID, Loan_ID, Fine_Amount, Payment_Status)
    VALUES (:fid, :lid, 50.00, 'Unpaid')
""", {"fid": f2_id, "lid": test_lid})
conn.commit()

cur.execute("SELECT COUNT(*) FROM Fines WHERE Loan_ID = :lid", {"lid": test_lid})
count_fines = cur.fetchone()[0]
assert count_fines >= 2, "Expected at least 2 fines for the loan"
print(f"PASS: Single loan #{test_lid} successfully holds multiple fine line items.")

# Clean up test fines
cur.execute("BEGIN DBMS_APPLICATION_INFO.SET_CLIENT_INFO('ALLOW_DELETE'); END;")
cur.execute("DELETE FROM Fines WHERE Fine_ID IN (:f1, :f2)", {"f1": f1_id, "f2": f2_id})
cur.execute("BEGIN DBMS_APPLICATION_INFO.SET_CLIENT_INFO(NULL); END;")
conn.commit()

# ---------------------------------------------------------------------------
# TEST 2: Foreign Key Indexes on Loans & Fines
# ---------------------------------------------------------------------------
print("\n--- 2. Testing Foreign Key Indexes in Oracle 21c ---")
cur.execute("""
    SELECT index_name, table_name 
    FROM user_indexes 
    WHERE index_name IN ('IDX_LOANS_BORROWER', 'IDX_LOANS_COPY', 'IDX_FINES_LOAN')
""")
indexes_found = {row[0]: row[1] for row in cur.fetchall()}
print("Indexes found:", indexes_found)
assert "IDX_LOANS_BORROWER" in indexes_found
assert "IDX_LOANS_COPY" in indexes_found
assert "IDX_FINES_LOAN" in indexes_found
print("PASS: All 3 foreign key indexes exist to prevent table locks.")

# ---------------------------------------------------------------------------
# TEST 3: Fine Append on sp_ReturnBook
# ---------------------------------------------------------------------------
print("\n--- 3. Testing Fine Balance Addition on Return ---")
# Create test patron
cur.execute("DELETE FROM Users WHERE Username = 'test_overdue_user'")
conn.commit()
cur.execute("""
    INSERT INTO Users (Username, Email, Password_Hash, Role, Account_Status)
    VALUES ('test_overdue_user', 'overdue@test.edu', 'TestPass@123', 'Student', 'Active')
""")
conn.commit()
cur.execute("SELECT User_ID FROM Users WHERE Username = 'test_overdue_user'")
user_id = cur.fetchone()[0]

cur.execute("SELECT Copy_ID FROM Book_Copies WHERE Status = 'Available' AND ROWNUM = 1")
copy_id = cur.fetchone()[0]

cur.execute("SELECT NVL(MAX(Loan_ID), 0) + 1 FROM Loans")
ret_lid = cur.fetchone()[0]

# Insert loan due 3 days ago (Return_Date IS NULL)
cur.execute("""
    INSERT INTO Loans (Loan_ID, Copy_ID, Borrower_ID, Issued_By, Issue_Date, Due_Date, Return_Date)
    VALUES (:lid, :cid, :p_uid, 1, SYSDATE - 10, SYSDATE - 3, NULL)
""", {"lid": ret_lid, "cid": copy_id, "p_uid": user_id})
cur.execute("UPDATE Book_Copies SET Status = 'Borrowed' WHERE Copy_ID = :cid", {"cid": copy_id})

# Pre-existing fine of Rs. 30 on this loan
cur.execute("SELECT NVL(MAX(Fine_ID), 0) + 1 FROM Fines")
existing_fid = cur.fetchone()[0]
cur.execute("""
    INSERT INTO Fines (Fine_ID, Loan_ID, Fine_Amount, Payment_Status)
    VALUES (:fid, :lid, 30.00, 'Unpaid')
""", {"fid": existing_fid, "lid": ret_lid})
conn.commit()

# Call sp_ReturnBook (overdue 3 days * 10 = Rs. 30 new fine)
# New balance should be 30 + 30 = 60
cur.callproc("LIBRARY_OPS_PKG.sp_ReturnBook", [ret_lid])

cur.execute("SELECT Fine_Amount FROM Fines WHERE Fine_ID = :fid", {"fid": existing_fid})
updated_fine = cur.fetchone()[0]
print(f"Initial fine: Rs. 30.00 | After overdue return: Rs. {updated_fine:.2f}")
assert updated_fine == 60.00, f"Expected 60.00, got {updated_fine}"
print("PASS: Existing unpaid fine amount was appended (30.00 + 30.00 = 60.00).")

# Clean up
cur.execute("BEGIN DBMS_APPLICATION_INFO.SET_CLIENT_INFO('ALLOW_DELETE'); END;")
cur.execute("DELETE FROM Fines WHERE Loan_ID = :lid", {"lid": ret_lid})
cur.execute("BEGIN DBMS_APPLICATION_INFO.SET_CLIENT_INFO(NULL); END;")
cur.execute("DELETE FROM Loans WHERE Loan_ID = :lid", {"lid": ret_lid})
cur.execute("UPDATE Book_Copies SET Status = 'Available' WHERE Copy_ID = :cid", {"cid": copy_id})
conn.commit()

# ---------------------------------------------------------------------------
# TEST 4: Direct Issue Quota Check (Active Loans + Pending Requests >= 3)
# ---------------------------------------------------------------------------
print("\n--- 4. Testing Direct Issue Quota Loophole Guard ---")
# Insert 2 active loans and 1 pending request for test_overdue_user (Total bandwidth = 3)
cur.execute("SELECT Copy_ID FROM Book_Copies WHERE Status = 'Available' AND ROWNUM <= 3")
avail_copies = [r[0] for r in cur.fetchall()]

loan_ids = []
for i in range(2):
    cur.execute("SELECT NVL(MAX(Loan_ID), 0) + 1 FROM Loans")
    new_lid = cur.fetchone()[0]
    loan_ids.append(new_lid)
    cur.execute("""
        INSERT INTO Loans (Loan_ID, Copy_ID, Borrower_ID, Issued_By, Issue_Date, Due_Date, Return_Date)
        VALUES (:lid, :cid, :p_uid, 1, SYSDATE, SYSDATE + 14, NULL)
    """, {"lid": new_lid, "cid": avail_copies[i], "p_uid": user_id})
    cur.execute("UPDATE Book_Copies SET Status = 'Borrowed' WHERE Copy_ID = :cid", {"cid": avail_copies[i]})

# Insert 1 pending loan request
cur.execute("SELECT Book_ID FROM Book_Copies WHERE Copy_ID = :cid", {"cid": avail_copies[2]})
book_for_req = cur.fetchone()[0]
cur.execute("SELECT NVL(MAX(Request_ID), 0) + 1 FROM Loan_Requests")
req_id = cur.fetchone()[0]
cur.execute("""
    INSERT INTO Loan_Requests (Request_ID, Book_ID, Borrower_ID, Request_Date, Status)
    VALUES (:rid, :bid, :p_uid, SYSDATE, 'Pending')
""", {"rid": req_id, "bid": book_for_req, "p_uid": user_id})
conn.commit()

# Total bandwidth is now: 2 active loans + 1 pending request = 3
# Attempting to issue a 3rd copy directly via /issue_loan
with client.session_transaction() as sess:
    sess["user_id"] = 1
    sess["username"] = "admin"
    sess["role"] = "Admin"

res_iss = client.post("/issue_loan", data={
    "copy_id": str(avail_copies[2]),
    "borrower_username": "test_overdue_user",
    "due_in_days": "14"
}, follow_redirects=True)
html_iss = res_iss.data.decode("utf-8")
assert "Borrowing Prohibited" in html_iss and ("quota" in html_iss.lower() or "bandwidth" in html_iss.lower()), "Librarian was able to bypass quota when patron has 2 active loans + 1 pending request!"
print("PASS: /issue_loan correctly blocked when patron has 2 active loans + 1 pending request.")

# Clean up
for lid in loan_ids:
    cur.execute("DELETE FROM Loans WHERE Loan_ID = :lid", {"lid": lid})
cur.execute("DELETE FROM Loan_Requests WHERE Request_ID = :rid", {"rid": req_id})
for cid in avail_copies[:2]:
    cur.execute("UPDATE Book_Copies SET Status = 'Available' WHERE Copy_ID = :cid", {"cid": cid})
cur.execute("DELETE FROM Users WHERE User_ID = :p_uid", {"p_uid": user_id})
conn.commit()

conn.close()
print("\n=====================================================================")
print("ALL NEW ARCHITECTURAL FIXES TESTED AND PASSED SUCCESSFULLY!")
print("=====================================================================")
