import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()

cur.execute("""
    UPDATE Loan_Requests lr
    SET Copy_ID = (
        SELECT MIN(Copy_ID) 
        FROM Book_Copies bc 
        WHERE bc.Book_ID = lr.Book_ID AND bc.Status IN ('Reserved', 'Available')
    )
    WHERE lr.Status = 'Awaiting Pickup' AND lr.Copy_ID IS NULL
""")
conn.commit()
print(f"Updated {cur.rowcount} rows with reserved copy IDs")

cur.execute("""
    SELECT lr.Request_ID, lr.Book_ID, lr.Borrower_ID, lr.Status, lr.Copy_ID
    FROM Loan_Requests lr
    WHERE lr.Status = 'Awaiting Pickup'
""")
for r in cur.fetchall():
    print(r)

cur.close()
conn.close()
