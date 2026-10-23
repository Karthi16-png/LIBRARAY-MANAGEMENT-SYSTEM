import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()

cur.execute("SELECT Status, COUNT(*) FROM Book_Copies GROUP BY Status")
print("BOOK COPIES BY STATUS:", cur.fetchall())

cur.execute("SELECT Status, COUNT(*) FROM Loan_Requests GROUP BY Status")
print("LOAN REQUESTS BY STATUS:", cur.fetchall())

cur.execute("""
    SELECT bc.Copy_ID, bc.Book_ID, bc.Status, b.Title 
    FROM Book_Copies bc 
    JOIN Books b ON bc.Book_ID = b.Book_ID 
    WHERE bc.Status = 'Reserved'
""")
print("RESERVED COPIES:", cur.fetchall())

cur.execute("""
    SELECT lr.Request_ID, lr.Book_ID, lr.Borrower_ID, lr.Status, b.Title, u.Username
    FROM Loan_Requests lr
    JOIN Books b ON lr.Book_ID = b.Book_ID
    JOIN Users u ON lr.Borrower_ID = u.User_ID
    ORDER BY lr.Request_ID DESC
    FETCH FIRST 15 ROWS ONLY
""")
print("LATEST LOAN REQUESTS:")
for r in cur.fetchall():
    print("  ", r)

conn.close()
