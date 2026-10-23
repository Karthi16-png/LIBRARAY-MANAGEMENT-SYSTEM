import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()

# 1. Let's find a test book and a test student
cur.execute("SELECT User_ID, Username FROM Users WHERE Role = 'Student' AND Username = 'student'")
student_user = cur.fetchone()
print("Student:", student_user)

cur.execute("""
    SELECT b.Book_ID, b.Title, 
           (SELECT COUNT(*) FROM Book_Copies bc WHERE bc.Book_ID = b.Book_ID AND bc.Status = 'Available') as avail,
           (SELECT COUNT(*) FROM Book_Copies bc WHERE bc.Book_ID = b.Book_ID AND bc.Status = 'Reserved') as resv
    FROM Books b
    WHERE ROWNUM <= 5
""")
for r in cur.fetchall():
    print("Book:", r)

conn.close()
