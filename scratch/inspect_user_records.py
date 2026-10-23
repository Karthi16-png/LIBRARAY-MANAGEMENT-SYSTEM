import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cursor = conn.cursor()

cursor.execute("SELECT User_ID, Username, Role FROM Users WHERE User_ID != 0 ORDER BY User_ID")
users = cursor.fetchall()

print(f"{'User_ID':<8} {'Username':<15} {'Role':<10} {'Loans':<8} {'Fines':<8} {'Requests':<10}")
print("-" * 65)

for uid, uname, role in users:
    cursor.execute("SELECT COUNT(*) FROM Loans WHERE Borrower_ID = :u_id", {"u_id": uid})
    loans_cnt = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*) FROM Fines f 
        JOIN Loans l ON f.Loan_ID = l.Loan_ID 
        WHERE l.Borrower_ID = :u_id
    """, {"u_id": uid})
    fines_cnt = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Loan_Requests WHERE Borrower_ID = :u_id", {"u_id": uid})
    req_cnt = cursor.fetchone()[0]
    print(f"{uid:<8} {uname:<15} {role:<10} {loans_cnt:<8} {fines_cnt:<8} {req_cnt:<10}")
