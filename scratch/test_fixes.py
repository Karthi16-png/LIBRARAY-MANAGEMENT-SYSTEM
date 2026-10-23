import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()

# Test 1: Check uq_active_requests
print("Testing uq_active_requests unique index...")
try:
    cur.execute("SELECT User_ID FROM Users WHERE ROWNUM = 1")
    uid = cur.fetchone()[0]
    cur.execute("SELECT Book_ID FROM Books WHERE ROWNUM = 1")
    bid = cur.fetchone()[0]
    
    # Clean up any existing request for this pair first
    cur.execute("DELETE FROM Loan_Requests WHERE Borrower_ID = :borrower_id AND Book_ID = :bid", {"borrower_id": uid, "bid": bid})
    conn.commit()

    cur.execute("INSERT INTO Loan_Requests (Book_ID, Borrower_ID, Request_Date, Status) VALUES (:bid, :borrower_id, SYSDATE, 'Pending')", {"bid": bid, "borrower_id": uid})
    try:
        cur.execute("INSERT INTO Loan_Requests (Book_ID, Borrower_ID, Request_Date, Status) VALUES (:bid, :borrower_id, SYSDATE, 'Pending')", {"bid": bid, "borrower_id": uid})
        print("FAIL: Duplicate request allowed!")
    except oracledb.IntegrityError as e:
        print("SUCCESS: IntegrityError caught for duplicate active request ->", e)
finally:
    cur.execute("DELETE FROM Loan_Requests WHERE Borrower_ID = :borrower_id AND Book_ID = :bid", {"borrower_id": uid, "bid": bid})
    conn.commit()

# Test 2: Check Audit_Logs insert
print("Testing Audit_Logs insertion for LOAN_DELETED...")
cur.execute("""
    INSERT INTO Audit_Logs (Action_Type, Target_User, Performed_By, Log_Date, Details)
    VALUES ('LOAN_DELETED', '1', '1', SYSDATE, 'Test Loan ID #999 deletion audit entry')
""")
conn.commit()
cur.execute("SELECT Log_ID, Action_Type, Details FROM Audit_Logs WHERE Action_Type = 'LOAN_DELETED' AND ROWNUM = 1")
print("SUCCESS: Audit log verified ->", cur.fetchone())

conn.close()
