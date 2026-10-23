import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cursor = conn.cursor()

tables = [
    "USERS", "CATEGORIES", "PUBLISHERS", "AUTHORS", "BOOKS", 
    "BOOK_AUTHORS", "BOOK_COPIES", "LOANS", "FINES", "LOAN_REQUESTS", "AUDIT_LOGS"
]

print("CURRENT TABLE COUNTS:")
for t in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cursor.fetchone()[0]
        print(f"  {t:15}: {cnt}")
    except Exception as e:
        print(f"  {t:15}: Error - {e}")
