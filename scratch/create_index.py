import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()
try:
    cur.execute("""
        CREATE UNIQUE INDEX uq_active_requests ON Loan_Requests (
            CASE WHEN Status IN ('Pending', 'Awaiting Pickup') THEN Borrower_ID ELSE NULL END, 
            CASE WHEN Status IN ('Pending', 'Awaiting Pickup') THEN Book_ID ELSE NULL END
        )
    """)
    print("SUCCESS: uq_active_requests created.")
except Exception as e:
    print("ERROR:", e)
conn.close()
