import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()
cur.execute("""
    SELECT constraint_name, table_name, delete_rule 
    FROM user_constraints 
    WHERE constraint_name IN ('FK_BOOKCOPIES_BOOK', 'FK_BOOKAUTHORS_BOOK', 'FK_LOANS_COPY', 'FK_FINES_LOAN')
""")
for row in cur.fetchall():
    print(row)
conn.close()
