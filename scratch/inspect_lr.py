import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()
cur.execute("SELECT index_name, uniqueness FROM user_indexes WHERE table_name = 'LOAN_REQUESTS'")
print("INDEXES:", cur.fetchall())

cur.execute("SELECT index_name, column_name FROM user_ind_columns WHERE table_name = 'LOAN_REQUESTS'")
print("INDEX COLUMNS:", cur.fetchall())

cur.execute("SELECT * FROM Loan_Requests WHERE ROWNUM <= 10")
print("SAMPLE ROWS:", cur.fetchall())
conn.close()
