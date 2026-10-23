import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cursor = conn.cursor()

# Test 1: unpaid_fines_list
cursor.execute("""
    SELECT f.Fine_ID, f.Fine_Amount, f.Payment_Status,
           u.Username AS borrower_name, u.Email AS borrower_email,
           NVL(b.Title, 'Archived/Deleted Title') AS book_title, l.Loan_ID, l.Due_Date
    FROM Fines f
    JOIN Loans l ON f.Loan_ID = l.Loan_ID
    JOIN Users u ON l.Borrower_ID = u.User_ID
    LEFT JOIN Book_Copies bc ON l.Copy_ID = bc.Copy_ID
    LEFT JOIN Books b ON bc.Book_ID = b.Book_ID
    WHERE f.Payment_Status = 'Unpaid'
    ORDER BY f.Fine_Amount DESC
""")
res1 = cursor.fetchall()
print(f"Test 1 (unpaid_fines_list) passed: {len(res1)} records found.")

# Test 2: my_fines query
cursor.execute("""
    SELECT 
        f.Fine_ID,
        f.Fine_Amount,
        f.Payment_Status,
        l.Loan_ID,
        l.Issue_Date,
        l.Due_Date,
        l.Return_Date,
        NVL(b.Title, 'Archived/Deleted Title') AS book_title,
        NVL(b.Title, 'Archived/Deleted Title') AS title,
        bc.Copy_ID
    FROM Fines f
    JOIN Loans l ON f.Loan_ID = l.Loan_ID
    LEFT JOIN Book_Copies bc ON l.Copy_ID = bc.Copy_ID
    LEFT JOIN Books b ON bc.Book_ID = b.Book_ID
    WHERE l.Borrower_ID = :borrower_id
    ORDER BY f.Fine_ID DESC
""", {"borrower_id": 1})
res2 = cursor.fetchall()
print(f"Test 2 (my_fines) passed: {len(res2)} records found.")

conn.close()
