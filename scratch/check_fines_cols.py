import oracledb

conn = oracledb.connect(user="system", password="root", dsn="localhost:1521/XEPDB1")
cur = conn.cursor()
cur.execute("SELECT column_name FROM user_tab_cols WHERE table_name = 'FINES'")
print([r[0] for r in cur.fetchall()])
conn.close()
