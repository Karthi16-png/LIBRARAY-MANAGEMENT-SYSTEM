import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cursor = conn.cursor()

queries = [
    (
        "1. Display all registered library users",
        "SELECT User_ID, Username, Role, Email, Account_Status FROM Users WHERE User_ID != 0 ORDER BY User_ID",
        "Retrieves all active patron, staff, and administrator accounts registered in the library directory."
    ),
    (
        "2. List all catalog books with category and publisher details",
        """SELECT b.Book_ID, b.Title, b.ISBN, c.Name AS Category, p.Name AS Publisher, b.Publication_Year
FROM Books b
JOIN Categories c ON b.Category_ID = c.Category_ID
JOIN Publishers p ON b.Publisher_ID = p.Publisher_ID
ORDER BY b.Book_ID""",
        "Performs a multi-table INNER JOIN across Books, Categories, and Publishers to display complete bibliographic metadata."
    ),
    (
        "3. Inventory copy count and physical availability status per book title",
        """SELECT b.Book_ID, b.Title, 
       COUNT(bc.Copy_ID) AS Total_Copies,
       SUM(CASE WHEN bc.Status = 'Available' THEN 1 ELSE 0 END) AS Available_Copies,
       SUM(CASE WHEN bc.Status = 'Borrowed' THEN 1 ELSE 0 END) AS Borrowed_Copies
FROM Books b
LEFT JOIN Book_Copies bc ON b.Book_ID = bc.Book_ID
GROUP BY b.Book_ID, b.Title
ORDER BY b.Book_ID""",
        "Aggregates total physical shelf inventory and tracks real-time availability ratios for each catalog title."
    ),
    (
        "4. Books and their designated author attributions",
        """SELECT b.Title, a.First_Name || ' ' || a.Last_Name AS Author_Name
FROM Books b
JOIN Book_Authors ba ON b.Book_ID = ba.Book_ID
JOIN Authors a ON ba.Author_ID = a.Author_ID
ORDER BY b.Title, Author_Name""",
        "Traverses the many-to-many Book_Authors bridge entity to link book titles to their respective authors."
    ),
    (
        "5. Complete loan history for patron 'karthik'",
        """SELECT l.Loan_ID, b.Title, bc.Copy_ID, l.Issue_Date, l.Due_Date, l.Return_Date
FROM Loans l
JOIN Book_Copies bc ON l.Copy_ID = bc.Copy_ID
JOIN Books b ON bc.Book_ID = b.Book_ID
JOIN Users u ON l.Borrower_ID = u.User_ID
WHERE LOWER(u.Username) = 'karthik'
ORDER BY l.Loan_ID""",
        "Displays personalized circulation check-out records and historical return timelines for a specific student patron."
    ),
    (
        "6. Summary of overdue fines assessed across borrowers",
        """SELECT u.Username, u.Role, COUNT(f.Fine_ID) AS Total_Fines, 
       SUM(f.Fine_Amount) AS Total_Amount, f.Payment_Status
FROM Fines f
JOIN Loans l ON f.Loan_ID = l.Loan_ID
JOIN Users u ON l.Borrower_ID = u.User_ID
GROUP BY u.Username, u.Role, f.Payment_Status
ORDER BY Total_Amount DESC""",
        "Aggregates financial penalties grouped by patron and payment status (Paid vs Unpaid)."
    ),
    (
        "7. Patrons holding multiple active or completed loans",
        """SELECT u.Username, u.Role, COUNT(*) AS Total_Loans
FROM Loans l
JOIN Users u ON l.Borrower_ID = u.User_ID
GROUP BY u.Username, u.Role
HAVING COUNT(*) > 1
ORDER BY Total_Loans DESC""",
        "Employs a HAVING clause to identify frequent library users with multiple borrowing transactions."
    ),
    (
        "8. Total revenue collected by payment status",
        """SELECT Payment_Status, COUNT(*) AS Transaction_Count, 
       SUM(Fine_Amount) AS Total_Revenue
FROM Fines
GROUP BY Payment_Status
ORDER BY Total_Revenue DESC""",
        "Calculates revenue streams collected vs outstanding liabilities in the fines ledger."
    ),
    (
        "9. Average book publication year by category",
        """SELECT c.Name AS Category, ROUND(AVG(b.Publication_Year), 0) AS Avg_Year, 
       COUNT(b.Book_ID) AS Total_Books
FROM Categories c
JOIN Books b ON c.Category_ID = b.Category_ID
GROUP BY c.Name
ORDER BY Avg_Year DESC""",
        "Uses AVG and ROUND aggregate functions to evaluate recency and depth of catalog titles per academic discipline."
    ),
    (
        "10. Books published above the catalog's average publication year",
        """SELECT Title, Publication_Year
FROM Books
WHERE Publication_Year > (SELECT AVG(Publication_Year) FROM Books)
ORDER BY Publication_Year DESC""",
        "Demonstrates a scalar subquery in the WHERE clause to isolate modern, recent publications."
    ),
    (
        "11. Patrons with zero active or pending loans",
        """SELECT u.User_ID, u.Username, u.Role
FROM Users u
WHERE u.Role IN ('Student', 'Staff')
  AND NOT EXISTS (
      SELECT 1 FROM Loans l 
      WHERE l.Borrower_ID = u.User_ID AND l.Return_Date IS NULL
  )
ORDER BY u.User_ID""",
        "Uses a correlated NOT EXISTS subquery to find eligible patrons currently holding zero active physical loans."
    ),
    (
        "12. Categories and their assigned catalog count (including empty sections)",
        """SELECT c.Name AS Category, c.Section_Code, COUNT(b.Book_ID) AS Book_Count
FROM Categories c
LEFT JOIN Books b ON c.Category_ID = b.Category_ID
GROUP BY c.Name, c.Section_Code
ORDER BY Book_Count DESC""",
        "Applies a LEFT OUTER JOIN to preserve all classification categories even if no books are currently assigned."
    ),
    (
        "13. Publishers associated with multiple published catalog titles",
        """SELECT p.Name AS Publisher, COUNT(b.Book_ID) AS Title_Count
FROM Publishers p
JOIN Books b ON p.Publisher_ID = b.Publisher_ID
GROUP BY p.Name
HAVING COUNT(b.Book_ID) >= 2
ORDER BY Title_Count DESC""",
        "Identifies major publishing partners supplying the academic repository."
    ),
    (
        "14. Most expensive fine assessed in library history",
        """SELECT f.Fine_ID, u.Username, b.Title, f.Fine_Amount, f.Payment_Status
FROM Fines f
JOIN Loans l ON f.Loan_ID = l.Loan_ID
JOIN Users u ON l.Borrower_ID = u.User_ID
JOIN Book_Copies bc ON l.Copy_ID = bc.Copy_ID
JOIN Books b ON bc.Book_ID = b.Book_ID
WHERE f.Fine_Amount = (SELECT MAX(Fine_Amount) FROM Fines)""",
        "Employs a MAX subquery to pinpoint the highest penalty recorded in the system."
    ),
    (
        "15. End-to-end circulation audit linking Patron, Book, Loan, and Fine",
        """SELECT l.Loan_ID, u.Username AS Patron, b.Title, 
       TO_CHAR(l.Issue_Date, 'YYYY-MM-DD') AS Issued,
       TO_CHAR(l.Return_Date, 'YYYY-MM-DD') AS Returned,
       NVL(f.Fine_Amount, 0) AS Fine, NVL(f.Payment_Status, 'None') AS Status
FROM Loans l
JOIN Users u ON l.Borrower_ID = u.User_ID
JOIN Book_Copies bc ON l.Copy_ID = bc.Copy_ID
JOIN Books b ON bc.Book_ID = b.Book_ID
LEFT JOIN Fines f ON l.Loan_ID = f.Loan_ID
WHERE ROWNUM <= 8
ORDER BY l.Loan_ID""",
        "Integrates multi-table joins and NULL value conversion (NVL) to produce a comprehensive audit ledger."
    ),
    (
        "16. Total fine liabilities and payments per patron",
        """SELECT u.Username,
       NVL(SUM(CASE WHEN f.Payment_Status = 'Paid' THEN f.Fine_Amount ELSE 0 END), 0) AS Paid_Total,
       NVL(SUM(CASE WHEN f.Payment_Status = 'Unpaid' THEN f.Fine_Amount ELSE 0 END), 0) AS Unpaid_Total
FROM Users u
JOIN Loans l ON u.User_ID = l.Borrower_ID
LEFT JOIN Fines f ON l.Loan_ID = f.Loan_ID
WHERE u.Role IN ('Student', 'Staff')
GROUP BY u.Username
ORDER BY Paid_Total DESC""",
        "Aggregates total customer lifetime spend vs current outstanding liabilities across all patrons."
    ),
    (
        "17. Books that have never received hold requests",
        """SELECT Book_ID, Title, ISBN
FROM Books
WHERE Book_ID NOT IN (
    SELECT DISTINCT Book_ID FROM Loan_Requests WHERE Book_ID IS NOT NULL
)""",
        "Uses a NOT IN subquery to identify titles with zero queue requests."
    ),
    (
        "18. Audit log chronological security feed",
        """SELECT Log_ID, Action_Type, Target_User, Performed_By, 
       TO_CHAR(Log_Date, 'YYYY-MM-DD HH24:MI') AS Log_Time, Details
FROM Audit_Logs
ORDER BY Log_ID DESC
FETCH FIRST 8 ROWS ONLY""",
        "Extracts timestamped administrative actions and system security events ordered chronologically."
    )
]

print("Executing all 18 queries...")
results_data = []

for title, sql, purpose in queries:
    cursor.execute(sql)
    col_names = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    
    # Format rows nicely
    formatted_rows = []
    for r in rows:
        formatted_r = []
        for v in r:
            if v is None:
                formatted_r.append("NULL")
            elif hasattr(v, "strftime"):
                formatted_r.append(v.strftime("%Y-%m-%d"))
            else:
                formatted_r.append(str(v))
        formatted_rows.append(formatted_r)
        
    results_data.append({
        "title": title,
        "sql": sql.strip(),
        "purpose": purpose,
        "columns": col_names,
        "rows": formatted_rows
    })

print(f"Successfully executed all {len(results_data)} queries!")

# Save as python json or data module for the docx generator
import json
with open("scratch/query_results.json", "w", encoding="utf-8") as f:
    json.dump(results_data, f, indent=2)

print("Saved to scratch/query_results.json")
